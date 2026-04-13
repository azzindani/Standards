# Data Pipeline Standards

Rules for building data pipelines — ingestion, validation, transformation,
quality enforcement, and output. Language-agnostic. Applies to batch,
streaming, and hybrid pipelines at any scale.

Derived from: MapReduce, Apache Beam model, Kappa/Lambda architectures,
dbt contracts, Great Expectations, Schema Registry (Confluent), Airflow DAG
model, event sourcing, ACID transactions, Unix pipes, copy-on-write semantics.

Composable with: architecture/STANDARDS.md · error_handling/STANDARDS.md ·
observability/STANDARDS.md · database/STANDARDS.md · configuration/STANDARDS.md

---

## Table of Contents

1. [Pipeline Architecture](#1-pipeline-architecture)
2. [Data Ingestion](#2-data-ingestion)
3. [Data Validation](#3-data-validation)
4. [Data Transformation](#4-data-transformation)
5. [Data Quality](#5-data-quality)
6. [Schema Management](#6-schema-management)
7. [Batch Processing](#7-batch-processing)
8. [Streaming vs Batch](#8-streaming-vs-batch)
9. [Idempotency](#9-idempotency)
10. [Error Recovery](#10-error-recovery)
11. [Orchestration](#11-orchestration)
12. [Output & Export](#12-output--export)
13. [Monitoring](#13-monitoring)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Pipeline Architecture

### ETL vs ELT Selection

| Factor | ETL (transform before load) | ELT (load then transform) |
|---|---|---|
| Destination has compute | ✗ | Preferred |
| Complex pre-validation needed | Preferred | Possible with staging |
| Source data untrusted | Preferred — validate early | Validate in staging layer |
| Destination is data warehouse | Overhead | Preferred |
| Resource-constrained environment | Preferred — reduce load volume | Avoid |
| Audit trail required | Transform logs explicit | Transform in SQL — auditable |

Default: ELT when destination supports compute (warehouse, database with CTEs). ETL when destination is flat storage or when pre-load validation is mandatory.

### Pipeline as DAG

Every pipeline is a directed acyclic graph (DAG) of stages. Each stage:

| Property | Rule |
|---|---|
| Single responsibility | One logical operation per stage |
| Explicit inputs/outputs | Declared schema at entry and exit |
| No side channels | Data flows through stage interfaces, not shared state |
| Idempotent | Re-running stage with same input → same output |
| Observable | Emits metrics: rows in, rows out, rows rejected, duration |

Cycles in the DAG are forbidden. If stage B depends on stage A, A must never depend on B or any descendant of B.

See architecture/STANDARDS.md §1 — principles #1 (single in/out), #25 (unidirectional data flow).

### Stage Classification

| Stage Type | Purpose | Examples |
|---|---|---|
| Source | Reads external data into pipeline | File reader, API poller, DB extractor |
| Validator | Enforces schema + constraints | Type checker, constraint validator |
| Transformer | Reshapes, enriches, aggregates | Join, pivot, normalize, denormalize |
| Quality Gate | Blocks pipeline on quality failure | Null rate check, distribution check |
| Sink | Writes data to destination | DB writer, file exporter, API pusher |

Every pipeline has at minimum: Source → Validator → Sink. Skipping validation is a defect.

### Data Contracts Between Stages

Each stage-to-stage boundary has an explicit contract:

- Schema: field names, types, nullability
- Cardinality: expected row count range (min/max or ratio to input)
- Invariants: uniqueness constraints, referential integrity, sort order

Contract violations halt the pipeline at the boundary — ✗ propagate bad data downstream.

---

## 2. Data Ingestion

### Source Validation

Before reading data, validate source accessibility and basic properties:

| Check | Rule |
|---|---|
| Existence | Source file/endpoint/table must exist before read attempt |
| Permissions | Verify read access before starting extraction |
| Size sanity | Compare source size to expected range — reject anomalous sizes |
| Freshness | Verify source timestamp is within expected window |
| Format detection | Confirm format matches expectation (file magic bytes, content-type header) |

✗ Silently skip missing sources. ✗ Proceed if source size deviates >2× from historical average without explicit override.

### Encoding Handling

| Rule | Detail |
|---|---|
| Declare encoding explicitly | ✗ rely on platform default encoding |
| UTF-8 default | Unless source contract specifies otherwise |
| Detect and fail on mismatch | If declared encoding fails to decode, reject — ✗ replace with ? |
| BOM handling | Strip BOM if present, log its detection |

### Bulk Input Patterns

| Pattern | When |
|---|---|
| Full extract | Source has no change tracking; small enough for full read |
| Incremental extract | Source supports timestamps/sequence numbers; large datasets |
| Change data capture (CDC) | Source provides change log/stream |
| Snapshot + diff | Full extract with comparison to previous snapshot |

Track high-water marks for incremental extracts. Persist marks only after successful downstream processing.

### File Format Rules

| Format | Validation | Watch for |
|---|---|---|
| CSV/TSV | Header row match, delimiter consistency, quote handling | Embedded newlines, mixed delimiters, encoding |
| JSON/JSONL | Schema validation per record, UTF-8 enforcement | Nested nulls, inconsistent field presence |
| Parquet/ORC | Schema in file header — validate against contract | Column type drift between partitions |
| XML | XSD validation if schema available | Namespace conflicts, encoding declaration mismatch |
| Fixed-width | Field position map required; validate record length | Trailing spaces, truncated records |

---

## 3. Data Validation

### Validation Layers

Validation operates at three layers, each mandatory:

| Layer | Scope | Fails on |
|---|---|---|
| Schema | Field names, types, nullability | Missing/extra fields, type mismatch |
| Constraint | Value ranges, patterns, referential integrity | Out-of-range, format violation, broken FK |
| Semantic | Business rules, cross-field logic | Inconsistent field combinations, impossible values |

Execute in order: schema → constraint → semantic. If schema validation fails, skip constraint and semantic — they depend on valid schema.

### Row-Level vs Batch-Level Validation

| Scope | Use when | Behavior on failure |
|---|---|---|
| Row-level | Independent row constraints | Reject row, continue batch, accumulate errors |
| Batch-level | Aggregate constraints (totals, counts, distributions) | Reject entire batch |

Row-level failures accumulate into a rejection report. Batch-level failures halt pipeline immediately.

### Rejection Handling

| Rule | Detail |
|---|---|
| Rejected rows → dead letter output | Separate output with original data + rejection reason |
| Rejection threshold | Pipeline fails if rejection rate exceeds configured threshold (default: 5%) |
| Rejection is data | Dead letter output has same retention and schema as primary output |
| No silent drops | Every input row must appear in output OR dead letter — ✗ disappear rows |

Row accounting: `rows_in = rows_out + rows_rejected`. Verify this identity at every stage.

See error_handling/STANDARDS.md — partial failure accumulation patterns.

---

## 4. Data Transformation

### Pure Transform Rule

Every transformation stage is a pure function: input data → output data. No database writes, no API calls, no file mutations inside transforms. Side effects belong in Source and Sink stages only.

See architecture/STANDARDS.md §1 — principle #2 (I/O or logic, never both).

### Immutable Intermediates

Intermediate data between stages is immutable once produced. Downstream stages read it; ✗ modify it. If a stage needs modified data, produce a new intermediate.

See architecture/STANDARDS.md §6 — copy-on-write, immutability default.

### Stage Isolation Rules

| Rule | Detail |
|---|---|
| No shared mutable state | Stages communicate via declared outputs only |
| No implicit ordering | Stage reads only declared inputs — ✗ assume execution order beyond DAG |
| No cross-stage globals | Configuration injected per-stage, not via global variables |
| Deterministic output | Same input + same config → identical output every run |

### Common Transform Patterns

| Pattern | Description | Constraint |
|---|---|---|
| Map | 1:1 row transformation | Output row count = input row count |
| Filter | Remove rows matching predicate | Output ≤ input; log filter count |
| Flatten | Unnest nested structures | Output ≥ input; preserve parent keys |
| Aggregate | Reduce rows to summary | Output < input; declare grouping keys |
| Join | Combine two inputs on key | Declare join type; log match/miss rates |
| Pivot/Unpivot | Reshape columns ↔ rows | Declare axis columns explicitly |
| Enrich | Add fields from lookup source | Declare lookup source; handle missing keys |

Every transform declares expected cardinality change (1:1, 1:N, N:1, N:M). Pipeline validates actual cardinality against declaration.

### Transformation Ordering

Within a pipeline, transformations follow this order:

1. **Clean** — fix encoding, trim whitespace, normalize case
2. **Validate** — apply constraints after cleaning
3. **Enrich** — add derived/lookup fields
4. **Reshape** — pivot, flatten, aggregate
5. **Filter** — remove rows (after enrichment to preserve audit trail)

Deviations from this order require documented justification.

---

## 5. Data Quality

### Quality Dimensions

| Dimension | Metric | Threshold |
|---|---|---|
| Completeness | % of non-null values per required field | Per-field threshold in contract |
| Uniqueness | Duplicate rate on declared unique keys | 0% for primary keys; configurable for others |
| Freshness | Time since source last updated | SLA-defined per pipeline |
| Accuracy | % of values passing format/range checks | Per-field threshold in contract |
| Consistency | Cross-field rule pass rate | 100% for hard rules; configurable for soft |
| Volume | Row count vs expected range | ±configured % of historical average |

### Data Profiling

Run profiling on first ingestion and periodically thereafter:

| Profile Metric | Purpose |
|---|---|
| Cardinality per column | Detect low-entropy or constant columns |
| Null rate per column | Baseline for completeness monitoring |
| Min/max/mean/stddev for numerics | Baseline for anomaly detection |
| Top-N value frequencies | Detect distribution shifts |
| String length distribution | Detect truncation or padding issues |
| Pattern frequency (dates, IDs) | Detect format drift |

Store profiles as versioned artifacts. Compare current run profile against baseline — alert on drift beyond configured thresholds.

### Anomaly Detection Rules

| Rule | Detail |
|---|---|
| Volume spike/drop | Row count deviates >configured % from rolling average → alert |
| Schema drift | New/missing/retyped columns vs registered schema → halt |
| Null spike | Null rate for any field increases >configured % above baseline → alert |
| Distribution shift | Numeric field mean/stddev deviates >configured σ from baseline → alert |
| Late arrival | Data arrives after SLA window → alert |

Anomaly thresholds are configuration, not hardcoded. Different pipelines have different tolerances.

### Data Contracts

A data contract defines the agreement between producer and consumer:

| Element | Required |
|---|---|
| Schema (fields, types, nullability) | Yes |
| Freshness SLA | Yes |
| Quality thresholds per dimension | Yes |
| Owner (team/person) | Yes |
| Notification channels | Yes |
| Versioning policy | Yes |
| Breaking change process | Yes |

Contracts are versioned artifacts stored alongside pipeline definitions. Contract changes follow schema evolution rules (§6).

---

## 6. Schema Management

### Schema Registry

Every pipeline registers input and output schemas in a central registry. The registry provides:

| Capability | Rule |
|---|---|
| Version history | Every schema change creates new version |
| Compatibility check | Automated check before registration |
| Discovery | Any consumer can look up schema by name + version |
| Lineage | Track which pipelines produce/consume each schema |

### Schema Evolution Rules

| Change Type | Backward Compatible | Forward Compatible | Action |
|---|---|---|---|
| Add optional field | Yes | Yes | Register new version |
| Add required field | ✗ | Yes | Major version bump; coordinate consumers |
| Remove field | Yes (if optional) | ✗ | Deprecate first; remove after consumer migration |
| Rename field | ✗ | ✗ | Treat as remove + add; alias during migration |
| Change type (widening) | Yes (int→long) | ✗ | Register new version |
| Change type (narrowing) | ✗ | ✗ | Major version bump; validate data fits |
| Change nullability (required→optional) | Yes | ✗ | Register new version |
| Change nullability (optional→required) | ✗ | Yes | Major version bump; backfill nulls first |

### Compatibility Modes

| Mode | Rule | Use when |
|---|---|---|
| Backward | New schema reads old data | Consumers upgrade before producers |
| Forward | Old schema reads new data | Producers upgrade before consumers |
| Full | Both backward and forward | Independent deployment of producer/consumer |
| None | No compatibility guaranteed | Breaking migration with coordinated cutover |

Default: backward compatible. Full compatibility required for shared data platforms.

### Schema Versioning

- Schema version = monotonically increasing integer (not semver)
- Producer declares minimum and maximum compatible schema versions
- Consumer declares minimum and maximum compatible schema versions
- Pipeline refuses to run if producer/consumer version ranges don't overlap

See database/STANDARDS.md — schema design, migration patterns.

---

## 7. Batch Processing

### Chunking Strategy

| Rule | Detail |
|---|---|
| Never load full dataset into memory | Process in bounded chunks |
| Chunk size = configuration | Default: 10,000 rows; tunable per pipeline |
| Chunk boundaries respect record integrity | ✗ split mid-record (multi-line JSON, nested structures) |
| Each chunk is independently processable | No state carried between chunks except explicit accumulators |

### Memory Management

| Pattern | When |
|---|---|
| Streaming read (row-by-row) | Source is unbounded or larger than available memory |
| Chunk-and-flush | Intermediate results fit in memory per chunk; flush after each |
| Memory-mapped files | Random access needed on large files; OS manages paging |
| Spill-to-disk | Accumulator (sort, group-by) exceeds memory budget |

Declare memory budget per stage. If stage exceeds budget → spill to disk or fail, ✗ crash with OOM.

See architecture/STANDARDS.md §1 — principle #29 (explicit resource budgets).

### Progress Reporting

| Rule | Detail |
|---|---|
| Report progress per chunk | Emit: chunks completed, total chunks (if known), rows processed |
| Estimated time remaining | After first chunk, extrapolate; update each chunk |
| Machine-readable format | Structured log/event, not free text |
| No progress → stall detection | If no progress event in configured timeout → alert |

### Partial Failure Handling

| Failure Scope | Response |
|---|---|
| Single row fails validation | Route to dead letter; continue processing |
| Chunk fails (transient) | Retry chunk with backoff; max 3 attempts |
| Chunk fails (persistent) | Route failed chunk rows to dead letter; continue remaining chunks |
| Stage fails entirely | Halt pipeline; trigger recovery (§10) |

Rejection threshold applies across chunks: if cumulative rejection rate exceeds threshold, halt pipeline even if individual chunks succeed.

---

## 8. Streaming vs Batch

### Selection Criteria

| Factor | Batch | Streaming | Hybrid |
|---|---|---|---|
| Latency requirement | Minutes–hours acceptable | Seconds–minutes required | Mixed SLAs |
| Data volume | Bounded, known size | Unbounded, continuous | Both patterns present |
| Processing complexity | Complex joins/aggregations | Simple transforms/filters | Complex on batch; simple on stream |
| Resource availability | Can burst; off-peak scheduling | Constant resource allocation | Tiered allocation |
| Ordering guarantees | Natural (file order) | Must be enforced (watermarks) | Per-path |
| Reprocessing need | Full rerun | Replay from offset | Batch backfill + stream forward |

Default to batch unless latency SLA demands streaming. Batch is simpler to debug, test, and recover.

### Hybrid Patterns

| Pattern | Description |
|---|---|
| Lambda | Batch layer for accuracy + speed layer for freshness; merge at query time |
| Kappa | Stream-only; batch = replay of stream from beginning |
| Batch-triggered stream | Batch pipeline triggers streaming enrichment for near-real-time consumers |
| Stream-to-batch landing | Stream writes micro-batches to storage; batch pipeline reads on schedule |

### Windowing (Streaming)

| Window Type | Use when |
|---|---|
| Tumbling (fixed) | Non-overlapping fixed intervals (e.g., 5-minute aggregations) |
| Sliding (hopping) | Overlapping windows for moving averages |
| Session | Group events by activity gaps (e.g., user sessions) |
| Global | Accumulate across entire stream lifetime (counters, running totals) |

Every windowed operation declares: window size, allowed lateness, trigger policy (on-time, early, late).

Late data policy: accept with configured lateness threshold → update result; beyond threshold → route to dead letter.

---

## 9. Idempotency

### Core Rule

Every pipeline stage, and the pipeline as a whole, produces identical output when run multiple times with identical input. This enables safe retries, backfill, and crash recovery.

See architecture/STANDARDS.md §1 — principle #16 (idempotency).

### Idempotency Patterns

| Pattern | Mechanism | Best for |
|---|---|---|
| Overwrite | Write output to deterministic location; re-run overwrites | File-based sinks |
| Upsert | Insert or update on natural key | Database sinks |
| Deduplication key | Assign deterministic ID to each record; reject duplicates | Streaming sinks |
| Transactional write | Write output + checkpoint in same transaction | Database-backed pipelines |
| Partition swap | Write to staging partition; atomic swap into target | Partitioned data stores |

### Deduplication Rules

| Rule | Detail |
|---|---|
| Deterministic record ID | Derive from business key (✗ random UUID) |
| Deduplicate at sink | Sink is responsible for rejecting duplicate writes |
| Idempotency window | Define time window for duplicate detection (streaming) |
| At-least-once + dedup = exactly-once | Prefer this over complex exactly-once protocols |

### Non-Idempotent Operations

Some operations are inherently non-idempotent (sending email, external API calls). Isolate them:

- Gate behind a "processed" flag checked before execution
- Record completion in durable state before proceeding
- If flag check and execution are not atomic, accept and handle duplicates downstream

---

## 10. Error Recovery

### Checkpoint/Restart

| Rule | Detail |
|---|---|
| Checkpoint after each stage | Persist intermediate state at stage boundaries |
| Checkpoint after each chunk | Within a stage, persist progress per chunk |
| Checkpoint = input offset + stage state | Enough to resume without re-reading processed data |
| Checkpoint storage is durable | ✗ in-memory only; use file system or database |
| Resume = skip completed chunks | On restart, read checkpoint, skip processed chunks, continue |

See architecture/STANDARDS.md §6 — WAL (write-ahead log), crash recovery.

### Dead Letter Queues

| Property | Rule |
|---|---|
| Every pipeline has a dead letter destination | Matching the output format of the failing stage |
| Dead letter records include | Original data · error message · stage name · timestamp · pipeline run ID |
| Dead letter data is replayable | Can feed dead letter output back into pipeline as input |
| Dead letter has same retention as primary output | ✗ auto-delete dead letter data before primary |

### Retry Strategy

| Failure Type | Strategy |
|---|---|
| Transient (network timeout, temp file lock) | Retry with exponential backoff; max 3 attempts; jitter |
| Persistent (schema mismatch, corrupt data) | Route to dead letter immediately; ✗ retry |
| Ambiguous (unknown error code) | Retry once; if same error, treat as persistent |
| Resource exhaustion (OOM, disk full) | Halt pipeline; alert operator; ✗ retry without intervention |

### Poison Pill Handling

A poison pill is a record that crashes the processing stage (not just fails validation).

| Rule | Detail |
|---|---|
| Isolate on detection | If a chunk fails, binary-search to identify failing record(s) |
| Quarantine | Move poison record(s) to dead letter with crash details |
| Continue | Resume processing remaining records after quarantine |
| Alert | Poison pill detection → immediate alert to pipeline owner |

✗ Let a single bad record halt an entire pipeline permanently. ✗ Silently skip poison records without logging.

---

## 11. Orchestration

### DAG Execution Rules

| Rule | Detail |
|---|---|
| Declare all dependencies explicitly | ✗ implicit ordering based on definition order |
| Parallelize independent stages | Stages with no dependency relationship run concurrently |
| Fail-fast on critical path | If a stage on the critical path fails, halt dependent stages immediately |
| Allow partial DAG success | Independent branches continue even if sibling branch fails |
| Execution is deterministic | Same DAG + same input + same config → same execution plan |

### Dependency Resolution

| Dependency Type | Behavior |
|---|---|
| Data dependency | Stage B reads output of stage A → B waits for A |
| Resource dependency | Stage B needs same resource as A (exclusive lock) → serialize |
| Time dependency | Stage B runs after wall-clock time → schedule, ✗ poll |
| External dependency | Stage depends on external system availability → health check before start |

Circular dependencies are a build-time error. Orchestrator rejects DAG registration if cycle detected.

### Scheduling

| Pattern | Use when |
|---|---|
| Cron/interval | Fixed schedule (daily, hourly); source updates predictably |
| Event-triggered | Source emits event on new data; low-latency requirement |
| Dependency-triggered | Upstream pipeline completes → downstream starts |
| Manual/ad-hoc | Backfill, debugging, one-off analysis |

Every scheduled pipeline has a defined execution window. If previous run hasn't completed by next scheduled start → skip or queue (configurable), ✗ overlap.

### Backfill

| Rule | Detail |
|---|---|
| Backfill = re-run pipeline over historical range | Uses same pipeline code as production |
| Parameterize by time range | Pipeline accepts start/end bounds; processes only that window |
| Backfill isolation | Backfill writes to staging; promote to production after validation |
| Rate limiting | Backfill runs at lower priority than production; ✗ starve live pipeline |
| Idempotent backfill | Re-running backfill for same range produces identical output |

---

## 12. Output & Export

### Format Selection

| Output Target | Preferred Format | Rationale |
|---|---|---|
| Data warehouse | Parquet/native load format | Columnar; schema embedded; compressed |
| Data lake | Parquet with partitioning | Schema-on-read; splittable; efficient |
| API consumers | JSON/JSONL | Human-readable; widely supported |
| Spreadsheet users | CSV with explicit encoding/header | Universal compatibility |
| Downstream pipeline | Parquet or native format | Schema preserved; no parsing overhead |
| Archive/compliance | Parquet + schema file | Self-describing; compact; immutable |

### Partitioning

| Rule | Detail |
|---|---|
| Partition by time (default) | Year/month/day hierarchy for time-series data |
| Partition by key | When queries filter by a high-cardinality dimension |
| Partition size target | 128MB–1GB per partition file (compressed) |
| ✗ over-partition | Too many small files degrade read performance |
| Partition scheme in contract | Consumer depends on partition layout; changing it is a breaking change |

### Atomic Writes

| Rule | Detail |
|---|---|
| Write to temp location first | ✗ write directly to final destination |
| Rename/move atomically | After write completes, atomic rename to final path |
| Database: use transactions | Wrap sink writes in transaction; commit on success, rollback on failure |
| Verify after write | Read back sample/checksum of written data; compare to expected |
| No partial output visible | Consumers see either complete output or previous version — ✗ partial |

See architecture/STANDARDS.md §1 — principle #17 (copy-on-write, write new then switch).

### Output Validation

| Check | Rule |
|---|---|
| Row count | Output row count matches expected (from transform accounting) |
| Schema | Output matches declared output schema exactly |
| Checksum | Compute checksum of output; store alongside for consumer verification |
| Sample inspection | Automated spot-check of N random rows against constraints |
| Empty output guard | Output with 0 rows → fail unless pipeline explicitly allows empty output |

---

## 13. Monitoring

### Pipeline Health Metrics

| Metric | Purpose |
|---|---|
| Run status (success/failure/partial) | Basic health indicator |
| Duration (total + per-stage) | Performance tracking; SLA compliance |
| Rows processed (in/out/rejected per stage) | Data accounting |
| Error count by type | Failure pattern detection |
| Resource usage (memory peak, CPU, I/O) | Capacity planning |
| Checkpoint lag | How far behind is the pipeline from source |

### Data Freshness

| Rule | Detail |
|---|---|
| Define freshness SLA per pipeline | e.g., "output reflects source data no older than 4 hours" |
| Measure freshness = now - max(source_timestamp in output) | Not pipeline run time; actual data age |
| Alert on freshness violation | Before SLA breach if possible (warn at 80% of SLA window) |
| Dashboard freshness per output table/file | Consumers check freshness before using data |

### SLA Tracking

| SLA Type | Metric |
|---|---|
| Freshness | Data age in output ≤ threshold |
| Completeness | Row count ≥ expected minimum |
| Quality | Quality dimension scores ≥ thresholds (§5) |
| Availability | Pipeline success rate over rolling window ≥ target |
| Latency | Pipeline duration ≤ threshold |

SLA violations → alert immediately. Repeated violations → escalate. Track SLA compliance percentage over 7/30/90-day windows.

### Alerting Rules

| Rule | Detail |
|---|---|
| Alert on failure | Every pipeline failure → alert |
| Alert on SLA breach | Freshness, quality, latency thresholds exceeded |
| Alert on anomaly | Data profiling anomalies (§5) |
| ✗ Alert fatigue | Tune thresholds; group related alerts; suppress duplicates within window |
| Actionable alerts only | Every alert includes: what failed, which pipeline/stage, run ID, link to logs |
| Escalation path | Alert → owner → team → on-call; defined per pipeline |

See observability/STANDARDS.md — structured logging, metrics, health checks.

---

## 14. Scale Matrix

| Dimension | Small | Medium | Large | Enterprise |
|---|---|---|---|---|
| **Data volume** | <1GB/run | 1–100GB/run | 100GB–10TB/run | >10TB/run |
| **Pipeline count** | 1–5 | 5–50 | 50–500 | >500 |
| **Stages per pipeline** | 3–5 | 5–15 | 15–30 | 30+ |
| **Scheduling** | Cron/manual | Orchestrator (basic) | Orchestrator (full DAG) | Multi-orchestrator federation |
| **Schema registry** | File-based (JSON/YAML) | Central registry (single instance) | Registry with versioning + CI | Federated registry with governance |
| **Validation** | Schema + basic constraints | Full 3-layer validation | Data contracts with SLAs | Automated contract testing in CI |
| **Quality monitoring** | Row counts + null checks | Profiling + anomaly alerts | Quality dashboards + trend tracking | Quality gates blocking deployment |
| **Error recovery** | Manual rerun | Checkpoint/restart | Dead letter + auto-retry | Self-healing with backfill |
| **Idempotency** | Overwrite output | Upsert on key | Transactional checkpoint | Exactly-once with dedup across systems |
| **Monitoring** | Log inspection | Metrics + basic alerting | SLA tracking + dashboards | Cross-pipeline lineage + impact analysis |
| **Team** | 1 engineer | 2–5 engineers | Team with data platform | Multiple teams with platform team |

Grow incrementally. Start at the column matching current scale. Move right only when current column constraints are met.

---

## 15. Checklist

### Pipeline Setup

- [ ] Pipeline modeled as DAG with explicit stage dependencies
- [ ] ETL vs ELT decision documented with rationale
- [ ] Each stage has single responsibility
- [ ] Data contracts defined between every stage pair

### Ingestion

- [ ] Source validation (existence, permissions, size, freshness) before read
- [ ] Encoding declared explicitly; UTF-8 default
- [ ] Incremental extraction uses persisted high-water marks
- [ ] File format validation matches contract

### Validation

- [ ] Three-layer validation: schema → constraint → semantic
- [ ] Rejected rows route to dead letter with rejection reason
- [ ] Rejection threshold configured and enforced
- [ ] Row accounting verified: rows_in = rows_out + rows_rejected

### Transformation

- [ ] All transforms are pure functions (no side effects)
- [ ] Intermediate data is immutable
- [ ] Cardinality expectation declared and verified per transform
- [ ] Transform ordering follows clean → validate → enrich → reshape → filter

### Data Quality

- [ ] Quality dimensions defined per field (completeness, uniqueness, accuracy)
- [ ] Baseline profiles established and versioned
- [ ] Anomaly detection thresholds configured
- [ ] Data contracts include freshness SLA and quality thresholds

### Schema Management

- [ ] All schemas registered in registry
- [ ] Schema evolution follows compatibility rules
- [ ] Producer/consumer version ranges declared and validated
- [ ] Breaking changes follow documented migration process

### Processing

- [ ] Chunk size configured; full dataset never loaded into memory at once
- [ ] Memory budget declared per stage
- [ ] Progress reporting emits structured events per chunk
- [ ] Partial failure accumulates to dead letter; threshold enforced

### Idempotency & Recovery

- [ ] Pipeline produces identical output on re-run with same input
- [ ] Deduplication uses deterministic business key (not random ID)
- [ ] Checkpoints persisted at stage and chunk boundaries
- [ ] Dead letter includes original data + error context + run ID
- [ ] Retry strategy defined per failure type

### Orchestration

- [ ] Dependencies declared explicitly; no implicit ordering
- [ ] Schedule defined with overlap policy
- [ ] Backfill parameterized by time range; writes to staging first
- [ ] Circular dependencies rejected at registration

### Output

- [ ] Output format matches consumer contract
- [ ] Writes are atomic (temp → rename pattern)
- [ ] Output validated (row count, schema, checksum)
- [ ] Empty output explicitly handled (fail or allow)

### Monitoring

- [ ] Pipeline health metrics collected (status, duration, rows, errors)
- [ ] Freshness SLA defined and monitored
- [ ] Alerts configured for failure, SLA breach, anomaly
- [ ] Alerts are actionable with pipeline/stage/run-ID context
