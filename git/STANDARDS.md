# Git & Version Control Standards

> Branching, commits, merges, tags, semantic versioning, changelog format, and history hygiene for every project regardless of stack.

**ID** `git` · **Tier** Delivery · **Version** 1.0
**Owns** branching strategy · Conventional Commits format · atomic commits · merge strategy (squash/rebase/merge) · **semantic versioning (SemVer 2.0.0)** · **changelog format (Keep a Changelog 1.1.0)** · **release tagging** · signed commits · linear history + rebase policy · protected branches · history hygiene · `.gitignore` · git hooks · large files/LFS · monorepo git conventions · secret-in-VCS remediation
**Defers to** PR size + reviewer counts + review criteria → [code_review](../code_review/STANDARDS.md) · secrets management architecture + rotation → [security](../security/STANDARDS.md) · release automation + artifact signing + pipeline → [cicd](../cicd/STANDARDS.md) · branching ↔ lifecycle phase → [workflow](../workflow/STANDARDS.md) · changelog rendering/publishing → [documentation](../documentation/STANDARDS.md)
**Load with** [cicd](../cicd/STANDARDS.md) · [code_review](../code_review/STANDARDS.md) · [workflow](../workflow/STANDARDS.md)

---

## Table of Contents

1. [Branching Strategy](#1-branching-strategy)
2. [Commit Conventions](#2-commit-conventions)
3. [Commit Message Format](#3-commit-message-format)
4. [Merge Strategy](#4-merge-strategy)
5. [Versioning, Tagging & Changelog](#5-versioning-tagging--changelog)
6. [Pull Requests](#6-pull-requests)
7. [History Hygiene](#7-history-hygiene)
8. [.gitignore Rules](#8-gitignore-rules)
9. [Hooks](#9-hooks)
10. [Large Files](#10-large-files)
11. [Monorepo Git Practices](#11-monorepo-git-practices)
12. [Sensitive Data](#12-sensitive-data)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Branching Strategy

Trunk-based development by default. `main` always deployable, always green.

| Scale | Model | Characteristics |
|---|---|---|
| PoC / solo | Trunk-based | Commit direct to `main`, optional short-lived branches |
| Small team (2–5) | Trunk + short-lived branches | Feature branches merge < 2 days |
| Production / team (5+) | Trunk + release branches | `main` deployable, `release/*` for stabilization |

- ✗ Long-lived feature branches (> 3 days). Exceeds 3 days → rebase + split.
- ✗ Gitflow for new projects — overhead without proportional benefit.
- Short-lived branches integrate to trunk frequently → reduces merge conflict + review size.

### Branch Naming

| Pattern | Use |
|---|---|
| `main` | Primary integration branch. Always deployable |
| `feat/<ticket>-<slug>` | New feature work |
| `fix/<ticket>-<slug>` | Bug fix |
| `refactor/<slug>` | Restructuring, no behavior change |
| `docs/<slug>` · `test/<slug>` · `chore/<slug>` | Docs · tests · tooling/deps/config |
| `release/<version>` | Release stabilization (production scale) |
| `hotfix/<ticket>-<slug>` | Emergency production fix |

- Lowercase, hyphen-delimited. ✗ underscores · ✗ uppercase · ✗ spaces.
- `<ticket>` = issue ID when tracking system exists. `<slug>` = 2–4 words. Max 50 chars total.
- Delete branch after merge. Zero stale branches.

### Branch Lifecycle & Protection

- Lifecycle: **create → push → PR → review → merge → delete**.
- Branch from `main` (or `release/*` for hotfixes). Rebase from `main` ≥ daily for branches lasting > 1 day.
- Merge back via PR. ✗ direct push to `main` ; exception: solo PoC scale.
- Protected branches (`main`, `release/*`): required status checks · required reviews · linear history · ✗ force-push · ✗ deletion. Enforced server-side (§9).

---

## 2. Commit Conventions

### Atomic Commits

One commit = one logical change: single feature/sub-feature · single bug fix · single refactor · single dependency update · single config change.

- ✗ Mix refactoring with feature work in one commit.
- ✗ Mix formatting changes with logic changes.
- ✗ Commit half-working state — every commit builds + passes tests.

### Commit Granularity

| Too small | Right size | Too large |
|---|---|---|
| Fix typo in one variable | Add input validation to user registration | Implement entire auth system |
| Add single import | Refactor DB layer to connection pooling | Rewrite frontend + backend + tests |
| Whitespace change | Extract payment processing into module | Week of work in one commit |

Rule of thumb: reviewer understands the full diff in < 5 minutes → right size.

### What Gets Committed

- Source, configuration, infrastructure-as-code, documentation, tests.
- ✗ Build artifacts · ✗ generated files · ✗ secrets · ✗ local environment files.
- ✗ Files > 5 MB (§10).
- Lock files (`package-lock.json`, `Cargo.lock`, …) → commit when they change.

---

## 3. Commit Message Format

Conventional Commits. Structure: `<type>(<scope>): <subject>` · blank line · `<body>` · blank line · `<footer>`.

### Type Prefixes

Spec mandates only `feat` + `fix`; the rest are the widely-adopted commitlint convention — adopt this set repo-wide.

| Type | Meaning |
|---|---|
| `feat` | New feature or capability (→ MINOR bump) — **spec** |
| `fix` | Bug fix (→ PATCH bump) — **spec** |
| `refactor` | Restructuring, no behavior change |
| `docs` · `test` · `chore` | Docs only · tests only · build/tooling/deps |
| `perf` | Performance improvement, no behavior change |
| `style` · `ci` · `revert` | Formatting · CI/CD changes · reverts a prior commit |

### Subject Rules

| Rule | Constraint |
|---|---|
| Max length | 72 characters |
| Capitalization | Lowercase after type prefix |
| Tense | Imperative mood (`add`, ✗ `added`/`adds`) |
| Punctuation | ✗ trailing period |
| Content | What changed, not how |

### Body & Footer

- Body separated from subject by blank line, wrapped at 72 chars. Explain *what* + *why*, not *how*.
- Breaking change: `!` after type/scope (`feat(api)!: …`) **or** footer `BREAKING CHANGE: <description>` → MAJOR bump.
- Issue refs: `Fixes #<id>` | `Closes #<id>` | `Refs #<id>`. Co-authors: `Co-authored-by: Name <email>`.
- `commit-msg` hook validates format (§9). ✗ non-conforming messages on `main`.

---

## 4. Merge Strategy

| Strategy | When | Result |
|---|---|---|
| **Squash merge** | Feature/fix branches → `main` (default) | Single clean commit on `main`, detail in PR |
| **Merge commit** | `release/*` → `main` · `hotfix/*` → `main` + `release/*` | Preserves branch history, clear merge point |
| **Rebase + fast-forward** | Small branches keeping linear history | Linear history, no merge commit |

- Default: squash merge for feature/fix. PR title → commit subject; PR description → commit body.
- Update feature branch by rebasing onto `main`. ✗ merge `main` into feature (noise merge commits).
- ✗ Rebase commits already pushed to a shared branch others pulled.
- ✗ Rebase `main` or `release/*`.

---

## 5. Versioning, Tagging & Changelog

Single source of truth for SemVer, release tags, and changelog format across the repo. `cicd` release automation, `documentation` changelog rendering, and `cli` compatibility promises all defer here.

### Semantic Versioning (SemVer 2.0.0)

Format `MAJOR.MINOR.PATCH`, tag `v<MAJOR>.<MINOR>.<PATCH>`.

| Component | Increment when |
|---|---|
| MAJOR | Breaking change to public API/contract/behavior |
| MINOR | New feature, backward compatible |
| PATCH | Bug fix, backward compatible |

- Pre-1.0.0: API unstable; MINOR may break. 1.0.0 = first stable public contract.
- Pre-release suffixes: `-alpha.N` (early preview) · `-beta.N` (feature-complete, untested) · `-rc.N` (release candidate). Precedence `alpha < beta < rc < release`.
- Build metadata: `+<meta>` (ignored in precedence).
- Version lives in exactly one place (package/version file or tag). ✗ version strings scattered across sources.

### Tag Rules

| Pattern | Purpose |
|---|---|
| `v1.2.3` | Stable release |
| `v1.2.3-rc.1` · `-beta.1` · `-alpha.1` | Pre-release for validation |

- Tags on `main` only (or `release/*` for pre-release). Tag after merge, ✗ before.
- Annotated tags only (`git tag -a`). ✗ lightweight tags for releases. Tag message = changelog summary.
- ✗ Move or delete published tags → create new patch version instead.
- Tag triggers release pipeline (release automation → [cicd](../cicd/STANDARDS.md)).
- Monorepo: scope tags to package — `auth/v1.2.3`, `api/v2.0.0` (§11).

### Changelog Format (Keep a Changelog 1.1.0)

`CHANGELOG.md` at repo root, reverse-chronological. Top `## [Unreleased]` section accumulates changes; released on version bump with date `## [1.2.3] - YYYY-MM-DD`.

| Category | Contains |
|---|---|
| Added | New features |
| Changed | Changes to existing functionality |
| Deprecated | Soon-to-be-removed features |
| Removed | Removed features |
| Fixed | Bug fixes |
| Security | Vulnerability fixes |

- Entry = one line per change, human-readable, issue/PR reference. Breaking changes flagged explicitly.
- Written for humans, ✗ raw commit dump. Auto-draft from Conventional Commits, then curate.
- Keep an `[Unreleased]` heading always present. Link versions to compare/diff URLs at file bottom.

---

## 6. Pull Requests

Size limits + reviewer counts + review criteria → [code_review](../code_review/STANDARDS.md). This section covers VCS-side PR mechanics only.

### PR Description Requirements

Every PR contains: **Summary** (1–3 bullets: what + why) · **Test plan** (how verified) · **Issue reference** (when applicable) · **Breaking changes** (explicit callout) · **Screenshots/output** (UI or output-format changes).

### PR Lifecycle

- **draft → ready → CI green → review → approved → merge → branch deleted**.
- Draft PRs for work-in-progress. ✗ open non-draft PR until ready for review.
- CI passes before review begins. All review comments resolved before merge.
- Stale PRs (no activity > 7 days) → close or rebase and update.
- Author merges after approval. ✗ reviewer merges unless team convention states otherwise.

---

## 7. History Hygiene

### Clean, Linear History on `main`

- `main` reads as a linear sequence of logical changes. Squash merge (§4) produces this by default.
- Each commit on `main` builds, passes tests, is independently deployable.
- Feature branch behind `main` → rebase onto `main` before PR. ✗ merge `main` into feature.

### Interactive Rebase (Local Only)

Permitted on **unpushed** or **force-push-safe** branches only: squash fixups · reword unclear messages · reorder for logical flow · drop accidental commits.

- ✗ Interactive rebase on `main`, `release/*`, or any shared branch.
- ✗ Force-push to branches others checked out without coordination.
- Fixup workflow: `git commit --fixup=<sha>` → autosquash before merge. ✗ "fix typo"/"fix lint" commits surviving into `main`.

### Signed Commits

- Production scale: signed commits required for releases (GPG, SSH, or `gitsign`/Sigstore keyless).
- Verified-signature status enforced on protected branches. Release tags signed (`git tag -s`).
- Signing keys tied to identity provider; ✗ shared signing keys across developers.

---

## 8. .gitignore Rules

### Mandatory Ignores (Every Project)

| Category | Examples |
|---|---|
| Build output | `build/`, `dist/`, `target/`, `out/`, `bin/` |
| Dependencies | `node_modules/`, `vendor/`, `.venv/`, `__pycache__/` |
| Environment files | `.env`, `.env.local`, `.env.*.local` |
| Secrets / credentials | `*.pem`, `*.key`, `credentials.json`, `secrets.*` |
| IDE / editor / OS | `.idea/`, `.vscode/`, `*.swp`, `.DS_Store`, `Thumbs.db` |
| Logs · coverage · temp | `*.log`, `coverage/`, `htmlcov/`, `*.tmp`, `*.bak`, `*.orig` |

- Root `.gitignore` covers project-wide patterns; subdirectory files only for local overrides.
- ✗ rely on `.gitignore` negation patterns for secrets (unreliable).
- Global gitignore (`~/.config/git/ignore`) for personal IDE/OS files.
- New project → start from language/framework template + project additions. Review in code review — missing entries = secrets/artifacts in repo.

---

## 9. Hooks

| Hook | Trigger | Enforces |
|---|---|---|
| `pre-commit` | Before commit | Lint · format · ✗ secrets in staged files · reject files > 5 MB |
| `commit-msg` | After message | Conventional Commits format (§3) |
| `pre-push` | Before push | Tests pass · build succeeds · branch name valid · ✗ push to protected branches |

- Hooks stored in repo (`.githooks/` or `husky`/`pre-commit`/`lefthook`). Setup automated: `git config core.hooksPath .githooks` in init script.
- pre-commit < 10 s, pre-push < 60 s. Hook failure = operation blocked. ✗ `--no-verify` ; exception: documented emergency with follow-up fix.
- Secret detection scans staged diff for API keys, tokens, passwords, private keys.
- Protected-branch rules enforced server-side (branch protection). ✗ rely solely on client-side hooks. See [cicd](../cicd/STANDARDS.md) for pipeline-as-gatekeeper.

---

## 10. Large Files

| Threshold | Action |
|---|---|
| < 1 MB | Commit normally |
| 1–5 MB | Justify in commit message; consider alternatives |
| 5–100 MB | Must use Git LFS |
| > 100 MB | ✗ In repo. External storage (S3, artifact registry) with reference |

- ✗ Binary files unless essential (fonts, small icons, certificates). Images → optimize; prefer SVG over raster.
- Data files → external storage. Compiled artifacts → build from source. ✗ commit `.o`, `.class`, `.pyc`, `.dll`, `.so`.
- LFS tracked by extension pattern in `.gitattributes` at repo root (`*.psd`, `*.zip`, `*.bin`, `*.model`, …). LFS quota monitored, old versions pruned.
- CI must `git lfs install` + `git lfs pull` if LFS files needed for build.

---

## 11. Monorepo Git Practices

- Commit touches one package/service/module when possible. Scope = package name: `feat(auth): add token refresh`.
- Cross-cutting changes → single commit scoped `shared`/`core`.
- `CODEOWNERS` maps directory paths → responsible teams. PR auto-assigns reviewers by changed path. Every deployable directory has ≥ 1 owner.
- Large monorepos → sparse checkout per area; CI runs only affected paths (path-filter). See [cicd](../cicd/STANDARDS.md).
- Single `main` for the entire monorepo. ✗ per-package branches. Tags + release branches scoped: `auth/v1.2.3`, `release/auth/1.2`.

---

## 12. Sensitive Data

### Prevention

- Pre-commit hook scans for secrets (§9). ✗ rely on developer discipline alone.
- `.gitignore` covers all known secret file patterns (§8).
- Environment-specific values → environment variables | secret manager. ✗ config files in repo. See [security](../security/STANDARDS.md) for secrets architecture.

### Detection Patterns

| Pattern | Examples |
|---|---|
| API keys | `AKIA*`, `sk-*`, `ghp_*`, `glpat-*` |
| Private keys | `-----BEGIN.*PRIVATE KEY-----` |
| Connection strings | `postgres://`, `mysql://`, `mongodb+srv://` with passwords |
| Tokens | `Bearer .*`, `token = ".*"`, `password = ".*"` |
| High-entropy strings | Base64/hex > 40 chars in assignment context |

Tools: `gitleaks`, `trufflehog`, `detect-secrets`, `git-secrets` — ≥ 1 required in pre-commit.

### Remediation (Secret Committed)

Severity **Critical** — security incident. Ordered:

1. **Revoke** the secret immediately — assume compromised. ✗ remove from history first.
2. **Rotate** the credential; deploy new to all consumers.
3. **Remove** from history via `git filter-repo` (preferred) or BFG Repo-Cleaner. ✗ `git filter-branch` (deprecated, error-prone).
4. **Force-push** cleaned history. Collaborators re-clone or `git fetch --all && git reset --hard origin/main`.
5. **Add** pattern to pre-commit hook + `.gitignore`.
6. **Audit** access logs for the compromised credential.

✗ assume the secret is safe because "nobody saw it" — bots scrape public repos in seconds.

---

## 13. Scale Matrix

Git discipline by project scale. Scale definitions → [architecture](../architecture/STANDARDS.md) §12.

| Practice | PoC | Small | Production |
|---|---|---|---|
| Branching model | Direct to `main` | Trunk + short branches | Trunk + release branches |
| Commit message format | Type prefix + subject | Full format (§3) | Full format + issue refs |
| PR required | ✗ | Required (counts → code_review) | Required (counts → code_review) |
| Merge strategy | Optional | Squash default | Squash default (merge for releases) |
| Tags | Optional | `v*` on releases | SemVer + release notes |
| Changelog | ✗ | `[Unreleased]` maintained | Keep a Changelog per release |
| Pre-commit hooks | Recommended | Lint + format | Lint + format + secrets |
| Pre-push hooks | ✗ | Recommended (tests) | Required (tests + build) |
| `.gitignore` | Basic template | Full template | Full + audited |
| Branch protection | ✗ | `main` protected | `main` + `release/*` protected |
| CODEOWNERS | ✗ | ✗ | Required |
| Secret scanning | ✗ | Pre-commit | Pre-commit + CI + server-side |
| Signed commits | ✗ | ✗ | Required for releases |
| History cleanliness | Informal | Clean `main` (squash) | Linear `main`, auditable |

---

## 14. Checklist

### New Repository Setup

- [ ] `main` created, set as default, branch protection configured
- [ ] `.gitignore` from language/framework template + project additions
- [ ] `.gitattributes` with LFS patterns if needed
- [ ] `CODEOWNERS` file (production scale)
- [ ] Hooks configured: pre-commit (lint + format + secret scan) · commit-msg (format)
- [ ] CI triggered on push + PR ([cicd](../cicd/STANDARDS.md))
- [ ] Merge strategy set in platform (squash default) · PR template with summary + test plan
- [ ] `CHANGELOG.md` created with `[Unreleased]` section

### Every Commit

- [ ] One logical change per commit
- [ ] Message follows Conventional Commits (§3): type prefix, imperative, ≤ 72-char subject
- [ ] No secrets, credentials, or environment-specific values
- [ ] No files > 5 MB (LFS or external storage) · no build artifacts or generated files
- [ ] Tests pass · build succeeds · pre-commit hooks pass without `--no-verify`

### Every PR

- [ ] Branch name follows convention (§1)
- [ ] PR description: summary + test plan + issue reference
- [ ] CI green before requesting review · all review comments resolved
- [ ] Squash merged (feature/fix) or merge commit (release/hotfix) · branch deleted after merge

### Release

- [ ] Annotated (signed at production scale) tag on `main`: `v<MAJOR>.<MINOR>.<PATCH>`
- [ ] Version bumped per SemVer in the single source of truth
- [ ] `CHANGELOG.md` `[Unreleased]` promoted to the version with date
- [ ] All CI checks pass on the tagged commit
- [ ] Pre-release tags used for RC/beta/alpha: `v1.0.0-rc.1`
