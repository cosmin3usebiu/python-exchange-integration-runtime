"""Basic repository smoke tests for the core package structure."""

from importlib import import_module


def test_package_can_be_imported() -> None:
    """Verify that the package namespace is available."""
    module = import_module("python_exchange_integration_runtime")
    assert module is not None


def test_public_exports_are_available() -> None:
    """Verify that the stable public object model is exported."""
    module = import_module("python_exchange_integration_runtime")
    assert hasattr(module, "ExchangeAdapter")
    assert hasattr(module, "ExchangeEndpoint")
    assert hasattr(module, "ExchangeRequest")
    assert hasattr(module, "ExchangeResponse")
    assert hasattr(module, "ExchangeRuntime")


def test_public_exports_remain_minimal() -> None:
    """Verify that only the approved public API is exported."""
    module = import_module("python_exchange_integration_runtime")
    assert module.__all__ == [
        "ExchangeRuntime",
        "ExchangeAdapter",
        "ExchangeRequest",
        "ExchangeResponse",
        "ExchangeEndpoint",
    ]


def test_internal_modules_can_be_imported() -> None:
    """Verify that the expected package modules exist."""
    module_names = (
        "python_exchange_integration_runtime.adapter",
        "python_exchange_integration_runtime.errors",
        "python_exchange_integration_runtime.exchange_endpoint",
        "python_exchange_integration_runtime.exchange_request",
        "python_exchange_integration_runtime.exchange_response",
        "python_exchange_integration_runtime.runtime",
        "python_exchange_integration_runtime.signing",
        "python_exchange_integration_runtime.types",
    )

    for module_name in module_names:
        assert import_module(module_name) is not None


def test_internal_signing_contract_is_not_exported() -> None:
    """Verify internal signing contracts remain outside the package root."""
    module = import_module("python_exchange_integration_runtime")
    assert not hasattr(module, "RequestSigner")
