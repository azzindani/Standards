# Token Authentication Standards

> How bearer tokens are chosen, signed, validated, rotated, revoked, and stored — the mechanics behind the token classes security defines.

**ID** `security/tokens` · **Tier** Core · **Version** 1.0
**Owns** token format selection · sender constraining · signing algorithm policy · claim set + validation rules · key management + rotation · JWKS · revocation strategy · client-side storage · scope + audience separation · service-to-service tokens · token anti-patterns
**Defers to** OAuth + OIDC flow security · PKCE · authorization codes · redirect validation · consent → [OAUTH.md](OAUTH.md) · token classes · lifetimes · session management · password rules · rate limiting → [security](STANDARDS.md) · RBAC/ABAC · default-deny · resource checks → [security §6](STANDARDS.md#6-authorization) · secret storage + rotation cadence → [security §7](STANDARDS.md#7-secrets-management) · cookie attributes · CSRF · frontend gating → [web](../web/STANDARDS.md) · wire contracts · versioning · error shape → [api](../api/STANDARDS.md) · config cascade for key material → [configuration](../configuration/STANDARDS.md) · vault + injection mechanics → [devops](../devops/STANDARDS.md) · audit event format → [observability](../observability/STANDARDS.md)
**Load with** [security](STANDARDS.md) · [OAUTH.md](OAUTH.md) · [api](../api/STANDARDS.md) · [web](../web/STANDARDS.md)

---

## Table of Contents

1. [Format Selection](#1-format-selection)
2. [Sender Constraining](#2-sender-constraining)
3. [Signing Policy](#3-signing-policy)
4. [Claim Validation](#4-claim-validation)
5. [Key Management](#5-key-management)
6. [Revocation](#6-revocation)
7. [Client Storage](#7-client-storage)
8. [Scope and Audience](#8-scope-and-audience)
9. [Service-to-Service](#9-service-to-service)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Format Selection

Format follows the revocation requirement, ✗ familiarity. Choose before writing code — retrofitting revocation onto a stateless token is a rewrite.

| Format | Use when | ✗ use when |
|---|---|---|
| Opaque session token | Single trust domain · immediate revocation required | Verifier cannot reach the session store |
| JWT (signed) | Multiple independent verifiers · stateless verification required | Immediate revocation is a requirement and no denylist exists |
| PASETO | Same case as JWT · a versioned protocol removes algorithm negotiation entirely | Ecosystem lacks a maintained library for the stack |
| API key | Machine caller · long-lived · one owner | A human identity is behind it |
| mTLS certificate | Service-to-service inside a controlled network | Clients are browsers |

PASETO removes §2's whole failure class by construction — the version pins the
algorithm, so there is no `alg` header to confuse. Prefer it over JWT on a new
system where library support exists; JWT stays the interoperability default.

Rules:

- Default to **opaque server-side session tokens** for browser sessions. JWT for a browser session buys statelessness and pays for it in revocation (§6).
- JWT is justified by multiple verifiers that cannot share a session store. One service verifying its own tokens is ✗ a justification.
- ✗ mix formats on one interface. Two accepted formats mean two validation paths, and the weaker one decides security.
- Encrypted tokens (JWE) only when claims carry data the client must not read. Signing ✗ hides contents — a signed JWT is readable by anyone holding it.
- API keys are identities, ✗ passwords: scoped, individually revocable, and attributable to one owner.

---

## 2. Sender Constraining

A bearer token is bearer: whoever holds it may use it. Sender constraining binds
a token to a key the client proves it holds, so a stolen token is inert.

| Mechanism | Where | Status |
|---|---|---|
| mTLS-bound tokens (RFC 8705) | Service-to-service · controlled network | Use where the network already carries client certificates |
| DPoP (RFC 9449) | Public clients · browsers · agents | Use where the authorization server advertises `dpop_signing_alg_values_supported` |
| Rotating refresh tokens (§6) | Public clients | The fallback · RFC 9700 requires rotation **or** sender constraining, ✗ neither |

Rules:

- A public client uses sender-constrained tokens **or** rotating refresh tokens with reuse detection (§6). Neither is ✗ acceptable — that pair is the RFC 9700 requirement.
- ✗ block on DPoP support: adoption among authorization servers is thin, so rotation is the conforming fallback, ✗ a shortcut.
- Where the AS advertises DPoP, prefer it for public clients — theft of a DPoP-bound token gives an attacker nothing without the private key.
- Agent clients are public clients. An agent holding a long-lived bearer is the same exposure as a browser holding one.

---

## 3. Signing Policy

| Rule | Detail |
|---|---|
| Algorithm allowlist | Verifier accepts an explicit list. ✗ read the algorithm from the token and trust it |
| `alg: none` | Rejected unconditionally. ✗ configurable, ✗ permitted in any environment |
| Symmetric (HS256) | Only when issuer and verifier are the same trust domain and share the secret |
| Asymmetric (RS256 · ES256 · `EdDSA`) | Required when verifiers are independent — a verifier ✗ hold signing capability |
| Key length | RSA ≥ 2048 bits · EC ≥ P-256 |
| Secret entropy | Symmetric keys ≥ 256 bits from a CSPRNG. ✗ a passphrase, ✗ a derived string |

The allowlist rule is load-bearing: a verifier that honours the token's own `alg` header lets an attacker downgrade RS256 to HS256 and sign with the public key. The algorithm is the verifier's decision, ✗ the token's.

---

## 4. Claim Validation

Every claim is **verified**, ✗ read. A decoded token is untrusted input until each row below passes.

| Claim | Rule |
|---|---|
| `alg` | Matches the verifier's allowlist (§3) before signature check |
| signature | Verified before any claim is read |
| `exp` | Present and in the future · required, ✗ optional |
| `nbf` | If present, in the past |
| `iat` | Present · rejected if implausibly future-dated |
| `iss` | Matches the expected issuer exactly. ✗ prefix | substring match |
| `aud` | Contains this service's identifier. A token for another audience is rejected |
| `sub` | Present · the identity the request acts as |
| `jti` | Required when a denylist (§6) is in use |

Rules:

- Clock skew tolerance ≤ 60 s, applied to `exp` and `nbf` only.
- Rejection is generic to the caller and specific in the audit log. "Invalid token" to the client; which check failed to the log.
- ✗ trust a claim a client can set. Roles and scopes come from the issuer, ✗ from a claim the client supplied at token request.
- Validate before use, ✗ alongside it. A handler that reads `sub` before signature verification is exploitable regardless of what follows.
- Unknown claims are ignored, ✗ rejected — forward compatibility. Unknown *critical* claims are rejected.
- **Token type is validated, ✗ assumed.** Only an access token authorizes; only an ID token proves authentication. A verifier that accepts any well-signed token from its issuer accepts the wrong one — same signature, same `aud`, different purpose.
- Where one issuer key serves several audiences, the audience restriction must uniquely identify the intended one; a dynamically provisioned audience is validated by the issuer, else a client names an audience it may then impersonate.

---

## 5. Key Management

| Rule | Detail |
|---|---|
| `kid` header | Every signed token carries a key id · verifier selects the key by `kid`, ✗ tries each |
| Unknown `kid` | Rejected. ✗ fall back to a default key |
| Publication | Asymmetric public keys published at a JWKS endpoint · cached with an explicit TTL |
| JWKS refresh | Scheduled · plus one on-demand refresh per unknown `kid`, rate-limited. ✗ refresh per request |
| Rotation cadence | Signing keys rotate on a schedule, ✗ only after an incident. Cadence → [security §7](STANDARDS.md#7-secrets-management) |
| Overlap window | Old key stays in the verification set for at least one max token lifetime after the new key starts signing |
| Retirement | Key removed from the verification set only after the overlap window, ✗ at rotation |
| Storage | Private keys from the config cascade | a vault · ✗ in the repo, ✗ in an image layer |

Rotation without an overlap window invalidates every live token at the instant of rotation. The overlap is what makes rotation a non-event, so it is a hard requirement, ✗ a convenience.

Compromise response is different from rotation: retire the key immediately, accept the mass invalidation, and revoke the refresh chains (§6).

---

## 6. Revocation

The JWT weak point, and the reason §1 defaults to opaque tokens. A signed token is valid until it expires — nothing about it consults the issuer.

| Strategy | Immediacy | Cost |
|---|---|---|
| Short expiry alone | Bounded by lifetime | None · the weakest option |
| Denylist by `jti` | Immediate | A store every verifier reaches — the statelessness JWT was chosen for is gone |
| Session lookup per request | Immediate | Equivalent to an opaque token · then use one |
| Refresh-token revocation | Bounded by access-token lifetime | Low · the common compromise |

Rules:

- Pick a strategy before choosing JWT, ✗ after. "We will add revocation later" means shipping without it.
- Logout must invalidate the refresh chain server-side. Deleting a client-side token is ✗ revocation.
- Refresh tokens are single-use and rotate on use. Reuse of a spent refresh token means theft: revoke the entire chain and log a security event.
- Privilege change (role removed, account disabled) revokes the refresh chain — otherwise the old privileges survive until the access token expires.
- A revocation path that is never exercised is untested: revoke-and-verify belongs in the test suite → [testing](../testing/STANDARDS.md).

---

## 7. Client Storage

| Location | Verdict |
|---|---|
| `HttpOnly` · `Secure` · `SameSite` cookie | ✓ for browser sessions · unreachable from script. Attributes → [web](../web/STANDARDS.md) |
| Memory only, for the page's lifetime | ✓ for an access token in a SPA |
| `localStorage` · `sessionStorage` | ✗ for any token · readable by any script the page loads, including a compromised dependency |
| URL · query string · path | ✗ always · leaks to logs, referrer headers, browser history, proxies |
| Native secure enclave | ✓ on mobile · Keychain | Keystore |

Rules:

- Refresh tokens never reach script-accessible storage. `HttpOnly` cookie | native secure storage only.
- Tokens are sent in the `Authorization` header | a cookie, ✗ both on one request — two sources mean the weaker one can be forged.
- Token values are redacted in logs, traces, and error reports at the logging boundary, ✗ by remembering to omit them at each call site.
- A token in a crash dump, a request log, or an analytics payload is a leaked token. Treat it as compromised and revoke.

---

## 8. Scope and Audience

| Rule | Detail |
|---|---|
| Least privilege | Token carries the narrowest scope the operation needs |
| Audience per service | One `aud` per verifier · a token for service A is rejected by service B |
| ✗ scope escalation | A token ✗ mint a broader-scoped token. Escalation goes through the issuer |
| Scope names are stable | Renaming a scope is a breaking change → [api](../api/STANDARDS.md) |
| Deny by default | Absent scope → denied. ✗ treat an empty scope set as full access |

An empty scope claim meaning "everything" is a standing outage: any bug that drops the claim grants full access silently. Absent means none.

---

## 9. Service-to-Service

| Rule | Detail |
|---|---|
| Distinct identity | Each service authenticates as itself · ✗ share one credential across services |
| ✗ user tokens for service calls | A service acting on its own behalf uses its own token. Forwarding a user token makes every downstream a confused deputy |
| Delegation is explicit | When a call acts for a user, the token records both service and user identity |
| Short lifetime | ≤ 1 h → [security §5](STANDARDS.md#5-authentication) |
| mTLS where available | Certificate identity inside a controlled network · tokens on top only when scope is needed |
| Credential provisioning | Issued by the platform, rotated automatically · ✗ hand-placed, ✗ in an image |

---

## 10. Anti-Patterns

| Anti-pattern | Symptom | Correction |
|---|---|---|
| Trusting `alg` | Verifier honours the token's algorithm header | Allowlist in the verifier (§3) |
| `alg: none` accepted | Unsigned tokens verify | Reject unconditionally (§3) |
| Decode without verify | Claims read before signature check | Verify first, always (§4) |
| Missing `aud` check | A token minted for another service is accepted | Verify audience (§4) |
| Missing `iss` check | Any issuer's token with the right shape works | Exact issuer match (§4) |
| Long-lived access token | 24 h access token "to avoid refresh complexity" | Short access + rotating refresh (§6) |
| Revocation deferred | JWT chosen, revocation "later" | Choose the strategy before the format (§6) |
| Client-side logout | Token deleted in the browser, still valid | Revoke the chain server-side (§6) |
| Token in `localStorage` | Any injected script exfiltrates it | `HttpOnly` cookie | memory (§7) |
| Token in a URL | Appears in access logs and referrers | Header only (§7) |
| Empty scope = full access | A dropped claim grants everything | Absent means none (§8) |
| Shared service credential | One key used by every service | Per-service identity (§9) |
| User token forwarded downstream | Deputy acts with the user's full rights | Service token + explicit delegation (§9) |
| Key rotation without overlap | Every live token dies at rotation | Overlap ≥ one max lifetime (§5) |
| Unknown `kid` falls back | Verifier tries a default key | Reject unknown `kid` (§5) |
| Tokens in logs | Bearer values in request logs | Redact at the logging boundary (§7) |
| Bearer-only public client | Agent | browser holds a bearer with no rotation and no binding | Rotate with reuse detection, | bind (§2) |
| DPoP made a blocker | Rollout stalls waiting for issuer support | Rotation is the conforming fallback (§2) |

---

## 11. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Format | Opaque session token | Opaque, | JWT with a chosen revocation strategy | JWT + JWKS + denylist |
| Sender constraining | Rotation only | Rotation with reuse detection | DPoP | mTLS where the AS supports it |
| Signing | HS256, single domain | Asymmetric when verifiers are independent | Asymmetric · `kid` required · per-environment keys |
| Key rotation | Manual | Scheduled with overlap window | Automated · overlap ≥ one max lifetime · audited |
| Revocation | Short expiry | Refresh-chain revocation | Immediate by `jti` denylist |
| Audience | Single audience | One `aud` per service | Per-service · verified · monitored for cross-audience attempts |
| Refresh rotation | Optional | Single-use with reuse detection | Single-use · reuse revokes chain · alerts |
| Audit | Auth failures logged | Failures + issuance logged | Full lifecycle: issue · refresh · revoke · reuse-detected |

---

## 12. Checklist

- [ ] Token format chosen from the revocation requirement, not familiarity
- [ ] One token format per interface
- [ ] Public clients use sender-constrained tokens or rotating refresh tokens with reuse detection — never neither
- [ ] DPoP is used where the authorization server advertises it, and its absence does not block rollout
- [ ] Verifier validates against an algorithm allowlist it owns
- [ ] `alg: none` rejected unconditionally in every environment
- [ ] The algorithm allowlist holds one family; mixing symmetric and asymmetric carries extra key-confusion controls
- [ ] `jku`, `x5u`, `jwk` and `x5c` are validated against an allowlist of trusted sources, never fetched as given
- [ ] Token type is validated — only access tokens authorize, only ID tokens prove authentication
- [ ] Asymmetric signing wherever verifiers are independent of the issuer
- [ ] Signature verified before any claim is read
- [ ] `exp` required and enforced; clock skew tolerance ≤ 60 s
- [ ] `iss` matched exactly, never by prefix or substring
- [ ] `aud` verified to contain this service
- [ ] No authorization decision reads a claim the client could set
- [ ] Every token carries `kid`; unknown `kid` is rejected with no default-key fallback
- [ ] Signing keys rotate on a schedule with an overlap of at least one max token lifetime
- [ ] Private key material comes from the config cascade or a vault, never the repo or an image
- [ ] A revocation strategy was chosen before the token format
- [ ] Logout revokes the refresh chain server-side
- [ ] Refresh tokens are single-use and rotate; reuse revokes the whole chain and raises an event
- [ ] Privilege change revokes the refresh chain
- [ ] Revoke-and-verify is covered by a test
- [ ] No token is stored in localStorage or sessionStorage
- [ ] No token appears in a URL, query string, or path
- [ ] Tokens are redacted at the logging boundary, not per call site
- [ ] Absent scope denies; an empty scope set never means full access
- [ ] Each service authenticates with its own identity
- [ ] No user token is forwarded as a service credential
