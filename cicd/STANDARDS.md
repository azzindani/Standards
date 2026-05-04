# CI/CD Pipeline Standards

Rules for continuous integration and continuous deployment pipelines.
Every commit potentially deployable. Every repeatable action automated.
Fast feedback, reproducible builds, immutable artifacts.

Pairs with `testing/STANDARDS.md` — CI/CD executes the test suites and
reality dimensions defined there. Every test stage below names which
testing dimension it gates; every reality dimension in testing names
which CI/CD stage runs it. Confidence Level (`testing/STANDARDS.md §1`)
determines which suites must pass before deploy.

Composable with: Testing · Git · Security · Dependencies · DevOps.

---

## Table of Contents

1. [Pipeline Philosophy](#1-pipeline-philosophy)
2. [Pipeline Stages](#2-pipeline-stages)
3. [Lint Stage](#3-lint-stage)
4. [Build Stage](#4-build-stage)
5. [Test Stage](#5-test-stage)
6. [Security Stage](#6-security-stage)
7. [Artifact Management](#7-artifact-management)
8. [Deployment Stages](#8-deployment-stages)
9. [Environment Parity](#9-environment-parity)
10. [Pipeline Speed](#10-pipeline-speed)
11. [Secrets in Pipeline](#11-secrets-in-pipeline)
12. [Branch Pipeline Rules](#12-branch-pipeline-rules)
13. [Rollback Strategy](#13-rollback-strategy)
14. [Release Process](#14-release-process)
15. [Cross-Platform Matrix](#15-cross-platform-matrix)
16. [Scale Matrix](#16-scale-matrix)
17. [CI/CD Checklist](#17-cicd-checklist)

---

## 1. Pipeline Philosophy

| Principle | Rule |
|---|---|
| Every commit is deployable | Trunk never breaks. Broken commit → immediate fix or revert. |
| Automate everything repeatable | Manual steps = future incidents. If done twice, script it. |
| Fast feedback | Developer learns of failure within minutes, not hours. |
| Build once, deploy many | One build artifact flows through all environments. ✗ rebuild per environment. |
| Pipeline is code | Pipeline definition lives in repo, version-controlled, reviewed like application code. |
| Fail fast, fail loud | First failure stops pipeline. ✗ continue past broken stage. |
| Reproducibility | Same commit + same config = identical output every time. |
| Immutable artifacts | Published artifact never modified. New version → new artifact. |
| Least privilege | Pipeline has minimum permissions required per stage. ✗ admin credentials everywhere. |
| Auditability | Every deployment traceable to commit, build, approver, timestamp. |

### Non-Negotiables

- Pipeline runs on every push. ✗ manual-only CI.
- Pipeline definition changes go through code review.
- Pipeline failures block merge. ✗ override without documented reason.
- Pipeline output deterministic — flaky tests fixed or quarantined immediately.

---

## 2. Pipeline Stages

Ordered sequence. Each stage gates the next. Failure at any stage halts progression.

```
lint → build → unit test → integration test → security scan → deploy(dev) → deploy(staging) → deploy(production)
```

### Stage Rules

| Stage | Gate | Runs On | Max Duration |
|---|---|---|---|
| Lint | All checks pass, zero warnings in CI | Every push | 2 min |
| Build | Compiles/packages without error | Every push | 3 min |
| Unit Test | 100% pass, coverage threshold met | Every push | 3 min |
| Integration Test | All contract + integration tests pass | PR merge to trunk | 5 min |
| Security Scan | Zero critical/high vulnerabilities | PR merge to trunk | 3 min |
| Deploy (dev) | All prior stages green | Trunk merge | 2 min |
| Deploy (staging) | Dev deployment healthy for N minutes | After dev soak | 2 min |
| Deploy (production) | Staging smoke tests pass + approval | Manual trigger or auto | 5 min |

### Stage Dependencies

- Stages run sequentially by default. Parallel only where no data dependency exists.
- Lint + Build + Unit Test may run in parallel if independent.
- Integration Test runs only after Build succeeds (needs artifact).
- Security Scan runs after Build (scans built artifact + dependencies).
- Deploy stages strictly sequential: dev → staging → production.

---

## 3. Lint Stage

Enforces code consistency before any build or test resources consumed.

### What Lint Covers

| Check | Purpose | Failure Action |
|---|---|---|
| Code formatting | Consistent style | Block merge |
| Static analysis | Catch bugs without execution | Block merge |
| Type checking | Type errors caught early | Block merge |
| Import ordering | Deterministic imports | Block merge |
| Determinism violations | ✗ wall-clock · random · UUID without injection (`testing/STANDARDS.md §14`) | Block merge |
| Dead code detection | Remove unused code | Warn (block in production) |
| Complexity metrics | Flag threshold exceeders | Warn |
| Commit message format | Enforce conventional commits | Block merge |

### Lint Rules

- Linter config in repo root, version-controlled.
- CI lint config identical to local. ✗ divergent rules.
- Lint runs before build — cheapest check first.
- Auto-fixable issues fixed locally before push (pre-commit hook). CI verifies, ✗ auto-fixes.
- New rules applied incrementally — existing violations tracked, new violations blocked.
- Warnings promoted to errors in CI. ✗ warning-only mode.
- Determinism enforcement runs alongside type check — gates §14 of testing standard at lint time, ✗ runtime.

See `testing/STANDARDS.md §14` for determinism rules · §20 for test-specific lint.

---

## 4. Build Stage

Produces deployable artifact from source. Deterministic, reproducible, environment-agnostic.

### Build Rules

| Rule | Detail |
|---|---|
| Reproducible | Same commit → byte-identical output (where toolchain supports) |
| Deterministic dependencies | Lock files pinned. ✗ floating versions in CI. See `dependencies/STANDARDS.md` |
| Build once | Single artifact used across dev/staging/production. ✗ rebuild per env. |
| No environment config baked in | Configuration injected at deploy time, not build time |
| Build metadata embedded | Commit SHA, build timestamp, version tag embedded in artifact |
| Clean build environment | Build starts from clean state. ✗ rely on cached state for correctness |
| Build cache for speed | Cache dependencies + intermediate outputs. Cache = optimization, not correctness requirement |
| Compilation warnings = errors | `-Werror` or equivalent. ✗ ship with warnings |

### Build Output

- Single versioned artifact (binary, container image, package, archive).
- Artifact tagged with: version, commit SHA, build number.
- Build log captured and stored alongside artifact.
- Build failure output includes full error context — ✗ truncated logs.

---

## 5. Test Stage

Executes test pyramid + reality dimensions per `testing/STANDARDS.md`. System-level pressure / survival / penetration suites per `testing/PRESSURE.md`. This section covers pipeline execution only — strategy lives in testing standards.

### Suite Execution Mapping

Maps testing suites (`testing/STANDARDS.md §20`) → pipeline stages.

| Testing Suite | Reality Dimensions Covered | Pipeline Position | Parallel | Failure |
|---|---|---|---|---|
| Unit | Correctness · property · contract · fast adversarial · time-boundary | Every push | Yes — per-module | Blocks merge |
| Integration | Boundary · faults (§10) · concurrency unit · resources w/ limits (§13) · observability (§17) · recovery (§18) | Every push | Limited — shared resources | Blocks merge |
| E2E | Full workflow | Pre-merge | No — sequential | Blocks merge |
| Scenario | Multi-step journeys (§7) | Nightly · pre-prod | Limited | Blocks promotion |
| Long-run | State accumulation (§15) · leak · stress (§12) | Nightly | Yes — per-target | Notify, ✗ block merge |
| Fuzz | Adversarial (§11) | Nightly | Yes — per-target | Crash = P1, blocks merge |
| Mutation | Test effectiveness (§19) | Nightly | Weekly | Yes — per-module | L5 gates release |
| Replay | Drift (§16) · prod traces | Pre-prod deploy | No — sequential | Blocks promotion |
| Performance | Budgets (§25) | Nightly | Yes | Regression > 20% blocks |
| Pressure (`PRESSURE.md §3`) | Stress · endurance · capacity | Nightly + per release | No — dedicated runner | Regression > 20% blocks release |
| Survival (`PRESSURE.md §4`) | Multi-fault · cascading · chaos | Nightly · weekly full matrix | No — pre-prod env | Single-fault blocks; multi-fault if user-facing |
| Penetration (`PRESSURE.md §5`) | Auth · authz · session · server-side · logic flaws | Nightly + per release | Yes — staging | Critical/High blocks release |

### Confidence Level → Required Suites

Per `testing/STANDARDS.md §1`. CI gates by declared level.

| Level | Suites Gating Merge | Suites Gating Deploy |
|---|---|---|
| L1 | Unit (happy path) | Unit |
| L2 | Unit + Contract + Property | Unit + Integration |
| L3 | + Faults · Adversarial · Concurrency | + E2E + Pen tests (auth/authz/session) |
| L4 | + Resources · Time · Observability · Recovery | + Scenario + Long-run nightly green + Pressure (stress/endurance/capacity) green + Survival single-fault green |
| L5 | + all of L4 | + Mutation green · Replay green · Chaos nightly green · Pen full corpus green · annual red-team current |

### Rules

- All tests run in isolated environments. ✗ shared state between runs.
- Test DB/state fresh per run. ✗ leftover data dependency.
- Machine-readable output (JUnit XML, TAP, or equivalent). Results published to CI dashboard every run.
- Flaky test → quarantine immediately. Max 7 days before fix or delete (`testing/STANDARDS.md §3`).
- Coverage threshold enforced, ratchets — ✗ decreases (`testing/STANDARDS.md §22`).
- Per-suite + per-test timeout enforced. Hung test ✗ blocks pipeline indefinitely.
- Race detector enabled in CI when toolchain supports (`testing/STANDARDS.md §12`).
- Resource tests run with explicit cgroup/ulimit (`testing/STANDARDS.md §13`), ✗ host defaults.
- Replay corpus runs in pre-prod env, ✗ against production.

### Parallelization

- Unit split per module/package across runners. Each runner = independent env.
- Test order randomized to catch hidden dependencies.
- Results aggregated after all runners complete.
- Cross-platform matrix (§15) parallelizes across OS runners.

---

## 6. Security Stage

Automated security checks integrated into pipeline. Shift security left —
catch vulnerabilities before deploy, not after incident.

See `security/STANDARDS.md` for security rules. This section covers pipeline integration.

### Security Checks in Pipeline

| Check | Stage Position | Blocks Deploy | Tool Category |
|---|---|---|---|
| Dependency audit | After build | Yes — critical/high | SCA (Software Composition Analysis) |
| Secret scanning | Pre-commit + CI | Yes — any finding | Secret detection |
| SAST (static analysis) | After lint | Yes — critical/high | Static Application Security Testing |
| Container scanning | After container build | Yes — critical/high | Container vulnerability scanning |
| License compliance | After dependency resolution | Yes — copyleft in proprietary | License checker |
| DAST (dynamic testing) | Post-deploy to staging | Yes — critical | Dynamic Application Security Testing |

### Security Stage Rules

- Dependency audit runs against lock file, not floating versions. See `dependencies/STANDARDS.md`.
- Known vulnerability exceptions documented with: CVE, justification, expiry date, owner.
- Exception expires → pipeline blocks until renewed or fixed.
- Secret scanning covers: API keys, tokens, passwords, private keys, certificates.
- Secret detected in commit history → rotate immediately. ✗ just remove from current commit.
- SAST rules tuned to reduce false positives. False positive rate > 20% → retune before next release.
- Security scan results stored per build — audit trail required.

### Severity → Action Map

| Severity | Action | Timeline |
|---|---|---|
| Critical | Block deploy. Fix immediately. | Same day |
| High | Block deploy. Fix before next release. | Within sprint |
| Medium | Track in backlog. ✗ block deploy. | Next 2 sprints |
| Low | Track. Fix opportunistically. | Best effort |
| Informational | Log only. Review quarterly. | Quarterly |

---

## 7. Artifact Management

Artifacts = build outputs stored for deployment. Versioned, immutable, traceable.

### Artifact Rules

| Rule | Detail |
|---|---|
| Immutable | Published artifact never modified. Fix → new version. |
| Versioned | Every artifact has unique version. Semantic versioning required. See §14. |
| Signed | Production artifacts cryptographically signed. Verify before deploy. |
| Reproducible | Same source + same toolchain → same artifact. |
| Retention policy | Dev: 7 days · Staging: 30 days · Production: 1 year minimum |
| Single source of truth | One artifact registry per artifact type. ✗ duplicate registries. |
| Promotion, not rebuild | Artifact promoted between environments. ✗ rebuild for each env. |
| Metadata | Each artifact stores: version, commit SHA, build ID, timestamp, builder |

### Artifact Types

| Type | Registry | Naming Convention |
|---|---|---|
| Container image | Container registry | `<service>:<semver>-<sha7>` |
| Binary / executable | Binary store | `<name>-<semver>-<os>-<arch>` |
| Library / package | Language package registry | `<name>@<semver>` |
| Configuration bundle | Config store | `<service>-config-<semver>` |
| Database migration | Migration store | `<timestamp>-<description>` |

### Cleanup

- Automated cleanup of untagged/expired artifacts.
- Artifacts referenced by any deployment ✗ eligible for cleanup.
- Cleanup runs daily. Alert on storage > 80% capacity.

---

## 8. Deployment Stages

Progressive deployment through environments. Each environment validates before promotion.

### Environment Progression

```
dev → staging → production
```

| Environment | Purpose | Deploy Trigger | Rollback |
|---|---|---|---|
| Dev | Integration validation | Automatic on trunk merge | Automatic |
| Staging | Pre-production validation | Automatic after dev soak | Automatic |
| Production | Live traffic | Manual approval or auto after staging soak | Automatic + manual option |

### Promotion Rules

- Artifact promoted, not rebuilt. Same binary/image in every environment.
- Promotion requires all prior environment checks green.
- Production promotion requires: staging smoke tests pass + health check green + approval (if manual).
- Rollback artifact always available. Previous known-good version retained.
- Blue-green or canary deployment for production. ✗ in-place overwrite without rollback path.

### Deployment Rules

| Rule | Detail |
|---|---|
| Zero-downtime | Production deploys ✗ cause service interruption |
| Health check gate | New version must pass health check before receiving traffic |
| Traffic shift | Canary: 5% → 25% → 50% → 100% with monitoring at each step |
| Soak time | Dev: 5 min · Staging: 15 min · Production: canary 15 min per step |
| Deployment window | Production deploys during business hours (team available for rollback) |
| Deploy lock | One deployment at a time per service. ✗ concurrent deploys. |
| Deployment record | Every deploy logged: who, what version, when, from which build |

### Deployment Strategies

| Strategy | When to Use | Rollback Speed |
|---|---|---|
| Blue-green | Stateless services, fast switchover needed | Instant (switch back) |
| Canary | High-traffic services, gradual validation | Fast (route to old) |
| Rolling | Stateful services, resource-constrained | Medium (roll back instances) |
| Recreate | Dev/staging only, downtime acceptable | Slow (full redeploy) |

---

## 9. Environment Parity

Staging mirrors production. Differences between environments = deployment risk.

### Parity Rules

| Dimension | Requirement |
|---|---|
| Infrastructure | Same OS, runtime versions, resource shape (scaled down ok, different stack ✗) |
| Configuration | Same config keys. Values differ by environment (injected at deploy). |
| Data shape | Staging uses production schema. Synthetic data matching production patterns. |
| Dependencies | Same service versions. ✗ staging on v2 while production on v1. |
| Networking | Same topology. Load balancer, DNS, TLS present in staging. |
| Feature flags | Staging matches production flag state unless explicitly testing new flag. |

### What Breaks Parity (✗ allowed)

- Different OS or kernel version between staging and production.
- Missing infrastructure component in staging (queue, cache, CDN).
- Test-only shortcuts (in-memory DB replacing real DB in staging).
- Manual configuration changes in any environment. All config via code.
- "Works on my machine" — local dev environment ✗ authoritative for deployment.

### Environment Configuration

- Environment-specific values stored in environment config, not in artifact.
- Config injection at deploy time via environment variables or config service.
- Sensitive config (secrets) injected via secret manager. See §11.
- Configuration drift detection — automated comparison between environments. Alert on drift.

See `configuration/STANDARDS.md` for configuration cascade rules.

---

## 10. Pipeline Speed

Slow pipeline = developers batch changes = larger failures = slower recovery.
Target: total pipeline < 10 minutes for commit-to-deploy-dev.

### Speed Targets

| Metric | Target | Hard Limit |
|---|---|---|
| Lint + Build + Unit Test | < 5 min | 10 min |
| Full pipeline (to dev deploy) | < 10 min | 20 min |
| Production deploy (after approval) | < 5 min | 15 min |
| Rollback execution | < 2 min | 5 min |
| Feedback to developer (first failure) | < 3 min | 5 min |

### Speed Optimization

| Technique | Impact | Priority |
|---|---|---|
| Dependency caching | Avoid re-downloading on every build | High |
| Build caching | Reuse unchanged compilation outputs | High |
| Test parallelization | Split test suites across runners | High |
| Incremental builds | Only rebuild changed modules | Medium |
| Docker layer caching | Reuse unchanged image layers | Medium |
| Selective test execution | Run only tests affected by changed code | Medium |
| Pre-built base images | Base image built weekly, not per pipeline | Medium |
| Pipeline step parallelization | Run independent stages concurrently | High |

### Speed Rules

- Pipeline duration tracked as metric. Alert on regression > 20%.
- New pipeline step requires impact assessment on total duration.
- Long-running tests (> 30s each) moved to post-merge pipeline, not PR pipeline.
- Build cache invalidation explicit — stale cache ✗ mask build failures.
- Pipeline infrastructure scaled to demand. Queue wait time < 1 min.

---

## 11. Secrets in Pipeline

Secrets = credentials, API keys, tokens, certificates, signing keys.
✗ hardcoded anywhere. ✗ visible in logs. ✗ stored in repo.

### Secret Rules

| Rule | Detail |
|---|---|
| ✗ hardcoded secrets | Zero secrets in source code, config files, pipeline definitions |
| ✗ secrets in logs | Pipeline masks secret values in all output |
| ✗ secrets in artifacts | Build output ✗ contains embedded credentials |
| Environment injection | Secrets injected as environment variables at runtime |
| Secret manager | All secrets stored in dedicated secret management service |
| Rotation | Secrets rotated on schedule. Max lifetime per secret type defined. |
| Least privilege | Each pipeline stage gets only secrets it needs. ✗ global secret access. |
| Audit trail | Every secret access logged: who, when, which secret |

### Secret Lifecycle

```
Create → Store (encrypted) → Inject (runtime) → Use → Rotate → Revoke
```

### Rotation Schedule

| Secret Type | Max Lifetime | Rotation Trigger |
|---|---|---|
| API keys | 90 days | Automated rotation |
| Database credentials | 90 days | Automated rotation |
| Signing keys | 1 year | Manual + automated |
| TLS certificates | 1 year (automate renewal) | Automated (30 days before expiry) |
| Service tokens | 24 hours | Automated per deploy |
| CI/CD tokens | 90 days | Automated rotation |

### Secret Leak Response

1. Revoke compromised secret immediately.
2. Rotate all secrets that shared scope with compromised secret.
3. Audit access logs for unauthorized use.
4. Scan commit history — remove if present (rewrite history as last resort).
5. Post-incident review within 48 hours.

See `security/STANDARDS.md` for broader secret management rules.

---

## 12. Branch Pipeline Rules

Different branches trigger different pipeline subsets. Balance thoroughness with speed.

See `git/STANDARDS.md` for branching strategy.

### Pipeline by Branch Type

| Branch Type | Stages Executed | Deploy Target |
|---|---|---|
| Feature branch (PR) | Lint → Build → Unit Test | None |
| PR merge to trunk | Lint → Build → Unit Test → Integration Test → Security Scan | Dev (auto) |
| Trunk (main/master) | Full pipeline | Dev → Staging (auto) |
| Release tag | Full pipeline + signing + release artifact | Production |
| Hotfix branch | Lint → Build → Unit Test → Integration Test | Staging (fast-track) |

### Branch Rules

- Feature branch pipeline runs on every push to branch.
- PR pipeline runs full test suite — ✗ merge with failing tests.
- Trunk pipeline triggers deploy to dev automatically on every merge.
- Release tag triggers production deploy pipeline (with approval gate if configured).
- Hotfix branches bypass feature branch restrictions but ✗ skip any test stage.
- Long-lived feature branches ✗ allowed. Max 3 days before merge or rebase.

### PR Pipeline Requirements

| Requirement | Enforced By |
|---|---|
| All lint checks pass | CI status check |
| All unit tests pass | CI status check |
| Coverage threshold met | CI status check |
| No critical security findings | CI status check |
| Build succeeds | CI status check |
| PR approved by reviewer | Branch protection rule |
| Branch up to date with trunk | Branch protection rule |

---

## 13. Rollback Strategy

Every deployment has a rollback plan. Rollback tested as regularly as deployment.

### Automated Rollback Triggers

| Trigger | Threshold | Action |
|---|---|---|
| Health check failure | 3 consecutive failures post-deploy | Automatic rollback |
| Error rate spike | > 5% error rate (above baseline) | Automatic rollback |
| Latency spike | p99 > 2x baseline for 2 minutes | Automatic rollback |
| Canary failure | Canary metrics worse than baseline | Stop rollout, rollback canary |
| Deployment timeout | Deploy ✗ complete within max duration | Automatic rollback |

### Rollback Rules

- Previous known-good artifact always available for instant rollback.
- Rollback = deploy previous version. ✗ rollback by reverting code and rebuilding.
- Rollback procedure tested monthly (deploy old version, verify, deploy current again).
- Database migrations forward-only by default. Rollback-safe migrations: additive changes only during deploy window.
- Backward-incompatible schema changes require two-phase deploy: expand phase (add new) → migrate → contract phase (remove old).
- Rollback ✗ requires approval gate — speed is critical. Audit after.
- Rollback event triggers incident review within 24 hours.

### Rollback Procedure

1. Detect failure (automated monitoring or manual observation).
2. Trigger rollback (automated or single-command manual).
3. Route traffic to previous version.
4. Verify previous version healthy.
5. Notify team with: what failed, which version rolled back to, timeline.
6. Root cause analysis within 24 hours.

---

## 14. Release Process

Structured release process from version bump to production deploy.

### Semantic Versioning

All releases follow semver (`MAJOR.MINOR.PATCH`).

| Component | Increment When |
|---|---|
| MAJOR | Breaking change to public API or behavior |
| MINOR | New feature, backward-compatible |
| PATCH | Bug fix, backward-compatible |

Pre-release tags: `x.y.z-alpha.1`, `x.y.z-beta.1`, `x.y.z-rc.1`.

### Release Workflow

```
Version bump → Changelog update → Tag → Pipeline → Artifact publish → Deploy
```

### Release Rules

| Rule | Detail |
|---|---|
| Version in one place | Single source of version truth (package file, version file, or tag) |
| Changelog generated | Auto-generated from conventional commits. Manual summary for major releases. |
| Release notes required | Every release has human-readable notes: what changed, migration steps if any |
| Tag triggers release | Git tag (e.g., `v1.2.3`) triggers release pipeline. ✗ manual release steps. |
| Release artifact signed | Cryptographic signature on release artifacts |
| Release immutable | Published release ✗ modified. Error → publish new patch release. |
| Rollback version available | Previous release always downloadable/deployable |

### Changelog Format

Each entry includes:
- Category: Added | Changed | Fixed | Removed | Security | Deprecated
- One-line description per change
- Issue/PR reference
- Breaking change flag (if applicable)

---

## 15. Cross-Platform Matrix

CI/CD runners support Windows · macOS · Linux as first-class environments. Tests + build run on all target OS per `testing/STANDARDS.md §26`. Matrix executes in parallel; all OSes must pass to merge.

### Runner Matrix

| OS | Runner Type | Suite Coverage | Required For |
|---|---|---|---|
| Linux | x86_64 · arm64 | Full unit + integration + container | All projects |
| Windows | Server LTSC | Full unit + integration; PowerShell scripts | Cross-platform target projects |
| macOS | x86_64 (Intel) · arm64 (Apple Silicon) | Full unit + integration; native APIs | macOS-target or polyglot projects |

### OS-Specific Stage Rules

| Stage | Linux | Windows | macOS |
|---|---|---|---|
| Lint | All linters · POSIX shell scripts via shellcheck | PowerShell ScriptAnalyzer · YAML/JSON validators | All linters · zsh scripts validated |
| Build | Native + container artifacts | Native binary, NSIS/MSI installer if shipping | Native binary, codesigned + notarized if shipping |
| Unit test | Full suite · race detector enabled | Full suite · race detector if toolchain supports | Full suite · race detector enabled |
| Integration | Full suite + container tests | Full suite · ✗ container tests (use Linux runner) | Full suite · ✗ container tests |
| E2E | Full | Full where applicable to OS-target | Full where applicable |
| Security scan | SCA + SAST + container scan | SCA + SAST | SCA + SAST |

### Matrix Rules

- All target platforms run in parallel via CI matrix. Total wall time = slowest runner, ✗ sum.
- Container-based tests run on Linux only — explicitly documented as such, ✗ skipped silently.
- Platform-specific code paths (`#ifdef`, `os.platform`, conditional imports) require platform-specific tests, OS-gated.
- Path handling via stdlib abstractions only. ✗ raw `/` or `\` in source. Lint enforces (`testing/STANDARDS.md §26`).
- Line endings normalized: source `\n` (enforced by `.gitattributes`); tests assert both `\n` and `\r\n` parsing.
- Shell scripts in build/CI: bash equivalents in `scripts/posix/`, PowerShell equivalents in `scripts/windows/`. ✗ assume one shell on all OSes.
- Encoding: source files UTF-8 (BOM-less) enforced by lint. Tests cover UTF-8 (Linux/macOS) + UTF-16/codepage (Windows) input handling.
- File-locking semantics differ — tests assert behavior on each OS where locking matters.
- Time resolution differs (Windows 100ns · POSIX ns) — performance tests use per-platform tolerance.

### Matrix Failure Handling

- Any OS fail = merge blocked. ✗ "Linux green is enough."
- OS-specific flake → quarantine the OS-specific test, ✗ disable the OS from matrix.
- Platform-specific bug = P1, fixed before next release. ✗ "Windows users can wait."
- Removing an OS from the matrix = same review weight as removing test coverage — requires explicit owner sign-off.

### Self-Hosted vs Hosted Runners

| Runner Type | Use For | Limits |
|---|---|---|
| Hosted (provider-managed) | Default. All public + most private projects. | Spec varies, time-quota'd, ephemeral. |
| Self-hosted | Specialty hardware (GPU, ARM, mainframe), restricted networks, large caches. | Patching + security ownership stays with project. |
| Dedicated pressure runner | Stress / endurance / capacity tests (`PRESSURE.md §9`). | Production-shaped; one test at a time per env; ✗ shared with regular CI workloads. |
| Pre-prod survival environment | Survival / chaos / multi-fault (`PRESSURE.md §9`). | Multi-zone topology · fault-injection layer · isolated network. |
| Staging pen-test environment | Penetration testing corpus (`PRESSURE.md §9`). | Mirrors prod auth/authz/TLS · synthetic data only · isolated from prod. |

Self-hosted runners isolated per job (fresh container/VM). ✗ persist state between jobs. ✗ shared filesystem across builds. Pressure / survival / pen environments retain state between runs (capacity baselines, attack corpora) but reset per-test on demand.

---

## 16. Scale Matrix

Apply pipeline rules proportionally to project scale. Cross-references `testing/STANDARDS.md §28` (testing scale matrix) — confidence level there gates pipeline gates here.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Pipeline definition | Shell script or single CI file | Standard CI config | Multi-stage pipeline as code |
| Lint stage | Formatter only | Formatter + static analysis | Full lint + type check + determinism enforcement |
| Build stage | Direct run | Single build command | Reproducible, cached, multi-target |
| Test stage | Unit smoke | Unit + basic integration | Full suites per Confidence Level (§5) |
| Reality dimensions (§5) | ✗ required | Faults + adversarial on critical paths | All per `testing/STANDARDS.md §28` |
| System-level dimensions (§5) | ✗ required | Pen auth/authz once · capacity baseline | Pressure + survival + pen per `testing/PRESSURE.md §10` |
| Security scan | ✗ required | Dependency audit only | Full SCA + SAST + secret scan |
| Artifact management | Local only | Registry, basic versioning | Signed, immutable, retention policy |
| Environments | Local only | Dev + production | Dev + staging + production |
| Deploy strategy | Manual | Script-based, single target | Blue-green or canary, zero-downtime |
| Rollback | Manual redeploy | Script-based | Automated with health checks |
| Secrets | Env vars | CI secret variables | Secret manager + rotation |
| Monitoring post-deploy | Manual | Basic health check | Full observability + auto rollback |
| Release process | Git tag | Tag + changelog | Full semver + signed + notes |
| Cross-platform (§15) | Single OS | Two target OSes | All target OSes in matrix |
| Pipeline speed target | < 2 min | < 5 min | < 10 min |

### Transitions

- PoC → Small: CI config · linter · basic tests · single deploy target.
- Small → Production: security scanning · staging env · artifact signing · automated rollback · secret rotation · reality dimensions per `testing/STANDARDS.md §28`.
- Incremental, ✗ rewrite from scratch. Add stages as project matures.

---

## 17. CI/CD Checklist

### New Project Pipeline

- [ ] Pipeline definition in repo, version-controlled
- [ ] Confidence level declared (`testing/STANDARDS.md §1`); pipeline gates by it
- [ ] Lint stage: formatter + static analysis + determinism enforcement (§3)
- [ ] Build produces single versioned artifact
- [ ] Unit + integration suites run every push (§5)
- [ ] Cross-platform matrix configured for all target OS (§15)
- [ ] Pipeline failure blocks merge · ✗ override without documented reason
- [ ] Secrets in secret manager, ✗ repo
- [ ] Pipeline duration baselined and monitored

### Production Readiness

- [ ] Test stage gates by Confidence Level (§5)
- [ ] Reality dimensions wired: faults · adversarial · concurrency in unit/integration suites
- [ ] Nightly suites: scenario · long-run · fuzz · mutation · performance (`testing/STANDARDS.md §20`)
- [ ] Replay corpus runs in pre-prod (L5) (`testing/STANDARDS.md §16`)
- [ ] Cross-platform matrix green on every commit (§15)
- [ ] Pressure / survival / pen test runners provisioned (`PRESSURE.md §9`)
- [ ] Pressure suite gates per release (§5); chaos + pen-corpus nightly gates for L5
- [ ] Security scanning: SCA + SAST + secret scan
- [ ] Artifact signed, stored with retention policy
- [ ] Dev → Staging → Production progression with parity verified
- [ ] Zero-downtime deployment configured
- [ ] Automated rollback triggers defined and tested
- [ ] Health check gates on every deploy · monitoring + alerting active
- [ ] Rollback procedure tested monthly
- [ ] Secret rotation active · release process follows semver

### Per-Release

- [ ] Version bumped per semver · changelog generated · release notes written
- [ ] Tag triggers pipeline · all suites green per Confidence Level (§5)
- [ ] Cross-platform matrix green (§15)
- [ ] Artifact signed and published · staged deployment · post-deploy health green

### Pipeline Maintenance

- [ ] Pipeline duration reviewed monthly — no creep beyond targets
- [ ] Flaky tests quarantined and resolved within 7 days (`testing/STANDARDS.md §3`)
- [ ] Security scan exceptions reviewed and renewed
- [ ] Secret rotation audited quarterly
- [ ] Artifact retention cleanup daily
- [ ] Runner queue wait < 1 min · cross-platform matrix all OSes provisioned
