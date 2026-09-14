# OAuth and OIDC Standards

> Flow security for delegated authorization: what the client, the resource server, and the authorization server each must enforce, independent of what the tokens themselves look like.

**ID** `security/oauth` · **Tier** Core · **Version** 1.0
**Owns** role responsibilities (client · resource server · authorization server) · redirect URI validation · authorization code rules · PKCE · state + nonce binding · grant restriction · mix-up defence · dynamic client registration · client authentication · consent · OIDC client obligations
**Defers to** token format · signing · claim validation · key rotation · revocation strategy · client storage · scope semantics → [TOKENS.md](TOKENS.md) · token classes · lifetimes · session management · rate limiting → [security](STANDARDS.md) · RBAC/ABAC · default-deny → [security §6](STANDARDS.md#6-authorization) · cookie attributes · CSRF surface · frontend gating → [web](../web/STANDARDS.md) · wire contracts · error shape · versioning → [api](../api/STANDARDS.md) · TLS + transport → [security §12](STANDARDS.md#12-transport--headers)
**Load with** [security](STANDARDS.md) · [TOKENS.md](TOKENS.md) · [web](../web/STANDARDS.md)

---

## Table of Contents

1. [Roles](#1-roles)
2. [Grant Selection](#2-grant-selection)
3. [Authorization Request](#3-authorization-request)
4. [Authorization Code](#4-authorization-code)
5. [Client Obligations](#5-client-obligations)
6. [Resource Server Obligations](#6-resource-server-obligations)
7. [Client Registration and Authentication](#7-client-registration-and-authentication)
8. [Consent](#8-consent)
9. [OIDC Specifics](#9-oidc-specifics)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Roles

Four roles, each with obligations the others cannot discharge. A system that conflates them loses the checks each was meant to apply.

| Role | Is | Must |
|---|---|---|
| Authorization server | Issues tokens | Validate redirect · bind the transaction · restrict grants · enforce PKCE |
| Client | Requests tokens on a user's behalf | Bind state + nonce · defend against mix-up · request minimum scope |
| Resource server | The API | Validate the token · check audience · decide from claims |
| Resource owner | The user | Consent knowingly |

Confidentiality is a property of where the client runs, ✗ of what it is called.

| Client kind | Classification |
|---|---|
| Backend · backend-for-frontend | Confidential — can hold a secret |
| SPA · browser · mobile app · agent | Public — cannot hold a secret, whatever the docs say |
| Native app using dynamic client registration | Confidential, per-install |

A public client that is treated as confidential has a secret extractable by anyone who downloads it. ✗ ship one.

---

## 2. Grant Selection

| Grant | Verdict |
|---|---|
| Authorization code + PKCE | The default for any user-facing flow |
| Client credentials | Service acting as itself · ✗ on behalf of a user |
| Refresh | Paired with code · rules → [TOKENS.md §6](TOKENS.md#6-revocation) |
| Implicit (`token`) | ✗ — removed. Returns tokens through the browser URL |
| Resource owner password credentials (`password`) | ✗ — removed. Hands the client the user's password |

Rules:

- The authorization server allows each client only the grants that client actually uses. An unused grant enabled is an unused attack path enabled.
- Implicit and ROPC are not deprecated-but-tolerated: they are removed. A system still using either is migrating, ✗ compliant.

---

## 3. Authorization Request

| Rule | Detail |
|---|---|
| PKCE required | Code grant requires a valid `code_challenge` · the server validates `code_verifier` at exchange |
| `plain` refused | `code_challenge_method` of `plain` makes the challenge equal the verifier · ✗ accept it, ✗ fall back to it when the method is absent |
| `state` bound | Unguessable · transaction-specific · bound to the user-agent session that started the flow |
| `nonce` bound (OIDC) | Same properties · replayed ID tokens are caught here |
| Response mode restricted | The server permits only the `response_mode` a given client needs |
| Minimum scope | The client requests only the scopes the operation needs |

`state` and PKCE are not interchangeable in intent — PKCE binds the code to the client, `state` binds the response to the session. A flow needs both; using one to excuse the other leaves the corresponding attack open.

At L3: the authorization request itself is protected — pushed authorization requests (PAR) | JWT-secured authorization requests (JAR), so parameters cannot be tampered with in the browser.

---

## 4. Authorization Code

| Rule | Detail |
|---|---|
| Single use | A code redeems exactly once |
| Reuse revokes | Presenting an already-redeemed code → refuse **and** revoke every token issued from that code |
| Short-lived | ≤ 10 min · ≤ 1 min where the stakes justify L3 |
| Bound to the client | A code issued to client A is ✗ redeemable by client B |
| Bound to the redirect | The `redirect_uri` at exchange matches the one at authorization |

Reuse is the load-bearing rule and the one most often half-implemented. Deleting the code on first read stops a second redemption but leaves whatever the first redemption minted alive — and if the attacker redeemed first, that is precisely the grant to kill. Refusing without revoking hands the attacker a working session and the user an error message.

---

## 5. Client Obligations

| Rule | Detail |
|---|---|
| CSRF defence | PKCE \| `state` validation on the authorization response · one of them, verified |
| Mix-up defence | A client talking to more than one authorization server validates the `iss` returned in the authorization and token responses |
| Token confinement | Tokens reach only components that need them · in a backend-for-frontend, access and refresh tokens stay in the backend |
| Accept only own transactions | A code or ID token is accepted only when it results from a flow this user-agent session started |
| Minimum scope | ✗ request scopes for future features |

Tokens in a browser-based client are reachable by every script the page loads. The backend-for-frontend pattern exists so that they are not — routing them to the frontend "for convenience" discards the pattern's only benefit.

---

## 6. Resource Server Obligations

Performed **after** token validation ([TOKENS.md §4](TOKENS.md#4-claim-validation)), before any authorization decision.

| Rule | Detail |
|---|---|
| Audience | Accept only tokens intended for this service · by `aud` claim \| introspection |
| Decide from claims | `sub` · `scope` · `authorization_details` are part of the decision when present, ✗ decoration |
| Stable identity | Identify the user by claims that cannot be reassigned — `iss` + `sub` together, ✗ email, ✗ username |
| Authentication strength | Where an operation requires a strength, method, or recency, verify it — `acr` · `amr` · `auth_time` |
| Replay defence (L3) | Require sender-constrained access tokens → [TOKENS.md §2](TOKENS.md#2-sender-constraining) |

Identifying a user by a reassignable claim means a recycled email address inherits the previous holder's access.

---

## 7. Client Registration and Authentication

| Rule | Detail |
|---|---|
| Backchannel authentication | Confidential clients authenticate on token, PAR, and revocation requests |
| Strong client auth (L3) | Public-key and replay-resistant — mTLS (`tls_client_auth` · `self_signed_tls_client_auth`) \| `private_key_jwt` |
| Scope assignment | The server assigns each client only the scopes it needs |
| Open dynamic registration | Permitted only with metadata validation, explicit user consent, and a warning before an untrusted client's authorization request |
| Registration caps | Anonymous registration is capped and aged out · uncapped, it is memory exhaustion by design |

An open `/register` endpoint is an unauthenticated allocation primitive. Treat the cap as a security control, ✗ as tidiness.

---

## 8. Consent

| Rule | Detail |
|---|---|
| Consent is informed | The user sees which client, which scopes, and which resource before granting |
| Consent is revocable | The user can revoke refresh tokens and reference access tokens through an interface they can reach |
| Untrusted clients flagged | A dynamically registered, unverified client is presented as such |
| ✗ silent re-consent | A scope increase requires fresh consent, ✗ inheritance from an earlier grant |

---

## 9. OIDC Specifics

| Rule | Detail |
|---|---|
| ID token ≠ access token | An ID token proves authentication · it ✗ authorize anything → [TOKENS.md §4](TOKENS.md#4-claim-validation) |
| `nonce` verified | The `nonce` in the ID token matches the one sent in the authentication request |
| `aud` equals `client_id` | The client verifies the ID token was minted for it |
| Issuer exact match | Authorization server metadata is rejected when its issuer URL ✗ exactly match the pre-configured one |
| Stable subject | The user is identified by a claim that cannot be reassigned within the provider |

Issuer metadata that the client accepts on trust lets a malicious authorization server impersonate the real one. The pre-configured issuer is the anchor, and an exact comparison is what makes it one.

---

## 10. Anti-Patterns

| Anti-pattern | Symptom | Correction |
|---|---|---|
| PKCE downgrade | `code_challenge_method` falls back to `plain` when absent or unknown | Refuse anything but S256 (§3) |
| `state` omitted because PKCE is present | One control excused by the other | Both · they bind different things (§3) |
| Code reuse refused but not revoked | Second redemption fails, the attacker's first-issued tokens live on | Revoke everything that code minted (§4) |
| Implicit flow "for simplicity" | Tokens in the browser URL, in history, in referrers | Code + PKCE (§2) |
| Password grant for a first-party app | The client sees the user's password | Code + PKCE (§2) |
| Public client with a shipped secret | Secret in a bundle or an APK | Treat as public; there is no secret (§1) |
| Tokens forwarded to the SPA | Backend-for-frontend built, then bypassed | Tokens stay in the backend (§5) |
| Audience unchecked at the resource server | Any token from the issuer is accepted | Verify audience (§6) |
| User identified by email | A recycled address inherits access | `iss` + `sub` (§6) |
| Uncapped dynamic registration | Anonymous allocation without limit | Cap, age out, require consent (§7) |
| Every grant enabled per client | Unused grants left on | Restrict to what the client uses (§2) |
| Issuer metadata trusted as returned | A hostile server impersonates the real one | Exact match against pre-configured issuer (§9) |

---

## 11. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Grant set | Code + PKCE | Code + PKCE · per-client restriction | Per-client restriction · PAR required |
| PKCE | Required · S256 | Required · S256 · `plain` refused | Same, plus JAR \| PAR protecting the request |
| Code lifetime | ≤ 10 min | ≤ 10 min · single use · reuse revokes | ≤ 1 min · reuse revokes · alerted |
| Client authentication | Secret for confidential clients | Secret + backchannel auth | mTLS \| `private_key_jwt` |
| Access-token replay | Bearer | Bearer + short lifetime | Sender-constrained only |
| Dynamic registration | Closed | Closed \| capped with consent | Capped · consent · metadata validated · warned |
| Consent | Implicit for first-party | Explicit, revocable | Explicit · revocable · audited · re-consent on scope increase |
| Mix-up defence | Single AS | `iss` validated when multiple | `iss` validated always |

---

## 12. Checklist

- [ ] Every client is classified by where it runs, and no public client ships a secret
- [ ] Implicit and resource-owner-password grants are absent, not merely discouraged
- [ ] Each client is permitted only the grants it uses
- [ ] The code grant requires PKCE, and `code_challenge_method` `plain` is refused rather than accepted as a fallback
- [ ] `state` is unguessable, transaction-specific, and bound to the user-agent session
- [ ] `state` and PKCE are both present; neither is excused by the other
- [ ] Authorization codes are single-use
- [ ] Reusing a code revokes every token that code issued, not only the second request
- [ ] Authorization codes expire within 10 minutes
- [ ] The `redirect_uri` is validated against a per-client allowlist by exact string comparison
- [ ] The client validates `iss` when it can talk to more than one authorization server
- [ ] Access and refresh tokens never reach a browser-based frontend behind a backend-for-frontend
- [ ] The resource server verifies audience before any authorization decision
- [ ] Authorization decisions use `sub`, `scope`, and `authorization_details` where present
- [ ] Users are identified by claims that cannot be reassigned, typically `iss` plus `sub`
- [ ] Required authentication strength or recency is verified against `acr`, `amr`, or `auth_time`
- [ ] Confidential clients authenticate on token, PAR, and revocation requests
- [ ] Dynamic client registration is capped, aged out, and gated by consent
- [ ] Consent names the client, the scopes, and the resource, and a scope increase re-prompts
- [ ] Users can revoke refresh and reference access tokens through an interface they can reach
- [ ] ID tokens are never accepted as authorization
- [ ] The OIDC `nonce` is verified against the value sent in the authentication request
- [ ] The ID token `aud` equals this client's `client_id`
- [ ] Authorization server metadata is rejected unless its issuer exactly matches the pre-configured value
