# SQL Standards

Rules for writing, organizing, and maintaining SQL across all projects.
Covers formatting, naming, schema design, query patterns, migrations,
and engine-specific guidance for DuckDB/SQLite.

Composable with: `database/STANDARDS.md` (schema design · migrations · transactions),
`security/STANDARDS.md` (injection prevention), `performance/STANDARDS.md` (query tuning).

---

## Table of Contents

1. [Formatting](#1-formatting)
2. [Naming Conventions](#2-naming-conventions)
3. [Schema Design](#3-schema-design)
4. [Data Types](#4-data-types)
5. [Query Style](#5-query-style)
6. [Index Strategy](#6-index-strategy)
7. [Migration Format](#7-migration-format)
8. [Transaction Patterns](#8-transaction-patterns)
9. [Parameterized Queries](#9-parameterized-queries)
10. [Common Table Expressions](#10-common-table-expressions)
11. [Stored Procedures](#11-stored-procedures)
12. [Performance](#12-performance)
13. [DuckDB / SQLite Patterns](#13-duckdb--sqlite-patterns)
14. [Anti-Patterns](#14-anti-patterns)
15. [Checklist](#15-checklist)

---

## 1. Formatting

### 1.1 Keyword Casing

All SQL keywords uppercase. All identifiers (tables, columns, aliases) lowercase snake_case.

```sql
-- Correct
SELECT
    user_id,
    created_at
FROM account
WHERE status = 'active';

-- Wrong
select User_Id, Created_At from Account where Status = 'active';
```

### 1.2 Clause Indentation

Each major clause starts at column 0. Columns, conditions, and expressions indented 4 spaces.

```sql
SELECT
    o.order_id,
    o.total_amount,
    c.email
FROM order_line o
INNER JOIN customer c
    ON c.customer_id = o.customer_id
WHERE
    o.status = 'shipped'
    AND o.created_at >= '2025-01-01'
ORDER BY
    o.created_at DESC
LIMIT 100;
```

### 1.3 One Column Per Line

Every column in SELECT, every condition in WHERE/ON gets its own line.
Exception: `SELECT COUNT(*)` or single-column queries.

```sql
-- Correct
SELECT
    product_id,
    product_name,
    unit_price,
    quantity_in_stock
FROM product;

-- Wrong
SELECT product_id, product_name, unit_price, quantity_in_stock FROM product;
```

### 1.4 Comma Placement

Leading commas (comma at start of line). Easier to comment out columns, cleaner diffs.

```sql
SELECT
    user_id
    , first_name
    , last_name
    , email
FROM account;
```

### 1.5 Trailing Semicolons

Every statement ends with `;`. No exceptions.

---

## 2. Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Table | singular snake_case | `customer`, `order_line` |
| Column | snake_case | `created_at`, `unit_price` |
| Primary key | `id` or `<table>_id` | `id`, `customer_id` |
| Foreign key | `<referenced_table>_id` | `customer_id` in `order` |
| Boolean column | `is_` / `has_` prefix | `is_active`, `has_paid` |
| Timestamp column | `_at` suffix | `created_at`, `deleted_at` |
| Date column | `_on` suffix | `shipped_on`, `due_on` |
| Index | `ix_<table>_<columns>` | `ix_order_customer_id` |
| Unique constraint | `uq_<table>_<columns>` | `uq_customer_email` |
| Check constraint | `ck_<table>_<description>` | `ck_order_positive_total` |
| Foreign key constraint | `fk_<table>_<ref_table>` | `fk_order_customer` |
| Primary key constraint | `pk_<table>` | `pk_customer` |
| Default value | `df_<table>_<column>` | `df_order_status` |

Rules:
- ✗ pluralized table names (`customers` → `customer`)
- ✗ camelCase or PascalCase anywhere
- ✗ reserved words as identifiers (`user` → `account`, `order` → `purchase_order` or quote)
- ✗ abbreviations unless universally understood (`id`, `url`, `ip` OK; `cust`, `amt` ✗)
- Junction/bridge tables: `<table_a>_<table_b>` alphabetical → `author_book`

---

## 3. Schema Design

### 3.1 Normalization Default

Normalize to 3NF by default. Denormalize only with documented justification + performance evidence.

| Situation | Action |
|---|---|
| Read-heavy reporting table | Materialized view or denormalized read model — document why |
| Repeated joins killing latency | Add redundant column — add comment + trigger/app-level sync |
| Analytics/OLAP workload | Star schema acceptable — separate from OLTP schema |
| Everything else | 3NF minimum |

### 3.2 Every Table Must Have

```sql
CREATE TABLE customer (
    id          INTEGER PRIMARY KEY,              -- or BIGINT/UUID per engine
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(), -- row birth
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()  -- last mutation
);
```

- Primary key: always. Prefer surrogate `id` (integer or UUID).
- `created_at` + `updated_at`: always present, never nullable.
- Natural keys → unique constraint, not primary key.

### 3.3 Constraint Naming

✗ anonymous constraints. Every constraint explicitly named.

```sql
-- Correct
ALTER TABLE order_line
    ADD CONSTRAINT fk_order_line_product
    FOREIGN KEY (product_id) REFERENCES product (id);

-- Wrong
ALTER TABLE order_line
    ADD FOREIGN KEY (product_id) REFERENCES product (id);
```

### 3.4 Soft Deletes vs Hard Deletes

| Approach | When |
|---|---|
| Soft delete (`deleted_at TIMESTAMP NULL`) | Audit requirements · undo capability needed · foreign key dependencies |
| Hard delete | Ephemeral data · GDPR/compliance requirement · no downstream references |

Soft delete columns are nullable — `NULL` means not deleted. Add partial index on `deleted_at IS NULL` for active-row queries.

See `database/STANDARDS.md` for migration and schema evolution rules.

---

## 4. Data Types

### 4.1 Core Rules

| Rule | Detail |
|---|---|
| ✗ stringly-typed data | Dates → `DATE`/`TIMESTAMP`. Booleans → `BOOLEAN`. Numbers → numeric type. |
| Monetary values | `NUMERIC(19,4)` or `DECIMAL(19,4)`. ✗ `FLOAT`/`DOUBLE` for money. |
| UUIDs | Use native `UUID` type where available. ✗ store as `VARCHAR(36)`. |
| IP addresses | `INET` (Postgres) or `INTEGER` (SQLite, store as 32-bit). ✗ `VARCHAR(15)`. |
| JSON/semi-structured | `JSONB` (Postgres) or `JSON` (SQLite/DuckDB). ✗ untyped `TEXT` blobs. |
| Enums | Check constraint or enum type. ✗ unconstrained `VARCHAR`. |
| Text with limit | `VARCHAR(n)` with realistic max. ✗ `VARCHAR(255)` as default for everything. |
| Unlimited text | `TEXT`. ✗ `VARCHAR(99999)`. |

### 4.2 Timestamp Rules

- Store timestamps in UTC. Always.
- Use `TIMESTAMP WITH TIME ZONE` (`TIMESTAMPTZ`) where engine supports it.
- Display timezone conversion happens at application layer, never in stored data.
- ✗ `TIMESTAMP WITHOUT TIME ZONE` for anything user-facing.

### 4.3 NULL Semantics

- Column is `NOT NULL` by default — add nullable only with explicit reason.
- ✗ use `NULL` to mean "empty string" or "zero" or "false".
- `NULL` means "unknown" or "not applicable" — no other meaning.
- Document nullable columns: why NULL is valid state.

---

## 5. Query Style

### 5.1 Explicit Column Lists

```sql
-- Correct
SELECT
    customer_id
    , first_name
    , email
FROM customer;

-- Wrong: schema changes silently break consumers
SELECT * FROM customer;
```

✗ `SELECT *` in application queries. Allowed only in: ad-hoc exploration, `EXISTS` subqueries, CTEs that immediately follow with explicit column list.

### 5.2 ANSI JOIN Syntax

✗ implicit joins (comma-separated FROM with WHERE conditions).

```sql
-- Correct (ANSI)
SELECT
    o.id
    , c.email
FROM purchase_order o
INNER JOIN customer c
    ON c.id = o.customer_id;

-- Wrong (implicit/theta)
SELECT
    o.id
    , c.email
FROM purchase_order o, customer c
WHERE c.id = o.customer_id;
```

### 5.3 Table Aliases

- Use short meaningful aliases, not single letters (unless table name is short).
- Alias every table when query has 2+ tables.

| Table | Acceptable Aliases |
|---|---|
| `customer` | `c`, `cust` |
| `purchase_order` | `o`, `po` |
| `order_line_item` | `li`, `oli` |
| Single-table query | No alias needed |

### 5.4 JOIN Order

FROM the driving/primary table first. JOIN tables in logical dependency order.

### 5.5 WHERE Clause Style

```sql
WHERE
    o.status = 'shipped'
    AND o.created_at >= :start_date
    AND o.total_amount > 0
```

- Leading `AND`/`OR` operators.
- ✗ trailing `AND` style.
- Group complex conditions with parentheses — even when precedence is unambiguous.

### 5.6 INSERT Style

```sql
INSERT INTO customer (
    first_name
    , last_name
    , email
    , created_at
) VALUES (
    :first_name
    , :last_name
    , :email
    , NOW()
);
```

✗ `INSERT INTO table VALUES (...)` without column list.

---

## 6. Index Strategy

### 6.1 When to Index

| Index When | Skip When |
|---|---|
| Column in WHERE/JOIN/ORDER BY on large table (>10K rows) | Table <1K rows (full scan faster) |
| Foreign key columns (always) | Columns rarely filtered/sorted |
| Columns with high selectivity | Low-selectivity columns (boolean with 50/50 split) |
| Covering index eliminates table lookup | Write-heavy table where index maintenance > read benefit |

### 6.2 Composite Index Column Order

Column order in composite index matters. Rule: **equality → range → sort**.

```sql
-- Query pattern
WHERE status = 'active' AND created_at >= '2025-01-01' ORDER BY last_name

-- Index for this pattern
CREATE INDEX ix_customer_status_created_last
    ON customer (status, created_at, last_name);
--             equality  range       sort
```

### 6.3 Covering Indexes

Include all columns query needs → index-only scan, no heap lookup.

```sql
-- Query only needs email + status
CREATE INDEX ix_customer_status_email
    ON customer (status) INCLUDE (email);
```

### 6.4 Partial Indexes

Index only rows that matter. Smaller index → faster lookups.

```sql
-- Only index active customers (90% of queries filter on active)
CREATE INDEX ix_customer_active
    ON customer (last_name, email)
    WHERE deleted_at IS NULL;
```

### 6.5 Index Rules

- ✗ index every column. Each index costs write performance.
- ✗ duplicate indexes (index on `(a, b)` already covers queries on `(a)`).
- Review unused indexes periodically — drop dead indexes.
- Name all indexes explicitly: `ix_<table>_<columns>`.
- Unique business rules → unique index, not application-level check.

---

## 7. Migration Format

### 7.1 File Naming

Sequential numbering with timestamp prefix + descriptive name.

```
migrations/
├── 001_20250115_create_customer.sql
├── 002_20250115_create_purchase_order.sql
├── 003_20250120_add_customer_email_index.sql
├── 004_20250201_add_order_status_column.sql
```

### 7.2 Structure

Every migration file has up (apply) and down (rollback) sections.

```sql
-- migrate:up
CREATE TABLE customer (
    id          BIGINT GENERATED ALWAYS AS IDENTITY,
    email       VARCHAR(320) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT pk_customer PRIMARY KEY (id),
    CONSTRAINT uq_customer_email UNIQUE (email)
);

CREATE INDEX ix_customer_email ON customer (email);

-- migrate:down
DROP INDEX IF EXISTS ix_customer_email;
DROP TABLE IF EXISTS customer;
```

### 7.3 Migration Rules

| Rule | Detail |
|---|---|
| One change per migration | ✗ create table + add column to another table in same file |
| ✗ mix schema + data | Schema DDL and data DML in separate migrations |
| Idempotent when possible | `CREATE TABLE IF NOT EXISTS`, `DROP INDEX IF EXISTS` |
| ✗ modify past migrations | Applied migrations are immutable — create new migration to fix |
| Backward compatible | New columns `NULL` or with default — ✗ break running application |
| Test rollback | Every `down` must cleanly reverse `up` |
| ✗ `DROP TABLE` without backup plan | Data-destructive migrations need explicit confirmation in deploy pipeline |

### 7.4 Large Table Migrations

For tables >1M rows:
- Add columns as `NULL` first, backfill in batches, then add `NOT NULL` constraint.
- ✗ `ALTER TABLE ... ADD COLUMN ... NOT NULL` on large table without default — locks table.
- Create indexes `CONCURRENTLY` (Postgres) to avoid blocking writes.

See `database/STANDARDS.md` for migration orchestration and deployment strategy.

---

## 8. Transaction Patterns

### 8.1 Explicit Transactions

✗ rely on autocommit for multi-statement operations. Wrap in explicit transactions.

```sql
BEGIN;

UPDATE account
SET balance = balance - 100.00
WHERE id = :sender_id;

UPDATE account
SET balance = balance + 100.00
WHERE id = :receiver_id;

INSERT INTO transfer_log (sender_id, receiver_id, amount, created_at)
VALUES (:sender_id, :receiver_id, 100.00, NOW());

COMMIT;
```

### 8.2 Transaction Scope

- Minimal scope — hold locks for shortest duration possible.
- ✗ user interaction inside transaction (waiting for input while holding locks).
- ✗ external API calls inside transaction.
- ✗ long-running computations inside transaction.

### 8.3 Isolation Level Selection

| Level | Use When | Trade-off |
|---|---|---|
| READ COMMITTED | Default for most OLTP | Phantom reads possible |
| REPEATABLE READ | Report generation · balance checks | Higher lock contention |
| SERIALIZABLE | Financial transactions · inventory | Highest contention, retry on conflict |
| READ UNCOMMITTED | ✗ Never use | Dirty reads — data integrity risk |

### 8.4 Deadlock Prevention

- Access tables in consistent order across all transactions.
- Keep transactions short.
- Use `SELECT ... FOR UPDATE` explicitly when row-level locking needed.
- Implement retry logic for serialization failures (SQLSTATE 40001).

---

## 9. Parameterized Queries

### 9.1 Core Rule

**✗ string concatenation or interpolation for SQL values. Ever.**

```python
# CORRECT — parameterized
cursor.execute(
    "SELECT id, email FROM customer WHERE status = ? AND created_at >= ?",
    (status, start_date)
)

# WRONG — SQL injection vector
cursor.execute(
    f"SELECT id, email FROM customer WHERE status = '{status}'"
)
```

```javascript
// CORRECT
await db.query(
    'SELECT id, email FROM customer WHERE status = $1 AND created_at >= $2',
    [status, startDate]
);

// WRONG
await db.query(
    `SELECT id, email FROM customer WHERE status = '${status}'`
);
```

### 9.2 Identifier Quoting

Table/column names cannot be parameterized in most engines. When dynamic:
- Validate against allowlist of known identifiers.
- ✗ pass user input directly as table/column name.

```python
# CORRECT — allowlist validation
ALLOWED_SORT_COLUMNS = {'created_at', 'email', 'last_name'}
if sort_column not in ALLOWED_SORT_COLUMNS:
    raise ValueError(f"Invalid sort column: {sort_column}")
query = f"SELECT id, email FROM customer ORDER BY {sort_column}"

# WRONG — user controls identifier
query = f"SELECT id, email FROM customer ORDER BY {request.args['sort']}"
```

### 9.3 Batch Parameters

Use executemany / batch parameter binding for bulk operations.

```python
# CORRECT — batch insert
cursor.executemany(
    "INSERT INTO tag (name, category) VALUES (?, ?)",
    [("python", "language"), ("sql", "language"), ("docker", "tool")]
)
```

See `security/STANDARDS.md` for comprehensive injection prevention rules.
