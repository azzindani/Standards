# Data Pipeline Standards

> Rules for pipelines that move and reshape data — ingestion, schema-on-write validation, transformation, batch orchestration, replay, and delivery.

**ID** `data_pipeline` · **Tier** Domain · **Version** 1.0
**Owns** ETL/ELT selection · pipeline DAG · stage contracts · ingestion · pipeline schema enforcement + schema registry · data quality · dead-letter queues · idempotent + replayable batches · watermarks + late data · backfill safety · batch orchestration · pipeline output
**Defers to** input validation classes · injection · secrets → [security](../security/STANDARDS.md) · error taxonomy · boundaries · retry semantics → [error_handling](../error_handling/STANDARDS.md) · log format · metric plumbing · traces · alert routing → [observability](../observability/STANDARDS.md) · table schema · indexes · migrations → [database](../database/STANDARDS.md) · query style → [sql](../sql/STANDARDS.md) · test pyramid · coverage → [testing](../testing/STANDARDS.md) · CI stages → [cicd](../cicd/STANDARDS.md) · experiment tracking · data versioning · model registry · drift → [ml](../ml/STANDARDS.md) · layering · dependency direction → [architecture](../architecture/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [observability](../observability/STANDARDS.md) · [database](../database/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Pipeline Architecture](#2-pipeline-architecture)
3. [Ingestion](#3-ingestion)
4. [Validation](#4-validation)
5. [Transformation](#5-transformation)
6. [Schema Management](#6-schema-management)
7. [Data Quality](#7-data-quality)
8. [Batch Processing](#8-batch-processing)
9. [Streaming and Late Data](#9-streaming-and-late-data)
10. [Idempotency and Replay](#10-idempotency-and-replay)
11. [Error Recovery](#11-error-recovery)
12. [Orchestration and Backfill](#12-orchestration-and-backfill)
13. [Output](#13-output)
14. [Monitoring](#14-monitoring)
15. [Anti-Patterns](#15-anti-patterns)
16. [Scale Matrix](#16-scale-matrix)
17. [Checklist](#17-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Schema-on-write | Data is validated against a declared schema **before** it lands. An unvalidated write is a defect |
| Rows are conserved | `rows_in = rows_out + rows_rejected` at every stage. A row that disappears is a bug, not a filter |
| Idempotent | Re-running a stage or a whole run with identical input yields identical output |
| Replayable | Any window of history can be reprocessed with production code, without hand edits |
| Immutable intermediates | A produced dataset is never mutated; a change produces a new dataset |
| Fail loud, fail early | Bad data halts at the boundary it violates. ✗ propagate downstream and reconcile later |
| No silent drops | Every rejected row lands in a dead letter with its reason |
| Pure transforms | Transform stages have no I/O. Side effects live only in sources and sinks |

Boundary with [ml](../ml/STANDARDS.md): pipelines own batch orchestration, ingestion, and data quality. ML owns dataset versioning, experiment tracking, model registry, and drift. A feature pipeline feeding a model is a pipeline and follows this standard.

---

## 2. Pipeline Architecture

### ETL vs ELT

| Choose | When |
|---|---|
| ELT — load then transform | Destination has compute (warehouse, DB with CTEs) · transform auditable as SQL |
| ETL — transform before load | Destination is flat storage · pre-load validation mandatory · source untrusted · runner resource-constrained |

Default ELT when the destination has compute; ETL otherwise. The choice is recorded, ✗ implicit.

### Pipeline as DAG

Every pipeline is a directed acyclic graph of stages. Cycles are rejected at registration — if B depends on A, neither A nor any ancestor of A may depend on B.

Every stage: single responsibility · declared schema at entry and exit · no side channels (data moves through interfaces, ✗ shared state) · idempotent · emits rows in · rows out · rows rejected · duration.

| Stage type | Role | I/O |
|---|---|---|
| Source | Reads external data in | Yes |
| Validator | Enforces schema + constraints | ✗ |
| Transformer | Reshapes · enriches · aggregates | ✗ |
| Quality gate | Halts on quality breach | ✗ |
| Sink | Writes to destination | Yes |

Minimum viable pipeline: Source → Validator → Sink. Skipping the validator is a defect, ✗ a shortcut.

Every stage boundary declares field names + types + nullability · expected row-count range or ratio to input · invariants (uniqueness, referential integrity, sort order). Contract violation halts the pipeline **at that boundary**.

---

## 3. Ingestion

### Source preflight

| Check | Rule |
|---|---|
| Existence | Source must exist before a read is attempted |
| Permission | Read access verified before extraction starts |
| Size sanity | Deviation > 2× from the historical average halts the run ; explicit override |
| Freshness | Source timestamp within the expected window |
| Format | Confirmed by magic bytes or content-type, ✗ by file extension |

✗ silently skip a missing source. A missing source is a failure with an alert, not a no-op run.

### Encoding

Declared explicitly per source — ✗ platform default. UTF-8 unless the contract says otherwise. Undecodable bytes → reject the record; ✗ substitute replacement characters. BOM stripped if present, detection logged.

### Extraction patterns

| Pattern | When | Watermark |
|---|---|---|
| Full extract | No change tracking; small enough to read whole | None |
| Incremental extract | Source exposes timestamps or sequence numbers | Required |
| Change data capture | Source emits a change log or stream | Log offset |
| Snapshot + diff | Full read compared against the previous snapshot | Snapshot id |

! Watermarks advance **only after** the downstream write has committed. Advancing on read loses data on any crash between read and write.

### Format rules

| Format | Validate | Watch for |
|---|---|---|
| CSV/TSV | Header match · delimiter consistency · quoting | Embedded newlines · mixed delimiters · encoding drift |
| JSON/JSONL | Per-record schema · UTF-8 | Nested nulls · inconsistent field presence |
| Parquet/ORC | File-header schema against the contract | Column type drift between partitions |
| XML | Schema validation when available | Namespace conflicts · encoding declaration mismatch |
| Fixed-width | Field position map · record length | Trailing spaces · truncated records |

---

## 4. Validation

### Three layers, in order

| Layer | Scope | Fails on |
|---|---|---|
| Schema | Field names · types · nullability | Missing or extra field · type mismatch |
| Constraint | Value ranges · patterns · referential integrity | Out of range · format violation · broken key |
| Semantic | Business rules · cross-field logic | Impossible combinations |

Schema failure short-circuits: constraint and semantic checks presuppose a valid schema. Generic input-validation theory and injection classes → [security](../security/STANDARDS.md); this section governs pipeline data only.

### Scope

Row-level (independent per-row constraints) → reject the row · continue the batch · accumulate errors. Batch-level (aggregates: totals, counts, distributions) → reject the whole batch · halt.

### Rejection

| Rule | Detail |
|---|---|
| Dead letter destination | Every rejected row is written with its original payload + reason + stage + run id |
| Rejection threshold | Run fails when the rejection rate exceeds the configured threshold; default 5% |
| Rejections are data | Same retention, schema discipline, and monitoring as primary output |
| ✗ silent drops | ! Every input row appears in the output or in the dead letter. Never neither |
| Row accounting | `rows_in = rows_out + rows_rejected` asserted at every stage — mismatch halts the run |

---

## 5. Transformation

| Rule | Detail |
|---|---|
| Pure | Transform stages perform no I/O — ✗ DB write · ✗ API call · ✗ file mutation |
| Deterministic | Same input + same config → identical output, every run |
| Immutable intermediates | Downstream reads an intermediate, ✗ modifies it — a change produces a new intermediate |
| Isolated | Stages communicate via declared outputs only — ✗ shared mutable state · ✗ globals · ✗ assumed execution order beyond the DAG. Config injected per stage |

### Patterns and cardinality

| Pattern | Cardinality constraint |
|---|---|
| Map | Output rows = input rows |
| Filter | Output ≤ input; filtered count logged |
| Flatten | Output ≥ input; parent keys preserved |
| Aggregate | Output < input; grouping keys declared |
| Join | Join type declared; match and miss rates logged |
| Pivot / unpivot | Axis columns declared explicitly |
| Enrich | Lookup source declared; missing-key behavior declared |

Every transform declares its expected cardinality change (1:1 · 1:N · N:1 · N:M). Actual cardinality is asserted against the declaration.

### Ordering

Clean → validate → enrich → reshape → filter.

Filtering runs last so that enrichment and audit trail exist for the rows that get dropped. Deviation requires a recorded reason.

---

## 6. Schema Management

Every pipeline registers its input and output schemas. The registry provides version history · automated compatibility check before registration · lookup by name and version · lineage from schema to producing and consuming pipelines.

### Evolution

| Change | Backward compatible | Forward compatible | Action |
|---|---|---|---|
| Add optional field | Yes | Yes | New version |
| Add required field | ✗ | Yes | Major bump · coordinate consumers |
| Remove field | Yes, if optional | ✗ | Deprecate → migrate consumers → remove |
| Rename field | ✗ | ✗ | Remove + add; alias during migration |
| Widen type (int → long) | Yes | ✗ | New version |
| Narrow type | ✗ | ✗ | Major bump · validate every existing value fits |
| Required → optional | Yes | ✗ | New version |
| Optional → required | ✗ | Yes | Major bump · backfill nulls first |

### Compatibility modes

Backward (new schema reads old data) → consumers upgrade first · Forward (old schema reads new data) → producers upgrade first · Full (both) → producer and consumer deploy independently · None → coordinated breaking cutover only.

Default backward. Shared data platforms: full.

Schema version = monotonic integer, ✗ semver. Producer and consumer each declare a min + max compatible version; the pipeline refuses to start when the ranges do not overlap. ! An unregistered column, a missing column, or a retyped column halts the run — ✗ auto-adapt.

Physical table schema, indexes, and DB migrations → [database](../database/STANDARDS.md).

---

## 7. Data Quality

### Dimensions

| Dimension | Metric | Threshold |
|---|---|---|
| Completeness | Non-null rate per required field | Per-field, in the contract |
| Uniqueness | Duplicate rate on declared keys | 0% for primary keys; configurable otherwise |
| Freshness | Age of the newest source record in the output | Per-pipeline SLA |
| Accuracy | Rate passing format and range checks | Per-field, in the contract |
| Consistency | Cross-field rule pass rate | 100% for hard rules |
| Volume | Row count vs expected range | ± configured % of the rolling average |

### Profiling

Profile on first ingestion and every run thereafter: cardinality per column · null rate per column · min/max/mean/stddev for numerics · top-N value frequencies · string length distribution · pattern frequency for dates and ids. Profiles are versioned artifacts stored with the run; each run is compared against the baseline.

### Anomaly rules

Alert on: volume spike or drop beyond the configured band · null-rate rise beyond the configured band for any field · numeric mean or stddev beyond the configured σ from baseline · arrival after the SLA window.
! Halt on: schema drift vs the registered schema.

Thresholds are configuration, ✗ hardcoded — tolerances differ per pipeline.

### Data contract

A contract binds producer and consumer. Required elements: schema · freshness SLA · quality threshold per dimension · owner · notification channel · versioning policy · breaking-change process. Contracts are versioned artifacts stored beside the pipeline definition and enforced in CI ([cicd](../cicd/STANDARDS.md)).

---

## 8. Batch Processing

### Chunking

| Rule | Detail |
|---|---|
| ✗ load the full dataset into memory | Process in bounded chunks |
| Chunk size is configuration | Default 10,000 rows; tuned per pipeline |
| Respect record integrity | ✗ split mid-record — multi-line JSON, nested structures |
| Chunks are independent | No state carried between chunks except declared accumulators |

### Memory

Streaming read → source unbounded or larger than memory · chunk-and-flush → per-chunk results fit in memory · memory-mapped read → random access over a large file · spill-to-disk → sort/group-by accumulator exceeds its budget.

Every stage declares a memory budget. Exceeding it → spill or fail with a clear error. ✗ die of OOM.

### Progress and partial failure

| Rule | Detail |
|---|---|
| Progress per chunk | Structured event: chunks done · chunks total · rows processed · ETA after the first chunk |
| Stall detection | No progress event within the configured timeout → alert |
| Row fails validation | Dead letter · continue |
| Chunk fails, transient | Retry with backoff · max 3 attempts |
| Chunk fails, persistent | Chunk rows → dead letter · continue remaining chunks |
| Stage fails | Halt · recover per §11 |

The rejection threshold is cumulative across chunks: exceeding it halts the run even when every individual chunk succeeded.

---

## 9. Streaming and Late Data

| Factor | Batch | Streaming |
|---|---|---|
| Latency SLA | Minutes–hours | Seconds–minutes |
| Volume | Bounded, known | Unbounded, continuous |
| Complexity | Complex joins and aggregations | Simple transforms and filters |
| Ordering | Natural | Enforced via watermarks |
| Reprocessing | Full rerun | Replay from offset |

Default to batch. Batch is simpler to test, debug, and recover. Adopt streaming only when a latency SLA demands it.

Hybrids: **Lambda** — batch layer for accuracy + speed layer for freshness, merged at query time · **Kappa** — stream only, batch = replay from the beginning · **stream-to-batch landing** — stream writes micro-batches, batch reads them on schedule.

### Windows and watermarks

Windows: tumbling (non-overlapping fixed intervals) · sliding (overlapping — moving averages) · session (grouped by activity gaps) · global (lifetime accumulators).

Every windowed operation declares window size · allowed lateness · trigger policy (on-time · early · late).

| Late data | Rule |
|---|---|
| Within allowed lateness | Accepted → window result updated |
| Beyond allowed lateness | Dead letter, ✗ silent discard |
| Watermark | Advances monotonically; ✗ move backward to admit late data |
| Out-of-order tolerance | Declared per stream, not assumed to be zero |

---

## 10. Idempotency and Replay

Every stage, and the run as a whole, produces identical output when re-run on identical input. This is what makes retries, backfills, and crash recovery safe.

| Pattern | Mechanism | Best for |
|---|---|---|
| Overwrite | Deterministic output location; re-run overwrites | File sinks |
| Upsert | Insert-or-update on a natural key | Database sinks |
| Dedup key | Deterministic record id; duplicates rejected at the sink | Streaming sinks |
| Transactional write | Output + checkpoint committed in one transaction | Database-backed pipelines |
| Partition swap | Write a staging partition → atomic swap | Partitioned stores |

Record id is derived from the business key — ✗ random UUID, it defeats deduplication. The sink rejects duplicate writes. At-least-once + dedup = exactly-once; prefer it over an exactly-once delivery protocol. Streaming sinks declare a dedup window.

Inherently non-idempotent effects (email, payment, external API call) are isolated: gate behind a durable "processed" marker checked before execution, record completion durably before continuing, and — when the check and the effect cannot be atomic — make the downstream consumer duplicate-tolerant.

---

## 11. Error Recovery

### Checkpoints

Persisted at stage boundaries and at chunk boundaries within a stage. Content = input offset + stage state — enough to resume without re-reading processed data. Storage is durable (file system or database), ✗ in-memory only. On restart the run reads the checkpoint and skips completed chunks.

### Dead-letter queues

| Property | Rule |
|---|---|
| Present | Every pipeline has a dead-letter destination |
| Record | Original payload · error message · stage · timestamp · run id · schema version |
| Replayable | ! Dead-letter output can be fed back in as pipeline input without transformation |
| Retention | Equal to primary output. ✗ expire dead letters first |
| Monitored | Dead-letter growth rate is an alerting signal, not a silent sink |

### Retry and poison pills

| Failure | Strategy |
|---|---|
| Transient — network timeout, lock contention | Exponential backoff + jitter · max 3 attempts |
| Persistent — schema mismatch, corrupt record | Dead letter immediately. ✗ retry |
| Ambiguous | Retry once; same error → treat as persistent |
| Resource exhaustion — OOM, disk full | Halt · alert. ✗ retry without intervention |

A poison pill crashes the stage rather than failing validation. On a chunk crash: bisect the chunk to isolate the offending record(s) → quarantine to the dead letter with crash details → resume the remaining records → alert the owner.

✗ let one bad record halt a pipeline permanently. ✗ skip a poison record without recording it.

Retry semantics, backoff theory, and error class taxonomy → [error_handling](../error_handling/STANDARDS.md).

---

## 12. Orchestration and Backfill

| Rule | Detail |
|---|---|
| Explicit dependencies | Declared, ✗ inferred from definition order |
| Parallel by default | Stages with no dependency relation run concurrently |
| Fail fast on the critical path | A critical-path failure halts dependent stages immediately |
| Partial success allowed | Independent branches continue when a sibling branch fails |
| Deterministic plan | Same DAG + config → same execution plan |
| Cycles rejected | At registration, not at runtime |
| Overlap policy | A scheduled run whose predecessor is still running skips or queues — declared per pipeline. ✗ overlap |
| External dependency | Health-checked before the run starts, ✗ discovered by failing mid-run |

Trigger: cron/interval for predictable sources · event for low-latency sources · upstream-completion for chained pipelines · manual for backfill and debugging.

### Backfill safety

| Rule | Detail |
|---|---|
| Same code | Backfill runs production pipeline code. ✗ a one-off script |
| Parameterized | Pipeline accepts a start/end bound and processes only that window |
| Staged | Backfill writes to a staging location → validated → promoted. ✗ write straight over live output |
| Rate limited | Runs at lower priority than live pipelines; ✗ starve them |
| Idempotent | Re-running the same range produces identical output |
| Bounded | Range is explicit and finite; an unbounded backfill is rejected |
| Recorded | Backfill runs are tagged and distinguishable from scheduled runs in metrics |

---

## 13. Output

Format: warehouse · lake · downstream pipeline · archive → columnar (Parquet) or the destination's native load format — schema embedded, splittable, compressed. API consumers → JSON/JSONL. Spreadsheet users → CSV with explicit encoding + header row.

### Partitioning

Default key = time (year/month/day). Alternative = a high-cardinality dimension consumers filter on. Target 128 MB–1 GB compressed per partition file. ✗ over-partition — many small files destroy read performance. The partition layout is part of the contract: changing it is a breaking change.

### Atomic write and verification

| Rule | Detail |
|---|---|
| Temp then rename | Write to a temp location → atomic rename. ✗ write directly to the final path |
| Transactional sinks | Wrap sink writes in a transaction; commit on success, roll back on failure |
| ! No partial output visible | A consumer sees the previous complete version or the new complete version. Never a half-written one |
| Row count | Output count matches the transform accounting |
| Schema | Output matches the declared output schema exactly |
| Checksum | Computed and stored beside the output for consumer verification |
| Empty output | 0 rows → fail, unless the pipeline explicitly declares empty output legal |

---

## 14. Monitoring

Log format, metric plumbing, tracing, and alert routing → [observability](../observability/STANDARDS.md). This section names only the **pipeline-specific signals** that must exist.

| Signal | Emitted per |
|---|---|
| Run status: success · failure · partial | Run |
| Duration | Run and stage |
| Rows in · rows out · rows rejected | Stage |
| Rejection rate vs threshold | Stage |
| Dead-letter volume and growth rate | Run |
| Data freshness = now − newest source timestamp **in the output** | Output dataset |
| Watermark / checkpoint lag | Stream or incremental source |
| Quality dimension scores (§7) | Run |
| Peak memory · spill events | Stage |

| Rule | Detail |
|---|---|
| Freshness measures data age | ✗ measure pipeline run time and call it freshness. Warn at 80% of the SLA window |
| Alert content | What failed · pipeline · stage · run id · link to logs · dead-letter location |
| Actionable only | Tune thresholds, group related alerts, suppress duplicates within a window |
| SLA tracking | Freshness · completeness · quality · success rate · latency, over 7/30/90-day windows |

---

## 15. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| Watermark advanced on read | Crash between read and write loses data | Advance after the write commits (§3) |
| Rows filtered without accounting | Silent data loss discovered months later | `rows_in = rows_out + rows_rejected` (§4) |
| Rejected rows logged and dropped | Unreplayable loss | Dead letter with payload + reason (§4, §11) |
| Transform that writes to a DB | Untestable, non-idempotent, unreplayable | Side effects only in sinks (§5) |
| Auto-adapting to schema drift | Corrupt data lands with no signal | Drift halts the run (§6) |
| Random UUID as record id | Deduplication impossible; replay duplicates everything | Deterministic business key (§10) |
| Backfill via a one-off script | Backfilled data differs from live data | Parameterized production code (§12) |
| Backfill written over live output | Corrupt output with no rollback | Staging → validate → promote (§12) |
| Write straight to the final path | Consumers read a half-written file | Temp → atomic rename (§13) |
| Full dataset loaded to memory | OOM at the first volume spike | Bounded chunks (§8) |
| Freshness measured as run time | A pipeline that runs on stale data looks healthy | Measure data age (§14) |
| Retrying a corrupt record forever | Pipeline wedged on one row | Persistent failure → dead letter (§11) |

---

## 16. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Volume per run | < 1 GB | 1 GB–1 TB | > 1 TB |
| Scheduling | Cron or manual | Orchestrator with a full DAG | Federated orchestration, cross-pipeline lineage |
| Schema registry | Versioned file in the repo | Central registry + CI compatibility check | Federated registry with governance + contract tests in CI |
| Validation | Schema + basic constraints | Full three-layer validation | Contracts with SLAs, enforced in CI |
| Quality | Row counts + null checks | Profiling + anomaly alerts | Quality gates blocking promotion |
| Recovery | Manual rerun | Checkpoint/restart + dead letter + auto-retry | Self-healing with automated backfill |
| Idempotency | Overwrite output | Upsert on key | Transactional checkpoint + dedup across systems |
| Monitoring | Log inspection | Metrics + SLA alerting | SLA dashboards + lineage + impact analysis |

Move right only when the current column's rules are fully met.

---

## 17. Checklist

- [ ] ETL vs ELT choice recorded with its reason
- [ ] Pipeline is an acyclic DAG with explicitly declared stage dependencies
- [ ] Every stage declares input and output schema, and expected cardinality change
- [ ] Pipeline contains at least Source → Validator → Sink
- [ ] Source preflight checks existence, permission, size, freshness, and format
- [ ] Encoding declared explicitly; undecodable bytes rejected, never substituted
- [ ] Watermarks advance only after the downstream write commits
- [ ] Validation runs schema → constraint → semantic, in that order
- [ ] Rejected rows land in a dead letter with payload, reason, stage, and run id
- [ ] `rows_in = rows_out + rows_rejected` asserted at every stage
- [ ] Rejection-rate threshold configured and enforced cumulatively across chunks
- [ ] Transform stages are pure — zero I/O, deterministic, no shared mutable state
- [ ] Transform order is clean → validate → enrich → reshape → filter
- [ ] All schemas registered; compatibility checked before registration
- [ ] Schema drift halts the run; ✗ auto-adaptation
- [ ] Quality thresholds configured not hardcoded; baseline profile compared each run
- [ ] Full dataset never loaded into memory; chunk size and memory budget declared per stage
- [ ] Windowed operations declare window size, allowed lateness, and trigger policy
- [ ] Late data beyond allowed lateness goes to the dead letter, never dropped
- [ ] Re-running with identical input produces identical output
- [ ] Deduplication uses a deterministic business key, never a random id
- [ ] Checkpoints persisted at stage and chunk boundaries, durably
- [ ] Dead-letter output is replayable as pipeline input and retained as long as primary output
- [ ] Poison pills are isolated, quarantined, and alerted; the pipeline continues
- [ ] Backfill uses production code, is range-parameterized, and writes to staging first
- [ ] Scheduled runs declare an overlap policy; overlapping runs never occur
- [ ] Writes are atomic (temp → rename); no partial output is ever visible
- [ ] Output validated: row count, schema, checksum; empty output explicitly handled
- [ ] Freshness measured as data age, not run time, and alerted at 80% of the SLA window
- [ ] Alerts carry pipeline, stage, run id, and dead-letter location
