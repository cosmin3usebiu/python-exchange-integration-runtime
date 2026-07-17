"""Exchange runtime orchestration object definitions."""

from __future__ import annotations

from dataclasses import dataclass

from python_http_runtime import HttpRuntime
from python_http_runtime import HttpRequest
from python_http_runtime import HttpResponse
from python_http_runtime.errors import HttpRuntimeError
from python_exchange_integration_runtime.adapter import ExchangeAdapter
from python_exchange_integration_runtime.errors import AdapterConfigurationError
from python_exchange_integration_runtime.errors import EndpointResolutionError
from python_exchange_integration_runtime.errors import ExchangeRequestError
from python_exchange_integration_runtime.errors import ExchangeResponseError
from python_exchange_integration_runtime.errors import RequestSigningError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.exchange_request import ExchangeRequest
from python_exchange_integration_runtime.exchange_response import ExchangeResponse
from python_exchange_integration_runtime.signing import RequestSigner


@dataclass(slots=True)
class ExchangeRuntime:
    """Coordinate exchange request execution through a generic workflow.

    Purpose:
        Reserve the public runtime object that will later orchestrate endpoint
        ownership checks, request construction, optional signing, lower-level
        HTTP execution, and response interpretation.

    Parameters:
        http_runtime: Lower-level HTTP runtime used for transport execution.
        adapter: Exchange-specific behavior provider.

    Attributes:
        http_runtime: Lower-level HTTP runtime used for transport execution.
        adapter: Exchange-specific behavior provider.

    Raises:
        No additional exceptions are raised during skeleton construction.

    Usage Notes:
        This runtime is an orchestrator only. Exchange-specific behavior
        belongs to the adapter and signing contracts.
    """

    http_runtime: HttpRuntime
    adapter: ExchangeAdapter

    def __post_init__(self) -> None:
        """Validate runtime collaborators before execution begins."""
        if not isinstance(self.http_runtime, HttpRuntime):
            raise AdapterConfigurationError(
                "Exchange runtime http_runtime must be an HttpRuntime instance."
            )

        if not isinstance(self.adapter, ExchangeAdapter):
            raise AdapterConfigurationError(
                "Exchange runtime adapter must be an ExchangeAdapter instance."
            )

    def execute(self, request: ExchangeRequest) -> ExchangeResponse:
        """Execute one exchange request through the runtime.

        Args:
            request: Immutable exchange request to execute.

        Returns:
            A stable exchange response object.

        Raises:
            ExchangeRequestError: If request construction or collaborator
                outputs violate runtime contracts.
            RequestSigningError: If signing outputs violate runtime contracts.
            ExchangeResponseError: If response interpretation violates runtime
                contracts.
        """
        if not isinstance(request, ExchangeRequest):
            raise ExchangeRequestError(
                "Exchange runtime execute() requires an ExchangeRequest instance."
            )

        endpoint = _resolve_endpoint(
            adapter=self.adapter,
            request=request,
        )
        canonical_request = _canonicalize_request(
            request=request,
            endpoint=endpoint,
        )

        unsigned_http_request = _build_http_request(
            adapter=self.adapter,
            request=canonical_request,
        )
        if not isinstance(unsigned_http_request, HttpRequest):
            raise ExchangeRequestError(
                "Exchange adapter build_http_request() must return an HttpRequest "
                "instance."
            )

        final_http_request = unsigned_http_request
        signer = _get_signer(
            adapter=self.adapter,
            endpoint=endpoint,
        )
        if signer is not None:
            final_http_request = _sign_http_request(
                signer=signer,
                http_request=unsigned_http_request,
                exchange_request=canonical_request,
            )
            if not isinstance(final_http_request, HttpRequest):
                raise RequestSigningError(
                    "Exchange request signer must return an HttpRequest instance."
                )

        http_response = _execute_http_request(
            http_runtime=self.http_runtime,
            request=final_http_request,
        )
        if not isinstance(http_response, HttpResponse):
            raise ExchangeResponseError(
                "Underlying HttpRuntime must return an HttpResponse instance."
            )

        exchange_response = _interpret_response(
            adapter=self.adapter,
            request=canonical_request,
            response=http_response,
        )
        if not isinstance(exchange_response, ExchangeResponse):
            raise ExchangeResponseError(
                "Exchange adapter interpret_response() must return an "
                "ExchangeResponse instance."
            )

        return exchange_response


