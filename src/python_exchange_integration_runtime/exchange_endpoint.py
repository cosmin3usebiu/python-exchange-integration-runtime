"""Exchange endpoint object definitions."""

from __future__ import annotations

from dataclasses import dataclass

from python_exchange_integration_runtime.errors import AdapterConfigurationError


@dataclass(slots=True, frozen=True, kw_only=True)
class ExchangeEndpoint:
    """Describe immutable metadata for one exchange endpoint.

    Purpose:
        Provide a stable metadata object that identifies one exchange endpoint
        without embedding request construction or execution behavior.

    Parameters:
        name: Stable logical endpoint identifier owned by one adapter.
        method: HTTP method associated with the endpoint.
        path: Relative path template associated with the endpoint.
        requires_auth: Whether the endpoint requires signing or authentication.
        version: Optional exchange API version label.
        content_type: Optional request content type declaration.

    Attributes:
        name: Stable logical endpoint identifier.
        method: HTTP method associated with the endpoint.
        path: Relative path template associated with the endpoint.
        requires_auth: Whether the endpoint requires signing.
        version: Optional exchange API version label.
        content_type: Optional request content type declaration.

    Raises:
        AdapterConfigurationError: If endpoint metadata is structurally
            invalid.

    Usage Notes:
        Validation and metadata normalization are intentionally deferred to a
        later milestone.
    """

    name: str
    method: str
    path: str
    requires_auth: bool = False
    version: str | None = None
    content_type: str | None = None

    def __post_init__(self) -> None:
        """Normalize and validate immutable endpoint metadata."""
        object.__setattr__(self, "name", _normalize_name(self.name))
        object.__setattr__(self, "method", _normalize_method(self.method))
        object.__setattr__(self, "path", _normalize_path(self.path))
        object.__setattr__(
            self,
            "requires_auth",
            _normalize_requires_auth(self.requires_auth),
        )
        object.__setattr__(self, "version", _normalize_optional_text(self.version))
        object.__setattr__(
            self,
            "content_type",
            _normalize_optional_text(self.content_type),
        )


def _normalize_name(name: str) -> str:
    """Normalize and validate an endpoint name."""
    if not isinstance(name, str):
        raise AdapterConfigurationError("Exchange endpoint name must be a string.")

    normalized_name = name.strip()
    if not normalized_name:
        raise AdapterConfigurationError("Exchange endpoint name must be non-empty.")

    if any(character.isspace() for character in normalized_name):
        raise AdapterConfigurationError(
            "Exchange endpoint name must not contain whitespace."
        )

    return normalized_name


def _normalize_method(method: str) -> str:
    """Normalize and validate an endpoint HTTP method."""
    if not isinstance(method, str):
        raise AdapterConfigurationError("Exchange endpoint method must be a string.")

    normalized_method = method.strip().upper()
    if not normalized_method:
        raise AdapterConfigurationError("Exchange endpoint method must be non-empty.")

    if any(character.isspace() for character in normalized_method):
        raise AdapterConfigurationError(
            "Exchange endpoint method must not contain whitespace."
        )

    return normalized_method


def _normalize_path(path: str) -> str:
    """Normalize and validate an endpoint path template."""
    if not isinstance(path, str):
        raise AdapterConfigurationError("Exchange endpoint path must be a string.")

    normalized_path = path.strip()
    if not normalized_path:
        raise AdapterConfigurationError("Exchange endpoint path must be non-empty.")

    if any(character.isspace() for character in normalized_path):
        raise AdapterConfigurationError(
            "Exchange endpoint path must not contain whitespace."
        )

    if not normalized_path.startswith("/"):
        raise AdapterConfigurationError(
            "Exchange endpoint path must start with '/'."
        )

    lowercase_path = normalized_path.lower()
    if lowercase_path.startswith("http://") or lowercase_path.startswith("https://"):
        raise AdapterConfigurationError(
            "Exchange endpoint path must be relative and must not be an absolute URL."
        )

    return normalized_path


def _normalize_requires_auth(requires_auth: bool) -> bool:
    """Normalize and validate the endpoint auth requirement flag."""
    if not isinstance(requires_auth, bool):
        raise AdapterConfigurationError(
            "Exchange endpoint requires_auth flag must be a boolean."
        )

    return requires_auth


def _normalize_optional_text(value: str | None) -> str | None:
    """Normalize and validate an optional text metadata field."""
    if value is None:
        return None

    if not isinstance(value, str):
        raise AdapterConfigurationError(
            "Optional endpoint metadata values must be strings or None."
        )

    normalized_value = value.strip()
    if not normalized_value:
        raise AdapterConfigurationError(
            "Optional endpoint metadata values must be non-empty when set."
        )

    return normalized_value
