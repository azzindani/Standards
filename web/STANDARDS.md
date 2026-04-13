# Web Application Standards

Rules for structuring web applications — frontend, backend, and their integration.
Language-agnostic. Applies to any framework or runtime.

Composable with: architecture/STANDARDS.md (tier model), api/STANDARDS.md (API design),
security/STANDARDS.md (XSS · CSRF · CSP), performance/STANDARDS.md (budgets · profiling).

Web handlers = Tier 3 (Interface). Domain logic stays in Tier 1–2.
See architecture/STANDARDS.md §2 for tier definitions.

---

## Table of Contents

1. [Web Architecture](#1-web-architecture)
2. [Routing](#2-routing)
3. [Middleware](#3-middleware)
4. [Request Handling](#4-request-handling)
5. [Response Design](#5-response-design)
6. [State Management](#6-state-management)
7. [Authentication](#7-authentication)
8. [Authorization](#8-authorization)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Static Assets](#10-static-assets)
11. [WebSocket](#11-websocket)
12. [CORS](#12-cors)
13. [Performance](#13-performance)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Web Architecture

### Rendering Strategy Selection

| Strategy | Use When | Trade-off |
|---|---|---|
| Server-Side Rendering (SSR) | SEO required · first-paint critical · dynamic per-request data | Higher server cost · full roundtrip per navigation |
| Static Site Generation (SSG) | Content changes infrequently · marketing pages · docs | Build-time cost · stale until rebuild |
| Client-Side Rendering (CSR) | Authenticated apps · rich interactivity · real-time updates | Poor SEO · blank initial paint · JS dependency |
| Hybrid (SSR + CSR hydration) | SEO + interactivity both required | Complexity · hydration mismatch bugs |

Pick one primary strategy per application. ✗ mixing strategies without explicit boundary per route.

### API-First Rule

Backend exposes API (REST | GraphQL | gRPC). Frontend consumes API. ✗ server-rendered HTML that embeds business logic in templates. Templates render data — they do not compute it.

### Backend Tier Mapping

| Web Layer | Architecture Tier | Responsibility |
|---|---|---|
| Route handler / controller | Tier 3 (Interface) | Parse request → call service → format response |
| Service / use case | Tier 2 (Service) | Orchestrate domain operations |
| Domain logic | Tier 1 (Engine) | Business rules · validation · transforms |
| Types · constants | Tier 0 (Kernel) | Shared data structures |
| Database / external API | Tier 3 (Interface) | I/O adapters |

Route handlers: thin. Extract params → delegate → return response. ✗ business logic in handlers.

### Frontend/Backend Separation

| Rule | Detail |
|---|---|
| Separate deployable units | Frontend and backend deploy independently |
| Contract-first | API schema defined before implementation on either side |
| ✗ shared runtime state | Frontend and backend share nothing at runtime except API calls |
| Versioned API | Backend supports ≥1 previous API version during frontend rollout |

---

## 2. Routing

### URL Design

| Rule | Example | Violation |
|---|---|---|
| Lowercase, hyphen-separated | `/user-profiles` | `/UserProfiles` `/user_profiles` |
| Nouns for resources | `/orders/123` | `/getOrder/123` |
| Verbs for actions (non-CRUD) | `/orders/123/cancel` | `/orders/123/cancelled` |
| Plural collection names | `/users` `/users/42` | `/user` `/user/42` |
| Max 3 nesting levels | `/users/42/orders` | `/users/42/orders/7/items/3/tags` |
| No trailing slash | `/users` | `/users/` |
| No file extensions in API routes | `/users/42` | `/users/42.json` |

### Path Parameter Conventions

| Parameter Type | Format | Example |
|---|---|---|
| Resource identifier | Numeric or UUID in path | `/users/42` `/users/a1b2-...` |
| Filter / search | Query string | `/users?role=admin&active=true` |
| Pagination | Query string | `/users?page=2&limit=20` |
| Sort | Query string | `/users?sort=-created_at` |
| Partial response | Query string | `/users?fields=id,name,email` |

### Redirect Rules

| Scenario | Status Code | Rule |
|---|---|---|
| Permanent move | 301 | Use only when URL permanently changes. Browsers cache aggressively |
| Temporary redirect | 302/307 | Prefer 307 (preserves HTTP method) |
| POST → GET after submit | 303 | Post/Redirect/Get pattern — prevents duplicate submissions |
| ✗ redirect chains | — | Max 1 redirect hop. ✗ A→B→C chains |
| ✗ redirect loops | — | Validate redirect targets before deploying |

---

## 3. Middleware

### Ordering

Middleware executes in declared order. Order matters — incorrect ordering = security gaps.

| Position | Middleware | Reason |
|---|---|---|
| 1 | Request ID / correlation ID | Tag every log entry from request start |
| 2 | Logging (request start) | Record incoming request before any processing |
| 3 | Security headers | Set CSP · HSTS · X-Frame-Options early |
| 4 | CORS | Reject disallowed origins before further processing |
| 5 | Rate limiting | Block abusive traffic before auth cost |
| 6 | Body parsing | Parse request body (JSON · form · multipart) |
| 7 | Authentication | Identify caller |
| 8 | Authorization | Verify permissions |
| 9 | Validation | Validate parsed input against schema |
| 10 | Route handler | Business logic delegation |
| 11 | Error handling | Catch + format all uncaught errors |
| 12 | Logging (request end) | Record response status · duration |

### Middleware Responsibility Rules

| Rule | Detail |
|---|---|
| Single purpose | Each middleware does exactly one thing |
| ✗ business logic in middleware | Middleware handles cross-cutting concerns only |
| Pass or reject | Middleware either passes request to next handler or returns error response |
| ✗ modify response body | Middleware sets headers · status. ✗ rewrite response payloads (exception: compression) |
| Configurable | Middleware accepts configuration — ✗ hardcoded values |
| Skippable per route | Route-level opt-out for specific middleware when justified |

### Error Handling Middleware

- Sits at outer edge — catches all unhandled errors from inner middleware + handlers
- Maps domain errors → HTTP status codes. See §5 Response Design
- ✗ expose stack traces in production. Log full trace server-side → return sanitized message to client
- Return consistent error envelope format for all error responses

---

## 4. Request Handling

### Validation at Boundary

All input validation occurs in Tier 3 (Interface) before data reaches Tier 2.
See architecture/STANDARDS.md §2.

| Validation Layer | What | When |
|---|---|---|
| Schema validation | Structure · required fields · types · formats | Before handler logic |
| Business validation | Domain rules · cross-field constraints · uniqueness | In Tier 1 (Engine) |
| ✗ trusted input | Never trust client-provided data — validate everything | Always |

### Request Parsing Rules

| Rule | Detail |
|---|---|
| Content-Type enforcement | Reject requests with wrong/missing Content-Type. Return 415 |
| Size limits | Enforce max body size per route. Default: 1MB JSON · 10MB file upload |
| Charset | Accept UTF-8 only unless explicit multi-charset requirement |
| Path parameters | Validate format (UUID, integer) before database lookup |
| Query parameters | Whitelist known params. ✗ pass unknown params through silently |
| Header extraction | Validate required headers (Authorization · Accept · Content-Type) |

### Content Negotiation

| Accept Header | Server Response |
|---|---|
| `application/json` | JSON response (default for APIs) |
| `text/html` | HTML response (server-rendered pages) |
| `*/*` or missing | Default to JSON for API routes · HTML for page routes |
| Unsupported type | Return 406 Not Acceptable |

### Request ID

- Generate unique request ID at edge (middleware position 1)
- Propagate through all service calls · log entries · downstream API requests
- Return in response header (`X-Request-Id`)
- If client sends `X-Request-Id`, use it (enables end-to-end tracing)

---

## 5. Response Design

### HTTP Status Code Usage

| Category | Code | Use |
|---|---|---|
| Success | 200 | GET · PUT · PATCH successful |
| Success | 201 | POST created new resource. Include `Location` header |
| Success | 204 | DELETE successful · no response body |
| Client error | 400 | Malformed request · validation failure |
| Client error | 401 | Missing or invalid authentication |
| Client error | 403 | Authenticated but insufficient permissions |
| Client error | 404 | Resource not found |
| Client error | 409 | Conflict (duplicate · concurrent modification) |
| Client error | 415 | Unsupported Content-Type |
| Client error | 422 | Request well-formed but semantically invalid |
| Client error | 429 | Rate limit exceeded. Include `Retry-After` header |
| Server error | 500 | Unhandled server error — log full context server-side |
| Server error | 502 | Upstream dependency failure |
| Server error | 503 | Service unavailable. Include `Retry-After` header |

### Response Envelope

All API responses use consistent envelope structure.

| Field | Present | Purpose |
|---|---|---|
| `data` | Success responses | Payload — object or array |
| `error` | Error responses | Error object with `code` · `message` |
| `meta` | When applicable | Pagination · timing · request ID |

✗ mix envelope shapes across endpoints. One format, entire API.

### Caching Headers

| Header | Rule |
|---|---|
| `Cache-Control` | Set explicitly on every response. ✗ rely on browser defaults |
| `ETag` | Use for resource versioning — enables conditional requests (304) |
| `Last-Modified` | Set for resources with known modification timestamps |
| `Vary` | Include when response varies by Accept · Authorization · Accept-Encoding |
| API responses | `Cache-Control: no-store` for authenticated/dynamic data |
| Static assets | `Cache-Control: public, max-age=31536000, immutable` (with content-hashed filenames) |

### Response Rules

| Rule | Detail |
|---|---|
| Consistent content type | Response Content-Type matches what was negotiated |
| No null fields | Omit absent fields from response. ✗ `"field": null` unless schema requires it |
| Timestamps | ISO 8601 · UTC · include timezone offset (`Z` or `+00:00`) |
| Pagination | Cursor-based for large datasets. Offset-based acceptable for ≤10K total records |
| Empty collections | Return `[]` not `null` · not omitted |

---

## 6. State Management

### Stateless Server Preference

| Rule | Detail |
|---|---|
| Default stateless | Servers store no per-request state between requests |
| State in backing store | Session data → database | cache (Redis). ✗ in-memory server state |
| Horizontal scaling | Stateless servers = add instances without session affinity |
| ✗ sticky sessions | If session affinity required, architecture needs re-evaluation |

### Session Handling

| Aspect | Rule |
|---|---|
| Storage | Server-side session store (database | encrypted cache). ✗ store session data in cookie payload |
| Cookie | Session ID only. `HttpOnly` · `Secure` · `SameSite=Lax` minimum |
| Expiry | Absolute expiry (max 24h default) + sliding window on activity |
| Rotation | Rotate session ID on privilege escalation (login · role change) |
| Invalidation | Explicit logout destroys server-side session. ✗ rely on cookie expiry alone |
| Cleanup | Expired sessions purged on schedule — ✗ unbounded session store growth |

### Client-Side State Rules

| Rule | Detail |
|---|---|
| Minimal client state | Store only what's needed for current view. ✗ cache entire backend state client-side |
| Single source of truth | Each piece of state owned by exactly one store/component |
| URL as state | Shareable/bookmarkable state encoded in URL (filters · pagination · selected tab) |
| ✗ sensitive data in client state | Tokens in memory only — ✗ localStorage for auth tokens (XSS risk) |
| Derived state | Compute from source state — ✗ duplicate/sync separate copies |
