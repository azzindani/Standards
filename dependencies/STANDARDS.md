# Dependency Management Standards

Rules for acquiring, isolating, updating, and auditing external and internal
dependencies across all projects. Language-agnostic — language-specific
tooling rules belong in their respective standards.

Composable with: architecture/STANDARDS.md §3, security/STANDARDS.md,
cicd/STANDARDS.md, configuration/STANDARDS.md.

---

## Table of Contents

1. [Dependency Philosophy](#1-dependency-philosophy)
2. [Wrapper Pattern](#2-wrapper-pattern)
3. [Version Pinning](#3-version-pinning)
4. [Lock Files](#4-lock-files)
5. [Update Strategy](#5-update-strategy)
6. [Vulnerability Scanning](#6-vulnerability-scanning)
7. [Dependency Evaluation](#7-dependency-evaluation)
8. [Transitive Dependencies](#8-transitive-dependencies)
9. [Vendoring](#9-vendoring)
10. [License Compliance](#10-license-compliance)
11. [Internal Dependencies](#11-internal-dependencies)
12. [Dependency Isolation](#12-dependency-isolation)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Dependency Philosophy

Every dependency = liability. Each one adds attack surface, maintenance burden,
upgrade risk, build complexity, and license obligation. Minimize count ruthlessly.

### Core Rules

| Rule | Rationale |
|---|---|
| Justify every addition in writing | Forces cost-benefit analysis before adoption |
| Prefer standard library over third-party | Standard library matches language lifecycle |
| Prefer one dep that does three things over three deps | Fewer moving parts, fewer conflicts |
| ✗ add dependency for trivial functionality | Write 20 lines instead of importing 2000 |
| Remove unused dependencies on every release | Dead deps still carry vulnerability + license risk |
| Count dependencies as part of project complexity | More deps = harder to build, test, audit, deploy |

### Dependency Justification

Before adding any dependency, answer:

| Question | Fail condition |
|---|---|
| What problem does it solve? | Vague answer → write it yourself |
| How much of it do you use? | <20% of surface area → too heavy |
| What happens if it is abandoned? | No fork path → unacceptable risk |
| Can standard library cover it? | Yes → use standard library |
| Does it pull transitive deps? | >5 transitive → evaluate alternatives |
| What is its license? | Incompatible → reject immediately |

---

## 2. Wrapper Pattern

All third-party libraries are wrapped at tier boundaries. Core logic (Tier 0–1)
never calls third-party code directly. See architecture/STANDARDS.md §3.

### Wrapper Rules

| Rule | Detail |
|---|---|
| One wrapper per external library | Single point of contact between project and dependency |
| Wrapper exposes project-native types | Internal code never imports third-party types directly |
| Wrapper lives at Tier 3 (Interface) | Or at Tier 2 boundary if library is pure logic |
| Swap test: remove library, only wrapper breaks | If core logic breaks → wrapper is leaking |
| Wrapper is thin — translation only | ✗ business logic in wrappers |
| Standard library exemption | Language stdlib used directly, no wrapper needed |

### Wrapper Scope

| What to wrap | What NOT to wrap |
|---|---|
| HTTP clients | Language builtins (string, math, collections) |
| Database drivers | Standard library I/O |
| Serialization libraries | Language type system features |
| Cloud SDKs | Build tool plugins |
| Logging frameworks | Test frameworks (test-time only) |
| Templating engines | Development-only tooling (linters, formatters) |

### Wrapper Contract

Each wrapper must:
- Accept and return project-native types only
- Translate between project types and library types internally
- Handle library-specific exceptions, convert to project error types
- Expose only the subset of library functionality actually used
- Document which library version it targets

---

## 3. Version Pinning

### Pinning Rules

| Context | Version format | Rationale |
|---|---|---|
| Lock file | Exact: `1.2.3` | Reproducible builds — byte-identical output |
| Project metadata (manifest) | Range: `>=1.2,<2.0` | Allows compatible resolution across consumers |
| Internal shared library | Exact in lock, range in manifest | Same discipline as external deps |
| Development tools | Exact in lock file | Linter version drift causes spurious failures |

### Version Constraints

| Constraint | Rule |
|---|---|
| Minimum version | Always specify — bare `*` is prohibited |
| Maximum version | Use next-major ceiling: `<2.0` for `1.x` series |
| Pre-release versions | ✗ in production dependencies; allowed in dev-only |
| Multiple major versions | ✗ two major versions of same dep in one project |

### Reproducibility Requirement

Given identical source + lock file + build tooling version, builds produce
identical output on any machine. If they don't, the pinning strategy is broken.

---

## 4. Lock Files

### Rules

| Rule | Detail |
|---|---|
| Always commit lock files to version control | Lock file = reproducibility guarantee |
| One canonical lock file per deployable unit | Monorepo: one per package/service, not one global |
| Regenerate lock on every dependency change | Manual edit of lock file is prohibited |
| CI validates lock file freshness | Build fails if lock file is stale or missing |
| Lock file includes integrity hashes | Checksum verification prevents supply-chain tampering |
| ✗ `.gitignore` lock files | Ever. For any reason. |

### Lock File Hygiene

| Action | When |
|---|---|
| Regenerate from scratch | Quarterly, or after major dependency upgrade |
| Diff-review lock file changes | Every PR that modifies dependencies |
| Verify hash integrity | Every CI build |
| Audit transitive additions | When lock file diff introduces new packages |

---

## 5. Update Strategy

### Update Classification

| Category | Timeline | Process |
|---|---|---|
| Critical security patch (CVE, actively exploited) | Within 24 hours | Hotfix branch → expedited review → deploy |
| High-severity vulnerability (CVSS ≥ 7.0) | Within 1 week | Normal PR → prioritized review |
| Medium-severity vulnerability (CVSS 4.0–6.9) | Within 1 month | Batched with scheduled update cycle |
| Low-severity vulnerability (CVSS < 4.0) | Next scheduled cycle | Batched update |
| Feature update (minor version) | Scheduled cycle | Batched, tested, reviewed |
| Major version upgrade | Planned migration | Dedicated branch, migration plan, extended testing |

### Update Process

| Step | Detail |
|---|---|
| 1. Review changelog | Understand what changed — ✗ blind update |
| 2. Check breaking changes | Major version bumps require migration plan |
| 3. Update in isolation | One dependency per commit for bisectability |
| 4. Run full test suite | Including integration tests, not just unit |
| 5. Review lock file diff | Verify transitive changes are expected |
| 6. Deploy to staging first | Production deploy only after staging validation |

### Scheduled Update Cadence

| Project scale | Cadence |
|---|---|
| PoC / Script | Ad hoc — update when needed |
| Small project | Monthly review cycle |
| Production system | Bi-weekly automated scan + monthly manual review |

### ✗ Forbidden Update Practices

- Auto-merge dependency update PRs without review
- Update multiple unrelated deps in single commit
- Skip changelog review
- Update production deps without running tests
- Pin to `latest` or floating tags

---

## 6. Vulnerability Scanning

### Scanning Rules

| Rule | Detail |
|---|---|
| Automated scan on every CI build | Catch vulnerabilities before merge |
| Scan lock file, not manifest | Lock file reflects actual resolved versions |
| Block merge on critical/high severity | ✗ ship known high-severity vulnerabilities |
| Scan transitive dependencies | Vulnerabilities hide in indirect deps |
| Maintain exception list with expiry dates | Acknowledged vulns get documented deadline, not ignored |
| Scan container images separately | OS-level packages have independent vulnerability surface |

### Severity Thresholds

| Severity | CI gate | Remediation deadline |
|---|---|---|
| Critical (CVSS ≥ 9.0) | Block merge + alert | 24 hours |
| High (CVSS 7.0–8.9) | Block merge | 1 week |
| Medium (CVSS 4.0–6.9) | Warn, allow merge | 1 month |
| Low (CVSS < 4.0) | Log only | Next scheduled cycle |

### Exception Process

When a vulnerability cannot be remediated immediately:

| Field | Required |
|---|---|
| CVE identifier | Yes |
| Affected dependency + version | Yes |
| Justification for exception | Yes — ✗ "will fix later" without reasoning |
| Mitigation in place | Yes — compensating control or reduced exposure |
| Expiry date | Yes — exception auto-expires, forces re-evaluation |
| Owner | Yes — named person, not team |

### Scanning Pipeline Integration

See cicd/STANDARDS.md for pipeline stage placement. Vulnerability scans run:
- Pre-merge: on every PR that modifies dependency files
- Post-merge: nightly on main/default branch
- Pre-deploy: as deploy gate for production releases

---

## 7. Dependency Evaluation

### Evaluation Criteria

Score each candidate dependency before adoption. All criteria must pass minimum
threshold — one failure vetoes adoption.

| Criterion | Minimum threshold | Red flag |
|---|---|---|
| Maintenance activity | Commit in last 6 months | No commit in 12+ months |
| Issue response time | Maintainer responds within 30 days | Issues unanswered for 90+ days |
| Release cadence | At least 1 release/year | Last release > 2 years ago |
| Test suite | Tests exist and pass in CI | No tests or broken CI |
| Documentation | API docs + usage guide | No docs beyond README stub |
| License | OSI-approved, compatible with project | No license, AGPL (if shipping SaaS), or custom |
| Transitive dependency count | ≤ 10 transitive deps | > 20 transitive deps |
| Download/usage metrics | Established user base | < 100 weekly downloads (context-dependent) |
| Security track record | No unpatched critical CVEs | History of slow vulnerability response |
| Bus factor | ≥ 2 active maintainers | Single maintainer, no org backing |
| Binary size / footprint | Proportional to value provided | Adds > 10% to total binary for minor feature |

### Decision Record

Every new dependency addition requires a decision record:

| Field | Content |
|---|---|
| Dependency name + version | Exact version being adopted |
| Problem it solves | Concrete use case, not "might be useful" |
| Alternatives considered | Minimum 2 alternatives evaluated (including "write it ourselves") |
| Evaluation scores | Criteria table filled per above |
| Wrapper plan | Which module wraps it, what interface it exposes |
| Exit strategy | How to remove or replace if needed |

---

## 8. Transitive Dependencies

### Awareness Rules

| Rule | Detail |
|---|---|
| Know your full dependency tree | Audit transitive deps at adoption and on updates |
| Review transitive additions in lock diffs | New indirect deps require same scrutiny as direct |
| ✗ depend on transitive dep directly | If you use it, declare it as direct dependency |
| Monitor transitive dep licenses | Incompatible license in transitive dep = project risk |
| Transitive depth limit | > 5 levels deep → evaluate if direct dep is worth it |

### Conflict Resolution

| Scenario | Resolution |
|---|---|
| Two deps require incompatible versions of same transitive | Upgrade both to compatible range; if impossible → replace one |
| Transitive dep has critical vulnerability | Patch, override, or replace parent dep |
| Transitive dep is abandoned | Fork transitive, or replace parent dep |
| Diamond dependency (A→B→D, A→C→D) | Pin D to single version compatible with both B and C |

### Transitive Pinning

When package manager supports it, pin critical transitive dependencies explicitly.
Critical = transitive deps that handle security-sensitive operations (crypto, parsing,
network) or that have caused past breakage.

---

## 9. Vendoring

### When to Vendor

| Scenario | Vendor? | Rationale |
|---|---|---|
| Air-gapped / offline builds required | Yes | No network access at build time |
| Critical dependency with uncertain future | Yes | Insurance against disappearance |
| Need to patch upstream bug locally | Yes | Fork-in-repo until upstream merges fix |
| Regulatory requirement for source audit | Yes | Full source must be inspectable |
| Standard open-source dep, stable, maintained | No | Package manager handles it |
| Large dependency (>10MB source) | Avoid | Bloats repository; use artifact cache instead |

### Vendoring Rules

| Rule | Detail |
|---|---|
| Vendored code lives in dedicated directory | `vendor/`, `third_party/`, or language convention |
| ✗ modify vendored code without patch file | Changes must be trackable and re-appliable |
| Record original version + source URL | Provenance must be traceable |
| License file included with vendored code | Legal requirement — ✗ strip license from vendored source |
| Review vendored code for security | Vendored = your responsibility now |
| Update vendored code on same schedule as managed deps | ✗ vendor-and-forget |
| Patch files stored alongside vendored source | `vendor/lib-name/patches/*.patch` |

---

## 10. License Compliance

### License Tiers

| Tier | Licenses | Usage rule |
|---|---|---|
| Permissive (preferred) | MIT, BSD-2, BSD-3, ISC, Apache-2.0, Unlicense, Zlib | Use freely in any project |
| Weak copyleft (caution) | LGPL-2.1, LGPL-3.0, MPL-2.0 | Dynamic linking ok; static linking may trigger copyleft |
| Strong copyleft (restricted) | GPL-2.0, GPL-3.0 | ✗ in proprietary projects; ok in GPL-licensed projects |
| Network copyleft (high risk) | AGPL-3.0 | ✗ in SaaS/server applications unless project is AGPL |
| No license | Unlicensed code on public repos | ✗ use — no license = all rights reserved by default |
| Custom / proprietary | Vendor-specific terms | Legal review required before adoption |

### Compliance Rules

| Rule | Detail |
|---|---|
| Audit licenses on every dependency addition | Including transitive deps |
| Maintain project-level license compatibility matrix | Document which license tiers are acceptable |
| Automate license scanning in CI | Fail build on forbidden license detected |
| Attribution file for all permissive deps | Collect NOTICE/LICENSE per dependency |
| Re-audit on major version upgrades | License can change between major versions |
| ✗ assume license from parent project | Each dependency has its own license |

### License Change Detection

Monitor dependencies for license changes across versions. A dependency that
was MIT in v1.x may become AGPL in v2.x. Lock file review + automated
scanning catches this at update time, not after deployment.

---

## 11. Internal Dependencies

### Shared Library Rules

| Rule | Detail |
|---|---|
| Shared internal libraries follow same discipline as external deps | Version, pin, test, release |
| Semantic versioning for all internal packages | Breaking change = major bump |
| ✗ depend on internal library's `main` branch directly | Use tagged releases |
| Internal library has its own test suite + CI | ✗ rely on downstream projects to validate library |
| API stability contract | Public API changes follow deprecation protocol |

### Monorepo Dependencies

| Rule | Detail |
|---|---|
| Explicit dependency declaration between packages | ✗ implicit path imports across package boundaries |
| Build system enforces dependency graph | Unauthorized cross-package imports fail the build |
| Shared code extracted into explicit internal package | ✗ reach into another service's source directory |
| Version pinning within monorepo | Workspace protocol or explicit version references |
| Independent deployability | Service A deploys without rebuilding Service B |

### Internal Library Versioning

| Stage | Version strategy |
|---|---|
| Pre-1.0 (unstable) | `0.x.y` — breaking changes allowed in minor bumps |
| Stable (1.0+) | Strict semver — breaking = major, features = minor, fixes = patch |
| Deprecation | Mark deprecated in `1.x`, remove in `2.0` |

### Dependency Direction in Monorepos

Follows architecture/STANDARDS.md §3 — dependencies form a DAG. If package A
depends on package B, package B must never depend on package A, directly or
transitively. Circular dependencies between internal packages are architectural
violations.

---

## 12. Dependency Isolation

### Isolation Mechanisms

| Mechanism | Use case | Isolation level |
|---|---|---|
| Virtual environment | Language-level dep isolation (Python venv, Node node_modules) | Process |
| Container | Full OS-level isolation, reproducible runtime | OS |
| Sandbox / jail | Untrusted dependency execution | Kernel |
| Dependency scope (dev/prod/test) | Separate deps by lifecycle phase | Build |
| Workspace / package boundary | Monorepo internal isolation | Project |

### Isolation Rules

| Rule | Detail |
|---|---|
| Every project has isolated dependency environment | ✗ global/system package installs for project deps |
| Dev dependencies never ship to production | Build system strips dev-only deps from production artifact |
| Test dependencies isolated from production deps | Test frameworks ✗ in production dependency tree |
| CI builds in clean environment | ✗ rely on cached global state from previous builds |
| Container builds start from pinned base image | `FROM image:latest` is prohibited — use digest or exact tag |

### Scope Classification

| Scope | Contains | Ships to production? |
|---|---|---|
| Production | Runtime dependencies | Yes |
| Development | Linters, formatters, type checkers, build tools | No |
| Test | Test frameworks, mocking libraries, fixtures | No |
| Build | Compilers, bundlers, code generators | No (output ships, tools don't) |
| Optional | Feature-gated dependencies, plugins | Only if feature enabled |

### Environment Reproducibility

Development environment setup must be a single command. That command reads lock
files, installs exact pinned versions, and produces a ready-to-use environment.
If setup requires manual steps beyond one command → automation is incomplete.

---

## 13. Scale Matrix

Apply dependency management rigor proportionally to project scale.
See architecture/STANDARDS.md §12 for scale definitions.

| Practice | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Dependency justification | Informal | Written in commit message | Formal decision record |
| Wrapper pattern | Not required | Wrap critical deps | Wrap all external deps |
| Version pinning | Lock file sufficient | Lock file + ranges in manifest | Lock file + ranges + hash verification |
| Lock file committed | Yes | Yes | Yes — CI enforces freshness |
| Update cadence | Ad hoc | Monthly review | Bi-weekly scan + monthly review |
| Vulnerability scanning | Manual before release | CI on every PR | CI + nightly + deploy gate |
| Dependency evaluation | Quick assessment | Criteria checklist | Full evaluation + decision record |
| Transitive dep awareness | Know direct deps | Review transitives on add | Full tree audit + critical transitive pinning |
| Vendoring | Not needed | Only if offline required | Per policy — critical deps may be vendored |
| License audit | Check direct deps | Automated scan on direct | Automated scan on full tree + attribution file |
| Internal dep versioning | Path references ok | Tagged versions | Strict semver + CI validation |
| Dependency isolation | Virtual env minimum | Virtual env + scoped deps | Container + virtual env + scoped deps |
| Security exception process | Not required | Documented exceptions | Formal exception with owner + expiry |

### Scale Transition

When graduating from one scale to the next, apply new practices incrementally:
1. Add lock file and commit it (PoC → Small)
2. Wrap critical external dependencies (PoC → Small)
3. Enable automated vulnerability scanning (Small → Production)
4. Formalize evaluation and decision records (Small → Production)
5. Implement full isolation + deploy gates (Small → Production)

---

## 14. Checklist

### Adding a New Dependency

- [ ] Problem it solves clearly identified
- [ ] Alternatives evaluated (minimum 2, including "write it ourselves")
- [ ] License compatible with project
- [ ] Maintenance status acceptable (commits, releases, issue response)
- [ ] Transitive dependency count reviewed
- [ ] Security track record checked (CVE history)
- [ ] Bus factor ≥ 2 (or risk acknowledged + exit strategy documented)
- [ ] Wrapper module created (production scale)
- [ ] Wrapper exposes project-native types only
- [ ] Version pinned in lock file
- [ ] Range specified in manifest
- [ ] Decision record written (production scale)
- [ ] CI passes with new dependency

### Updating Dependencies

- [ ] Changelog reviewed for breaking changes
- [ ] Single dependency per commit
- [ ] Lock file diff reviewed (transitive changes inspected)
- [ ] Full test suite passes
- [ ] License unchanged or still compatible
- [ ] No new critical/high vulnerabilities introduced
- [ ] Staging validation before production deploy

### Periodic Review (Monthly/Quarterly)

- [ ] Unused dependencies removed
- [ ] Vulnerability scan results reviewed
- [ ] Security exceptions re-evaluated (expired ones remediated)
- [ ] Lock file regenerated from scratch (quarterly)
- [ ] License audit up to date
- [ ] Transitive dependency tree reviewed for unexpected growth
- [ ] Internal library versions current
- [ ] Vendored dependencies updated if applicable

### Project Setup

- [ ] Dependency isolation mechanism in place (venv, container, etc.)
- [ ] Lock file exists and is committed
- [ ] CI validates lock file freshness
- [ ] Vulnerability scanning enabled in CI pipeline
- [ ] License scanning enabled in CI pipeline
- [ ] Dev/test/prod dependency scopes properly separated
- [ ] Single-command environment setup works
- [ ] Wrapper pattern established for external dependencies
