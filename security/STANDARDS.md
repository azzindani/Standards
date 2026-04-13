# Security Standards

Rules for application-level security across all projects, all languages.
Defines validation boundaries, access control, secrets handling, and
data protection. ✗ infrastructure security (→ `devops/STANDARDS.md`).
✗ language-specific security libraries (→ language-specific standards).
✗ API protocol security details (→ `api/STANDARDS.md`).

Composable with: Architecture Standards, API Standards, Database Standards,
Observability Standards, and language-specific standards.

---

## Table of Contents

1. [Input Validation](#1-input-validation)
2. [Injection Prevention](#2-injection-prevention)
3. [Authentication](#3-authentication)
4. [Authorization](#4-authorization)
5. [Secrets Management](#5-secrets-management)
6. [Data Protection](#6-data-protection)
7. [Dependency Security](#7-dependency-security)
8. [Path & File Security](#8-path--file-security)
9. [Subprocess Security](#9-subprocess-security)
10. [Output Encoding](#10-output-encoding)
11. [Error Information Exposure](#11-error-information-exposure)
12. [Security Headers & Transport](#12-security-headers--transport)
13. [Audit & Logging](#13-audit--logging)
14. [Scale Matrix](#14-scale-matrix)
15. [Security Checklist](#15-security-checklist)

---

## 1. Input Validation

All external input is hostile until validated. Validation happens once,
at the Tier 3 boundary (see `architecture/STANDARDS.md` §2). Tiers 0–2
operate on validated data only — no re-validation inside core logic.

### Validation Boundary

| Rule | Detail |
|---|---|
| Validate at entry | Every Tier 3 adapter validates all input before passing inward |
| Trust internally | Tiers 0–2 receive validated types, not raw strings |
| Parse, don't validate | Convert raw input into typed domain objects at boundary; reject if conversion fails |
| Fail closed | Invalid input → reject. ✗ attempt to "fix" malformed input |
| Allowlist over denylist | Define what IS valid. ✗ enumerate what is invalid — attackers find gaps |

### Validation Rules

| Input type | Validation |
|---|---|
| Strings | Max length · allowed character set · encoding (UTF-8) |
| Numbers | Range (min/max) · type (integer vs float) · no NaN/Infinity |
| Dates/times | Format · range · timezone presence |
| Enums | Exact match against allowed values |
| Collections | Max size · element validation · no duplicates where required |
| File uploads | Max size · allowed MIME types · content verification (✗ trust extension alone) |
| Identifiers | Format (UUID, slug) · existence check at service layer |
| URLs | Scheme allowlist (https) · ✗ file:// · ✗ internal IPs (SSRF) |
| Email | RFC 5321 format · max length |

### Compound Validation

Validate individual fields first, then cross-field constraints. Return
all validation errors at once — ✗ stop at first failure (see
`architecture/STANDARDS.md` §7, partial failure).

---

## 2. Injection Prevention

Every injection attack exploits the same root cause: mixing data with
control instructions. Prevention: never concatenate user input into
structured languages.

### Injection Types & Prevention

| Attack vector | Prevention | ✗ Never |
|---|---|---|
| SQL injection | Parameterized queries · prepared statements | ✗ string concatenation in queries |
| Command injection | Structured subprocess APIs · argument arrays | ✗ shell string interpolation |
| Path traversal | Resolve + validate against allowed root | ✗ raw user input in file paths |
| XSS (reflected) | Context-aware output encoding | ✗ raw user data in HTML |
| XSS (stored) | Encode on output · sanitize on input | ✗ trust stored data as safe |
| LDAP injection | Parameterized LDAP queries · escape special chars | ✗ concatenate user input in LDAP filters |
| Template injection | Logic-less templates · ✗ user input as template code | ✗ eval user strings |
| Header injection | Strip newlines from header values | ✗ raw input in HTTP headers |
| XML injection | Disable external entities (XXE) · use safe parsers | ✗ parse untrusted XML with DTD enabled |

### Core Rule

Data and code occupy separate channels. User input is always data —
it flows through parameterized APIs, never through string interpolation
into executable contexts.

---

## 3. Authentication

### Principles

| Rule | Detail |
|---|---|
| Authentication at edge | Verify identity in Tier 3 before any request reaches Tier 2 |
| One canonical method | Single authentication mechanism per interface; ✗ mix methods |
| Fail closed | Unauthenticated requests → reject. ✗ default to anonymous access |
| Rate limit auth attempts | Brute-force protection: exponential backoff after N failures |
| Multi-factor for privileged ops | Elevated operations require additional verification |

### Token Handling

| Rule | Detail |
|---|---|
| Tokens are opaque to client | Client stores, never parses or modifies tokens |
| Short-lived access tokens | Expiry ≤ 1 hour for access tokens |
| Refresh tokens: long-lived, rotatable | Single-use refresh tokens; revoke on reuse detection |
| Signed tokens | Cryptographic signature verification on every request |
| ✗ tokens in URLs | Tokens in headers only; URLs leak via logs, referrer, browser history |
| ✗ symmetric signing in distributed systems | Use asymmetric keys when multiple services verify tokens |

### Session Management

| Rule | Detail |
|---|---|
| Server-side session state | Session data on server; client holds only session ID |
| Regenerate session ID on auth change | New session ID after login, logout, privilege elevation |
| Absolute + idle timeout | Sessions expire after max lifetime AND after idle period |
| Secure cookie attributes | `Secure` · `HttpOnly` · `SameSite=Strict|Lax` · domain-scoped |
| Invalidate on logout | Destroy session server-side; ✗ rely on client-side deletion |

### Password Rules (when applicable)

| Rule | Detail |
|---|---|
| Hash with modern algorithm | bcrypt · scrypt · Argon2 — with per-user salt |
| ✗ store plaintext or reversible encryption | |
| Minimum length 12+ characters | ✗ maximum length below 64 |
| ✗ composition rules | ✗ require uppercase/special — length matters more |
| Check against breach databases | Reject known-compromised passwords |

---

## 4. Authorization

Authentication proves WHO. Authorization decides WHAT they can do.
Enforce authorization in Tier 2 (service layer) after authentication
completes in Tier 3. See `architecture/STANDARDS.md` §2.

### Access Control Models

| Model | Use when | Mechanism |
|---|---|---|
| RBAC (Role-Based) | Fixed roles with predictable permissions | User → Role → Permissions |
| ABAC (Attribute-Based) | Context-dependent decisions (time, location, resource state) | Policy engine evaluates attributes |
| Capability-Based | Fine-grained, delegatable permissions | Caller holds unforgeable capability token |
| ACL (Access Control List) | Per-resource permission lists | Resource → list of (subject, permission) |

Choose one model per system. ✗ mix models unless clear boundary between subsystems.

### Principles

| Rule | Detail |
|---|---|
| Least privilege | Grant minimum permissions required for task. ✗ broad defaults |
| Deny by default | No permission → denied. Every access requires explicit grant |
| Check on every request | ✗ cache authorization decisions across requests unless TTL-bounded |
| Separate from business logic | Authorization checks in service layer, not embedded in domain logic |
| Resource-level checks | Verify access to specific resource, not just resource type |
| Time-bound elevation | Temporary privilege grants expire automatically |

### Capability-Based Security

| Rule | Detail |
|---|---|
| Capabilities are unforgeable tokens | Cryptographically signed or server-validated references |
| Attenuable | Holder can create restricted sub-capabilities; ✗ escalate |
| Revocable | System can invalidate capabilities without revoking all access |
| Transfer-explicit | Capability delegation is audited and intentional |

### Multi-Tenancy

| Rule | Detail |
|---|---|
| Tenant isolation at query level | Every data query scoped to tenant; ✗ rely on application-layer filtering alone |
| Tenant context propagated | Tenant ID injected at Tier 3, flows through all layers |
| Cross-tenant access = explicit exception | Requires separate authorization path, fully audited |

---

## 5. Secrets Management

Secrets: API keys, database credentials, encryption keys, certificates,
tokens. See `architecture/STANDARDS.md` §8 — secrets never in committed
files; enter through environment at Tier 3; derived values (authenticated
clients, connections) flow inward, raw secrets do not.

### Storage & Access

| Rule | Detail |
|---|---|
| ✗ secrets in source code | Not in code, config files, comments, or commit history |
| ✗ secrets in logs | Mask/redact before logging; ✗ log request bodies containing credentials |
| ✗ secrets in URLs | Query parameters logged by proxies, browsers, CDNs |
| ✗ secrets in error messages | Stack traces and error details must never expose secret values |
| Environment variables or vault | Secrets injected at runtime, never baked into artifacts |
| Separate from config | Secrets ≠ configuration; different storage, different access control |

### Lifecycle

| Phase | Rule |
|---|---|
| Generation | Use cryptographically secure random generators; ✗ predictable values |
| Rotation | Automated rotation on schedule; support concurrent old+new during transition |
| Revocation | Immediate invalidation capability; revoked secrets fail instantly |
| Expiry | All secrets have maximum lifetime; ✗ indefinite credentials |
| Audit | Log secret access (who, when, which); ✗ log secret values |

### Derived Values Pattern

Raw secrets stay in Tier 3. Pass derived values inward:

| ✗ Pass inward | Pass inward instead |
|---|---|
| Database password | Authenticated connection object |
| API key | Configured HTTP client |
| Encryption key bytes | Encryption service instance |
| Certificate file path | TLS-configured transport |

Core logic (Tiers 0–2) never sees, stores, or logs raw secret material.

---

## 6. Data Protection

### Data Classification

| Level | Examples | Handling |
|---|---|---|
| Public | Marketing content, open docs | No restrictions |
| Internal | Business data, internal reports | Access control required |
| Confidential | User data, financial records | Encryption + access control + audit |
| Restricted | PII, health data, credentials | Encryption + strict access + audit + retention limits |

Classify data at creation. Classification drives encryption, access,
retention, and logging decisions.

### Encryption

| Context | Rule |
|---|---|
| In transit | TLS 1.2+ for all network communication; ✗ plaintext protocols |
| At rest | Encrypt Confidential and Restricted data; AES-256 or equivalent |
| Key management | Separate encryption keys from encrypted data; rotate keys on schedule |
| ✗ custom crypto | Use established libraries and algorithms; ✗ invent cryptographic schemes |
| Hash integrity | SHA-256+ for integrity verification; ✗ MD5, ✗ SHA-1 |

### PII Handling

| Rule | Detail |
|---|---|
| Minimize collection | Collect only PII required for function; ✗ "nice to have" fields |
| Purpose limitation | PII used only for stated purpose; ✗ repurpose without consent |
| Retention limits | Define and enforce maximum retention period per data type |
| Right to deletion | System supports complete removal of individual's PII |
| Pseudonymization | Replace identifying fields with tokens where full identity unnecessary |
| ✗ PII in logs | Mask, hash, or omit PII from log entries |
| ✗ PII in error messages | Error context must not expose personal data |

### Data Sanitization

| When | Action |
|---|---|
| Data deletion | Overwrite or crypto-erase; ✗ rely on filesystem delete alone |
| Decommissioning storage | Wipe all media before disposal or return |
| Test environments | Use synthetic data or anonymized production data; ✗ raw production PII |

---

## 7. Dependency Security

Third-party code = third-party risk. Every dependency is an implicit
trust grant. See `architecture/STANDARDS.md` §3 — wrap externals,
pin versions, update deliberately.

### Vulnerability Management

| Rule | Detail |
|---|---|
| Automated scanning | Run vulnerability scanner on every build; block deploy on critical/high CVEs |
| Audit command | Every project has one-command dependency audit (language-specific tool) |
| Fix window | Critical: 24 hours · High: 7 days · Medium: 30 days · Low: next release |
| Transitive dependencies | Scan full dependency tree, not just direct dependencies |

### Supply Chain

| Rule | Detail |
|---|---|
| Lock files committed | Exact resolved versions in lock file; reproducible builds |
| Verify checksums | Package manager verifies integrity hashes on install |
| ✗ install from unverified sources | Official registries only; ✗ arbitrary URLs or forks |
| Review new dependencies | Evaluate: maintenance status, download count, known issues, license |
| Minimize dependency count | Every dependency = attack surface. Prefer standard library where adequate |

### Update Cadence

| Dependency type | Update frequency |
|---|---|
| Security patches | Immediately upon availability |
| Minor/patch versions | Monthly review |
| Major versions | Quarterly evaluation; test before upgrade |
| Deprecated dependencies | Replace before EOL |

---

## 8. Path & File Security

File operations are Tier 3 I/O (see `architecture/STANDARDS.md` §2).
Path security prevents directory traversal and unauthorized file access.

### Path Traversal Prevention

| Rule | Detail |
|---|---|
| Resolve then validate | Canonicalize path (resolve symlinks, `..`, `.`) → check against allowed root |
| Allowed root enforcement | Every file operation scoped to declared root directory; ✗ unrestricted filesystem access |
| ✗ raw user input in paths | User-supplied filenames validated against allowlist pattern |
| Reject path separators | User-supplied names: ✗ `/` · ✗ `\` · ✗ `..` · ✗ null bytes |
| Canonical comparison | Compare resolved absolute paths; ✗ string prefix matching on raw input |

### Symlink Rules

| Rule | Detail |
|---|---|
| Resolve before access | Follow symlinks to final target; validate target is within allowed root |
| ✗ create symlinks from user input | User-controlled symlink targets enable escapes |
| TOCTOU awareness | Check-then-use on paths is race-prone; use atomic open-and-verify where possible |

### File Permissions

| Rule | Detail |
|---|---|
| Least privilege | Files created with minimum necessary permissions |
| Sensitive files restrictive | Credentials, keys: owner-read only (0600) |
| Temp files in secure location | System temp directory with restricted permissions; cleanup after use |
| ✗ world-writable output | ✗ create files writable by all users |

---

## 9. Subprocess Security

Subprocesses are Tier 3 operations. Every subprocess call is a potential
command injection vector.

### Rules

| Rule | Detail |
|---|---|
| ✗ shell interpolation | ✗ pass user input through shell strings |
| Argument arrays | Pass command + arguments as array/list, not single string |
| Allowlist commands | Permitted executables defined in configuration; ✗ arbitrary commands |
| ✗ shell=true with user input | Shell mode enables metacharacter expansion; use only for static commands |
| Validate arguments | Each argument validated against expected format before execution |
| Restrict PATH | Subprocess inherits minimal environment; explicit executable paths preferred |
| Timeout enforcement | Every subprocess has maximum execution time; kill on timeout |
| Capture and validate output | Subprocess output is untrusted data; validate before use |

### Environment Inheritance

| Rule | Detail |
|---|---|
| Minimal environment | Pass only required environment variables to subprocess |
| ✗ inherit secrets | Subprocess environment ✗ includes parent's secret variables unless explicitly needed |
| Sanitize inherited values | Strip control characters from any inherited environment variable |

---

## 10. Output Encoding

User-supplied data rendered in any output context requires context-aware
encoding. Encoding prevents stored/reflected XSS and format injection.

### Context-Specific Encoding

| Output context | Encoding rule |
|---|---|
| HTML body | HTML-entity encode: `<>&"'` |
| HTML attributes | Attribute-encode; always quote attribute values |
| JavaScript context | JavaScript-encode; ✗ inline user data in `<script>` blocks |
| CSS context | CSS-encode; ✗ user data in style attributes or `<style>` blocks |
| URL parameters | Percent-encode (URL-encode) all user values |
| JSON responses | Proper JSON serialization; ✗ string concatenation to build JSON |
| SQL (as fallback) | Parameterized queries preferred (§2); encoding as defense-in-depth only |
| Log entries | Strip/escape control characters; prevent log injection |
| Shell display | Strip ANSI escape sequences from untrusted data |

### Principles

| Rule | Detail |
|---|---|
| Encode on output, not input | Store data in original form; encode at render time for correct context |
| ✗ double encoding | Apply encoding exactly once per output context |
| ✗ raw user data in any output | Every output path requires explicit encoding step |
| Framework auto-encoding | Use framework's built-in encoding; verify it covers the specific context |

---

## 11. Error Information Exposure

Errors are an information leak vector. Internal details help attackers
map system internals. See `architecture/STANDARDS.md` §7 for error
architecture.

### Rules

| Rule | Detail |
|---|---|
| ✗ stack traces to users | Stack traces in logs only; user sees generic message |
| ✗ internal paths in errors | File paths, class names, module structure → logs, not response |
| ✗ database details in errors | Query text, table names, column names → logs, not response |
| ✗ version info in errors | Software versions, framework names → not in error responses |
| ✗ dependency names in errors | Third-party library names/versions → logs only |
| Error IDs for correlation | Return opaque error ID to user; full details in logs keyed by same ID |
| Different detail by environment | Development: verbose errors · Production: generic messages + error ID |

### Error Response Pattern

| Component | User-facing response | Internal log |
|---|---|---|
| Message | Generic, actionable ("Request failed") | Full technical detail |
| Error ID | Unique correlation ID | Same correlation ID |
| Stack trace | ✗ never | Full trace |
| Input data | ✗ never echoed raw | Sanitized copy (mask PII/secrets) |
| Remediation | Generic ("try again", "contact support") | Specific fix needed |

---

## 12. Security Headers & Transport

Applies to web-facing interfaces (HTTP APIs, web applications).

### Transport

| Rule | Detail |
|---|---|
| HTTPS everywhere | TLS 1.2+ for all endpoints; ✗ plaintext HTTP in production |
| HSTS enabled | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| Certificate validation | Verify full chain; ✗ disable certificate checks (even in staging) |
| TLS configuration | Disable SSLv3, TLS 1.0, TLS 1.1; prefer forward-secrecy cipher suites |

### Security Headers

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Restrictive policy; ✗ `unsafe-inline`, ✗ `unsafe-eval` | XSS mitigation |
| `X-Content-Type-Options` | `nosniff` | Prevent MIME-type sniffing |
| `X-Frame-Options` | `DENY` or `SAMEORIGIN` | Clickjacking prevention |
| `Referrer-Policy` | `strict-origin-when-cross-origin` or `no-referrer` | Referrer leak prevention |
| `Permissions-Policy` | Disable unused browser features (camera, mic, geolocation) | Feature restriction |
| `Cache-Control` | `no-store` for sensitive responses | Prevent caching of secrets/PII |

### CORS

| Rule | Detail |
|---|---|
| ✗ `Access-Control-Allow-Origin: *` for authenticated endpoints | Wildcard origin incompatible with credentials |
| Allowlist specific origins | Validate `Origin` header against configured list |
| Restrict methods and headers | Allow only required HTTP methods and custom headers |
| Preflight caching | `Access-Control-Max-Age` set to reduce preflight requests |
| Credentials explicit | `Access-Control-Allow-Credentials: true` only when cookies/auth needed |

### Request Protection

| Rule | Detail |
|---|---|
| CSRF protection | State-changing requests require anti-CSRF token or SameSite cookies |
| Request size limits | Maximum body size enforced at web server/framework level |
| Rate limiting | Per-client rate limits on all endpoints; stricter on auth endpoints |
| Request timeout | Maximum request processing time; kill long-running requests |

---

## 13. Audit & Logging

Security events require dedicated logging separate from application
logs. Cross-reference `observability/STANDARDS.md` for general logging
standards.

### Security Events to Log

| Event category | Examples |
|---|---|
| Authentication | Login success/failure · logout · token refresh · token revocation |
| Authorization | Access denied · privilege elevation · role change |
| Data access | Read/write of Confidential/Restricted data · bulk export |
| Configuration change | Permission change · security setting modification · secret rotation |
| Input validation failure | Rejected requests · repeated validation failures from same source |
| Administrative actions | User create/delete · role assignment · system configuration |
| Anomalies | Unusual access patterns · impossible travel · concurrent sessions |

### Log Content

| Include | ✗ Exclude |
|---|---|
| Timestamp (UTC, ISO 8601) | Passwords or credentials |
| Actor identity (user ID, service ID) | Raw secret values |
| Action performed | Full PII (hash or mask) |
| Resource affected | Session tokens |
| Source IP / request ID | Encryption keys |
| Outcome (success/failure) | Internal file paths (in user-facing logs) |
| Correlation ID | |

### Log Protection

| Rule | Detail |
|---|---|
| Immutable storage | Security logs written to append-only storage; ✗ modifiable after write |
| Access restricted | Security logs readable by security team only; ✗ general access |
| Retention policy | Minimum retention per compliance requirements; default 1 year |
| Tamper detection | Integrity verification (checksums, hash chains) on log entries |
| Separate from application logs | Security audit trail distinct from operational logging |

---

## 14. Scale Matrix

Apply security rules proportionally to project scale.

| Security area | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Input validation (§1) | Type checking at entry | Full validation at boundary | Schema validation + rate limiting |
| Injection prevention (§2) | Parameterized queries | All injection types covered | Automated scanning + WAF |
| Authentication (§3) | Basic/API key | Token-based with expiry | MFA + short-lived tokens + rotation |
| Authorization (§4) | Single role | RBAC | RBAC/ABAC + per-resource checks |
| Secrets management (§5) | Environment variables | Vault/encrypted config | Automated rotation + audit trail |
| Data protection (§6) | TLS in transit | + encryption at rest | + classification + PII controls |
| Dependency security (§7) | Manual audit | Automated scanning | Block on CVE + SLA fix windows |
| Path security (§8) | Basic validation | Allowed root enforcement | + symlink resolution + TOCTOU |
| Subprocess security (§9) | Argument arrays | + command allowlist | + minimal environment + timeout |
| Output encoding (§10) | Framework defaults | Context-specific encoding | + CSP + automated XSS testing |
| Error exposure (§11) | Generic messages | + error IDs | + per-environment detail levels |
| Headers & transport (§12) | HTTPS | + basic security headers | Full header suite + CORS + CSRF |
| Audit logging (§13) | Auth events only | + access denied + data access | Full security event logging + immutable storage |

### Scale Transitions

When graduating from one scale to the next, prioritize in order:
1. Input validation + injection prevention (highest attack surface)
2. Authentication + authorization (access control)
3. Secrets management (credential protection)
4. Everything else (defense in depth)

---

## 15. Security Checklist

### New Project

- [ ] Data classification defined for all data types
- [ ] Input validation at Tier 3 boundary for all external input
- [ ] Parameterized queries for all database access
- [ ] Authentication mechanism selected and implemented at edge
- [ ] Authorization model chosen; deny-by-default enforced
- [ ] Secrets in environment variables or vault; ✗ in code or config files
- [ ] TLS enabled for all network communication
- [ ] Dependency vulnerability scanning in build pipeline
- [ ] Error responses expose no internal details in production
- [ ] Security audit logging for auth events

### New Feature / Endpoint

- [ ] All input validated against explicit schema
- [ ] No string concatenation into SQL, shell, HTML, or template contexts
- [ ] Authorization check on every access path (including direct object references)
- [ ] Output encoding applied for target context
- [ ] Secrets used only in Tier 3; derived values passed inward
- [ ] File paths validated against allowed root
- [ ] Subprocess arguments passed as arrays; commands on allowlist
- [ ] Error responses return correlation ID, not internal details
- [ ] Security-relevant actions logged with actor, action, resource, outcome

### Pre-Release Review

- [ ] Dependency audit: zero critical/high CVEs
- [ ] Security headers configured for all HTTP responses
- [ ] CORS policy restricts origins to known allowlist
- [ ] CSRF protection on state-changing endpoints
- [ ] Rate limiting on authentication and public endpoints
- [ ] Session management: secure cookies, timeouts, server-side invalidation
- [ ] PII handling: minimized, encrypted, retention-limited
- [ ] No stack traces, internal paths, or version info in production responses
- [ ] Security logs: immutable, access-restricted, retained per policy
- [ ] Secrets rotation process documented and tested
