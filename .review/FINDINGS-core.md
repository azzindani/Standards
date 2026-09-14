# Best-practice review — findings

> Standards audited against current external guidance, ✗ only internal consistency. `validate.py` already covers the latter.

Pass 1 · security tier. Method: search for current authoritative guidance, compare rule by rule, apply the clear-cut, record the rest.

! Egress limits: `datatracker.ietf.org` · `rfc-editor.org` · `oauth.net` · `cheatsheetseries.owasp.org` · `workos.com` are blocked by this environment's proxy. Findings below rest on search-result summaries of those sources, ✗ on the primary text. Re-verify against primaries before treating any threshold as settled.

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

## Raised, not applied

| # | Standard | Finding | Why not applied |
|---|---|---|---|
| 6 | `security/TOKENS.md` | PKCE and exact redirect-URI matching are RFC 9700 requirements and appear in no standard | Flow security, ✗ token mechanics. Belongs in `api/` | `web/`, or a new `security/OAUTH.md`. Placing it wrongly is worse than a tracked gap |
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
