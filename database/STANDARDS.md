# Database Standards

Rules for schema design, data integrity, migrations, queries, transactions,
connection management, and data lifecycle. Language-agnostic — applies to
any relational or relational-compatible database.

Derived from: ACID properties, relational theory, Codd's rules,
write-ahead logging, copy-on-write principles, connection pooling
patterns, and operational best practices from PostgreSQL, MySQL, SQLite.

Composable with: Architecture Standards, Security Standards,
Configuration Standards, API Standards, Performance Standards.

---

## Table of Contents

1. [Schema Design](#1-schema-design)
2. [Naming Conventions](#2-naming-conventions)
3. [Data Types](#3-data-types)
4. [Constraints & Integrity](#4-constraints--integrity)
5. [Indexes](#5-indexes)
6. [Migrations](#6-migrations)
7. [Query Patterns](#7-query-patterns)
8. [Transactions](#8-transactions)
9. [Connection Management](#9-connection-management)
10. [Data Lifecycle](#10-data-lifecycle)
11. [Backup & Recovery](#11-backup--recovery)
12. [Scale Matrix](#12-scale-matrix)
13. [Database Checklist](#13-database-checklist)

---

## 1. Schema Design

### Normalization Default

Design to third normal form (3NF) by default. Every non-key column depends on the key, the whole key, and nothing but the key.

| Normal Form | Rule | Violation signal |
|---|---|---|
| 1NF | Every column holds atomic values; no repeating groups | Comma-separated lists in column, JSON arrays storing structured data |
| 2NF | Every non-key column depends on the entire primary key | Column depends on part of composite key only |
| 3NF | No transitive dependencies between non-key columns | Column derivable from another non-key column |

### Denormalization Criteria

Denormalize only when all three conditions are met:

1. Measured query performance fails defined budget (see performance/STANDARDS.md)
2. Read-to-write ratio exceeds 100:1 for target data
3. Denormalized view is maintained by database triggers or materialized views — ✗ application-level sync

Document every denormalization with: justification, source of truth table, refresh mechanism, staleness tolerance.

### Primary Keys

| Rule | Detail |
|---|---|
| Every table has explicit primary key | ✗ heap tables without PK |
| Prefer surrogate keys for entity tables | Auto-increment integer or UUID depending on distribution needs |
| Natural keys for lookup/enum tables | `country_code`, `currency_code` — stable, meaningful identifiers |
| Composite keys for junction tables | Composed of foreign keys to joined tables |
| ✗ mutable columns as primary key | PK values never change after insert |

### Foreign Keys

Every relationship between tables expressed as explicit foreign key constraint. ✗ application-only referential integrity — database enforces relationships.

### Single Source of Truth

Each fact stored in exactly one table. Other tables reference via foreign key — ✗ duplicated data across tables without explicit denormalization tracking. See architecture/STANDARDS.md §6 — state ownership.

---

## 2. Naming Conventions

### General Rules

| Element | Convention | Example |
|---|---|---|
| Tables | `snake_case`, singular noun | `user`, `order_item`, `payment_method` |
| Columns | `snake_case`, descriptive | `created_at`, `email_address`, `total_amount` |
| Primary key | `id` for surrogate; `{entity}_id` when referenced | `id` in own table, `user_id` as FK |
| Foreign key column | `{referenced_table}_id` | `order_id`, `product_id` |
| Boolean columns | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamp columns | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |
| Date columns | `_on` suffix | `born_on`, `expires_on` |
| Count/amount columns | `_count` or `_amount` suffix | `retry_count`, `total_amount` |

### Index & Constraint Names

| Element | Pattern | Example |
|---|---|---|
| Primary key | `pk_{table}` | `pk_user` |
| Foreign key | `fk_{table}_{referenced_table}` | `fk_order_item_order` |
| Unique constraint | `uq_{table}_{columns}` | `uq_user_email_address` |
| Check constraint | `ck_{table}_{description}` | `ck_order_total_positive` |
| Index | `ix_{table}_{columns}` | `ix_order_created_at` |
| Unique index | `ux_{table}_{columns}` | `ux_user_username` |

### Prohibited Names

- ✗ reserved SQL keywords as identifiers (`order`, `user`, `group`, `select`) — append domain suffix: `customer_order`, `app_user`, `team_group`
- ✗ abbreviations unless universally understood (`id`, `url`, `ip` are acceptable; `qty`, `addr`, `txn` are not)
- ✗ prefixes indicating type (`tbl_`, `vw_`, `sp_`) — Hungarian notation adds noise

---

## 3. Data Types

### Type Selection Rules

| Data | Correct type | ✗ Wrong type |
|---|---|---|
| Money/currency | Fixed-point decimal (DECIMAL/NUMERIC) | Float/double (rounding errors) |
| Timestamps | Timestamp with time zone | Varchar, Unix epoch integer |
| Booleans | Native BOOLEAN | Integer 0/1, varchar "Y"/"N" |
| UUIDs | Native UUID type (where available) | VARCHAR(36) |
| IP addresses | Native INET type (where available) | VARCHAR(45) |
| Enumerations (≤10 values, stable) | Database ENUM or check constraint | Unconstrained varchar |
| Enumerations (>10 values or evolving) | Lookup table with FK | Application-level strings |
| JSON/semi-structured | Native JSON/JSONB column | TEXT column with JSON string |
| Email, URL | VARCHAR with check constraint | TEXT without validation |
| Short text (bounded) | VARCHAR(n) with explicit limit | TEXT (unbounded) |
| Long text (unbounded) | TEXT | VARCHAR(4000) |
| Binary data | BYTEA / BLOB | Base64-encoded TEXT |
| Percentages | DECIMAL(5,4) range 0.0000–1.0000 | Integer 0–100 (ambiguous scale) |

### Precision Rules

- Monetary values: minimum DECIMAL(19,4) — covers all currency precisions
- Coordinates: DECIMAL(10,7) for latitude, DECIMAL(11,7) for longitude
- Scientific measurements: document required precision per domain; ✗ default float

### ✗ Stringly-Typed Data

Never store structured data as unvalidated strings. Every column's type constrains valid values at database level. If data has internal structure (dates, numbers, enums, JSON), use typed column — ✗ VARCHAR catch-all.

---

## 4. Constraints & Integrity

### NOT NULL Default

Every column is NOT NULL unless absence is a valid domain state. Justify every nullable column in schema comments. ✗ nullable columns as lazy default — null propagates unpredictably through queries.

### Constraint Hierarchy

Apply constraints from most restrictive (top) to least (bottom):

| Level | Constraint | Purpose |
|---|---|---|
| 1 | Data type | Structural validity — integer, date, boolean |
| 2 | NOT NULL | Presence guarantee |
| 3 | CHECK | Domain range — `ck_order_total_positive: total > 0` |
| 4 | UNIQUE | Uniqueness within table |
| 5 | FOREIGN KEY | Referential integrity across tables |
| 6 | Application logic | Business rules too complex for SQL constraints |

Push validation as low as possible. Database-level constraints survive application bugs, migration scripts, and direct SQL access.

### Foreign Key Rules

| Rule | Detail |
|---|---|
| Explicit ON DELETE action | Every FK specifies `CASCADE`, `SET NULL`, `SET DEFAULT`, or `RESTRICT` |
| Default to RESTRICT | Prevent accidental orphaning; use CASCADE only for true ownership (parent → child) |
| ✗ ON DELETE CASCADE on shared references | If multiple parents reference same child, CASCADE creates surprise deletions |
| FK indexes | Every foreign key column has corresponding index (many databases do not auto-create) |

### Check Constraints

- Positive amounts: `total_amount > 0`
- Valid ranges: `percentage BETWEEN 0 AND 1`
- Enum-like: `status IN ('draft', 'active', 'archived')`
- Cross-column: `end_date > start_date`
- ✗ complex business rules in CHECK — keep to simple value/range validation

### Default Values

| Rule | Detail |
|---|---|
| `created_at` | Default to `CURRENT_TIMESTAMP` |
| `updated_at` | Default to `CURRENT_TIMESTAMP`, update via trigger |
| Boolean flags | Explicit default (`DEFAULT FALSE`) — ✗ implicit NULL |
| Status columns | Default to initial state (`DEFAULT 'draft'`) |
| Counter columns | `DEFAULT 0` |

---

## 5. Indexes

### When to Index

| Index when | ✗ Skip when |
|---|---|
| Column appears in WHERE clauses frequently | Table has fewer than 1,000 rows |
| Column used in JOIN conditions | Column has very low cardinality (boolean) in large table without compound index |
| Column used in ORDER BY | Column rarely appears in queries |
| Foreign key columns | Write-heavy table where read speed is not bottleneck |
| Columns in unique constraints | Speculative "might need it later" |

### Index Types

| Type | Use case |
|---|---|
| B-tree (default) | Equality, range queries, sorting |
| Hash | Exact equality only (when supported and faster) |
| GIN | Full-text search, JSONB containment, array membership |
| GiST | Geometric/spatial data, range types, nearest-neighbor |
| Partial index | Queries targeting subset (`WHERE is_active = TRUE`) |
| Expression index | Queries on computed values (`LOWER(email)`) |

### Composite Index Rules

| Rule | Rationale |
|---|---|
| Most selective column first | Narrows candidate set fastest |
| Equality columns before range columns | `WHERE status = 'active' AND created_at > X` → index `(status, created_at)` |
| Match query column order | Composite index serves queries on leftmost prefix only |
| Maximum 3–4 columns per composite | Beyond 4, maintenance cost outweighs benefit — reconsider query design |

### Covering Indexes

Include all columns needed by query in index (via INCLUDE clause where supported). Covering index eliminates table lookup — index-only scan. Use for high-frequency read queries with stable column sets.

### ✗ Over-Indexing

- Every index costs write performance (insert, update, delete maintain index)
- Monitor unused indexes — drop indexes with zero reads over 30-day window
- ✗ duplicate indexes (index on `(a, b)` already covers queries on `(a)`)
- Total index size per table: alert when indexes exceed 2× table data size

---

## 6. Migrations

### Core Rules

| Rule | Detail |
|---|---|
| Versioned | Every migration has monotonically increasing version identifier (timestamp or sequence) |
| Ordered | Migrations execute in strict version order — ✗ out-of-order execution |
| Idempotent checks | Use `IF NOT EXISTS` / `IF EXISTS` guards where supported |
| One change per migration | Single logical change (add table, add column, add index) — ✗ multiple unrelated changes |
| Reversible | Every migration has corresponding rollback (down migration) — ; exceptions: destructive drops after data migration confirmed |
| Reviewed | Schema migrations pass code review like application code |

### ✗ Schema + Data in Same Migration

Separate schema changes from data changes. Schema migration alters structure; data migration transforms content. Mixing them creates rollback complexity and lock contention.

Migration ordering for combined changes:
1. Schema migration: add new column (nullable)
2. Data migration: populate new column from existing data
3. Schema migration: add NOT NULL constraint, drop old column

### Safe Operations

| Operation | Safe at scale? | Mitigation |
|---|---|---|
| Add nullable column | Yes | No table rewrite |
| Add column with default | Database-dependent | PostgreSQL 11+: safe; older: table rewrite |
| Add index | Risk — locks writes | Use `CONCURRENTLY` (PostgreSQL) or equivalent |
| Drop column | Yes | Drop dependent indexes/constraints first |
| Rename column | Risk — breaks queries | Use add-new → migrate → drop-old pattern |
| Change column type | Risk — table rewrite | Use add-new → migrate → drop-old pattern |
| Add NOT NULL | Risk — full scan | Add with valid default, backfill first |

### Migration File Naming

`{version}_{description}.{direction}.sql` — example: `20260413_001_add_user_email_verified.up.sql`

Version format: `YYYYMMDD_NNN` (date + sequence within date) or Unix timestamp. Consistent per project.

### Environment Rules

- Migrations run automatically on deploy — ✗ manual SQL execution in production
- Migration state tracked in database (`schema_migrations` table or equivalent)
- All environments (dev, staging, production) use same migration sequence
- ✗ environment-specific migrations — use configuration/feature flags for environment differences

---

## 7. Query Patterns

### Parameterized Queries

All queries use parameterized statements (bind variables). ✗ string concatenation of user input into SQL — SQL injection is a solved problem. See security/STANDARDS.md for input validation boundary.

| ✗ Never | Correct approach |
|---|---|
| String interpolation in SQL | Bind parameters / prepared statements |
| Dynamic table/column names from user input | Allowlist validation → interpolation |
| Raw SQL from configuration | Parameterized templates with bind slots |

### N+1 Prevention

| Pattern | Solution |
|---|---|
| Loop fetching related records one-by-one | JOIN or batch `WHERE id IN (...)` |
| Lazy loading in ORM triggers per-row query | Eager loading / explicit join specification |
| Nested loop across two tables | Single query with JOIN |

Detect N+1: monitor query count per request. Alert when single request exceeds 10 queries. Investigate when exceeds 5.

### Pagination

| Rule | Detail |
|---|---|
| Paginate at database level | `LIMIT` + `OFFSET` or cursor-based — ✗ fetch-all-filter-in-app |
| Prefer cursor-based for large datasets | Keyset pagination: `WHERE id > last_seen_id ORDER BY id LIMIT N` |
| ✗ OFFSET for deep pages | Performance degrades linearly — O(offset + limit) |
| Always specify ORDER BY with pagination | Without ordering, page content is non-deterministic |
| Return total count separately | `COUNT(*)` in parallel query or cached — ✗ in same query with window function on large sets |

### Query Hygiene

| Rule | Detail |
|---|---|
| ✗ SELECT * in application queries | Explicit column list — reduces I/O, prevents schema change breakage |
| ✗ unbounded queries | Every query has `LIMIT` or known-bounded WHERE clause |
| ✗ implicit type coercion in WHERE | Explicit cast — mismatched types defeat index usage |
| ✗ functions on indexed columns in WHERE | `WHERE LOWER(email) = ?` defeats index — use expression index or store normalized |
| Use EXPLAIN for new queries | Verify index usage before deploying query changes |

---

## 8. Transactions

### ACID Compliance

Every write operation that modifies multiple rows or tables executes within explicit transaction. ✗ implicit auto-commit for multi-step writes — partial state is corrupt state. See architecture/STANDARDS.md §1 principle #17 (copy-on-write) and #18 (WAL).

### Isolation Levels

| Level | Guarantees | Trade-off | Use when |
|---|---|---|---|
| READ UNCOMMITTED | None | Maximum throughput | ✗ Never use — dirty reads cause data corruption |
| READ COMMITTED | No dirty reads | Phantom reads possible | Default for most applications |
| REPEATABLE READ | No dirty + no non-repeatable reads | Higher lock contention | Financial calculations, report generation |
| SERIALIZABLE | Full isolation | Highest contention, retry on conflict | Money transfers, inventory decrement, critical state transitions |

### Transaction Scope

| Rule | Detail |
|---|---|
| As small as possible | Transaction boundary wraps only statements that require atomicity |
| ✗ I/O inside transactions | No HTTP calls, file operations, or message sends within open transaction |
| ✗ user interaction in transaction | Never hold transaction open waiting for user input |
| ✗ long-running transactions | Set statement_timeout; alert on transactions exceeding 5 seconds |
| Explicit COMMIT/ROLLBACK | Every transaction path ends in explicit commit or rollback — ✗ relying on connection close |

### Deadlock Prevention

| Strategy | Implementation |
|---|---|
| Consistent lock ordering | All transactions accessing multiple tables lock in same alphabetical table order |
| Short hold times | Minimize work between first lock and commit |
| Lock timeout | Set `lock_timeout` — fail fast rather than wait indefinitely |
| Retry on deadlock | Application retries deadlock errors (limited retries with backoff) |

### Optimistic Concurrency

For low-contention scenarios, prefer optimistic concurrency over pessimistic locking:
- Add `version` column (integer, incremented on update) or `updated_at` timestamp
- UPDATE includes `WHERE version = expected_version`
- Zero rows affected → conflict detected → application retries or reports conflict
- ✗ SELECT FOR UPDATE as default — use only for high-contention, short-lived operations

---

## 9. Connection Management

### Connection Pooling

| Rule | Detail |
|---|---|
| Pool connections — ✗ connect-per-query | Every application uses connection pool |
| Size pool to hardware | `pool_size = (2 × CPU cores) + disk_spindles` as starting point; tune by measurement |
| Minimum idle connections | Keep 2–5 warm connections to avoid cold-start latency |
| Maximum pool size | Hard cap; reject/queue when pool exhausted — ✗ unbounded growth |
| Connection lifetime | Recycle connections after max lifetime (30 min default) — prevents stale state |
| Idle timeout | Close connections idle beyond threshold (10 min default) |

### Timeout Configuration

| Timeout | Purpose | Default guidance |
|---|---|---|
| Connection timeout | Maximum wait to establish connection | 5 seconds |
| Statement timeout | Maximum execution time per query | 30 seconds (web), 5 min (batch) |
| Lock timeout | Maximum wait to acquire lock | 10 seconds |
| Idle-in-transaction timeout | Maximum time in open transaction without activity | 60 seconds |
| Pool checkout timeout | Maximum wait to acquire connection from pool | 5 seconds |

All timeouts explicitly configured — ✗ relying on database defaults (often infinite). See configuration/STANDARDS.md for connection string management.

### Health Checks

- Pool validates connections before checkout (test query or protocol-level ping)
- Detect and evict broken connections automatically
- Monitor: active connections, idle connections, wait queue depth, checkout time p99
- Alert when pool utilization exceeds 80% sustained over 5 minutes

### Multi-Database

When application connects to multiple databases:
- Separate pool per database
- Independent timeout configuration per pool
- ✗ cross-database transactions — use application-level saga pattern instead

---

## 10. Data Lifecycle

### Soft Delete vs Hard Delete

| Approach | When to use | Implementation |
|---|---|---|
| Soft delete | Audit trail required · undo capability · regulatory retention | `deleted_at TIMESTAMP NULL` — NULL = active, non-NULL = deleted |
| Hard delete | No retention requirement · GDPR right-to-erasure · storage-sensitive | Physical `DELETE` from table |

### Soft Delete Rules

- Every query on soft-deletable tables includes `WHERE deleted_at IS NULL` — use views or ORM default scopes
- Unique constraints include `deleted_at` to allow re-creation: `UNIQUE(email, deleted_at)` or partial unique index on active records
- Soft-deleted records excluded from foreign key validation logic at application level
- Periodic hard-delete of soft-deleted records past retention window (archival job)

### Archival

| Rule | Detail |
|---|---|
| Define retention period per table | Business/regulatory requirement — document in schema comments |
| Archive before delete | Move to archive table or cold storage before hard delete |
| Archive tables mirror source schema | Same columns + `archived_at` timestamp |
| ✗ archive to different column structure | Schema drift between active and archive breaks restore |
| Automate archival | Scheduled job — ✗ manual archive runs |

### Temporal Data

For tables requiring full history (audit, compliance):
- Use temporal table pattern: `{table}_history` with `valid_from`, `valid_to` columns
- Triggers populate history on UPDATE/DELETE
- Current state: query main table. Historical state: query history table with point-in-time filter

---

## 11. Backup & Recovery

### Backup Strategy

| Component | Rule |
|---|---|
| Full backup frequency | Daily minimum; hourly for critical systems |
| Incremental/WAL archiving | Continuous — enables point-in-time recovery between full backups |
| Backup location | Different physical location than primary — ✗ same disk/server |
| Encryption | Backups encrypted at rest — same security as live data |
| Retention | Minimum 30 days; match regulatory requirements |
| Monitoring | Alert on backup failure within 1 hour |

### Point-in-Time Recovery (PITR)

- Enable WAL archiving (PostgreSQL) or binary log (MySQL) — continuous transaction log shipping
- Test PITR recovery monthly — restore to specific timestamp and validate data
- Document recovery time objective (RTO) and recovery point objective (RPO) per database
- See architecture/STANDARDS.md §1 principle #18 (WAL) — log intent before action

### Restore Testing

| Rule | Detail |
|---|---|
| Test restores quarterly minimum | ✗ untested backups — they are not backups, they are hopes |
| Restore to isolated environment | ✗ restore testing against production |
| Validate data integrity post-restore | Row counts, checksums, application-level smoke test |
| Document restore procedure | Step-by-step runbook — recovery is not the time for improvisation |
| Measure restore time | Track actual RTO against target |

### Disaster Recovery

- Replicas in different availability zone minimum; different region for critical systems
- Failover tested semi-annually
- Replica lag monitored — alert when lag exceeds 30 seconds
- ✗ promotion without data integrity check — verify replica consistency before promoting

---

## 12. Scale Matrix

Apply database rigor proportionally to project scale.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Schema design (§1) | Single table ok | 3NF, basic relationships | Full 3NF · documented denormalizations |
| Naming (§2) | Consistent within project | Full convention | Full convention · automated linting |
| Data types (§3) | Reasonable defaults | Correct types, basic constraints | Strict typing · CHECK constraints on all bounded values |
| Constraints (§4) | PK + basic NOT NULL | PK · FK · NOT NULL · unique | Full hierarchy · CHECK · triggers for `updated_at` |
| Indexes (§5) | Primary key only | FK indexes · obvious query indexes | Measured · monitored · covering indexes for hot paths |
| Migrations (§6) | Manual SQL ok | Versioned · reversible | Versioned · reversible · CI-tested · zero-downtime safe |
| Query patterns (§7) | Parameterized minimum | Parameterized · no N+1 | Full hygiene · EXPLAIN-verified · query budget per request |
| Transactions (§8) | Auto-commit ok | Explicit for multi-table writes | Explicit · isolation level chosen · deadlock handling |
| Connections (§9) | Single connection ok | Basic pool | Tuned pool · all timeouts · health checks · monitoring |
| Data lifecycle (§10) | Delete freely | Soft delete for core entities | Full lifecycle · archival · retention policy |
| Backup (§11) | Export/dump sufficient | Daily backup · tested | PITR · encrypted · replicated · tested quarterly |

### Scale Transition

When graduating from one scale to next, apply changes incrementally using migration-based approach. ✗ rewrite schema from scratch — evolve in place per architecture/STANDARDS.md §11 (Strangler Fig).

---

## 13. Database Checklist

### New Database

- [ ] Database engine selected with documented rationale
- [ ] Character encoding set to UTF-8 (or UTF8MB4 for MySQL)
- [ ] Default timezone set to UTC
- [ ] Connection pool configured with all timeouts (§9)
- [ ] Backup schedule configured and first backup verified (§11)
- [ ] Migration tooling chosen and initial migration created (§6)
- [ ] Monitoring: connection count, query latency p99, replication lag

### New Table

- [ ] Table name follows naming convention (§2) — singular, snake_case
- [ ] Primary key defined (§1)
- [ ] All columns NOT NULL unless absence is valid domain state (§4)
- [ ] Data types match domain semantics — ✗ stringly-typed (§3)
- [ ] Foreign keys with explicit ON DELETE action (§4)
- [ ] `created_at` with default CURRENT_TIMESTAMP
- [ ] `updated_at` with trigger-maintained timestamp
- [ ] Indexes on foreign key columns (§5)
- [ ] Soft delete column if retention required (§10)
- [ ] Check constraints on bounded values (§4)

### New Query

- [ ] Parameterized — ✗ string concatenation (§7)
- [ ] Explicit column list — ✗ SELECT * (§7)
- [ ] LIMIT clause or known-bounded WHERE (§7)
- [ ] EXPLAIN reviewed for index usage (§7)
- [ ] N+1 pattern absent — JOINs or batch IN clauses (§7)
- [ ] Pagination uses cursor-based approach for large datasets (§7)

### New Migration

- [ ] Single logical change per migration (§6)
- [ ] Reversible (down migration exists) (§6)
- [ ] Safe for zero-downtime deploy (§6 safe operations table)
- [ ] Schema and data changes in separate migrations (§6)
- [ ] Tested in staging environment before production

### Pre-Production

- [ ] All constraints in §4 applied — NOT NULL, FK, CHECK, UNIQUE
- [ ] Index strategy measured against actual query patterns (§5)
- [ ] Transaction isolation levels documented per operation (§8)
- [ ] Backup tested — restore verified (§11)
- [ ] Connection pool tuned to expected load (§9)
- [ ] Data retention policy defined per table (§10)
- [ ] Disaster recovery runbook written and tested (§11)