def _canonicalize_request(
    *,
    request: ExchangeRequest,
    endpoint: ExchangeEndpoint,
) -> ExchangeRequest:
    """Return a request that references the canonical adapter-owned endpoint."""
    if request.endpoint is endpoint:
        return request

    return ExchangeRequest(
        endpoint=endpoint,
        path_params=request.path_params,
        query_params=request.query_params,
        headers=request.headers,
        body=request.body,
        timeout_seconds=request.timeout_seconds,
    )


def _resolve_endpoint(
    *,
    adapter: ExchangeAdapter,
    request: ExchangeRequest,
) -> ExchangeEndpoint:
    """Resolve one request endpoint through the adapter boundary."""
    try:
        return adapter.resolve_endpoint(request.endpoint)
    except EndpointResolutionError:
        raise
    except Exception as exc:
        raise EndpointResolutionError(
            "Exchange adapter failed to resolve the request endpoint."
        ) from exc


def _build_http_request(
    *,
    adapter: ExchangeAdapter,
    request: ExchangeRequest,
) -> HttpRequest:
    """Build one unsigned HTTP request through the adapter boundary."""
    try:
        return adapter.build_http_request(request)
    except ExchangeRequestError:
        raise
    except Exception as exc:
        raise ExchangeRequestError(
            "Exchange adapter failed to build an HttpRequest."
        ) from exc


def _get_signer(
    *,
    adapter: ExchangeAdapter,
    endpoint: ExchangeEndpoint,
) -> RequestSigner | None:
    """Resolve the optional request signer for one endpoint."""
    try:
        signer = adapter.get_signer(endpoint)
    except AdapterConfigurationError:
        raise
    except Exception as exc:
        raise AdapterConfigurationError(
            "Exchange adapter failed to resolve a request signer."
        ) from exc

    if signer is not None and not isinstance(signer, RequestSigner):
        raise AdapterConfigurationError(
            "Exchange adapter get_signer() must return a RequestSigner or None."
        )

    return signer


def _sign_http_request(
    *,
    signer: RequestSigner,
    http_request: HttpRequest,
    exchange_request: ExchangeRequest,
) -> HttpRequest:
    """Sign one immutable HTTP request through the signer boundary."""
    try:
        return signer.sign(http_request, exchange_request)
    except RequestSigningError:
        raise
    except Exception as exc:
        raise RequestSigningError("Exchange request signing failed.") from exc


def _execute_http_request(
    *,
    http_runtime: HttpRuntime,
    request: HttpRequest,
) -> HttpResponse:
    """Execute one HTTP request through the lower-level runtime."""
    try:
        return http_runtime.execute(request)
    except HttpRuntimeError as exc:
        raise ExchangeResponseError(
            "Underlying HttpRuntime failed to execute the exchange request."
        ) from exc
    except Exception as exc:
        raise ExchangeResponseError(
            "Underlying HttpRuntime raised an unexpected execution failure."
        ) from exc


def _interpret_response(
    *,
    adapter: ExchangeAdapter,
    request: ExchangeRequest,
    response: HttpResponse,
) -> ExchangeResponse:
    """Interpret one HTTP response through the adapter boundary."""
    try:
        return adapter.interpret_response(request, response)
    except ExchangeResponseError:
        raise
    except Exception as exc:
        raise ExchangeResponseError(
            "Exchange adapter failed to interpret the HttpResponse."
        ) from exc
