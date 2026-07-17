"""Behavioral tests for exchange adapter registration and ownership."""

from __future__ import annotations

from python_exchange_integration_runtime.adapter import ExchangeAdapter
from python_exchange_integration_runtime.errors import (
    AdapterConfigurationError,
    EndpointResolutionError,
)
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.exchange_request import ExchangeRequest
from python_exchange_integration_runtime.signing import RequestSigner


class _DummySigner(RequestSigner):
    """Minimal signer used to validate signer ownership and lookup."""

    def sign(self, request, exchange_request):
        del exchange_request
        return request


class _DummyAdapter(ExchangeAdapter):
    """Concrete adapter used to validate registration behavior."""

    def build_http_request(self, request: ExchangeRequest):
        raise NotImplementedError

    def interpret_response(self, request, response):
        raise NotImplementedError


def test_adapter_registers_endpoints_in_declaration_order() -> None:
    """Verify endpoint registration preserves declaration order."""
    first_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    second_endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )

    adapter = _DummyAdapter(
        name="demo",
        endpoints=(first_endpoint, second_endpoint),
    )

    assert adapter.name == "demo"
    assert adapter.endpoints == (first_endpoint, second_endpoint)


def test_adapter_can_lookup_registered_endpoint_by_name() -> None:
    """Verify adapters return canonical endpoint metadata by name."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(endpoint,),
    )

    resolved_endpoint = adapter.get_endpoint("public_ping")

    assert resolved_endpoint is endpoint


def test_adapter_supports_only_owned_canonical_endpoints() -> None:
    """Verify endpoint ownership requires matching canonical metadata."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(endpoint,),
    )
    equivalent_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    mismatched_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="POST",
        path="/v1/ping",
    )
    unknown_endpoint = ExchangeEndpoint(
        name="unknown",
        method="GET",
        path="/v1/unknown",
    )

    assert adapter.supports_endpoint(endpoint) is True
    assert adapter.supports_endpoint(equivalent_endpoint) is True
    assert adapter.supports_endpoint(mismatched_endpoint) is False
    assert adapter.supports_endpoint(unknown_endpoint) is False


def test_adapter_resolve_endpoint_rejects_mismatched_metadata() -> None:
    """Verify canonical endpoint resolution rejects unsupported metadata."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(endpoint,),
    )
    mismatched_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="POST",
        path="/v1/ping",
    )

    try:
        adapter.resolve_endpoint(mismatched_endpoint)
    except EndpointResolutionError as exc:
        assert str(exc) == (
            "Endpoint 'public_ping' does not match the canonical definition "
            "owned by adapter 'demo'."
        )
    else:
        raise AssertionError("Expected EndpointResolutionError to be raised.")


def test_adapter_returns_registered_optional_signer() -> None:
    """Verify adapters return optional signers for owned endpoints."""
    public_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    private_endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )
    signer = _DummySigner()
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(public_endpoint, private_endpoint),
        signers={"private_account": signer},
    )

    assert adapter.get_signer(public_endpoint) is None
    assert adapter.get_signer(private_endpoint) is signer


def test_adapter_rejects_invalid_endpoint_registry() -> None:
    """Verify endpoint registry validation fails fast."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )

    try:
        _DummyAdapter(name="demo", endpoints=())
    except AdapterConfigurationError as exc:
        assert str(exc) == "Exchange adapter must define at least one endpoint."
    else:
        raise AssertionError("Expected AdapterConfigurationError to be raised.")

    try:
        _DummyAdapter(
            name="demo",
            endpoints=(endpoint, endpoint),
        )
    except AdapterConfigurationError as exc:
        assert str(exc) == (
            "Exchange adapter endpoints must not contain duplicate names: "
            "'public_ping'."
        )
    else:
        raise AssertionError("Expected AdapterConfigurationError to be raised.")


def test_adapter_rejects_invalid_signer_registry() -> None:
    """Verify signer registry validation fails fast."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )

    try:
        _DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
            signers={"unknown": _DummySigner()},
        )
    except AdapterConfigurationError as exc:
        assert str(exc) == (
            "Exchange adapter signer registry references unknown endpoint "
            "'unknown'."
        )
    else:
        raise AssertionError("Expected AdapterConfigurationError to be raised.")

    try:
        _DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
            signers={"public_ping": object()},  # type: ignore[arg-type]
        )
    except AdapterConfigurationError as exc:
        assert str(exc) == (
            "Exchange adapter signers must be RequestSigner instances."
        )
    else:
        raise AssertionError("Expected AdapterConfigurationError to be raised.")
