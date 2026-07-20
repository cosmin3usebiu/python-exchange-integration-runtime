"""Public submodule error contracts for the exchange integration runtime."""

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
        failures derive from this base type. Repository-native errors are
        public submodule contracts and are not package-root exports.
    """


class AdapterConfigurationError(ExchangeRuntimeError):
    """Describe invalid adapter configuration or collaborator state.

    Purpose:
        Represent invalid adapter setup, incompatible collaborators, or
        misconfigured runtime construction state.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        Runtime construction and execution raise this exception when
        adapter-level configuration is invalid.

    Usage Notes:
        Adapter configuration failures are distinct from endpoint, signing, and
        exchange response failures.
    """


class EndpointResolutionError(ExchangeRuntimeError):
    """Describe invalid or unsupported endpoint resolution.

    Purpose:
        Represent unsupported endpoints, invalid endpoint ownership, or other
        endpoint-resolution failures at runtime boundaries.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        Adapter and runtime boundaries raise this exception when endpoint
        resolution fails.

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
        Runtime signing boundaries raise this exception for signer contract
        violations and signing failures.

    Usage Notes:
        Original signing exceptions should be preserved as chained context.
    """


class ExchangeRequestError(ExchangeRuntimeError):
    """Describe failures while constructing or dispatching exchange requests.

    Purpose:
        Represent invalid exchange request execution boundaries that are not
        endpoint-resolution failures and not response failures.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        Adapter and runtime boundaries raise this exception when request
        construction or transport delegation violates runtime contracts.

    Usage Notes:
        Request failures are distinct from signing and remote response
        interpretation failures.
    """


class ExchangeResponseError(ExchangeRuntimeError):
    """Describe failures while interpreting exchange HTTP responses.

    Purpose:
        Represent malformed, unsupported, or contract-violating exchange
        responses surfaced by adapters.

    Parameters:
        This exception accepts the standard ``Exception`` initialization
        arguments only.

    Attributes:
        No additional public attributes are defined.

    Raises:
        Adapter and runtime boundaries raise this exception when raw HTTP
        responses cannot be interpreted into a stable ``ExchangeResponse``
        boundary object.

    Usage Notes:
        Response failures are intentionally modeled separately from transport
        and request-construction failures.
    """
