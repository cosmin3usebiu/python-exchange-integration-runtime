"""Internal signing contracts for exchange request execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from python_http_runtime import HttpRequest

    from python_exchange_integration_runtime.exchange_request import ExchangeRequest


class RequestSigner(ABC):
    """Define the internal contract for immutable request signing.

    Purpose:
        Standardize how adapters optionally transform an unsigned ``HttpRequest``
        into a new signed request without mutating the original request object.

    Parameters:
        This abstract interface does not define constructor parameters.

    Attributes:
        Concrete implementations own signing-specific state and credentials.

    Raises:
        Concrete implementations may later raise signing-related exceptions.

    Usage Notes:
        This contract is internal. It is not part of the repository's public
        root API.
    """

    @abstractmethod
    def sign(
        self,
        request: HttpRequest,
        exchange_request: ExchangeRequest,
    ) -> HttpRequest:
        """Return a new signed request for one exchange execution.

        Args:
            request: Unsigned immutable HTTP request.
            exchange_request: Higher-level exchange request metadata.

        Returns:
            A new immutable signed HTTP request.

        Raises:
            RequestSigningError: If signing fails or returns an invalid result.
        """
