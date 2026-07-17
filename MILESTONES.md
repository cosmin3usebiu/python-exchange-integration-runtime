# R003 Milestones: python-exchange-integration-runtime

## Status

This is a recovered draft proposal based on observed implementation evidence.
It does not approve or freeze R003.

R003 approval/freeze state remains unverified. The API is not frozen. Release Phase is not assigned.

Milestone approval is not granted by this file. Observed code and tests are
evidence only.

No milestone is approved or frozen by this file.

## Proposed Milestone 1: Repository Skeleton

Observed evidence:

- Packaging metadata.
- CI workflow.
- Source package layout.
- Test package layout.
- Documentation and example directories.
- `py.typed`.

Acceptance criteria:

- Repository structure exists.
- Package is importable.
- No runtime behavior required.

Status:

- Appears implemented based on observed files.
- Not approved.

## Proposed Milestone 2: Core Package Structure

Observed evidence:

- Package root exports five objects.
- Core modules exist.
- Exception hierarchy exists.
- Internal signing and type modules exist.

Acceptance criteria:

- Minimal package-root exports.
- Internal module structure established.
- No exchange-specific adapters required.

Status:

- Appears implemented based on observed source/tests.
- Not approved.

## Proposed Milestone 3: Endpoint and Request/Response Models

Observed evidence:

- `ExchangeEndpoint`
- `ExchangeRequest`
- `ExchangeResponse`
- Model validation tests.

Acceptance criteria:

- Immutable endpoint metadata.
- Immutable request boundary.
- Immutable response boundary.
- Local structural validation.
- No domain-specific market, trading, order, account, or strategy models.

Status:

- Appears implemented based on observed source/tests.
- Not approved.

## Proposed Milestone 4: Adapter Contracts

Observed evidence:

- `ExchangeAdapter`
- Endpoint registration.
- Endpoint lookup.
- Endpoint ownership validation.
- Optional signer registry.
- Adapter contract tests.

Acceptance criteria:

- Adapter owns endpoints.
- Adapter resolves canonical endpoints.
- Adapter validates signer registry.
- Adapter defines request construction and response interpretation contracts.
- No transport execution.

Status:

- Appears implemented based on observed source/tests.
- Not approved.

## Proposed Milestone 5: Runtime Orchestration

Observed evidence:

- `ExchangeRuntime`
- Runtime collaborator validation.
- Runtime execution tests.

Acceptance criteria:

- Runtime validates collaborators.
- Runtime resolves endpoints through adapter.
- Runtime builds unsigned HTTP requests through adapter.
- Runtime optionally invokes signer.
- Runtime delegates execution to R002 `HttpRuntime`.
- Runtime delegates response interpretation to adapter.
- Runtime validates boundary output types.

Status:

- Appears implemented based on observed source/tests.
- Not approved.

## Proposed Milestone 6: Error Normalization

Observed evidence:

- `ExchangeRuntimeError`
- `AdapterConfigurationError`
- `EndpointResolutionError`
- `RequestSigningError`
- `ExchangeRequestError`
- `ExchangeResponseError`
- Runtime tests for unexpected and repository-native failures.

Acceptance criteria:

- Unexpected endpoint failures normalize to `EndpointResolutionError`.
- Unexpected request construction failures normalize to `ExchangeRequestError`.
- Unexpected signing failures normalize to `RequestSigningError`.
- R002 runtime failures normalize to `ExchangeResponseError`.
- Unexpected response interpretation failures normalize to `ExchangeResponseError`.
- Repository-native errors pass through without losing context.

Status:

- Appears implemented based on observed source/tests.
- Not approved.

## Proposed Milestone 7: Documentation and Release Recovery

Observed evidence:

- README says repository is still Milestone 1.
- Documentation and examples are placeholder-level.
- CHANGELOG is generic.

Acceptance criteria:

- README reflects observed implementation.
- Architecture docs describe runtime, adapter, signing, and R002 boundaries.
- API documentation reflects approved API after review.
- Examples use approved public API only.
- Changelog and release notes align with approved scope.

Status:

- Incomplete.
- Not approved.

## Recovery Status

Proposed milestones 1-6 appear implemented based on observed source/tests but
are not approved.

Proposed milestone 7 is incomplete because documentation, examples, and
changelog remain stale or placeholder-level.

No milestone is approved or frozen by this file.

No concrete adapter, concrete signer, or domain model milestone is approved by
this file.
