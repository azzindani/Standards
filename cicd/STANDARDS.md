# CI/CD Pipeline Standards

> Build, test, secure, and deliver every commit through an automated, reproducible, hermetic pipeline — fast feedback, immutable signed artifacts, progressive rollout.

**ID** `cicd` · **Tier** Delivery · **Version** 1.0
**Owns** pipeline stages + gating (lint/build/test/security/deploy) · **DORA four key metrics** · progressive delivery (canary/blue-green/feature-flag) · reproducible + hermetic builds · **supply chain (SLSA levels · SBOM · artifact signing/Sigstore-cosign · pinned action SHAs)** · **OIDC keyless auth** · artifact management + promotion · environment parity · pipeline speed budgets · rollback triggers · **release automation** · cross-platform matrix
**Defers to** test strategy + pyramid + coverage gate → [testing](../testing/STANDARDS.md) · SemVer + changelog + release tagging → [git](../git/STANDARDS.md) · secrets rotation cadence + lifecycle → [security](../security/STANDARDS.md) · alert thresholds + SLO design → [observability](../observability/STANDARDS.md) · deployment infra mechanics (containers/IaC/networking) → [devops](../devops/STANDARDS.md) · branching strategy → [git](../git/STANDARDS.md) · injection/vuln taxonomy → [security](../security/STANDARDS.md) · license policy → [dependencies](../dependencies/STANDARDS.md)
**Load with** [testing](../testing/STANDARDS.md) · [git](../git/STANDARDS.md) · [security](../security/STANDARDS.md) · [devops](../devops/STANDARDS.md)

---

## Table of Contents

