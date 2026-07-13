# Error Handling Standards

> How every system classifies, represents, propagates, retries, and recovers from failure — the sole home for error taxonomy, boundaries, and never-swallow rules.

**ID** `error_handling` · **Tier** Core · **Version** 1.0
**Owns** error taxonomy · error-as-data vs exceptions · result types · propagation + boundary placement · retry/backoff/timeout/circuit-breaker · partial failure · recovery + degradation · validation-error structure · internal vs user reporting · never-swallow rules
**Defers to** layer/tier model → [architecture](../architecture/STANDARDS.md) · input-validation boundary + info-exposure → [security](../security/STANDARDS.md) · structured log format + SLO/error-budget math → [observability](../observability/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [security](../security/STANDARDS.md) · [observability](../observability/STANDARDS.md)

---

## Table of Contents

1. [Classification](#1-classification)
2. [Representation & Result Types](#2-representation--result-types)
3. [Propagation & Boundaries](#3-propagation--boundaries)
4. [Error Messages](#4-error-messages)
5. [Retry, Backoff, Timeouts & Circuit Breakers](#5-retry-backoff-timeouts--circuit-breakers)
6. [Partial Failure](#6-partial-failure)
7. [Recovery & Degradation](#7-recovery--degradation)
8. [Validation Errors](#8-validation-errors)
9. [Logging & Reporting](#9-logging--reporting)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Classification

Four categories. Every error maps to exactly one. Category determines strategy.

| Category | Definition | Examples | Strategy |
|---|---|---|---|
| Programmer error | Bug — violated invariant, unreachable state | Index out of bounds · null deref · type mismatch · failed assertion | Crash immediately · fix code · ✗ catch or retry |
| Data error | Invalid, malformed, or unexpected input | Missing required field · schema violation · out-of-range value · corrupt payload | Return error in result · ✗ throw · caller decides |
| Environment error | External system failure | Connection refused · timeout · disk full · permission denied · DNS failure | Raise/throw · supervisor handles · retry if idempotent |
| Partial failure | Some items succeed, some fail in a batch | 3 of 10 records fail validation · 1 API call in batch times out | Accumulate all errors · continue · report complete results |

### Classification Rules

- Unknown errors default to environment error until diagnosed.
- Programmer errors are ✗ caught in production — they crash. Catching masks bugs.
- Data errors ✗ crash the system — bad input is expected at runtime.
- Environment errors are transient until proven permanent.
- Partial failures are ✗ treated as full failures — surviving items proceed.

### Fatal vs Recoverable

Every error is also fatal or recoverable — this decides crash vs continue.

| Condition | Class | Action |
|---|---|---|
| Invariant violated / corrupt internal state | Fatal | Crash — continuing risks data corruption |
| Required config missing at startup | Fatal | Crash before serving requests |
| Schema incompatible with code | Fatal | Crash at startup |
| Out of memory · stack overflow | Fatal | Crash — cannot recover |
| Network timeout · dependency error | Recoverable | Retry with backoff or degrade |
| Invalid user input | Recoverable | Return validation errors |
| Expected file missing · rate limit · disk full on write | Recoverable | Return error · back off · retry · alert |

Decision: (1) can the process continue without data corruption? No → fatal. (2) Caused by a code bug? Yes → fatal. (3) Missing precondition for the whole process? Yes → fatal. (4) Recovery possible within bounded time? No → fatal. (5) Else → recoverable.

- Fatal → crash with non-zero exit code; log full state (stack trace, variables, config snapshot) before exit.
- ✗ catch fatal errors in application code — only crash handlers and supervisors catch them. Crash handler runs cleanup, ✗ attempts recovery.
- Recoverable → propagate via result types or controlled exceptions; bounded attempt count + time budget; log at `warn` (handled), not `error`.

---

## 2. Representation & Result Types

Two mechanisms. Each has one correct use — mixing them creates ambiguity.

| Mechanism | Use when | Tier affinity |
|---|---|---|
| Error as data (result type) | Failure is expected, part of normal flow | Tier 0–1 (logic) |
| Exception / raise / throw | Failure is unexpected, environment disruption | Tier 3 (interface) |

| Condition | Mechanism |
|---|---|
| Caller can reasonably handle the error immediately | Error as data |
| Error crosses a tier boundary upward | Error as data |
| Multiple errors possible in one operation | Error as data (accumulate) |
| External system failure (I/O, network, disk) | Exception |
| Unrecoverable invariant violation | Exception (crash) |
| Validation failure | Error as data |

### Structural Requirements

Every error — returned or thrown — carries:

| Field | Required | Purpose |
|---|---|---|
| Error code | Yes | Machine-readable, stable across versions |
| Message | Yes | Human-readable, developer-facing |
| Category | Yes | One of the four (§1) |
| Context | Yes | Key-value: operation, input summary, relevant IDs |
| Source | No | Module/function that originated the error |
| Cause | No | Wrapped inner error if translated at a boundary |

- Error codes are strings: `DOMAIN.CATEGORY.SPECIFIC` (e.g. `PAYMENT.DATA.INVALID_AMOUNT`).
- Error codes ✗ change once published — they are part of the contract.
- Error messages ✗ contain sensitive data (credentials, PII, internal paths) → [security §11](../security/STANDARDS.md).

### Result Types

| Variant | Contains | When |
|---|---|---|
| Success | Data payload | Completed without error |
| Failure | Error (or list of errors) | Operation failed |

- Result types are the **default** return for Tier 0–1 functions that can fail.
- Caller ✗ access success data without first checking for failure.
- ✗ use null/nil/None to represent failure — use the explicit failure variant.
- Functions that cannot fail return plain values (no wrapper).
- Nested results (Result inside Result) indicate a missing boundary translation — flatten.

### Batch Results

| Field | Purpose |
|---|---|
| `succeeded` | List of (item, output) |
| `failed` | List of (item, error) |
| `total` · `success_count` · `failure_count` | Counts |

- Batch is a success if `failure_count == 0`.
- Batch ✗ treated as full failure when `success_count > 0` — partial success is valid.

---

## 3. Propagation & Boundaries

Errors propagate outward (upward): Tier 0 → 1 → 2 → 3 → caller. ✗ propagate inward toward lower tiers. Boundary placement follows the layer model → [architecture §2](../architecture/STANDARDS.md).

### Tier Behavior

| Tier | On error | Action |
|---|---|---|
| 0 (Kernel) | Return error in result | ✗ catch · ✗ log · ✗ retry |
| 1 (Engine) | Return error in result | ✗ catch · ✗ log · may enrich context |
| 2 (Service) | Catch domain errors | Translate to structured result · decide retry · accumulate partial failures |
| 3 (Interface) | Catch environment errors | Translate to user-facing message · log · trigger recovery |

### Boundary & Translation Rules

Errors are translated at each boundary — never passed raw across tiers.

| Boundary | Between | Translation |
|---|---|---|
| Tier | Tier N → N+1 | Preserve or wrap with domain context |
| Module | Module A → B | Don't leak implementation details |
| System | Internal → external caller | Map to protocol format (HTTP status, exit code, error response) |
| Async | Producer → consumer | Serialize error for cross-process/thread transport |

- Original error preserved as `cause` — full chain available for debugging. ✗ lose the original when translating; wrap, don't replace.
- Every boundary has exactly one handler — ✗ duplicate catch blocks at the same boundary.
- Handlers catch **specific** error types — ✗ catch-all without re-raise.
- Catch-all at the outermost boundary (Tier 3 entry point) is **required** — prevents unhandled crashes leaking to the user.
- Caught errors are translated, not swallowed. Swallowed error = hidden bug (§10).
- ✗ expose internal codes or stack traces to external callers → [security §11](../security/STANDARDS.md).

---

## 4. Error Messages

Two audiences, generated at different tiers.

| Audience | Content | Where generated |
|---|---|---|
| Developer | Technical detail · variable state · error chain | Tier 0–2 (internal) |
| User | What happened · what to do next | Tier 3 (translated at boundary) |

### Developer-Facing

| Rule | Detail |
|---|---|
| State what failed | `"Failed to parse configuration file"` — not `"Error"` |
| Discriminating context | Operation · input identifier · expected vs actual |
| ✗ sensitive data | No credentials · no PII · no full paths beyond project root |
| ✗ duplicate the code | Message adds information the code does not carry |
| Present tense | `"Connection refused"` — not `"Connection was refused"` |

### User-Facing

| Rule | Detail |
|---|---|
| State what happened | Plain language, no jargon |
| State what to do | Actionable next step or "contact support" as last resort |
| ✗ expose internals | No stack traces · no error codes · no module names |
| ✗ blame the user | `"File not found"` — not `"You provided an invalid file"` |
| Include request ID | If applicable — lets the user reference it when reporting |

Templates — developer: `"{operation} failed: {reason} [context: {k}={v}]"` · user: `"{what_happened}. {what_to_do}."`

---

## 5. Retry, Backoff, Timeouts & Circuit Breakers

Retry transient environment errors with discipline. ✗ retry programmer or data errors.

### Preconditions

| Condition | Required |
|---|---|
| Operation is idempotent | Yes — ✗ retry non-idempotent operations without an idempotency key |
| Error is an environment error | Yes |
| Error is transient (not permanent) | Yes — permanent errors fail immediately |
| Max retry count defined | Yes — ✗ retry indefinitely |
| Total timeout budget defined | Yes — total time across all retries is bounded |

Idempotency keys make retries safe for non-idempotent writes — caller supplies a stable key; server deduplicates.

### Backoff

| Pattern | Formula | Use when |
|---|---|---|
| Exponential + full jitter | `random(0, min(max_delay, base * 2^attempt))` | Default for all retries |
| Fixed delay | `constant` | Only when server sends `Retry-After` |
| Immediate (1 retry) | `0` delay, single retry | Local transient failures (file lock) |

- **Full jitter is mandatory** on exponential backoff — prevents synchronized retry storms.
- ✗ linear backoff — creates thundering herd on shared resources.

| Parameter | Default | Range |
|---|---|---|
| Max retries | 3 | 1–5 interactive · up to 10 batch/background |
| Base delay | 1 s | 100 ms–5 s |
| Max delay | 30 s | Per-retry cap |
| Total timeout | 60 s | Hard cap for the whole sequence |

### Timeouts & Deadlines

| Rule | Detail |
|---|---|
| Every external call has a timeout | ✗ unbounded waits |
| Propagate deadlines | Pass remaining budget downstream; a callee ✗ exceed the caller's deadline |
| Deadline over per-hop timeout | Total request deadline governs; ✗ let stacked per-hop timeouts exceed it |
| Fail fast when budget spent | Deadline exceeded → abort, ✗ start new work |

### Circuit Breaker

| State | Behavior |
|---|---|
| Closed (normal) | Requests pass; failure counter increments on error |
| Open (tripped) | Requests fail immediately with circuit-open error; ✗ attempt call |
| Half-open (probing) | One probe allowed; success → close · failure → re-open |

| Parameter | Default |
|---|---|
| Failure threshold to open | 5 consecutive failures |
| Cooldown before half-open | 30 s |
| Success threshold to close | 1 successful probe |

- Circuit state is per-dependency, not global. Circuit-open error is an environment error — propagates as such.
- Exhausted retries on a non-recoverable async message → **dead-letter queue**; ✗ drop silently, ✗ block the queue.

---

## 6. Partial Failure

Batch operations process all items — ✗ stop on first error.

### Accumulation

1. Initialize empty success list and error list.
2. Process each item independently.
3. Success → append to success list with output.
4. Failure → append to error list with item identifier + error. Continue.
5. Return the batch result (§2) containing both lists.

| Rule | Detail |
|---|---|
| Independence | Each item processed in isolation — one failure ✗ affects others |
| Error identity | Every error linked to its source item — ✗ orphaned errors |
| Ordering preserved | Success/failure lists keep original input order |
| Threshold abort | Optional: stop after N% failure rate — but still report accumulated results |
| Transactional items | Multi-step item → item-level rollback on failure |

- Result includes per-item status, not just counts. Caller can retry only failed items.
- Failed items carry full error detail — ✗ generic "some items failed."

---

## 7. Recovery & Degradation

Goal: continue operating at reduced capability rather than crash. Tie degraded state to SLO error budgets → [observability §9](../observability/STANDARDS.md).

### Graceful Degradation

| Scenario | Response |
|---|---|
| Non-critical dependency unavailable | Disable dependent feature · continue core |
| Cache unavailable | Bypass cache · serve from origin |
| Secondary data source fails | Serve incomplete data · flag what is missing |
| Rate limit exceeded | Queue · throttle · serve cached response |
| Config source unavailable | Use last-known-good config · log warning |

| Rule | Detail |
|---|---|
| Fallback is pre-defined | Every external dependency has a declared fallback before production |
| Fallback is tested | Fallback paths tested the same as primary paths |
| Fallback is visible | System reports degraded state — ✗ silently serve degraded response |
| Fallback has limits | Degraded mode has its own timeout — ✗ degrade indefinitely without alerting |

### Cleanup & Resource Release

| Principle | Rule |
|---|---|
| Deterministic cleanup | Every acquired resource released on success AND failure paths |
| Reverse order | Resources released in reverse acquisition order |
| Cleanup ✗ throws | Cleanup code ✗ raises new errors — log and continue releasing |
| Scope-bound | Resource lifetime tied to scope — released when scope exits |
| Partial-operation cleanup | Failed multi-step operation rolls back completed steps |

### Supervisor Pattern

| Component | Role |
|---|---|
| Worker | Performs operation · reports errors upward · ✗ decides recovery |
| Supervisor | Monitors workers · decides restart/skip/escalate · owns recovery policy |

- Worker crashes → supervisor restarts with clean state.
- Max restart attempts: **3 within 60 s**. Exceeding → escalate to parent supervisor or halt; ✗ restart loop.

---

## 8. Validation Errors

Input validation produces data errors — returned as structured results, ✗ thrown. The validation boundary (where untrusted input is checked) is owned by [security §2](../security/STANDARDS.md); this section owns the error structure and codes.

| Validation type | Where | Tier |
|---|---|---|
| Schema (structure, types) | Entry point — first contact with external data | 3 |
| Business rule (domain constraints) | Engine — domain logic | 1 |
| Cross-field (interdependencies) | Engine — after individual fields | 1 |
| Referential (existence, needs I/O) | Service — orchestrates lookup + validation | 2–3 |

- Validate all fields — ✗ stop at first invalid field. Collect all violations.
- Schema validation runs before business-rule validation — reject structurally invalid data early.
- ✗ validate inside Tier 0 — types enforce structure via the type system, not runtime checks.

### Field Error Structure

| Field | Purpose |
|---|---|
| `path` | Dot-notation to invalid field: `"address.zip_code"` |
| `code` | Machine-readable code (see below) |
| `message` | Human-readable description |
| `constraint` | Expected constraint: `"min: 1, max: 100"` |
| `actual` | Actual value received (omit if sensitive) |

Standard codes: `REQUIRED` · `INVALID_FORMAT` · `OUT_OF_RANGE` · `INVALID_TYPE` · `TOO_LONG` · `TOO_SHORT` · `NOT_UNIQUE` · `INVALID_REFERENCE` · `IMMUTABLE` · `DEPENDENCY`.

---

## 9. Logging & Reporting

What to log, at which level. Structured log format and fields → [observability](../observability/STANDARDS.md).

| Log | ✗ Don't log |
|---|---|
| All environment errors | Expected data-validation failures (unless aggregated) |
| Circuit-breaker state transitions | Successful operations (unless an audit trail requires it) |
| Recovery actions (fallback, retry) | Programmer errors in production (crash + stack trace suffices) |
| Partial-failure summaries (N ok, M failed) | Raw input containing PII/secrets |
| Escalations (worker → supervisor) | Duplicate entries for the same error at multiple layers |

### Log Level by Category

| Situation | Level |
|---|---|
| Programmer error | `error` (captured by crash handler) |
| Data error (single) | `warn` (or `debug` if high volume) |
| Environment error | `error` |
| Environment error recovered via retry | `warn` |
| Circuit breaker opened | `error` |
| Circuit breaker closed (recovered) | `info` |
| Graceful degradation activated | `warn` |

- Log once per error, at the boundary where it is handled — ✗ log the same error at multiple tiers.
- Include the full cause chain in the structured log — ✗ log only the outermost message.
- ✗ log and rethrow without marking the error already logged — prevents duplicate logging.
- Aggregate repeated identical errors — log a count per window, not every occurrence.

---

## 10. Anti-Patterns

| Anti-pattern | Problem | Correct approach |
|---|---|---|
| Catch and ignore | Bug hidden — no one knows it happened | Catch, translate, propagate or log |
| Catch and log only | Acknowledged but caller uninformed | Catch, log, AND return error to caller |
| Catch too broad | Masks unrelated errors | Catch specific types at each boundary |
| Catch too deep | Logic tier catching what it cannot handle | Let it propagate to the appropriate tier |
| Rethrow without context | Error chain loses information | Wrap with context, preserve cause |
| Exceptions for control flow | Expected branching via exceptions | Result types for expected outcomes |
| Retry non-idempotent write | Duplicate side effects | Idempotency key, or ✗ retry |
| Unbounded retry / no jitter | Thundering herd, infinite loop | Max count + total budget + full jitter |
| Swallow at outer boundary | Silent failure to the user | Catch-all translates + logs, never silent |

Never-swallow rule: a caught error is always translated, propagated, or logged — never discarded. A silently swallowed error is a hidden bug.

---

## 11. Scale Matrix

| Capability | Prototype | Production | Scale |
|---|---|---|---|
| Classification | Crash on all (fail fast) | Data vs environment | Full 4-category + fatal/recoverable |
| Representation | Language default | Result types in core | Structured errors + codes + context |
| Propagation | Unhandled → crash | Catch at entry point | Tier-boundary translation everywhere |
| Result types | Not needed | Success/failure in domain | Full result + batch results |
| Messages | Print to stderr | Developer-facing | Dual audience (developer + user) |
| Retry | None | Single retry on I/O | Backoff + full jitter + circuit breaker + DLQ |
| Timeouts | Default/none | Per-call timeout | Deadline propagation across hops |
| Partial failure | Stop on first | Continue + collect | Full accumulation + per-item reporting |
| Recovery | Crash and restart | Basic fallback for critical paths | Graceful degradation + supervisor |
| Validation | Null/type checks | Schema at entry | Field-level + cross-field + referential |
| Logging | Print to stderr | Structured on error | Structured + aggregation + alerting |

Transition — Prototype → Production: add result types · catch at entry · basic I/O retry. Production → Scale: add error codes · circuit breakers · deadline propagation · validation layer · fallback per dependency · supervisor.

---

## 12. Checklist

- [ ] Every error maps to one category: programmer · data · environment · partial
- [ ] Fatal vs recoverable classified; fatal crashes with diagnostic output
- [ ] Programmer errors crash in production; ✗ caught or retried
- [ ] Result types are the default return for fallible Tier 0–1 functions
- [ ] Errors carry code + message + category + context; codes are stable strings
- [ ] Errors propagate outward only; translated (not raw) at every boundary
- [ ] Original error preserved as `cause`; ✗ lose the chain when wrapping
- [ ] Catch-all only at the outermost Tier 3 boundary; ✗ elsewhere
- [ ] User-facing messages expose no internals; developer messages no secrets/PII
- [ ] Retries only for idempotent transient environment errors
- [ ] Exponential backoff with full jitter; max count + total timeout budget
- [ ] Every external call has a timeout; deadlines propagate downstream
- [ ] Circuit breaker per external dependency (threshold · cooldown)
- [ ] Non-recoverable async messages routed to a dead-letter queue
- [ ] Batch ops accumulate errors; partial success is valid; per-item detail returned
- [ ] Every external dependency has a defined, tested, visible fallback
- [ ] Cleanup runs on success AND failure paths, in reverse order
- [ ] Validation collects all field errors; ✗ stop at first
- [ ] Errors logged once at the handling boundary; full cause chain included
- [ ] No swallowed errors — every catch translates, propagates, or logs
