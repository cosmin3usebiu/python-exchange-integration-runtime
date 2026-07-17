"""Exchange request object definitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType

from python_exchange_integration_runtime.errors import ExchangeRequestError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.types import HeaderMapping
from python_exchange_integration_runtime.types import PathParameterMapping
from python_exchange_integration_runtime.types import PathParameterValue
from python_exchange_integration_runtime.types import PayloadType
from python_exchange_integration_runtime.types import QueryParameterMapping
from python_exchange_integration_runtime.types import QueryParameterValue


@dataclass(slots=True, frozen=True, kw_only=True)
class ExchangeRequest:
    """Describe one exchange request in HTTP-oriented runtime terms.

    Purpose:
        Provide a business-neutral request boundary that references immutable
        endpoint metadata and caller-supplied HTTP-oriented inputs.

    Parameters:
        endpoint: Immutable endpoint metadata owned by an adapter.
        path_params: Optional path-parameter mapping.
        query_params: Optional query-parameter mapping.
        headers: Optional caller-supplied header mapping.
        body: Optional request body payload.
        timeout_seconds: Optional timeout override for one execution.

    Attributes:
        endpoint: Immutable endpoint metadata owned by an adapter.
        path_params: Optional path-parameter mapping.
        query_params: Optional query-parameter mapping.
        headers: Optional caller-supplied header mapping.
        body: Optional request body payload.
        timeout_seconds: Optional timeout override for one execution.

    Raises:
        ExchangeRequestError: If request metadata is structurally invalid.

    Usage Notes:
        Validation and runtime normalization are intentionally deferred to a
        later milestone.
    """

    endpoint: ExchangeEndpoint
    path_params: PathParameterMapping = field(default_factory=dict)
    query_params: QueryParameterMapping = field(default_factory=dict)
    headers: HeaderMapping = field(default_factory=dict)
    body: PayloadType = None
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        """Normalize and validate immutable request metadata."""
        if not isinstance(self.endpoint, ExchangeEndpoint):
            raise ExchangeRequestError(
                "Exchange request endpoint must be an ExchangeEndpoint instance."
            )

        object.__setattr__(
            self,
            "path_params",
            _normalize_path_params(self.path_params),
        )
        object.__setattr__(
            self,
            "query_params",
            _normalize_query_params(self.query_params),
        )
        object.__setattr__(self, "headers", _normalize_headers(self.headers))
        object.__setattr__(
            self,
            "timeout_seconds",
            _normalize_timeout_seconds(self.timeout_seconds),
        )


def _normalize_path_params(path_params: PathParameterMapping) -> PathParameterMapping:
    """Normalize path parameters into an immutable mapping."""
    normalized_path_params: dict[str, PathParameterValue] = {}

    for parameter_name, parameter_value in path_params.items():
        if not isinstance(parameter_name, str):
            raise ExchangeRequestError("Path parameter names must be strings.")

        normalized_parameter_name = parameter_name.strip()
        if not normalized_parameter_name:
            raise ExchangeRequestError("Path parameter names must be non-empty.")

        if isinstance(parameter_value, bool) or not isinstance(
            parameter_value,
            (str, int),
        ):
            raise ExchangeRequestError(
                "Path parameter values must be strings or integers."
            )

        if isinstance(parameter_value, str):
            normalized_parameter_value = parameter_value.strip()
            if not normalized_parameter_value:
                raise ExchangeRequestError(
                    "String path parameter values must be non-empty."
                )
            normalized_path_params[normalized_parameter_name] = (
                normalized_parameter_value
            )
            continue

        normalized_path_params[normalized_parameter_name] = parameter_value

    return MappingProxyType(normalized_path_params)


def _normalize_query_params(
    query_params: QueryParameterMapping,
) -> QueryParameterMapping:
    """Normalize query parameters into an immutable mapping."""
    normalized_query_params: dict[str, QueryParameterValue] = {}

    for parameter_name, parameter_value in query_params.items():
        if not isinstance(parameter_name, str):
            raise ExchangeRequestError("Query parameter names must be strings.")

        normalized_parameter_name = parameter_name.strip()
        if not normalized_parameter_name:
            raise ExchangeRequestError("Query parameter names must be non-empty.")

        if not isinstance(parameter_value, (str, int, float, bool)):
            raise ExchangeRequestError(
                "Query parameter values must be str, int, float, or bool."
            )

        if isinstance(parameter_value, str):
            normalized_parameter_value = parameter_value.strip()
            if not normalized_parameter_value:
                raise ExchangeRequestError(
                    "String query parameter values must be non-empty."
                )
            normalized_query_params[normalized_parameter_name] = (
                normalized_parameter_value
            )
            continue

        normalized_query_params[normalized_parameter_name] = parameter_value

    return MappingProxyType(normalized_query_params)


def _normalize_headers(headers: HeaderMapping) -> HeaderMapping:
    """Normalize request headers into an immutable lowercase mapping."""
    normalized_headers: dict[str, str] = {}

    for header_name, header_value in headers.items():
        if not isinstance(header_name, str):
            raise ExchangeRequestError("Exchange request header names must be strings.")

        if not isinstance(header_value, str):
            raise ExchangeRequestError(
                "Exchange request header values must be strings."
            )

        normalized_header_name = header_name.strip().lower()
        normalized_header_value = header_value.strip()

        if not normalized_header_name:
            raise ExchangeRequestError(
                "Exchange request header names must be non-empty."
            )

        normalized_headers[normalized_header_name] = normalized_header_value

    return MappingProxyType(normalized_headers)


def _normalize_timeout_seconds(timeout_seconds: float | None) -> float | None:
    """Normalize and validate an optional timeout override."""
    if timeout_seconds is None:
        return None

    if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)):
        raise ExchangeRequestError(
            "Exchange request timeout must be an int, float, or None."
        )

    normalized_timeout = float(timeout_seconds)
    if normalized_timeout <= 0:
        raise ExchangeRequestError(
            "Exchange request timeout must be greater than zero."
        )

    return normalized_timeout
