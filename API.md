# R003 API: python-exchange-integration-runtime

## Status

This is a recovered draft proposal based on observed implementation evidence.
It does not approve or freeze R003.

R003 approval/freeze state remains unverified. The API is not frozen. Release Phase is not assigned.

Current `__all__` is observed implementation evidence, not a frozen public
contract.

Any future API freeze requires explicit review and approval.

## Observed Public Exports

Package-root `__all__` exports:

- `ExchangeRuntime`
- `ExchangeAdapter`
- `ExchangeRequest`
- `ExchangeResponse`
- `ExchangeEndpoint`

## Proposed Classification: Core Public API

- `ExchangeRuntime`
- `ExchangeAdapter`
- `ExchangeRequest`
- `ExchangeResponse`
- `ExchangeEndpoint`

## Proposed Classification: Public But Requires Review

- `ExchangeRuntimeError`
- `AdapterConfigurationError`
- `EndpointResolutionError`
- `RequestSigningError`
- `ExchangeRequestError`
- `ExchangeResponseError`
- `RequestSigner`

## Proposed Classification: Internal Implementation Candidates

- `HeaderMapping`
- `QueryParameterMapping`
- `PathParameterMapping`
- `QueryParameterValue`
- `PathParameterValue`
- `PayloadType`
- runtime helper functions
- endpoint/request/response normalization helpers

## Known API Caveats

Errors and signing contracts are implemented but are not package-root exports.

`RequestSigner` is explicitly documented in source as internal.

No concrete exchange adapter is exported.

No concrete signing implementation is exported.

No market-data, metadata, order, trade, account, balance, position, dataset, or
strategy model is exported.

## API Freeze Status

The API is not frozen.

This file does not approve R003, freeze R003, assign Release Phase, approve any
milestone, or declare release readiness.
