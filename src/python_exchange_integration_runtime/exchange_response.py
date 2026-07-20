"""Exchange response object definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType

from python_exchange_integration_runtime.errors import ExchangeResponseError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.types import HeaderMapping, PayloadType


@dataclass(slots=True, frozen=True, kw_only=True)
class ExchangeResponse:
    """Describe one exchange response at the repository boundary.

    Purpose:
        Provide a stable response boundary that contains exchange/runtime
        response information only and excludes higher-level business models.

    Parameters:
        endpoint: Immutable endpoint metadata associated with the response.
        status_code: HTTP status code returned by the remote exchange.
        headers: Optional HTTP response header mapping.
        payload: Optional interpreted payload owned by the adapter boundary.
        request_id: Optional exchange request identifier if exposed.

    Attributes:
        endpoint: Immutable endpoint metadata associated with the response.
        status_code: HTTP status code returned by the remote exchange.
        headers: Optional HTTP response header mapping.
        payload: Optional interpreted payload owned by the adapter boundary.
        request_id: Optional exchange request identifier if exposed.

    Raises:
        ExchangeResponseError: If response metadata is structurally invalid.

    Usage Notes:
        Construction normalizes and validates response metadata. Adapter
        implementations own payload interpretation; this model does not expose
        higher-level business-domain objects.
    """

    endpoint: ExchangeEndpoint
    status_code: int
    headers: HeaderMapping = field(default_factory=dict)
    payload: PayloadType = None
    request_id: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate immutable response metadata."""
        if not isinstance(self.endpoint, ExchangeEndpoint):
            raise ExchangeResponseError(
                "Exchange response endpoint must be an ExchangeEndpoint instance."
            )

        if isinstance(self.status_code, bool) or not isinstance(self.status_code, int):
            raise ExchangeResponseError(
                "Exchange response status code must be an integer."
            )

        if self.status_code < 100 or self.status_code > 599:
            raise ExchangeResponseError(
                "Exchange response status code must be between 100 and 599."
            )

        object.__setattr__(self, "headers", _normalize_headers(self.headers))
        object.__setattr__(self, "request_id", _normalize_request_id(self.request_id))


def _normalize_headers(headers: HeaderMapping) -> HeaderMapping:
    """Normalize response headers into an immutable lowercase mapping."""
    normalized_headers: dict[str, str] = {}

    for header_name, header_value in headers.items():
        if not isinstance(header_name, str):
            raise ExchangeResponseError(
                "Exchange response header names must be strings."
            )

        if not isinstance(header_value, str):
            raise ExchangeResponseError(
                "Exchange response header values must be strings."
            )

        normalized_header_name = header_name.strip().lower()
        normalized_header_value = header_value.strip()

        if not normalized_header_name:
            raise ExchangeResponseError(
                "Exchange response header names must be non-empty."
            )

        normalized_headers[normalized_header_name] = normalized_header_value

    return MappingProxyType(normalized_headers)


def _normalize_request_id(request_id: str | None) -> str | None:
    """Normalize and validate an optional exchange request identifier."""
    if request_id is None:
        return None

    if not isinstance(request_id, str):
        raise ExchangeResponseError(
            "Exchange response request_id must be a string or None."
        )

    normalized_request_id = request_id.strip()
    if not normalized_request_id:
        raise ExchangeResponseError(
            "Exchange response request_id must be non-empty when set."
        )

    return normalized_request_id
