"""Exception hierarchy for the exchange integration runtime."""

from __future__ import annotations


class ExchangeRuntimeError(Exception):
    """Base exception for exchange integration runtime failures.

    Purpose:
        Provide a stable repository-level root exception for failures that
        occur while integrating exchange-style HTTP APIs through this runtime.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This class serves as the repository root exception and is not raised
        directly for normal operational categories.

    Usage Notes:
        More specific configuration, resolution, signing, request, and response
        failures derive from this base type.
    """


class AdapterConfigurationError(ExchangeRuntimeError):
    """Describe invalid adapter configuration or collaborator state.

    Purpose:
        Reserve a category for invalid adapter setup, incompatible
        collaborators, or misconfigured runtime construction state.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This exception will later be raised when runtime construction or
        execution detects invalid adapter-level configuration.

    Usage Notes:
        Adapter configuration failures are distinct from endpoint, signing, and
        exchange response failures.
    """


class EndpointResolutionError(ExchangeRuntimeError):
    """Describe invalid or unsupported endpoint resolution.

    Purpose:
        Reserve a category for unsupported endpoints, invalid endpoint
        ownership, or other endpoint-resolution failures at runtime boundaries.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This exception will later be raised when adapters reject or cannot
        resolve an endpoint.

    Usage Notes:
        Endpoint failures are modeled separately from request signing and
        exchange response handling.
    """


class RequestSigningError(ExchangeRuntimeError):
    """Describe failures produced during request signing.

    Purpose:
        Normalize failures that occur while transforming an unsigned
        ``HttpRequest`` into a signed immutable request.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This exception will later wrap signer contract violations and
        exchange-specific signing failures.

    Usage Notes:
        Original signing exceptions should be preserved as chained context.
    """


class ExchangeRequestError(ExchangeRuntimeError):
    """Describe failures while constructing or dispatching exchange requests.

    Purpose:
        Reserve a category for invalid exchange request execution boundaries
        that are not endpoint-resolution failures and not response failures.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This exception will later be raised when request construction or
        transport delegation violates runtime contracts.

    Usage Notes:
        Request failures are distinct from signing and remote response
        interpretation failures.
    """


class ExchangeResponseError(ExchangeRuntimeError):
    """Describe failures while interpreting exchange HTTP responses.

    Purpose:
        Reserve a category for malformed, unsupported, or contract-violating
        exchange responses surfaced by adapters.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        This exception will later be raised when adapters cannot interpret raw
        HTTP responses into a stable ``ExchangeResponse`` boundary object.

    Usage Notes:
        Response failures are intentionally modeled separately from transport
        and request-construction failures.
    """
