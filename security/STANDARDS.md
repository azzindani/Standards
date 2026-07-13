# Security Standards

> Application-level security for every project: the validation boundary, access control, secrets, and supply-chain integrity every input and credential passes through.

**ID** `security` · **Tier** Core · **Version** 1.0
**Owns** input-validation boundary · injection prevention · authn/authz (RBAC/ABAC · token lifetimes · default-deny) · secrets (token classes · rotation cadence · derived values) · PII/data protection · supply-chain integrity (SLSA · SBOM) · output encoding · transport/TLS · security audit events
**Defers to** tier/layer model → [architecture](../architecture/STANDARDS.md) · error taxonomy + boundaries → [error_handling](../error_handling/STANDARDS.md) · structured log format + retention → [observability](../observability/STANDARDS.md) · license policy → [dependencies](../dependencies/STANDARDS.md) · config cascade → [configuration](../configuration/STANDARDS.md) · vault/injection mechanics → [devops](../devops/STANDARDS.md) · pipeline secret scoping → [cicd](../cicd/STANDARDS.md) · cookie/CSRF/frontend gating → [web](../web/STANDARDS.md) · API protocol specifics → [api](../api/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [observability](../observability/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Input Validation Boundary](#2-input-validation-boundary)
3. [Injection Prevention](#3-injection-prevention)
4. [Output Encoding](#4-output-encoding)
5. [Authentication](#5-authentication)
6. [Authorization](#6-authorization)
7. [Secrets Management](#7-secrets-management)
8. [Data Protection & PII](#8-data-protection--pii)
9. [Supply-Chain Security](#9-supply-chain-security)
10. [Filesystem & Subprocess Security](#10-filesystem--subprocess-security)
11. [Error & Information Exposure](#11-error--information-exposure)
12. [Transport & Headers](#12-transport--headers)
13. [Audit & Logging](#13-audit--logging)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Fail closed | Any ambiguity → deny. ✗ default to allow/anonymous/verbose |
| Allowlist over denylist | Define what IS valid; ✗ enumerate what is invalid — attackers find gaps |
| Defense in depth | No single control is trusted alone; layer validation, encoding, access control |
| Least privilege | Every actor, token, process, file gets the minimum grant for its task |
| Data ≠ code | User input is always data; it never enters an executable/structured channel raw |
| Secure by default | The safe path is the default path; unsafe behavior requires explicit opt-in |

Benchmark against **OWASP Top 10:2025** (A01 Broken Access Control · A02 Security Misconfiguration · A03 Software Supply Chain Failures · A04 Cryptographic Failures · A05 Injection · A06 Insecure Design · A07 Authentication Failures · A08 Software/Data Integrity Failures · A09 Logging & Alerting Failures · A10 Mishandling of Exceptional Conditions), **CWE Top 25 (2025)** (top weaknesses: XSS · SQLi · CSRF · missing authorization · out-of-bounds write), and **OWASP ASVS 5.0** verification levels (L1 automatable baseline · L2 default for apps handling sensitive data · L3 high-assurance/critical).

---

## 2. Input Validation Boundary

All external input is hostile until validated. Validation happens **once**, at the Tier 3 boundary ([architecture §2](../architecture/STANDARDS.md)). Tiers 0–2 operate on validated typed data only — ✗ re-validate inside core logic. This standard owns the boundary rule; each other standard keeps only its own injection vectors (§3).

### Boundary Rules

| Rule | Detail |
|---|---|
| Validate at entry | Every Tier 3 adapter validates all input before passing inward |
| Trust internally | Tiers 0–2 receive validated types, not raw strings |
| Parse, don't validate | Convert raw input into typed domain objects at the boundary; reject if conversion fails |
| Fail closed | Invalid input → reject. ✗ attempt to "fix" malformed input |
| Allowlist | Define the valid set; reject everything else |

### Per-Type Rules

| Input type | Validation |
|---|---|
| Strings | Max length · allowed charset · UTF-8 encoding |
| Numbers | Range (min/max) · integer vs float · ✗ NaN/Infinity |
| Dates/times | Format · range · timezone presence |
| Enums | Exact match against allowed values |
| Collections | Max size · element validation · no duplicates where required |
| File uploads | Max size · allowed MIME · content verification (✗ trust extension) |
| Identifiers | Format (UUID, slug) · existence check at service layer |
| URLs | Scheme allowlist (https) · ✗ `file://` · ✗ internal IPs (SSRF) |
| Email | RFC 5321 format · max length |

Validate individual fields first, then cross-field constraints. Return **all** validation errors at once — ✗ stop at first failure. Validation produces data errors (structured results, ✗ thrown) → [error_handling §9](../error_handling/STANDARDS.md).

---

## 3. Injection Prevention

Every injection exploits the same root cause: mixing data with control instructions. Prevention: never concatenate user input into a structured language.

| Vector | Prevention | ✗ Never |
|---|---|---|
| SQL | Parameterized queries · prepared statements | ✗ string concatenation in queries |
| Command | Structured subprocess APIs · argument arrays | ✗ shell string interpolation |
| Path traversal | Resolve + validate against allowed root | ✗ raw user input in file paths |
| XSS (reflected/stored) | Context-aware output encoding (§4) | ✗ raw user data in HTML |
| LDAP | Parameterized queries · escape special chars | ✗ concatenate input in LDAP filters |
| Template (SSTI) | Logic-less templates | ✗ user input as template code · ✗ eval |
| Header | Strip newlines from header values | ✗ raw input in HTTP headers |
| XML (XXE) | Disable external entities · safe parser | ✗ parse untrusted XML with DTD enabled |
| Deserialization | Typed schema · allowlist classes | ✗ deserialize untrusted data into arbitrary types |

Core rule: data and code occupy separate channels. User input flows through parameterized APIs, never through interpolation into an executable context.

---

## 4. Output Encoding

User-supplied data rendered in any output context requires context-aware encoding at render time.

| Output context | Encoding rule |
|---|---|
| HTML body | HTML-entity encode `<>&"'` |
| HTML attribute | Attribute-encode; always quote values |
| JavaScript | JS-encode; ✗ inline user data in `<script>` |
| CSS | CSS-encode; ✗ user data in style blocks |
| URL parameter | Percent-encode all user values |
| JSON | Proper serialization; ✗ concatenate to build JSON |
| Log entry | Strip/escape control chars — prevent log injection |
| Shell display | Strip ANSI escape sequences from untrusted data |

| Rule | Detail |
|---|---|
| Encode on output, not input | Store original form; encode at render for the target context |
| Encode exactly once | ✗ double encoding |
| Every output path encodes | ✗ raw user data in any output |
| Prefer framework auto-encoding | Verify it covers the specific context |

---

## 5. Authentication

Authentication proves WHO. Verify identity in Tier 3 before any request reaches Tier 2. This standard owns token lifetimes and classes; `web` keeps cookie attributes/CSRF, `api` keeps protocol specifics.

### Principles

| Rule | Detail |
|---|---|
| Authenticate at edge | Identity verified in Tier 3 before request reaches Tier 2 |
| One canonical method | Single mechanism per interface; ✗ mix methods |
| Fail closed | Unauthenticated → reject. ✗ default to anonymous |
| Rate-limit attempts | Exponential backoff after N failures; brute-force protection |
| MFA for privileged ops | Elevated operations require additional verification |

### Token Classes & Lifetime (! canonical)

Two access-token classes — both apply, scope decides which. ✗ collapse into one number.

| Token class | Max lifetime | Rule |
|---|---|---|
| Browser / user-facing access token | ≤ 15 min | Pair with refresh-token rotation |
| Service-to-service access token | ≤ 1 h | No interactive user; issued per service identity |
| Refresh token | Long-lived, single-use | Rotate on every use · revoke entire chain on reuse detection |

| Rule | Detail |
|---|---|
| Opaque to client | Client stores, never parses or modifies tokens |
| Signed | Cryptographic signature verified on every request |
| ✗ tokens in URLs | Headers only; URLs leak via logs, referrer, history |
| Asymmetric signing when distributed | ✗ symmetric signing when multiple services verify |

### Session Management

| Rule | Detail |
|---|---|
| Server-side state | Session data on server; client holds only session ID |
| Regenerate on auth change | New session ID after login, logout, privilege elevation |
| Absolute + idle timeout | Expire after max lifetime AND after idle period |
| Invalidate on logout | Destroy server-side; ✗ rely on client-side deletion |

Cookie attributes (`Secure` · `HttpOnly` · `SameSite`) → [web](../web/STANDARDS.md).

### Password Rules

| Rule | Detail |
|---|---|
| Hash with memory-hard algorithm | **Argon2id** (preferred) · scrypt · bcrypt — per-user salt |
| ✗ plaintext or reversible encryption | — |
| Minimum length ≥ 12 | ✗ maximum length below 64 |
| ✗ composition rules | ✗ require uppercase/special — length matters more |
| Check breach databases | Reject known-compromised passwords |

---

## 6. Authorization

Authorization decides WHAT an authenticated identity may do. Enforce in Tier 2 (service layer) after authentication. This standard owns the RBAC/ABAC model, default-deny, least-privilege, and resource-level checks.

### Access-Control Models

| Model | Use when | Mechanism |
|---|---|---|
| RBAC | Fixed roles, predictable permissions | User → Role → Permissions |
| ABAC | Context-dependent (time, location, resource state) | Policy engine evaluates attributes |
| Capability | Fine-grained, delegatable | Caller holds unforgeable capability token |
| ACL | Per-resource permission lists | Resource → (subject, permission) list |

Choose one model per system; ✗ mix unless a clear subsystem boundary separates them.

### Principles

| Rule | Detail |
|---|---|
| Least privilege | Grant the minimum permission for the task; ✗ broad defaults |
| Deny by default | No grant → denied. Every access requires an explicit grant |
| Check on every request | ✗ cache authorization decisions across requests unless TTL-bounded |
| Separate from business logic | Checks in service layer, ✗ embedded in domain logic |
| Resource-level checks | Verify access to the specific resource, not just the type — defeats IDOR |
| Time-bound elevation | Temporary privilege grants expire automatically |

### Capability & Multi-Tenancy

| Rule | Detail |
|---|---|
| Capabilities unforgeable | Cryptographically signed or server-validated references |
| Attenuable, revocable | Holder makes restricted sub-capabilities; ✗ escalate; system can revoke |
| Tenant isolation at query level | Every query scoped to tenant; ✗ rely on app-layer filtering alone |
| Tenant context propagated | Tenant ID injected at Tier 3, flows through all layers |
| Cross-tenant = explicit exception | Separate authorization path, fully audited |

---

## 7. Secrets Management

Secrets: API keys, DB credentials, encryption keys, certificates, tokens. Enter through environment at Tier 3; raw secrets never reach core logic ([architecture §8](../architecture/STANDARDS.md)). This standard owns rotation cadence, token classes, and the derived-values pattern; `configuration` keeps cascade/sourcing, `devops` keeps vault/injection mechanics, `cicd` keeps pipeline scoping, `git` keeps the never-commit rule.

### Storage & Access

| Rule | Detail |
|---|---|
| ✗ secrets in source | Not in code, config files, comments, or commit history |
| ✗ secrets in logs | Mask/redact before logging; ✗ log bodies containing credentials |
| ✗ secrets in URLs | Query params logged by proxies, browsers, CDNs |
| ✗ secrets in errors | Stack traces and error detail never expose secret values |
| Env var or vault | Injected at runtime, never baked into artifacts |
| Separate from config | Secrets ≠ configuration; different storage, different access control |

### Rotation Cadence by Credential Class (! canonical)

Distinct classes carry distinct maximum cadences — both are true. ✗ restate a single flat "rotate every N" elsewhere.

| Credential class | Examples | Max cadence |
|---|---|---|
| Long-lived service-account credential | DB password · service API key · signing key | ≤ 90 days |
| Ephemeral CI / deploy token | OIDC-issued build token · deploy job token | ≤ 24 h (per-run preferred) |
| TLS certificate | Server/client cert | ≤ 90 days (ACME auto-renew) |
| Data encryption key | AES key | Scheduled rotation + re-encryption / envelope keys |

Access-token lifetimes (user ≤ 15 min · service ≤ 1 h) are stated in §5. Prefer short-lived OIDC-issued tokens over long-lived keys for CI/deploy (§9).

### Lifecycle

| Phase | Rule |
|---|---|
| Generation | Cryptographically secure random; ✗ predictable values |
| Rotation | Automated on schedule; support concurrent old+new during transition |
| Revocation | Immediate invalidation; revoked secrets fail instantly |
| Expiry | Every secret has a maximum lifetime; ✗ indefinite credentials |
| Audit | Log secret access (who, when, which); ✗ log secret values |

### Derived-Values Pattern (! sole home)

Raw secrets stay in Tier 3. Pass derived values inward; core logic (Tiers 0–2) never sees, stores, or logs raw secret material.

| ✗ Pass inward | Pass inward instead |
|---|---|
| Database password | Authenticated connection object |
| API key | Configured HTTP client |
| Encryption key bytes | Encryption/cipher service instance |
| Certificate file path | TLS-configured transport |

---

## 8. Data Protection & PII

### Classification

| Level | Examples | Handling |
|---|---|---|
| Public | Marketing content, open docs | No restrictions |
| Internal | Business data, internal reports | Access control |
| Confidential | User data, financial records | Encryption + access control + audit |
| Restricted | PII, health data, credentials | Encryption + strict access + audit + retention limits |

Classify at creation. Classification drives encryption, access, retention, and logging.

### Encryption

| Context | Rule |
|---|---|
| In transit | **TLS 1.3** (TLS 1.2 minimum floor); ✗ plaintext protocols |
| At rest | Encrypt Confidential + Restricted; AES-256 or equivalent |
| Key management | Separate keys from encrypted data; rotate on schedule (§7) |
| ✗ custom crypto | Established libraries + algorithms; ✗ invent schemes |
| Hash integrity | SHA-256+; ✗ MD5, ✗ SHA-1 |

### PII Handling (canonical home)

| Rule | Detail |
|---|---|
| Minimize collection | Only PII required for function; ✗ "nice to have" fields |
| Purpose limitation | Used only for the stated purpose; ✗ repurpose without consent |
| Retention limits | Enforce a maximum retention period per data type |
| Right to deletion | Support complete removal of an individual's PII |
| Pseudonymization | Replace identifying fields with tokens where full identity is unneeded |
| ✗ PII in logs | Mask, hash, or omit — same exclusion set applies to receipts and traces |
| ✗ PII in error messages | Error context must not expose personal data |

Sanitization: deletion → overwrite or crypto-erase (✗ filesystem delete alone) · decommissioned storage → wipe media before disposal/return · test environments → synthetic or anonymized data (✗ raw production PII).

---

## 9. Supply-Chain Security

Every dependency and build artifact is an implicit trust grant (OWASP A03). License policy → [dependencies](../dependencies/STANDARDS.md); pin/wrap/update mechanics → [dependencies](../dependencies/STANDARDS.md).

### Dependency Integrity

| Rule | Detail |
|---|---|
| Lock files committed | Exact resolved versions; reproducible builds |
| Verify checksums | Package manager verifies integrity hashes on install |
| ✗ unverified sources | Official registries only; ✗ arbitrary URLs or forks |
| Block dependency confusion | Pin internal scope/namespace; ✗ let public registry shadow private packages |
| Automated CVE scanning | Scan full tree (transitive included) every build; block deploy on critical/high |
| Fix window | Critical 24 h · High 7 days · Medium 30 days · Low next release |

### Artifact & Build Integrity

| Rule | Detail |
|---|---|
| SBOM per release | Generate a Software Bill of Materials (SPDX/CycloneDX) for every build |
| Sign artifacts + commits | Cryptographically sign released artifacts and commits (Sigstore/GPG); verify on consume |
| Secret scanning | Pre-commit + CI scan blocks committed credentials |
| Target SLSA build integrity | L1 automated provenance · L2 signed provenance from a hosted builder · L3 non-falsifiable provenance from an isolated builder |
| OIDC over long-lived keys | CI/deploy authenticate via short-lived OIDC-issued tokens; ✗ long-lived static keys in CI (reinforces §7 ephemeral class) |
| Least-privilege CI tokens | Pipeline credentials scoped to the single job; ✗ org-wide admin tokens |

---

## 10. Filesystem & Subprocess Security

File and subprocess operations are Tier 3 I/O. Both are command/traversal-injection vectors.

### Path Traversal

| Rule | Detail |
|---|---|
| Resolve then validate | Canonicalize (resolve symlinks, `..`, `.`) → check against allowed root |
| Allowed-root enforcement | Every file op scoped to a declared root; ✗ unrestricted filesystem access |
| ✗ raw user input in paths | User-supplied names validated against an allowlist pattern |
| Reject separators | User names: ✗ `/` · ✗ `\` · ✗ `..` · ✗ null bytes |
| Canonical comparison | Compare resolved absolute paths; ✗ string-prefix match on raw input |
| TOCTOU-aware | Check-then-use is race-prone; atomic open-and-verify where possible |

### File Permissions

| Rule | Detail |
|---|---|
| Least privilege | Files created with minimum necessary permissions |
| Sensitive files restrictive | Credentials/keys: owner-read only (0600) |
| Temp files secure | System temp dir with restricted permissions; clean up after use |
| ✗ world-writable output | ✗ create files writable by all users |

### Subprocess

| Rule | Detail |
|---|---|
| ✗ shell interpolation | ✗ pass user input through shell strings |
| Argument arrays | Command + args as an array/list, not a single string |
| Allowlist commands | Permitted executables in config; ✗ arbitrary commands |
| ✗ `shell=true` with user input | Shell mode expands metacharacters; static commands only |
| Timeout enforcement | Every subprocess has a max execution time; kill on timeout |
| Minimal environment | Pass only required env vars; ✗ inherit parent secrets unless explicitly needed |
| Output is untrusted | Validate subprocess output before use |

---

## 11. Error & Information Exposure

Errors leak internals that help attackers map the system (OWASP A10). Error taxonomy, boundaries, and never-swallow rules → [error_handling](../error_handling/STANDARDS.md); this section covers only what must not reach an external caller.

| Rule | Detail |
|---|---|
| ✗ stack traces to users | Logs only; user sees a generic message |
| ✗ internal paths/class names in responses | → logs |
| ✗ database details in responses | Query text, table/column names → logs |
| ✗ version/dependency names in responses | → logs |
| ✗ raw input echoed | Log a sanitized copy (mask PII/secrets); ✗ echo to user |
| Error IDs for correlation | Return an opaque error ID; full detail in logs keyed by that ID |
| Detail by environment | Development verbose · production generic + error ID |

---

## 12. Transport & Headers

Applies to web-facing interfaces (HTTP APIs, web apps).

### Transport

| Rule | Detail |
|---|---|
| HTTPS everywhere | **TLS 1.3** preferred, TLS 1.2 minimum; ✗ plaintext HTTP in production |
| Disable legacy | ✗ SSLv3 · ✗ TLS 1.0 · ✗ TLS 1.1; prefer forward-secrecy ciphers |
| HSTS | `Strict-Transport-Security: max-age=31536000; includeSubDomains` |
| Certificate validation | Verify full chain; ✗ disable cert checks (even in staging) |

### Security Headers

| Header | Value | Purpose |
|---|---|---|
| `Content-Security-Policy` | Restrictive; ✗ `unsafe-inline`, ✗ `unsafe-eval` | XSS mitigation |
| `X-Content-Type-Options` | `nosniff` | Block MIME sniffing |
| `X-Frame-Options` | `DENY` \| `SAMEORIGIN` | Clickjacking |
| `Referrer-Policy` | `strict-origin-when-cross-origin` \| `no-referrer` | Referrer leak |
| `Permissions-Policy` | Disable unused features (camera, mic, geo) | Feature restriction |
| `Cache-Control` | `no-store` for sensitive responses | ✗ cache secrets/PII |

### CORS & Request Protection

| Rule | Detail |
|---|---|
| ✗ `Allow-Origin: *` with credentials | Wildcard origin incompatible with credentials |
| Allowlist origins | Validate `Origin` against a configured list |
| Restrict methods/headers | Allow only required HTTP methods and custom headers |
| Request size limits | Max body size enforced at server/framework |
| Rate limiting | Per-client limits on all endpoints; stricter on auth |
| CSRF protection | State-changing requests require anti-CSRF token or SameSite cookies → [web](../web/STANDARDS.md) |

---

## 13. Audit & Logging

Security events require dedicated, tamper-evident logging. Structured log format, fields, and retention tiers → [observability](../observability/STANDARDS.md); this section owns which security events to capture and their integrity controls.

### Events to Log

| Category | Examples |
|---|---|
| Authentication | Login success/failure · logout · token refresh · token revocation |
| Authorization | Access denied · privilege elevation · role change |
| Data access | Read/write of Confidential/Restricted · bulk export |
| Configuration change | Permission change · security-setting change · secret rotation |
| Input validation failure | Rejected requests · repeated failures from one source |
| Administrative | User create/delete · role assignment · system config change |
| Anomalies | Impossible travel · concurrent sessions · brute-force detected |

Log fields per event: timestamp (UTC ISO 8601) · actor identity · action · resource · source IP / request ID · outcome · correlation ID. ✗ log passwords, raw secrets, full PII (hash/mask), session tokens, or encryption keys.

### Integrity Controls

| Rule | Detail |
|---|---|
| Immutable storage | Append-only; ✗ modifiable after write |
| Access restricted | Readable by security/compliance roles only |
| Tamper-evident | Checksums or hash chains on entries |
| Separate from app logs | Security audit trail distinct from operational logging |
| Retention | Default ≥ 1 year (regulated: per compliance) → [observability](../observability/STANDARDS.md) |

---

## 14. Scale Matrix

| Security area | Prototype | Production | Scale |
|---|---|---|---|
| Input validation (§2) | Type checking at entry | Full validation at boundary | Schema validation + rate limiting |
| Injection (§3) | Parameterized queries | All vectors covered | + automated scanning + WAF |
| Authentication (§5) | API key / basic | Token-based with expiry + classes | MFA + short-lived tokens + rotation |
| Authorization (§6) | Single role | RBAC + resource-level checks | RBAC/ABAC + policy engine |
| Secrets (§7) | Env variables | Vault + class-based rotation | Automated rotation + audit trail |
| Data protection (§8) | TLS in transit | + encryption at rest | + classification + PII controls |
| Supply chain (§9) | Lock file + manual audit | Automated scanning + SBOM | Signed artifacts + SLSA L3 + OIDC |
| Filesystem/subprocess (§10) | Argument arrays | + allowed root + command allowlist | + symlink/TOCTOU + minimal env |
| Error exposure (§11) | Generic messages | + error IDs | + per-environment detail levels |
| Transport/headers (§12) | HTTPS | + core security headers | Full header suite + CORS + CSRF |
| Audit logging (§13) | Auth events | + access-denied + data access | Full event set + immutable storage |

Transition priority: (1) input validation + injection · (2) authn + authz · (3) secrets · (4) defense in depth.

---

## 15. Checklist

- [ ] Data classification defined for all data types
- [ ] Input validated once at the Tier 3 boundary; core logic trusts typed data
- [ ] All validation errors returned at once; ✗ stop at first
- [ ] Parameterized queries / structured APIs for every injection vector
- [ ] Output encoded per target context; ✗ raw user data in any output
- [ ] One canonical auth method per interface; unauthenticated → reject
- [ ] Access tokens: user ≤ 15 min + refresh rotation · service-to-service ≤ 1 h
- [ ] Passwords hashed with Argon2id/scrypt/bcrypt + per-user salt; ✗ plaintext
- [ ] Authorization deny-by-default; resource-level checks on every access path
- [ ] Secrets in env/vault; ✗ in code, config, or commit history
- [ ] Rotation by class: service-account ≤ 90 days · CI/deploy token ≤ 24 h
- [ ] Derived values pass inward; raw secrets never leave Tier 3
- [ ] PII minimized, encrypted, retention-limited; ✗ PII in logs/errors/receipts
- [ ] TLS 1.3 (1.2 floor); legacy TLS/SSL disabled; HSTS enabled
- [ ] Lock files committed; CVE scan blocks critical/high; dependency-confusion pinned
- [ ] SBOM generated; artifacts + commits signed; secret scanning in CI
- [ ] CI authenticates via OIDC short-lived tokens; ✗ long-lived static keys
- [ ] File ops scoped to allowed root; subprocess args as arrays; commands allowlisted
- [ ] Error responses return correlation ID, ✗ stack traces / internal detail
- [ ] Security headers + CORS allowlist + CSRF on state-changing endpoints
- [ ] Security audit trail immutable, access-restricted, retained ≥ 1 year
