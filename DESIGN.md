# R003 Design: python-exchange-integration-runtime

## Status

This is a recovered draft proposal based on observed implementation evidence.
It does not approve or freeze R003.

R003 approval/freeze state remains unverified. The API is not frozen. Release Phase is not assigned.

This design is not yet approved.

## Purpose

R003 provides a generic exchange integration runtime built above
`python-http-runtime`.

The repository coordinates exchange-style request execution while delegating
exchange-specific behavior to adapters and HTTP execution to R002.

## Scope

R003 owns:

- Exchange runtime orchestration.
- Exchange adapter contract.
- Immutable exchange endpoint metadata.
- Immutable exchange request boundary.
- Immutable exchange response boundary.
- Endpoint ownership and canonical endpoint resolution through adapters.
- Optional internal signing pipeline.
- Repository-native exchange runtime exceptions.
- Normalization of runtime, adapter, signing, request, and response failures.

## Non-Goals

R003 does not own:

- HTTP transport implementation.
- HTTP middleware policies owned by R002.
- Concrete exchange adapters.
- Exchange endpoint catalogs.
- Concrete signing implementations.
- Market-data models.
- Metadata models.
- Order, trade, account, balance, or position models.
- Dataset persistence.
- Caching.
- WebSocket connectivity.
- Trading logic.
- Strategy logic.
- Application orchestration.

## Architecture Boundaries

Boundary models:

- `exchange_endpoint.py`
- `exchange_request.py`
- `exchange_response.py`

Adapter layer:

- `adapter.py`

Runtime layer:

- `runtime.py`

Internal signing layer:

- `signing.py`

Error layer:

- `errors.py`

Shared typing layer:

- `types.py`

## Dependency Policy

R003 depends on `python-http-runtime`.

R003 must not bypass R002 for HTTP execution.

R003 must remain independent of downstream repositories such as market-data
downloaders, metadata services, dataset pipelines, indicator engines, trading
systems, or applications.

Downstream requirements must not silently redefine R003 scope.

## Public / Private Module Boundary

The observed package-root public API is:

- `ExchangeRuntime`
- `ExchangeAdapter`
- `ExchangeRequest`
- `ExchangeResponse`
- `ExchangeEndpoint`

Repository-native errors and `RequestSigner` are observed implementation
components and require explicit review before any public API freeze.

Request signing is optional and requires explicit review before any public API
freeze.

## Exchange Runtime Model

`ExchangeRuntime` is an orchestrator only.

It coordinates:

1. `ExchangeRequest`
2. adapter endpoint resolution
3. canonical request rebuilding
4. adapter HTTP request construction
5. optional signing
6. R002 `HttpRuntime` execution
7. adapter response interpretation
8. `ExchangeResponse`

The runtime must not own exchange-specific endpoint catalogs, signing
algorithms, response schemas, or domain models.

## Adapter Boundary

`ExchangeAdapter` owns exchange-specific behavior:

- endpoint registry
- endpoint lookup
- endpoint ownership enforcement
- unsigned HTTP request construction
- optional signer lookup
- HTTP response interpretation

Adapters should remain stateless where practical.

Exchange-specific behavior is delegated to adapters.

## Signing Boundary

Signing is an optional internal pipeline stage.

Unsigned `HttpRequest` enters a signer; a new signed `HttpRequest` is returned.

Signing must not mutate existing request objects.

Concrete signing implementations are not approved by this design.

## HTTP Runtime Boundary

R003 delegates all HTTP execution to R002.

R003 should not implement transports, retries, rate limits, authentication
middleware, or response decoding owned by R002.

## Validation And Error-Handling Expectations

R003 should fail fast on invalid collaborators, invalid boundary objects,
invalid adapter outputs, invalid signer outputs, and invalid response
interpretation outputs.

Repository-native exceptions should preserve original exception context when
normalizing unexpected failures.

## Known Incomplete Or Deferred Capabilities

Observed deferred or absent capabilities:

- no concrete exchange adapter
- no endpoint catalog
- no concrete signing implementation
- no market-data models
- no metadata models
- no order, trade, account, balance, or position models
- no dataset persistence
- no live exchange examples
- stale README, documentation, examples, and changelog
- clean CI dependency-resolution risk if `python-http-runtime` is not resolvable

## Evidence Limitations

This design is recovered from observed source, tests, metadata, and stale
documentation.

Source and tests are implementation evidence, not approval evidence.

This document does not approve R003, freeze R003, freeze the API, assign Release
Phase, approve milestones, or declare release readiness.