1. [Pipeline Philosophy](#1-pipeline-philosophy)
2. [Delivery Performance (DORA)](#2-delivery-performance-dora)
3. [Pipeline Stages](#3-pipeline-stages)
4. [Lint Stage](#4-lint-stage)
5. [Build Stage](#5-build-stage)
6. [Test Stage](#6-test-stage)
7. [Security Stage](#7-security-stage)
8. [Artifacts & Supply Chain](#8-artifacts--supply-chain)
9. [Progressive Delivery](#9-progressive-delivery)
10. [Environment Parity](#10-environment-parity)
11. [Pipeline Speed](#11-pipeline-speed)
12. [Secrets in Pipeline](#12-secrets-in-pipeline)
13. [Branch Pipeline Rules](#13-branch-pipeline-rules)
14. [Rollback Strategy](#14-rollback-strategy)
15. [Release Automation](#15-release-automation)
16. [Cross-Platform Matrix](#16-cross-platform-matrix)
17. [Scale Matrix](#17-scale-matrix)
18. [Checklist](#18-checklist)

---

## 1. Pipeline Philosophy

| Principle | Rule |
|---|---|
| Every commit deployable | Trunk never breaks. Broken commit → immediate fix or revert |
| Automate everything repeatable | Manual steps = future incidents. Done twice → script it |
| Fast feedback | Developer learns of failure in minutes, not hours |
| Build once, deploy many | One artifact flows through all environments. ✗ rebuild per environment |
| Pipeline is code | Definition lives in repo, version-controlled, reviewed like application code |
| Fail fast, fail loud | First failure stops the pipeline. ✗ continue past a broken stage |
| Hermetic + reproducible | Same commit + config = identical output; build isolated from network/host state |
| Immutable artifacts | Published artifact never modified. New version → new artifact |
| Least privilege | Each stage gets minimum permissions. ✗ admin credentials everywhere |
| Auditability | Every deployment traceable to commit, build, approver, timestamp |

### Non-Negotiables

- Pipeline runs on every push. ✗ manual-only CI. Definition changes go through code review.
- Pipeline failure blocks merge. ✗ override without documented reason.
- Output deterministic — flaky tests fixed or quarantined immediately.

---

## 2. Delivery Performance (DORA)

Pipeline health measured by DORA's key metrics. The **four key metrics** are the stable core — track all four continuously; degrading a metric class is a regression.

| Key metric | Measures |
|---|---|
| Deployment frequency | Throughput |
| Lead time for changes | Throughput |
| Change failure rate | Stability |
| Failed-deployment recovery time | Stability |

- **Fifth metric (added 2024): Deployment Rework Rate** — share of deployments needing unplanned remediation (hotfix · rollback · patch-forward). Rising rework = eroding stability even when the other four look healthy.
- Optimize throughput + stability together — ✗ trade stability for speed. Enablers: trunk-based development · small batch size · full test automation · progressive delivery · fast rollback.

**Benchmark reference.** The Elite/High/Medium/Low four-cluster model was **retired in the 2025 DORA report** (replaced by percentile bands + team archetypes) — use it only as a dated reference, ✗ as the current framework. *2024 cluster benchmarks (superseded by 2025 percentile bands):* Elite ≈ on-demand deploy · lead time < 1 day · change failure rate ~5% · restore < 1 hour. Low ≈ < monthly deploy · lead time > 1 month · restore > 1 week.

---

## 3. Pipeline Stages

Ordered sequence, each stage gates the next. Failure at any stage halts progression: **lint → build → unit test → integration test → security scan → deploy(dev) → deploy(staging) → deploy(production)**.

| Stage | Gate | Runs On | Max Duration |
|---|---|---|---|
| Lint | All checks pass, zero warnings in CI | Every push | 2 min |
| Build | Compiles/packages without error | Every push | 3 min |
| Unit Test | 100% pass, coverage threshold met | Every push | 3 min |
| Integration Test | All contract + integration tests pass | PR merge to trunk | 5 min |
| Security Scan | Zero critical/high vulnerabilities | PR merge to trunk | 3 min |
| Deploy (dev) | All prior stages green | Trunk merge | 2 min |
| Deploy (staging) | Dev deployment healthy for N minutes | After dev soak | 2 min |
| Deploy (production) | Staging smoke tests pass + approval | Manual or auto | 5 min |

- Stages run sequentially by default; parallel only where no data dependency exists.
- Lint + Build + Unit Test may run in parallel if independent. Integration Test + Security Scan run after Build (need the artifact).
- Deploy stages strictly sequential: dev → staging → production.

---

## 4. Lint Stage

Enforces consistency before any build or test resources consumed — cheapest check first.

| Check | Failure Action |
|---|---|
| Code formatting · import ordering | Block merge |
| Static analysis · type checking | Block merge |
| Determinism violations (✗ wall-clock · random · UUID without injection, [testing](../testing/STANDARDS.md) §14) | Block merge |
| Commit message format (Conventional Commits, [git](../git/STANDARDS.md)) | Block merge |
| Dead code detection | Warn (block in production) |
| Complexity metrics | Warn |

- Linter config in repo root, version-controlled. CI config identical to local. ✗ divergent rules.
- Auto-fixable issues fixed locally (pre-commit hook). CI verifies, ✗ auto-fixes.
- Warnings promoted to errors in CI. ✗ warning-only mode.
- New rules applied incrementally — existing violations tracked, new violations blocked.

See [testing](../testing/STANDARDS.md) §14 for determinism rules · §20 for test-specific lint.

---

## 5. Build Stage

Produces the deployable artifact. Deterministic, reproducible, hermetic, environment-agnostic.

| Rule | Detail |
|---|---|
| Reproducible | Same commit → byte-identical output where toolchain supports |
| Hermetic | Build isolated from network + host state; all inputs declared + pinned. ✗ fetch-during-build |
| Deterministic dependencies | Lock files pinned. ✗ floating versions in CI ([dependencies](../dependencies/STANDARDS.md)) |
| Build once | Single artifact across dev/staging/production. ✗ rebuild per env |
| No config baked in | Configuration injected at deploy time, not build time |
| Metadata embedded | Commit SHA, build timestamp, version tag embedded in artifact |
| Clean environment | Build from clean state. Cache = speed optimization, ✗ correctness requirement |
| Warnings = errors | `-Werror` or equivalent. ✗ ship with warnings |

Build output = single versioned artifact (binary, container image, package, archive), tagged with version + commit SHA + build number. Build log captured and stored alongside. Failure output includes full error context — ✗ truncated logs.

---

## 6. Test Stage

Executes the test pyramid + reality dimensions per [testing](../testing/STANDARDS.md); system-level pressure/survival/penetration per [testing/PRESSURE.md](../testing/PRESSURE.md). This section covers pipeline execution only — **strategy lives in the testing standards**.

### Suite → Pipeline Position

| Suite | Pipeline Position | Parallel | Failure |
|---|---|---|---|
| Unit | Every push | Yes — per-module | Blocks merge |
| Integration | Every push | Limited — shared resources | Blocks merge |
| E2E | Pre-merge | No — sequential | Blocks merge |
| Scenario | Nightly · pre-prod | Limited | Blocks promotion |
| Long-run | Nightly | Yes — per-target | Notify, ✗ block merge |
| Fuzz | Nightly | Yes — per-target | Crash = P1, blocks merge |
| Mutation | Weekly | Per-module | L5 gates release |
| Replay | Pre-prod deploy | No — sequential | Blocks promotion |
| Performance | Nightly | Yes | Regression > 20% blocks |
| Pressure ([PRESSURE.md](../testing/PRESSURE.md) §3) | Nightly + per release | No — dedicated runner | Regression > 20% blocks release |
| Survival ([PRESSURE.md](../testing/PRESSURE.md) §4) | Nightly · weekly full matrix | No — pre-prod env | Single-fault blocks; multi-fault if user-facing |
| Penetration ([PRESSURE.md](../testing/PRESSURE.md) §5) | Nightly + per release | Yes — staging | Critical/High blocks release |

### Confidence Level → Required Suites

Per [testing](../testing/STANDARDS.md) §1. CI gates by declared level.

| Level | Gating Merge | Gating Deploy |
|---|---|---|
| L1 | Unit (happy path) | Unit |
| L2 | Unit + Contract + Property | Unit + Integration |
| L3 | + Faults · Adversarial · Concurrency | + E2E + Pen (auth/authz/session) |
| L4 | + Resources · Time · Observability · Recovery | + Scenario + Long-run + Pressure (stress/endurance/capacity) + Survival single-fault green |
| L5 | + all of L4 | + Mutation · Replay · Chaos nightly · Pen full corpus · annual red-team current |

### Rules

- All tests in isolated environments. ✗ shared state between runs. Test DB/state fresh per run.
- Machine-readable output (JUnit XML, TAP). Results published every run.
- Flaky test → quarantine immediately. Max 7 days before fix or delete ([testing](../testing/STANDARDS.md) §3).
- Coverage threshold ratchets — ✗ decreases ([testing](../testing/STANDARDS.md) §22). Per-suite + per-test timeout enforced.
- Race detector enabled when toolchain supports. Resource tests use explicit cgroup/ulimit, ✗ host defaults.
- Test order randomized to catch hidden dependencies. Replay corpus runs pre-prod, ✗ against production.

---

## 7. Security Stage

Shift security left — catch vulnerabilities before deploy. Vuln + injection taxonomy → [security](../security/STANDARDS.md); this covers pipeline integration.

| Check | Stage Position | Blocks Deploy |
|---|---|---|
| Dependency audit (SCA) | After build | Yes — critical/high |
| Secret scanning | Pre-commit + CI | Yes — any finding |
| SAST (static analysis) | After lint | Yes — critical/high |
| Container scanning | After container build | Yes — critical/high |
| License compliance | After dependency resolution | Yes — policy violation ([dependencies](../dependencies/STANDARDS.md)) |
| DAST (dynamic testing) | Post-deploy to staging | Yes — critical |

- Dependency audit runs against lock file, ✗ floating versions.
- Vulnerability exceptions documented: CVE, justification, expiry date, owner. Exception expires → pipeline blocks until renewed or fixed.
- Secret detected in history → rotate immediately. ✗ just remove from current commit.
- SAST false-positive rate > 20% → retune before next release. Results stored per build (audit trail).

### Severity → Action

| Severity | Action | Timeline |
|---|---|---|
| Critical | Block deploy. Fix immediately | Same day |
| High | Block deploy. Fix before next release | Within sprint |
| Medium | Track in backlog. ✗ block deploy | Next 2 sprints |
| Low | Track. Fix opportunistically | Best effort |

---

## 8. Artifacts & Supply Chain

Artifacts = build outputs stored for deployment: versioned, immutable, traceable, signed, provenance-attested.

### Artifact Rules

| Rule | Detail |
|---|---|
| Immutable | Published artifact never modified. Fix → new version |
| Versioned | Unique SemVer per artifact ([git](../git/STANDARDS.md) owns SemVer) |
| Promotion not rebuild | Artifact promoted between environments. ✗ rebuild per env |
| Retention | Dev: 7 days · Staging: 30 days · Production: ≥ 1 year |
| Single registry | One registry per artifact type. ✗ duplicate registries |
| Metadata | Version, commit SHA, build ID, timestamp, builder |

Naming: container `<service>:<semver>-<sha7>` · binary `<name>-<semver>-<os>-<arch>` · package `<name>@<semver>`. Automated cleanup of untagged/expired artifacts daily; artifacts referenced by any deployment ✗ eligible. Alert on storage > 80%.

### Supply Chain Hardening

| Control | Rule |
|---|---|
| SLSA provenance | Target SLSA Build L3: non-falsifiable provenance generated by the build platform, attached to every artifact |
| SBOM | Generate SBOM (SPDX or CycloneDX) per build; store with the artifact; scan it for known CVEs |
| Artifact signing | Sign all release artifacts (Sigstore/cosign, keyless). Verify signature + provenance before deploy. ✗ deploy unsigned |
| Pinned dependencies | Third-party CI actions/steps pinned to full commit SHA, ✗ mutable tags (`@v3`, `@main`) |
| Trusted builders | Builds run on trusted, ephemeral runners only. ✗ untrusted PR code with secret access |
| Verification gate | Deploy stage verifies signature + provenance + SBOM policy. Failure blocks promotion |

OIDC keyless auth for signing + registry/cloud push (§12) — ✗ long-lived signing keys or cloud credentials in the pipeline.

---

## 9. Progressive Delivery

Production changes roll out gradually with automated verification at each step. Deployment infra mechanics (how blue-green/canary are wired) → [devops](../devops/STANDARDS.md) §3.

### Environment Progression

**dev → staging → production**, each validating before promotion.

| Environment | Deploy Trigger | Rollback |
|---|---|---|
| Dev | Automatic on trunk merge | Automatic |
| Staging | Automatic after dev soak | Automatic |
| Production | Manual approval or auto after staging soak | Automatic + manual option |

### Rollout Strategies

| Strategy | When | Rollback Speed |
|---|---|---|
| Blue-green | Stateless services, fast switchover | Instant (switch back) |
| Canary | High-traffic, gradual validation | Fast (route to old) |
| Feature flag | Decouple deploy from release; segment rollout | Instant (flag toggle) |
| Rolling | Stateful services, resource-constrained | Medium |

### Rules

- Artifact promoted, not rebuilt; all prior environment checks green. Production requires staging smoke tests + health check + approval (if manual).
- Zero-downtime: production deploys ✗ cause interruption. New version passes health check before receiving traffic.
- Canary traffic shift: 5% → 25% → 50% → 100% with monitoring at each step. Soak: dev 5 min · staging 15 min · production canary 15 min per step.
- One deployment at a time per service (deploy lock). ✗ concurrent deploys. Previous known-good artifact retained for instant rollback.
- Deploy during business hours (team available for rollback). Every deploy logged: who, version, when, from which build.

---

## 10. Environment Parity

Staging mirrors production. Differences = deployment risk. Config cascade → [configuration](../configuration/STANDARDS.md).

| Dimension | Requirement |
|---|---|
| Infrastructure | Same OS, runtime versions, resource shape (scaled down ok, different stack ✗) |
| Configuration | Same config keys; values differ by environment (injected at deploy) |
| Data shape | Staging uses production schema; synthetic data matching production patterns |
| Dependencies | Same service versions. ✗ staging on v2 while production on v1 |
| Networking | Same topology — load balancer, DNS, TLS present in staging |
| Feature flags | Staging matches production flag state unless explicitly testing a new flag |

✗ different OS/kernel between staging + production · ✗ missing infra component (queue, cache, CDN) · ✗ in-memory DB replacing real DB · ✗ manual config changes in any environment · ✗ "works on my machine" as authoritative. Configuration drift detection — automated comparison between environments, alert on drift.

---

## 11. Pipeline Speed

Slow pipeline = batched changes = larger failures = slower recovery. Target: commit-to-deploy-dev < 10 min.

| Metric | Target | Hard Limit |
|---|---|---|
| Lint + Build + Unit Test | < 5 min | 10 min |
| Full pipeline (to dev deploy) | < 10 min | 20 min |
| Production deploy (after approval) | < 5 min | 15 min |
| Rollback execution | < 2 min | 5 min |
| Feedback to developer (first failure) | < 3 min | 5 min |

Optimizations (high priority): dependency caching · build caching · test parallelization · step parallelization. Medium: incremental builds · Docker layer caching · selective test execution · pre-built base images.

- Pipeline duration tracked as a metric. Alert on regression > 20%. New step requires impact assessment.
- Long-running tests (> 30s each) moved to post-merge pipeline, not PR pipeline.
- Cache invalidation explicit — stale cache ✗ mask build failures. Queue wait time < 1 min.

---

## 12. Secrets in Pipeline

Pipeline secret **scoping + injection** only. Rotation cadence, lifetimes, and token classes → [security](../security/STANDARDS.md) — ✗ restate schedules here.

| Rule | Detail |
|---|---|
| OIDC keyless first | Authenticate to cloud/registry/signing via short-lived OIDC tokens. ✗ long-lived static cloud keys in CI |
| ✗ hardcoded secrets | Zero secrets in source, config, or pipeline definitions |
| ✗ secrets in logs | Pipeline masks secret values in all output |
| ✗ secrets in artifacts | Build output ✗ contains embedded credentials |
| Secret manager | All secrets stored in a dedicated secret management service |
| Least privilege | Each stage gets only the secrets it needs. ✗ global secret access |
| Audit trail | Every secret access logged: who, when, which secret |

Lifecycle: create → store (encrypted) → inject (runtime) → use → rotate → revoke. Leak response: revoke immediately → rotate all secrets sharing scope → audit access logs → scan + purge from history → post-incident review within 48 h. Rotation frequencies + token lifetimes → [security](../security/STANDARDS.md).

---

## 13. Branch Pipeline Rules

Different branches trigger different pipeline subsets. Branching strategy → [git](../git/STANDARDS.md).

| Branch Type | Stages Executed | Deploy Target |
|---|---|---|
| Feature branch (PR) | Lint → Build → Unit Test | None |
| PR merge to trunk | Lint → Build → Unit + Integration → Security Scan | Dev (auto) |
| Trunk (main) | Full pipeline | Dev → Staging (auto) |
| Release tag | Full pipeline + signing + release artifact | Production |
| Hotfix branch | Lint → Build → Unit + Integration | Staging (fast-track) |

- Feature branch pipeline runs on every push. PR pipeline runs full test suite — ✗ merge with failing tests.
- Trunk merge auto-deploys to dev. Release tag triggers production pipeline (approval gate if configured).
- Hotfix branches bypass feature-branch restrictions but ✗ skip any test stage.

PR gate (branch protection): all lint + unit tests pass · coverage threshold met · no critical security findings · build succeeds · PR approved ([code_review](../code_review/STANDARDS.md)) · branch up to date with trunk.

---

## 14. Rollback Strategy

Every deployment has a tested rollback plan. Rollback tested as regularly as deployment.

| Trigger | Threshold | Action |
|---|---|---|
| Health check failure | 3 consecutive post-deploy | Automatic rollback |
| Error rate spike | > 5% above baseline | Automatic rollback |
| Latency spike | p99 > 2x baseline for 2 min | Automatic rollback |
| Canary failure | Metrics worse than baseline | Stop rollout, rollback canary |
| Deployment timeout | Deploy ✗ complete within max duration | Automatic rollback |

- Previous known-good artifact always available. Rollback = deploy previous version. ✗ rollback by reverting code and rebuilding.
- Rollback procedure tested monthly. ✗ approval gate — speed is critical; audit after. Rollback event → incident review within 24 h.
- DB migrations forward-only by default. Backward-incompatible schema → two-phase deploy: expand (add new) → migrate → contract (remove old).

Procedure: detect → trigger (automated or single command) → route to previous version → verify healthy → notify team (what failed, version rolled back to, timeline) → root cause within 24 h.

---

## 15. Release Automation

Release automation only. **SemVer rules, changelog format, and release tagging → [git](../git/STANDARDS.md)** — ✗ restate them here.

| Rule | Detail |
|---|---|
| Tag triggers release | Git tag (`v1.2.3`, [git](../git/STANDARDS.md)) triggers the release pipeline. ✗ manual release steps |
| Version single-sourced | Read version from the one source of truth ([git](../git/STANDARDS.md)); ✗ hand-edit at release |
| Changelog auto-drafted | Auto-draft from Conventional Commits into the changelog format [git](../git/STANDARDS.md) owns; human curates for major releases |
| Release notes | Every release has human-readable notes: what changed, migration steps |
| Artifact signed | Release artifacts signed + provenance-attested (§8) |
| Release immutable | Published release ✗ modified. Error → publish a new patch release |
| Rollback version available | Previous release always downloadable/deployable |

Workflow: **version bump → changelog update → tag → pipeline → artifact publish (signed) → deploy**. Version bump + changelog content follow [git](../git/STANDARDS.md); this pipeline only executes and gates them.

---

## 16. Cross-Platform Matrix

CI runners support Windows · macOS · Linux as first-class environments. Tests + build run on all target OS per [testing](../testing/STANDARDS.md) §26. Matrix runs in parallel; all OSes must pass to merge.

| OS | Runner | Coverage | Required For |
|---|---|---|---|
| Linux | x86_64 · arm64 | Full unit + integration + container | All projects |
| Windows | Server LTSC | Full unit + integration; PowerShell scripts | Cross-platform targets |
| macOS | x86_64 · arm64 | Full unit + integration; native APIs | macOS-target or polyglot |

### Rules

- All target platforms run in parallel. Total wall time = slowest runner, ✗ sum.
- Container-based tests run on Linux only — explicitly documented, ✗ skipped silently.
- Platform-specific code paths require platform-specific tests, OS-gated. Path handling via stdlib abstractions only; lint enforces.
- Line endings: source `\n` (enforced by `.gitattributes`); tests assert both `\n` and `\r\n`. Source files UTF-8 BOM-less.
- Any OS fail = merge blocked. ✗ "Linux green is enough." OS-specific flake → quarantine the OS-specific test, ✗ disable the OS from the matrix.
- Platform-specific bug = P1, fixed before next release. Removing an OS from the matrix = same review weight as removing test coverage.

### Runner Types

| Type | Use For | Limits |
|---|---|---|
| Hosted | Default; all public + most private projects | Time-quota'd, ephemeral |
| Self-hosted | Specialty hardware (GPU, ARM), restricted networks, large caches | Patching + security ownership stays with project; isolated per job, ✗ shared state |
| Dedicated pressure runner | Stress/endurance/capacity ([PRESSURE.md](../testing/PRESSURE.md) §9) | Production-shaped; one test at a time per env |
| Pre-prod survival env | Survival/chaos/multi-fault | Multi-zone · fault-injection layer · isolated network |
| Staging pen-test env | Penetration corpus | Mirrors prod auth/authz/TLS · synthetic data · isolated from prod |

---

## 17. Scale Matrix

Cross-references [testing](../testing/STANDARDS.md) §28 — confidence level there gates the pipeline gates here.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Pipeline definition | Shell script or single CI file | Standard CI config | Multi-stage pipeline as code |
| Lint stage | Formatter only | Formatter + static analysis | Full lint + type check + determinism |
| Build stage | Direct run | Single build command | Reproducible, hermetic, cached, multi-target |
| Test stage | Unit smoke | Unit + basic integration | Full suites per Confidence Level (§6) |
| Security scan | ✗ required | Dependency audit only | Full SCA + SAST + secret scan |
| Supply chain (§8) | ✗ required | SBOM generated | SLSA L3 provenance · signed artifacts · pinned SHAs |
| Artifact management | Local only | Registry, basic versioning | Signed, immutable, retention policy |
| Environments | Local only | Dev + production | Dev + staging + production |
| Deploy strategy | Manual | Script-based, single target | Blue-green or canary, zero-downtime |
| Rollback | Manual redeploy | Script-based | Automated with health checks |
| Secrets | Env vars | CI secret variables | OIDC keyless + secret manager |
| DORA tracking (§2) | ✗ | Deployment frequency + lead time | All four key metrics + rework rate |
| Cross-platform (§16) | Single OS | Two target OSes | All target OSes in matrix |
| Pipeline speed target | < 2 min | < 5 min | < 10 min |

Transition PoC → Small: CI config · linter · basic tests · single deploy target. Small → Production: security scanning · staging env · SBOM + signing · automated rollback · OIDC. Incremental, ✗ rewrite from scratch.

---

## 18. Checklist

### New Project Pipeline

- [ ] Pipeline definition in repo, version-controlled
- [ ] Confidence level declared ([testing](../testing/STANDARDS.md) §1); pipeline gates by it
- [ ] Lint stage: formatter + static analysis + determinism enforcement (§4)
- [ ] Build reproducible + hermetic; produces single versioned artifact (§5)
- [ ] Unit + integration suites run every push (§6)
- [ ] Cross-platform matrix configured for all target OS (§16)
- [ ] Pipeline failure blocks merge · ✗ override without documented reason
- [ ] Secrets via OIDC keyless / secret manager, ✗ repo (§12)
- [ ] Pipeline duration baselined and monitored (§11)

### Production Readiness

- [ ] Test stage gates by Confidence Level (§6)
- [ ] Nightly suites wired: scenario · long-run · fuzz · mutation · performance ([testing](../testing/STANDARDS.md) §20)
- [ ] Pressure / survival / pen runners provisioned ([PRESSURE.md](../testing/PRESSURE.md) §9)
- [ ] Security scanning: SCA + SAST + secret scan (§7)
- [ ] Supply chain: SBOM generated · artifacts signed (cosign) · provenance attested · action SHAs pinned (§8)
- [ ] Artifact immutable, stored with retention policy (§8)
- [ ] Dev → Staging → Production progression with parity verified (§9, §10)
- [ ] Zero-downtime deployment configured; automated rollback triggers tested (§9, §14)
- [ ] DORA four key metrics + deployment rework rate tracked (§2)
- [ ] Rollback procedure tested monthly (§14)

### Per-Release

- [ ] Tag triggers pipeline; version + changelog per [git](../git/STANDARDS.md) (§15)
- [ ] All suites green per Confidence Level (§6); cross-platform matrix green (§16)
- [ ] Artifact signed + provenance-attested + published; post-deploy health green (§8, §9)

### Pipeline Maintenance

- [ ] Pipeline duration reviewed monthly — no creep beyond targets (§11)
- [ ] Flaky tests quarantined and resolved within 7 days ([testing](../testing/STANDARDS.md) §3)
- [ ] Security scan exceptions reviewed and renewed (§7)
- [ ] Artifact retention cleanup daily; runner queue wait < 1 min (§8, §11)
