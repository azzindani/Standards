# Configuration Standards

> How a project sources, layers, types, validates, and evolves its configuration — and how it gates behavior behind feature flags.

**ID** `configuration` · **Tier** Core · **Version** 1.0
**Owns** config cascade + precedence · typed config schema · fail-fast startup validation · environment parity · defaults · config file formats · dynamic reload · feature flags (lifecycle · kill switches · rollout · flag debt)
**Defers to** secrets — rotation cadence · token classes · derived-values pattern · lifecycle → [security](../security/STANDARDS.md) · vault + runtime injection mechanics → [devops](../devops/STANDARDS.md) · pipeline secret scoping → [cicd](../cicd/STANDARDS.md) · never-commit enforcement + history scrubbing → [git](../git/STANDARDS.md) · changelog format + semver → [git](../git/STANDARDS.md) · layer/tier model → [architecture](../architecture/STANDARDS.md) · file placement + naming → [directory](../directory/STANDARDS.md)
**Load with** [security](../security/STANDARDS.md) · [architecture](../architecture/STANDARDS.md) · [devops](../devops/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Cascade and Precedence](#2-cascade-and-precedence)
3. [Config Schema](#3-config-schema)
4. [Secret Sourcing](#4-secret-sourcing)
5. [Environments and Parity](#5-environments-and-parity)
6. [Feature Flags](#6-feature-flags)
7. [Defaults](#7-defaults)
8. [File Formats and Organization](#8-file-formats-and-organization)
9. [Startup Validation](#9-startup-validation)
10. [Dynamic Configuration](#10-dynamic-configuration)
11. [Config Documentation](#11-config-documentation)
12. [Anti-Patterns](#12-anti-patterns)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Principles

| # | Rule |
|---|---|
| 1 | Config is what varies between deploys. Everything else is code |
| 2 | Config is **data**, ✗ code — ✗ executable config files (Python/JS/Lua) |
| 3 | Strict separation of config from code — the same artifact runs in every environment |
| 4 | Resolved once at startup, at the outermost layer, then **frozen** and passed inward |
| 5 | Validate at startup, ✗ at first use — a bad value must kill the process, not a request at 3 AM |
| 6 | Typed all the way — ✗ a bag of strings reaching business logic |
| 7 | ✗ secrets in config files · ✗ secrets in the repo — injected at runtime (§4) |
| 8 | Environment differences are **values**, ✗ code paths — ✗ `if env == "production"` |
| 9 | Every key has a default that works locally; zero-config startup works for the default case |

---

## 2. Cascade and Precedence

Sources are layered. Later sources override earlier ones, key by key.

| Precedence | Source | Mutability | Typical use |
|---|---|---|---|
| 4 — highest | Runtime flags / CLI args | Per-invocation | Overrides, debugging, one-off runs |
| 3 | Environment variables | Per-process | Deploy-specific values, injected secrets |
| 2 | Config file(s) | Per-deploy | Stable project-wide settings |
| 1 — lowest | Code defaults | Per-release | Fallback for every key |

Order: **defaults → file → env → flags**.

### Resolution Algorithm

1. Load code defaults from the schema (§3).
2. Overlay config file(s).
3. Overlay environment variables.
4. Overlay runtime flags.
5. Validate the merged result against the schema (§9).
6. Freeze — immutable from here (except declared dynamic fields, §10).

### Cascade Rules

| Rule | Detail |
|---|---|
| Merge, ✗ replace | A higher source overrides only the keys it sets; unset keys fall through |
| Single resolution point | Resolved once, at the outermost layer — see [architecture](../architecture/STANDARDS.md) |
| ✗ re-read sources mid-flight | Core logic receives resolved config as an argument; ✗ reads env vars itself |
| ✗ env var access in core logic | Environment reads happen exclusively at the edge |
| Traceability | Startup log records which source supplied each value (secret-flagged values masked) |
| No exceptions to the order | ✗ a key that "just this once" ignores the cascade |

---

## 3. Config Schema

One typed schema is the single source of truth for shape, types, defaults, and constraints. It lives in the innermost dependency-free layer — no I/O.

| Rule | Detail |
|---|---|
| Typed definition | Every key has an explicit type: string · int · bool · duration · path · URL · enum |
| ✗ stringly typed | ✗ port as string · ✗ duration as bare int · ✗ enum as free-form string |
| Typed object out of resolution | Resolution emits a typed struct/object, ✗ a dict of strings |
| Defaults in the schema | Every optional field carries its default in the type definition |
| Required vs optional | Explicit. Required = no default, must be supplied by some source |
| Flat over nested | Dotted keys; max 2 levels of nesting |
| Grouped by concern | Sub-structs: `database` · `server` · `logging` · `auth` |
| Enum constraints | Fixed value sets are enums — an unknown value fails validation, ✗ falls through |

### Per-Field Contract

Every field declares:

| Attribute | Content |
|---|---|
| Name | Dot-path key: `database.pool_size` |
| Type | Semantic type: `uint16` · `duration` · `path` · `enum[...]` |
| Default | Value when no source sets it (optional fields) |
| Constraints | Range · pattern · enum members · min/max |
| Env var | Mapped variable: `APP_DATABASE_POOL_SIZE` |
| Secret | Boolean — drives masking in logs, errors, and diagnostics |
| Dynamic | Boolean — reloadable at runtime (§10) or static |
| Description | One line |

---

## 4. Secret Sourcing

Secrets are owned by [security](../security/STANDARDS.md): rotation cadence, token classes, the derived-values pattern, and secret lifecycle live there. ✗ restate them here. This section covers only where config **sources** secrets from.

### Sourcing Rules

| Rule | Detail |
|---|---|
| ✗ secrets in config files | Never. ✗ in `config.toml`, ✗ in an environment overlay, ✗ in a comment, ✗ in a test fixture |
| ✗ secrets in the repo | Never committed. Enforcement + history scrubbing → [git](../git/STANDARDS.md) |
| Injected at runtime | Secrets enter the process as environment variables or mounted files, ✗ baked into an artifact or image |
| Referenced, ✗ embedded | Config holds a *reference* (`db.password_ref = "secret://app/db"`), resolved at startup |
| ✗ secrets in CLI arguments | Visible in the process list to every user on the host |
| Enter at the edge only | Secrets resolve at the outermost layer; inward code receives derived values — pattern → [security](../security/STANDARDS.md) |
| Masked in output | Secret-flagged fields masked in startup logs, error messages, diagnostics, and config dumps |
| Fail closed | Unresolvable secret → process exits. ✗ start with an empty credential |

### Secret Source by Environment

| Environment | Source |
|---|---|
| Development | `.env` file (gitignored) · local secret manager |
| Test | Static test-only values · `.env.test` (gitignored) |
| Staging · Production | Secret manager / runtime injection — ✗ `.env` files. Mechanics → [devops](../devops/STANDARDS.md) |

### .env Rules

| Rule | Detail |
|---|---|
| `.env` in `.gitignore` | Every project, no exceptions |
| `.env.example` committed | Every key present, placeholder values only, zero real secrets |
| One `.env` per purpose | `.env` (dev) · `.env.test` (test). ✗ `.env.production` |
| `KEY=value` | Quotes only when the value contains spaces; ✗ inline comments |
| ✗ `.env` in production | Production injects from the secret manager |

---

## 5. Environments and Parity

| Environment | Config source | Purpose |
|---|---|---|
| Development | Local file + defaults | Developer workstation |
| Test | Test overrides | Automated test execution |
| Staging | Deployed file + injected env | Pre-production validation — production's twin |
| Production | Deployed file + injected env | Live system |

### Parity Rules

| Rule | Detail |
|---|---|
| One base config | Shared settings live once; per-environment files override only what differs |
| Staging mirrors production | Same config **structure**, same code paths, same backing-service types. Only values differ |
| ✗ environment conditionals in code | ✗ `if env == "production"`. Behavior differences are config values or feature flags |
| ✗ dev-only code paths | A feature exists in all environments or none — flags control activation |
| ✗ backing-service substitution | ✗ SQLite in dev and Postgres in prod — same engine, different instance |
| Single environment variable | `APP_ENV` identifies the environment; everything else is derived from config |
| Naming convention | `APP_` prefix + section + key, uppercase, dots → underscores: `database.host` → `APP_DATABASE_HOST` |

### What Differs vs What Is Shared

| Differs per environment | Identical everywhere |
|---|---|
| Hosts · ports · URLs · connection strings | Key names, schema shape, and types |
| Secret values | Validation rules and constraints |
| Log level and destination | Business logic and code paths |
| Resource limits (pool size, timeouts) | Flag evaluation logic |

---

## 6. Feature Flags

A feature flag decouples a deploy from a release: code ships dark, behavior toggles by config. Every flag is also a fork in the code and a line of debt — it must be removed.

### Flag Types

| Type | Purpose | Default | Lifetime |
|---|---|---|---|
| Release flag | Gate an in-progress feature; enable when ready | OFF | Short — removed after full rollout |
| Kill switch | Instantly disable a risky subsystem in production | ON (feature live) | Long — a permanent operational lever |
| Rollout flag | Gradual exposure — %, cohort, or region | OFF → ramp | Short — removed at 100% |
| Ops flag | Toggle operational behavior (verbose logging, degraded mode) | Per default | Long |

### Lifecycle

| Stage | Rule |
|---|---|
| Born | Created with an **owner** and a **mandatory removal date**; code path gated; default OFF |
| Active | Toggled per environment; rollout flags ramp % → cohort → 100% |
| Decided | Feature permanent (locked ON) or abandoned (locked OFF) — the decision is recorded |
| Removed | Flag, gated branches, and evaluation logic deleted within one release cycle of the decision |

### Rules

| Rule | Detail |
|---|---|
| Every flag has an owner + removal date | ✗ create a flag without both — this is how flag debt is prevented |
| Named by feature, ✗ by ticket | `enable_batch_export` · ✗ `JIRA_1234_flag` |
| Positive naming | `enable_<feature>` · `use_<new_impl>`. ✗ `disable_<feature>` — double negatives when OFF |
| Boolean by default | ON/OFF; multivariate (A/B, %) only when the rollout demands it |
| Evaluated once at entry | Capture the value at the request/invocation boundary — ✗ re-evaluate mid-operation |
| Evaluate at the edge | Flag resolves at the outermost layer; inward code receives a plain boolean, ✗ a flag reference |
| ✗ nested/dependent flags | A flag whose meaning depends on another flag's state → combinatorial explosion |
| New flags default OFF | A newly gated feature starts disabled |
| Kill switch is independent | A kill switch must not depend on the subsystem it disables — evaluate it before that subsystem loads |
| Removal is mandatory | Permanent decision → remove the flag within one release cycle |
| Stale-flag detection | Lint/CI flags unreferenced flags and flags past their removal date for deletion |
| Audit trail | Flag state changes logged: who · when · why |
| Flag state in config or a flag service | ✗ hard-coded in application logic |

---

## 7. Defaults

Every key has a default that makes zero-config startup work for the default use case.

| Rule | Detail |
|---|---|
| Every key defaultable | Except genuinely required, deploy-specific values (which have no safe default) |
| Secure by default | The default is the safer option: TLS on · strict validation · minimal permissions |
| Development-friendly | Defaults target local dev: `localhost` · standard ports · local paths |
| ✗ production values as defaults | ✗ production URLs or credentials as a default — a misconfig must fail, ✗ silently hit prod |
| Conservative resources | Small-but-functional pool sizes, timeouts, buffers |
| Documented | Every default appears in the schema and in `.env.example` |
| Overridable | Any default can be overridden by a higher cascade source |

| Category | Default |
|---|---|
| Host / URL | `localhost` / `127.0.0.1` |
| Port | Standard for the service (5432 Postgres · 8080 HTTP) |
| Timeout | 30 s HTTP · 5 s internal |
| Pool size | 5 connections (functional, not production-scaled) |
| Log level | `INFO` |
| Retry | 3 attempts, exponential backoff |
| TLS/SSL | ON |
| Feature flags | OFF |
| File paths | Relative to project root or XDG-compliant |

---

## 8. File Formats and Organization

| Format | Use for | ✗ When |
|---|---|---|
| TOML | Application config, human-edited, typed values | Nesting > 2 levels |
| YAML | Infra config, complex/multi-doc structures | Simple flat config (TOML is simpler) |
| JSON | Machine-generated config, schemas | Human-edited (no comments) |
| `.env` | Env-var overrides, dev secrets | Structured/nested config |

### Format Rules

| Rule | Detail |
|---|---|
| One primary format per project | ✗ mix TOML and YAML for the same purpose |
| Comments required | The primary format must support comments — rules out JSON as primary |
| ✗ executable config | Config is data — ✗ Python/JS/Lua files as config |
| Standard parser only | Well-maintained, widely-adopted; ✗ invent a config syntax |
| UTF-8, ✗ BOM | Always |

### File Layout

| File | Purpose | Committed |
|---|---|---|
| `config/defaults.*` | Base config with all defaults | Yes |
| `config/config.*` | Primary project config (non-secret) | Yes |
| `config/<env>.*` | Environment overlay | Yes (✗ secrets) |
| `.env` · `.env.test` | Local dev/test vars + secrets | No (gitignored) |
| `.env.example` | Template: all keys, placeholder values | Yes |

Placement + naming conventions → [directory](../directory/STANDARDS.md). Split a config file exceeding ~200 keys by concern; overlays merge alphabetically within a cascade level.

---

## 9. Startup Validation

Config is validated at startup, before any business logic runs. Invalid config → the process exits. See [architecture](../architecture/STANDARDS.md) for fail-fast.

| Rule | Detail |
|---|---|
| Validate after resolution, before use | Immediately after the cascade merges, before the first request |
| Fail fast | Invalid config → non-zero exit + descriptive error. ✗ start in a broken state |
| ✗ validate at first use | A config error must surface at boot, ✗ mid-request in production |
| Collect all errors | ✗ stop at the first bad field — report every failure together |
| Schema-driven | Validation derives from the schema (§3), ✗ ad-hoc checks scattered in code |
| Type · range · enum | Value must parse to its type, sit within range, and be a declared enum member |
| Required-field check | Every required (defaultless) key present in some source |
| Path / URL check | Path-typed keys checked for existence/access; URL-typed checked for format |
| Cross-field check | Dependent fields validated together: `tls_enabled=true` requires `tls_cert_path` |

### Validation Error Content

Every error carries: **key** (full path) · **value** (masked if secret) · **constraint** (what was expected) · **source** (which cascade layer supplied it) · **message** (one line).

---

## 10. Dynamic Configuration

Most config is static — resolved at startup, frozen. A minority reloads at runtime without a restart.

| Category | Static (restart) | Dynamic (reload) |
|---|---|---|
| Network | Bind address, port, TLS certs | — |
| Database | Connection string, pool size | Query timeout |
| Logging | Destination, format | Log level |
| Features | Core toggles with code-path changes | Simple on/off flags |
| Performance | Worker pool, buffer sizes | Throttle thresholds |

### Reload Rules

| Rule | Detail |
|---|---|
| Explicit declaration | Each field is `static` or `dynamic` in the schema; default `static` |
| Atomic swap | Reload replaces the whole config snapshot atomically — ✗ partial updates |
| Re-validate on reload | A reload runs full validation (§9) before applying |
| Rollback on invalid | Failed validation → keep the previous config, log, alert |
| Signal-triggered | SIGHUP · API call · file-watch — ✗ a polling timer |
| Audit | Every dynamic change logged: old value · new value · timestamp · trigger |
| ✗ dynamic secrets | Secret rotation is handled by the secret manager, ✗ config reload — see [security](../security/STANDARDS.md) |

---

## 11. Config Documentation

Config documents itself; users discover it from the config, ✗ from external docs that drift.

| Rule | Detail |
|---|---|
| Schema is the doc | The typed schema (§3) is the primary reference |
| `.env.example` is the quick-start | Every key, placeholder values, one-line comments |
| Generated reference | CI generates a config reference from the schema — single source of truth |
| ✗ separate hand-maintained config docs | They drift from the schema |
| Config changes documented on release | Breaking config changes carry a migration path in release notes — changelog format → [git](../git/STANDARDS.md) |

Per-key doc entry: key path · type · default · env var · constraints · secret · dynamic · since-version · one-line description.

| Change type | Required action |
|---|---|
| New optional key (has default) | Note in changelog; update `.env.example` |
| New required key (no default) | Major version bump; migration guide; update `.env.example` |
| Key renamed | Deprecation warning; accept both for one release cycle |
| Key removed | Major version bump; migration guide |
| Default changed | Note in changelog with rationale |

---

## 12. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Secrets in a config file | Leaks to the repo and to logs | Reference + runtime injection (§4) |
| `if env == "production"` in code | Environments diverge invisibly; staging lies | Config values or feature flags (§5) |
| Validate on first use | Bad config surfaces mid-request in prod | Fail fast at startup (§9) |
| Config as a bag of strings | Type errors reach business logic | Typed schema + resolution (§3) |
| Re-reading env vars in core logic | Config becomes unpredictable and untestable | Resolve once at the edge, freeze (§2) |
| Flag with no owner or removal date | Flag debt accretes forever | Owner + mandatory removal date (§6) |
| Production values as defaults | A misconfig silently hits production | Dev-friendly, secure defaults (§7) |
| SQLite in dev, Postgres in prod | Bugs that only appear in production | Backing-service parity (§5) |
| Kill switch depending on its subsystem | The switch is dead exactly when needed | Evaluate the switch before the subsystem (§6) |

---

## 13. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Cascade sources | Defaults only | File + defaults | Full cascade (4 sources) |
| Schema | Informal | Typed struct + defaults | Full schema + constraints |
| Validation | None | Types at load | Types · ranges · enums · cross-field · paths |
| Environments | Local only | Dev + production | Dev · test · staging · production |
| Secret sourcing | `.env` | `.env` + gitignore enforced | Secret manager + runtime injection |
| Feature flags | ✗ | Boolean flags in config | Flag service + lifecycle + removal-date tracking |
| Dynamic config | ✗ | ✗ | Signal-based reload for declared fields |
| Config docs | Comments | `.env.example` | Generated reference + change log |
| Config files | Inline defaults | Single file | Split by concern + environment overlays |

Transition triggers: second contributor joins → add a file layer + `.env.example` · external users depend on it → full cascade, real secret manager, validation gate in CI · rollouts needed → adopt a flag service with lifecycle tracking.

---

## 14. Checklist

- [ ] Config schema is typed; resolution emits a typed object, not a string map
- [ ] Every field declares type, default, env-var mapping, secret flag, and description
- [ ] Cascade order is defaults → file → env → flags, merge not replace
- [ ] Config resolved once at the edge, then frozen and passed inward
- [ ] Core logic never reads environment variables directly
- [ ] Startup log records the source of each value, secrets masked
- [ ] No secret appears in any config file or anywhere in the repo
- [ ] Secrets are injected at runtime and held by reference, never embedded
- [ ] Secret-flagged fields masked in logs, errors, and config dumps
- [ ] `.env` is gitignored; `.env.example` is committed with placeholders only
- [ ] Production sources secrets from a secret manager, not `.env`
- [ ] Validation runs at startup; the process exits on invalid config
- [ ] All validation errors are collected and reported together
- [ ] Every key has a default; zero-config startup works for the default case
- [ ] No production values used as defaults
- [ ] Staging mirrors production structure; no `if env ==` conditionals in code
- [ ] Backing-service types match across environments
- [ ] Every feature flag has an owner and a mandatory removal date
- [ ] New flags default OFF; flags are evaluated once at the edge as a boolean
- [ ] Kill switches evaluate independently of the subsystem they disable
- [ ] Stale/expired flags are detected by lint/CI and removed within one release cycle
- [ ] Dynamic fields declared in the schema; reload re-validates and rolls back on failure
- [ ] Config reference generated from the schema; breaking changes carry a migration path
