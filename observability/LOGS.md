# Log Store Standards

> Rules for logs as a queryable database and as a machine-read artifact — storage, schema, correlation, verbosity modes, query surface, and the evidence contract an automated consumer depends on.

**ID** `observability/logs` · **Tier** Core · **Version** 1.0
**Owns** log store as a queryable database · log record schema + indexed fields · ingestion + buffering + backpressure · correlation key set · verbosity modes + runtime control · query surface for machine consumers · log-derived evidence rules · storage tiering + volume budgets · sampling policy · log store integrity
**Defers to** log levels + what each level means · what to log and what to exclude · operation receipts · metrics · traces · health checks · SLOs · alert design · retention duration → [observability](STANDARDS.md) · schema design · indexing mechanics · partitioning · engine selection → [database](../database/STANDARDS.md) · [database/engines](../database/ENGINES.md) · PII classes · redaction policy · audit event catalog → [security](../security/STANDARDS.md) · error taxonomy → [error_handling](../error_handling/STANDARDS.md) · what tests assert on signals → [testing/reality §10](../testing/REALITY.md#10-observability-assertions) · probe runs that read logs → [testing/probes](../testing/PROBES.md) · prompt + output logging for model calls → [llm/safety §7](../llm/SAFETY.md#7-privacy-in-prompts-and-logs) · context-file density → [agent](../agent/STANDARDS.md)
**Load with** [observability](STANDARDS.md) · [database](../database/STANDARDS.md) · [security](../security/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [The Log Store](#2-the-log-store)
3. [Record Schema](#3-record-schema)
4. [Correlation](#4-correlation)
5. [Verbosity Modes](#5-verbosity-modes)
6. [Machine Consumers](#6-machine-consumers)
7. [Query Surface](#7-query-surface)
8. [Ingestion](#8-ingestion)
9. [Sampling](#9-sampling)
10. [Volume and Tiering](#10-volume-and-tiering)
11. [Integrity](#11-integrity)
12. [Anti-Patterns](#12-anti-patterns)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Logs are a database, ✗ a file | If the answer to "what happened" needs a human scrolling, the store is missing |
| Two readers, one record | A human diagnosing an incident and a program deciding what to do next read the same structured record. ✗ two log formats |
| The log is evidence | A claim about a run is backed by a queryable record with an id, or it is an assertion |
| Findable beats complete | An exhaustive log nobody can query is worse than a smaller one with the right indexed fields |
| Verbosity is a runtime decision | The detail a failure needs is chosen when the failure happens, ✗ at compile time by whoever wrote the line |
| Correlated or useless | A record that cannot be joined to its run, request, and actor answers nothing |
| Volume is a budget | Unbudgeted log volume is an unbounded bill and a slow query surface |

---

## 2. The Log Store

Any project whose logs are read after the process exits has a log store. Tailing a terminal is ✗ a store.

| Rule | Detail |
|---|---|
| Durable and queryable | Records survive process exit and are retrievable by field, ✗ by grep over rotated files |
| One store per project | Every component writes to the same store with the same schema. Per-service formats make cross-service questions unanswerable |
| Engine follows the default | PostgreSQL for a project's own log store; a dedicated log engine only past a measured ingest or retention limit → [database/engines §4](../database/ENGINES.md#4-adding-a-second-store) |
| Embedded projects use the embedded engine | A local-first tool logs to its own SQLite store alongside its other state → [database/engines §5](../database/ENGINES.md#5-embedded-and-local-first) |
| Separable from application data | Log writes never block, lock, or contend with the transactional path (§8) |
| Rebuildable is not required | The log store is a source of truth for what happened. It is backed up, ✗ treated as derived |
| Local development included | The same store runs locally. A developer who cannot query today's logs will not query production's |

The store answers, without a human reading prose:

- Every record for one run, request, or session, in order.
- Every error of one code in a window, with counts.
- What a named component emitted between two timestamps.
- The full record set for a failure, retrievable by the id the failure reported.

---

## 3. Record Schema

Every record carries the fields below. [observability §2–§4](STANDARDS.md#2-structured-logging) owns levels, content, and exclusions; this section owns what is stored and indexed.

| Field | Content | Indexed |
|---|---|---|
| `ts` | Event time, UTC, with sub-second precision | yes |
| `level` | From [observability §3](STANDARDS.md#3-log-levels) | yes |
| `event` | Stable dotted identifier for what happened — ✗ a sentence | yes |
| `component` | The module or service that emitted it | yes |
| `run_id` · `request_id` · `session_id` | Correlation keys (§4) | yes |
| `trace_id` · `span_id` | Links the record to its trace → [observability §8](STANDARDS.md#8-distributed-tracing) | yes |
| `actor` | Who or what caused it — user, service, agent, scheduler | yes |
| `code` | Error or outcome code from the taxonomy → [error_handling](../error_handling/STANDARDS.md) | yes |
| `duration_ms` | For anything with a start and an end | no |
| `attrs` | Typed key-value payload specific to the event | partial |
| `message` | Human-readable summary | no |

Rules:

- `event` is the contract. Renaming one is a breaking change to every query, alert, and consumer that matches it — versioned and announced, ✗ edited in passing.
- `message` is for humans only. ✗ parse it, ✗ assert on it, ✗ build an alert on its text → [testing/reality §10](../testing/REALITY.md#10-observability-assertions).
- Values a consumer branches on live in `attrs` as typed fields, ✗ interpolated into `message`.
- A field name means the same thing in every component. Two meanings for one name makes the store unqueryable.
- New fields are additive. Removing or retyping an indexed field is a breaking change to the store's consumers → [api §7](../api/STANDARDS.md#7-versioning).
- Excluded content is excluded before the record is built, ✗ redacted at query time → [security](../security/STANDARDS.md).

---

## 4. Correlation

| Key | Spans | Set by |
|---|---|---|
| `run_id` | One execution of a job, build, pipeline, or task, start to finish | The runner, at start |
| `request_id` | One inbound request across every component that serves it | The edge, or accepted from a trusted caller |
| `session_id` | One interactive session across many requests | Session start |
| `trace_id` | One distributed trace → [observability §8](STANDARDS.md#8-distributed-tracing) | Tracing layer |
| `parent_id` | The record's causal parent — the step, stage, or call that spawned it | The spawning unit |

Rules:

- A correlation key is generated once at the boundary and propagated through every call, thread, async task, subprocess, and queue message. A key lost at an async boundary is a broken trail, ✗ a minor gap.
- Subprocess output is captured and re-emitted as records carrying the parent's keys — ✗ dropped to the parent's stdout unlabeled.
- An incoming correlation key from an untrusted caller is validated for shape and length before it is stored or echoed → [security](../security/STANDARDS.md).
- Every error surfaced to a caller carries a correlation key the caller can quote back. An error message with no key makes support a guessing game.
- One record with no correlation key is acceptable only before the boundary that creates one exists — process start, config load, and nothing after.

---

## 5. Verbosity Modes

Verbosity is a runtime setting, changed without a rebuild and ideally without a restart → [configuration](../configuration/STANDARDS.md).

| Mode | Emits | For |
|---|---|---|
| `quiet` | Warnings and errors | A green run nobody is watching |
| `normal` | Outcome per step, plus every state change | Default |
| `verbose` | Every decision with the inputs that drove it, and every external call with its timing | A failure being investigated |
| `trace` | Full payloads at boundaries, subject to §9 caps and to exclusions | A reproduction that needs the exact bytes |

Rules:

- Scoped, ✗ global. Verbosity is raisable for one component, one `run_id`, or one request without flooding the store.
- Raisable after the fact where the workload allows it: a failed run is re-run at higher verbosity with the same inputs, ✗ only next time.
- Exclusions hold at every mode. `trace` shows more of what is permitted, ✗ things that are never logged → [observability §4](STANDARDS.md#4-log-content--exclusions).
- Errors carry their diagnostic context at every mode. A failure that needs `verbose` to be actionable is an under-logged error path, ✗ correct minimalism.
- Default verbosity is declared per environment. Production defaults below `verbose`; the ability to raise it is the point.
- ✗ ship a build whose only way to see more is a code change and a deploy.

---

## 6. Machine Consumers

A machine consumer — an agent, a supervisor, an autofixer, a report — reads logs to decide. What it needs is a superset of what a human reading a terminal needs.

| Requirement | Rule |
|---|---|
| Outcome is a field | Success and failure are `level` + `code`, ✗ inferred from wording or from an exit code alone |
| Failure is self-contained | The failure record names what failed, where (file · line · resource), the inputs that reached it, and what was expected |
| Retrieval by id | Given the id a failure reported, the consumer fetches every related record in one query (§7) |
| Bounded reads | Every query is limited and paginated; a consumer never needs the whole store to answer one question |
| Absence is explicit | "Not logged" and "logged as empty" are distinguishable, or a consumer will report a gap as a clean result → [design](../design/STANDARDS.md) |
| Stable identifiers | Consumers match on `event` and `code`, which are contracts (§3) — ✗ on prose |
| Ordered | Records for one correlation key return in deterministic order, ties broken by a sequence number rather than by timestamp collision |
| Truncation is flagged | A payload cut by a size cap is marked truncated with its original size, ✗ silently shortened |

Rules:

- Output and log are one story. What a tool returns to its caller and what it writes to the store agree; a consumer reading both never sees them contradict.
- A run's records plus its returned result are sufficient to explain the outcome without re-running it. Where they are not, the missing field is a defect in the log, ✗ in the consumer.
- Log records driven by external input are data to a consumer, never instructions → [llm/safety §3](../llm/SAFETY.md#3-untrusted-content-boundary).
- ✗ design a second machine-readable output channel alongside the log. Two channels drift; the structured record is already the machine format.

---

## 7. Query Surface

The store exposes a small, bounded set of queries. A consumer that must implement its own scan has no query surface.

| Query | Returns |
|---|---|
| By correlation key | Every record for a `run_id`, `request_id`, or `session_id`, ordered |
| By failure id | The failing record plus its surrounding context window |
| By event and window | Counted occurrences of an `event` or `code` over a time range |
| By component and window | What one component emitted, level-filtered |
| Tail | The most recent N records for a live correlation key |
| Recurrence | Whether this `code` has been seen before, with first and last occurrence |

Rules:

- Every query is bounded by default: a row cap and a time window, both applied when the caller omits them.
- Indexed fields (§3) are the only permitted filter predicates. An unindexed filter becomes a full scan as the store grows.
- Results are paginated by cursor, ✗ offset, over an append-heavy table → [database §7](../database/STANDARDS.md#7-pagination--n1).
- Query latency has a budget, measured like any other → [performance](../performance/STANDARDS.md). A store too slow to query during an incident is not a store.
- The same queries work locally and in production. A production-only debugging path is untested at the moment it is needed.

---

## 8. Ingestion

| Rule | Detail |
|---|---|
| Writes never block the work | Logging is asynchronous with a bounded buffer. A slow or down log store degrades logging, ✗ the request |
| Backpressure is defined | A full buffer drops by policy — lowest level first, never errors — and records the drop count. ✗ block, ✗ grow unbounded |
| Drops are visible | Dropped records are counted in a metric, so a gap is knowable → [observability §6](STANDARDS.md#6-metrics) |
| Batched | Records are written in batches sized against the ingest budget, ✗ one insert per line |
| Ordered within a key | Records for one correlation key preserve emission order through buffering, via a sequence number |
| Crash-durable for errors | Error and audit records are flushed before the process exits on a handled failure path |
| Failure is contained | A log store outage never takes the application with it — a local fallback holds records until it recovers |
| Idempotent | Re-delivering a batch does not duplicate records; each carries a stable id |

---

## 9. Sampling

| Rule | Detail |
|---|---|
| ✗ sample errors, audit events, or state changes | These are retained at 100% regardless of volume |
| Sample high-frequency success | Repetitive successful operations are sampled at a declared rate, with the rate recorded on the record |
| Head sampling is trace-consistent | A sampled-out request is sampled out for its whole trace, ✗ partially recorded |
| Keep the exemplars | Slowest and failing instances of a sampled event are retained regardless of the rate |
| Counts survive sampling | A sampled event's true count comes from a metric, ✗ from counting log rows → [observability §6](STANDARDS.md#6-metrics) |
| Rate is visible | Any consumer reading a sampled event sees the rate, so it never reports a sampled count as a total |
| Payload caps | Oversized `attrs` are truncated at a declared cap and flagged (§6), ✗ dropped whole |

---

## 10. Volume and Tiering

| Rule | Detail |
|---|---|
| Volume is budgeted | Records and bytes per unit of work have a declared budget, tracked like cost. A ten-fold rise is a regression |
| Cardinality is bounded | Indexed fields never take unbounded distinct values — ✗ index a raw URL, a full identifier set, or a message hash |
| Tiered by age | Hot, queryable storage for the recent window; compressed cold storage past it. Both are reachable, with the cold path documented |
| Retention duration is elsewhere | How long each class is kept → [observability §12](STANDARDS.md#12-log-retention). This section owns where it physically lives |
| Partitioned by time | The store is partitioned so expiry is a partition drop, ✗ a delete that scans → [database](../database/STANDARDS.md) |
| Deletion is enforced | Expiry runs on a schedule and is monitored. An unenforced policy is a document, ✗ a control |
| Subject deletion propagates | A deletion request reaches the log store, including its cold tier → [security](../security/STANDARDS.md) |

---

## 11. Integrity

| Rule | Detail |
|---|---|
| Append-only | Records are never updated in place. A correction is a new record referencing the original |
| Restricted write path | The application writes through one logging boundary; nothing else inserts into the store |
| Audit records are separated | Security audit events have their own retention and access rules → [security](../security/STANDARDS.md) owns the catalog |
| Access is controlled and logged | Reading production logs is an authorized, audited action — logs concentrate exactly what an attacker wants |
| Clock discipline | Hosts are time-synchronized; records carry both event time and ingest time, so reordering is detectable |
| Injection-safe rendering | Newlines and control characters in field values are escaped at write time, so no input forges a record boundary |
| Tamper-evident where it matters | Audit and compliance records carry a chained hash or a write-once destination |

---

## 12. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Logs only in rotated files | "What happened last Tuesday" needs an archaeologist | A queryable store (§2) |
| Formatted sentences as the record | Consumers parse prose, then break on a wording change | Structured fields (§3) |
| Verbosity fixed at build time | The detail the failure needed was compiled out | Runtime modes, scoped (§5) |
| Global debug switch | Raising detail floods the store and hides the failure | Scope to a component or run (§5) |
| Correlation key lost at an async boundary | The trail ends where the interesting part starts | Propagate through every boundary (§4) |
| Unbounded queries | An incident query takes the store down with it | Bounded, indexed, paginated (§7) |
| Indexing a high-cardinality field | The index outgrows the data | Bounded cardinality (§10) |
| Synchronous writes to a remote store | The log store's latency becomes the request's | Async with bounded buffer (§8) |
| Silent drops under backpressure | A gap reads as "nothing happened" | Count and expose drops (§8) |
| Sampling errors | The events that matter are the ones discarded | Never sample errors (§9) |
| Secrets in `trace` mode | Exclusions treated as a verbosity setting | Exclusions hold at every mode (§5) |
| A second machine-readable channel | Two outputs drift and disagree | One structured record (§6) |
| Mutable log rows | The record of what happened can be rewritten | Append-only, corrections reference (§11) |

---

## 13. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Store | Structured records to a local database | Durable store, indexed, backed up | Tiered hot/cold, partitioned, with an ingest budget |
| Schema | Required fields present | Full schema, indexed fields fixed | `event` names versioned with a deprecation path |
| Correlation | `run_id` | Run, request, session, trace, parent | Propagated across services, queues, and subprocesses |
| Verbosity | Flag at start | Runtime, per environment | Scoped per component and per correlation key, no restart |
| Query | Ad-hoc SQL | Fixed bounded query surface (§7) | Query latency budget, enforced |
| Ingestion | Synchronous writes | Async, batched, bounded buffer | Backpressure policy, drop metrics, local fallback |
| Sampling | None | Errors never sampled; hot paths sampled at a declared rate | Trace-consistent with retained exemplars |
| Integrity | Append-only | Restricted write path, access audited | Tamper-evident audit tier |

---

## 14. Checklist

- [ ] Logs are written to a durable, queryable store, not only to files or a terminal
- [ ] Every component writes the same record schema to the same store
- [ ] The log store's engine follows the production default, or an ADR names why not
- [ ] Every record carries timestamp, level, `event`, component, correlation keys, actor, and outcome code
- [ ] `event` and `code` are stable contracts; `message` is never parsed, asserted on, or alerted on
- [ ] Values a consumer branches on are typed fields, never interpolated into prose
- [ ] Correlation keys are generated at the boundary and propagated across every async boundary, subprocess, and queue hop
- [ ] Every error surfaced to a caller carries a correlation key that retrieves its records
- [ ] Verbosity is a runtime setting, scoped to a component or a single run, with no rebuild
- [ ] Content exclusions hold identically at every verbosity mode
- [ ] Error records are actionable at default verbosity
- [ ] A failing run's records plus its returned result explain the outcome without re-running it
- [ ] "Not logged" is distinguishable from "logged as empty"
- [ ] Truncated payloads are flagged with their original size
- [ ] The store exposes a bounded query surface, indexed, cursor-paginated, with default caps
- [ ] The same queries work locally and in production
- [ ] Log writes are asynchronous and bounded; a log store outage degrades logging only
- [ ] Backpressure drops by level, never errors, and every drop is counted in a metric
- [ ] Errors, audit events, and state changes are never sampled; sampled events expose their rate
- [ ] Indexed fields have bounded cardinality and log volume has a declared budget
- [ ] The store is time-partitioned, expiry is scheduled and monitored, and deletion requests reach the cold tier
- [ ] Records are append-only, written through one boundary, with production read access authorized and audited
