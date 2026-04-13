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

---

## 7. Authentication

### Strategy Selection

| Strategy | Use When | ✗ Use When |
|---|---|---|
| Session cookie | Server-rendered apps · same-origin frontend | Third-party API consumers |
| JWT (access token) | Stateless APIs · cross-origin · mobile clients | Long-lived sessions (JWT can't be revoked without infra) |
| OAuth 2.0 + OIDC | Third-party login · SSO · delegated access | Simple internal tools |
| API key | Machine-to-machine · server-to-server | Browser-based user auth |

### Token Rules

| Rule | Detail |
|---|---|
| Access token lifetime | Short: 5–15 minutes |
| Refresh token lifetime | Moderate: 1–14 days. Rotate on use (one-time use) |
| ✗ JWT in localStorage | XSS exposes tokens. Use `HttpOnly` cookies or in-memory only |
| Token payload | Minimal claims: sub · exp · iat · roles. ✗ embed sensitive data |
| Signature algorithm | RS256 or ES256 for production. ✗ HS256 with shared secrets across services |
| Token revocation | Maintain server-side deny list for compromised tokens |

### Cookie Security

| Attribute | Required Value | Reason |
|---|---|---|
| `HttpOnly` | `true` | ✗ JavaScript access to auth cookies |
| `Secure` | `true` | Transmit over HTTPS only |
| `SameSite` | `Lax` minimum · `Strict` for sensitive ops | CSRF mitigation |
| `Domain` | Explicit, narrowest scope | ✗ overly broad domain |
| `Path` | `/` or narrowest applicable path | Limit cookie scope |
| `Max-Age` / `Expires` | Explicit. Match session policy | ✗ session cookies without expiry |

### CSRF Protection

| Rule | Detail |
|---|---|
| Synchronizer token | Server generates unique token per session → embedded in forms → validated on submit |
| Double-submit cookie | Alternative: random value in cookie + request header/body → server compares |
| `SameSite` cookies | Defense-in-depth — ✗ sole CSRF protection (older browsers lack support) |
| Safe methods exempt | GET · HEAD · OPTIONS ✗ mutate state → no CSRF token needed |
| ✗ state mutation via GET | GET requests are idempotent + safe. ✗ `/delete?id=5` via GET |

---

## 8. Authorization

### Model Selection

| Model | Use When | Complexity |
|---|---|---|
| Role-Based (RBAC) | Fixed permission sets per role (admin · editor · viewer) | Low |
| Permission-Based | Granular: `orders.create` · `orders.delete` per user | Medium |
| Attribute-Based (ABAC) | Context-dependent: time · IP · resource owner · department | High |
| Relationship-Based (ReBAC) | "User X can edit because they own resource Y" | High |

Start with RBAC. Move to permission-based when roles become insufficient. ABAC/ReBAC only when ownership or context rules dominate.

### Authorization Rules

| Rule | Detail |
|---|---|
| Server-side enforcement | All authorization checks on server. ✗ client-side auth checks as sole protection |
| Middleware placement | Authorization middleware runs after authentication (position 8 in §3) |
| Default deny | Unauthenticated requests → 401. Unauthorized requests → 403 |
| Resource-level checks | Verify caller has access to specific resource, not just endpoint. ✗ "can access /orders" without checking order ownership |
| ✗ role checks in business logic | Use middleware or decorators. Domain logic receives pre-authorized context |
| Audit trail | Log authorization decisions (granted + denied) with caller identity · resource · action |
| Principle of least privilege | Grant minimum permissions required. Expand only when justified |

### Frontend Authorization

| Rule | Detail |
|---|---|
| UI gating | Hide/disable UI elements user cannot access — for UX, not security |
| ✗ client-only enforcement | Server re-validates every request regardless of frontend checks |
| Permission-aware components | Components receive permission set → render conditionally |
| ✗ embed permission logic in components | Centralize permission evaluation → components consume boolean results |

---

## 9. Frontend Architecture

### Component Design

| Rule | Detail |
|---|---|
| Single responsibility | One component = one purpose. Split when component handles >1 concern |
| Presentational vs container | Separate data-fetching components from rendering components |
| Props down, events up | Parent → child via props/attributes. Child → parent via events/callbacks |
| ✗ prop drilling >3 levels | Use context/state management for deeply nested data |
| Composition over inheritance | Build complex components by composing simple ones |
| Deterministic rendering | Same props + same state = same output. ✗ side effects in render path |

### Frontend State Management

| State Type | Storage | Example |
|---|---|---|
| Server state | Cache layer with stale/revalidate | API responses · user profile |
| UI state | Component-local state | Dropdown open · modal visible |
| URL state | URL params / query string | Active tab · filters · page number |
| Form state | Component or form library | Input values · validation errors |
| Global app state | State store (single source of truth) | Auth status · theme · feature flags |

✗ put everything in global store. Most state is local or server-derived.

### Frontend Routing

| Rule | Detail |
|---|---|
| Declarative route config | Routes defined as data structure — ✗ scattered across components |
| Code splitting per route | Each route loads its own bundle. ✗ single monolithic bundle |
| Route guards | Auth/permission checks before route renders |
| 404 fallback | Unmatched routes → dedicated not-found page |
| URL reflects state | Back button · bookmark · share URL all work correctly |
| ✗ hash routing in production | Use history API (clean URLs). Hash routing = legacy fallback only |

### Build Optimization

| Rule | Detail |
|---|---|
| Tree shaking | Dead code elimination enabled. ✗ import entire libraries for one function |
| Code splitting | Route-based + component-based lazy loading |
| Bundle analysis | Run bundle analyzer in CI. Fail build if bundle exceeds budget (see §13) |
| Source maps | Generate for production but ✗ serve publicly. Upload to error tracking service |
| Minification | HTML · CSS · JS all minified in production builds |
| Environment variables | Inject at build time. ✗ runtime environment checks in client bundle |

---

## 10. Static Assets

### Caching Strategy

| Asset Type | Cache-Control | Filename Strategy |
|---|---|---|
| JS · CSS bundles | `public, max-age=31536000, immutable` | Content hash in filename (`app.a3f9c2.js`) |
| Images · fonts | `public, max-age=31536000, immutable` | Content hash or versioned path |
| HTML entry point | `no-cache` (revalidate every request) | No hash — always latest |
| API responses | `no-store` or short `max-age` | N/A |
| Service worker | `no-cache` | Fixed filename, browser handles updates |

### CDN Rules

| Rule | Detail |
|---|---|
| Static assets served via CDN | ✗ serve static files from application server in production |
| Origin shield | CDN caches pull from single origin — reduces origin load |
| Cache invalidation | Use content-hashed filenames → ✗ manual cache purge needed |
| Geographic distribution | CDN edge nodes close to users. Measure TTFB per region |
| ✗ CDN for authenticated content | Authenticated responses bypass CDN or use signed URLs |
| Fallback | Application server serves assets if CDN fails (graceful degradation) |

### Compression

| Rule | Detail |
|---|---|
| Brotli preferred | Brotli (br) for text assets — 15-25% smaller than gzip |
| Gzip fallback | Serve gzip when client doesn't support Brotli |
| Pre-compressed | Build step generates `.br` + `.gz` files. ✗ on-the-fly compression for static assets |
| Minimum size | ✗ compress files <1KB — overhead exceeds savings |
| Binary assets | ✗ compress already-compressed formats (JPEG · PNG · WOFF2) |

---

## 11. WebSocket

### When to Use

| Use WebSocket | Use HTTP Polling | Use Server-Sent Events (SSE) |
|---|---|---|
| Bidirectional real-time (chat · collaborative editing) | Infrequent updates (<1/min) | Server → client only (notifications · feeds) |
| Low-latency required (<100ms) | Simple infrastructure required | One-way push sufficient |
| High-frequency messages | WebSocket infra unavailable | Auto-reconnect built in |

### Connection Lifecycle

| Phase | Rule |
|---|---|
| Connect | Authenticate during handshake (token in query param or first message). ✗ unauthenticated WebSocket connections |
| Heartbeat | Client + server send ping/pong every 30s. Detect dead connections within 60s |
| Reconnect | Client implements exponential backoff: 1s → 2s → 4s → 8s → max 30s |
| Message format | Structured messages with `type` field for routing. ✗ untyped string messages |
| Close | Clean close with status code. Server broadcasts disconnect to relevant parties |
| ✗ large payloads | Keep messages <64KB. Large data → HTTP endpoint + notify via WebSocket |

### WebSocket State Rules

| Rule | Detail |
|---|---|
| Server authoritative | Server state = source of truth. Client state = optimistic projection |
| Idempotent messages | Client may resend on reconnect — server handles duplicates |
| Sequence tracking | Messages carry sequence numbers for ordering + gap detection |
| Connection limit | Budget max concurrent connections per server instance |
| ✗ session state in WS only | Persist critical state to database. WebSocket connection is ephemeral |

---

## 12. CORS

### Policy Rules

| Rule | Detail |
|---|---|
| Explicit allowed origins | Whitelist specific origins. ✗ `Access-Control-Allow-Origin: *` for authenticated APIs |
| Wildcard acceptable for | Public read-only APIs with no authentication |
| Credentials mode | `Access-Control-Allow-Credentials: true` requires specific origin (✗ wildcard) |
| Allowed methods | List only methods the API uses. ✗ allow all methods |
| Allowed headers | List only headers the API expects. ✗ allow all headers |
| Expose headers | Explicitly expose custom response headers client needs (e.g., `X-Request-Id`) |

### Preflight Handling

| Rule | Detail |
|---|---|
| Cache preflight | `Access-Control-Max-Age: 7200` (2h) minimum — reduces OPTIONS requests |
| OPTIONS response | Return 204 with CORS headers. ✗ process body on preflight |
| ✗ auth on preflight | OPTIONS requests carry no credentials — ✗ require auth |
| Rate limiting | Exempt preflight OPTIONS from rate limiting |

### CORS Middleware Placement

Position 4 in middleware stack (see §3). CORS rejection occurs before authentication — saves processing cost for disallowed origins.

---

## 13. Performance

### Server Response Time Budgets

| Endpoint Type | Budget (p95) | Action on Breach |
|---|---|---|
| Health check | <10ms | Investigate immediately |
| Simple read (by ID) | <50ms | Add caching or index |
| List/search | <200ms | Paginate · optimize query · add cache |
| Write (create/update) | <200ms | Async processing if >200ms |
| Complex aggregation | <500ms | Pre-compute or background job |
| File upload | <2s (excluding transfer) | Stream processing · async |

### Frontend Performance Budgets

| Metric | Budget | Measurement |
|---|---|---|
| Initial JS bundle (compressed) | <100KB per route | Build-time bundle analysis |
| Total JS (all routes, compressed) | <300KB | Build-time |
| First Contentful Paint (FCP) | <1.5s | Lighthouse / field data |
| Largest Contentful Paint (LCP) | <2.5s | Core Web Vitals |
| Cumulative Layout Shift (CLS) | <0.1 | Core Web Vitals |
| Interaction to Next Paint (INP) | <200ms | Core Web Vitals |
| Time to Interactive (TTI) | <3.5s | Lighthouse |

### Optimization Rules

| Technique | When | Rule |
|---|---|---|
| Lazy loading | Below-fold images · non-critical routes | Load on scroll/navigate — ✗ load everything upfront |
| Preloading | Critical resources (fonts · above-fold images) | `<link rel="preload">` for render-critical assets |
| SSR/SSG | SEO pages · landing pages | Server-render critical path — hydrate interactivity |
| Database query optimization | Every query | Index lookup ✗ table scan. Explain plan in review |
| Connection pooling | All database connections | Pool size = (cores × 2) + spindle_count as starting point |
| Response compression | All text responses >1KB | Brotli preferred → gzip fallback |
| HTTP/2+ | All production deployments | Multiplexed connections · header compression · server push |
| Request collapsing | Duplicate concurrent requests | Deduplicate identical in-flight requests |

### Caching Strategy

| Layer | Cache | TTL | Invalidation |
|---|---|---|---|
| Browser | HTTP cache headers | Per-resource (see §5 · §10) | Content-hashed URLs |
| CDN edge | Static assets · public pages | Long (immutable for hashed assets) | Deploy new hashed filenames |
| Application | Computed results · API responses | Short (seconds to minutes) | Event-driven or TTL expiry |
| Database | Query results | Short | Write-through or cache-aside pattern |

See performance/STANDARDS.md for profiling methodology · budget enforcement.

---

## 14. Scale Matrix

| Aspect | Solo/Prototype | Small Team (2–5) | Production | Large Scale |
|---|---|---|---|---|
| **Rendering** | CSR (SPA) | SSR or CSR based on need | Hybrid SSR + CSR | SSR + CDN edge rendering |
| **API** | REST, single version | REST with versioning | REST or GraphQL + versioning | API gateway + multiple backends |
| **State** | In-memory | Database sessions | Distributed cache (Redis) | Distributed cache + partitioned state |
| **Auth** | Session cookie | JWT or session + CSRF | OAuth 2.0 + OIDC | Federated identity + SSO |
| **Authorization** | Simple role check | RBAC | Permission-based | ABAC or ReBAC |
| **Static assets** | Serve from app server | CDN for production | CDN + content hashing | Multi-region CDN + edge caching |
| **WebSocket** | Direct connection | Direct + heartbeat | Load-balanced + pub/sub | Dedicated WS cluster + message broker |
| **Middleware** | Minimal (logging + errors) | Standard stack (§3 full list) | Full stack + APM | Full stack + distributed tracing |
| **CORS** | Wildcard for dev | Explicit origin list | Strict origin whitelist | Per-service CORS policy |
| **Monitoring** | Console logging | Structured logging | APM + error tracking + alerts | Distributed tracing + real-time dashboards |
| **Performance** | No budgets | Bundle size budget | Full budget enforcement in CI | Per-region performance monitoring |
| **Deployment** | Manual | CI/CD single region | Blue-green or canary | Multi-region + traffic shifting |

---

## 15. Checklist

### Backend

- [ ] Route handlers are thin — delegate to service layer (Tier 2)
- [ ] ✗ business logic in handlers or middleware
- [ ] All input validated at boundary (Tier 3) before reaching domain logic
- [ ] Consistent response envelope across all endpoints
- [ ] Correct HTTP status codes per §5 table
- [ ] Request ID generated + propagated + returned in response
- [ ] Error handling middleware catches all unhandled errors
- [ ] ✗ stack traces exposed to client in production
- [ ] Content-Type enforcement on all routes accepting body
- [ ] Body size limits set per route
- [ ] Cache-Control headers set explicitly on every response

### Authentication + Authorization

- [ ] Auth cookies: `HttpOnly` · `Secure` · `SameSite`
- [ ] CSRF protection on all state-mutating endpoints
- [ ] ✗ state mutation via GET
- [ ] Session ID rotated on privilege change
- [ ] Access tokens short-lived (5–15 min)
- [ ] Authorization enforced server-side on every request
- [ ] Default deny — unauthenticated → 401, unauthorized → 403
- [ ] Resource-level permission checks (not just endpoint-level)

### Frontend

- [ ] Single source of truth per state type (§9)
- [ ] Code splitting per route
- [ ] Bundle size within budget (§13)
- [ ] Core Web Vitals within budget (§13)
- [ ] Tree shaking enabled · ✗ unused imports
- [ ] ✗ auth tokens in localStorage
- [ ] URL state supports bookmarking + back button
- [ ] Permission-aware UI gating (UX only — ✗ sole enforcement)

### Infrastructure

- [ ] CORS explicit origin whitelist (✗ wildcard for authenticated APIs)
- [ ] Preflight caching enabled (max-age ≥ 2h)
- [ ] Static assets: content-hashed filenames + immutable cache headers
- [ ] HTML entry point: `no-cache`
- [ ] Compression: Brotli preferred + gzip fallback
- [ ] CDN serves static assets in production
- [ ] HTTP/2+ enabled
- [ ] Server response time budgets monitored (§13)

### WebSocket (if applicable)

- [ ] Authenticated during handshake
- [ ] Heartbeat ping/pong every 30s
- [ ] Client reconnect with exponential backoff
- [ ] Messages structured with `type` field
- [ ] Message size <64KB
- [ ] Critical state persisted to database (✗ WS-only state)
