"""Signing extension contracts for exchange request execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from python_http_runtime import HttpRequest

    from python_exchange_integration_runtime.exchange_request import ExchangeRequest


class RequestSigner(ABC):
    """Define the public submodule contract for immutable request signing.

    Purpose:
        Standardize how adapters optionally transform an unsigned ``HttpRequest``
        into a new signed request without mutating the original request object.

    Parameters:
        This abstract interface does not define constructor parameters.

    Attributes:
        Concrete implementations supplied by adapter code own any
        signing-specific state.

    Raises:
        Concrete implementations may raise signing-related exceptions.

    Usage Notes:
        This contract is a public submodule extension point. It is not exported
        from the package root and does not provide concrete signing algorithms.
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
