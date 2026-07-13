# Database Standards

> Rules for schema design, integrity, indexing, queries, transactions, migrations, and connection management in any relational store.

**ID** `database` · **Tier** Interface · **Version** 1.0
**Owns** schema design + normalization/denormalization · table + column naming · data types · constraints · indexing strategy · query patterns · **pagination strategy (keyset vs OFFSET)** · **N+1 prevention** · transactions + isolation levels · migrations (expand/contract) · connection pooling · data lifecycle · WAL/PITR + replica mechanics
**Defers to** backup cadence + DR + RTO/RPO + failover testing → [devops](../devops/STANDARDS.md) · query syntax + formatting → [sql](../sql/STANDARDS.md) · N+1 detection + profiling + cache strategy → [performance](../performance/STANDARDS.md) · cursor + response-envelope contract → [api](../api/STANDARDS.md) · input validation + secrets + credential storage → [security](../security/STANDARDS.md) · alert thresholds → [observability](../observability/STANDARDS.md) · migration execution stage → [cicd](../cicd/STANDARDS.md) · coverage + pyramid → [testing](../testing/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [sql](../sql/STANDARDS.md) · [security](../security/STANDARDS.md) · [performance](../performance/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Schema Design](#2-schema-design)
3. [Naming Conventions](#3-naming-conventions)
4. [Data Types](#4-data-types)
5. [Constraints & Integrity](#5-constraints--integrity)
6. [Indexes](#6-indexes)
7. [Pagination & N+1](#7-pagination--n1)
8. [Query Patterns](#8-query-patterns)
9. [Transactions & Isolation](#9-transactions--isolation)
10. [Migrations](#10-migrations)
11. [Connection Management](#11-connection-management)
12. [Data Lifecycle](#12-data-lifecycle)
13. [Durability & Replication](#13-durability--replication)
14. [Anti-Patterns](#14-anti-patterns)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

| # | Principle | Rule |
|---|---|---|
| 1 | Database enforces integrity | Constraints live in the schema, not only in application code — the app is one of many writers |
| 2 | Normalize first | 3NF by default. Denormalize only against measured evidence (§2) |
| 3 | One fact, one place | Each fact stored in exactly one table. See [architecture](../architecture/STANDARDS.md) — state ownership |
| 4 | Types are constraints | Every column's type narrows the set of writable values |
| 5 | Explain before ship | No new query reaches production without an EXPLAIN plan reviewed (§8) |
| 6 | Migrations are forward-only | Roll forward. Rollback scripts exist, but recovery is a new migration, ✗ a reverse-deploy |
| 7 | Bounded everything | Every query has a LIMIT or bounded predicate; every pool has a max; every statement has a timeout |
| 8 | Zero-downtime by construction | Schema changes ship in expand → migrate → contract phases (§10) |

---

## 2. Schema Design

### Normalization

Design to third normal form (3NF). Every non-key column depends on the key, the whole key, and nothing but the key.

| Form | Rule | Violation signal |
|---|---|---|
| 1NF | Atomic values; no repeating groups | Comma-separated list in a column · array smuggling structured rows |
| 2NF | Every non-key column depends on the entire primary key | Column depends on part of a composite key |
| 3NF | No transitive dependencies between non-key columns | Column derivable from another non-key column |

### Deliberate Denormalization

Denormalize only when **all four** hold:

1. Measured query latency fails its budget → [performance](../performance/STANDARDS.md).
2. Read-to-write ratio for the target data exceeds 100:1.
3. Refresh is maintained by the database — trigger, materialized view, or generated column. ✗ application-level sync.
4. Documented: justification · source-of-truth table · refresh mechanism · staleness tolerance.

✗ denormalize speculatively. ✗ duplicated columns without a recorded refresh path.

### Keys

| Rule | Detail |
|---|---|
| Every table has an explicit primary key | ✗ heap tables |
| Surrogate keys for entity tables | Auto-increment integer (locality) \| UUIDv7 (distributed, time-ordered). ✗ UUIDv4 as a clustered PK — random insert order fragments the index |
| Natural keys for lookup/enum tables | `country_code` · `currency_code` — stable and meaningful |
| Composite keys for junction tables | Composed of the foreign keys they join |
| ✗ mutable column as primary key | PK values never change after insert |
| Foreign key for every relationship | Database enforces referential integrity. ✗ application-only relationships |

---

## 3. Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Table | `snake_case`, singular noun | `user_account` · `order_item` |
| Column | `snake_case`, descriptive | `email_address` · `total_amount` |
| Primary key | `id` in its own table; `{entity}_id` when referenced | `id` · `user_id` |
| Foreign key column | `{referenced_table}_id` | `order_id` |
| Boolean column | `is_` · `has_` prefix | `is_active` · `has_verified_email` |
| Timestamp column | `_at` suffix | `created_at` · `deleted_at` |
| Date column | `_on` suffix | `expires_on` |
| Count / amount column | `_count` · `_amount` suffix | `retry_count` · `total_amount` |
| Primary key constraint | `pk_{table}` | `pk_user_account` |
| Foreign key constraint | `fk_{table}_{referenced}` | `fk_order_item_order` |
| Unique constraint | `uq_{table}_{columns}` | `uq_user_account_email` |
| Check constraint | `ck_{table}_{description}` | `ck_order_total_positive` |
| Index · unique index | `ix_{table}_{columns}` · `ux_{table}_{columns}` | `ix_order_created_at` |

- ✗ reserved SQL keywords as identifiers (`order`, `user`, `group`) → prefix the domain: `customer_order`, `app_user`.
- ✗ abbreviations ; universally understood (`id`, `url`, `ip` ✓ · `qty`, `addr`, `txn` ✗).
- ✗ type prefixes (`tbl_`, `vw_`, `sp_`).

---

## 4. Data Types

| Data | Correct type | ✗ Wrong type |
|---|---|---|
| Money / currency | DECIMAL / NUMERIC, minimum `DECIMAL(19,4)` | Float · double — rounding errors compound |
| Timestamp | `TIMESTAMP WITH TIME ZONE`, stored UTC | Varchar · naive local timestamp · epoch integer |
| Boolean | Native BOOLEAN | Integer 0/1 · varchar `"Y"`/`"N"` |
| UUID | Native UUID type | `VARCHAR(36)` |
| IP address | Native INET | `VARCHAR(45)` |
| Enum ≤ 10 values, stable | Database ENUM \| CHECK constraint | Unconstrained varchar |
| Enum > 10 values \| evolving | Lookup table + FK | Application-level strings |
| Semi-structured | Native JSON/JSONB | TEXT holding a JSON string |
| Email · URL | VARCHAR + CHECK constraint | TEXT, unvalidated |
| Bounded text | `VARCHAR(n)` with an explicit limit | TEXT — unbounded input |
| Unbounded text | TEXT | `VARCHAR(4000)` — arbitrary cliff |
| Binary | BYTEA / BLOB | Base64 in TEXT |
| Percentage | `DECIMAL(5,4)`, range 0.0000–1.0000 | Integer 0–100 — ambiguous scale |
| Coordinates | `DECIMAL(10,7)` latitude · `DECIMAL(11,7)` longitude | Float |

✗ stringly-typed data. If the value has internal structure (date, number, enum, JSON), the column type expresses it.

JSONB columns are for genuinely schemaless attributes. ✗ JSONB as an escape hatch from schema design — fields queried in a WHERE clause become real columns.

---

## 5. Constraints & Integrity

Every column is NOT NULL unless absence is a valid domain state. Justify each nullable column in a schema comment. ✗ nullable as a lazy default — NULL propagates unpredictably through predicates and aggregates.

Apply constraints top-down; push validation as low as it will go. Database constraints survive application bugs, ad-hoc SQL, and migration scripts.

| Level | Constraint | Guarantees |
|---|---|---|
| 1 | Data type | Structural validity |
| 2 | NOT NULL | Presence |
| 3 | CHECK | Domain range — `total_amount > 0` · `end_date > start_date` · `status IN (…)` |
| 4 | UNIQUE | Uniqueness within the table |
| 5 | FOREIGN KEY | Referential integrity across tables |
| 6 | Application logic | Business rules too complex for SQL — nothing that levels 1–5 can express |

| Rule | Detail |
|---|---|
| Explicit ON DELETE per FK | `CASCADE` · `SET NULL` · `SET DEFAULT` · `RESTRICT` — always stated |
| Default RESTRICT | CASCADE only for true ownership (parent → child) |
| ✗ CASCADE on shared references | Multiple parents referencing one child → cascade deletes rows other parents still need |
| Index every FK column | Most engines do not create it automatically; without it, deletes on the parent table scan |
| ✗ complex business rules in CHECK | Keep CHECK to value/range validation |
| Defaults | `created_at DEFAULT CURRENT_TIMESTAMP` · `updated_at` maintained by trigger · booleans explicit (`DEFAULT FALSE`) · counters `DEFAULT 0` · status → initial state |

---

## 6. Indexes

| Index when | ✗ Skip when |
|---|---|
| Column appears in WHERE frequently | Table under 1,000 rows |
| Column used in a JOIN condition | Very low cardinality alone (boolean) in a large table |
| Column used in ORDER BY | Column rarely queried |
| Foreign key column | Write-heavy table where reads are not the bottleneck |
| Column backing a unique constraint | Speculative "might need it later" |

| Type | Use |
|---|---|
| B-tree | Default — equality, range, sorting |
| Hash | Exact equality only, where measurably faster |
| GIN | Full-text · JSONB containment · array membership |
| GiST | Spatial · range types · nearest-neighbour |
| Partial | Predicate targets a subset — `WHERE is_active` |
| Expression | Query filters on a computed value — `LOWER(email)` |

### Composite Column Order

| Rule | Detail |
|---|---|
| Equality columns before range columns | `WHERE status = ? AND created_at > ?` → index `(status, created_at)`, ✗ `(created_at, status)` |
| Most selective equality column first | Narrows the candidate set fastest |
| Sort column last, matching direction | Index order must satisfy ORDER BY, else a sort node appears in the plan |
| Leftmost-prefix rule | Index `(a, b, c)` serves `(a)`, `(a, b)`, `(a, b, c)` — ✗ `(b)`, ✗ `(b, c)` |
| Max 3–4 columns | Beyond that, maintenance cost outweighs benefit — revisit the query |

**Covering index:** include every column the query touches (INCLUDE clause where supported) → index-only scan, no heap lookup. Use on high-frequency reads with a stable column set.

### ✗ Over-Indexing

- Every index taxes every INSERT, UPDATE, DELETE.
- Drop indexes with zero reads over a 30-day window.
- ✗ redundant indexes — `(a, b)` already serves `(a)`.
- Total index size > 2× table data size → review before adding more.

---

## 7. Pagination & N+1

`database` owns pagination strategy and N+1 prevention. [api](../api/STANDARDS.md) owns the cursor + response-envelope contract the client sees. [performance](../performance/STANDARDS.md) owns detection + profiling. [sql](../sql/STANDARDS.md) owns query syntax. ✗ restate this section elsewhere.

### Ruling

**Keyset (cursor) pagination by default · OFFSET permitted only on datasets under 10K rows.**

| Strategy | Cost | Use |
|---|---|---|
| Keyset / cursor | `O(limit)` — index seek to the last-seen key, then scan forward | **Default.** Every user-facing or growing dataset |
| OFFSET / LIMIT | `O(offset + limit)` — scans and discards every skipped row | Only when the total dataset is **< 10K rows** (admin tables, static lookups) |

- ✗ OFFSET on any dataset ≥ 10K rows — deep pages degrade linearly and lock the scanned rows under some isolation levels.
- ✗ OFFSET on a live feed even under 10K rows if rows are inserted/deleted concurrently — pages silently duplicate or skip rows.

### Keyset Rules

| Rule | Detail |
|---|---|
| Order by a unique, immutable key | Non-unique sort key → append the PK as a tiebreaker: `ORDER BY created_at DESC, id DESC` |
| Predicate matches the sort | `WHERE (created_at, id) < (?, ?)` — a row-value comparison, ✗ a chain of ORs |
| Index the exact sort tuple | `(created_at DESC, id DESC)` — else every page sorts the table |
| Always specify ORDER BY | Without it, page contents are non-deterministic |
| Total count is a separate query | ✗ a window-function count in the page query on large sets — it forces a full scan. Cache it, approximate it, or omit it |

### N+1 Prevention

| Pattern | Fix |
|---|---|
| Loop fetching related rows one at a time | Single JOIN \| batched `WHERE id IN (…)` |
| ORM lazy loading inside an iteration | Eager load / explicit join specification declared at query construction |
| Nested loop across two collections | One query with a JOIN |
| Per-row aggregate lookup | One grouped aggregate joined back |

- Query count per request is bounded and asserted in tests — a request whose query count scales with result-set size is a bug, ✗ a tuning opportunity.
- Batch `IN (…)` lists are chunked (1,000 max) — ✗ unbounded IN lists.
- Detection tooling + per-request query budgets → [performance](../performance/STANDARDS.md).

---

## 8. Query Patterns

| Rule | Detail |
|---|---|
| Parameterized always | Bind variables. ✗ string concatenation of user input — see [security](../security/STANDARDS.md) |
| Dynamic identifiers | Table/column names from user input → allowlist validation, then interpolate. ✗ pass through |
| ✗ `SELECT *` in application code | Explicit column list — bounds I/O and survives column additions |
| ✗ unbounded queries | Every query carries a LIMIT or a known-bounded predicate |
| ✗ implicit type coercion in WHERE | Type mismatch defeats the index — cast explicitly |
| ✗ functions on indexed columns | `WHERE LOWER(email) = ?` defeats the index → expression index \| store normalized |
| ✗ leading wildcard LIKE | `LIKE '%term'` cannot use a B-tree → full-text index |
| EXPLAIN every new query | Verify index usage, row estimates, and join order before deploy. Sequential scan on a large table → justify or fix |
| Read-your-writes | Reads that must observe a just-committed write go to the primary, ✗ a replica (§13) |

---

## 9. Transactions & Isolation

Every write touching multiple rows or tables runs inside an explicit transaction. ✗ implicit auto-commit for multi-step writes — partial state is corrupt state.

### Isolation Levels and the Anomalies They Permit

| Level | Dirty read | Non-repeatable read | Phantom read | Write skew | Use |
|---|---|---|---|---|---|
| READ UNCOMMITTED | Permitted | Permitted | Permitted | Permitted | ✗ Never |
| READ COMMITTED | Prevented | Permitted | Permitted | Permitted | Default for most workloads |
| REPEATABLE READ | Prevented | Prevented | Permitted by the SQL standard; prevented by PostgreSQL's snapshot implementation | Permitted | Reports · multi-read consistency |
| SERIALIZABLE | Prevented | Prevented | Prevented | Prevented | Money transfer · inventory decrement · any invariant across rows |

- Constraint-violating invariants that span rows (balance ≥ 0 across two accounts) require SERIALIZABLE — READ COMMITTED and REPEATABLE READ both permit write skew.
- SERIALIZABLE aborts on conflict: the application **must** retry serialization failures with backoff. ✗ treat them as fatal.
- Isolation level declared per operation, ✗ set globally and forgotten.

### Scope & Locking

| Rule | Detail |
|---|---|
| Smallest possible scope | The transaction wraps only what must be atomic |
| ✗ I/O inside a transaction | No HTTP call, file write, or message publish while a transaction is open |
| ✗ user interaction inside a transaction | Never hold a transaction open across a prompt |
| ✗ long transactions | `statement_timeout` set; transactions over 5 s investigated — they pin vacuum and bloat the WAL |
| Explicit COMMIT/ROLLBACK | Every path ends explicitly. ✗ rely on connection close |
| Consistent lock ordering | All transactions lock multiple tables in the same order — this is the primary deadlock defence |
| Lock timeout | `lock_timeout` set — fail fast, ✗ wait indefinitely |
| Retry on deadlock | Bounded retries with backoff; deadlock is expected, not exceptional |
| Optimistic by default | `version` column + `WHERE version = ?`; zero rows affected = conflict → retry. `SELECT FOR UPDATE` only for high-contention, short-lived critical sections |

---

## 10. Migrations

| Rule | Detail |
|---|---|
| Versioned | Monotonic version identifier — `{version}_{description}.{up\|down}.sql` |
| Ordered | Strict version order. ✗ out-of-order application |
| One logical change per migration | ✗ unrelated changes batched |
| Forward-only in production | Recovery = a new forward migration. Down scripts exist for local/staging, ✗ as the production rollback plan |
| Reversible | Every migration has a down script ; irreversible destructive drops, which are flagged and reviewed |
| Reviewed | Migrations pass code review like application code |
| Automated on deploy | Run by the pipeline → [cicd](../cicd/STANDARDS.md). ✗ manual SQL in production |
| State tracked in-database | `schema_migrations` table |
| Same sequence everywhere | ✗ environment-specific migrations — use configuration/feature flags |
| Tested against production-shape data | Timed on a restored copy; a migration whose lock window is unknown is untested |

### Expand / Contract (Parallel Change)

Zero-downtime schema change. Old and new code run concurrently — every intermediate state must be readable and writable by **both**. Ordered:

1. **Expand** — add the new structure, nullable/defaulted, non-breaking. Old code ignores it.
2. **Dual-write** — deploy code writing both old and new. Reads still come from old.
3. **Backfill** — migrate existing rows in bounded batches, throttled, resumable. ✗ one unbounded UPDATE.
4. **Flip reads** — deploy code reading the new structure. Verify.
5. **Contract** — after a soak period with no old-path traffic, drop the old column/table and the dual-write.

Rename, type change, and column split are never done in place — they are always expand/contract.

### Operation Safety

| Operation | Safe at scale? | Mitigation |
|---|---|---|
| Add nullable column | Yes | No rewrite |
| Add column with default | Engine-dependent | PostgreSQL ≥ 11 safe; older rewrites the table |
| Add index | ✗ — locks writes | `CREATE INDEX CONCURRENTLY` (or engine equivalent), outside a transaction |
| Add NOT NULL | ✗ — full scan | Add CHECK NOT VALID → VALIDATE → promote |
| Add FK constraint | ✗ — locks both tables | Add NOT VALID → VALIDATE separately |
| Rename \| retype column | ✗ — breaks running code | Expand/contract |
| Drop column | Yes | Drop dependent indexes/constraints first; contract phase only |

✗ schema and data changes in the same migration — they have different rollback and lock profiles.

---

## 11. Connection Management

| Rule | Detail |
|---|---|
| Pool always | ✗ connect-per-query |
| Starting size | `(2 × CPU cores) + effective_spindle_count` — then tune by measurement, ✗ by guess |
| Max size is a hard cap | Exhausted pool → queue then reject. ✗ unbounded growth — the database, not the app, is the scarce resource |
| Min idle | 2–5 warm connections to avoid cold-start latency |
| Max lifetime | Recycle after 30 min — prevents stale server-side state |
| Idle timeout | Close after 10 min idle |
| Serverless / high-fan-out clients | Front the database with an external pooler — ✗ one pool per lambda instance |
| Validate on checkout | Ping or test query; evict broken connections automatically |
| Separate pool per database | Independent timeouts. ✗ cross-database transactions — use a saga |

| Timeout | Default |
|---|---|
| Connection (establish) | 5 s |
| Statement execution | 30 s web · 5 min batch |
| Lock acquisition | 10 s |
| Idle-in-transaction | 60 s |
| Pool checkout | 5 s |

All timeouts explicitly configured — database defaults are frequently infinite. Credentials + connection strings → [security](../security/STANDARDS.md) · [configuration](../configuration/STANDARDS.md). Pool saturation + latency alerting → [observability](../observability/STANDARDS.md).

---

## 12. Data Lifecycle

| Approach | Use when | Implementation |
|---|---|---|
| Soft delete | Audit trail · undo · regulatory retention | `deleted_at TIMESTAMP NULL` — NULL = active |
| Hard delete | No retention requirement · GDPR erasure request · storage pressure | Physical DELETE |

- Every query on a soft-deletable table filters `WHERE deleted_at IS NULL` — enforce via a view or ORM default scope, ✗ per-query discipline.
- Unique constraints on soft-deletable tables use a partial unique index on active rows — else a deleted row blocks re-creation.
- Retention period defined per table and documented in a schema comment.
- Archive before hard delete: archive table mirrors the source schema + `archived_at`. ✗ divergent archive structure — it breaks restore.
- Archival runs as a scheduled job in bounded batches. ✗ manual runs.
- Full history requirement → temporal table (`{table}_history` with `valid_from` · `valid_to`), populated by trigger on UPDATE/DELETE.
- GDPR erasure must reach backups and replicas — a delete that survives in the archive is not a delete.

---

## 13. Durability & Replication

Backup cadence · retention · RTO/RPO targets · DR strategy · failover test cadence (**≥ semi-annually**) → [devops](../devops/STANDARDS.md). ✗ restate them here. This section covers database-layer mechanics only.

| Mechanism | Rule |
|---|---|
| Write-ahead log | Enabled and archived continuously — WAL (PostgreSQL) · binlog (MySQL). The log is the durability boundary |
| Point-in-time recovery | Base backup + continuous log archive → restore to an arbitrary timestamp. PITR is unavailable without continuous archiving |
| Backup encryption | Backups encrypted at rest — identical classification to live data |
| Backup isolation | Stored outside the primary's failure domain — ✗ same host, ✗ same disk |
| Replica lag | Monitored continuously; investigate above 30 s. Lagging replica → stale reads |
| Read routing | Replicas serve reads that tolerate staleness. Read-your-writes goes to the primary |
| Promotion gate | ✗ promote a replica without verifying consistency + replay position |

### Restore Verification Procedure

Ordered — a backup that has not completed these steps is a hope, not a backup:

1. Restore into an **isolated** environment. ✗ restore-test against production.
2. Replay logs to a target timestamp (exercise PITR, not just the base backup).
3. Verify integrity: row counts per table · checksums · foreign-key validation.
4. Run an application-level smoke test against the restored copy.
5. Record the measured restore duration and compare against the RTO target owned by [devops](../devops/STANDARDS.md).
6. Log the result. A failed or skipped verification is an incident.

---

## 14. Anti-Patterns

| Anti-pattern | Failure | Instead |
|---|---|---|
| EAV ("entity-attribute-value") table | No types, no constraints, unindexable queries | Real columns · JSONB for genuinely sparse attributes |
| Application-enforced foreign keys | Every other writer orphans rows | FK constraints (§5) |
| `SELECT *` in application code | Silent breakage on column change; wasted I/O | Explicit column list |
| OFFSET for deep pagination | Linear degradation; duplicated/skipped rows | Keyset (§7) |
| ORM lazy loading in a loop | N+1 — latency scales with result size | Eager load \| batch (§7) |
| Storing money as float | Rounding errors compound irreversibly | DECIMAL (§4) |
| Nullable-by-default columns | NULL leaks through predicates and aggregates | NOT NULL + justified exceptions (§5) |
| Locking migration in a deploy window | Table lock stalls all writes | Expand/contract + CONCURRENTLY (§10) |
| Unbounded connection pool | The database, not the app, falls over | Hard max + queue + reject (§11) |
| Untested backups | Discovered broken during the incident | Restore verification procedure (§13) |

---

## 15. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Schema | Loose | Full 3NF · documented denormalizations | 3NF + measured denormalization + partitioning |
| Constraints | PK + NOT NULL | PK · FK · NOT NULL · UNIQUE · CHECK | Full hierarchy + trigger-maintained `updated_at` |
| Indexes | PK only | FK indexes + query-driven indexes | Measured · covering indexes on hot paths · unused indexes dropped |
| Pagination | OFFSET (< 10K rows) | Keyset on every growing list | Keyset + cached/approximate counts |
| Migrations | Manual SQL | Versioned · reversible · CI-tested | Expand/contract · timed on production-shape data |
| Transactions | Auto-commit | Explicit for multi-table writes | Isolation level chosen per operation + retry on serialization failure |
| Connections | Single connection | Pool + all timeouts | Tuned pool + external pooler + saturation alerting |
| Durability | Dump/export | WAL archiving + PITR + restore tested | PITR + replicas + verified restore + DR drills → [devops](../devops/STANDARDS.md) |

---

## 16. Checklist

- [ ] Every table has an explicit primary key; no mutable column serves as PK
- [ ] Every relationship is a foreign key constraint with an explicit ON DELETE action
- [ ] Every FK column is indexed
- [ ] Every column is NOT NULL unless the nullable case is justified in a comment
- [ ] Money is DECIMAL, timestamps are TIMESTAMPTZ stored UTC — no stringly-typed columns
- [ ] CHECK constraints cover every bounded value range
- [ ] Every denormalization has a documented source of truth and refresh mechanism
- [ ] Composite indexes order equality columns before range columns
- [ ] Unused indexes (zero reads / 30 days) dropped
- [ ] List queries use keyset pagination; OFFSET appears only on datasets under 10K rows
- [ ] Keyset queries order by a unique tiebreaker and are backed by a matching index
- [ ] No query's count scales with result-set size (N+1 absent) — asserted in tests
- [ ] Every query is parameterized; no user input is concatenated into SQL
- [ ] No `SELECT *` and no unbounded query in application code
- [ ] EXPLAIN reviewed for every new or changed query
- [ ] Multi-row writes run in explicit transactions with an isolation level chosen per operation
- [ ] Serialization failures and deadlocks are retried with backoff, not surfaced as fatal
- [ ] No I/O (HTTP, file, message) inside an open transaction
- [ ] Schema changes ship as expand → dual-write → backfill → flip → contract
- [ ] Index creation uses CONCURRENTLY (or engine equivalent)
- [ ] Schema and data changes live in separate migrations
- [ ] Connection pool has a hard max and every timeout is explicitly configured
- [ ] Soft-deleted rows are filtered by a view or default scope, not per-query discipline
- [ ] Retention period defined and automated per table
- [ ] WAL/binlog archiving enabled; PITR restore verified in an isolated environment
- [ ] Replica lag monitored; reads requiring read-your-writes go to the primary
