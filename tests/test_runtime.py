"""Behavioral tests for runtime orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from python_http_runtime import HttpRequest
from python_http_runtime import HttpResponse
from python_http_runtime import HttpRuntime
from python_http_runtime import RuntimeSettings
from python_http_runtime.errors import HttpTransportError
from python_http_runtime.testing import MockTransport
from python_exchange_integration_runtime.adapter import ExchangeAdapter
from python_exchange_integration_runtime.errors import AdapterConfigurationError
from python_exchange_integration_runtime.errors import EndpointResolutionError
from python_exchange_integration_runtime.errors import ExchangeRequestError
from python_exchange_integration_runtime.errors import ExchangeResponseError
from python_exchange_integration_runtime.errors import RequestSigningError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.exchange_request import ExchangeRequest
from python_exchange_integration_runtime.exchange_response import ExchangeResponse
from python_exchange_integration_runtime.runtime import ExchangeRuntime
from python_exchange_integration_runtime.signing import RequestSigner


@dataclass(slots=True)
class _RecordingSigner(RequestSigner):
    """Signer double that records inputs and returns a new signed request."""

    seen_requests: list[HttpRequest] = field(default_factory=list)
    seen_exchange_requests: list[ExchangeRequest] = field(default_factory=list)

    def sign(
        self,
        request: HttpRequest,
        exchange_request: ExchangeRequest,
    ) -> HttpRequest:
        self.seen_requests.append(request)
        self.seen_exchange_requests.append(exchange_request)
        signed_headers = dict(request.headers)
        signed_headers["x-signature"] = "signed"
        return HttpRequest(
            method=request.method,
            target=request.target,
            headers=signed_headers,
            query_params=request.query_params,
            body=request.body,
            timeout_seconds=request.timeout_seconds,
        )


@dataclass(slots=True)
class _InvalidSigner(RequestSigner):
    """Signer double that violates the runtime contract."""

    def sign(
        self,
        request: HttpRequest,
        exchange_request: ExchangeRequest,
    ) -> HttpRequest:
        del request
        del exchange_request
        return object()  # type: ignore[return-value]


class _DummyAdapter(ExchangeAdapter):
    """Concrete adapter used to verify runtime orchestration behavior."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.built_requests: list[ExchangeRequest] = []
        self.interpreted_requests: list[ExchangeRequest] = []
        self.interpreted_http_responses: list[HttpResponse] = []

    def build_http_request(self, request: ExchangeRequest) -> HttpRequest:
        self.built_requests.append(request)
        return HttpRequest(
            method=request.endpoint.method,
            target=request.endpoint.path,
            headers=request.headers,
            query_params=request.query_params,
            timeout_seconds=request.timeout_seconds,
        )

    def interpret_response(
        self,
        request: ExchangeRequest,
        response: HttpResponse,
    ) -> ExchangeResponse:
        self.interpreted_requests.append(request)
        self.interpreted_http_responses.append(response)
        return ExchangeResponse(
            endpoint=request.endpoint,
            status_code=response.status_code,
            headers=response.headers,
            payload={"body": response.body},
        )


class _InvalidRequestAdapter(_DummyAdapter):
    """Adapter double that violates request-construction output contracts."""

    def build_http_request(self, request: ExchangeRequest) -> HttpRequest:
        del request
        return object()  # type: ignore[return-value]


class _InvalidResponseAdapter(_DummyAdapter):
    """Adapter double that violates response-interpretation output contracts."""

    def interpret_response(
        self,
        request: ExchangeRequest,
        response: HttpResponse,
    ) -> ExchangeResponse:
        del request
        del response
        return object()  # type: ignore[return-value]


class _RaisingEndpointAdapter(_DummyAdapter):
    """Adapter double that raises during endpoint resolution."""

    def resolve_endpoint(self, endpoint: ExchangeEndpoint) -> ExchangeEndpoint:
        del endpoint
        raise ValueError("resolution failure")


class _RaisingRequestAdapter(_DummyAdapter):
    """Adapter double that raises during request construction."""

    def build_http_request(self, request: ExchangeRequest) -> HttpRequest:
        del request
        raise ValueError("request build failure")


class _RaisingSigner(RequestSigner):
    """Signer double that raises during signing."""

    def sign(
        self,
        request: HttpRequest,
        exchange_request: ExchangeRequest,
    ) -> HttpRequest:
        del request
        del exchange_request
        raise ValueError("signing failure")


class _RaisingResponseAdapter(_DummyAdapter):
    """Adapter double that raises during response interpretation."""

    def interpret_response(
        self,
        request: ExchangeRequest,
        response: HttpResponse,
    ) -> ExchangeResponse:
        del request
        del response
        raise ValueError("response interpretation failure")


