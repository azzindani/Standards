# API & Communication Standards

Rules for designing, versioning, and operating APIs across protocols.
Language-agnostic — protocol-specific implementation details belong in
language-specific standards.

Composable with: architecture/STANDARDS.md, security/STANDARDS.md,
error_handling/STANDARDS.md, documentation/STANDARDS.md.

---

## Table of Contents

1. [API Design Principles](#1-api-design-principles)
2. [Protocol Selection](#2-protocol-selection)
3. [REST Conventions](#3-rest-conventions)
4. [Request/Response Contracts](#4-requestresponse-contracts)
5. [Versioning](#5-versioning)
6. [Error Responses](#6-error-responses)
7. [Pagination](#7-pagination)
8. [Filtering & Sorting](#8-filtering--sorting)
9. [Authentication & Authorization](#9-authentication--authorization)
10. [Rate Limiting](#10-rate-limiting)
11. [Serialization](#11-serialization)
12. [Idempotency](#12-idempotency)
13. [API Documentation](#13-api-documentation)
14. [Scale Matrix](#14-scale-matrix)
15. [API Checklist](#15-api-checklist)

---

## 1. API Design Principles

Every API decision traces to these principles.
See `architecture/STANDARDS.md §1` — principles #9 (contract-first),
#11 (universal format), #16 (idempotency).

| # | Principle | Rule |
|---|---|---|
| 1 | Contract-first | Define schema before implementation. Schema is source of truth. |
| 2 | Consumer-driven | API shape serves consumers, not internal data models. |
| 3 | Backward compatible | Existing clients never break from additive changes. |
| 4 | Minimal surface | Expose only what consumers need. Internal state stays internal. |
| 5 | Consistent naming | Same concept → same name across every endpoint. |
| 6 | Predictable behavior | Same input → same output. No hidden state changes. |
| 7 | Self-describing | Response carries enough context for client to act without docs lookup. |
| 8 | Evolvable | API supports versioning, deprecation, extension without rewrites. |
| 9 | Transport-independent | Business logic decoupled from protocol. Swap REST ↔ gRPC without core changes. |
| 10 | Secure by default | Auth required on every endpoint. Opt-out, not opt-in. See `security/STANDARDS.md`. |

---

## 2. Protocol Selection

Choose protocol based on communication pattern, not preference.

| Protocol | Best For | Latency | Streaming | Browser | Schema |
|---|---|---|---|---|---|
| REST/HTTP | CRUD, public APIs, wide compatibility | Medium | No (SSE possible) | Native | OpenAPI |
| gRPC | Service-to-service, high throughput, typed | Low | Bidirectional | Via proxy | Protobuf |
| GraphQL | Consumer-driven queries, aggregation | Medium | Subscriptions | Native | SDL |
| WebSocket | Real-time, bidirectional, persistent | Low | Full-duplex | Native | Custom |
| Server-Sent Events | Server-push, live feeds | Low | Server→Client | Native | None |

### Selection Criteria

| Factor | REST | gRPC | GraphQL | WebSocket |
|---|---|---|---|---|
| Public API consumers | Preferred | Avoid | Good | Avoid |
| Internal microservices | Good | Preferred | Avoid | Situational |
| Mobile clients on slow networks | Good | Good (binary) | Good (fewer round trips) | Costly (persistent conn) |
| Real-time updates | SSE instead | Streaming RPCs | Subscriptions | Preferred |
| File upload/download | Preferred | Streaming | Avoid | Avoid |
| Strong typing required | OpenAPI + codegen | Native | Native | Manual |

### Multi-Protocol Rule

Systems exposing multiple protocols share one service layer.
Protocol adapters (Tier 3) translate between wire format and service calls.
✗ duplicate business logic per protocol.

---

## 3. REST Conventions

### Resource Naming

| Rule | Correct | Incorrect |
|---|---|---|
| Plural nouns for collections | `/users` | `/user`, `/getUsers` |
| Singular sub-resource | `/users/{id}` | `/users/get/{id}` |
| Lowercase, hyphen-separated | `/user-profiles` | `/userProfiles`, `/user_profiles` |
| ✗ verbs in URLs | `/orders/{id}/cancel` (POST) | `/cancelOrder/{id}` |
| Nested max 2 levels deep | `/users/{id}/orders` | `/users/{id}/orders/{oid}/items/{iid}/tags` |
| Action sub-resources via POST | `/orders/{id}/cancel` | `/orders/{id}?action=cancel` |

### HTTP Methods

| Method | Semantics | Idempotent | Request Body | Success Code |
|---|---|---|---|---|
| GET | Read resource(s) | Yes | ✗ | 200 |
| POST | Create resource / trigger action | No | Yes | 201 (create) · 200 (action) |
| PUT | Full replace of resource | Yes | Yes | 200 |
| PATCH | Partial update of resource | No* | Yes | 200 |
| DELETE | Remove resource | Yes | ✗ | 204 (no body) · 200 (with body) |
| HEAD | Read metadata only (no body) | Yes | ✗ | 200 |
| OPTIONS | Describe allowed methods | Yes | ✗ | 204 |

*PATCH idempotent when using merge-patch or JSON Patch with absolute operations.

### HTTP Status Codes

| Range | Meaning | Common Codes |
|---|---|---|
| 2xx | Success | 200 OK · 201 Created · 202 Accepted · 204 No Content |
| 3xx | Redirect | 301 Permanent · 304 Not Modified |
| 4xx | Client error | 400 Bad Request · 401 Unauthorized · 403 Forbidden · 404 Not Found · 409 Conflict · 422 Unprocessable · 429 Too Many Requests |
| 5xx | Server error | 500 Internal · 502 Bad Gateway · 503 Unavailable · 504 Timeout |

### Status Code Selection Rules

| Scenario | Status |
|---|---|
| Malformed request syntax | 400 |
| Valid syntax, invalid semantics (field out of range) | 422 |
| Missing or invalid auth token | 401 |
| Valid token, insufficient permissions | 403 |
| Resource does not exist | 404 |
| Resource state conflict (duplicate, wrong state) | 409 |
| Rate limit exceeded | 429 |
| Unexpected server failure | 500 |
| Downstream dependency failure | 502 |
| Server overloaded or in maintenance | 503 |

### URL Structure

| Component | Convention |
|---|---|
| Base path | `/api` or `/api/v{N}` |
| Resource path | `/api/v1/resources/{id}` |
| Query params | Filtering, sorting, pagination only |
| ✗ in URL path | Session IDs, auth tokens, PII |

---

## 4. Request/Response Contracts

### Schema Definition Rules

| Rule | Detail |
|---|---|
| Schema-first | Define request/response schemas in OpenAPI, Protobuf, or GraphQL SDL before coding |
| Explicit types | Every field has declared type, format, constraints |
| Required vs optional | Every field explicitly marked. ✗ implicit optionality |
| No extra fields | Unknown fields in requests → reject (strict) or ignore (permissive) — pick one, enforce consistently |
| Stable field names | Field rename = breaking change. Add new field, deprecate old |

### Request Contract

| Aspect | Rule |
|---|---|
| Content-Type | Required on all requests with body. 415 if unsupported |
| Accept | Client declares expected response format. Default: `application/json` |
| Body shape | Flat preferred. Nest only for genuine sub-objects |
| Field naming | Consistent across entire API (see §11 Serialization) |
| Validation | Validate at API boundary. ✗ pass raw input to business logic. See `security/STANDARDS.md` |

### Response Envelope

Two valid patterns — pick one per API, enforce consistently.

**Flat response** (preferred for simple APIs):

Direct resource or array as top-level response body.
Metadata in HTTP headers (`X-Total-Count`, `Link`).

**Envelope response** (required when metadata is complex):

Top-level object with fixed structure:
- `data` — resource or array of resources
- `meta` — pagination, timing, request ID
- `errors` — array of error objects (§6)

### Response Rules

| Rule | Detail |
|---|---|
| Consistent envelope | Same structure on every endpoint. ✗ mix flat and envelope |
| Empty collections → `[]` | ✗ return null or omit field for empty lists |
| Created resources → full object | POST returning 201 includes created resource in body |
| Timestamps in body | Use ISO 8601 (§11). Include `created_at`, `updated_at` where applicable |
| Request ID | Every response includes unique request ID for tracing (header or meta) |

---

## 5. Versioning

### Strategy Selection

| Strategy | When to Use | Trade-offs |
|---|---|---|
| URL path (`/v1/`) | Public APIs, clear separation | URL changes on version bump |
| Header (`Accept: application/vnd.api.v1+json`) | Internal APIs, same URL | Less discoverable, harder to test |
| Query param (`?version=1`) | Transitional only | Easy to forget, not RESTful |

**Default: URL path versioning** for public APIs. Header versioning acceptable for internal service-to-service.

### Version Lifecycle

| Phase | Duration | Rules |
|---|---|---|
| Active | Current | Full support, bug fixes, new features |
| Deprecated | Min 6 months (production) · 1 month (internal) | Deprecation header in responses. No new features. Bug fixes only |
| Sunset | Fixed date announced | Requests return 410 Gone after sunset date |

### Breaking Change Rules

A change is breaking if any existing client could fail after deployment.

| Breaking (requires version bump) | Non-breaking (safe to add) |
|---|---|
| Remove field from response | Add optional field to response |
| Remove endpoint | Add new endpoint |
| Rename field | Add optional query parameter |
| Change field type | Add new enum value (if client handles unknown) |
| Change validation (stricter) | Relax validation (wider acceptance) |
| Change error response structure | Add new error code within existing structure |
| Change URL path | Add new header |
| Make optional field required | Add new optional field to request |

### Deprecation Protocol

1. Add `Deprecation` header with date to responses
2. Add `Sunset` header with removal date
3. Log usage of deprecated endpoints — notify consumers
4. Document migration path (old → new)
5. Remove after sunset date passes

---

## 6. Error Responses

Standard error format used across all endpoints.
See `error_handling/STANDARDS.md` for domain error classification.
See `architecture/STANDARDS.md §7` for error architecture.

### Error Object Structure

Every error response body contains array of error objects with these fields:

| Field | Required | Type | Purpose |
|---|---|---|---|
| `code` | Yes | string | Machine-readable error code (e.g., `VALIDATION_FAILED`) |
| `message` | Yes | string | Human-readable description |
| `target` | No | string | Field or parameter that caused error |
| `details` | No | array | Nested errors for field-level validation |
| `request_id` | Yes | string | Trace ID for support/debugging |

### Error Code Conventions

| Pattern | Format | Example |
|---|---|---|
| Namespace | `DOMAIN_ACTION` | `ORDER_NOT_FOUND`, `AUTH_TOKEN_EXPIRED` |
| Stable codes | ✗ change codes after release | Codes are part of API contract |
| Documented | Every code listed in API docs | Clients switch on codes, not messages |

### HTTP Status → Error Mapping

| Status | Error Code Pattern | Client Action |
|---|---|---|
| 400 | `INVALID_REQUEST` | Fix request format |
| 401 | `AUTH_*` (expired, missing, invalid) | Re-authenticate |
| 403 | `FORBIDDEN_*` | Request access or change scope |
| 404 | `*_NOT_FOUND` | Check resource ID |
| 409 | `CONFLICT_*` | Resolve conflict, retry |
| 422 | `VALIDATION_*` | Fix field values |
| 429 | `RATE_LIMITED` | Backoff, retry after delay |
| 500 | `INTERNAL_ERROR` | Report with request_id |
| 503 | `SERVICE_UNAVAILABLE` | Retry with backoff |

### Field-Level Validation Errors

Return all validation failures at once. ✗ fail on first error only.

Top-level error: `code: "VALIDATION_FAILED"`, `message` summarizes.
`details` array: one entry per invalid field, each with `target` (field path),
`code` (specific validation code), `message` (what's wrong).

### Error Response Rules

| Rule | Detail |
|---|---|
| ✗ expose stack traces | Production APIs never leak internals |
| ✗ expose DB details | No table names, column names, query fragments |
| Consistent structure | Same error shape on 4xx and 5xx |
| Log full context server-side | Bind to request_id for correlation |
| Localization | `message` in request's `Accept-Language` if supported; `code` is always English |

---

## 7. Pagination

### Strategy Selection

| Strategy | When to Use | Trade-offs |
|---|---|---|
| Cursor-based | Large/dynamic datasets, real-time feeds | No random page access. Stable under inserts/deletes |
| Offset-based | Small/static datasets, admin UIs | Skips/duplicates on concurrent writes. Simple to implement |
| Keyset | Sorted datasets with unique key | Fast, stable. Requires sortable unique field |

**Default: cursor-based** for production APIs. Offset acceptable for internal/admin tools.

### Page Size

| Rule | Detail |
|---|---|
| Default page size | Server defines (e.g., 20). Client can override up to max |
| Max page size | Hard server-side cap (e.g., 100). ✗ let client request unbounded |
| Page size = 0 | Return count only (if supported) or reject |

### Pagination Response Fields

| Field | Type | Purpose |
|---|---|---|
| `data` | array | Current page of results |
| `next_cursor` | string/null | Opaque cursor for next page. Null = last page |
| `has_more` | boolean | Whether more results exist beyond this page |
| `total_count` | integer/null | Total matching items (optional — expensive on large sets) |

### Pagination Rules

| Rule | Detail |
|---|---|
| Cursors are opaque | Client treats cursor as black box. ✗ parse or construct cursors |
| Stable ordering | Paginated results maintain consistent order across pages |
| Empty page → `[]` + `has_more: false` | ✗ return 404 for empty results |
| Pagination on all list endpoints | Every endpoint returning collections supports pagination |
| Cursor expiration | Document cursor lifetime. Expired cursor → 400 with clear error |

---

## 8. Filtering & Sorting

### Query Parameter Conventions

| Feature | Format | Example |
|---|---|---|
| Filter by field | `?field=value` | `?status=active` |
| Multiple values (OR) | `?field=val1,val2` | `?status=active,pending` |
| Range filter | `?field_gte=X&field_lte=Y` | `?created_at_gte=2024-01-01` |
| Sorting | `?sort=field` (asc) · `?sort=-field` (desc) | `?sort=-created_at` |
| Multi-sort | `?sort=-created_at,name` | Primary desc by date, secondary asc by name |
| Field selection | `?fields=id,name,email` | Return only specified fields |
| Search | `?q=term` or `?search=term` | Free-text search across searchable fields |

### Filter Operators

| Suffix | Meaning | Example |
|---|---|---|
| (none) | Equals | `?status=active` |
| `_ne` | Not equals | `?status_ne=deleted` |
| `_gt` / `_gte` | Greater than / greater or equal | `?amount_gte=100` |
| `_lt` / `_lte` | Less than / less or equal | `?amount_lt=500` |
| `_in` | In set | `?status_in=active,pending` |
| `_like` | Pattern match | `?name_like=john` |
| `_is_null` | Null check | `?deleted_at_is_null=true` |

### Filtering Rules

| Rule | Detail |
|---|---|
| Allowlist filterable fields | ✗ expose arbitrary field filtering — SQL injection risk |
| Unknown filter params → 400 | Reject, ✗ silently ignore |
| Validate filter values | Type-check against field schema |
| Document sortable fields | Not all fields are sortable. Unsupported sort field → 400 |
| Default sort order | Every list endpoint has documented default sort |
| Field selection is additive | `?fields=` requests minimum; server may include extras (IDs, type) |

---

## 9. Authentication & Authorization

Cross-reference: `security/STANDARDS.md` for full security rules.
This section covers API-specific auth patterns only.

### Token Placement

| Method | Where | When |
|---|---|---|
| Bearer token | `Authorization: Bearer <token>` header | Default for all APIs |
| API key | `X-API-Key` header | Service-to-service, third-party integrations |
| Cookie | `Set-Cookie` / `Cookie` header | Browser-based sessions only |
| Query param | `?api_key=` | ✗ Forbidden — leaked in logs, referrer, browser history |

### Auth Rules

| Rule | Detail |
|---|---|
| Auth on every endpoint | Default deny. Explicitly mark public endpoints |
| 401 vs 403 | 401 = identity unknown (missing/invalid token). 403 = identity known, insufficient permission |
| Token expiration | Access tokens: short-lived (minutes–hours). Refresh tokens: longer, rotated on use |
| Scope-based access | Tokens carry scopes. Endpoint checks scope before executing |
| ✗ auth in URL | Tokens in URL path or query string leak via logs, referrer headers, proxy caches |
| ✗ roll custom crypto | Use established standards (OAuth 2.0, JWT, OIDC) |
| Key rotation | API keys rotatable without downtime. Support overlapping validity windows |

### API Key Rules

| Rule | Detail |
|---|---|
| Prefix keys | Format: `prefix_environment_random` (e.g., `sk_prod_abc123`) — identifies key type at sight |
| Hash storage | Store hashed keys. ✗ store plaintext |
| Per-client keys | One key per client/integration. ✗ shared keys |
| Revocation | Instant revocation without redeploying |
| Rate limit per key | Each key has independent rate limits |

---

## 10. Rate Limiting

### Server-Side Rate Limiting

| Aspect | Rule |
|---|---|
| Scope | Per-client (API key or token), not per-IP alone |
| Algorithm | Token bucket or sliding window. Fixed window has burst edge cases |
| Headers in response | `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (Unix epoch) |
| Exceeded response | 429 Too Many Requests + `Retry-After` header (seconds) |
| Granularity | Different limits per endpoint tier (read vs write vs admin) |
| Burst allowance | Allow short bursts above sustained rate (token bucket refill) |

### Rate Limit Tiers

| Tier | Applies To | Typical Limit |
|---|---|---|
| Read | GET endpoints | Higher (e.g., 1000/min) |
| Write | POST, PUT, PATCH, DELETE | Lower (e.g., 100/min) |
| Search | Full-text search, complex queries | Lowest (e.g., 30/min) |
| Admin | Management endpoints | Separate, configurable |

### Client-Side Rate Limit Handling

| Rule | Detail |
|---|---|
| Respect `Retry-After` | Wait at least the specified duration before retrying |
| Exponential backoff | On repeated 429s: base delay × 2^attempt + jitter |
| Jitter | Add random offset (0–base_delay) to prevent thundering herd |
| Max retries | Cap retry attempts (e.g., 5). Fail after exhaustion |
| Circuit breaker | Stop retrying after sustained 429s. See `architecture/STANDARDS.md §7` |

---

## 11. Serialization

### JSON Conventions

| Aspect | Rule |
|---|---|
| Content type | `application/json` with `charset=utf-8` |
| Field naming | Choose one: `camelCase` (JS-ecosystem default) or `snake_case` (Python/Ruby default). Enforce across entire API |
| Boolean fields | Prefix with `is_`, `has_`, `can_` — reads as question |
| Enum values | `UPPER_SNAKE_CASE` strings. ✗ numeric enums — fragile across versions |
| Empty string vs null | Distinct meanings. Empty = explicitly blank. Null = not provided. Document which |
| Absent vs null | Absent field = default applies. Null = explicitly cleared. ✗ treat as identical |

### Date & Time

| Rule | Detail |
|---|---|
| Format | ISO 8601: `2024-01-15T09:30:00Z` |
| Timezone | UTC always in API. Client converts for display |
| Precision | Seconds minimum. Milliseconds when needed |
| Date-only | `2024-01-15` (ISO 8601 date) |
| Duration | ISO 8601 duration: `P1DT2H30M` or integer seconds with named field (`timeout_seconds`) |
| Timestamps in responses | `created_at`, `updated_at` on every mutable resource |

### Numeric Values

| Rule | Detail |
|---|---|
| Monetary values | String or integer (cents/minor unit). ✗ floating-point for money |
| Large integers | String for values > 2^53 (JavaScript integer limit) |
| Units | Field name includes unit: `weight_kg`, `duration_seconds`. ✗ ambiguous `size` or `length` |

### Null Handling

| Context | Rule |
|---|---|
| Response fields | Include field with `null` value. ✗ omit field — client can't distinguish absent from null |
| Request fields | Absent = no change (PATCH). Null = clear value. ✗ treat same |
| Collections | Empty array `[]`. ✗ null for empty collections |
| Nested objects | Empty object `{}` or null. Document which means what |

---

## 12. Idempotency

See `architecture/STANDARDS.md §1` — principle #16.

### Method Safety

| Method | Safe | Idempotent | Notes |
|---|---|---|---|
| GET | Yes | Yes | ✗ side effects on read |
| HEAD | Yes | Yes | Same as GET without body |
| OPTIONS | Yes | Yes | Metadata only |
| PUT | No | Yes | Full replace — same input = same state |
| DELETE | No | Yes | Delete of already-deleted → 204 or 404 (pick one, be consistent) |
| POST | No | No | Requires idempotency key for safe retry |
| PATCH | No | No* | Idempotent with absolute operations (set to X), not relative (increment by Y) |

### Idempotency Key Protocol

For non-idempotent operations (POST, non-absolute PATCH):

| Aspect | Rule |
|---|---|
| Header | `Idempotency-Key: <client-generated UUID>` |
| Server behavior | First request: execute + store result keyed by idempotency key |
| Duplicate request | Return stored result. ✗ re-execute |
| Key lifetime | Server stores results for defined window (e.g., 24 hours) |
| Expired key | Re-execute (client must handle) |
| Conflict | Same key + different body → 422 Unprocessable |

### Retry Semantics

| Rule | Detail |
|---|---|
| Safe methods (GET, HEAD) | Always safe to retry |
| Idempotent methods (PUT, DELETE) | Safe to retry with same body |
| POST with idempotency key | Safe to retry with same key + body |
| POST without idempotency key | ✗ auto-retry — may create duplicates |
| Timeout (no response received) | Retry with same idempotency key. Server deduplicates |
| Network error | Same as timeout — retry is safe with idempotency key |

---

## 13. API Documentation

Schema-first approach — documentation generated from contract definitions.
Cross-reference: `documentation/STANDARDS.md` for general documentation rules.

### Documentation Source of Truth

| Aspect | Rule |
|---|---|
| Schema defines API | OpenAPI (REST) · Protobuf (gRPC) · SDL (GraphQL) — these are the contract |
| Generated docs | Documentation rendered from schema. ✗ hand-written docs that diverge from schema |
| Schema in version control | Committed alongside code. Schema changes reviewed like code changes |
| Validation | CI validates implementation matches schema. Drift = build failure |

### Required Documentation Per Endpoint

| Element | Detail |
|---|---|
| Summary | One-line description of what endpoint does |
| Method + path | HTTP method and URL |
| Auth requirements | Required scopes/permissions |
| Request schema | All fields with types, constraints, required/optional |
| Response schema | Per status code (200, 400, 404, etc.) |
| Error codes | All possible error codes this endpoint returns |
| Rate limit tier | Which rate limit applies |
| Deprecation status | If deprecated: migration path + sunset date |

### Contract Testing

| Rule | Detail |
|---|---|
| Schema validation in CI | Every request/response validated against schema |
| Contract tests | Consumer-driven contract tests verify compatibility |
| Breaking change detection | CI compares schema against previous version, blocks breaking changes |
| Changelog | Every schema change documented with version, date, description |

---

## 14. Scale Matrix

Apply rules proportionally to project scale.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Protocol | REST only | REST + one more if needed | Multi-protocol with shared service layer |
| Versioning | None | URL path `/v1/` | URL path + deprecation lifecycle |
| Error format | Status code + message string | Standard error object (§6) | Full error structure + field-level details |
| Auth | API key or none | Bearer token | OAuth 2.0 / OIDC + scopes + key rotation |
| Rate limiting | None | Basic per-client | Tiered per endpoint + backpressure |
| Pagination | Offset, default page size | Cursor-based | Cursor + total count + configurable page size |
| Schema definition | Informal | OpenAPI / Protobuf | Schema-first + CI validation + contract tests |
| Idempotency | PUT/DELETE natural | Idempotency keys on critical POST | Full idempotency protocol on all mutations |
| Documentation | README | Generated from schema | Generated + changelog + deprecation notices |
| Filtering/sorting | Query params ad hoc | Defined filter fields | Allowlisted fields + operator support |
| Serialization | Consistent naming | Consistent + date format | Full serialization rules (§11) |

### Scale Transition

When graduating from one scale to next, apply new rules incrementally.
Use Strangler Fig pattern — new endpoints follow production rules,
migrate existing endpoints progressively.
See `architecture/STANDARDS.md §11`.

---

## 15. API Checklist

### New API / Service

- [ ] Protocol selected based on communication pattern (§2)
- [ ] Schema defined before implementation (§1, §13)
- [ ] Resource naming follows conventions (§3)
- [ ] Versioning strategy chosen and applied (§5)
- [ ] Error response format standardized (§6)
- [ ] Auth required on all endpoints by default (§9)
- [ ] Rate limiting configured per endpoint tier (§10)
- [ ] Serialization conventions documented and enforced (§11)
- [ ] Pagination on all list endpoints (§7)
- [ ] Request ID in every response for tracing

### New Endpoint

- [ ] HTTP method matches semantics (§3)
- [ ] Status codes correct for each scenario (§3)
- [ ] Request/response schemas defined in contract (§4)
- [ ] Error codes documented for this endpoint (§6)
- [ ] Auth scopes declared (§9)
- [ ] Rate limit tier assigned (§10)
- [ ] Idempotency requirements identified (§12)
- [ ] Filterable/sortable fields declared if collection endpoint (§8)
- [ ] Pagination parameters supported if returning list (§7)
- [ ] Breaking change review: does this change break existing clients? (§5)

### Pre-Release

- [ ] Schema validated against implementation in CI (§13)
- [ ] Contract tests cover all consumer expectations
- [ ] Error responses verified — no stack traces, no DB details (§6)
- [ ] Rate limit headers present in responses (§10)
- [ ] Deprecation headers on deprecated endpoints (§5)
- [ ] Documentation generated from schema and published (§13)
- [ ] Idempotency key storage configured for POST endpoints (§12)
- [ ] Monitoring: latency, error rate, rate limit hits per endpoint
