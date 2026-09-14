# Best-practice review — findings

> Standards audited against current external guidance, ✗ only internal consistency. `validate.py` already covers the latter.

Pass 1 · security tier. Method: search for current authoritative guidance, compare rule by rule, apply the clear-cut, record the rest.

**Primary-source access — solved.** `datatracker.ietf.org` · `rfc-editor.org` ·
`oauth.net` · `cheatsheetseries.owasp.org` are blocked by this environment's
proxy, but **`github.com` and `raw.githubusercontent.com` are not**, and the
sources that matter are maintained there in the open:

| Source | Location | Status |
|---|---|---|
| OWASP ASVS 5.0 | `github.com/OWASP/ASVS` → `5.0/en/*.md` | ✓ read directly |
| OWASP Cheat Sheets | `github.com/OWASP/CheatSheetSeries` | ✓ available |
| OpenTelemetry semantic conventions | `github.com/open-telemetry/semantic-conventions` | ✓ available |
| NIST SP 800-63-4 | `github.com/usnistgov/800-63-4` | ✓ available |
| RFC text | ✗ on GitHub · IETF mirrors blocked | ✗ search summaries only |

Method: `git clone --depth 1` the source repo, read the requirement text, cite by
requirement id. Pass 2 below used it for ASVS V9 and V10.

! Still unverified against primaries: RFC 9700 · RFC 9449 · RFC 7636 language.
ASVS restates their requirements with ids, which is a strong secondary citation,
✗ the normative text itself.

---

## Applied

| # | Standard | Finding | Source | Change |
|---|---|---|---|---|
| 1 | `security/TOKENS.md` | Sender-constrained tokens absent entirely. RFC 9700 requires a public client to use sender constraining **or** rotating refresh tokens — the standard mandated rotation but never named the alternative, so the requirement's shape was invisible | RFC 9700 (BCP 240) · RFC 9449 DPoP | New §2 Sender Constraining · mTLS · DPoP · rotation as the conforming fallback |
| 2 | `security/TOKENS.md` | PASETO missing from format selection. ASVS 5.0 V9 covers JWT **and** PASETO; PASETO's versioned protocol removes the algorithm-confusion class by construction | OWASP ASVS 5.0 V9 Self-Contained Tokens | Added to §1 with the condition that decides it — library support |
| 3 | `security/TOKENS.md` | Agent clients unaddressed. MCP lists sender-constrained tokens as recommended hardening for public clients, and an agent holding a long-lived bearer is a browser's exposure | RFC 9700 · MCP guidance | Rule in §2: agent clients are public clients |
| 4 | `security/STANDARDS.md` | Password minimum of 12 is below current guidance for single-factor | NIST SP 800-63B-4 (min 8, 15 recommended single-factor) | ≥ 15 single-factor · ≥ 12 with a second factor, cited |
| 5 | `security/STANDARDS.md` | Session timeouts required but unquantified — "absolute AND idle" with no numbers is unenforceable | NIST SP 800-63B-4 AAL tiers | AAL2 absolute ≤ 24 h · idle ≤ 1 h · AAL1 absolute ≤ 30 d, cited |

---

## Pass 2 — applied from ASVS primary text

Read from `OWASP/ASVS` `5.0/en/0x18-V9-Self-contained-Tokens.md` and
`0x19-V10-OAuth-and-OIDC.md`. Three gaps that the search summaries did not
surface, and one confirmation that mattered.

| # | Standard | Finding | Requirement | Change |
|---|---|---|---|---|
| 9 | `security/TOKENS.md` | **Key-source headers unaddressed.** `kid` and JWKS were covered, but nothing forbade a token naming its *own* key source. A verifier that fetches the JWKS a token points at validates the attacker's signature against the attacker's key, and every other rule becomes decorative | ASVS 9.1.3 — `jku` · `x5u` · `jwk` validated against an allowlist of trusted sources | New table in §3 · the token ✗ choose its key source |
| 10 | `security/TOKENS.md` | **Token type confusion unaddressed.** A verifier accepting any well-signed token from its issuer accepts the wrong one — same signature, same `aud`, different purpose | ASVS 9.2.2 — only access tokens authorize, only ID tokens prove authentication | Rule in §4 · type validated, ✗ assumed |
| 11 | `security/TOKENS.md` | Algorithm allowlist permitted mixing families without comment | ASVS 9.1.2 — ideally only symmetric **or** asymmetric; both needs extra controls against key confusion | §3 prefers one family |
| 12 | `security/TOKENS.md` | Audience rule missed the shared-key and dynamic-provisioning case | ASVS 9.2.4 | Rule in §4 |