class _EndpointErrorAdapter(_DummyAdapter):
    """Adapter double that raises a repository-native endpoint error."""

    def resolve_endpoint(self, endpoint: ExchangeEndpoint) -> ExchangeEndpoint:
        del endpoint
        raise EndpointResolutionError("native endpoint failure")


class _RequestErrorAdapter(_DummyAdapter):
    """Adapter double that raises a repository-native request error."""

    def build_http_request(self, request: ExchangeRequest) -> HttpRequest:
        del request
        raise ExchangeRequestError("native request failure")


class _NativeSigningErrorSigner(RequestSigner):
    """Signer double that raises a repository-native signing error."""

    def sign(
        self,
        request: HttpRequest,
        exchange_request: ExchangeRequest,
    ) -> HttpRequest:
        del request
        del exchange_request
        raise RequestSigningError("native signing failure")


class _ResponseErrorAdapter(_DummyAdapter):
    """Adapter double that raises a repository-native response error."""

    def interpret_response(
        self,
        request: ExchangeRequest,
        response: HttpResponse,
    ) -> ExchangeResponse:
        del request
        del response
        raise ExchangeResponseError("native response failure")


def test_runtime_executes_unsigned_request_through_adapter_and_http_runtime() -> None:
    """Verify the runtime orchestrates unsigned execution end to end."""
    registered_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    equivalent_endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(registered_endpoint,),
    )
    transport = MockTransport(
        outcomes=(HttpResponse(status_code=200, body=b"pong"),),
    )
    http_runtime = HttpRuntime(
        settings=RuntimeSettings(base_url="https://api.exchange.test"),
        transport=transport,
    )
    runtime = ExchangeRuntime(http_runtime=http_runtime, adapter=adapter)
    request = ExchangeRequest(
        endpoint=equivalent_endpoint,
        query_params={"limit": 1},
        headers={"X-Trace-ID": "trace-1"},
        timeout_seconds=5,
    )

    response = runtime.execute(request)

    assert adapter.built_requests[0].endpoint is registered_endpoint
    assert transport.requests[0].target == "https://api.exchange.test/v1/ping"
    assert transport.requests[0].headers == {"x-trace-id": "trace-1"}
    assert transport.requests[0].query_params == {"limit": 1}
    assert adapter.interpreted_requests[0].endpoint is registered_endpoint
    assert response.endpoint is registered_endpoint
    assert response.status_code == 200
    assert response.payload == {"body": b"pong"}


def test_runtime_invokes_optional_signer_immutably() -> None:
    """Verify signing is optional and produces a new immutable request."""
    endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )
    signer = _RecordingSigner()
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(endpoint,),
        signers={"private_account": signer},
    )
    transport = MockTransport(
        outcomes=(HttpResponse(status_code=200, body=b"ok"),),
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(base_url="https://api.exchange.test"),
            transport=transport,
        ),
        adapter=adapter,
    )
    request = ExchangeRequest(
        endpoint=endpoint,
        headers={"X-API-KEY": "client-key"},
    )

    runtime.execute(request)

    assert len(signer.seen_requests) == 1
    assert signer.seen_requests[0].headers == {"x-api-key": "client-key"}
    assert transport.requests[0].headers == {
        "x-api-key": "client-key",
        "x-signature": "signed",
    }


def test_runtime_rejects_invalid_collaborators() -> None:
    """Verify collaborator type validation fails fast."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    adapter = _DummyAdapter(
        name="demo",
        endpoints=(endpoint,),
    )
    http_runtime = HttpRuntime(
        settings=RuntimeSettings(),
        transport=MockTransport(),
    )

    with pytest.raises(
        AdapterConfigurationError,
        match="Exchange runtime http_runtime must be an HttpRuntime instance.",
    ):
        ExchangeRuntime(
            http_runtime=object(),  # type: ignore[arg-type]
            adapter=adapter,
        )

    with pytest.raises(
        AdapterConfigurationError,
        match="Exchange runtime adapter must be an ExchangeAdapter instance.",
    ):
        ExchangeRuntime(
            http_runtime=http_runtime,
            adapter=object(),  # type: ignore[arg-type]
        )


def test_runtime_rejects_invalid_request_object() -> None:
    """Verify execute() validates the request boundary."""
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
            name="demo",
            endpoints=(endpoint,),
        ),
    )

    with pytest.raises(
        ExchangeRequestError,
        match="Exchange runtime execute\\(\\) requires an ExchangeRequest instance.",
    ):
        runtime.execute(object())  # type: ignore[arg-type]


def test_runtime_rejects_invalid_http_request_output_type() -> None:
    """Verify adapter request-construction output must be an HttpRequest."""
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
        adapter=_InvalidRequestAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeRequestError,
        match="Exchange adapter build_http_request\\(\\) must return an HttpRequest instance.",
    ):
        runtime.execute(request)


def test_runtime_rejects_invalid_signer_output_type() -> None:
    """Verify signer outputs must remain immutable HttpRequest objects."""
    endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(
                outcomes=(HttpResponse(status_code=200),),
            ),
        ),
        adapter=_DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
            signers={"private_account": _InvalidSigner()},
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        RequestSigningError,
        match="Exchange request signer must return an HttpRequest instance.",
    ):
        runtime.execute(request)


def test_runtime_rejects_invalid_exchange_response_output_type() -> None:
    """Verify adapter response interpretation must return ExchangeResponse."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(
                outcomes=(HttpResponse(status_code=200),),
            ),
        ),
        adapter=_InvalidResponseAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeResponseError,
        match=(
            "Exchange adapter interpret_response\\(\\) must return an "
            "ExchangeResponse instance."
        ),
    ):
        runtime.execute(request)


