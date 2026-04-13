# CI/CD Pipeline Standards

Rules for continuous integration and continuous deployment pipelines.
Every commit potentially deployable. Every repeatable action automated.
Fast feedback, reproducible builds, immutable artifacts.

Composable with: Testing Standards, Git Standards, Security Standards,
Dependencies Standards, DevOps Standards.

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
15. [Scale Matrix](#15-scale-matrix)
16. [CI/CD Checklist](#16-cicd-checklist)

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
| Code formatting | Consistent style across codebase | Block merge |
| Static analysis | Catch bugs without execution | Block merge |
| Type checking | Type errors caught early | Block merge |
| Import ordering | Deterministic imports | Block merge |
| Dead code detection | Remove unused code | Warn (block in production) |
| Complexity metrics | Flag functions exceeding threshold | Warn |
| Commit message format | Enforce conventional commits | Block merge |

### Lint Rules

- Linter config lives in repo root, version-controlled.
- CI lint config identical to local developer config. ✗ divergent rules.
- Lint runs before build — cheapest check first.
- Auto-fixable issues fixed locally before push (pre-commit hook). CI verifies, ✗ auto-fixes.
- New lint rules applied incrementally — existing violations tracked, new violations blocked.
- Lint warnings promoted to errors in CI. ✗ warning-only mode in pipeline.

See `testing/STANDARDS.md` for test-specific linting rules.

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

Executes test pyramid in pipeline. Test strategy defined in `testing/STANDARDS.md` —
this section covers pipeline execution only.

### Test Execution Order

| Level | Runs When | Parallelizable | Failure Impact |
|---|---|---|---|
| Unit tests | Every push | Yes — per-module parallel | Blocks merge |
| Integration tests | PR merge to trunk | Limited — may share resources | Blocks deploy |
| Contract tests | PR merge to trunk | Yes | Blocks deploy |
| E2E / smoke tests | Post-deploy per environment | No — sequential | Triggers rollback |

### Test Stage Rules

- All tests run in isolated environments. ✗ shared state between test runs.
- Test database/state created fresh per run. ✗ depend on leftover data.
- Tests produce machine-readable output (JUnit XML, TAP, or equivalent).
- Test results published to CI dashboard — every run, not just failures.
- Flaky test detected → quarantine immediately. Flaky test ✗ blocks pipeline for others.
- Quarantined tests tracked in issue tracker. Max 7 days quarantine before fix or delete.
- Coverage threshold enforced. Threshold ratchets — never decreases.
- Test timeout per suite. Individual test timeout enforced. Hung test ✗ blocks pipeline indefinitely.

### Parallelization

- Unit tests split across runners by module/package.
- Each runner gets independent environment.
- Test ordering randomized to catch hidden dependencies.
- Results aggregated after all runners complete.

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

## 15. Scale Matrix

Apply pipeline rules proportionally to project scale.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Pipeline definition | Shell script or single CI file | Standard CI config | Multi-stage pipeline as code |
| Lint stage | Formatter only | Formatter + static analysis | Full lint suite + type checking |
| Build stage | Direct run (no build) | Single build command | Reproducible, cached, multi-target |
| Unit tests | Smoke tests only | Full unit suite | Full suite + coverage threshold |
| Integration tests | Manual | Basic integration | Full contract + integration suite |
| Security scan | ✗ required | Dependency audit only | Full SCA + SAST + secret scan |
| Artifact management | Local only | Registry with basic versioning | Signed, immutable, retention policy |
| Environments | Local only | Dev + production | Dev + staging + production |
| Deploy strategy | Manual | Script-based, single target | Blue-green or canary, zero-downtime |
| Rollback | Manual redeploy | Script-based rollback | Automated rollback with health checks |
| Secrets management | Environment variables | CI secret variables | Dedicated secret manager + rotation |
| Monitoring post-deploy | Manual check | Basic health check | Full observability + automated rollback |
| Release process | Git tag only | Tag + changelog | Full semver + signed artifacts + notes |
| Pipeline speed target | < 2 min | < 5 min | < 10 min |

### Scale Transitions

- PoC → Small: Add CI config, linter, basic tests, single deploy target.
- Small → Production: Add security scanning, staging environment, artifact signing, automated rollback, secret rotation.
- Transition incrementally. ✗ rewrite pipeline from scratch. Add stages as project matures.

---

## 16. CI/CD Checklist

### New Project Pipeline

- [ ] Pipeline definition in repo, version-controlled
- [ ] Lint stage configured (formatter + static analysis)
- [ ] Build stage produces single versioned artifact
- [ ] Unit test stage with coverage threshold
- [ ] Pipeline runs on every push
- [ ] Pipeline failure blocks merge
- [ ] Secrets stored in secret manager, ✗ in repo
- [ ] Pipeline duration baselined and monitored

### Production Readiness

- [ ] Integration test stage active
- [ ] Security scanning (SCA + SAST + secret scan) enabled
- [ ] Artifact signed and stored in registry with retention policy
- [ ] Dev → Staging → Production environment progression established
- [ ] Environment parity verified (staging mirrors production)
- [ ] Zero-downtime deployment strategy configured
- [ ] Automated rollback triggers defined and tested
- [ ] Health check gates on every deploy
- [ ] Monitoring + alerting post-deploy
- [ ] Rollback procedure documented and tested monthly
- [ ] Secret rotation schedule active
- [ ] Release process follows semver with changelog

### Per-Release

- [ ] Version bumped according to semver
- [ ] Changelog generated and reviewed
- [ ] Release notes written (migration steps if breaking)
- [ ] Tag created, pipeline triggered
- [ ] Artifact signed and published
- [ ] Staged deployment: dev → staging → production
- [ ] Post-deploy health checks green
- [ ] Monitoring baseline verified — no regression

### Pipeline Maintenance

- [ ] Pipeline duration reviewed monthly — no creep beyond targets
- [ ] Flaky tests quarantined and resolved within 7 days
- [ ] Security scan exceptions reviewed and renewed or resolved
- [ ] Secret rotation schedule audited quarterly
- [ ] Artifact retention cleanup running daily
- [ ] Pipeline infrastructure capacity meets demand (queue wait < 1 min)
