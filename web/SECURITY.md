# Web Security Standards

> What the browser enforces on a page's behalf: headers, escaping, cross-origin rules, cookies, CSRF, and where a token may live.

**ID** `web/security` · **Tier** Interface · **Version** 1.0
**Owns** security headers · Subresource Integrity · Trusted Types · XSS escaping contexts · CORS · browser token storage · cookie attributes · browser session handling · CSRF · frontend route gating
**Defers to** rendering · routing · middleware · caching · accessibility · i18n · Core Web Vitals → [web](STANDARDS.md) · validation boundary · secrets · access control model → [security](../security/STANDARDS.md) · token format · signing · claims · revocation → [security/TOKENS.md](../security/TOKENS.md) · OAuth + OIDC flow · PKCE · redirect validation → [security/OAUTH.md](../security/OAUTH.md) · token classes + lifetimes + session timeouts → [security §5](../security/STANDARDS.md#5-authentication) · wire contract · status codes · problem details → [api](../api/STANDARDS.md) · TLS termination + CDN config → [devops](../devops/STANDARDS.md)
**Load with** [web](STANDARDS.md) · [security](../security/STANDARDS.md) · [security/TOKENS.md](../security/TOKENS.md)

---

## Table of Contents

1. [Security Headers](#1-security-headers)
2. [XSS Escaping](#2-xss-escaping)
3. [CORS](#3-cors)
4. [Browser Token Storage](#4-browser-token-storage)
5. [Cookie Attributes](#5-cookie-attributes)
6. [Session Handling](#6-session-handling)
7. [CSRF](#7-csrf)
8. [Frontend Route Gating](#8-frontend-route-gating)
9. [Checklist](#9-checklist)

---

XSS injection vectors and CSP are web's to own. The validation boundary + secrets are owned by [security](../security/STANDARDS.md).

## 1. Security Headers

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Explicit allowlist; `default-src 'self'` baseline | Primary XSS defense — restrict script/style/connect origins |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | Force HTTPS |
| `X-Content-Type-Options` | `nosniff` | Stop MIME sniffing |
| `X-Frame-Options` / CSP `frame-ancestors` | `DENY` \| explicit allowlist | Clickjacking defense |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Limit referrer leakage |
| `Permissions-Policy` | Deny unused features explicitly | Camera · mic · geolocation off unless the app uses them |
| `Cross-Origin-Opener-Policy` | `same-origin` | Severs the opener reference · blocks cross-window scripting |
| `Cross-Origin-Resource-Policy` | `same-origin` \| `same-site` | Stops other origins embedding this response |

CSP: ✗ `unsafe-inline` (nonce/hash any inline script) · ✗ `unsafe-eval` · ship `Content-Security-Policy-Report-Only` first, enforce once clean.

| Rule | Detail |
|---|---|
| Subresource Integrity | Every third-party script \| stylesheet loaded by URL carries `integrity` + `crossorigin`. Without it a CDN compromise runs as first-party code, and CSP's origin allowlist still permits it |
| Trusted Types | `require-trusted-types-for 'script'` where browser support allows · removes DOM XSS sinks by construction rather than by escaping discipline |
| Report before enforce | Applies to every header above, ✗ CSP alone. A header enforced blind breaks the app for users before it is measured |

## 2. XSS Escaping

| Context | Encoding |
|---|---|
| HTML body | HTML-entity encode |
| HTML attribute | Attribute-encode + always quote |
| JS string / JSON in page | JS-encode; ✗ interpolate untrusted data into a `<script>` |
| URL parameter | URL-encode; validate the scheme — ✗ `javascript:` |
| CSS value | CSS-encode |

Encode on output per context (auto-escaping template engine, encoding matches the sink). ✗ raw HTML injection — `innerHTML` / `dangerouslySetInnerHTML` only through a sanitizer allowlist; build DOM via framework binding or `textContent`, ✗ from strings.

## 3. CORS

Runs at middleware position 4 (§3) — before authentication.

| Rule | Detail |
|---|---|
| Explicit allowed origins | Allowlist specific origins. ✗ `Access-Control-Allow-Origin: *` for authenticated APIs — wildcard only for public, unauthenticated, read-only APIs |
| Credentials mode | `Access-Control-Allow-Credentials: true` requires a specific origin — ✗ wildcard |
| Methods + headers | List only what the API uses. ✗ allow-all |
| Preflight | Cache with `Access-Control-Max-Age` ≥ 7200 · respond 204 · ✗ require auth on OPTIONS · exempt from rate limiting |

---

## 4. Browser Token Storage

The authn/authz model — RBAC/ABAC, default-deny, resource-level checks, least privilege, **token lifetimes**, secret rotation — is owned by [security](../security/STANDARDS.md). This section covers the web delta only: how credentials live in the browser and how requests are protected. ✗ restate a token lifetime number — token lifetimes (browser-facing and service-to-service classes) are stated in [security](../security/STANDARDS.md).

| Store | Verdict |
|---|---|
| `HttpOnly` cookie | Preferred for session credentials — unreachable from JS |
| In-memory (JS variable) | Acceptable for a short-lived access token in an SPA — lost on reload, refreshed via cookie |
| `localStorage` / `sessionStorage` | ✗ for auth tokens — any XSS reads them |

Rely on refresh-token rotation (one-time use) for session continuity; lifetimes and rotation policy → [security](../security/STANDARDS.md).

## 5. Cookie Attributes

| Attribute | Value | Reason |
|---|---|---|
| `HttpOnly` | `true` | ✗ JavaScript access to auth cookies |
| `Secure` | `true` | HTTPS transmission only |
| `SameSite` | `Lax` minimum · `Strict` for sensitive operations | CSRF mitigation |
| `Domain` | Narrowest explicit scope | ✗ overly broad |
| `Path` | `/` or narrower | Limit scope |
| `Max-Age` / `Expires` | Explicit, matching session policy | ✗ non-expiring session cookies |
| `__Host-` prefix | For host-locked session cookies | Binds the cookie to the exact host + path |

## 6. Session Handling

| Rule | Detail |
|---|---|
| Store server-side | Session data in a database or encrypted cache. ✗ store session state in the cookie payload |
| Cookie carries the ID only | Opaque session identifier |
| Rotate on privilege change | New session ID on login and on role change — defeats fixation |
| Absolute + idle expiry | Absolute cap (24 h default) + sliding idle window |
| Explicit logout | Destroys the server-side session. ✗ rely on cookie expiry alone |
| Purge expired sessions | Scheduled cleanup. ✗ unbounded store growth |

## 7. CSRF

| Rule | Detail |
|---|---|
| Synchronizer token | Per-session token embedded in forms, validated on every state-changing submit |
| Double-submit cookie | Alternative: random value in a cookie + matching header, server compares |
| `SameSite` is defense-in-depth | ✗ sole CSRF defense — legacy browsers and some flows bypass it |
| Safe methods exempt | GET · HEAD · OPTIONS carry no CSRF token — they must not mutate state |
| ✗ state mutation via GET | ✗ `/delete?id=5` over GET |

## 8. Frontend Route Gating

| Rule | Detail |
|---|---|
| UI gating is UX, not security | Hide/disable what the user can't use — the server re-authorizes every request regardless |
| Route guards | Auth/permission checks before a route renders; unauthenticated → redirect to login |
| ✗ permission logic in components | Centralize evaluation → components consume boolean results |

---

## 9. Checklist

- [ ] `Content-Security-Policy` is set with an explicit allowlist and a `default-src 'self'` baseline
- [ ] CSP contains neither `unsafe-inline` nor `unsafe-eval`; inline scripts carry a nonce or hash
- [ ] CSP shipped in report-only mode first and was enforced only once clean
- [ ] `Strict-Transport-Security`, `X-Content-Type-Options`, `Referrer-Policy` and `frame-ancestors` are set
- [ ] `Permissions-Policy` denies features the application does not use
- [ ] `Cross-Origin-Opener-Policy` and `Cross-Origin-Resource-Policy` are set
- [ ] Every third-party script and stylesheet carries Subresource Integrity with `crossorigin`
- [ ] Trusted Types are required for script sinks where browser support allows
- [ ] Output is escaped for its context — HTML, attribute, JS, URL, CSS — not escaped once generically
- [ ] CORS rejects disallowed origins rather than reflecting the request origin
- [ ] No token is stored in `localStorage` or `sessionStorage`
- [ ] Session cookies set `Secure`, `HttpOnly` and `SameSite`
- [ ] The session identifier is regenerated on login, logout and privilege change
- [ ] Logout invalidates the session server-side rather than deleting a client-side value
- [ ] State-changing requests carry CSRF protection, or rely on `SameSite` deliberately and documented
- [ ] Frontend route gating is treated as presentation only, with the real check server-side
