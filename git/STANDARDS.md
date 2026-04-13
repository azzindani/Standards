# Git & Version Control Standards

Rules for branching, commits, merges, tags, history hygiene, and repository
discipline. Language-agnostic — applies to every project regardless of stack.

Composable with: `cicd/STANDARDS.md` (pipeline triggers) · `code_review/STANDARDS.md`
(PR process) · `workflow/STANDARDS.md` (branching ↔ lifecycle) ·
`security/STANDARDS.md` (secrets in VCS).

---

## Table of Contents

1. [Branching Strategy](#1-branching-strategy)
2. [Commit Conventions](#2-commit-conventions)
3. [Commit Message Format](#3-commit-message-format)
4. [Merge Strategy](#4-merge-strategy)
5. [Tag Strategy](#5-tag-strategy)
6. [Pull Requests / Merge Requests](#6-pull-requests--merge-requests)
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

### Model Selection

| Scale | Model | Characteristics |
|---|---|---|
| PoC / solo | Trunk-based | Commit directly to `main`, optional short-lived branches |
| Small team (2–5) | Trunk-based + short-lived branches | Feature branches live < 2 days, merge to `main` |
| Production / team (5+) | Trunk-based + release branches | `main` always deployable, `release/*` for stabilization |

✗ Long-lived feature branches (> 3 days). Rebase + split if work exceeds 3 days.
✗ Gitflow for new projects — overhead without proportional benefit.

### Branch Naming

| Pattern | Use |
|---|---|
| `main` | Primary integration branch. Always deployable. |
| `feat/<ticket>-<slug>` | New feature work |
| `fix/<ticket>-<slug>` | Bug fix |
| `refactor/<slug>` | Restructuring, no behavior change |
| `docs/<slug>` | Documentation only |
| `test/<slug>` | Test additions/fixes only |
| `chore/<slug>` | Tooling, deps, config |
| `release/<version>` | Release stabilization (production scale only) |
| `hotfix/<ticket>-<slug>` | Emergency production fix |

Rules:
- Lowercase, hyphen-delimited. ✗ underscores · ✗ uppercase · ✗ spaces.
- `<ticket>` = issue/ticket ID when tracking system exists.
- `<slug>` = 2–4 word summary. Max 50 characters total branch name.
- Delete branch after merge. Zero stale branches.

### Branch Lifecycle

```
create → push → PR → review → merge → delete
```

- Branch from `main` (or `release/*` for hotfixes).
- Pull/rebase from `main` at least daily for branches lasting > 1 day.
- Merge back via PR. ✗ direct push to `main` ; exception: solo PoC scale.

---

## 2. Commit Conventions

### Atomic Commits

One commit = one logical change. Logical change = one of:
- Single feature or sub-feature
- Single bug fix
- Single refactor operation
- Single dependency update
- Single configuration change

✗ Mix refactoring with feature work in same commit.
✗ Mix formatting changes with logic changes.
✗ Commit half-working state (every commit builds + passes tests).

### Commit Granularity

| Too small | Right size | Too large |
|---|---|---|
| Fix typo in one variable | Add input validation to user registration | Implement entire authentication system |
| Add single import | Refactor database layer to use connection pooling | Rewrite frontend + backend + tests |
| Whitespace change | Extract payment processing into dedicated module | Week of work in one commit |

Rule of thumb: reviewer understands the full diff in < 5 minutes → right size.

### What Gets Committed

- Source code, configuration, infrastructure-as-code, documentation, tests.
- ✗ Build artifacts · ✗ generated files · ✗ secrets · ✗ local environment files.
- ✗ Files > 5 MB (see §10 Large Files).
- Lock files (package-lock.json, Cargo.lock, etc.) → commit when they change.

---

## 3. Commit Message Format

### Structure

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type Prefixes

| Type | Meaning |
|---|---|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `refactor` | Code restructuring, no behavior change |
| `docs` | Documentation only |
| `test` | Add/modify tests only |
| `chore` | Build, tooling, deps, config |
| `perf` | Performance improvement, no behavior change |
| `style` | Formatting, whitespace — no logic change |
| `ci` | CI/CD pipeline changes |
| `revert` | Reverts a previous commit |

### Subject Line Rules

| Rule | Constraint |
|---|---|
| Max length | 72 characters |
| Capitalization | Lowercase after type prefix |
| Tense | Imperative mood (`add`, not `added` or `adds`) |
| Punctuation | ✗ trailing period |
| Content | What changed, not how |

### Body Rules

- Separate from subject by blank line.
- Wrap at 72 characters.
- Explain *what* and *why*, not *how* (code shows how).
- Required when subject alone is insufficient context.
- Reference issue/ticket IDs: `Fixes #123`, `Closes PROJ-456`.

### Footer Rules

- Breaking changes: `BREAKING CHANGE: <description>`
- Issue references: `Fixes #<id>` | `Closes #<id>` | `Refs #<id>`
- Co-authors: `Co-authored-by: Name <email>`

---

## 4. Merge Strategy

### Strategy Selection

| Strategy | When to use | Result |
|---|---|---|
| **Merge commit** | Release branches → `main`, hotfixes | Preserves full branch history, clear merge point |
| **Squash merge** | Feature/fix branches → `main` (default) | Single clean commit on `main`, branch detail in PR |
| **Rebase + fast-forward** | Keeping linear history on small branches | Linear history, no merge commits |

### Default: Squash Merge for Feature Branches

- All feature/fix branches → squash merge into `main`.
- PR title becomes commit subject. PR description becomes commit body.
- Branch history preserved in PR record, not in `main` log.

### When to Use Merge Commit

- `release/*` → `main` (preserve release stabilization history).
- `hotfix/*` → `main` and `release/*` simultaneously.
- Long-running integration branches (rare, avoid when possible).

### When to Use Rebase

- Updating feature branch from `main` (rebase onto `main`, not merge `main` into feature).
- ✗ Rebase commits already pushed to shared branch others have pulled.
- ✗ Rebase `main` or `release/*` branches.

---

## 5. Tag Strategy

### Semantic Versioning Tags

Format: `v<MAJOR>.<MINOR>.<PATCH>` following semver.org.

| Component | Increment when |
|---|---|
| MAJOR | Breaking changes to public API/contract |
| MINOR | New features, backward compatible |
| PATCH | Bug fixes, backward compatible |

### Tag Types

| Pattern | Purpose | Example |
|---|---|---|
| `v1.2.3` | Release tag | Stable release |
| `v1.2.3-rc.1` | Release candidate | Pre-release for validation |
| `v1.2.3-beta.1` | Beta release | Feature-complete, not fully tested |
| `v1.2.3-alpha.1` | Alpha release | Early preview |

### Tag Rules

- Tags on `main` branch only (or `release/*` for pre-release).
- Annotated tags only (`git tag -a`). ✗ lightweight tags for releases.
- Tag message = changelog summary for that version.
- Tag after merge, not before.
- ✗ Move or delete published tags. Create new patch version instead.
- Tags trigger release pipelines. See `cicd/STANDARDS.md`.

---

## 6. Pull Requests / Merge Requests

### Size Limits

| Metric | Target | Hard limit |
|---|---|---|
| Lines changed (diff) | < 300 | 500 |
| Files changed | < 10 | 20 |
| Review time | < 30 min | 60 min |

PRs exceeding hard limits → split into stacked PRs or sequential PRs.
Exception: generated code, migrations, large deletions (flag in description).

### PR Description Requirements

Every PR contains:
- **Summary**: 1–3 bullet points describing what changed and why.
- **Test plan**: How the change was verified (manual steps, automated tests, or both).
- **Issue reference**: Link to ticket/issue when applicable.
- **Breaking changes**: Explicit callout if any.
- **Screenshots/output**: Required for UI or output-format changes.

### Review Requirements

| Scale | Minimum reviewers | Auto-merge allowed |
|---|---|---|
| PoC / solo | 0 (self-merge) | Yes |
| Small team | 1 | After approval |
| Production | 2 (1 domain expert) | After all approvals + CI green |

Rules:
- CI passes before review begins. ✗ Review red PRs.
- All review comments resolved before merge.
- Reviewer approves the PR, not individual files.
- See `code_review/STANDARDS.md` for review criteria and feedback style.

### PR Lifecycle

```
draft → ready → CI green → review → approved → merge → branch deleted
```

- Use draft PRs for work-in-progress. ✗ Open non-draft PR until ready for review.
- Stale PRs (no activity > 7 days) → close or rebase and update.
- Author merges after approval. ✗ Reviewer merges (unless team convention states otherwise).

---

## 7. History Hygiene

### Clean History on `main`

- `main` history reads as a linear sequence of logical changes.
- Each commit on `main` builds, passes tests, and is independently deployable.
- Squash merge (§4) produces this by default for feature branches.

### Rebase Before Merge

- Feature branch behind `main` → rebase onto `main` before creating PR.
- ✗ Merge `main` into feature branch (creates noise merge commits).
- Conflicts resolved during rebase, not in a merge commit.

### Interactive Rebase (Local Only)

Permitted on **unpushed** or **force-push-safe** branches only:
- Squash fixup commits into their parent.
- Reword unclear commit messages.
- Reorder commits for logical flow.
- Drop accidental commits (debug logs, temp files).

✗ Interactive rebase on `main`, `release/*`, or any shared branch.
✗ Force-push to branches others have checked out without coordination.

### Fixup Workflow

- Spotted issue in recent commit → `git commit --fixup=<sha>` → autosquash before merge.
- ✗ Separate "fix typo" / "fix linting" commits surviving into `main`.

---

## 8. .gitignore Rules

### Mandatory Ignores (Every Project)

| Category | Examples |
|---|---|
| Build output | `build/`, `dist/`, `target/`, `out/`, `bin/` |
| Dependencies | `node_modules/`, `vendor/`, `.venv/`, `__pycache__/` |
| Environment files | `.env`, `.env.local`, `.env.*.local` |
| Secrets / credentials | `*.pem`, `*.key`, `credentials.json`, `secrets.*` |
| IDE / editor | `.idea/`, `.vscode/`, `*.swp`, `*.swo`, `.DS_Store` |
| OS files | `Thumbs.db`, `.DS_Store`, `Desktop.ini` |
| Logs | `*.log`, `logs/` |
| Coverage / reports | `coverage/`, `.nyc_output/`, `htmlcov/` |
| Temporary files | `*.tmp`, `*.bak`, `*.orig` |

### .gitignore Structure

- Root `.gitignore` covers project-wide patterns.
- Subdirectory `.gitignore` only for directory-specific overrides.
- ✗ Use `.gitignore` to track negation patterns for secrets (unreliable).
- Global gitignore (`~/.config/git/ignore`) for personal IDE/OS files.

### Template Rule

New project → start from language/framework template, then add project-specific entries.
Review `.gitignore` in code review — missing entries = secrets/artifacts in repo.

---

## 9. Hooks

### Required Hooks

| Hook | Trigger | Enforces |
|---|---|---|
| `pre-commit` | Before commit created | Linting · formatting · ✗ secrets in staged files |
| `commit-msg` | After message written | Commit message format (§3) |
| `pre-push` | Before push to remote | Tests pass · build succeeds · ✗ push to protected branches |

### Hook Implementation Rules

- Hooks stored in repo (`.githooks/` or managed by tool like `husky`, `pre-commit`, `lefthook`).
- Setup automated: `git config core.hooksPath .githooks` in project init script.
- Hooks run fast (< 10 seconds for pre-commit, < 60 seconds for pre-push).
- Hook failure = operation blocked. ✗ `--no-verify` bypass ; exception: documented emergency with follow-up fix.

### What Hooks Enforce

| Check | Hook | Action |
|---|---|---|
| Secret detection | `pre-commit` | Scan staged diff for API keys, tokens, passwords, private keys |
| File size | `pre-commit` | Reject files > 5 MB |
| Commit message format | `commit-msg` | Validate type prefix, subject length, imperative mood |
| Branch name format | `pre-push` | Validate against naming convention (§1) |
| Test suite | `pre-push` | Run test suite, block push on failure |
| Lint | `pre-commit` | Run configured linters on staged files |
| Format | `pre-commit` | Auto-format staged files (or reject if not formatted) |

### Server-Side Hooks

- Protected branch rules enforced server-side (GitHub/GitLab branch protection).
- Required status checks, required reviewers — ✗ rely solely on client-side hooks.
- See `cicd/STANDARDS.md` for pipeline-as-gatekeeper.

---

## 10. Large Files

### Size Limits

| Threshold | Action |
|---|---|
| < 1 MB | Commit normally |
| 1–5 MB | Justify in commit message; consider alternatives |
| 5–100 MB | Must use Git LFS |
| > 100 MB | ✗ In repo. Use external storage (S3, artifact registry) with reference |

### Binary File Rules

- ✗ Binary files in repo unless essential (fonts, small icons, certificates).
- Images → optimize before commit. Prefer SVG over raster when possible.
- Data files → external storage. Repo stores schema/reference, not data.
- Compiled artifacts → build from source. ✗ commit `.o`, `.class`, `.pyc`, `.dll`, `.so`.

### Git LFS

- Track by extension pattern, not individual files.
- LFS patterns declared in `.gitattributes` at repo root.
- Common LFS patterns: `*.psd`, `*.ai`, `*.sketch`, `*.zip`, `*.tar.gz`, `*.bin`, `*.model`.
- LFS storage has quota — monitor usage, prune old versions.
- CI/CD pipelines must `git lfs install` + `git lfs pull` if LFS files needed for build.

---

## 11. Monorepo Git Practices

### Commit Scope

- Commit touches one package/service/module per commit when possible.
- Commit message scope = package name: `feat(auth): add token refresh`.
- Cross-cutting changes (shared lib update) → single commit with scope `shared` or `core`.

### Path-Based Ownership

- `CODEOWNERS` file maps directory paths → responsible teams/individuals.
- PR auto-assigns reviewers based on changed paths.
- Every directory with deployable code has at least one owner.

### Sparse Checkout

- Large monorepos → developers use sparse checkout for their area.
- CI checks run only for affected paths (path-filter in pipeline).
- See `cicd/STANDARDS.md` for path-based pipeline triggers.

### Monorepo Branch Rules

- Single `main` branch for entire monorepo. ✗ Per-package branches.
- Tags scoped to package: `auth/v1.2.3`, `api/v2.0.0`.
- Release branches scoped when needed: `release/auth/1.2`.

---

## 12. Sensitive Data

### Prevention

- Pre-commit hook scans for secrets (§9). ✗ Rely on developer discipline alone.
- `.gitignore` covers all known secret file patterns (§8).
- Environment-specific values → environment variables | secret manager. ✗ Config files in repo.
- See `security/STANDARDS.md` for secrets management architecture.

### Detection Patterns

| Pattern | Examples |
|---|---|
| API keys | `AKIA*`, `sk-*`, `ghp_*`, `glpat-*` |
| Private keys | `-----BEGIN.*PRIVATE KEY-----` |
| Connection strings | `postgres://`, `mysql://`, `mongodb+srv://` with passwords |
| Tokens | `Bearer .*`, `token = ".*"`, `password = ".*"` |
| High-entropy strings | Base64/hex strings > 40 characters in assignment context |

Tools: `gitleaks`, `trufflehog`, `detect-secrets`, `git-secrets` — at least one required in pre-commit.

### Remediation (Secret Committed)

Severity: **Critical**. Treat as security incident.

1. **Revoke** the secret immediately. ✗ Remove from history first — assume compromised.
2. **Rotate** the credential. Generate new secret, deploy to all consumers.
3. **Remove** from history using `git filter-repo` (preferred) or `BFG Repo-Cleaner`.
4. **Force-push** cleaned history. All collaborators must re-clone or `git fetch --all && git reset --hard origin/main`.
5. **Add** pattern to pre-commit hook + `.gitignore` to prevent recurrence.
6. **Audit** access logs for the compromised credential.

✗ `git filter-branch` — deprecated, slow, error-prone.
✗ Assume secret is safe because "nobody saw it" — bots scrape public repos in seconds.

---

## 13. Scale Matrix

Git discipline mapped to project scale. See `architecture/STANDARDS.md` §12 for scale definitions.

| Practice | PoC | Small | Production |
|---|---|---|---|
| Branching model | Direct to `main` | Trunk + short branches | Trunk + release branches |
| Commit message format | Type prefix + subject | Full format (§3) | Full format + issue refs |
| PR required | ✗ | Required, 1 reviewer | Required, 2 reviewers |
| Squash merge | Optional | Default | Default (merge for releases) |
| Tags | Optional | `v*` on releases | Semver + release notes |
| Pre-commit hooks | Recommended | Required (lint + format) | Required (lint + format + secrets) |
| Pre-push hooks | ✗ | Recommended (tests) | Required (tests + build) |
| .gitignore | Basic template | Full template | Full + audited |
| Branch protection | ✗ | `main` protected | `main` + `release/*` protected |
| CODEOWNERS | ✗ | ✗ | Required |
| Git LFS | If needed | If needed | Policy documented |
| Secret scanning | ✗ | Pre-commit | Pre-commit + CI + server-side |
| Signed commits | ✗ | ✗ | Required for releases |
| History cleanliness | Informal | Clean `main` (squash) | Linear `main`, auditable |

---

## 14. Checklist

### New Repository Setup

- [ ] `main` branch created and set as default
- [ ] Branch protection rules configured
- [ ] `.gitignore` from language/framework template + project additions
- [ ] `.gitattributes` with LFS patterns if needed
- [ ] `CODEOWNERS` file (production scale)
- [ ] Hooks configured (`.githooks/` or tool-managed)
- [ ] Pre-commit: linting + formatting + secret scanning
- [ ] Commit-msg: message format validation
- [ ] CI pipeline triggered on push + PR (see `cicd/STANDARDS.md`)
- [ ] Merge strategy configured in platform (squash default)
- [ ] PR template with summary + test plan sections

### Every Commit

- [ ] One logical change per commit
- [ ] Commit message follows format (§3): type prefix, imperative, ≤ 72 char subject
- [ ] No secrets, credentials, or environment-specific values
- [ ] No files > 5 MB (use LFS or external storage)
- [ ] No build artifacts or generated files
- [ ] All tests pass · build succeeds
- [ ] Pre-commit hooks pass without `--no-verify`

### Every PR

- [ ] Branch name follows convention (§1)
- [ ] PR description: summary + test plan + issue reference
- [ ] Diff size within limits (< 300 lines target, < 500 hard limit)
- [ ] CI green before requesting review
- [ ] All review comments resolved
- [ ] Squash merged (feature/fix) or merge commit (release/hotfix)
- [ ] Branch deleted after merge

### Release

- [ ] Annotated tag on `main`: `v<MAJOR>.<MINOR>.<PATCH>`
- [ ] Tag message contains changelog summary
- [ ] All CI checks pass on tagged commit
- [ ] Release notes published (platform release feature or `CHANGELOG.md`)
- [ ] Pre-release tags used for RC/beta/alpha: `v1.0.0-rc.1`
