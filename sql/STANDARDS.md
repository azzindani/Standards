# SQL Standards

> How SQL is written: formatting, identifier naming, query construction, parameterization, and migration file format.

**ID** `sql` · **Tier** Language · **Version** 1.0
**Owns** SQL formatting · identifier + constraint naming · data type selection · query style · parameterization at the call site · CTE + window function usage · migration file format · engine-specific SQL (Postgres · DuckDB · SQLite)
**Defers to** schema design + normalization + indexing strategy + transaction isolation + migration safety and orchestration → [database](../database/STANDARDS.md) · injection prevention policy + least-privilege DB users → [security](../security/STANDARDS.md) · performance budgets + profiling method → [performance](../performance/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md)
**Load with** [database](../database/STANDARDS.md) · [security](../security/STANDARDS.md) · [performance](../performance/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Formatting](#2-formatting)
3. [Naming](#3-naming)
4. [Schema Conventions](#4-schema-conventions)
5. [Data Types](#5-data-types)
6. [Query Style](#6-query-style)
7. [Parameterization](#7-parameterization)
8. [CTEs & Window Functions](#8-ctes--window-functions)
9. [Migration Format](#9-migration-format)
10. [Query Performance](#10-query-performance)
11. [Stored Procedures & Triggers](#11-stored-procedures--triggers)
12. [Engine Notes](#12-engine-notes)
13. [Anti-Patterns](#13-anti-patterns)
14. [Checklist](#14-checklist)

---

## 1. Principles

| # | Principle |
|---|---|
| 1 | SQL is source code — reviewed, versioned, formatted, tested. ✗ ad-hoc strings assembled at runtime |
| 2 | Values are always parameters, never concatenated text |
| 3 | Declarative over procedural — express the set, ✗ loop row by row |
| 4 | Explicit over implicit — column lists, join conditions, constraint names, casts |
| 5 | The database enforces its own invariants — constraints, ✗ application-only checks |
| 6 | A query touching production data ships only after `EXPLAIN ANALYZE` |

Schema design, indexing strategy, and transaction isolation → [database](../database/STANDARDS.md). This standard governs how the SQL text itself is written.

---

## 2. Formatting

| Rule | Detail |
|---|---|
| Keywords | UPPERCASE — `SELECT` · `INNER JOIN` · `GROUP BY` |
| Identifiers | lowercase `snake_case` — tables, columns, aliases, CTEs |
| Major clauses | Column 0 — `SELECT` · `FROM` · `WHERE` · `GROUP BY` · `ORDER BY` |
| Expressions | Indented 4 spaces under their clause |
| One item per line | One column per `SELECT` line, one condition per `WHERE`/`ON` line |
| Commas | Leading — `, column` |
| Boolean operators | Leading — `AND` / `OR` start the line, ✗ trailing |
| Terminator | Every statement ends with `;` |

Exception: single-column and `SELECT COUNT(*)` queries may sit on one line.

```sql
SELECT
    o.order_id
    , o.total_amount
    , c.email
FROM purchase_order o
INNER JOIN customer c
    ON c.customer_id = o.customer_id
WHERE
    o.status = :status
    AND o.created_at >= :since
ORDER BY
    o.created_at DESC
LIMIT 100;
```

---

## 3. Naming

| Element | Convention | Example |
|---|---|---|
| Table | singular `snake_case` | `customer` · `order_line` |
| Column | `snake_case` | `created_at` · `unit_price` |
| Primary key | `id` (surrogate) | `id` |
| Foreign key column | `<referenced_table>_id` | `customer_id` |
| Boolean column | `is_` / `has_` prefix | `is_active` · `has_paid` |
| Timestamp column | `_at` suffix | `created_at` · `deleted_at` |
| Date column | `_on` suffix | `shipped_on` · `due_on` |
| Junction table | `<a>_<b>`, alphabetical | `author_book` |
| Primary key constraint | `pk_<table>` | `pk_customer` |
| Foreign key constraint | `fk_<table>_<ref_table>` | `fk_order_customer` |
| Unique constraint | `uq_<table>_<columns>` | `uq_customer_email` |
| Check constraint | `ck_<table>_<description>` | `ck_order_positive_total` |
| Index | `ix_<table>_<columns>` | `ix_order_customer_id` |
| View | `vw_<subject>` | `vw_active_customer` |
| Function | `fn_<verb>_<noun>` | `fn_calculate_balance` |
| Procedure | `sp_<verb>_<noun>` | `sp_archive_old_order` |
| Trigger | `tr_<table>_<timing>_<event>` | `tr_customer_before_update` |

- ✗ pluralized table names — `customers` → `customer`
- ✗ camelCase · PascalCase · `Hungarian_notation` anywhere
- ✗ reserved words as identifiers — `user` → `account`, `order` → `purchase_order`
- ✗ abbreviations that are not universal — `id` · `url` · `ip` OK; `cust` · `amt` · `qty` ✗
- ✗ anonymous constraints — the engine's generated name is unusable in a migration

---

## 4. Schema Conventions

Normalization level, soft-delete policy, partitioning, and indexing strategy → [database](../database/STANDARDS.md). Conventions every table follows:

| Rule | Detail |
|---|---|
| Surrogate primary key | Always present, named `id` |
| Natural key | `UNIQUE` constraint — ✗ as the primary key |
| `created_at` · `updated_at` | Always present, `NOT NULL`, defaulted |
| `NOT NULL` by default | Nullable requires a documented reason |
| Every constraint named | `pk_` · `fk_` · `uq_` · `ck_` prefixes (§3) |
| Foreign keys declared in the schema | ✗ referential integrity enforced only in application code |
| Soft-delete column | `deleted_at TIMESTAMPTZ NULL` — `NULL` = live row |

```sql
CREATE TABLE customer (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    email       VARCHAR(320) NOT NULL,
    is_active   BOOLEAN NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at  TIMESTAMPTZ,
    CONSTRAINT pk_customer PRIMARY KEY (id),
    CONSTRAINT uq_customer_email UNIQUE (email)
);
```

---

## 5. Data Types

| Data | Type | ✗ |
|---|---|---|
| Money | `NUMERIC(19,4)` | `FLOAT` · `DOUBLE` — rounding error is silent and permanent |
| Timestamp | `TIMESTAMPTZ`, stored UTC | `TIMESTAMP WITHOUT TIME ZONE` for anything user-facing |
| Date without time | `DATE` | `VARCHAR` · epoch integer |
| Boolean | `BOOLEAN` | `CHAR(1)` · `INTEGER` 0/1 · `VARCHAR` `'Y'`/`'N'` |
| UUID | native `UUID` | `VARCHAR(36)` |
| IP address | `INET` (Postgres) · `INTEGER` (SQLite) | `VARCHAR(15)` |
| Semi-structured | `JSONB` (Postgres) · `JSON` (SQLite · DuckDB) | untyped `TEXT` blob |
| Closed value set | enum type \| `CHECK` constraint | unconstrained `VARCHAR` |
| Bounded text | `VARCHAR(n)` at the real limit | `VARCHAR(255)` as a reflex default |
| Unbounded text | `TEXT` | `VARCHAR(99999)` |

- Timezone conversion happens in the application layer — stored data is UTC. Always.
- `NULL` means "unknown" or "not applicable". ✗ `NULL` to mean empty string, zero, or false.
- ✗ stringly-typed columns — a date in a `VARCHAR` cannot be range-scanned or validated.

---

## 6. Query Style

| Rule | Detail |
|---|---|
| Explicit column list | ✗ `SELECT *` in application code. Permitted in ad-hoc exploration and `EXISTS` subqueries |
| ANSI joins | `JOIN ... ON` — ✗ comma-joins with predicates in `WHERE` (a missing predicate → silent cross join) |
| Alias every table | When the query has 2+ tables. Short, meaningful — ✗ `a`, `b`, `t1` |
| Qualify every column | `o.status`, ✗ bare `status` in a multi-table query |
| Driving table first | Then `JOIN` in dependency order |
| Parenthesize mixed `AND`/`OR` | Even when precedence is unambiguous |
| `INSERT` names its columns | ✗ `INSERT INTO t VALUES (...)` — positional inserts break on any column addition |
| `UPDATE`/`DELETE` always have `WHERE` | ✗ unqualified mutation. Review any statement without one |
| `COUNT(*)` | ✗ `COUNT(column)` unless deliberately counting non-`NULL` |
| Explicit casts | ✗ rely on implicit coercion across engines |

```sql
INSERT INTO customer (
    email
    , created_at
) VALUES (
    :email
    , NOW()
)
ON CONFLICT (email) DO UPDATE
    SET updated_at = NOW()
RETURNING id;
```

---

## 7. Parameterization

**✗ string concatenation, interpolation, or f-string construction of SQL containing external values. No exception.**

```python
cursor.execute(                                            # ✓ bound parameters
    "SELECT id, email FROM customer WHERE status = ? AND created_at >= ?",
    (status, start_date),
)
cursor.execute(f"SELECT id FROM customer WHERE status = '{status}'")   # ✗ injection
```

```javascript
await db.query(                                            // ✓ bound parameters
    'SELECT id, email FROM customer WHERE status = $1 AND created_at >= $2',
    [status, startDate],
);
await db.query(`SELECT id FROM customer WHERE status = '${status}'`);  // ✗ injection
```

| Rule | Detail |
|---|---|
| Values → placeholders | `?` · `$1` · `:name` per driver |
| Identifiers cannot be bound | Table/column names are not parameterizable — validate against an allowlist |
| ✗ user input as an identifier | `ORDER BY {user_input}` → allowlist the column set, reject anything else |
| Bulk writes | `executemany` / batch binding — ✗ interpolate a VALUES list |
| `IN` lists | Bind an array (`= ANY($1)`) \| generate exactly N placeholders — ✗ join user values into a string |
| ORM escape hatches (`raw`, `text`) | Still parameterize. The escape hatch does not escape the rule |

Least-privilege database users, secret handling, and the full injection threat model → [security](../security/STANDARDS.md).

---

## 8. CTEs & Window Functions

### CTEs

| Rule | Detail |
|---|---|
| Name the dataset, not the operation | `active_customer` ✓ · `filtered_data` ✗ · `temp1` ✗ |
| Use for | Readability · reuse within a statement · recursion · replacing nested subqueries |
| ✗ nested subqueries deeper than 2 levels | Refactor to a CTE chain |
| ✗ CTE for a trivial single-table filter | A subquery reads clearer |
| Recursive CTE | ! explicit termination condition + depth guard — unbounded recursion hangs the connection |
| Materialization | Postgres 12+ inlines CTEs; force with `MATERIALIZED` / `NOT MATERIALIZED` when the plan is wrong |

```sql
WITH RECURSIVE org_tree AS (
    SELECT id, name, manager_id, 0 AS depth
    FROM employee
    WHERE manager_id IS NULL

    UNION ALL

    SELECT e.id, e.name, e.manager_id, ot.depth + 1
    FROM employee e
    INNER JOIN org_tree ot
        ON ot.id = e.manager_id
    WHERE ot.depth < 20          -- ! guard: prevents infinite recursion on a cyclic graph
)
SELECT id, name, depth FROM org_tree;
```

### Window Functions

Use a window function instead of a self-join or a correlated subquery for ranking, running totals, and per-group comparisons.

| Need | Function |
|---|---|
| Latest row per group | `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ... DESC) = 1` |
| Rank with ties | `RANK()` · `DENSE_RANK()` |
| Running total | `SUM(x) OVER (ORDER BY ... ROWS UNBOUNDED PRECEDING)` |
| Previous / next row | `LAG(x)` · `LEAD(x)` |
| Group aggregate beside detail rows | `SUM(x) OVER (PARTITION BY ...)` |

```sql
SELECT
    customer_id
    , order_id
    , total_amount
FROM (
    SELECT
        customer_id
        , order_id
        , total_amount
        , ROW_NUMBER() OVER (PARTITION BY customer_id ORDER BY created_at DESC) AS rn
    FROM purchase_order
) ranked
WHERE rn = 1;                    -- ✓ latest order per customer, single scan
```

---

## 9. Migration Format

Migration safety, ordering, deployment, and rollback strategy → [database](../database/STANDARDS.md). File format below.

### File Naming

`<sequence>_<date>_<verb>_<subject>.sql` — sequence is zero-padded and monotonic.

```text
migrations/
├── 001_20260114_create_customer.sql
├── 002_20260114_create_purchase_order.sql
└── 003_20260120_add_customer_email_index.sql
```

### Structure

Every file carries an up section and a down section. ✗ a migration without a down.

```sql
-- migrate:up
CREATE TABLE customer (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    email       VARCHAR(320) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_customer PRIMARY KEY (id),
    CONSTRAINT uq_customer_email UNIQUE (email)
);

-- migrate:down
DROP TABLE IF EXISTS customer;
```

| Rule | Detail |
|---|---|
| One logical change per file | ✗ create a table and alter another in the same migration |
| Schema and data in separate files | DDL never mixed with DML |
| Applied migrations are immutable | ✗ edit a migration that has run anywhere — write a new one |
| Idempotent guards | `IF NOT EXISTS` · `IF EXISTS` |
| Down section is executable | Tested, not decorative |
| Destructive DDL flagged | `DROP TABLE` · `DROP COLUMN` · `TRUNCATE` require explicit sign-off in the deploy path |

---

## 10. Query Performance

Budgets, profiling methodology, and index design → [performance](../performance/STANDARDS.md) and [database](../database/STANDARDS.md). Rules for the query text:

### EXPLAIN Before Merge

Any query touching >10K rows or joining 3+ tables runs `EXPLAIN ANALYZE` before it merges.

| Engine | Command |
|---|---|
| Postgres | `EXPLAIN (ANALYZE, BUFFERS) SELECT ...` |
| DuckDB | `EXPLAIN ANALYZE SELECT ...` |
| SQLite | `EXPLAIN QUERY PLAN SELECT ...` |

Reject the plan on: sequential scan of a large table without justification · nested loop over a large join · row-estimate off by >10x from actual.

### Sargability

| ✗ | → |
|---|---|
| `WHERE UPPER(email) = :e` | Store normalized, or build an expression index. A function on an indexed column disables the index |
| `WHERE created_at::date = :d` | `WHERE created_at >= :d AND created_at < :d + INTERVAL '1 day'` |
| `WHERE col LIKE '%term%'` | Full-text index · trigram index |
| `WHERE col + 0 = :n` | `WHERE col = :n` |
| Correlated subquery per row | `JOIN` \| window function |
| `SELECT DISTINCT` to hide a duplicating join | Fix the join |
| `ORDER BY` with no `LIMIT` on a large table | Bound the result set |
| `ORDER BY RANDOM()` | `TABLESAMPLE` \| random offset on an indexed key |

### N+1

✗ a query inside a loop. Batch into one statement with `= ANY(:ids)` or a `JOIN` against a values list.

### Pagination

| Pattern | When | Cost |
|---|---|---|
| Keyset / cursor | Default | O(log n) — stable under concurrent writes |
| `OFFSET`/`LIMIT` | Static admin tables only, < 10K rows | O(offset) — threshold + rationale → [database](../database/STANDARDS.md#7-pagination--n1) |

```sql
SELECT id, email, created_at
FROM customer
WHERE created_at < :last_seen_created_at     -- ✓ keyset: seeks, never counts past rows
ORDER BY created_at DESC
LIMIT 50;
```

### Batching

Bulk insert via multi-row `VALUES` or `COPY` · bulk update via `UPDATE ... FROM` · bulk delete in batches of ≤1000 keys. ✗ single-row `INSERT` in a loop.

---

## 11. Stored Procedures & Triggers

| Use for | ✗ Use for |
|---|---|
| Multi-statement atomic operations | Business logic · domain rules |
| Database-internal maintenance | Input validation (belongs at the application boundary) |
| Audit-log triggers | Workflow orchestration |
| Performance-critical set operations | API response shaping |

- ✗ business logic in the database — business rules change faster than schema and are harder to test and deploy.
- Every function/procedure carries a header comment: purpose · parameters · return · side effects.
- Trigger cascade depth ≤ 2. ✗ triggers firing triggers firing triggers.
- Triggers that mutate other tables must be documented in the table's schema comment.

---

## 12. Engine Notes

### Postgres

Default choice for OLTP. `JSONB` over `JSON` · `TIMESTAMPTZ` over `TIMESTAMP` · `GENERATED ALWAYS AS IDENTITY` over `SERIAL` · `TEXT` over `VARCHAR(n)` when there is no real limit.

### DuckDB — In-Process OLAP

```sql
SELECT product_category, SUM(revenue) AS total_revenue
FROM read_parquet('data/sales_*.parquet')     -- ✓ query files directly, no import step
GROUP BY product_category
ORDER BY total_revenue DESC;

COPY (SELECT * FROM sales WHERE region = 'EMEA') TO 'emea.parquet' (FORMAT PARQUET);
```

- Parquet over CSV for anything >100MB.
- `:memory:` for ephemeral analysis; a file for reusable data.
- Write set-based SQL — DuckDB vectorizes it. Row-by-row patterns defeat the engine.

### SQLite — Embedded / Local-First

```sql
PRAGMA foreign_keys = ON;      -- ! OFF by default — set on every connection
PRAGMA journal_mode = WAL;     -- concurrent readers
PRAGMA busy_timeout = 5000;    -- ms — ✗ leave at 0, writers fail instantly under contention
PRAGMA synchronous = NORMAL;   -- safe under WAL
```

- `PRAGMA foreign_keys = ON` at **every** connection open — it does not persist.
- Type affinity is not type enforcement — add `CHECK` constraints for strict typing, or use `STRICT` tables (3.37+).
- Single writer only. Serialize writes; WAL gives concurrent reads, not concurrent writes.
- `INTEGER PRIMARY KEY` aliases the rowid — fastest key.
- Timestamps: ISO-8601 text (`'2026-01-15T10:30:00Z'`) or epoch integer, consistently, never mixed.

---

## 13. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| `SELECT *` in application code | A new column silently changes the result shape | Explicit column list |
| Comma joins | One missing `WHERE` predicate → cartesian product | `JOIN ... ON` |
| String-built SQL | Injection | Bound parameters (§7) |
| `FLOAT` for money | Rounding drift, unauditable totals | `NUMERIC(19,4)` |
| EAV (entity-attribute-value) | Unindexable · unqueryable · type-unsafe | Real columns \| `JSONB` |
| Polymorphic FK (`target_type` + `target_id`) | No referential integrity possible | One FK column per target \| bridge table |
| Comma-separated values in a column | Violates 1NF — cannot index or join | Junction table |
| `VARCHAR(255)` everywhere | Meaningless constraint, misleads the planner | Right-size or `TEXT` |
| Magic numbers — `WHERE status = 3` | Unreadable, unsearchable | Enum \| `CHECK`-constrained code |
| Nullable FK with no documented reason | Orphan semantics undefined | `NOT NULL`, or document why |
| Application-side referential integrity | Races leave orphans | Declare the foreign key |
| Query inside a loop | N+1 round trips | One batched statement |
| Unqualified `UPDATE` / `DELETE` | Whole-table mutation | Mandatory `WHERE` |

---

## 14. Checklist

- [ ] Keywords uppercase, identifiers lowercase `snake_case`
- [ ] Leading commas, leading `AND`/`OR`, one column per line, statement ends with `;`
- [ ] Table names singular; no reserved words as identifiers
- [ ] Every constraint explicitly named with the `pk_`/`fk_`/`uq_`/`ck_`/`ix_` prefix
- [ ] Every table has `id`, `created_at`, `updated_at`; columns `NOT NULL` unless justified
- [ ] Money is `NUMERIC`, timestamps are `TIMESTAMPTZ` in UTC, booleans are `BOOLEAN`
- [ ] ✗ `SELECT *` in application code
- [ ] ANSI `JOIN ... ON` — ✗ comma joins
- [ ] `INSERT` statements name their columns
- [ ] Every `UPDATE`/`DELETE` has a `WHERE` clause
- [ ] Every external value is a bound parameter — ✗ string interpolation anywhere
- [ ] Dynamic identifiers validated against an allowlist
- [ ] Recursive CTEs have a termination condition and a depth guard
- [ ] Window function used instead of a self-join or correlated subquery where applicable
- [ ] Migration file has both `-- migrate:up` and `-- migrate:down` sections
- [ ] One logical change per migration; schema and data changes in separate files
- [ ] ✗ edits to an already-applied migration
- [ ] `EXPLAIN ANALYZE` run on any query touching >10K rows or joining 3+ tables
- [ ] No function wrapped around an indexed column in a `WHERE` clause
- [ ] Pagination uses keyset, or `OFFSET` with a documented bound
- [ ] ✗ queries issued inside a loop
- [ ] SQLite connections set `foreign_keys = ON`, `journal_mode = WAL`, `busy_timeout`
- [ ] Business logic lives in the application, not in triggers or procedures
