# Configuration Standards

Rules for how projects load, validate, store, and manage configuration.
Covers cascade order, schema, environments, secrets, feature flags,
defaults, file formats, validation, dynamic reloading, and documentation.

Extends: `architecture/STANDARDS.md §8` — Configuration Architecture.
Composable with: Security Standards, Directory Standards, DevOps Standards.

---

## Table of Contents

1. [Configuration Cascade](#1-configuration-cascade)
2. [Configuration Schema](#2-configuration-schema)
3. [Environment Management](#3-environment-management)
4. [Secret Management](#4-secret-management)
5. [Feature Flags](#5-feature-flags)
6. [Default Values](#6-default-values)
7. [Config File Formats](#7-config-file-formats)
8. [Validation](#8-validation)
9. [Dynamic Configuration](#9-dynamic-configuration)
10. [Config Documentation](#10-config-documentation)
11. [Config Organization](#11-config-organization)
12. [Scale Matrix](#12-scale-matrix)
13. [Configuration Checklist](#13-configuration-checklist)

---

## 1. Configuration Cascade

Priority order from `architecture/STANDARDS.md §8` — highest wins.

| Priority | Source | Mutability | Typical Use |
|---|---|---|---|
| 1 (highest) | Runtime arguments (CLI flags, function params) | Per-invocation | Overrides, debugging, one-off runs |
| 2 | Environment variables | Per-process | Deployment-specific values, secrets |
| 3 | Configuration file(s) | Per-deploy | Stable project-wide settings |
| 4 (lowest) | Code defaults | Per-release | Sensible fallback for every key |

### Cascade Rules

| Rule | Detail |
|---|---|
| Merge, don't replace | Higher-priority source overrides only keys it sets; unset keys fall through to lower sources |
| Single resolution point | Config resolved once at startup in Tier 3, result passed inward as typed struct |
| ✗ re-resolve mid-flight | Core logic (Tiers 0–2) never re-reads config sources; receives resolved config as argument |
| Traceability | Resolved config logs which source provided each value (without exposing secrets) |
| ✗ env var in Tier 0–1 | Environment variable reads happen exclusively in Tier 3 |
| Override transparency | Runtime args override env vars override file values override defaults — no exceptions |

### Resolution Algorithm

1. Load code defaults (Tier 0 schema provides these).
2. Load config file(s), overlay onto defaults.
3. Read environment variables, overlay matching keys.
4. Apply runtime arguments, overlay matching keys.
5. Validate merged result against schema (§8).
6. Freeze config — immutable from this point forward.

---

## 2. Configuration Schema

Configuration shape defined in Tier 0. See `architecture/STANDARDS.md §2` — Tier 0 contains types, constants, configuration schema.

### Schema Rules

| Rule | Detail |
|---|---|
| Typed definition | Every config key has explicit type (string, int, bool, duration, path, enum) |
| Tier 0 placement | Schema struct/type lives in Tier 0 — no I/O, no defaults from external sources |
| Defaults in schema | Every field carries its default value in the type definition |
| Flat over nested | Prefer flat config with dotted keys over deep nesting; max 2 levels deep |
| Grouped by concern | Related keys grouped into sub-structs (database, server, logging, auth) |
| ✗ stringly typed | ✗ pass port as string; ✗ pass duration as raw int; use semantic types |
| Enum constraints | Fields with fixed valid values use enum types, not free-form strings |
| Required vs optional | Mark explicitly — required fields have no default; optional fields always have default |

### Field Definition Contract

Every config field specifies:

| Attribute | Required | Purpose |
|---|---|---|
| Name | Yes | Dot-path key: `database.pool_size` |
| Type | Yes | Semantic type: `uint16`, `duration`, `path`, `enum[...]` |
| Default | Yes (optional fields) | Value when unset by all sources |
| Constraints | If applicable | Range, pattern, enum values, min/max |
| Env var mapping | Yes | Corresponding env var: `DATABASE_POOL_SIZE` |
| Secret | Yes | Boolean — controls logging/display behavior |
| Description | Yes | One-line purpose |

---

## 3. Environment Management

### Environment Tiers

| Environment | Purpose | Config Source | Secrets Source |
|---|---|---|---|
| Development (local) | Developer workstation | Local config file + defaults | `.env` file (✗ committed) |
| Test | Automated test execution | Test-specific config/overrides | Hardcoded test values or `.env.test` |
| Staging | Pre-production validation | Deployed config file | Secret manager (same as production) |
| Production | Live system | Deployed config file | Secret manager |

### Environment Rules

| Rule | Detail |
|---|---|
| Shared base | One base config contains settings common across all environments |
| Environment overlay | Per-environment file overrides only what differs |
| ✗ environment conditionals in code | ✗ `if env == "production"` in logic; config values differ, code path stays same |
| Environment parity | Staging mirrors production config structure exactly; only values differ |
| ✗ dev-only code paths | Features exist in all environments or none; feature flags control activation |
| Environment variable naming | `APP_` prefix + `SECTION_KEY` → `APP_DATABASE_HOST`, `APP_SERVER_PORT` |
| Environment detection | Single env var (`APP_ENV`) identifies current environment; everything else derived from config |

### What Differs vs What's Shared

| Differs per environment | Shared across environments |
|---|---|
| Host/port/URL values | Config key names and structure |
| Connection strings | Schema shape and types |
| Log level, log destination | Validation rules and constraints |
| Secret values | Default values for non-env-specific keys |
| Resource limits (pool size, timeouts) | Feature flag evaluation logic |
| TLS/SSL settings | Application business logic |

---

## 4. Secret Management

Extends `architecture/STANDARDS.md §8` — secrets never appear in committed files.
See also: `security/STANDARDS.md` for access control and threat model.

### Cardinal Rules

| Rule | Detail |
|---|---|
| ✗ secrets in source control | Never — no config files, no code, no comments, no test fixtures |
| ✗ secrets in logs | Resolved config logging masks secret-flagged fields |
| ✗ secrets past Tier 3 | Secrets enter at Tier 3; pass derived values (clients, connections) inward |
| ✗ secrets in error messages | Error context strips secret fields before reporting |
| ✗ hardcoded secrets | ✗ even for development — use `.env` or local secret store |
| ✗ secrets in CLI arguments | Visible in process list; use env vars or file references instead |

### Secret Sources (by environment)

| Environment | Acceptable Secret Source |
|---|---|
| Development | `.env` file (gitignored) · local secret manager |
| Test | Test-specific static values · `.env.test` (gitignored) |
| Staging / Production | Secret manager (Vault, AWS Secrets Manager, GCP Secret Manager, etc.) |

### Secret Lifecycle

| Phase | Rule |
|---|---|
| Creation | Generate with cryptographically secure random source; ✗ human-chosen secrets |
| Storage | Encrypted at rest in secret manager; ✗ plaintext storage anywhere |
| Access | Least privilege — each service accesses only its own secrets |
| Rotation | Every secret has rotation schedule; system handles rotation without downtime |
| Revocation | Compromised secrets revoked immediately; dependent systems refresh on next startup or reload |
| Audit | All secret access logged with timestamp, accessor identity, and purpose |

### Derived Values Pattern

Instead of passing raw secrets to core logic, Tier 3 constructs derived values:

| ✗ Pass inward | Pass inward instead |
|---|---|
| Database password | Authenticated database connection/pool |
| API key | Configured HTTP client with auth headers |
| Encryption key | Initialized cipher/encryption service |
| OAuth client secret | Authenticated OAuth client |

### .env File Rules

| Rule | Detail |
|---|---|
| `.env` in `.gitignore` | Always — every project, no exceptions |
| `.env.example` committed | Contains every key with placeholder values, no real secrets |
| One `.env` per purpose | `.env` (dev), `.env.test` (test) — ✗ `.env.production` |
| KEY=value format | No quotes unless value contains spaces; no inline comments |
| ✗ `.env` in production | Production uses secret manager, not `.env` files |

---

## 5. Feature Flags

### Lifecycle

Every flag progresses through defined stages:

| Stage | Duration | Description |
|---|---|---|
| Born | 0–1 sprint | Flag created, code path gated, default OFF |
| Active | 1–N sprints | Flag actively toggled per environment; gradual rollout |
| Permanent | Indefinite | Decision made — flag locked ON or OFF across all environments |
| Removed | 1 sprint | Flag, gated code paths, and evaluation logic deleted |

### Rules

| Rule | Detail |
|---|---|
| Named by feature, not by ticket | `enable_batch_export` ✗ `JIRA_1234_flag` |
| Boolean by default | Flag is ON or OFF; complex variants (A/B/multivariate) only when justified |
| Evaluated once per request/invocation | ✗ re-evaluate mid-operation — capture flag value at entry point |
| Default OFF for new flags | New feature gated behind flag defaults to disabled |
| Flag removal is mandatory | When feature is permanent, remove flag within one release cycle |
| ✗ nested flags | ✗ flag that depends on another flag's state — creates combinatorial explosion |
| Flag state in config | Feature flags stored in config file or dedicated flag service, not in code |

### Naming Convention

| Pattern | Example |
|---|---|
| `enable_<feature>` | `enable_batch_export` |
| `use_<new_implementation>` | `use_v2_parser` |
| `disable_<feature>` | ✗ avoid — double negatives when flag is OFF; use `enable_` instead |

### Evaluation Rules

| Rule | Detail |
|---|---|
| Resolve at Tier 3 | Flag evaluation happens at system edge, result passed inward as boolean |
| ✗ flag checks in Tier 0–1 | Core logic receives behavior via arguments, not flag references |
| Stale flag cleanup | Automated check (lint/CI) flags unreferenced feature flags for removal |
| Audit trail | Flag state changes logged with who, when, and why |

---

## 6. Default Values

### Core Principle

Every configuration key has a sensible default. Zero-configuration must work for the default use case. See `architecture/STANDARDS.md §8`.

### Default Rules

| Rule | Detail |
|---|---|
| Every key has a default | Required fields have defaults that work for local development |
| Secure defaults | Default values choose the more secure option (TLS on, strict validation, minimal permissions) |
| Conservative resource defaults | Default pool sizes, timeouts, buffer sizes are small but functional |
| Development-friendly | Defaults target local development — `localhost`, standard ports, local paths |
| ✗ production values as defaults | Production URLs, production credentials never appear as defaults |
| Documented | Every default value appears in schema and `.env.example` |
| Overridable | Every default can be overridden by higher-priority cascade source |

### Default Selection Guide

| Config Category | Default Strategy |
|---|---|
| Hostname / URL | `localhost` or `127.0.0.1` |
| Port | Standard port for service type (5432 for Postgres, 8080 for HTTP) |
| Timeout | 30 seconds for HTTP; 5 seconds for internal calls |
| Pool size | 5 connections (functional, not production-scaled) |
| Log level | `INFO` for production defaults; overridden to `DEBUG` in dev |
| Retry count | 3 attempts with exponential backoff |
| Batch size | Small enough for development datasets |
| Feature flags | OFF — new features disabled by default |
| TLS / SSL | ON — secure by default |
| File paths | Relative to project root or XDG-compliant paths |

---

## 7. Config File Formats

### Format Selection

| Format | Best For | Avoid When |
|---|---|---|
| TOML | Application config, human-edited files, typed values | Deep nesting > 2 levels |
| YAML | Infrastructure config, complex structures, multi-doc | Simple flat config (TOML simpler) |
| JSON | Machine-generated config, API responses, schemas | Human-edited files (no comments) |
| `.env` | Environment variable overrides, secrets in dev | Structured/nested configuration |
| INI | Legacy systems, minimal dependencies | New projects (use TOML instead) |

### Format Rules

| Rule | Detail |
|---|---|
| One format per project | Pick one primary config format; ✗ mix TOML and YAML for same purpose |
| Comments required | Config format must support comments — rules out JSON for primary config |
| No executable config | ✗ Python/JS/Lua files as config — config is data, not code |
| Standard parser only | Use well-maintained, standard-library or widely-adopted parser |
| ✗ custom config format | ✗ inventing config syntax; use established formats |
| Encoding | UTF-8 always; ✗ BOM |

### Filename Conventions

| Pattern | Usage |
|---|---|
| `config.toml` / `config.yaml` | Primary project config |
| `config.<env>.toml` | Environment-specific overlay |
| `.env` | Local environment variables (gitignored) |
| `.env.example` | Template with placeholder values (committed) |

---

## 8. Validation

Config validated at startup before any business logic executes. Invalid config → immediate failure with clear error. See `architecture/STANDARDS.md §7` — fail fast.

### Validation Rules

| Rule | Detail |
|---|---|
| Validate at load time | All config validated immediately after cascade resolution, before use |
| Fail fast | Invalid config → process exits with non-zero code and descriptive error |
| All errors reported | ✗ stop at first invalid field; collect all validation failures, report together |
| Schema-driven | Validation rules derived from schema (§2), not ad-hoc checks scattered in code |
| Type enforcement | Value must parse to declared type; `"abc"` for a `uint16` field → validation error |
| Range enforcement | Numeric values within declared min/max; `port: 99999` → validation error |
| Enum enforcement | Enum fields accept only declared values; unknown value → validation error |
| Required field check | Required fields (no default) must be present in at least one source |
| Path validation | Path-typed config validated for existence/accessibility at startup |
| URL validation | URL-typed config validated for format; optionally for reachability |
| Cross-field validation | Dependent fields validated together: `tls_enabled=true` requires `tls_cert_path` set |

### Validation Error Format

Every validation error contains:

| Field | Content |
|---|---|
| Key | Full config path: `database.pool_size` |
| Value | Provided value (masked if secret-flagged) |
| Constraint | What was expected: `integer in range [1, 100]` |
| Source | Which cascade source provided the invalid value |
| Message | Human-readable one-line explanation |

### Validation Timing

| Phase | What's Validated |
|---|---|
| Parse time | Syntax correctness of config file (TOML/YAML/JSON well-formed) |
| Load time | Type correctness, range constraints, required fields, enum values |
| Startup time | Cross-field dependencies, path existence, service reachability (optional) |
| ✗ Runtime | Config already frozen and validated; ✗ re-validating in business logic |

---

## 9. Dynamic Configuration

Most config is static (resolved at startup, frozen). Some values require runtime change without restart.

### Static vs Dynamic

| Category | Static (requires restart) | Dynamic (runtime reload) |
|---|---|---|
| Network | Bind address, port, TLS certs | — |
| Database | Connection string, pool size | Query timeout |
| Logging | Log destination, format | Log level |
| Features | Core feature toggles with code path changes | Feature flags (simple on/off) |
| Security | Auth provider, encryption keys | IP allowlists, rate limits |
| Performance | Worker pool size, buffer sizes | Throttle thresholds |

### Dynamic Config Rules

| Rule | Detail |
|---|---|
| Explicit dynamic declaration | Config schema marks each field as `static` or `dynamic`; default is `static` |
| Atomic swap | Dynamic config update replaces entire config snapshot atomically; ✗ partial updates |
| Re-validate on reload | Dynamic config change triggers full validation (§8) before applying |
| Rollback on invalid | If reloaded config fails validation, retain previous valid config and log error |
| Signal-based reload | Reload triggered by explicit signal (SIGHUP, API call, file watch); ✗ polling timer |
| Audit log | Every dynamic config change logged with old value, new value, timestamp, trigger source |
| ✗ dynamic secrets | Secret rotation handled by secret manager, not by config reload |

### Reload Contract

1. Receive reload signal.
2. Read config sources (cascade resolution, same as startup).
3. Validate merged result against schema.
4. If valid → atomically replace config snapshot; log change.
5. If invalid → retain current config; log validation errors; alert.

---

## 10. Config Documentation

Every config key is self-documenting. Users discover configuration from the config itself, not from external docs that drift.

### Documentation Rules

| Rule | Detail |
|---|---|
| Schema is the doc | Config schema (§2) serves as primary documentation source |
| `.env.example` is the quick-start | Contains every key, placeholder values, and one-line comments |
| Inline comments in config files | Config files include comments explaining non-obvious values |
| Generated reference | CI generates config reference doc from schema — single source of truth |
| ✗ separate config docs | ✗ maintaining config docs separate from schema; they will drift |
| Changelog for config | Breaking config changes documented in release notes with migration path |

### Per-Key Documentation

Each config key documentation includes:

| Attribute | Example |
|---|---|
| Key path | `database.pool_size` |
| Type | `uint16` |
| Default | `5` |
| Env var | `APP_DATABASE_POOL_SIZE` |
| Constraints | `range: [1, 200]` |
| Secret | `false` |
| Dynamic | `false` |
| Since | `v1.2.0` |
| Description | Maximum number of connections in database pool |

### Config Change Communication

| Change Type | Required Action |
|---|---|
| New optional key (with default) | Document in changelog; `.env.example` updated |
| New required key (no default) | Major version bump; migration guide; `.env.example` updated |
| Key renamed | Deprecation warning for old key; accept both for one release cycle |
| Key removed | Major version bump; migration guide |
| Default value changed | Document in changelog with rationale |
| Constraint changed | Document in changelog; validate existing deployments |

---

## 11. Config Organization

### File Structure

| File | Purpose | Committed |
|---|---|---|
| `config/schema.*` | Typed config schema definition (Tier 0) | Yes |
| `config/defaults.toml` | Base config with all defaults | Yes |
| `config/config.toml` | Primary project config (non-secret) | Yes |
| `config/<env>.toml` | Environment overlay (staging, production) | Yes (✗ secrets) |
| `.env` | Local dev environment variables + secrets | No (gitignored) |
| `.env.example` | Template with all keys and placeholders | Yes |
| `.env.test` | Test environment variables | No (gitignored) |

### Organization Rules

| Rule | Detail |
|---|---|
| Config directory | All config files in `config/` directory at project root; see `directory/STANDARDS.md` |
| Split by concern | Large configs split into logical files: `config/database.toml`, `config/server.toml` |
| ✗ config in source directories | Config files live in config directory, not alongside source code |
| Merge order for split files | Alphabetical by filename within same cascade level |
| Environment overlays | Named by environment: `config/production.toml` overlays `config/defaults.toml` |
| ✗ monolith config | Single config file > 200 keys → split by concern |

### Env Var Mapping Convention

Config keys map to env vars through consistent transformation:

| Config Key | Env Var |
|---|---|
| `database.host` | `APP_DATABASE_HOST` |
| `database.pool_size` | `APP_DATABASE_POOL_SIZE` |
| `server.bind_address` | `APP_SERVER_BIND_ADDRESS` |
| `logging.level` | `APP_LOGGING_LEVEL` |

Rule: `APP_` prefix + section + `_` + key, all uppercase, dots → underscores.

---

## 12. Scale Matrix

Configuration formality scales with project complexity. See `architecture/STANDARDS.md §12`.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Cascade sources | Code defaults only | File + defaults | Full cascade (4 sources) |
| Schema | Informal / none | Typed struct with defaults | Full schema with constraints + validation |
| Validation | None | Type checking at load | Full validation: types, ranges, cross-field, paths |
| Environments | Single (local) | Dev + production | Dev · test · staging · production |
| Secrets | `.env` file | `.env` + gitignore enforcement | Secret manager + rotation + audit |
| Feature flags | ✗ not needed | Boolean flags in config | Flag service with lifecycle tracking |
| Config docs | Comments in code | `.env.example` | Generated reference + changelog |
| Dynamic config | ✗ not needed | ✗ not needed | Signal-based reload for dynamic fields |
| Config files | Inline defaults | Single config file | Split by concern + environment overlays |
| Config testing | ✗ not needed | Validate in CI | Config validation in CI + deployment gates |

### Graduation Triggers

| From → To | When |
|---|---|
| PoC → Small | Project persists beyond initial experiment; second contributor joins |
| Small → Production | External users/systems depend on it; uptime matters; secrets are real |

---

## 13. Configuration Checklist

### New Project

- [ ] Config schema defined in Tier 0 with typed fields
- [ ] Every field has type, default, env var mapping, description
- [ ] Cascade order implemented: runtime args → env vars → file → defaults
- [ ] Config resolved once at startup in Tier 3, passed inward as immutable struct
- [ ] `.env.example` committed with all keys and placeholder values
- [ ] `.env` added to `.gitignore`
- [ ] Zero-config startup works for default use case
- [ ] Config validation runs at load time; process exits on invalid config
- [ ] All validation errors collected and reported together
- [ ] Resolved config logged at startup (secrets masked)

### Secret Management

- [ ] ✗ secrets in source control — verified by pre-commit hook or CI
- [ ] Secrets enter at Tier 3 only; derived values passed inward
- [ ] `.env` file gitignored; `.env.example` committed
- [ ] Production secrets stored in secret manager, not `.env`
- [ ] Secret fields marked in schema; masked in logs and error messages
- [ ] Rotation plan defined for every secret

### Feature Flags

- [ ] Flags named by feature (`enable_<feature>`)
- [ ] New flags default to OFF
- [ ] Flags evaluated at Tier 3, result passed inward as boolean
- [ ] Stale flag cleanup tracked (lint/CI check for unreferenced flags)
- [ ] Permanent flags removed within one release cycle of decision

### Environment Management

- [ ] Base config shared across all environments
- [ ] Per-environment overlays contain only differing values
- [ ] ✗ environment conditionals in application code
- [ ] Staging config structure mirrors production exactly
- [ ] Environment identified by single `APP_ENV` variable

### Production Readiness

- [ ] Full cascade implemented with all 4 sources
- [ ] Schema validation covers types, ranges, enums, cross-field rules
- [ ] Dynamic config fields declared; reload mechanism tested
- [ ] Config changes documented in changelog with migration path
- [ ] CI validates config schema and `.env.example` completeness
- [ ] Config reference generated from schema (single source of truth)
