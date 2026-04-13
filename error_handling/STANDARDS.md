# Error Handling Standards

Rules for classifying, representing, propagating, and recovering from errors.
Language-agnostic — language-specific error types belong in language-specific standards.

Foundation: `architecture/STANDARDS.md §7` (Error Architecture).
Companion: `observability/STANDARDS.md` (structured error logging).

---

## Table of Contents

1. [Error Classification](#1-error-classification)
2. [Error Representation](#2-error-representation)
3. [Error Propagation](#3-error-propagation)
4. [Result Types](#4-result-types)
5. [Error Messages](#5-error-messages)
6. [Retry Strategy](#6-retry-strategy)
7. [Partial Failure](#7-partial-failure)
8. [Recovery Strategy](#8-recovery-strategy)
9. [Error Boundaries](#9-error-boundaries)
10. [Validation Errors](#10-validation-errors)
11. [Logging Errors](#11-logging-errors)
12. [Fatal vs Recoverable](#12-fatal-vs-recoverable)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Error Classification

Four error categories. Every error maps to exactly one.
See `architecture/STANDARDS.md §7` — Classification table.

| Category | Definition | Examples | Strategy |
|---|---|---|---|
| Programmer error | Bug in code logic — violated invariant, unreachable state | Index out of bounds · null dereference · type mismatch · assertion failure | Crash immediately · fix code · ✗ catch or retry |
| Data error | Invalid, malformed, or unexpected input data | Missing required field · schema violation · out-of-range value · corrupt payload | Return error in result · ✗ throw · caller decides |
| Environment error | External system failure — network, disk, service | Connection refused · timeout · disk full · permission denied · DNS failure | Raise/throw · supervisor handles · retry if idempotent |
| Partial failure | Some items succeed, some fail in batch operation | 3 of 10 records fail validation · 1 API call in batch times out | Accumulate all errors · continue processing · report complete results |

### Classification Rules

- Unknown errors default to environment error until diagnosed.
- Programmer errors are ✗ caught in production — they crash. Catching masks bugs.
- Data errors ✗ crash the system — bad input is expected at runtime.
- Environment errors are transient until proven permanent.
- Partial failures are ✗ treated as full failures — surviving items proceed.

---

## 2. Error Representation

Two mechanisms: error-as-data (returned) and exceptions (thrown/raised).
Each has a correct use case — mixing them creates ambiguity.

| Mechanism | Use when | Tier affinity |
|---|---|---|
| Error as data (result type) | Failure is expected, part of normal flow | Tier 0–1 (logic) |
| Exception / raise / throw | Failure is unexpected, environment disruption | Tier 3 (interface) |

### Decision Rules

| Condition | Mechanism |
|---|---|
| Caller can reasonably handle the error immediately | Error as data |
| Error crosses tier boundary upward | Error as data |
| External system failure (I/O, network, disk) | Exception |
| Multiple errors possible in single operation | Error as data (accumulate) |
| Unrecoverable invariant violation | Exception (crash) |
| Validation failure | Error as data |

### Structural Requirements

Every error — whether returned or thrown — carries:

| Field | Required | Purpose |
|---|---|---|
| Error code | Yes | Machine-readable identifier — stable across versions |
| Message | Yes | Human-readable description — developer-facing |
| Category | Yes | One of the four classification types |
| Context | Yes | Key-value pairs: operation, input summary, relevant IDs |
| Source | No | Module/function that originated error |
| Cause | No | Wrapped inner error if error was translated at boundary |
| Timestamp | No | When error occurred — added at logging layer |

- Error codes are strings, not integers. Format: `DOMAIN.CATEGORY.SPECIFIC` (e.g., `PAYMENT.DATA.INVALID_AMOUNT`).
- Error codes ✗ change once published — they are part of the contract.
- Error messages ✗ contain sensitive data (credentials, PII, internal paths).

---

## 3. Error Propagation

How errors flow through tiers. See `architecture/STANDARDS.md §2` (Tier Model) · `§7` (Boundaries).

### Propagation Direction

Errors propagate outward (upward): Tier 0 → 1 → 2 → 3 → caller.
✗ propagate errors inward (toward lower tiers).

### Tier Behavior

| Tier | On error | Action |
|---|---|---|
| 0 (Kernel) | Return error in result | ✗ catch · ✗ log · ✗ retry |
| 1 (Engine) | Return error in result | ✗ catch · ✗ log · may enrich context |
| 2 (Service) | Catch domain errors | Translate to structured result · decide retry · accumulate partial failures |
| 3 (Interface) | Catch environment errors | Translate to user-facing message · log · trigger recovery |

### Translation Rules

Errors are translated at each tier boundary — never passed raw across tiers.

| Boundary | Translation |
|---|---|
| Tier 0 → 1 | Preserve as-is or wrap with domain context |
| Tier 1 → 2 | Wrap into operation-level result with error list |
| Tier 2 → 3 | Translate to user-appropriate error (strip internals) |
| Tier 3 → External | Map to protocol format (HTTP status, CLI exit code, API error response) |

- Original error preserved as `cause` in wrapped error — full chain available for debugging.
- ✗ lose the original error when translating. Wrap, don't replace.
- ✗ expose internal error codes or stack traces to external callers.

---

## 4. Result Types

Structured return values carrying both success data and error information.
See `architecture/STANDARDS.md §4` — Return Contract · Explicit Absence.

### Result Structure

Every operation that can fail returns a result type, not a raw value.

| Variant | Contains | When |
|---|---|---|
| Success | Data payload | Operation completed without error |
| Failure | Error (or list of errors) | Operation failed |

### Rules

- Result types are the **default** return for Tier 0–1 functions that can fail.
- Caller ✗ access success data without first checking for failure.
- ✗ use null/nil/None to represent failure — use explicit failure variant.
- Functions that cannot fail return plain values (no result wrapper needed).
- Nested results (Result inside Result) indicate missing error translation at a boundary — flatten.

### Batch Results

Operations processing multiple items return a batch result:

| Field | Type | Purpose |
|---|---|---|
| `succeeded` | List of (item, output) | Items processed without error |
| `failed` | List of (item, error) | Items that failed with per-item error |
| `total` | Integer | Total items attempted |
| `success_count` | Integer | Count of succeeded |
| `failure_count` | Integer | Count of failed |

- Batch result is itself a success if `failure_count == 0`.
- Batch result ✗ treated as full failure when `success_count > 0` — partial success is valid.

---

## 5. Error Messages

### Two Audiences

| Audience | Content | Where generated |
|---|---|---|
| Developer | Technical detail · stack context · variable state · error chain | Tier 0–2 (internal message) |
| User | Action-oriented · what happened · what to do next | Tier 3 (translated at boundary) |

### Developer-Facing Message Rules

| Rule | Detail |
|---|---|
| State what failed | `"Failed to parse configuration file"` — not `"Error"` or `"Something went wrong"` |
| Include discriminating context | Operation name · input identifier · expected vs actual value |
| ✗ include sensitive data | No credentials · no PII · no full file paths beyond project root |
| ✗ duplicate the error code | Message adds information the code does not carry |
| Use present tense | `"Connection refused"` — not `"Connection was refused"` |

### User-Facing Message Rules

| Rule | Detail |
|---|---|
| State what happened | Plain language, no jargon |
| State what to do | Actionable next step or "contact support" as last resort |
| ✗ expose internals | No stack traces · no error codes · no module names |
| ✗ blame the user | `"File not found"` — not `"You provided an invalid file"` |
| Include request ID | If applicable — allows user to reference when reporting |

### Message Template

Developer: `"{operation} failed: {reason} [context: {key}={value}, ...]"`
User: `"{what_happened}. {what_to_do}."`

---

## 6. Retry Strategy

When environment errors are transient, retry with discipline.
See `architecture/STANDARDS.md §1` — Principle #16 (idempotency) · #20 (circuit breaker).

### Preconditions for Retry

| Condition | Required |
|---|---|
| Operation is idempotent | Yes — ✗ retry non-idempotent operations without idempotency key |
| Error is classified as environment error | Yes — ✗ retry programmer or data errors |
| Error is transient (not permanent) | Yes — permanent errors fail immediately |
| Max retry count defined | Yes — ✗ retry indefinitely |
| Timeout budget defined | Yes — total time across all retries bounded |

### Backoff Patterns

| Pattern | Formula | Use when |
|---|---|---|
| Exponential + jitter | `min(base * 2^attempt + random_jitter, max_delay)` | Default for all retries |
| Fixed delay | `constant_delay` | Only when server specifies `Retry-After` |
| Immediate (1 retry) | `0` delay, single retry | Transient failures in local operations (file lock) |

- ✗ use linear backoff — creates thundering herd on shared resources.
- Jitter is mandatory on exponential backoff — prevents synchronized retry storms.

### Default Retry Parameters

| Parameter | Default | Range |
|---|---|---|
| Max retries | 3 | 1–5 for interactive · up to 10 for batch/background |
| Base delay | 1 second | 100ms–5s depending on operation |
| Max delay | 30 seconds | Cap per-retry wait |
| Total timeout | 60 seconds | Hard cap for entire retry sequence |
| Jitter range | 0–100% of delay | Random spread |

### Circuit Breaker

See `architecture/STANDARDS.md §7` — Circuit Breaker.

| State | Behavior |
|---|---|
| Closed (normal) | Requests pass through · failure counter increments on error |
| Open (tripped) | Requests fail immediately with circuit-open error · ✗ attempt call |
| Half-open (probing) | One probe request allowed · success → close · failure → re-open |

| Parameter | Default |
|---|---|
| Failure threshold to open | 5 consecutive failures |
| Cooldown before half-open | 30 seconds |
| Success threshold to close | 1 successful probe |

- Circuit breaker wraps external dependency calls at Tier 3.
- Circuit state is per-dependency, not global.
- Circuit-open error is an environment error — propagates as such.

---

## 7. Partial Failure

Batch operations process all items — ✗ stop on first error.
See `architecture/STANDARDS.md §7` — Partial Failure.

### Accumulation Pattern

1. Initialize empty success list and error list.
2. Process each item independently.
3. On item success → append to success list with output.
4. On item failure → append to error list with item identifier + error. Continue.
5. Return batch result (§4 Batch Results) containing both lists.

### Rules

| Rule | Detail |
|---|---|
| Independence | Each item processed in isolation — one failure ✗ affects others |
| Error identity | Every error linked to its source item — ✗ orphaned errors |
| Ordering preserved | Success/failure lists maintain original input order |
| Threshold abort | Optional: stop after N% failure rate — but still report accumulated results |
| Transactional items | If single item requires multiple steps, item-level rollback on failure |

### Reporting

- Batch result includes per-item status, not just counts.
- Caller receives enough information to retry only failed items.
- Failed items carry full error detail — ✗ generic "some items failed."

---

## 8. Recovery Strategy

How systems respond when errors occur. Goal: continue operating at reduced capability rather than crash.
See `architecture/STANDARDS.md §1` — Principle #26 (graceful degradation).

### Graceful Degradation

| Scenario | Response |
|---|---|
| Non-critical dependency unavailable | Disable dependent feature · continue core operation |
| Cache unavailable | Bypass cache · serve from origin (slower but functional) |
| Secondary data source fails | Serve with incomplete data · flag what is missing |
| Rate limit exceeded | Queue · throttle · serve cached response |
| Configuration source unavailable | Use last-known-good configuration · log warning |

### Fallback Rules

| Rule | Detail |
|---|---|
| Fallback is pre-defined | Every external dependency has declared fallback behavior before production |
| Fallback is tested | Fallback paths tested same as primary paths |
| Fallback is visible | System reports degraded state — ✗ silently serve degraded response |
| Fallback has limits | Degraded mode has own timeout — ✗ degrade indefinitely without alerting |

### Cleanup and Resource Release

| Principle | Rule |
|---|---|
| Deterministic cleanup | Every acquired resource released on both success and failure paths |
| Cleanup ordering | Resources released in reverse acquisition order |
| Cleanup ✗ throws | Cleanup code ✗ raises new errors — log and continue releasing |
| Scope-bound resources | Resource lifetime tied to scope — released when scope exits |
| Partial-operation cleanup | Failed multi-step operations roll back completed steps |

### Supervisor Pattern

For long-running processes and services:

| Component | Role |
|---|---|
| Worker | Performs operation · reports errors upward · ✗ decides recovery |
| Supervisor | Monitors workers · decides restart/skip/escalate · owns recovery policy |

- Worker crashes → supervisor restarts with clean state (per `architecture/STANDARDS.md §1` — Principle #4).
- Supervisor tracks restart frequency — repeated crashes within window → escalate, ✗ restart loop.
- Maximum restart attempts: 3 within 60 seconds. Exceeding → escalate to parent supervisor or halt.

---

## 9. Error Boundaries

Where errors are caught, translated, and handled.
See `architecture/STANDARDS.md §7` — Boundaries.

### Boundary Locations

| Boundary | Between | Responsibility |
|---|---|---|
| Tier boundary | Tier N → Tier N+1 | Translate error representation to target tier's format |
| Module boundary | Module A → Module B | Ensure module-internal errors don't leak implementation details |
| System boundary | Internal → external caller | Map to protocol-appropriate error (HTTP status, exit code, error response) |
| Async boundary | Producer → consumer | Serialize error for cross-process/thread transport |

### Boundary Rules

- Every boundary has exactly one error handler — ✗ duplicate catch blocks at same boundary.
- Boundary handler catches **specific** error types — ✗ catch-all without re-raise.
- Catch-all at outermost boundary (Tier 3 entry point) is required — prevents unhandled crashes leaking to user.
- Caught errors are translated, not swallowed. Swallowed error = hidden bug.
- Error context enriched at each boundary: add operation name, request ID, relevant identifiers.

### Anti-Patterns

| Anti-pattern | Problem | Correct approach |
|---|---|---|
| Catch and ignore | Bug hiding — error occurred but no one knows | Catch, translate, propagate or log |
| Catch and log only | Error acknowledged but caller not informed | Catch, log, AND return error to caller |
| Catch too broad | Masks unrelated errors | Catch specific types at each boundary |
| Catch too deep | Logic tier catching errors it cannot handle | Let errors propagate to appropriate tier |
| Rethrow without context | Error chain loses information | Wrap with context, preserve cause |
| Error codes as control flow | Using exceptions for expected branching | Use result types for expected outcomes |

---

## 10. Validation Errors

Input validation produces data errors — returned as structured results, ✗ thrown.
See `architecture/STANDARDS.md §2` — Tier 3 (Interface) handles external input.

### Validation Location

| Validation type | Where | Tier |
|---|---|---|
| Schema validation (structure, types) | Entry point — first contact with external data | 3 |
| Business rule validation (domain constraints) | Engine — domain logic | 1 |
| Cross-field validation (field interdependencies) | Engine — after individual field validation | 1 |
| Referential validation (existence checks requiring I/O) | Service — orchestrates lookup + validation | 2–3 |

### Validation Rules

- Validate all fields — ✗ stop at first invalid field. Collect all violations.
- Each violation identifies: field path · rule violated · actual value (if safe) · expected constraint.
- Validation result is a list of field errors, not a single error message.
- Schema validation runs before business rule validation — reject structurally invalid data early.
- ✗ validate inside Tier 0 (Kernel) — Tier 0 types enforce structure via type system, not runtime checks.

### Field Error Structure

| Field | Purpose |
|---|---|
| `path` | Dot-notation path to invalid field: `"address.zip_code"` |
| `code` | Machine-readable validation code: `REQUIRED` · `OUT_OF_RANGE` · `INVALID_FORMAT` |
| `message` | Human-readable description |
| `constraint` | Expected constraint: `"min: 1, max: 100"` |
| `actual` | Actual value received (omit if sensitive) |

### Standard Validation Codes

| Code | Meaning |
|---|---|
| `REQUIRED` | Field missing or null |
| `INVALID_FORMAT` | Value does not match expected format/pattern |
| `OUT_OF_RANGE` | Value outside min/max bounds |
| `INVALID_TYPE` | Wrong data type |
| `TOO_LONG` | Exceeds maximum length |
| `TOO_SHORT` | Below minimum length |
| `NOT_UNIQUE` | Duplicate value where uniqueness required |
| `INVALID_REFERENCE` | Referenced entity does not exist |
| `IMMUTABLE` | Field cannot be changed after creation |
| `DEPENDENCY` | Field invalid due to value of another field |

---

## 11. Logging Errors

What to log and how. Detailed logging format → `observability/STANDARDS.md`.

### What to Log

| Log | Don't log |
|---|---|
| All environment errors | Expected data validation failures (unless aggregated) |
| Circuit breaker state transitions | Successful operations (unless audit trail required) |
| Recovery actions taken (fallback activated, retry attempted) | Programmer errors in production (crash + stack trace suffices) |
| Partial failure summaries (N succeeded, M failed) | Raw input data containing PII/secrets |
| Error escalations (worker → supervisor) | Duplicate entries for same error at multiple layers |

### Structured Error Log Fields

Every error log entry includes:

| Field | Required | Example |
|---|---|---|
| `level` | Yes | `error` · `warn` |
| `error_code` | Yes | `PAYMENT.ENV.TIMEOUT` |
| `message` | Yes | `"Payment gateway timeout after 5000ms"` |
| `operation` | Yes | `"process_payment"` |
| `request_id` | Yes (if available) | `"req-abc-123"` |
| `duration_ms` | Yes (if timed) | `5023` |
| `retry_attempt` | If retrying | `2` |
| `category` | Yes | `"environment"` |
| `context` | Yes | Key-value pairs relevant to operation |

### Log Level Mapping

| Error category | Log level |
|---|---|
| Programmer error | `error` (captured by crash handler) |
| Data error (single) | `warn` (or `debug` if high volume) |
| Data error (batch summary) | `warn` |
| Environment error | `error` |
| Environment error (recovered via retry) | `warn` |
| Circuit breaker opened | `error` |
| Circuit breaker closed (recovered) | `info` |
| Graceful degradation activated | `warn` |

### Rules

- Log once per error, at the boundary where it is handled — ✗ log same error at multiple tiers.
- Include full error chain (cause chain) in structured log — ✗ log only the outermost message.
- ✗ log and rethrow without marking that error was already logged — prevents duplicate logging.
- Aggregate repeated identical errors — log count per window, not every occurrence.

---

## 12. Fatal vs Recoverable

Every error is classified as fatal or recoverable. This determines crash vs continue.

### Classification Rules

| Condition | Classification | Action |
|---|---|---|
| Invariant violated (impossible state reached) | Fatal | Crash immediately |
| Required configuration missing at startup | Fatal | Crash before serving requests |
| Database schema incompatible with code | Fatal | Crash at startup |
| Out of memory | Fatal | Crash — OS handles |
| Stack overflow | Fatal | Crash — cannot recover |
| Corrupted internal data structure | Fatal | Crash — continuing risks data corruption |
| Network timeout | Recoverable | Retry with backoff |
| External service returns error | Recoverable | Retry or degrade |
| Invalid user input | Recoverable | Return validation errors |
| File not found (expected to exist) | Recoverable | Return error · caller decides |
| Rate limit hit | Recoverable | Back off · queue · retry later |
| Disk full on write | Recoverable | Clean up · alert · retry |

### Decision Process

1. Can the process continue without data corruption? No → fatal.
2. Is the error caused by a code bug (not data or environment)? Yes → fatal.
3. Does the error indicate a missing precondition for the entire process? Yes → fatal.
4. Is recovery possible within a bounded time? No → fatal.
5. All other errors → recoverable.

### Fatal Error Rules

- Fatal errors crash the process with non-zero exit code.
- Fatal errors log full state before crash: stack trace, relevant variables, configuration snapshot.
- ✗ catch fatal errors in application code — only crash handlers and supervisors catch them.
- Crash handler runs cleanup (resource release) before exit — but ✗ attempt recovery.

### Recoverable Error Rules

- Recoverable errors propagate via result types or controlled exceptions.
- Recovery has a bounded attempt count and time budget.
- Recovered errors are logged at `warn` level (not `error`) — error occurred but was handled.
- If recovery fails after all attempts → escalate to supervisor or convert to user-facing error.

---

## 13. Scale Matrix

Error handling depth scales with project complexity.
See `architecture/STANDARDS.md §12` — Project Scale Matrix.

| Capability | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Error classification | Crash on all errors (fail fast) | Distinguish data vs environment | Full 4-category classification |
| Error representation | Language default (exceptions/panics) | Result types in core logic | Structured errors with codes + context |
| Error propagation | Unhandled → crash | Catch at entry point | Tier-boundary translation at every level |
| Result types | Not needed | Success/failure in domain functions | Full result types + batch results |
| Error messages | Print to stderr | Developer-facing messages | Dual audience (developer + user) |
| Retry strategy | No retries | Single retry on I/O | Exponential backoff + jitter + circuit breaker |
| Partial failure | Stop on first error | Continue + collect errors | Full accumulation + per-item reporting |
| Recovery | Crash and restart | Basic fallback for critical paths | Graceful degradation + supervisor pattern |
| Error boundaries | None (crash through) | Catch at module boundary | Every tier + module + system boundary |
| Validation | Basic null/type checks | Schema validation at entry | Full field-level validation + cross-field + referential |
| Error logging | Print to stderr | Structured log on error | Full structured logging + aggregation + alerting |
| Fatal vs recoverable | Everything is fatal | Distinguish crash vs return-error | Full classification + recovery budgets + supervisor |

### Scale Transition

When graduating between scales:
- PoC → Small: add result types to domain functions · catch errors at entry point · add basic retry for I/O.
- Small → Production: add error codes · implement circuit breaker · add validation layer · define fallback for every external dependency · implement supervisor for long-running processes.

---

## 14. Checklist

### New Project

- [ ] Error categories defined (programmer · data · environment · partial)
- [ ] Error representation chosen (result types for domain · exceptions for environment)
- [ ] Error code format defined (`DOMAIN.CATEGORY.SPECIFIC`)
- [ ] Error boundaries identified at tier and module boundaries
- [ ] Validation strategy defined (where, what level)
- [ ] Retry parameters configured (max retries · backoff · timeout budget)
- [ ] Fatal vs recoverable classification documented
- [ ] Error logging structure agreed (cross-ref `observability/STANDARDS.md`)

### New Module

- [ ] All public functions return result types for expected failures
- [ ] No catch blocks in Tier 0–1 logic
- [ ] Errors carry code + message + category + context
- [ ] Module boundary translates internal errors — ✗ leak implementation details
- [ ] Validation collects all field errors — ✗ stop at first

### New External Dependency

- [ ] Fallback behavior defined for unavailability
- [ ] Circuit breaker configured (threshold · cooldown)
- [ ] Retry parameters set (idempotent operations only)
- [ ] Timeout budget defined
- [ ] Error from dependency translated to internal error format at Tier 3 boundary

### New Batch Operation

- [ ] Accumulation pattern: success list + error list
- [ ] Per-item errors linked to source item
- [ ] Partial success is valid result — ✗ treated as full failure
- [ ] Caller can identify and retry only failed items
- [ ] Threshold abort configured if applicable (stop at N% failure)

### Pre-Production Review

- [ ] No swallowed errors (catch without propagate or log)
- [ ] No catch-all without re-raise (except outermost boundary)
- [ ] No raw exceptions crossing tier boundaries
- [ ] All environment errors have retry or fallback path
- [ ] All fatal conditions crash cleanly with diagnostic output
- [ ] Error log entries include: code · message · operation · request_id · context
- [ ] User-facing messages contain no internal details
- [ ] Circuit breakers configured for every external dependency
- [ ] Cleanup runs on both success and failure paths
