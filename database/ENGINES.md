# Database Engine Standards

> Which database a project runs in production, what it takes to add a second one, and how engines are versioned, upgraded, and migrated.

**ID** `database/engines` · **Tier** Interface · **Version** 1.0
**Owns** production engine default · single-store rule + justification bar for a second store · PostgreSQL extension coverage map · embedded + local-first exception · analytical store rule · managed vs self-hosted decision · engine version + upgrade policy · engine migration protocol · engine parity between environments
**Defers to** schema design · naming · types · constraints · indexes · pagination · transactions · migrations · pooling · WAL/PITR mechanics → [database](STANDARDS.md) · query syntax · engine-specific SQL dialect · migration file format → [sql](../sql/STANDARDS.md) · backup cadence · DR · RTO/RPO · failover testing · infrastructure cost → [devops](../devops/STANDARDS.md) · container base image + runtime hardening → [devops/containers](../devops/CONTAINERS.md) · credential storage · encryption at rest policy · access control → [security](../security/STANDARDS.md) · log store engine + retention → [observability/logs](../observability/LOGS.md) · vector store for embeddings in an LLM application → [llm](../llm/STANDARDS.md) · profiling · cache strategy → [performance](../performance/STANDARDS.md) · environment definitions → [configuration](../configuration/STANDARDS.md)
**Load with** [database](STANDARDS.md) · [sql](../sql/STANDARDS.md) · [devops](../devops/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Production Default](#2-production-default)
3. [Extension Coverage](#3-extension-coverage)
4. [Adding a Second Store](#4-adding-a-second-store)
5. [Embedded and Local-First](#5-embedded-and-local-first)
6. [Analytical Stores](#6-analytical-stores)
7. [Managed vs Self-Hosted](#7-managed-vs-self-hosted)
8. [Version and Upgrade Policy](#8-version-and-upgrade-policy)
9. [Environment Parity](#9-environment-parity)
10. [Engine Migration](#10-engine-migration)
11. [Anti-Patterns](#11-anti-patterns)
12. [Scale Matrix](#12-scale-matrix)
13. [Checklist](#13-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| One engine until it demonstrably cannot | A second store is added against a measured limit of the first, ✗ against a category name |
| The engine is a pinned dependency | Major version declared in config, identical in every environment → [dependencies](../dependencies/STANDARDS.md) |
| Operational surface is the real cost | Each additional engine adds backups, upgrades, monitoring, failover, access control, and an on-call surface — ✗ only a client library |
| Boring wins | An engine the team can already operate beats a better engine nobody can restore at 3am |
| Consistency is a product decision | Choosing an engine that cannot hold a transaction across the data that must agree is choosing to reconcile in application code forever |

---

## 2. Production Default

**PostgreSQL is the default production database for every project.** A project using anything else in production names the reason in an ADR → [documentation](../documentation/STANDARDS.md).

| Scope | Engine |
|---|---|
| Production — any persistent application state | PostgreSQL |
| Embedded · single-writer · local-first | SQLite (§5) |
| Analytical scan over columnar data | Postgres first; a dedicated OLAP store only past the threshold in §6 |
| Cache · ephemeral · ✗ source of truth | Redis \| Valkey, with the loss of its whole dataset an accepted, tested state |
| Anything else | ADR with the measured limit that forced it (§4) |

Rules:

- The default holds regardless of workload shape until §4's bar is met. "It is a document workload" and "it is a queue" are category names, ✗ measurements — Postgres covers both (§3).
- Development and test run the same engine and the same major version as production (§9). "SQLite locally, Postgres in production" is two untested engines, ✗ one.
- A greenfield project starts with exactly one store. A second on day one is speculative operations cost.
- ✗ let a framework default, a hosting provider's free tier, or a starter template pick the engine. The choice is explicit.
- A managed Postgres-compatible service is Postgres for this rule; its compatibility gaps are recorded (§7).

---

## 3. Extension Coverage

Workloads commonly used to justify a second engine, and the PostgreSQL feature that covers them. Reach for the specialized store only once the covering feature is measured insufficient (§4).

| Workload | Covered by | Sufficient until |
|---|---|---|
| Document / schemaless | `JSONB` with GIN indexes | Document size or write rate dominates the working set |
| Key-value | Plain table, or `UNLOGGED` for throwaway | Read rate exceeds what a cache in front of it absorbs |
| Full-text search | `tsvector` + GIN, `pg_trgm` for fuzzy | Relevance tuning, faceting, or multi-language analysis is the product |
| Vector similarity | `pgvector` (HNSW \| IVFFlat) | Index size or recall targets need a dedicated ANN engine → [llm](../llm/STANDARDS.md) |
| Geospatial | PostGIS | Effectively never — PostGIS is the reference implementation |
| Time series | Partitioned tables, BRIN indexes, TimescaleDB | Ingest rate or retention volume needs columnar compression |
| Job queue | `SELECT … FOR UPDATE SKIP LOCKED` | Throughput, fan-out, or delivery semantics exceed what one table sustains |
| Pub/sub · change notification | `LISTEN`/`NOTIFY`, logical replication | Durability, replay, or cross-service fan-out is required → a broker |
| Materialized rollup | Materialized views, incremental refresh | Refresh cost dominates the write path |
| Row-level multi-tenancy | Row-level security + tenant column | Tenants need physical isolation for compliance |

Rules:

- The covering feature is tried and measured first. A benchmark on the real dataset is the evidence, ✗ a blog post about someone else's.
- Every extension in use is pinned by version and present in every environment (§9). An extension available in development and missing in production is a deploy-time outage.
- An extension the managed provider does not offer is a §7 constraint, ✗ a reason to abandon the default silently.

---

## 4. Adding a Second Store

A second engine is a schema change to the whole system's operations. It passes every row before it ships.

| Gate | Evidence required |
|---|---|
| Measured limit | A benchmark on production-shaped data showing the covering Postgres feature (§3) misses a stated budget → [performance](../performance/STANDARDS.md) |
| Tuning exhausted | Index, query, partition, and hardware changes tried and recorded first |
| Bounded scope | Exactly which data moves, and which stays. "Some of it, eventually" is unbounded |
| Consistency model stated | What can be stale, for how long, and what reconciles it. A dual write with no reconciliation is a data-loss design |
| Source of truth named | One store is authoritative per fact → [architecture](../architecture/STANDARDS.md). ✗ two writers to the same fact |
| Operational plan | Backup, restore rehearsal, upgrade path, monitoring, alerting, access control, on-call runbook → [devops](../devops/STANDARDS.md) |
| Exit plan | How the data comes back if the store is retired (§10) |
| ADR | Decision, alternatives measured, and the trigger that would reverse it → [documentation](../documentation/STANDARDS.md) |

Rules:

- Dual writes across two stores without a transaction need an outbox or CDC, ✗ two calls in a request handler and hope.
- A cache is not a second store while its whole dataset may be lost and rebuilt. The moment anything is read from it that cannot be recomputed, it is a store and every gate applies.
- Derived stores (search index, read model, warehouse) are rebuildable from the source of truth by a tested, scheduled job. A derived store that cannot be rebuilt is a source of truth wearing the wrong label.
- ✗ add a store for a workload that has not shipped. Speculative persistence is the most expensive speculation.

---

## 5. Embedded and Local-First

SQLite is the correct engine — ✗ a compromise — where the workload matches every row:

| Condition | Rule |
|---|---|
| Single writer | One process writes, or writes are serialized. Multi-writer concurrency is where SQLite stops being the right answer |
| Data is local to its owner | The file lives with the project, device, or user it describes — ✗ shared across hosts |
| Network access ✗ required | Embedding the engine removes a service, a port, and a failure mode |
| Dataset fits local storage | With headroom for the WAL and for growth over the retention window |

Rules:

- Local-first is a deliberate architecture, ✗ a smaller Postgres. Declared in the ADR the same way a second store is.
- Required pragmas at every connection: `foreign_keys = ON` · `journal_mode = WAL` · `busy_timeout` set → [sql](../sql/STANDARDS.md) owns the settings.
- Backup is a documented file-level procedure including the WAL, ✗ copying the database file while writers are live.
- An embedded store that later needs concurrent remote writers migrates to the production default (§10) — ✗ grows a network layer in front of SQLite.
- ✗ ship SQLite in production for shared multi-user application state to avoid running a database.

---

## 6. Analytical Stores

| Rule | Detail |
|---|---|
| Analytics on the production database is bounded | Read replica, statement timeout, and a separate pool. An analyst's query never contends with a user's |
| Postgres first | Partitioning, BRIN, materialized views, and a replica carry most reporting workloads |
| Threshold for a columnar store | Scan volume, concurrency, or refresh latency misses a stated budget on a tuned replica — measured, ✗ assumed |
| Embedded analytics | DuckDB for local, single-process analysis over files or an extract — ✗ a shared warehouse |
| The warehouse is derived | Rebuildable from the source of truth. A fact that exists only in the warehouse is an unbackedup source of truth |
| One lineage | Every warehouse table names its upstream source and the job that populates it → [data_pipeline](../data_pipeline/STANDARDS.md) |

---

## 7. Managed vs Self-Hosted

| Rule | Detail |
|---|---|
| Managed by default | Provider-operated Postgres unless a named constraint (residency, compliance, cost at measured scale, required extension) forbids it |
| Compatibility gaps recorded | Postgres-compatible ✗ Postgres. Unsupported extensions, missing superuser operations, and differing defaults are documented before the project depends on them |
| Self-hosted carries the full burden | Backups, restore rehearsals, upgrades, patching, failover, monitoring — assigned to a named owner → [devops](../devops/STANDARDS.md), ✗ implied |
| Restore is rehearsed either way | A managed backup nobody has restored is a hypothesis. Rehearsal cadence → [devops](../devops/STANDARDS.md) |
| Connection limits are a design input | Serverless and pooled architectures hit connection ceilings first. Pooler placement is decided before load, ✗ after |
| Portability is maintained | ✗ depend on a proprietary extension or API without an ADR recording the lock-in accepted |

---

## 8. Version and Upgrade Policy

| Rule | Detail |
|---|---|
| Major version pinned in config | Not "latest", not the provider's rolling default → [configuration](../configuration/STANDARDS.md) |
| Supported versions only | Run a version still receiving security patches. An end-of-life engine is an unpatched network service |
| Minor upgrades on the provider's cadence | Applied within the patch window the project's policy sets → [dependencies](../dependencies/STANDARDS.md) |
| Major upgrades are a project | Tested against a production-shaped copy, with a measured rollback path, before the production window |
| Extension compatibility checked first | Every pinned extension is confirmed against the target major version before the upgrade is scheduled |
| Deprecations tracked | Behavior changes that affect queries, collation, or defaults are reviewed against the schema, ✗ discovered in production |
| Collation changes are index-invalidating | A libc or ICU collation change requires index rebuild. Planned, ✗ absorbed silently |

---

## 9. Environment Parity

| Rule | Detail |
|---|---|
| Same engine, same major version | dev · test · CI · staging · production. A different engine in any one of them means the tests prove nothing about production |
| Same extensions | Every extension present and version-matched everywhere |
| Containerized locally | The engine runs as a pinned container image so every machine gets the same one → [devops/containers](../devops/CONTAINERS.md) |
| Integration tests use the real engine | Tests that touch SQL run against the production engine, ✗ an in-memory substitute with a different dialect → [testing](../testing/STANDARDS.md) |
| Configuration differences are declared | Where a setting legitimately differs by environment, it is named in config, ✗ left to a default |
| Data shape, ✗ data volume | Lower environments match production's schema and cardinality distribution as far as privacy allows — ✗ its size |

---

## 10. Engine Migration

Moving between engines. Expand → dual-run → verify → cut over → contract, the same shape as a schema migration → [database §10](STANDARDS.md#10-migrations).

| Step | Rule |
|---|---|
| Inventory | Every query, extension, type, and engine-specific behavior in use is listed before the first line is written |
| Target schema | Re-modeled for the target engine, ✗ a mechanical type-for-type copy that carries workarounds forward |
| Backfill | Idempotent, resumable, and rate-limited. A backfill that cannot resume restarts from zero on any error |
| Dual-run | Both stores written, the old one authoritative, for a stated window |
| Verification | Row counts, checksums, and a sampled field-level diff — the exit criterion is a number, ✗ a feeling |
| Cutover | Reads switch behind a flag → [configuration](../configuration/STANDARDS.md), reversible without a deploy |
| Contract | The old store is removed only after the rollback window closes, with a final backup retained |

Rules:

- The application talks to the database through one boundary, so a migration touches that boundary — ✗ every call site → [architecture](../architecture/STANDARDS.md).
- ✗ migrate and change the schema's meaning in the same step. The diff becomes unverifiable.
- A migration with no verification step is a copy, ✗ a migration.

---

## 11. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Engine chosen by category name | "Document workload → document database" skips measuring that `JSONB` covers it | Measure the covering feature (§3) |
| SQLite in dev, Postgres in production | Dialect and concurrency differences surface only in production | Same engine everywhere (§9) |
| Store per feature | Operations cost multiplies; nobody can restore all of them | One engine until measured (§2, §4) |
| Cache promoted to store by accident | Data nobody can recompute lives somewhere with no backup | Any non-recomputable read makes it a store (§4) |
| Dual writes in a request handler | Partial failure leaves the stores permanently disagreeing | Outbox or CDC (§4) |
| Floating major version | The engine changes under the schema with no deploy | Pin the major (§8) |
| Postgres-compatible assumed identical | Missing extensions and operations found at deploy time | Record the gaps (§7) |
| Analytics on the primary | An analyst's scan becomes a user's timeout | Replica, timeout, separate pool (§6) |
| In-memory substitute in tests | Tests pass against a dialect production never runs | Real engine in integration tests (§9) |
| Migration with no verification | Silent data loss discovered by a user | Counts, checksums, sampled diff (§10) |
| End-of-life engine left running | An unpatched network service holding all the data | Supported versions only (§8) |

---

## 12. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Engines in use | One | One, plus a cache | One primary, plus derived stores each with an owner |
| Hosting | Container locally | Managed, with restore rehearsed | Managed with replicas, pooler, and a tested failover |
| Version policy | Pinned major | Pinned major, patched on cadence | Pinned major with a scheduled upgrade project per cycle |
| Analytics | Same database | Read replica with timeouts | Derived warehouse, rebuildable, with lineage |
| Parity | Same image locally | Same engine + extensions everywhere | Parity asserted in CI, drift fails the build |
| Second store | Never | ADR + every §4 gate | Same bar; no exemption for scale |

---

## 13. Checklist

- [ ] Production runs PostgreSQL, or an ADR names the measured reason it does not
- [ ] Exactly one source of truth per fact, with the authoritative store named
- [ ] Any second store passed every §4 gate, including a consistency model and an exit plan
- [ ] Workloads that look like they need another engine were measured against the covering Postgres feature first
- [ ] Every extension in use is pinned and present in every environment
- [ ] Embedded SQLite use meets every §5 condition and is declared in an ADR
- [ ] Caches may lose their entire dataset without data loss, and that has been tested
- [ ] Derived stores are rebuildable from the source of truth by a scheduled, tested job
- [ ] Analytics run on a replica with statement timeouts and a separate pool
- [ ] Managed-provider compatibility gaps are documented before the project depends on them
- [ ] Engine major version is pinned in config and still receiving security patches
- [ ] Major upgrades are tested against a production-shaped copy with a measured rollback path
- [ ] dev · test · CI · staging · production run the same engine, major version, and extensions
- [ ] Integration tests run against the real engine, not an in-memory substitute
- [ ] Any engine migration has a numeric verification step and a flag-reversible cutover