**Confirmation.** ASVS 10.4.5 states the sender-constraining rule added in pass 1
almost verbatim — sender-constrained refresh tokens preferred (DPoP | mTLS), with
rotation permitted at L1/L2 **provided** the server invalidates the used token
and *revokes all refresh tokens for that authorization* when an already-used one
is presented. That is both the standard's §2/§6 rule and the behaviour
implemented in Pipeline's `oauth.rs` this session, now confirmed against primary
text rather than inferred.

ASVS 10.4.14 raises it at L3: issue **only** sender-constrained access tokens.

---

## Raised, not applied

| # | Standard | Finding | Why not applied |
|---|---|---|---|
| 6 | `security/TOKENS.md` | PKCE · exact redirect-URI matching · authorization-code lifetime and single-use · grant restriction appear in no standard | **Resolved in principle:** ASVS separates V9 (self-contained tokens) from V10 (OAuth and OIDC), which settles the placement question — these belong in a sibling `security/OAUTH.md`, ✗ in TOKENS.md. Writing it is its own task |
| 7 | `security/TOKENS.md` | DPoP stated as "use where advertised". Of 18 issuers surveyed in 2026, none advertised support | The rule is right for now and will age. Revisit when adoption moves — a standard that mandates an unavailable mechanism gets ignored wholesale |
| 8 | `security/STANDARDS.md` | ASVS 5.0 restructured: token requirements moved from V7 to a standalone V9 | Structural alignment with ASVS is a larger decision than one edit |

---

## Verified current — no change needed

Spot-checked against the sources that would most likely have moved. Recording
these matters: a review that only lists defects implies the unexamined rest is
also defective.

| Standard | Checked against | Result |
|---|---|---|
| `cicd/` §2 | DORA 2025 State of DevOps | Already correct, and ahead of most secondary writing: explicitly records that the Elite/High/Medium/Low four-cluster model was retired in 2025 and marks the 2024 numbers as dated reference. Several sources found in this search still present the retired clusters as current |
| `observability/` | OpenTelemetry semantic conventions | Cites OTel as the vendor-neutral emission path and names its semantic conventions · RED · USE · golden signals · SLOs + error budgets all present |
| `rust/` §1 | Current toolchain | Edition 2024 default with 2021 permitted only below MSRV 1.85 · `unsafe_code = "forbid"` default · Miri in CI · `cargo-fuzz` on unsafe boundaries |
| `dependencies/` | SLSA · SBOM practice | SLSA, signing, dependency confusion, typosquatting, SBOM-as-release-artifact and SBOM diffing all present |

---

## Remaining tiers

Not yet reviewed: Foundation (5) · Core (9 of 10) · Delivery (5) · Interface (4) · Domain (5) · Language (6). Highest expected yield, in order:

1. `devops/` against NIST SP 800-190 + CIS Benchmarks — container thresholds are externally fixed.
2. `api/` against OpenAPI 3.1 + the Microsoft and Google API design guides.
3. `web/` against the current OWASP Top 10 and browser platform changes.
4. `database/` · `sql/` — index, isolation and migration guidance ages quietly.
5. Remaining language standards (`python/` `go/` `typescript/` `shell/`) against current toolchain defaults — these age fastest.
6. `testing/` · `ml/` · `data_pipeline/` — mutation-testing and eval practice moved with AI tooling.

Expectation after pass 1: the yield is low and the findings are additive rather
than corrective. Both standards examined in depth were substantially right, and
`cicd/` was more current than several secondary sources describing the same
material. Budget the remaining passes accordingly — the value is in the few real
gaps, ✗ in a finding per standard.
