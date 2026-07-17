# R003 Decisions: python-exchange-integration-runtime

## Status

This is a recovered draft proposal based on observed implementation evidence.
It does not approve or freeze R003.

R003 approval/freeze state remains unverified. The API is not frozen. Release Phase is not assigned.

All decisions in this file are proposed and unapproved unless explicitly stated
otherwise.

## Decisions To Ratify

### DEC-R003-001: R003 Owns Exchange Runtime Orchestration

Decision to ratify:

R003 owns generic exchange request orchestration above R002.

Evidence:

Observed `ExchangeRuntime` coordinates adapter resolution, request construction,
signing, R002 execution, and response interpretation.

Status:

Proposed, not approved.

### DEC-R003-002: R003 Depends On R002 For HTTP Execution

Decision to ratify:

R003 must delegate HTTP execution to `python-http-runtime` and must not
implement transports or HTTP middleware behavior.

Evidence:

`pyproject.toml` declares `python-http-runtime`; runtime imports and uses R002
`HttpRuntime`.

Status:

Proposed, not approved.

### DEC-R003-003: ExchangeAdapter Owns Exchange-Specific Behavior

Decision to ratify:

Adapters own endpoint definitions, endpoint ownership checks, request
construction, signer lookup, and response interpretation.

Evidence:

Observed `ExchangeAdapter` implementation and adapter contract tests.

Status:

Proposed, not approved.

### DEC-R003-004: ExchangeEndpoint Is Immutable Metadata

Decision to ratify:

`ExchangeEndpoint` should remain immutable metadata and should not contain
execution behavior.

Evidence:

Observed frozen dataclass and endpoint model tests.

Status:

Proposed, not approved.

### DEC-R003-005: ExchangeRequest Remains HTTP-Oriented And Business-Neutral

Decision to ratify:

`ExchangeRequest` should remain generic and should not include market-data,
trading, order, account, or strategy concepts.

Evidence:

Observed request fields are endpoint, path parameters, query parameters,
headers, body, and timeout.

Status:

Proposed, not approved.

### DEC-R003-006: Signing Is An Optional Internal Pipeline Stage

Decision to ratify:

Signing transforms an unsigned immutable `HttpRequest` into a new signed
immutable `HttpRequest`.

Evidence:

Observed `RequestSigner` contract and runtime signing tests.

Status:

Proposed, not approved.

### DEC-R003-007: Public API Remains Minimal

Decision to ratify:

Package-root public API should remain limited to core runtime, adapter, and
boundary concepts unless expansion is explicitly approved.

Evidence:

Observed `__all__` exports exactly five objects.

Status:

Proposed, not approved.

## Open Decisions

- Whether repository-native exchange error classes should become package-root
  public API.
- Whether `RequestSigner` should remain internal or become public extension API.
- Whether concrete exchange adapters belong in R003 or downstream repositories.
- Whether concrete signing implementations belong in R003 or adapter-specific
  packages.
- Whether R003 should enter Release Phase after artifact recovery or require
  additional code work.
- Whether CI dependency installation risk should be addressed before release
  recovery.

## Evidence Limitations

Source and tests provide implementation evidence. They do not prove prior
approval, API freeze, milestone approval, or release readiness.

README and documentation are stale and should not be treated as authoritative
where they conflict with source/tests.

This file does not approve R003, freeze R003, freeze the API, assign Release
Phase, approve milestones, or declare release readiness.