def test_runtime_normalizes_unexpected_endpoint_resolution_failures() -> None:
    """Verify unexpected endpoint resolution failures are normalized."""
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
        adapter=_RaisingEndpointAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        EndpointResolutionError,
        match="Exchange adapter failed to resolve the request endpoint.",
    ) as exc_info:
        runtime.execute(request)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_runtime_normalizes_unexpected_request_construction_failures() -> None:
    """Verify unexpected request construction failures are normalized."""
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
        adapter=_RaisingRequestAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeRequestError,
        match="Exchange adapter failed to build an HttpRequest.",
    ) as exc_info:
        runtime.execute(request)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_runtime_normalizes_unexpected_signing_failures() -> None:
    """Verify unexpected signing failures are normalized."""
    endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(),
        ),
        adapter=_DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
            signers={"private_account": _RaisingSigner()},
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        RequestSigningError,
        match="Exchange request signing failed.",
    ) as exc_info:
        runtime.execute(request)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_runtime_normalizes_lower_http_runtime_failures() -> None:
    """Verify lower-level HTTP runtime failures are normalized."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    transport = MockTransport(
        outcomes=(HttpTransportError("transport failure"),),
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=transport,
        ),
        adapter=_DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeResponseError,
        match="Underlying HttpRuntime failed to execute the exchange request.",
    ) as exc_info:
        runtime.execute(request)

    assert isinstance(exc_info.value.__cause__, HttpTransportError)


def test_runtime_normalizes_unexpected_response_interpretation_failures() -> None:
    """Verify unexpected response interpretation failures are normalized."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(
                outcomes=(HttpResponse(status_code=200),),
            ),
        ),
        adapter=_RaisingResponseAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeResponseError,
        match="Exchange adapter failed to interpret the HttpResponse.",
    ) as exc_info:
        runtime.execute(request)

    assert isinstance(exc_info.value.__cause__, ValueError)


def test_runtime_preserves_repository_native_endpoint_errors() -> None:
    """Verify repository-native endpoint failures pass through unchanged."""
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
        adapter=_EndpointErrorAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        EndpointResolutionError,
        match="native endpoint failure",
    ) as exc_info:
        runtime.execute(request)

    assert exc_info.value.__cause__ is None


def test_runtime_preserves_repository_native_request_errors() -> None:
    """Verify repository-native request failures pass through unchanged."""
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
        adapter=_RequestErrorAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeRequestError,
        match="native request failure",
    ) as exc_info:
        runtime.execute(request)

    assert exc_info.value.__cause__ is None


def test_runtime_preserves_repository_native_signing_errors() -> None:
    """Verify repository-native signing failures pass through unchanged."""
    endpoint = ExchangeEndpoint(
        name="private_account",
        method="GET",
        path="/v1/account",
        requires_auth=True,
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(),
        ),
        adapter=_DummyAdapter(
            name="demo",
            endpoints=(endpoint,),
            signers={"private_account": _NativeSigningErrorSigner()},
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        RequestSigningError,
        match="native signing failure",
    ) as exc_info:
        runtime.execute(request)

    assert exc_info.value.__cause__ is None


def test_runtime_preserves_repository_native_response_errors() -> None:
    """Verify repository-native response failures pass through unchanged."""
    endpoint = ExchangeEndpoint(
        name="public_ping",
        method="GET",
        path="/v1/ping",
    )
    runtime = ExchangeRuntime(
        http_runtime=HttpRuntime(
            settings=RuntimeSettings(),
            transport=MockTransport(
                outcomes=(HttpResponse(status_code=200),),
            ),
        ),
        adapter=_ResponseErrorAdapter(
            name="demo",
            endpoints=(endpoint,),
        ),
    )
    request = ExchangeRequest(endpoint=endpoint)

    with pytest.raises(
        ExchangeResponseError,
        match="native response failure",
    ) as exc_info:
        runtime.execute(request)

    assert exc_info.value.__cause__ is None
