# API Standards

> Rules for designing, versioning, and operating network APIs across protocols.

**ID** `api` · **Tier** Interface · **Version** 1.0
**Owns** HTTP semantics + status codes · resource naming · request/response contract · versioning + deprecation protocol · problem-details errors · cursor + envelope pagination contract · rate limiting · idempotency keys · wire serialization · OpenAPI/Protobuf contract artifact
**Defers to** authn/authz model + token lifetimes + secrets → [security](../security/STANDARDS.md) · pagination query mechanics + N+1 → [database](../database/STANDARDS.md) · semver + changelog → [git](../git/STANDARDS.md) · caching strategy → [performance](../performance/STANDARDS.md) · coverage + pyramid → [testing](../testing/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md) · alert thresholds → [observability](../observability/STANDARDS.md) · error taxonomy → [error_handling](../error_handling/STANDARDS.md) · i18n/l10n → [web](../web/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [security](../security/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [database](../database/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Protocol Selection](#2-protocol-selection)
3. [REST Conventions](#3-rest-conventions)
4. [Request & Response Contract](#4-request--response-contract)
5. [Versioning & Deprecation](#5-versioning--deprecation)
6. [Error Responses](#6-error-responses)
7. [Pagination Contract](#7-pagination-contract)
8. [Filtering & Sorting](#8-filtering--sorting)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [Rate Limiting](#10-rate-limiting)
11. [Serialization](#11-serialization)
12. [Idempotency](#12-idempotency)
13. [Contract Artifact & Documentation](#13-contract-artifact--documentation)
14. [Anti-Patterns](#14-anti-patterns)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

| # | Principle | Rule |
|---|---|---|
| 1 | Contract-first | Schema defined before implementation. Schema = source of truth |
| 2 | Consumer-driven | API shape serves consumers, ✗ internal data models |
| 3 | Backward compatible | Additive change never breaks existing client |
| 4 | Minimal surface | Expose what consumers need. Internal state stays internal |
| 5 | Consistent naming | Same concept → same name on every endpoint |
| 6 | Predictable | Same input → same output. ✗ hidden state change |
| 7 | Self-describing | Response carries context to act without docs lookup |
| 8 | Evolvable | Versioning · deprecation · extension without rewrite |
| 9 | Transport-independent | Business logic decoupled from protocol — swap REST ↔ gRPC without core change |
| 10 | Secure by default | Auth required on every endpoint; public endpoints opt out explicitly |

API layer = Tier 3 Interface. Parse → delegate → format. ✗ domain logic in handlers. See [architecture §2](../architecture/STANDARDS.md).

---

## 2. Protocol Selection

Choose by communication pattern, ✗ preference.

| Protocol | Best for | Latency | Streaming | Browser | Schema |
|---|---|---|---|---|---|
| REST/HTTP | CRUD · public APIs · wide compatibility | Medium | SSE only | Native | OpenAPI |
| gRPC | Service-to-service · high throughput · typed | Low | Bidirectional | Via proxy (gRPC-Web) | Protobuf |
| GraphQL | Consumer-driven queries · aggregation | Medium | Subscriptions | Native | SDL |
| WebSocket | Real-time bidirectional · persistent | Low | Full-duplex | Native | Custom |
| Server-Sent Events | Server-push · live feeds | Low | Server→client | Native | None |

| Factor | Pick |
|---|---|
| Public API consumers | REST ; GraphQL when clients drive query shape |
| Internal service mesh · strong typing mandatory | gRPC |
| Real-time server→client only | SSE — ✗ WebSocket for one-way push |
| File upload/download | REST ; gRPC streaming internally |

Multi-protocol systems share one service layer. Protocol adapters translate wire ↔ service call. ✗ duplicate business logic per protocol.

---

## 3. REST Conventions

### Resource Naming

| Rule | Correct | ✗ Incorrect |
|---|---|---|
| Plural nouns for collections | `/users` | `/user` · `/getUsers` |
| Identifier in path | `/users/{id}` | `/users/get/{id}` |
| Lowercase, hyphen-separated | `/user-profiles` | `/userProfiles` · `/user_profiles` |
| ✗ verbs in URLs | `POST /orders/{id}/cancel` | `/cancelOrder/{id}` |
| Nesting ≤ 2 levels | `/users/{id}/orders` | `/users/{id}/orders/{oid}/items/{iid}` |
| Action as sub-resource | `POST /orders/{id}/cancel` | `/orders/{id}?action=cancel` |
| ✗ in path | — | session IDs · auth tokens · PII |

### HTTP Methods

| Method | Semantics | Safe | Idempotent | Body | Success |
|---|---|---|---|---|---|
| GET | Read | Yes | Yes | ✗ | 200 |
| HEAD | Read metadata | Yes | Yes | ✗ | 200 |
| OPTIONS | Describe allowed methods | Yes | Yes | ✗ | 204 |
| POST | Create · trigger action | No | No | Yes | 201 (create · `Location` header) · 200 (action) · 202 (async) |
| PUT | Full replace | No | Yes | Yes | 200 · 204 |
| PATCH | Partial update | No | No ! | Yes | 200 |
| DELETE | Remove | No | Yes | ✗ | 204 |

! PATCH is idempotent only with absolute operations (set field = X); relative operations (increment by Y) are not.

### Status Code Selection

| Scenario | Status |
|---|---|
| Malformed syntax · unparseable body | 400 Bad Request |
| Valid syntax, invalid semantics (field out of range) | 422 Unprocessable Content |
| Missing · expired · invalid credentials | 401 Unauthorized |
| Identity known, permission insufficient | 403 Forbidden |
| Resource does not exist | 404 Not Found |
| Method not allowed on resource | 405 Method Not Allowed (+ `Allow` header) |
| State conflict — duplicate, wrong state, version mismatch | 409 Conflict |
| Removed after sunset date | 410 Gone |
| Precondition (`If-Match`) failed | 412 Precondition Failed |
| Body exceeds size limit | 413 Content Too Large |
| Unsupported `Content-Type` | 415 Unsupported Media Type |
| Cannot satisfy `Accept` | 406 Not Acceptable |
| Rate limit exceeded | 429 Too Many Requests (+ `Retry-After`) |
| Unexpected server failure | 500 Internal Server Error |
| Downstream dependency failed | 502 Bad Gateway |
| Overloaded · maintenance · shedding load | 503 Service Unavailable (+ `Retry-After`) |
| Downstream timed out | 504 Gateway Timeout |

Conditional requests: `ETag` + `If-None-Match` → 304 Not Modified on read · `If-Match` → 412 on stale write. Every mutable resource emits `ETag`.

---

## 4. Request & Response Contract

### Schema Rules

| Rule | Detail |
|---|---|
| Schema-first | OpenAPI · Protobuf · SDL written before code |
| Explicit types | Every field: type · format · constraints |
| Required vs optional | Marked explicitly. ✗ implicit optionality |
| Unknown request fields | Reject (strict) \| ignore (permissive) — pick one per API, enforce everywhere |
| Stable field names | Rename = breaking change → add new field, deprecate old |
| Body size limit | Enforced per route. Exceed → 413 |

### Request

| Aspect | Rule |
|---|---|
| `Content-Type` | Required on every request with body. Unsupported → 415 |
| `Accept` | Client declares expected format. Default `application/json` |
| Body shape | Flat preferred; nest only for genuine sub-objects |
| Validation | At API boundary, before service call. ✗ raw input into business logic. See [security](../security/STANDARDS.md) |

### Response Envelope

Two valid shapes — pick one per API, enforce across every endpoint. ✗ mix.

| Shape | Structure | Use |
|---|---|---|
| Flat | Resource \| array as top-level body; metadata in headers | Simple APIs |
| Envelope | `data` (payload) · `meta` (pagination · timing · request ID) · `error` (§6) | Metadata-carrying APIs |

| Rule | Detail |
|---|---|
| Empty collection → `[]` | ✗ `null` · ✗ omitted field · ✗ 404 |
| 201 returns created resource | Body = full object · `Location` header = canonical URL |
| Request ID on every response | Header `X-Request-Id` (echo client-supplied value if present) |
| `Cache-Control` explicit | Set on every response. ✗ rely on client defaults. Strategy → [performance](../performance/STANDARDS.md) |

---

## 5. Versioning & Deprecation

Semver of the release artifact → [git](../git/STANDARDS.md). This section covers the wire-contract version only.

| Strategy | Use | Trade-off |
|---|---|---|
| URL path `/v1/` | **Default** — public APIs | URL changes on major bump |
| Header `Accept: application/vnd.acme.v1+json` | Internal service-to-service | Less discoverable · harder to curl |
| Query param `?version=1` | Transitional migrations only | Easy to omit → ambiguous default |

Version the major only. Additive changes ship without a version bump.

### Breaking vs Non-Breaking

| Breaking → new major | Non-breaking → ship freely |
|---|---|
| Remove \| rename field · endpoint · URL path | Add endpoint · optional response field |
| Change field type · default value · default sort | Add optional query param · optional request field |
| Tighten validation · make optional field required | Relax validation |
| Change error structure | Add error code within existing structure |
| Remove enum value | Add enum value ; clients that reject unknown enums |

### Deprecation Protocol

Ordered — ✗ skip a step:

1. Emit `Deprecation: <http-date>` header on every response from the deprecated endpoint.
2. Emit `Sunset: <http-date>` header with the removal date.
3. Emit `Link: <doc-url>; rel="deprecation"` pointing at the migration guide.
4. Log every call to the deprecated endpoint with caller identity → notify remaining consumers.
5. Hold for the deprecation window: ≥ 6 months public · ≥ 1 month internal.
6. After the sunset date → 410 Gone. ✗ silent removal · ✗ 404.

Deprecated phase: bug fixes only. ✗ new features on a deprecated version.

---

## 6. Error Responses

Wire format for errors. Domain error taxonomy → [error_handling](../error_handling/STANDARDS.md).

### Problem Details (RFC 9457)

`Content-Type: application/problem+json` on every 4xx/5xx body.

| Member | Required | Purpose |
|---|---|---|
| `type` | Yes | URI identifying the error class. Stable — part of the contract |
| `title` | Yes | Short human-readable summary. Same for every occurrence of `type` |
| `status` | Yes | HTTP status code, duplicated in body |
| `detail` | Yes | Human-readable explanation of this occurrence |
| `instance` | Yes | URI of the failing request/occurrence |
| `code` | Extension | Machine-readable stable code — `DOMAIN_ACTION`, e.g. `ORDER_NOT_FOUND` |
| `request_id` | Extension | Trace correlation ID |
| `errors` | Extension | Array of field-level failures — `field` · `code` · `detail` |

### Rules

| Rule | Detail |
|---|---|
| Return all validation failures at once | ✗ fail on first error — populate `errors` array fully |
| Codes are contract | ✗ change `type` \| `code` after release. Clients switch on codes, ✗ on messages |
| ✗ expose stack traces | Production never leaks internals |
| ✗ expose storage internals | No table names · column names · query fragments · file paths |
| Same shape on 4xx and 5xx | One error format across the whole API |
| Log full context server-side | Bind to `request_id` for correlation |
| Localized `detail` | Negotiated via `Accept-Language` → [web](../web/STANDARDS.md). `type` + `code` always English |

Code patterns by status: 400 `INVALID_REQUEST` · 401 `AUTH_*` · 403 `FORBIDDEN_*` · 404 `*_NOT_FOUND` · 409 `CONFLICT_*` · 422 `VALIDATION_*` · 429 `RATE_LIMITED` · 500 `INTERNAL_ERROR` · 503 `SERVICE_UNAVAILABLE`.

---

## 7. Pagination Contract

Query-layer mechanics (keyset vs OFFSET · index requirements · N+1) → [database §7](../database/STANDARDS.md). This section defines only what the client sees.

| Rule | Detail |
|---|---|
| Cursor-based by default | Every list endpoint. Offset exposed only where [database](../database/STANDARDS.md) permits it |
| Cursors are opaque | Base64 blob. Client treats as black box — ✗ parse · ✗ construct · ✗ increment |
| Stable ordering | Ordering key must be unique + stable, else pages repeat or skip rows |
| Pagination on every collection endpoint | ✗ unbounded list response |
| Default page size | Server-defined (20). Client overrides via `limit` |
| Max page size | Hard server cap (100). Request above cap → clamp to cap ; ✗ 400 |
| Cursor expiry | Documented lifetime. Expired · malformed cursor → 400 |

Response fields:

| Field | Type | Meaning |
|---|---|---|
| `data` | array | Current page |
| `meta.next_cursor` | string \| null | Cursor for next page. `null` = last page |
| `meta.has_more` | boolean | More results exist beyond this page |
| `meta.total_count` | integer \| null | Optional — expensive on large sets. `null` when not computed |

Empty result → `data: []` · `has_more: false` · 200. ✗ 404.

---

## 8. Filtering & Sorting

| Feature | Format | Example |
|---|---|---|
| Equality filter | `?field=value` | `?status=active` |
| Multi-value (OR) | `?field=v1,v2` | `?status=active,pending` |
| Range | `?field_gte=` · `?field_lte=` | `?created_at_gte=2026-01-01` |
| Sort | `?sort=field` asc · `?sort=-field` desc | `?sort=-created_at` |
| Multi-sort | comma-separated, precedence left→right | `?sort=-created_at,name` |
| Sparse fields | `?fields=id,name` | Server may still include IDs + type |
| Free-text search | `?q=term` | `?q=widget` |

| Suffix | Meaning |
|---|---|
| `_ne` | Not equals |
| `_gt` · `_gte` | Greater than · greater or equal |
| `_lt` · `_lte` | Less than · less or equal |
| `_in` | In set |
| `_like` | Pattern match |
| `_is_null` | Null check |

| Rule | Detail |
|---|---|
| Allowlist filterable + sortable fields | ✗ arbitrary field filtering — injection + full-scan risk |
| Unknown filter param → 400 | ✗ silently ignore |
| Validate filter values against field schema | Type mismatch → 422 |
| Documented default sort | Every list endpoint has one. Unsupported sort field → 400 |
| Every filterable field is indexed | Else the filter is a table scan → [database §5](../database/STANDARDS.md) |

---

## 9. Authentication & Authorization

Cross-reference: [security](../security/STANDARDS.md) owns the authn/authz model — RBAC/ABAC, default-deny, token lifetimes, token classes, secret rotation. This section covers API-specific patterns only. ✗ restate a lifetime number here.

### Credential Placement

| Method | Where | When |
|---|---|---|
| Bearer token | `Authorization: Bearer <token>` | Default for all APIs |
| API key | `X-API-Key` header | Service-to-service · third-party integration |
| mTLS client cert | TLS layer | Zero-trust service mesh |
| Cookie | `Cookie` header | Browser sessions only → [web](../web/STANDARDS.md) |
| Query param `?api_key=` | — | ✗ Forbidden — leaks via logs · `Referer` · proxy cache · browser history |

### API Auth Rules

| Rule | Detail |
|---|---|
| Auth on every endpoint | Default deny. Public endpoints marked explicitly in the schema |
| 401 vs 403 | 401 = identity unknown/invalid. 403 = identity known, permission insufficient |
| Scope check before execution | Token carries scopes; endpoint declares required scope in OpenAPI |
| ✗ auth material in URL | Path or query string → leaked |
| ✗ custom crypto | OAuth 2.0 · OIDC · JWT (RS256/ES256) only |
| Key format + storage | `prefix_env_random` (`sk_prod_…`) — type identifiable at sight · hashed at rest, ✗ plaintext |
| Key scope + rotation | One key per client/integration, ✗ shared keys · overlapping validity window → rotate without downtime · instant revocation without redeploy |
| Rate limit per key | Each key gets independent limits (§10) |

---

## 10. Rate Limiting

`api` owns rate limiting. Other standards cross-reference this section.

| Aspect | Rule |
|---|---|
| Scope | Per-principal (API key · token · account). ✗ per-IP alone — NAT collapses distinct clients |
| Algorithm | Token bucket \| sliding window. ✗ fixed window — burst edge at boundary doubles effective rate |
| Burst | Token bucket refill allows short bursts above sustained rate |
| Granularity | Separate budgets per endpoint tier — read · write · search · admin |
| Enforcement point | Edge/gateway, before authentication cost is paid where possible |
| Multi-instance | Shared counter store. ✗ per-instance counters — N instances = N× the limit |

### Response Headers

Emitted on **every** response, not only on 429.

| Header | Content |
|---|---|
| `RateLimit-Limit` | Quota for the current window |
| `RateLimit-Remaining` | Requests left in the current window |
| `RateLimit-Reset` | Seconds until the window resets |
| `RateLimit-Policy` | Declared policy, e.g. `100;w=60` |
| `Retry-After` | Required on 429 and 503. Seconds \| HTTP-date |

`X-RateLimit-*` accepted as a legacy alias only. New APIs emit `RateLimit-*`.

### Tiers

| Tier | Applies to | Relative limit |
|---|---|---|
| Read | GET · HEAD | Highest |
| Write | POST · PUT · PATCH · DELETE | ~10× lower than read |
| Search | Full-text · complex aggregation | Lowest |
| Admin | Management endpoints | Separate, configurable |

### Client Obligations

| Rule | Detail |
|---|---|
| Honour `Retry-After` | Wait at least the stated duration. ✗ retry sooner |
| Exponential backoff | `base × 2^attempt` on repeated 429/503 |
| Jitter | Add random offset `0…base` — prevents thundering herd |
| Max retries | Capped (5). Fail after exhaustion — ✗ retry forever |
| Circuit breaker | Open after sustained failures → [architecture](../architecture/STANDARDS.md) |
| ✗ retry 4xx other than 429 | 4xx (; 429) is a client bug — retrying repeats it |

---

## 11. Serialization

| Aspect | Rule |
|---|---|
| Content type | `application/json; charset=utf-8` |
| Field naming | `camelCase` \| `snake_case` — one choice, enforced across the entire API · booleans prefixed `is_` · `has_` · `can_` |
| Enum values | `UPPER_SNAKE_CASE` strings. ✗ numeric enums — fragile across versions |
| Absent vs null vs empty | Absent = default applies · `null` = explicitly cleared · `""` = explicitly blank. ✗ treat as identical |
| Collections | `[]` for empty. ✗ `null` |
| Response nulls | Include the field with `null`. ✗ omit — client cannot distinguish absent from cleared |
| PATCH semantics | Absent = no change. `null` = clear value |

| Data | Rule |
|---|---|
| Timestamp | ISO 8601 UTC: `2026-01-15T09:30:00Z`. Client converts for display |
| Date only | ISO 8601 date: `2026-01-15` |
| Duration | ISO 8601 (`P1DT2H30M`) \| integer with unit in the field name (`timeout_seconds`) |
| Money | Integer minor units \| decimal string + explicit `currency` (ISO 4217). ✗ floating point |
| Large integers | String above 2^53 — JavaScript loses precision |
| Units | Encoded in the field name: `weight_kg` · `duration_seconds`. ✗ bare `size` · `length` |
| Binary | Base64 in JSON \| separate binary endpoint. ✗ raw bytes in a JSON string |

---

## 12. Idempotency

| Method | Safe | Idempotent | Retry without a key? |
|---|---|---|---|
| GET · HEAD · OPTIONS | Yes | Yes | Yes |
| PUT | No | Yes | Yes — same body |
| DELETE | No | Yes | Yes — deleting an absent resource → 204 \| 404, pick one and be consistent |
| PATCH | No | Only with absolute ops | Only with absolute ops |
| POST | No | No | ✗ — duplicates the resource |

### Idempotency-Key Protocol

Required on every unsafe non-idempotent operation (POST, relative PATCH) that creates state or moves money.

| Aspect | Rule |
|---|---|
| Header | `Idempotency-Key: <client-generated UUID>` |
| First request | Execute → store `(key, request fingerprint, response)` |
| Duplicate key + same body | Return the stored response. ✗ re-execute |
| Duplicate key + different body | 422 Unprocessable Content — the key is bound to its payload |
| In-flight duplicate | 409 Conflict — original still executing |
| Key lifetime | Documented retention window (24 h). After expiry → re-executes; client must tolerate |
| Storage | Same transaction as the effect, else a crash between them breaks the guarantee |

Timeout · network error with no response = unknown outcome → retry with the **same** key. Server deduplicates.

---

## 13. Contract Artifact & Documentation

| Rule | Detail |
|---|---|
| Schema is the contract | OpenAPI 3.1+ (3.2.0 current, Sept 2025) for REST · Protobuf (gRPC) · SDL (GraphQL) |
| Committed to version control | Schema change reviewed like code |
| Docs generated from schema | ✗ hand-written docs that drift from the contract |
| Drift check in CI | Implementation validated against schema. Drift → build failure |
| Breaking-change gate in CI | Schema diffed against the previous release; breaking change without a major bump → build failure |
| Consumer-driven contract tests | Each consumer publishes its expectations; provider build verifies them before deploy. Coverage rules → [testing](../testing/STANDARDS.md) |

Per endpoint the schema declares: summary · method + path · required scopes · request schema · response schema per status code · every error `type`/`code` returned · rate-limit tier · deprecation status + sunset date.

---

## 14. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| 200 with `"success": false` | Breaks every HTTP intermediary, retry policy, and monitor | Correct 4xx/5xx status |
| Chatty endpoints forcing N calls | Client round-trip amplification | Batch endpoint \| expansion param |
| Leaking DB rows as the API model | Schema change = breaking API change | Explicit response DTO |
| Unbounded list endpoints | One client OOMs the server | Mandatory pagination (§7) |
| Versioning every minor change | Version sprawl; nobody migrates | Major only; additive changes ship unversioned |
| Custom error shape per endpoint | Clients cannot write one handler | RFC 9457 everywhere (§6) |
| Silent endpoint removal | Consumers break in production | Deprecation protocol (§5) |
| Retrying POST without a key | Duplicate orders · double charges | `Idempotency-Key` (§12) |

---

## 15. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Protocol | REST only | REST + one more if justified | Multi-protocol, shared service layer |
| Versioning | None | URL path `/v1/` | `/v1/` + full deprecation protocol (§5) |
| Error format | Status + message string | RFC 9457 problem details | RFC 9457 + field-level `errors` array |
| Auth | API key | Bearer token + scopes | OAuth 2.0 / OIDC + scopes + key rotation |
| Rate limiting | None | Per-key, single limit | Per-tier + shared counter store + backpressure |
| Pagination | Offset (< 10K rows) | Cursor | Cursor + optional `total_count` |
| Idempotency | PUT/DELETE natural | `Idempotency-Key` on money/state POSTs | Full protocol on every mutation |
| Contract + docs | Informal · README | OpenAPI committed · docs generated from schema | OpenAPI + CI drift gate + consumer contract tests + deprecation notices |

---

## 16. Checklist

- [ ] Protocol chosen from §2 by communication pattern, rationale documented
- [ ] Schema (OpenAPI · Protobuf · SDL) committed before implementation
- [ ] Resource paths: plural nouns · lowercase-hyphenated · ≤ 2 nesting levels
- [ ] HTTP method matches semantics; success status matches §3
- [ ] Every error scenario maps to the §3 status code — no 200-with-error bodies
- [ ] `ETag` emitted on mutable resources; `If-Match` honoured on writes
- [ ] Request body size limit enforced per route → 413 on exceed
- [ ] One response envelope shape across the entire API; empty collections return `[]` with 200
- [ ] `X-Request-Id` present on every response
- [ ] Breaking changes gated in CI against the previous schema version
- [ ] Deprecated endpoints emit `Deprecation` + `Sunset` headers; 410 after sunset
- [ ] Errors use RFC 9457 `application/problem+json` with stable `type` + `code`
- [ ] Validation returns all field failures at once, not just the first
- [ ] No stack traces, table names, or query fragments in any error body
- [ ] Every collection endpoint paginates; cursors opaque; max page size capped
- [ ] Filterable + sortable fields allowlisted and indexed
- [ ] Auth required by default; public endpoints marked explicitly in the schema
- [ ] No credential ever appears in a URL path or query string
- [ ] `RateLimit-Limit` · `RateLimit-Remaining` · `RateLimit-Reset` on every response; 429 carries `Retry-After`
- [ ] Rate-limit counters shared across instances
- [ ] Timestamps ISO 8601 UTC; money never floating point
- [ ] `Idempotency-Key` accepted on state-creating POSTs; duplicate key + different body → 422
- [ ] Consumer-driven contract tests pass in the provider build; generated docs match the deployed schema
