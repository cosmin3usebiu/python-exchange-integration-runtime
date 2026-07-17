"""Tests for the core package structure and immutable object model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType

import pytest

from python_http_runtime import HttpRuntime
from python_http_runtime import RuntimeSettings
from python_http_runtime.testing import MockTransport
from python_exchange_integration_runtime.adapter import ExchangeAdapter
from python_exchange_integration_runtime.errors import AdapterConfigurationError
from python_exchange_integration_runtime.errors import EndpointResolutionError
from python_exchange_integration_runtime.errors import ExchangeRequestError
from python_exchange_integration_runtime.errors import ExchangeResponseError
from python_exchange_integration_runtime.errors import ExchangeRuntimeError
from python_exchange_integration_runtime.errors import RequestSigningError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.exchange_request import ExchangeRequest
from python_exchange_integration_runtime.exchange_response import ExchangeResponse
from python_exchange_integration_runtime.runtime import ExchangeRuntime


class _DummyAdapter(ExchangeAdapter):
    """Minimal adapter used to verify non-operational runtime structure."""

    def supports_endpoint(self, endpoint: ExchangeEndpoint) -> bool:
        return True

    def build_http_request(self, request: ExchangeRequest):
        raise NotImplementedError

    def get_signer(self, endpoint: ExchangeEndpoint):
        return None

    def interpret_response(self, request: ExchangeRequest, response):
        raise NotImplementedError


def test_exchange_endpoint_is_immutable() -> None:
    """Verify immutable endpoint metadata cannot be mutated."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )

    with pytest.raises(FrozenInstanceError):
        endpoint.path = "/v2/ping"  # type: ignore[misc]


def test_exchange_endpoint_normalizes_method_and_optional_metadata() -> None:
    """Verify endpoint metadata is normalized deterministically."""
    endpoint = ExchangeEndpoint(
        name="  public_ping  ",
        method=" get ",
        path=" /v1/ping ",
        requires_auth=False,
        version=" v1 ",
        content_type=" application/json ",
    )

    assert endpoint.name == "public_ping"
    assert endpoint.method == "GET"
    assert endpoint.path == "/v1/ping"
    assert endpoint.version == "v1"
    assert endpoint.content_type == "application/json"


def test_exchange_endpoint_rejects_invalid_metadata() -> None:
    """Verify structurally invalid endpoint metadata fails fast."""
    with pytest.raises(
        AdapterConfigurationError,
        match="Exchange endpoint path must start with '/'.",
    ):
        ExchangeEndpoint(
            name="public_ping",
            method="GET",
            path="v1/ping",
        )

    with pytest.raises(
        AdapterConfigurationError,
        match="Exchange endpoint method must be non-empty.",
    ):
        ExchangeEndpoint(
            name="public_ping",
            method="   ",
            path="/v1/ping",
        )


def test_exchange_request_is_immutable() -> None:
    """Verify immutable exchange requests cannot be mutated."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(FrozenInstanceError):
        request.timeout_seconds = 5.0  # type: ignore[misc]


def test_exchange_request_normalizes_headers_and_mappings() -> None:
    """Verify request metadata is normalized into immutable mappings."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    request = ExchangeRequest(
        endpoint=endpoint,
        path_params={" symbol ": " BTCUSDT "},
        query_params={" limit ": 100, " recv_window ": " 5000 "},
        headers={" X-API-KEY ": " secret "},
        timeout_seconds=5,
    )

    assert isinstance(request.path_params, MappingProxyType)
    assert isinstance(request.query_params, MappingProxyType)
    assert isinstance(request.headers, MappingProxyType)
    assert request.path_params == {"symbol": "BTCUSDT"}
    assert request.query_params == {"limit": 100, "recv_window": "5000"}
    assert request.headers == {"x-api-key": "secret"}
    assert request.timeout_seconds == 5.0


def test_exchange_request_rejects_invalid_metadata() -> None:
    """Verify invalid request metadata fails fast."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )

    with pytest.raises(
        ExchangeRequestError,
        match="Exchange request endpoint must be an ExchangeEndpoint instance.",
    ):
        ExchangeRequest(endpoint="not-an-endpoint")  # type: ignore[arg-type]

    with pytest.raises(
        ExchangeRequestError,
        match="Path parameter values must be strings or integers.",
    ):
        ExchangeRequest(
            endpoint=endpoint,
            path_params={"symbol": True},
        )

    with pytest.raises(
        ExchangeRequestError,
        match="Exchange request timeout must be greater than zero.",
    ):
        ExchangeRequest(
            endpoint=endpoint,
            timeout_seconds=0,
        )


def test_exchange_response_is_immutable() -> None:
    """Verify immutable exchange responses cannot be mutated."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    response = ExchangeResponse(
        endpoint=endpoint,
        status_code=200,
    )

    with pytest.raises(FrozenInstanceError):
        response.status_code = 201  # type: ignore[misc]


def test_exchange_response_normalizes_headers_and_request_id() -> None:
    """Verify response metadata is normalized deterministically."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    response = ExchangeResponse(
        endpoint=endpoint,
        status_code=200,
        headers={" X-REQUEST-ID ": " abc-123 "},
        request_id=" req-1 ",
    )

    assert isinstance(response.headers, MappingProxyType)
    assert response.headers == {"x-request-id": "abc-123"}
    assert response.request_id == "req-1"


def test_exchange_response_rejects_invalid_metadata() -> None:
    """Verify invalid response metadata fails fast."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )

    with pytest.raises(
        ExchangeResponseError,
        match="Exchange response status code must be between 100 and 599.",
    ):
        ExchangeResponse(
            endpoint=endpoint,
            status_code=99,
        )

    with pytest.raises(
        ExchangeResponseError,
        match="Exchange response request_id must be non-empty when set.",
    ):
        ExchangeResponse(
            endpoint=endpoint,
            status_code=200,
            request_id="   ",
        )


def test_exchange_runtime_is_constructible_with_valid_collaborators() -> None:
    """Verify the runtime accepts valid collaborator wiring."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(),
        ),
        adapter=_DummyAdapter(
            name="dummy",
            endpoints=(endpoint,),
        ),
    )

    assert runtime.http_runtime is not None
    assert runtime.adapter is not None


def test_exception_hierarchy_uses_repository_root_type() -> None:
    """Verify structured repository exceptions share one explicit root type."""
    exceptions = (
        AdapterConfigurationError("adapter error"),
        EndpointResolutionError("endpoint error"),
        RequestSigningError("signing error"),
        ExchangeRequestError("request error"),
        ExchangeResponseError("response error"),
    )

    for exception in exceptions:
        assert isinstance(exception, ExchangeRuntimeError)
