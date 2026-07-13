# Web Application Standards

> Rules for structuring web applications — frontend, backend, their contract, accessibility, and internationalization.

**ID** `web` · **Tier** Interface · **Version** 1.0
**Owns** rendering strategy (SSR/CSR/SSG/hydration) · progressive enhancement · frontend routing + state · browser security (CSP · XSS escaping) · cookie attributes + CSRF + browser token storage + frontend route gating · Core Web Vitals · **accessibility (WCAG)** · **i18n/l10n** · HTTP/CDN caching + static-asset delivery
**Defers to** authn/authz model + token lifetimes + secrets → [security](../security/STANDARDS.md) · API design + status codes + envelope + versioning → [api](../api/STANDARDS.md) · rate limiting → [api](../api/STANDARDS.md) · caching strategy + profiling → [performance](../performance/STANDARDS.md) · pagination mechanics → [database](../database/STANDARDS.md) · CDN/edge infra + deploy → [devops](../devops/STANDARDS.md) · alert thresholds → [observability](../observability/STANDARDS.md) · coverage + pyramid → [testing](../testing/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [api](../api/STANDARDS.md) · [security](../security/STANDARDS.md) · [performance](../performance/STANDARDS.md)

---

## Table of Contents

1. [Web Architecture](#1-web-architecture)
2. [Routing](#2-routing)
3. [Middleware](#3-middleware)
4. [Request & Response](#4-request--response)
5. [Caching & Static Delivery](#5-caching--static-delivery)
6. [Browser Security](#6-browser-security)
7. [Session, Auth & CSRF](#7-session-auth--csrf)
8. [State Management](#8-state-management)
9. [Frontend Architecture](#9-frontend-architecture)
10. [Accessibility](#10-accessibility)
11. [Internationalization](#11-internationalization)
12. [Real-Time](#12-real-time)
13. [Core Web Vitals & Performance](#13-core-web-vitals--performance)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Web Architecture

Web handlers = Tier 3 Interface. Domain logic stays in Tier 1–2. See [architecture](../architecture/STANDARDS.md).

### Rendering Strategy

| Strategy | Use when | Trade-off |
|---|---|---|
| SSR | SEO required · first-paint critical · per-request dynamic data | Higher server cost · full roundtrip per navigation |
| SSG | Content changes infrequently · marketing · docs | Build-time cost · stale until rebuild |
| CSR | Authenticated apps · rich interactivity · real-time | Poor SEO · blank first paint · hard JS dependency |
| Hybrid (SSR + CSR hydration) | SEO **and** interactivity both required | Hydration-mismatch bugs · complexity |

Pick one primary strategy per app. ✗ mix without an explicit per-route boundary.

### Progressive Enhancement

| Rule | Detail |
|---|---|
| Core function without JS | Content readable and primary actions work as plain HTML forms; JS enhances, ✗ gates. A CDN miss or script error degrades, ✗ blanks the page |
| Server-rendered baseline | Meaningful first paint before hydration for content routes |
| Feature-detect | Detect capabilities, ✗ sniff user-agent strings |

### Tier Mapping & Separation

| Web layer | Tier | Responsibility |
|---|---|---|
| Route handler / controller | 3 Interface | Parse request → call service → format response |
| Service / use case | 2 Service | Orchestrate domain operations |
| Domain logic | 1 Engine | Business rules · validation · transforms |
| Types · constants | 0 Kernel | Shared data structures |
| DB / external API adapter | 3 Interface | I/O |

Handlers stay thin: extract → delegate → return. ✗ business logic in handlers. Frontend and backend deploy as separate units, share nothing at runtime except the versioned API contract → [api](../api/STANDARDS.md).

---

## 2. Routing

| Rule | Example | ✗ Violation |
|---|---|---|
| Lowercase, hyphen-separated | `/user-profiles` | `/UserProfiles` · `/user_profiles` |
| Nouns for resources | `/orders/123` | `/getOrder/123` |
| Verbs only for non-CRUD actions | `/orders/123/cancel` | `/orders/123/cancelled` |
| Plural collections | `/users` · `/users/42` | `/user/42` |
| Nesting ≤ 3 levels | `/users/42/orders` | `/users/42/orders/7/items/3/tags` |
| No trailing slash | `/users` | `/users/` |
| No file extension in API routes | `/users/42` | `/users/42.json` |

Path parameters carry resource identifiers only; filter · sort · pagination · sparse-field selection live in the query string.

Redirects: 301 permanent (browsers cache hard, use only for a permanent URL change) · 307 temporary (preserves the method, prefer over 302) · 303 after a form POST (Post/Redirect/Get, prevents duplicate submission). Max 1 hop — ✗ A→B→C chains, ✗ loops; validate targets before deploy.

---

## 3. Middleware

Executes in declared order. Order is a security control — wrong order = a gap.

| # | Middleware | Reason |
|---|---|---|
| 1 | Request ID / correlation ID | Tag every log line from the first byte |
| 2 | Request logging (start) | Record the request before processing |
| 3 | Security headers | CSP · HSTS · `X-Content-Type-Options` set early (§6) |
| 4 | CORS | Reject disallowed origins before spending further cost (§6) |
| 5 | Rate limiting | Shed abusive traffic before auth cost. Rules → [api](../api/STANDARDS.md) |
| 6 | Body parsing | Parse JSON · form · multipart |
| 7 | Authentication | Identify the caller → [security](../security/STANDARDS.md) |
| 8 | Authorization | Verify permission → [security](../security/STANDARDS.md) |
| 9 | Validation | Validate parsed input against schema |
| 10 | Route handler | Delegate to the service layer |
| 11 | Error handling | Catch + format every uncaught error |
| 12 | Request logging (end) | Record status + duration |

| Rule | Detail |
|---|---|
| Single purpose · pass or reject | Each middleware does one thing — cross-cutting concerns only — and either forwards or returns an error |
| ✗ business logic · ✗ rewrite bodies | Sets headers/status only ; compression |
| Error middleware at the outer edge | Catches everything inner. Maps domain errors → status (§4). ✗ leak stack traces — log server-side, return a sanitized envelope |

---

## 4. Request & Response

HTTP status codes, error envelope shape, and versioning are owned by [api](../api/STANDARDS.md). This section covers browser-facing handling. ✗ restate the status table.

| Rule | Detail |
|---|---|
| Validate at the boundary | All input validated in Tier 3 before Tier 2 — schema (structure · types · formats) at the edge, business rules in Tier 1. ✗ trust client input, ever |
| `Content-Type` enforced | Wrong/missing on a body → 415 |
| Body size limits | Per route. Default 1 MB JSON · 10 MB upload → 413 on exceed |
| Charset | UTF-8 only unless a multi-charset requirement is explicit |
| Params | Path params (UUID/integer) format-checked before any lookup; query params allowlisted, unknown → reject |
| Content negotiation | `application/json` → JSON · `text/html` → page · unsupported → 406 |
| Request ID | Generated at the edge, propagated through every call and log, returned as `X-Request-Id`; reuse a client-supplied value for tracing |
| Response envelope | One consistent shape across the app → [api](../api/STANDARDS.md); timestamps ISO 8601 UTC (`Z`); empty collections `[]`, ✗ `null` |

---

## 5. Caching & Static Delivery

The HTTP/CDN layer only. Caching **strategy** (what to cache, invalidation policy, cache tiers) → [performance](../performance/STANDARDS.md).

| Header | Rule |
|---|---|
| `Cache-Control` | Set explicitly on every response. ✗ rely on browser defaults |
| `ETag` | On versionable resources → enables conditional requests → 304 |
| `Last-Modified` | On resources with a known modification time |
| `Vary` | When the response varies by `Accept` · `Authorization` · `Accept-Encoding` · `Accept-Language` |

| Asset | `Cache-Control` | Filename |
|---|---|---|
| JS · CSS bundles | `public, max-age=31536000, immutable` | Content hash — `app.a3f9c2.js` |
| Images · fonts | `public, max-age=31536000, immutable` | Content-hashed or versioned |
| HTML entry point | `no-cache` (revalidate every request) | No hash — always latest |
| Authenticated / dynamic API | `no-store` | — |
| Service worker | `no-cache` | Fixed name; the browser manages updates |

| Rule | Detail |
|---|---|
| CDN serves static assets in production | ✗ from the app server. Content-hashed filenames → new deploy = new URL → ✗ manual purge |
| ✗ CDN for authenticated content | Bypass the CDN or use signed URLs; app server serves assets if the CDN fails |
| Compression | Brotli preferred → gzip fallback, pre-compressed at build (`.br` + `.gz`), ✗ on the fly. ✗ compress files < 1 KB or already-compressed formats (JPEG · PNG · WOFF2) |
| Protocol | HTTP/2 or HTTP/3 — multiplexing + header compression |

CDN edge/region topology and deploy mechanics → [devops](../devops/STANDARDS.md).

---

## 6. Browser Security

XSS injection vectors and CSP are web's to own. The validation boundary + secrets are owned by [security](../security/STANDARDS.md).

### Security Headers

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Explicit allowlist; `default-src 'self'` baseline | Primary XSS defense — restrict script/style/connect origins |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Stop MIME sniffing |
| `X-Frame-Options` / CSP `frame-ancestors` | `DENY` \| explicit allowlist | Clickjacking defense |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |

CSP: ✗ `unsafe-inline` (nonce/hash any inline script) · ✗ `unsafe-eval` · ship `Content-Security-Policy-Report-Only` first, enforce once clean.

### XSS Escaping

| Context | Encoding |
|---|---|
| HTML body | HTML-entity encode |
| HTML attribute | Attribute-encode + always quote |
| JS string / JSON in page | JS-encode; ✗ interpolate untrusted data into a `<script>` |
| URL parameter | URL-encode; validate the scheme — ✗ `javascript:` |
| CSS value | CSS-encode |

Encode on output per context (auto-escaping template engine, encoding matches the sink). ✗ raw HTML injection — `innerHTML` / `dangerouslySetInnerHTML` only through a sanitizer allowlist; build DOM via framework binding or `textContent`, ✗ from strings.

### CORS

Runs at middleware position 4 (§3) — before authentication.

| Rule | Detail |
|---|---|
| Explicit allowed origins | Allowlist specific origins. ✗ `Access-Control-Allow-Origin: *` for authenticated APIs — wildcard only for public, unauthenticated, read-only APIs |
| Credentials mode | `Access-Control-Allow-Credentials: true` requires a specific origin — ✗ wildcard |
| Methods + headers | List only what the API uses. ✗ allow-all |
| Preflight | Cache with `Access-Control-Max-Age` ≥ 7200 · respond 204 · ✗ require auth on OPTIONS · exempt from rate limiting |

---

## 7. Session, Auth & CSRF

The authn/authz model — RBAC/ABAC, default-deny, resource-level checks, least privilege, **token lifetimes**, secret rotation — is owned by [security](../security/STANDARDS.md). This section covers the web delta only: how credentials live in the browser and how requests are protected. ✗ restate a token lifetime number — token lifetimes (browser-facing and service-to-service classes) are stated in [security](../security/STANDARDS.md).

### Browser Token Storage

| Store | Verdict |
|---|---|
| `HttpOnly` cookie | Preferred for session credentials — unreachable from JS |
| In-memory (JS variable) | Acceptable for a short-lived access token in an SPA — lost on reload, refreshed via cookie |
| `localStorage` / `sessionStorage` | ✗ for auth tokens — any XSS reads them |

Rely on refresh-token rotation (one-time use) for session continuity; lifetimes and rotation policy → [security](../security/STANDARDS.md).

### Cookie Attributes

| Attribute | Value | Reason |
|---|---|---|
| `HttpOnly` | `true` | ✗ JavaScript access to auth cookies |
| `Secure` | `true` | HTTPS transmission only |
| `SameSite` | `Lax` minimum · `Strict` for sensitive operations | CSRF mitigation |
| `Domain` | Narrowest explicit scope | ✗ overly broad |
| `Path` | `/` or narrower | Limit scope |
| `Max-Age` / `Expires` | Explicit, matching session policy | ✗ non-expiring session cookies |
| `__Host-` prefix | For host-locked session cookies | Binds the cookie to the exact host + path |

### Session Handling

| Rule | Detail |
|---|---|
| Store server-side | Session data in a database or encrypted cache. ✗ store session state in the cookie payload |
| Cookie carries the ID only | Opaque session identifier |
| Rotate on privilege change | New session ID on login and on role change — defeats fixation |
| Absolute + idle expiry | Absolute cap (24 h default) + sliding idle window |
| Explicit logout | Destroys the server-side session. ✗ rely on cookie expiry alone |
| Purge expired sessions | Scheduled cleanup. ✗ unbounded store growth |

### CSRF

| Rule | Detail |
|---|---|
| Synchronizer token | Per-session token embedded in forms, validated on every state-changing submit |
| Double-submit cookie | Alternative: random value in a cookie + matching header, server compares |
| `SameSite` is defense-in-depth | ✗ sole CSRF defense — legacy browsers and some flows bypass it |
| Safe methods exempt | GET · HEAD · OPTIONS carry no CSRF token — they must not mutate state |
| ✗ state mutation via GET | ✗ `/delete?id=5` over GET |

### Frontend Route Gating

| Rule | Detail |
|---|---|
| UI gating is UX, not security | Hide/disable what the user can't use — the server re-authorizes every request regardless |
| Route guards | Auth/permission checks before a route renders; unauthenticated → redirect to login |
| ✗ permission logic in components | Centralize evaluation → components consume boolean results |

---

## 8. State Management

| Rule | Detail |
|---|---|
| Stateless servers | No per-request state between requests → horizontal scaling without affinity. ✗ sticky sessions — they signal a state-ownership problem |
| State in a backing store | Session/shared state → database or cache. ✗ in-memory server state |
| Minimal client state | Only what the current view needs; ✗ mirror the whole backend client-side |
| Single source of truth · derived state | Each piece owned by one store; compute from source, ✗ duplicate and sync copies |
| URL as state | Shareable/bookmarkable state (filters · pagination · active tab) encoded in the URL |
| ✗ sensitive data client-side | See §7 token storage |

State placement: server state → cache layer with stale-while-revalidate · UI state → component-local · URL state → query string/path · form state → component or form library · global app state (auth · theme · feature flags) → single store. ✗ put everything in the global store — most state is local or server-derived.

---

## 9. Frontend Architecture

| Rule | Detail |
|---|---|
| Single responsibility | One component = one purpose; separate data-fetching (container) from rendering (presentational) |
| Props down, events up | Parent → child via props · child → parent via callbacks. ✗ prop drilling > 3 levels — use context or a store |
| Composition over inheritance | Build complex UI from simple pieces |
| Deterministic render | Same props + state → same output. ✗ side effects in the render path |

| Build rule | Detail |
|---|---|
| Tree shaking · code splitting | Dead-code elimination on (✗ import a whole library for one function); split per route + lazy-load heavy components |
| Bundle budget in CI | Fail the build when a bundle exceeds its budget (§13) |
| Source maps · minification | Maps generated but ✗ served publicly (upload to the error tracker); HTML · CSS · JS minified in production |
| Env injection at build | ✗ runtime environment branching in the client bundle |
| Declarative routes · History API | Route config as data (✗ scattered), clean URLs (hash routing legacy-only), unmatched route → 404 page |

---

## 10. Accessibility

Target: **WCAG 2.2 Level AA**. Accessibility is a correctness requirement, ✗ an enhancement.

### Semantic Structure

| Rule | Detail |
|---|---|
| Semantic HTML first | Native `<button>` · `<a>` · `<nav>` · `<main>` · `<label>` · `<table>` before any ARIA. They ship focus, keyboard, and role behavior free |
| One `<h1>` per page · ordered headings | ✗ skip levels — headings are the screen-reader outline |
| Landmark regions | `<header>` · `<nav>` · `<main>` · `<footer>` for navigation-by-region |
| `lang` attribute | `<html lang>` set, and per-element when content language changes |
| `<a>` vs `<button>` | Link navigates to a URL · button performs an action. ✗ a `<div>` with a click handler |

### Keyboard & Focus

| Rule | Detail |
|---|---|
| Everything operable by keyboard | Every interactive element reachable and activatable with Tab · Enter · Space · arrows. ✗ mouse-only controls |
| Visible focus indicator | Never remove the focus ring without a stronger replacement — WCAG 2.2 requires a visible, non-obscured focus state |
| Logical focus order | Tab order follows reading order; ✗ positive `tabindex` |
| Focus management | Move focus into an opened modal, trap it there, restore it to the trigger on close |
| Skip link | "Skip to content" as the first focusable element |
| ✗ keyboard traps | Focus can always leave a component |

### Perceivable

| Rule | Threshold |
|---|---|
| Text contrast | ≥ **4.5:1** normal text · ≥ **3:1** large text (≥ 24px, or ≥ 19px bold) |
| Non-text contrast | ≥ **3:1** for UI components, focus indicators, and meaningful graphics |
| ✗ color as the sole signal | Pair color with text, icon, or pattern — error states never rely on red alone |
| Images | Informative → descriptive `alt`; decorative → `alt=""`; ✗ omit the attribute |
| Media | Captions for audio; text alternative for video |
| `prefers-reduced-motion` | Honor it — disable non-essential animation, parallax, autoplay |
| Text resize | Usable at 200% zoom and at 320px width without loss of content or horizontal scroll |

### Forms

| Rule | Detail |
|---|---|
| Every input labelled | A programmatic `<label for>` (or `aria-label` where no visible label exists). ✗ placeholder-as-label |
| Errors associated | Link the message to the field via `aria-describedby`; mark invalid fields `aria-invalid` |
| Errors announced | Validation summary in an `aria-live` region · move focus to the first error |
| Group related controls | `<fieldset>` + `<legend>` for radio/checkbox groups |
| Required marked | Programmatically (`required` / `aria-required`), ✗ by color or asterisk alone |

### ARIA & Testing

| Rule | Detail |
|---|---|
| "No ARIA is better than bad ARIA" | Reach for ARIA only when semantic HTML cannot express the pattern; wrong ARIA is worse than none |
| Dynamic updates | Announce async changes through `aria-live` regions |
| Automated axe in CI | An axe-core (or equivalent) scan gates the build — a **floor**, not a ceiling; it catches ~30–40% of issues |
| Manual verification | Keyboard-only walkthrough + one screen reader (NVDA · VoiceOver · JAWS) on primary flows — automation cannot confirm operability |

---

## 11. Internationalization

i18n = the app is *translatable and locale-aware*; l10n = a specific locale is *supplied*. Build for i18n from the first screen — retrofitting is a rewrite.

### Text

| Rule | Detail |
|---|---|
| Externalize every string | User-visible text lives in translation resources keyed by ID. ✗ hard-coded literals in components |
| ✗ concatenate translated fragments | Grammar and word order differ per language — one key per complete message with interpolated variables |
| ICU MessageFormat | Plurals, gender, and select handled by ICU — ✗ `if (count === 1)` branching in code |
| Interpolate, don't splice | `"Hello, {name}"` as one message. ✗ `"Hello, " + name` |
| Translator context | Provide a description + max length per key |
| Missing translation | Fall back to a default locale and surface it in QA. ✗ render a raw key to the user |

### Locale-Aware Formatting

| Data | Rule |
|---|---|
| Dates · times | Format per locale (order, separators, calendar) — ✗ a hard-coded `MM/DD/YYYY` |
| Numbers | Locale decimal + grouping separators (`1,234.5` vs `1.234,5`) |
| Currency | Format for the locale **and** show the currency explicitly; ✗ assume `$`. Money value handling → [database](../database/STANDARDS.md) · [api](../api/STANDARDS.md) |
| Collation / sorting | Locale-aware collation — ✗ raw byte/codepoint sort for display lists |
| Names · addresses | ✗ assume first/last order or a US address shape |

### Time Zones

| Rule | Detail |
|---|---|
| Store UTC | Persist and transmit timestamps in UTC → [api](../api/STANDARDS.md) · [database](../database/STANDARDS.md) |
| Render local | Convert to the user's time zone at display time |
| Carry the zone for future events | A future local appointment stores its IANA zone (`Europe/Paris`), not a fixed offset — offsets shift with DST |

### Layout & Negotiation

| Rule | Detail |
|---|---|
| RTL support | Logical CSS properties (`margin-inline-start`, not `margin-left`) + `dir="rtl"`; mirror layout, icons, and progress direction |
| Text-expansion tolerance | Design for ~30–40% growth from English; ✗ fixed-width buttons that clip translations · ✗ text baked into images |
| `Accept-Language` negotiation | Default from the header, matched against supported locales |
| Explicit user override | A user-chosen locale beats the header and persists across sessions |
| Locale in the URL or profile | Reflect the active locale (`/fr/…` or a stored preference) so it is shareable and cacheable; add `Vary: Accept-Language` |

---

## 12. Real-Time

| Use WebSocket | Use SSE | Use polling |
|---|---|---|
| Bidirectional (chat · collaborative editing) | Server → client only (feeds · notifications) | Infrequent updates (< 1/min) |
| Sub-100ms latency required | One-way push sufficient · auto-reconnect built in | WebSocket infra unavailable |

| Phase | Rule |
|---|---|
| Connect | Authenticate during the handshake. ✗ unauthenticated connections |
| Heartbeat · reconnect | ping/pong every 30 s (dead within 60 s); client exponential backoff 1s → 2s → 4s → 8s → max 30s |
| Message format · size | Structured with a `type` field, ✗ untyped strings; keep < 64 KB, large payloads go over HTTP + a notify message |
| Authority | Server state is the source of truth; client state is an optimistic projection |
| Idempotent + ordered | Handle client resends on reconnect; sequence numbers for ordering + gap detection |
| ✗ WS-only critical state | Persist to the database — the connection is ephemeral |

---

## 13. Core Web Vitals & Performance

Profiling methodology and budget enforcement → [performance](../performance/STANDARDS.md). Server response-time budgets → [api](../api/STANDARDS.md) · [performance](../performance/STANDARDS.md). Web owns the browser-experience metrics.

### Core Web Vitals

INP **replaced FID** as a Core Web Vital in March 2024. Thresholds are the "good" bar at the 75th percentile of field data:

| Metric | Good | Measures |
|---|---|---|
| Largest Contentful Paint (LCP) | ≤ **2.5 s** | Loading — largest element painted |
| Interaction to Next Paint (INP) | ≤ **200 ms** | Responsiveness — worst interaction latency across the visit |
| Cumulative Layout Shift (CLS) | ≤ **0.1** | Visual stability — unexpected layout movement |

Supporting: First Contentful Paint ≤ 1.8 s · Time to First Byte ≤ 0.8 s.

### Frontend Budgets

| Metric | Budget | Enforcement |
|---|---|---|
| Initial JS per route (compressed) | < 100 KB | Build-time bundle analysis |
| Total JS all routes (compressed) | < 300 KB | Build-time |
| CWV | Meet the thresholds above | Field data (RUM) + Lighthouse in CI |

| Technique | Rule |
|---|---|
| Reserve space for media | Width/height or `aspect-ratio` on images/embeds → protects CLS |
| Break up long tasks | Yield to the main thread; defer non-critical JS → protects INP |
| Lazy-load below the fold | Images and non-critical routes load on demand |
| Preload render-critical assets | `<link rel="preload">` for fonts + above-fold hero |
| Prioritize the LCP element | ✗ lazy-load the LCP image; preconnect to its origin |
| Optimize queries behind pages | Index lookups, ✗ table scans → [database](../database/STANDARDS.md) |

---

## 14. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Rendering | CSR SPA | SSR or hybrid by need | SSR + CDN edge rendering |
| Auth | Session cookie | Cookie/token + CSRF (model → [security](../security/STANDARDS.md)) | OAuth 2.0 / OIDC + SSO |
| State | In-memory dev only | DB / distributed cache | Partitioned distributed state |
| Static assets | App server | CDN + content hashing | Multi-region CDN + edge cache |
| Security headers | HTTPS + basic CSP | Full header set + enforced CSP | Per-service CSP + report pipeline |
| Accessibility | Semantic HTML + labels | WCAG 2.2 AA + axe in CI | AA + manual audit + screen-reader QA per release |
| i18n | Externalized strings, one locale | ICU + locale formatting + `Accept-Language` | Full RTL + N locales + translation pipeline |
| Performance | No budgets | CWV + bundle budgets in CI | Per-region RUM monitoring |
| Real-time | Direct connection | Load-balanced + pub/sub | Dedicated WS cluster + broker |

---

## 15. Checklist

- [ ] One primary rendering strategy per app; per-route exceptions explicit
- [ ] Core content and primary actions work without JavaScript
- [ ] Route handlers thin — no business logic in handlers or middleware
- [ ] Middleware ordered per §3; error middleware at the outer edge
- [ ] All input validated at the boundary before reaching domain logic
- [ ] `Content-Type` enforced · body size limits set → 415 / 413
- [ ] `X-Request-Id` generated, propagated, and returned
- [ ] `Cache-Control` set explicitly on every response
- [ ] Static assets content-hashed + immutable; HTML entry point `no-cache`; served via CDN
- [ ] CSP enforced without `unsafe-inline` / `unsafe-eval`; HSTS + `nosniff` set
- [ ] Output context-encoded against XSS; no raw HTML injection without a sanitizer
- [ ] CORS uses an explicit origin allowlist (no wildcard for authenticated APIs)
- [ ] Auth cookies `HttpOnly` · `Secure` · `SameSite`; auth tokens never in `localStorage`
- [ ] CSRF protection on every state-changing request; no state mutation via GET
- [ ] Session ID rotated on login and privilege change; explicit logout destroys it
- [ ] Server re-authorizes every request; frontend gating is UX only
- [ ] Single source of truth per state type; shareable state encoded in the URL
- [ ] Bundle sizes within budget; tree shaking on; code split per route
- [ ] Semantic HTML first; every interactive element keyboard-operable with a visible focus indicator
- [ ] Text contrast ≥ 4.5:1 (normal) / 3:1 (large + UI); color never the sole signal
- [ ] Every form input has an associated label and programmatically linked errors
- [ ] `prefers-reduced-motion` honored; ARIA only where semantic HTML cannot express it
- [ ] axe check gates CI; keyboard + screen-reader walkthrough on primary flows
- [ ] All user-facing strings externalized; plurals/gender via ICU; no concatenated fragments
- [ ] Dates, numbers, and currency formatted per locale; timestamps stored UTC, rendered local
- [ ] RTL supported via logical CSS; layout tolerates ~30-40% text expansion
- [ ] `Accept-Language` negotiated with a persisted explicit user override
- [ ] LCP ≤ 2.5s · INP ≤ 200ms · CLS ≤ 0.1 met on field data
- [ ] Real-time connections authenticated at handshake; critical state persisted, not WS-only
