# Dependency Management Standards

> How a project acquires, pins, isolates, audits, licenses, and retires every external and internal dependency in its supply chain.

**ID** `dependencies` · **Tier** Core · **Version** 1.0
**Owns** dependency minimization + evaluation · wrapper/adapter isolation · version pinning + lockfiles · reproducible builds · SBOM · supply-chain integrity (SLSA · signing · dependency-confusion · typosquatting) · vuln scanning + patch SLAs · **license tiers (sole owner)** · vendoring · internal + transitive dependencies
**Defers to** language-specific package tooling → language standards · CVE remediation vs exposure model → [security](../security/STANDARDS.md) · pipeline stage placement → [cicd](../cicd/STANDARDS.md) · container base-image supply chain → [devops](../devops/STANDARDS.md) · semver + release tagging → [git](../git/STANDARDS.md) · dependency isolation vs layer model → [architecture](../architecture/STANDARDS.md)
**Load with** [security](../security/STANDARDS.md) · [cicd](../cicd/STANDARDS.md) · [architecture](../architecture/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Evaluation and Adoption](#2-evaluation-and-adoption)
3. [Wrapper Pattern](#3-wrapper-pattern)
4. [Version Pinning and Lockfiles](#4-version-pinning-and-lockfiles)
5. [Reproducible Builds and SBOM](#5-reproducible-builds-and-sbom)
6. [Supply-Chain Integrity](#6-supply-chain-integrity)
7. [Vulnerability Scanning and Patch SLAs](#7-vulnerability-scanning-and-patch-slas)
8. [Update Strategy](#8-update-strategy)
9. [License Tiers](#9-license-tiers)
10. [Transitive Dependencies](#10-transitive-dependencies)
11. [Vendoring](#11-vendoring)
12. [Internal Dependencies and Isolation](#12-internal-dependencies-and-isolation)
13. [Anti-Patterns](#13-anti-patterns)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Principles

Every dependency is a liability: attack surface, maintenance burden, upgrade risk, build complexity, license obligation. Minimize count ruthlessly.

| # | Rule |
|---|---|
| 1 | Justify every addition in writing before adopting it |
| 2 | Prefer the standard library over a third-party package |
| 3 | Prefer one dependency doing three things over three doing one each |
| 4 | ✗ add a dependency for trivial functionality — 20 lines beats a 2000-line import |
| 5 | Remove unused dependencies every release — dead deps still carry vuln + license risk |
| 6 | Dependency count is part of project complexity — it is built, tested, audited, deployed |
| 7 | Core logic never touches a third-party API directly — it goes through a wrapper (§3) |
| 8 | Pin everything · commit the lockfile · scan every build |

---

## 2. Evaluation and Adoption

Score every candidate before adoption. One failed criterion vetoes it.

| Criterion | Minimum | Red flag |
|---|---|---|
| Maintenance activity | Commit within 6 months | No commit in 12+ months |
| Release cadence | ≥ 1 release/year | Last release > 2 years ago |
| Issue response | Maintainer responds within 30 days | Issues unanswered 90+ days |
| Test suite | Tests exist and pass in CI | No tests / broken CI |
| Documentation | API docs + usage guide | README stub only |
| License | Permissive or weak-copyleft (§9) | Strong/network copyleft in a proprietary project · no license |
| Transitive count | ≤ 10 | > 20 |
| Security track record | No unpatched critical CVEs | History of slow response |
| Bus factor | ≥ 2 active maintainers | Single maintainer, no org backing |
| Footprint | Proportional to value | Adds > 10% to the binary for a minor feature |

### Decision Record

Every new dependency (production scale) records: name + exact version · problem it solves (concrete, ✗ "might be useful") · ≥ 2 alternatives considered including "write it ourselves" · evaluation scores · wrapper plan · exit strategy.

---

## 3. Wrapper Pattern

Every third-party library is wrapped at a boundary. Core logic never imports third-party types directly. See [architecture](../architecture/STANDARDS.md).

| Rule | Detail |
|---|---|
| One wrapper per external library | Single point of contact between project and dependency |
| Wrapper exposes project-native types | Internal code never imports third-party types |
| Wrapper lives at a boundary layer | The edge, or the boundary where the library is used |
| Thin — translation only | ✗ business logic in a wrapper |
| Swap test | Remove the library and only the wrapper breaks; if core logic breaks, the wrapper leaked |
| Stdlib exemption | Language standard library used directly, no wrapper |

| Wrap | ✗ Wrap |
|---|---|
| HTTP clients · DB drivers · serialization libs | Language builtins (string, math, collections) |
| Cloud SDKs · logging frameworks · templating engines | Standard-library I/O · type-system features |

Each wrapper: accepts/returns project-native types only · converts library exceptions to project error types · exposes only the subset actually used · documents the library version it targets.

---

## 4. Version Pinning and Lockfiles

| Context | Version format |
|---|---|
| Lock file | Exact: `1.2.3` — reproducible, byte-identical builds |
| Manifest | Range: `>=1.2,<2.0` — compatible resolution across consumers |
| Internal shared library | Exact in lock, range in manifest |
| Development tools | Exact in lock — linter drift causes spurious failures |

| Constraint | Rule |
|---|---|
| Minimum version | Always specified — bare `*` is prohibited |
| Maximum version | Next-major ceiling: `<2.0` for a `1.x` series |
| Pre-release | ✗ in production deps; allowed dev-only |
| Multiple majors | ✗ two major versions of one dependency in a project |

### Lockfiles

| Rule | Detail |
|---|---|
| Always committed | Every project, every deployable unit. ✗ `.gitignore` a lockfile, ever, for any reason |
| One per deployable unit | Monorepo: one per package/service, ✗ a single global lock |
| Regenerated by tooling | Manual edits are prohibited |
| CI enforces freshness | Build fails on a stale or missing lockfile |
| Integrity hashes included | Checksums verified on install — blocks tampering |

**Reproducibility requirement:** identical source + lockfile + tooling version → byte-identical output on any machine. If not, the pinning strategy is broken.

---

## 5. Reproducible Builds and SBOM

### Reproducible Builds

| Rule | Detail |
|---|---|
| Deterministic output | Same inputs → identical artifact; ✗ embedded timestamps, paths, or build-host identity |
| Pinned toolchain | Compiler/build-tool version pinned alongside dependencies |
| Hermetic where possible | Build reads only declared inputs — ✗ ambient network or global state |
| Verified in CI | Rebuild and compare digests; a mismatch fails the build |

### SBOM

| Rule | Detail |
|---|---|
| Generated every build | A Software Bill of Materials lists every direct + transitive component with version and license |
| Standard format | SPDX or CycloneDX — ✗ a bespoke format |
| Published with the artifact | SBOM is a release artifact, retained with the build |
| Diffed on change | SBOM diff surfaces every added/removed/upgraded component for review |
| Feeds scanning | Vuln (§7) and license (§9) scanning consume the SBOM |

---

## 6. Supply-Chain Integrity

The dependency is only as trustworthy as its delivery path.

| Threat | Defense |
|---|---|
| Tampered package | Verify integrity hashes from the lockfile on every install |
| Compromised publisher | Prefer signed artifacts; verify signatures/provenance before install |
| Dependency confusion | Pin the registry/source per package; ✗ let an internal name resolve to a public registry |
| Typosquatting | Verify exact package name + namespace on add; new deps reviewed by a second person |
| Malicious postinstall | Disable arbitrary install scripts by default; allowlist the few that are required |
| Upstream account takeover | Pin exact versions; a sudden new version is reviewed, ✗ auto-adopted |

### Provenance

| Rule | Detail |
|---|---|
| Target a SLSA level | Adopt SLSA build-provenance; state the target level per project |
| Provenance attestation | Build emits a signed statement of what was built, from which source, by which builder |
| Verify on deploy | Deploy gate checks provenance + signature — ✗ deploy an unattested artifact |
| Trusted builders only | Artifacts built by the CI system, ✗ from a developer laptop |

---

## 7. Vulnerability Scanning and Patch SLAs

Scanning is owned here; the *exposure/risk model* (is this CVE reachable in our context) is owned by [security](../security/STANDARDS.md).

| Rule | Detail |
|---|---|
| Automated scan every CI build | Catch vulnerabilities before merge — stage placement → [cicd](../cicd/STANDARDS.md) |
| Scan the lockfile, not the manifest | The lockfile reflects actual resolved versions |
| Scan transitive deps | Vulnerabilities hide in indirect deps |
| Scan container images separately | OS packages have an independent surface — see [devops](../devops/STANDARDS.md) |
| Exception list with expiry | An accepted vuln gets a documented deadline, ✗ silent ignore |

### Patch SLA by Severity

| Severity | CI gate | Patch deadline |
|---|---|---|
| Critical (CVSS ≥ 9.0) | Block merge + alert | 24 hours |
| High (7.0–8.9) | Block merge | 1 week |
| Medium (4.0–6.9) | Warn, allow merge | 1 month |
| Low (< 4.0) | Log only | Next scheduled cycle |

### Exception Record

Required fields: CVE id · affected dependency + version · justification (✗ "will fix later") · compensating mitigation in place · expiry date (auto-expires, forces re-evaluation) · named owner (a person, ✗ a team).

---

## 8. Update Strategy

| Category | Timeline | Process |
|---|---|---|
| Critical security patch (exploited) | 24 hours | Hotfix branch → expedited review → deploy |
| High vuln (CVSS ≥ 7.0) | 1 week | Prioritized PR |
| Medium vuln (4.0–6.9) | 1 month | Batched with the scheduled cycle |
| Low vuln (< 4.0) | Next cycle | Batched |
| Feature / minor update | Scheduled cycle | Batched, tested, reviewed |
| Major version upgrade | Planned | Dedicated branch + migration plan + extended testing |

### Update Process

1. Review the changelog — ✗ blind update.
2. Check for breaking changes; a major bump needs a migration plan.
3. Update one dependency per commit — bisectable.
4. Run the full suite, integration tests included.
5. Review the lockfile diff — verify transitive changes are expected.
6. Deploy to staging before production.

**✗ Forbidden:** auto-merge dependency PRs without review · update multiple unrelated deps in one commit · skip changelog review · pin to `latest` or a floating tag.

---

## 9. License Tiers

**Sole owner.** Every other standard cross-references this table — ✗ restate it, ✗ flat-ban a tier locally.

| Tier | Licenses | Rule |
|---|---|---|
| Permissive (preferred) | MIT · BSD-2 · BSD-3 · ISC · Apache-2.0 · Unlicense · Zlib | Use freely in any project |
| Weak copyleft (caution) | LGPL-2.1 · LGPL-3.0 · MPL-2.0 | Permitted. **Dynamic linking only** — static linking may trigger copyleft. ✗ flat ban |
| Strong copyleft (restricted) | GPL-2.0 · GPL-3.0 | ✗ in proprietary/distributed products; OK inside a GPL-licensed project |
| Network copyleft (high risk) | AGPL-3.0 | ✗ in SaaS/server products unless the project is itself AGPL |
| No license | Unlicensed public code | ✗ use — absent a license, all rights are reserved by default |
| Custom / proprietary | Vendor-specific terms | Legal review required before adoption |

The LGPL ruling is authoritative: **permitted with caution, dynamic linking only** — ✗ reintroduce a flat ban (ROUTER.md §8).

### Compliance Rules

| Rule | Detail |
|---|---|
| Audit on every addition | Including transitive deps |
| Automated CI scan | Fail the build on a forbidden license |
| Attribution file | Collect NOTICE/LICENSE for every permissive dep |
| Re-audit on major upgrades | A license can change between major versions (MIT `1.x` → AGPL `2.x`) |
| ✗ assume license from the parent | Each dependency carries its own license |

---

## 10. Transitive Dependencies

| Rule | Detail |
|---|---|
| Know the full tree | Audit transitives at adoption and on every update |
| Review transitive additions | New indirect deps get the same scrutiny as direct ones |
| ✗ use a transitive directly | If you import it, declare it as a direct dependency |
| Monitor transitive licenses | An incompatible license in a transitive dep is project risk |
| Depth limit | > 5 levels deep → reconsider whether the direct dep is worth it |
| Pin critical transitives | Where the manager allows: crypto · parsing · network deps, or any that caused past breakage |

| Conflict | Resolution |
|---|---|
| Two deps need incompatible versions of one transitive | Upgrade both to a compatible range; if impossible, replace one |
| Transitive has a critical vuln | Patch, override the pin, or replace the parent |
| Transitive is abandoned | Fork it, or replace the parent |
| Diamond (A→B→D, A→C→D) | Pin D to a single version compatible with both |

---

## 11. Vendoring

| Scenario | Vendor? |
|---|---|
| Air-gapped / offline builds | Yes — no network at build time |
| Critical dep with an uncertain future | Yes — insurance against disappearance |
| Local patch pending upstream merge | Yes — fork-in-repo until upstream accepts |
| Regulatory source-audit requirement | Yes — full source must be inspectable |
| Standard, stable, maintained OSS dep | No — the package manager handles it |
| Large source (> 10 MB) | Avoid — use an artifact cache instead |

| Rule | Detail |
|---|---|
| Dedicated directory | `vendor/` · `third_party/` · language convention |
| ✗ modify without a patch file | Changes tracked and re-appliable: `vendor/<lib>/patches/*.patch` |
| Record version + source URL | Provenance is traceable |
| Keep the license file | ✗ strip a license from vendored source |
| Review for security | Vendored code is now your responsibility |
| Update on the managed schedule | ✗ vendor-and-forget |

---

## 12. Internal Dependencies and Isolation

### Internal / Monorepo

| Rule | Detail |
|---|---|
| Same discipline as external | Version · pin · test · release internal shared libraries |
| Strict semver (1.0+) | Breaking = major, feature = minor, fix = patch — format → [git](../git/STANDARDS.md) |
| ✗ depend on `main` | Use tagged releases, ✗ a moving branch |
| Explicit cross-package declaration | ✗ implicit path imports across package boundaries; the build enforces the graph |
| Acyclic | A → B forbids B → A directly or transitively — a cycle is an architectural violation |
| Independent deployability | Service A deploys without rebuilding Service B |

### Isolation

| Mechanism | Isolation level |
|---|---|
| Virtual environment (venv, node_modules) | Process |
| Container | OS |
| Sandbox / jail | Kernel (untrusted deps) |
| Dependency scope (dev/test/prod) | Build |

| Rule | Detail |
|---|---|
| Isolated environment per project | ✗ global/system installs for project deps |
| Dev/test deps never ship | The build strips them from the production artifact |
| Clean CI environment | ✗ rely on cached global state from a prior build |
| Pinned base image | ✗ `FROM image:latest` — use a digest or exact tag. Supply chain → [devops](../devops/STANDARDS.md) |
| One-command setup | Reads lockfiles, installs exact versions, produces a ready environment; more than one step = incomplete |

| Scope | Ships to production? |
|---|---|
| Production (runtime deps) | Yes |
| Development (linters, formatters, type checkers) | No |
| Test (frameworks, mocks, fixtures) | No |
| Build (compilers, bundlers, codegen) | No (output ships, tools don't) |
| Optional (feature-gated) | Only if the feature is enabled |

---

## 13. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Dependency for a one-liner | 2000 lines of surface for 20 lines of value | Write it (§1) |
| Lockfile gitignored | Non-reproducible builds; drift between machines | Always commit (§4) |
| `latest` / floating tag | Silent, unreviewed upgrades | Pin exact in the lock (§4) |
| Auto-merge dependency PRs | Malicious/breaking update ships unreviewed | Human review (§8) |
| Core logic imports a third-party type | Library swap becomes a rewrite | Wrapper at a boundary (§3) |
| Flat-banning LGPL | Loses usable deps on a false premise | Weak-copyleft-caution, dynamic link (§9) |
| Vendor-and-forget | Vendored code rots with unpatched vulns | Update on the managed schedule (§11) |
| Internal dep on `main` | Downstream breaks on an upstream push | Tagged releases (§12) |
| Scanning the manifest not the lockfile | Misses the actually-resolved versions | Scan the lockfile (§7) |

---

## 14. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Justification | Informal | Commit message | Formal decision record |
| Wrapper pattern | Not required | Wrap critical deps | Wrap all external deps |
| Pinning | Lockfile | Lock + manifest ranges | Lock + ranges + hash verification |
| Lockfile committed | Yes | Yes | Yes — CI enforces freshness |
| Reproducible build | Best effort | Deterministic output | Verified digest match in CI |
| SBOM | ✗ | Generated per build | Published + diffed + feeds scanning |
| Supply-chain integrity | Hash verify | + signature/provenance verify | + SLSA target + confusion/typosquat defense |
| Vuln scanning | Manual pre-release | CI on every PR | CI + nightly + deploy gate |
| Update cadence | Ad hoc | Monthly review | Bi-weekly scan + monthly review |
| License audit | Direct deps | Automated on direct | Full tree + attribution file |
| Isolation | Virtual env | + scoped deps | Container + venv + scoped deps |

Transitions: PoC → Small — commit a lockfile, wrap critical deps. Small → Production — enable vuln + license scanning, SBOM, decision records, provenance verification, full isolation + deploy gates.

---

## 15. Checklist

- [ ] Every dependency has a written justification; ≥ 2 alternatives were considered
- [ ] Standard library preferred where it covers the need
- [ ] Each external library is wrapped; core logic imports no third-party types
- [ ] The swap test passes — removing a library breaks only its wrapper
- [ ] Exact versions pinned in the lockfile; ranges in the manifest
- [ ] Lockfile committed; CI enforces its freshness and integrity hashes
- [ ] Build is reproducible — identical inputs yield an identical artifact
- [ ] SBOM generated every build in SPDX or CycloneDX and retained with the release
- [ ] Install verifies integrity hashes; artifacts are signed/attested where available
- [ ] Registry pinned per package — no dependency-confusion path to a public registry
- [ ] New dependency names verified against typosquats by a second reviewer
- [ ] Vulnerability scan runs on every CI build against the lockfile
- [ ] Patch SLAs enforced: critical 24 h · high 1 week · medium 1 month
- [ ] Vuln exceptions carry a mitigation, an expiry date, and a named owner
- [ ] Updates land one dependency per commit with the lockfile diff reviewed
- [ ] No `latest`/floating tags; no auto-merged dependency PRs
- [ ] Every dependency license classified against the tier table
- [ ] LGPL treated as weak-copyleft-caution (dynamic linking) — not flat-banned
- [ ] No strong/network copyleft or unlicensed code in a proprietary product
- [ ] License scan fails CI on a forbidden license; attribution file maintained
- [ ] Transitive tree audited; critical transitives pinned
- [ ] Vendored code carries a patch file, source URL, and its license
- [ ] Internal deps use tagged releases and strict semver; the dependency graph is acyclic
- [ ] Dev/test/build deps are stripped from the production artifact
- [ ] Environment setup is a single command; base images pinned by digest or exact tag
