# Observability Standards

Rules for structured logging, metrics, health checks, tracing,
alerting, and audit trails. Language-agnostic — applies to all
projects regardless of runtime or framework.

Composable with: Architecture Standards, Error Handling Standards,
Security Standards, API Standards, DevOps Standards.

---

## Table of Contents

1. [Structured Logging](#1-structured-logging)
2. [Log Levels](#2-log-levels)
3. [Log Content](#3-log-content)
4. [Operation Receipts](#4-operation-receipts)
5. [Metrics](#5-metrics)
6. [Health Checks](#6-health-checks)
7. [Distributed Tracing](#7-distributed-tracing)
8. [Alerting Rules](#8-alerting-rules)
9. [Performance Monitoring](#9-performance-monitoring)
10. [Audit Trail](#10-audit-trail)
11. [Log Retention](#11-log-retention)
12. [Scale Matrix](#12-scale-matrix)
13. [Observability Checklist](#13-observability-checklist)

---

## 1. Structured Logging

All log output is machine-parseable key-value structured data.
See `architecture/STANDARDS.md` §1 principle #11 — universal data format.

### Format Rules

| Rule | Detail |
|---|---|
| Output format | JSON objects, one per line (JSON Lines) |
| ✗ String interpolation | Never embed variables in message strings — use separate fields |
| ✗ Multi-line log entries | Each event = exactly one line; stack traces → dedicated field |
| Field naming | `snake_case`, consistent across all services |
| Timestamp format | ISO 8601 with timezone: `YYYY-MM-DDTHH:MM:SS.sssZ` |
| Timestamp source | UTC always; local time ✗ |
| Encoding | UTF-8; binary data → base64 in dedicated field |

### Required Fields (every log entry)

| Field | Type | Purpose |
|---|---|---|
| `timestamp` | string | ISO 8601 UTC when event occurred |
| `level` | string | Log level (debug/info/warn/error/fatal) |
| `message` | string | Human-readable event summary — static template, no interpolated values |
| `service` | string | Service or application name |
| `correlation_id` | string | Request/operation correlation identifier |

### Optional Standard Fields

| Field | Type | When |
|---|---|---|
| `operation` | string | Function or action name |
| `duration_ms` | number | Timed operations |
| `user_id` | string | Authenticated requests |
| `error_code` | string | Error events |
| `error_message` | string | Error events |
| `stack_trace` | string | Error/fatal events |
| `component` | string | Sub-module within service |
| `environment` | string | Deployment environment |
| `version` | string | Service version or build |
| `span_id` | string | Distributed tracing |
| `trace_id` | string | Distributed tracing |
| `parent_span_id` | string | Distributed tracing |

### Message Field Rules

- Static string template: `"User login succeeded"` — not `"User john logged in at 14:32"`
- Variable data goes in separate fields: `user_id`, `login_time`
- Messages are grep-friendly — identical events produce identical message strings
- Max message length: 200 characters

---

## 2. Log Levels

Five levels. Each has strict criteria — if an event does not meet
criteria, it belongs at a different level.

| Level | Criteria | Examples |
|---|---|---|
| `debug` | Internal state useful only during development or troubleshooting. ✗ enabled in production by default. | Variable values · branch decisions · cache hit/miss |
| `info` | Normal operational events confirming system is working as designed. | Request completed · job started/finished · config loaded |
| `warn` | Unexpected condition that does not prevent operation but indicates potential problem. Requires investigation within days. | Retry succeeded · deprecated API called · pool nearing capacity |
| `error` | Operation failed and cannot be completed. Requires investigation within hours. Does not mean system is down. | Request failed · dependency timeout · validation rejection |
| `fatal` | System cannot continue operating. Process will exit. Requires immediate response. | Port binding failure · missing critical config · corrupt state |

### Level Selection Rules

| Rule | Detail |
|---|---|
| One level per event | ✗ log same event at multiple levels |
| Error ≠ unexpected input | Client sending bad data → `warn`; server failing to process valid data → `error` |
| Retries | First attempt failure → `debug`; final attempt failure → `error`; retry succeeded → `warn` |
| Performance degradation | Slow but within SLA → `debug`; approaching SLA → `warn`; breaching SLA → `error` |
| Startup/shutdown | Normal → `info`; forced/unexpected → `warn` |
| ✗ `error` for flow control | Expected alternative paths (cache miss, 404) are not errors |
| Rate limiting | Repeated identical events → log first occurrence, then aggregate count at interval |

---

## 3. Log Content

### What to Include

| Context | Fields |
|---|---|
| Request identity | `correlation_id` · `trace_id` · `span_id` |
| Operation context | `operation` · `component` · `service` |
| Timing | `timestamp` · `duration_ms` |
| Outcome | `status` · `error_code` · `error_message` |
| Resource identifiers | Entity IDs · file paths · queue names (non-sensitive) |
| Quantitative data | Record count · byte size · retry count |

### What to Exclude (! critical)

| ✗ Never Log | Reason | Alternative |
|---|---|---|
| Passwords, tokens, API keys | Security breach | Log `"auth_method": "api_key"` — not the key itself |
| PII (names, emails, phone, SSN) | Privacy/compliance violation | Log hashed or tokenized identifiers |
| Credit card numbers | PCI-DSS violation | Log last 4 digits only, masked |
| Request/response bodies by default | Size, privacy, secrets | Log at `debug` level behind feature flag |
| Database connection strings | Credential exposure | Log host and database name only |
| Session tokens, cookies | Session hijacking | Log session ID hash |
| Encryption keys, certificates | Key compromise | Log key fingerprint or ID |
| Health check noise | Volume without value | Separate endpoint, ✗ info-level logging |

### Content Boundaries

- Log at operation boundaries: entry, exit, error — not every internal step
- Log before-and-after for state mutations (see §4 Operation Receipts)
- ✗ log inside tight loops — aggregate and log summary after loop completes
- ✗ log in library/utility code — let caller decide logging
- ✗ log raw exceptions as messages — extract code, message, type into fields
- See `error_handling/STANDARDS.md` for error classification rules

---

## 4. Operation Receipts

Every write operation returns a receipt confirming what changed.
See `architecture/STANDARDS.md` §1 principle #18 — log intent before execution.

### Receipt Structure

Every state-changing operation (create, update, delete, execute)
produces a receipt with these fields:

| Field | Type | Purpose |
|---|---|---|
| `operation` | string | What was performed |
| `entity_type` | string | What kind of thing changed |
| `entity_id` | string | Which specific thing changed |
| `status` | string | `success` · `partial` · `failed` · `noop` |
| `timestamp` | string | When operation completed |
| `changes` | object | Before/after values for modified fields |
| `correlation_id` | string | Links receipt to triggering request |
| `actor` | string | Who/what initiated the change |

### Receipt Rules

| Rule | Detail |
|---|---|
| Every write → receipt | ✗ fire-and-forget mutations |
| Noop is valid | If operation produces no change, receipt with `status: noop` |
| Partial is valid | Batch operations report partial success with details |
| Before/after for updates | `changes` field shows previous and new values per field |
| Receipt ≠ log entry | Receipt is returned to caller; logging receipt is separate |
| Receipts are structured data | Same format rules as log entries (JSON, typed fields) |
| ✗ secrets in receipts | Same exclusion rules as log content (§3) |
| Batch receipts | One receipt per batch with item-level status array |

### Receipt Logging

- Log every receipt at `info` level with `event_type: "operation_receipt"`
- Failed operations → log receipt at `error` level
- Noop operations → log receipt at `debug` level
- Receipt log entries include all receipt fields as structured fields

---

## 5. Metrics

Quantitative measurements of system behavior over time.
Three metric types cover all measurement needs.

### Metric Types

| Type | What It Measures | Use When | Example Metric |
|---|---|---|---|
| Counter | Cumulative count, only increases | Counting events | `http_requests_total` |
| Gauge | Current value, goes up and down | Point-in-time state | `active_connections` |
| Histogram | Distribution of values in buckets | Measuring durations, sizes | `request_duration_seconds` |

### Naming Conventions

| Rule | Detail |
|---|---|
| Format | `snake_case`, lowercase |
| Prefix | Service or domain name: `myapp_http_requests_total` |
| Suffix — counters | `_total` |
| Suffix — durations | `_seconds` (use base units) |
| Suffix — sizes | `_bytes` (use base units) |
| Suffix — gauges | Describe current state: `_active`, `_pending`, `_available` |
| ✗ type in name | Not `request_counter` — suffix convention conveys type |
| ✗ status in name | Use labels: `http_requests_total{status="200"}` |
| Unit consistency | Always base units (seconds not milliseconds, bytes not kilobytes) |

### What to Measure

| Category | Metrics |
|---|---|
| Request handling | Total requests · duration histogram · status code distribution · in-flight count |
| Dependencies | Call count · duration · error rate · circuit breaker state per dependency |
| Queues/buffers | Depth (gauge) · enqueue rate · dequeue rate · age of oldest item |
| Resources | CPU usage · memory usage · disk usage · file descriptors · thread/goroutine count |
| Business operations | Items processed · revenue events · user signups · domain-specific counters |
| Cache | Hit/miss ratio · eviction count · size |
| Connection pools | Active · idle · waiting · max capacity |

### Metric Rules

| Rule | Detail |
|---|---|
| Labels are low-cardinality | ✗ user IDs, ✗ request IDs, ✗ timestamps as label values |
| Label values are bounded | Every label has known finite set of values |
| Measure at boundaries | Instrument entry/exit points — not internal implementation |
| Use histograms for latency | ✗ averages alone — they hide tail latency |
| Percentiles from histograms | p50, p90, p95, p99 derived from histogram buckets |
| Counter resets are normal | Counters reset on process restart — tooling handles this |
| ✗ business logic in metrics | Metrics observe, never control flow |

---

## 6. Health Checks

Endpoints that report system operational status.
Two distinct check types serve different purposes.

### Check Types

| Check | Question It Answers | Failure Means | Response Time |
|---|---|---|---|
| Liveness | Is the process running and not deadlocked? | Restart the process | < 100ms, no dependencies |
| Readiness | Can this instance handle traffic? | Remove from load balancer | < 500ms, checks dependencies |

### Liveness Check Rules

- Returns healthy if process is running and responsive
- ✗ check external dependencies — liveness is self-only
- ✗ heavy computation — return immediately
- Failed liveness → orchestrator restarts the process
- Checks: event loop responsive · main thread alive · not in deadlock

### Readiness Check Rules

- Returns healthy if instance can serve requests end-to-end
- Checks all critical dependencies (database, cache, queues)
- Returns unhealthy during startup until initialization completes
- Returns unhealthy during graceful shutdown
- Dependency check uses cached status (< 10s stale), ✗ check on every request

### Health Response Structure

| Field | Type | Purpose |
|---|---|---|
| `status` | string | `healthy` · `degraded` · `unhealthy` |
| `checks` | object | Individual check results keyed by name |
| `checks[name].status` | string | `healthy` · `unhealthy` |
| `checks[name].duration_ms` | number | Time to execute check |
| `checks[name].message` | string | Optional detail on failure |
| `version` | string | Service version |
| `uptime_seconds` | number | Time since process start |

### Dependency Health

| Rule | Detail |
|---|---|
| Classify dependencies | Critical (must have) vs optional (degraded mode ok) |
| Critical dependency unhealthy | Readiness → `unhealthy` |
| Optional dependency unhealthy | Readiness → `degraded` |
| Check timeout | Each dependency check has 2s timeout max |
| Circuit breaker state | Report open circuit breakers as unhealthy dependencies |
| ✗ cascade failure | Health check ✗ trigger reconnection attempts or retries |

### Health Check Rules

| Rule | Detail |
|---|---|
| Separate endpoints | `/health/live` and `/health/ready` — not combined |
| No authentication | Health endpoints are public — load balancers need access |
| No sensitive data | ✗ connection strings, ✗ internal IPs in health response |
| HTTP 200 = healthy | HTTP 503 = unhealthy; ✗ use other status codes |
| Startup grace period | Readiness returns unhealthy until all init completes |
| Frequency | External polling 10–30s; ✗ more frequent than 5s |

---

## 7. Distributed Tracing

Track requests across service boundaries using correlation IDs
and span hierarchies.

### Core Concepts

| Concept | Definition |
|---|---|
| Trace | End-to-end journey of one request through all services |
| Span | One unit of work within a trace (one function, one RPC call) |
| Trace ID | Unique identifier for entire trace — propagated across all services |
| Span ID | Unique identifier for one span within a trace |
| Parent Span ID | Links child span to parent — builds the span tree |
| Correlation ID | Application-level request ID — may differ from trace ID |

### Propagation Rules

| Rule | Detail |
|---|---|
| Pass context explicitly | Trace context flows as function/call parameter, not global state |
| HTTP propagation | `traceparent` header (W3C Trace Context standard) |
| Message queue propagation | Trace context in message metadata/headers |
| Generate at entry point | First service receiving request generates trace ID if absent |
| ✗ generate new trace ID mid-chain | Preserves end-to-end visibility |
| Correlation ID separate | Application correlation ID propagated alongside trace context |

### Span Rules

| Rule | Detail |
|---|---|
| Span naming | `{service}.{operation}` — e.g., `orders.create`, `db.query` |
| ✗ high-cardinality span names | Not `orders.create.12345` — use span attributes for IDs |
| One span per logical operation | External call · database query · queue publish · significant computation |
| ✗ span per trivial function | Internal helpers do not need spans |
| Record duration | Every span has start time and end time |
| Record status | `ok` · `error` with error details as span attributes |
| Span attributes | Add contextual key-value pairs: entity IDs, result counts, status codes |

### What to Trace

| Always | Sometimes | ✗ Never |
|---|---|---|
| Incoming HTTP/RPC requests | Cache operations | Logging calls |
| Outgoing HTTP/RPC calls | Internal queue processing | Field getters/setters |
| Database queries | CPU-intensive computations | Iteration steps |
| Message queue publish/consume | File I/O operations | Utility functions |
| External service calls | Background job execution | Simple data transforms |

---

## 8. Alerting Rules

Alerts notify operators of conditions requiring human action.
Every alert is actionable — if nobody needs to act, it is not an alert.

### Alert Severity

| Severity | Response Time | Notification Channel | Criteria |
|---|---|---|---|
| Critical | Immediate (< 5 min) | Page / phone | Service down · data loss imminent · security breach |
| High | < 30 min | Urgent chat / ticket | Major degradation · error rate spike · dependency failure |
| Medium | < 4 hours | Normal ticket | Gradual degradation · resource trend · minor error increase |
| Low | Next business day | Email / dashboard | Informational threshold · maintenance needed |

### Alert Design Rules

| Rule | Detail |
|---|---|
| Every alert has a runbook | Link to steps operator takes to resolve |
| Alert on symptoms, not causes | "Error rate > 5%" — not "Database connection pool exhausted" |
| ✗ alert on single event | Threshold over time window — not one occurrence |
| Window-based thresholds | `error_rate > 5% for 5 minutes` — not instant spike |
| Alert on rate of change | Sudden shift matters even within absolute threshold |
| ✗ duplicate alerts | One condition → one alert; suppress duplicates during incident |
| Auto-resolve | Alert clears when condition returns to normal |
| ✗ alert fatigue | If alert fires > 5x/week without action → tune or remove |
| Test alerts | Verify alert fires in staging before production |

### What to Alert On

| Alert | Type | Threshold Guidance |
|---|---|---|
| Error rate spike | Counter rate | > 1% of requests over 5 min window |
| Latency degradation | Histogram percentile | p99 > 2x baseline for 5 min |
| Health check failure | Gauge | Unhealthy for > 2 consecutive checks |
| Resource exhaustion | Gauge | CPU > 85%, memory > 90%, disk > 85% for 10 min |
| Queue depth growing | Gauge | Monotonically increasing for > 15 min |
| Certificate expiry | Gauge | < 14 days until expiration |
| Dependency failure | Circuit breaker | Circuit open for > 2 min |
| Zero traffic | Counter rate | 0 requests for > 5 min during expected hours |

### ✗ What Not to Alert On

- Individual request failures (log and count, don't alert)
- Successful deployments (inform, don't alert)
- Auto-recovered transient errors (log, don't alert)
- Expected maintenance windows (suppress alerts)
- Debug-level anomalies (dashboard, don't alert)

---

## 9. Performance Monitoring

Track response times, throughput, and resource usage to detect
degradation before users notice. See `architecture/STANDARDS.md`
§1 principle #29 — explicit resource budgets.

### Response Time Tracking

| Rule | Detail |
|---|---|
| Measure end-to-end | Total time from request received to response sent |
| Measure per-stage | Time in each processing stage (auth, validation, logic, I/O, serialization) |
| Use histograms | ✗ averages alone — track p50, p90, p95, p99 |
| Establish baselines | Record normal performance; alert on deviation from baseline |
| Track by endpoint | Each API endpoint has independent performance metrics |
| Track by dependency | Each external call has independent latency tracking |

### Throughput Tracking

| Metric | Type | Purpose |
|---|---|---|
| Requests per second | Counter rate | System load measurement |
| Operations per second | Counter rate | Business throughput (orders, messages, jobs) |
| Bytes processed per second | Counter rate | Data pipeline throughput |
| Concurrent requests | Gauge | Current load level |
| Queue consumption rate | Counter rate | Worker throughput |

### Resource Usage

| Resource | Metric | Warning Threshold | Critical Threshold |
|---|---|---|---|
| CPU | Utilization % | > 70% sustained | > 85% sustained |
| Memory | RSS / heap usage | > 75% of limit | > 90% of limit |
| Disk | Usage % | > 75% | > 90% |
| Disk I/O | IOPS / throughput | > 70% capacity | > 85% capacity |
| Network | Bandwidth utilization | > 60% capacity | > 80% capacity |
| File descriptors | Open / max | > 70% | > 85% |
| Connection pool | Active / max | > 75% | > 90% |

### Performance Rules

- Compare current performance against rolling 7-day baseline
- Flag regression: p99 latency > 1.5x baseline for > 5 min
- Track performance per deployment — correlate deploys with regressions
- Monitor garbage collection pauses where applicable
- Measure and budget cold-start time separately from steady-state
- ✗ optimize without measurement — instrument first, then improve

---

## 10. Audit Trail

Security-relevant events logged for compliance, forensics, and
accountability. See `security/STANDARDS.md` for access control rules.

### Audit Event Structure

| Field | Type | Purpose |
|---|---|---|
| `timestamp` | string | ISO 8601 UTC |
| `event_type` | string | Categorized action (see table below) |
| `actor` | string | Who performed action (user ID, service ID, system) |
| `actor_ip` | string | Source IP address |
| `resource_type` | string | What kind of thing was accessed/changed |
| `resource_id` | string | Specific resource identifier |
| `action` | string | `create` · `read` · `update` · `delete` · `execute` · `grant` · `revoke` |
| `outcome` | string | `success` · `failure` · `denied` |
| `details` | object | Action-specific context |
| `correlation_id` | string | Links to request trace |

### Events That Require Audit Logging

| Category | Events |
|---|---|
| Authentication | Login success · login failure · logout · token refresh · MFA challenge |
| Authorization | Permission granted · permission denied · role change · privilege escalation |
| Data access | Read of sensitive data · bulk export · report generation |
| Data mutation | Create · update · delete of any business entity |
| Configuration change | Feature flag toggle · setting update · threshold adjustment |
| Administrative action | User create/disable · role assignment · system config change |
| Security event | Brute force detected · anomalous access pattern · key rotation |
| System lifecycle | Startup · shutdown · deployment · migration execution |

### Audit Trail Rules

| Rule | Detail |
|---|---|
| Immutable | Audit logs ✗ modified or deleted through application |
| Separate storage | Audit trail stored separately from application logs |
| Tamper-evident | Integrity protection (checksums, append-only store) |
| Retention | Minimum 1 year; regulated environments may require longer |
| Access controlled | Only security/compliance roles can read audit logs |
| ✗ PII in plain text | Same exclusion rules as log content (§3) — hash or tokenize |
| All failures logged | Failed actions are as important as successes |
| Synchronous write | Audit log write completes before operation response — ✗ async |
| No gaps | Every auditable action produces exactly one audit event |

---

## 11. Log Retention

Rules for rotation, archival, and storage of all observability data.

### Retention Periods

| Data Type | Hot Storage | Warm Storage | Cold/Archive | Total Minimum |
|---|---|---|---|---|
| Application logs | 7 days | 30 days | 90 days | 90 days |
| Audit logs | 30 days | 90 days | 1 year+ | 1 year |
| Metrics | 30 days (full res) | 90 days (downsampled) | 1 year (aggregated) | 1 year |
| Traces | 7 days | 30 days | — | 30 days |
| Error logs | 30 days | 90 days | 1 year | 1 year |
| Health check history | 7 days | 30 days | — | 30 days |

### Rotation Rules

| Rule | Detail |
|---|---|
| Size-based rotation | Rotate when file exceeds 100 MB |
| Time-based rotation | Rotate daily at minimum |
| Compression | Compress rotated logs immediately (gzip/zstd) |
| Naming convention | `{service}-{type}-{date}.log.gz` |
| Atomic rotation | ✗ lose entries during rotation — use rename + reopen |
| Disk budget | Total log storage has explicit max size per service |
| Overflow behavior | When disk budget exceeded → delete oldest non-audit logs first |
| ✗ delete audit logs | Audit logs overflow → alert, ✗ auto-delete |

### Storage Rules

- Hot = queryable in real-time (< 1s search)
- Warm = queryable with delay (< 1 min search)
- Cold = retrievable on request (< 1 hour retrieval)
- Downsample metrics when moving to warm: 1-second → 1-minute resolution
- Aggregate metrics when moving to cold: 1-minute → 1-hour resolution
- Log sensitive data retention per compliance requirements (GDPR, HIPAA, PCI)
- Deletion must be verifiable — confirm data is gone, not just deindexed

---

## 12. Scale Matrix

Apply observability rules proportionally to project scale.

| Capability | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Structured logging (§1) | Print statements ok | JSON to stdout | Centralized log aggregation |
| Log levels (§2) | info + error only | All 5 levels | All 5 levels + dynamic level control |
| Log content (§3) | Minimal fields | Required fields | Full standard + optional fields |
| Operation receipts (§4) | Return success/fail | Status + entity ID | Full receipt with before/after |
| Metrics (§5) | ✗ needed | Request count + errors | Full metrics suite + dashboards |
| Health checks (§6) | ✗ needed | Single `/health` endpoint | Liveness + readiness + dependency checks |
| Distributed tracing (§7) | ✗ needed | Correlation ID only | Full trace/span hierarchy |
| Alerting (§8) | ✗ needed | Error log monitoring | Threshold-based + runbooks |
| Performance monitoring (§9) | Manual timing | Response time logging | Full histogram suite + baselines |
| Audit trail (§10) | ✗ needed | Auth events only | Full audit trail + immutable storage |
| Log retention (§11) | Local files | 30-day retention | Tiered retention + archival |

### Scale Transition

When graduating from one scale to the next:
1. Add structured logging first — everything else depends on it
2. Add health checks second — enables automated deployment
3. Add metrics third — enables alerting and dashboards
4. Add tracing last — requires all services instrumented to be useful

---

## 13. Observability Checklist

### New Service

- [ ] Structured JSON logging configured (§1)
- [ ] All five log levels defined and documented (§2)
- [ ] Correlation ID generated/propagated on every request (§1, §7)
- [ ] PII and secrets excluded from all log output (§3)
- [ ] Operation receipts returned from all write endpoints (§4)
- [ ] Request count, error count, and duration histogram metrics emitted (§5)
- [ ] Metric names follow naming conventions (§5)
- [ ] `/health/live` endpoint implemented (§6)
- [ ] `/health/ready` endpoint implemented with dependency checks (§6)
- [ ] Trace context propagated to/from all external calls (§7)
- [ ] Alerts defined with runbooks for critical paths (§8)
- [ ] Response time baselines established (§9)
- [ ] Audit events emitted for auth and data mutation (§10)
- [ ] Log retention and rotation configured (§11)

### New Endpoint / Operation

- [ ] `info` log at entry and exit
- [ ] `error` log on failure with error code and context
- [ ] Duration metric recorded
- [ ] Operation receipt returned for write operations
- [ ] Trace span created with descriptive name
- [ ] Audit event emitted if security-relevant

### Pre-Production Review

- [ ] No PII or secrets in any log output (test with real data)
- [ ] All alerts have runbooks linked
- [ ] Alert thresholds validated in staging
- [ ] Dashboard shows request rate, error rate, latency (RED method)
- [ ] Log volume estimated — within storage budget
- [ ] Retention policies configured per §11
- [ ] Trace sampling rate set appropriately for production volume
- [ ] Health check responses contain no sensitive data
- [ ] Audit trail verified: no gaps for auditable operations
- [ ] Performance baselines recorded before go-live
