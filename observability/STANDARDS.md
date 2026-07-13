# Observability Standards

> Structured logging, metrics, traces, SLOs, health, and alerting that make production operable — the single source for alert design and resource thresholds.

**ID** `observability` · **Tier** Core · **Version** 1.0
**Owns** structured logging · log levels/content · operation receipts · metrics (golden signals/RED/USE) · health checks · distributed tracing · SLOs + error budgets · alert design rules + resource thresholds · log retention
**Defers to** error taxonomy/classification → [error_handling](../error_handling/STANDARDS.md) · security audit event catalog + PII basis → [security](../security/STANDARDS.md) · performance budgets + caching → [performance](../performance/STANDARDS.md) · which infra metrics to collect · backup/DR → [devops](../devops/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [security](../security/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Structured Logging](#2-structured-logging)
3. [Log Levels](#3-log-levels)
4. [Log Content & Exclusions](#4-log-content--exclusions)
5. [Operation Receipts](#5-operation-receipts)
6. [Metrics](#6-metrics)
7. [Health Checks](#7-health-checks)
8. [Distributed Tracing](#8-distributed-tracing)
9. [SLOs & Error Budgets](#9-slos--error-budgets)
10. [Alerting & Resource Thresholds](#10-alerting--resource-thresholds)
11. [Audit Trail](#11-audit-trail)
12. [Log Retention](#12-log-retention)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Three signals, one context | Logs, metrics, traces correlate via shared trace/correlation IDs |
| Vendor-neutral instrumentation | Emit via **OpenTelemetry** (OTel) — traces + metrics + logs; follow OTel semantic conventions |
| Instrument at boundaries | Entry/exit, external calls, state changes — ✗ every internal step |
| Alert on symptoms, not causes | Alert on user-facing SLO burn (§9), not on internal resource wobble |
| Measure distributions, not averages | Percentiles p50/p95/p99 — ✗ average latency (hides the tail) |
| Cardinality discipline | Bounded label/attribute sets — ✗ IDs, timestamps, or free text as labels |

Coverage models — instrument every service against all three:

| Model | Signals |
|---|---|
| Golden signals (SRE) | Latency · traffic · errors · saturation |
| RED (request-driven) | Rate · Errors · Duration |
| USE (resources) | Utilization · Saturation · Errors |

---

## 2. Structured Logging

All log output is machine-parseable key-value structured data.

| Rule | Detail |
|---|---|
| Output format | JSON objects, one per line (JSON Lines) |
| ✗ string interpolation | Never embed variables in the message — use separate fields |
| ✗ multi-line entries | One event = one line; stack traces → a dedicated field |
| Field naming | `snake_case`, consistent across all services |
| Timestamp | ISO 8601 with timezone, UTC always: `YYYY-MM-DDTHH:MM:SS.sssZ`; ✗ local time |
| Encoding | UTF-8; binary → base64 in a dedicated field |

### Required Fields (every entry)

| Field | Purpose |
|---|---|
| `timestamp` | ISO 8601 UTC when the event occurred |
| `level` | debug/info/warn/error/fatal |
| `message` | Static template summary — ✗ interpolated values |
| `service` | Service or application name |
| `correlation_id` | Request/operation correlation identifier |

### Optional Standard Fields

`operation` · `duration_ms` · `user_id` · `error_code` · `error_message` · `stack_trace` · `component` · `environment` · `version` · `trace_id` · `span_id` · `parent_span_id`.

### Message Field

- Static template: `"User login succeeded"` — not `"User john logged in at 14:32"`. Variable data → separate fields.
- Messages are grep-friendly — identical events produce identical strings. Max length 200 chars.

---

## 3. Log Levels

Five levels, strict criteria. If an event does not meet the criteria, it belongs at a different level.

| Level | Criteria | Examples |
|---|---|---|
| `debug` | Internal state for development/troubleshooting. ✗ enabled in production by default | Variable values · branch decisions · cache hit/miss |
| `info` | Normal operational events confirming the system works as designed | Request completed · job started/finished · config loaded |
| `warn` | Unexpected condition, operation continues; investigate within days | Retry succeeded · deprecated API called · pool nearing capacity |
| `error` | Operation failed, cannot complete; investigate within hours. ✗ means system down | Request failed · dependency timeout · validation rejection |
| `fatal` | System cannot continue; process exits; immediate response | Port bind failure · missing critical config · corrupt state |

| Rule | Detail |
|---|---|
| One level per event | ✗ log the same event at multiple levels |
| Error ≠ bad input | Client sends bad data → `warn`; server fails valid data → `error` |
| Retries | First-attempt failure → `debug`; final failure → `error`; retry succeeded → `warn` |
| ✗ `error` for flow control | Expected alternative paths (cache miss, 404) are not errors |
| Rate limiting | Repeated identical events → log first, then aggregate a count at interval |

Error classification (which category an error is) → [error_handling §1](../error_handling/STANDARDS.md).

---

## 4. Log Content & Exclusions

### Include

| Context | Fields |
|---|---|
| Request identity | `correlation_id` · `trace_id` · `span_id` |
| Operation context | `operation` · `component` · `service` |
| Timing | `timestamp` · `duration_ms` |
| Outcome | `status` · `error_code` · `error_message` |
| Identifiers | Entity IDs · file paths · queue names (non-sensitive) |
| Quantitative | Record count · byte size · retry count |

### Never Log (! critical)

| ✗ Never | Alternative |
|---|---|
| Passwords, tokens, API keys | Log `"auth_method": "api_key"` — not the key |
| PII (names, emails, phone, SSN) | Hashed or tokenized identifiers |
| Credit-card numbers | Last 4 digits only, masked |
| Request/response bodies by default | `debug` behind a feature flag |
| DB connection strings | Host and database name only |
| Session tokens, cookies | Session ID hash |
| Encryption keys, certificates | Key fingerprint or ID |

Exclusion basis and PII classification → [security §8](../security/STANDARDS.md). Same exclusions apply to receipts (§5), traces (§8), and audit logs (§11).

### Boundaries

- Log at operation boundaries: entry, exit, error — ✗ every internal step.
- ✗ log inside tight loops — aggregate and log a summary after the loop.
- ✗ log in library/utility code — let the caller decide.
- ✗ log raw exceptions as messages — extract code, message, type into fields.

---

## 5. Operation Receipts

Every state-changing operation (create, update, delete, execute) returns a receipt confirming what changed.

| Field | Purpose |
|---|---|
| `operation` | What was performed |
| `entity_type` · `entity_id` | What kind of thing changed · which specific one |
| `status` | `success` · `partial` · `failed` · `noop` |
| `timestamp` | When it completed |
| `changes` | Before/after values per modified field |
| `correlation_id` | Links receipt to the triggering request |
| `actor` | Who/what initiated the change |

| Rule | Detail |
|---|---|
| Every write → receipt | ✗ fire-and-forget mutations |
| Noop is valid | No change → receipt with `status: noop` |
| Partial is valid | Batch → per-item status array in one receipt |
| Receipt ≠ log entry | Receipt returned to caller; logging it is separate |
| Same exclusions | ✗ secrets/PII in receipts (§4) |

Log every receipt: `info` normally · `error` for failed · `debug` for noop; with `event_type: "operation_receipt"` and all receipt fields as structured fields.

---

## 6. Metrics

Three metric types cover all measurement needs.

| Type | Measures | Example |
|---|---|---|
| Counter | Cumulative count, only increases | `http_requests_total` |
| Gauge | Current value, up and down | `active_connections` |
| Histogram | Distribution in buckets | `request_duration_seconds` |

### Naming

| Rule | Detail |
|---|---|
| Format | `snake_case`, lowercase, service/domain prefix: `myapp_http_requests_total` |
| Suffixes | counters `_total` · durations `_seconds` · sizes `_bytes` · gauges `_active`/`_pending`/`_available` |
| Base units | Seconds not ms, bytes not KB |
| ✗ type in name | Suffix convention conveys type — not `request_counter` |
| ✗ status in name | Use labels: `http_requests_total{status="200"}` |

### What to Measure (golden signals / RED / USE)

| Category | Metrics |
|---|---|
| Requests (RED) | Rate · error rate · duration histogram · in-flight count |
| Dependencies | Call count · duration · error rate · circuit-breaker state per dependency |
| Queues | Depth (gauge) · enqueue/dequeue rate · age of oldest item |
| Resources (USE) | CPU · memory · disk · file descriptors · thread/goroutine count · saturation |
| Business | Items processed · signups · domain counters |
| Cache / pools | Hit/miss ratio · evictions · active/idle/waiting |

| Rule | Detail |
|---|---|
| Low cardinality | ✗ user IDs, ✗ request IDs, ✗ timestamps as label values |
| Bounded label values | Every label has a known finite value set |
| Measure at boundaries | Instrument entry/exit — ✗ internal implementation |
| Histograms for latency | Derive p50/p90/p95/p99 from buckets — ✗ averages alone |
| ✗ business logic in metrics | Metrics observe, never control flow |

---

## 7. Health Checks

Two distinct check types, separate endpoints.

| Check | Answers | Failure means | Budget |
|---|---|---|---|
| Liveness (`/health/live`) | Is the process running and not deadlocked? | Restart the process | < 100 ms, no dependencies |
| Readiness (`/health/ready`) | Can this instance serve traffic? | Remove from load balancer | < 500 ms, checks dependencies |

| Rule | Detail |
|---|---|
| Liveness is self-only | ✗ check external dependencies · ✗ heavy computation |
| Readiness checks dependencies | Critical dep unhealthy → `unhealthy`; optional dep → `degraded` |
| Cached dependency status | < 10 s stale; ✗ check on every request |
| Startup/shutdown | Readiness `unhealthy` until init completes and during graceful shutdown |
| No authentication | Load balancers need access; ✗ sensitive data in response |
| Status codes | HTTP 200 = healthy · 503 = unhealthy; ✗ other codes |
| Dependency check timeout | 2 s max each; ✗ trigger reconnection/retry from a health check |
| Frequency | External polling 10–30 s; ✗ more frequent than 5 s |

Response fields: `status` (`healthy`/`degraded`/`unhealthy`) · `checks{name: {status, duration_ms, message}}` · `version` · `uptime_seconds`.

---

## 8. Distributed Tracing

Track requests across service boundaries via trace context and span hierarchies. Instrument with OpenTelemetry.

| Concept | Definition |
|---|---|
| Trace | End-to-end journey of one request through all services |
| Span | One unit of work within a trace (one function, one RPC) |
| Trace ID | Identifies the whole trace — propagated across all services |
| Span ID / Parent Span ID | Identifies one span · links child to parent |
| Correlation ID | Application-level request ID — may differ from trace ID |

| Rule | Detail |
|---|---|
| Propagate context explicitly | Flows as a call parameter, not global state |
| HTTP propagation | `traceparent` header (W3C Trace Context) |
| Queue propagation | Trace context in message metadata/headers |
| Generate at entry | First service generates trace ID if absent; ✗ generate a new trace ID mid-chain |
| Span naming | `{service}.{operation}` — e.g. `orders.create`; ✗ high-cardinality names (`orders.create.12345`) |
| One span per logical op | External call · DB query · queue publish · significant computation; ✗ span per trivial helper |
| Record status | `ok` · `error` with error detail as span attributes |
| Attributes not names | Entity IDs, counts, status codes → span attributes |

Trace: incoming/outgoing requests · DB queries · queue publish/consume · external calls. ✗ trace logging calls, getters/setters, iteration steps, trivial transforms.

---

## 9. SLOs & Error Budgets

Service reliability is expressed as SLOs, not vibes. Alert on SLO burn (§10), not on raw causes.

| Concept | Definition |
|---|---|
| SLI | A measured indicator: success ratio · latency percentile · availability |
| SLO | Target for an SLI over a window: `99.9% of requests < 300 ms over 30 days` |
| Error budget | `1 − SLO` — the allowed failure amount in the window (99.9% → 0.1%) |
| Burn rate | How fast the error budget is consumed relative to the window |

| Rule | Detail |
|---|---|
| SLO per user-facing journey | Define SLIs for the paths users depend on, not every internal call |
| Latency as a percentile | `p99 < N ms` — ✗ average latency |
| Budget governs risk | Budget remaining → ship; budget exhausted → freeze risky change, prioritize reliability |
| Multi-window multi-burn-rate alerting | Page on fast burn (e.g. 2% budget in 1 h) · ticket on slow burn (e.g. 10% in 6 h) |
| Symptoms over causes | Alert on SLO burn and user-facing errors — ✗ page on internal resource metrics alone |

Degraded-mode/fallback decisions tie to remaining budget → [error_handling §7](../error_handling/STANDARDS.md).

---

## 10. Alerting & Resource Thresholds

Every alert is actionable — if nobody needs to act, it is not an alert. This standard owns alert design rules and resource thresholds; `devops` defers here and keeps only which infra metrics to collect.

### Severity

| Severity | Response | Channel | Criteria |
|---|---|---|---|
| Critical | < 5 min | Page/phone | Service down · data loss imminent · security breach |
| High | < 30 min | Urgent chat/ticket | Major degradation · error-rate spike · dependency failure |
| Medium | < 4 h | Normal ticket | Gradual degradation · resource trend |
| Low | Next business day | Email/dashboard | Informational threshold · maintenance needed |

### Design Rules

| Rule | Detail |
|---|---|
| Every alert has a runbook | Link to the operator's resolution steps |
| Alert on symptoms | SLO burn / error rate — not "connection pool exhausted" |
| ✗ alert on a single event | Threshold over a time window, not one occurrence |
| Alert on rate of change | Sudden shifts matter even within an absolute threshold |
| ✗ duplicate alerts | One condition → one alert; suppress duplicates during an incident |
| Auto-resolve | Alert clears when the condition returns to normal |
| ✗ alert fatigue | Fires > 5×/week without action → tune or remove |
| Test in staging | Verify the alert fires before production |

### Canonical Thresholds (! authoritative)

| Alert | Threshold |
|---|---|
| Resource saturation | **CPU > 85% · memory > 90% · disk > 85%, sustained 10 min** |
| Error-rate spike | > 1% of requests over a 5 min window |
| Latency degradation | p99 > 2× baseline for 5 min |
| Health-check failure | Unhealthy for > 2 consecutive checks |
| Queue depth growing | Monotonically increasing for > 15 min |
| Certificate expiry | < 14 days to expiration |
| Dependency failure | Circuit open for > 2 min |
| Zero traffic | 0 requests for > 5 min during expected hours |

Resource warning tier (pre-saturation, investigate): CPU > 70% · memory > 75% · disk > 75%. ✗ page on the warning tier — ticket only.

### ✗ Do Not Alert On

Individual request failures (log + count) · successful deployments · auto-recovered transient errors · expected maintenance windows · debug-level anomalies.

---

## 11. Audit Trail

Security-relevant events logged for compliance and forensics. The event catalog and integrity controls are owned by [security §13](../security/STANDARDS.md); this section states only the format and separation.

| Rule | Detail |
|---|---|
| Same structured format | Audit events are structured logs (§2) with a dedicated `event_type` |
| Fields | `timestamp` · `event_type` · `actor` · `actor_ip` · `resource_type` · `resource_id` · `action` · `outcome` · `correlation_id` |
| Separate storage | Audit trail stored apart from application logs |
| Synchronous write | Completes before the operation response — ✗ async |
| No gaps | Every auditable action → exactly one audit event |
| Same exclusions | ✗ PII/secrets in plain text (§4) |

Which events require an audit entry, immutability, tamper-evidence, and access restriction → [security §13](../security/STANDARDS.md).

---

## 12. Log Retention

| Data type | Hot | Warm | Cold/Archive | Minimum |
|---|---|---|---|---|
| Application logs | 7 d | 30 d | 90 d | 90 d |
| Audit logs | 30 d | 90 d | 1 year+ | 1 year |
| Metrics | 30 d full-res | 90 d downsampled | 1 year aggregated | 1 year |
| Traces | 7 d | 30 d | — | 30 d |
| Error logs | 30 d | 90 d | 1 year | 1 year |

| Rule | Detail |
|---|---|
| Rotation | Size (> 100 MB) or daily, whichever first; compress rotated logs (gzip/zstd) |
| Atomic rotation | ✗ lose entries — rename + reopen |
| Disk budget | Explicit max per service; overflow → delete oldest non-audit first |
| ✗ delete audit logs | Audit overflow → alert, ✗ auto-delete |
| Downsample on tier move | Warm: 1 s → 1 min · Cold: 1 min → 1 h resolution |
| Verifiable deletion | Confirm data is gone, not just deindexed; per compliance (GDPR/HIPAA/PCI) |

Storage tiers: hot = real-time query (< 1 s) · warm = delayed (< 1 min) · cold = retrievable on request (< 1 h).

---

## 13. Scale Matrix

| Capability | Prototype | Production | Scale |
|---|---|---|---|
| Structured logging (§2) | Print to stdout ok | JSON to stdout | Centralized aggregation |
| Log levels (§3) | info + error | All 5 | All 5 + dynamic control |
| Log content (§4) | Minimal fields | Required fields | Full standard + optional |
| Receipts (§5) | Return success/fail | Status + entity ID | Full receipt with before/after |
| Metrics (§6) | ✗ needed | Rate + errors + duration | Full RED/USE suite + dashboards |
| Health checks (§7) | ✗ needed | Single readiness | Liveness + readiness + dependency |
| Tracing (§8) | ✗ needed | Correlation ID only | Full OTel trace/span hierarchy |
| SLOs (§9) | ✗ needed | Availability + latency SLO | Multi-window burn-rate + budget policy |
| Alerting (§10) | ✗ needed | Error-log monitoring | Threshold + runbook + burn-rate |
| Audit (§11) | ✗ needed | Auth events | Full trail (→ security §13) |
| Retention (§12) | Local files | 30-day | Tiered + archival |

Transition order: (1) structured logging · (2) health checks · (3) metrics · (4) SLOs + alerting · (5) tracing.

---

## 14. Checklist

- [ ] Instrumented via OpenTelemetry; logs/metrics/traces share correlation/trace IDs
- [ ] Structured JSON logging; static message templates, variables in fields
- [ ] All five log levels applied per strict criteria; one level per event
- [ ] PII and secrets excluded from logs, receipts, traces, audit (→ security §8)
- [ ] Operation receipts returned from every write; secrets/PII excluded
- [ ] Rate, error, and duration metrics emitted; naming + base-unit conventions
- [ ] Latency tracked as p50/p95/p99 histograms; ✗ average latency
- [ ] Metric labels low-cardinality; ✗ IDs/timestamps as labels
- [ ] `/health/live` and `/health/ready` separate; readiness checks dependencies
- [ ] Trace context (`traceparent`) propagated to/from every external call
- [ ] SLOs defined for user-facing journeys with error budgets
- [ ] Burn-rate alerting: fast burn pages, slow burn tickets
- [ ] Alerts fire on symptoms/SLO burn, not raw causes; each has a runbook
- [ ] Resource saturation alerts: CPU > 85%, memory > 90%, disk > 85%, sustained 10 min
- [ ] Alerts use windowed thresholds; ✗ single-event alerts; auto-resolve on recovery
- [ ] Audit events structured, separate storage, synchronous, no gaps (→ security §13)
- [ ] Retention + rotation configured per data type; audit logs never auto-deleted
