"""Exchange adapter contract definitions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING

from python_exchange_integration_runtime.errors import AdapterConfigurationError
from python_exchange_integration_runtime.errors import EndpointResolutionError
from python_exchange_integration_runtime.exchange_endpoint import ExchangeEndpoint
from python_exchange_integration_runtime.signing import RequestSigner

if TYPE_CHECKING:
    from python_http_runtime import HttpRequest
    from python_http_runtime import HttpResponse
    from python_exchange_integration_runtime.exchange_request import ExchangeRequest
    from python_exchange_integration_runtime.exchange_response import ExchangeResponse


class ExchangeAdapter(ABC):
    """Define exchange-specific behavior for the generic runtime.

    Purpose:
        Standardize how exchange-specific request construction, endpoint
        ownership, optional signing, and response interpretation are delegated
        away from the generic runtime orchestrator.

    Parameters:
        name: Stable adapter identifier.
        endpoints: Immutable endpoint metadata owned by the adapter.
        signers: Optional signer registry owned by the adapter.

    Attributes:
        name: Stable adapter identifier.
        endpoints: Immutable endpoint metadata owned by the adapter.

    Raises:
        AdapterConfigurationError: If adapter configuration is structurally
            invalid.

    Usage Notes:
        Adapters should remain stateless where practical and reusable across
        multiple runtime instances.
    """

    def __init__(
        self,
        *,
        name: str,
        endpoints: Iterable[ExchangeEndpoint],
        signers: Mapping[str, RequestSigner] | None = None,
    ) -> None:
        """Normalize and validate adapter-owned collaborators."""
        self._name = _normalize_name(name)
        normalized_endpoints = _normalize_endpoints(endpoints)
        normalized_signers = _normalize_signers(
            signers=signers,
            endpoints=normalized_endpoints,
        )

        self._endpoints = tuple(normalized_endpoints.values())
        self._endpoint_index = MappingProxyType(normalized_endpoints)
        self._signers = MappingProxyType(normalized_signers)

    @property
    def name(self) -> str:
        """Return the stable adapter identifier."""
        return self._name

    @property
    def endpoints(self) -> tuple[ExchangeEndpoint, ...]:
        """Return immutable endpoint metadata in declaration order."""
        return self._endpoints

    def supports_endpoint(self, endpoint: ExchangeEndpoint) -> bool:
        """Return whether the adapter owns and supports the endpoint.

        Args:
            endpoint: Immutable endpoint metadata supplied by the caller.

        Returns:
            ``True`` if the adapter owns the endpoint, otherwise ``False``.
        """
        try:
            self.resolve_endpoint(endpoint)
        except EndpointResolutionError:
            return False

        return True

    def get_endpoint(self, name: str) -> ExchangeEndpoint:
        """Return a registered endpoint by stable logical name.

        Args:
            name: Stable logical endpoint identifier.

        Returns:
            The registered immutable endpoint metadata object.

        Raises:
            EndpointResolutionError: If the endpoint name is unknown.
        """
        normalized_name = _normalize_endpoint_name(name)

        try:
            return self._endpoint_index[normalized_name]
        except KeyError as exc:
            raise EndpointResolutionError(
                f"Adapter '{self.name}' does not define endpoint '{normalized_name}'."
            ) from exc

    def resolve_endpoint(self, endpoint: ExchangeEndpoint) -> ExchangeEndpoint:
        """Resolve and validate an endpoint owned by the adapter.

        Args:
            endpoint: Immutable endpoint metadata supplied by the caller.

        Returns:
            The canonical registered endpoint metadata object.

        Raises:
            EndpointResolutionError: If the endpoint is unsupported or does not
                match the adapter-owned canonical definition.
        """
        if not isinstance(endpoint, ExchangeEndpoint):
            raise EndpointResolutionError(
                "Adapter endpoint resolution requires an ExchangeEndpoint instance."
            )

        registered_endpoint = self.get_endpoint(endpoint.name)
        if endpoint != registered_endpoint:
            raise EndpointResolutionError(
                f"Endpoint '{endpoint.name}' does not match the canonical "
                f"definition owned by adapter '{self.name}'."
            )

        return registered_endpoint

    @abstractmethod
    def build_http_request(self, request: ExchangeRequest) -> HttpRequest:
        """Build an unsigned HTTP request for one exchange execution.

        Args:
            request: Higher-level exchange request metadata.

        Returns:
            An unsigned immutable HTTP request.

        Raises:
            ExchangeRequestError: If the adapter cannot construct a valid HTTP
                request.
        """

    def get_signer(self, endpoint: ExchangeEndpoint) -> RequestSigner | None:
        """Return the optional signer to use for the endpoint.

        Args:
            endpoint: Immutable endpoint metadata supplied by the caller.

        Returns:
            A signer instance when signing is required, otherwise ``None``.
        """
        canonical_endpoint = self.resolve_endpoint(endpoint)
        return self._signers.get(canonical_endpoint.name)

    @abstractmethod
    def interpret_response(
        self,
        request: ExchangeRequest,
        response: HttpResponse,
    ) -> ExchangeResponse:
        """Interpret a raw HTTP response at the exchange boundary.

        Args:
            request: Higher-level exchange request metadata.
            response: Raw immutable HTTP response returned by the lower runtime.

        Returns:
            A stable exchange response object.

        Raises:
            ExchangeResponseError: If the response contract is invalid or
                unsupported.
        """


def _normalize_name(name: str) -> str:
    """Normalize and validate an adapter name."""
    if not isinstance(name, str):
        raise AdapterConfigurationError("Exchange adapter name must be a string.")

    normalized_name = name.strip()
    if not normalized_name:
        raise AdapterConfigurationError("Exchange adapter name must be non-empty.")

    if any(character.isspace() for character in normalized_name):
        raise AdapterConfigurationError(
            "Exchange adapter name must not contain whitespace."
        )

    return normalized_name


def _normalize_endpoints(
    endpoints: Iterable[ExchangeEndpoint],
) -> dict[str, ExchangeEndpoint]:
    """Normalize and validate adapter-owned endpoint metadata."""
    normalized_endpoints: dict[str, ExchangeEndpoint] = {}

    for endpoint in endpoints:
        if not isinstance(endpoint, ExchangeEndpoint):
            raise AdapterConfigurationError(
                "Exchange adapter endpoints must contain ExchangeEndpoint instances."
            )

        if endpoint.name in normalized_endpoints:
            raise AdapterConfigurationError(
                f"Exchange adapter endpoints must not contain duplicate names: "
                f"'{endpoint.name}'."
            )

        normalized_endpoints[endpoint.name] = endpoint

    if not normalized_endpoints:
        raise AdapterConfigurationError(
            "Exchange adapter must define at least one endpoint."
        )

    return normalized_endpoints


def _normalize_signers(
    *,
    signers: Mapping[str, RequestSigner] | None,
    endpoints: Mapping[str, ExchangeEndpoint],
) -> dict[str, RequestSigner]:
    """Normalize and validate the optional signer registry."""
    if signers is None:
        return {}

    normalized_signers: dict[str, RequestSigner] = {}

    for endpoint_name, signer in signers.items():
        normalized_endpoint_name = _normalize_endpoint_name(endpoint_name)

        if normalized_endpoint_name not in endpoints:
            raise AdapterConfigurationError(
                f"Exchange adapter signer registry references unknown endpoint "
                f"'{normalized_endpoint_name}'."
            )

        if not isinstance(signer, RequestSigner):
            raise AdapterConfigurationError(
                "Exchange adapter signers must be RequestSigner instances."
            )

        normalized_signers[normalized_endpoint_name] = signer

    return normalized_signers


def _normalize_endpoint_name(name: str) -> str:
    """Normalize and validate an endpoint name used for adapter lookups."""
    if not isinstance(name, str):
        raise EndpointResolutionError("Endpoint name lookup requires a string.")

    normalized_name = name.strip()
    if not normalized_name:
        raise EndpointResolutionError("Endpoint name lookup requires a non-empty name.")

    if any(character.isspace() for character in normalized_name):
        raise EndpointResolutionError(
            "Endpoint names used for lookup must not contain whitespace."
        )

    return normalized_name
