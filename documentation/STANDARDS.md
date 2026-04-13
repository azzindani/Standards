# Documentation Standards

Rules for all project documentation — README, API docs, ADRs, runbooks,
changelogs, inline comments, and operational procedures. Language-agnostic.

Documentation is a deliverable, not an afterthought. Stale docs are bugs.
Undocumented public APIs are incomplete features.

Composable with: Code Writing Standards (§6 comments), API Standards,
Git Standards (changelog from history), Architecture Standards.

---

## Table of Contents

1. [Documentation Types](#1-documentation-types)
2. [README Standards](#2-readme-standards)
3. [API Documentation](#3-api-documentation)
4. [Architecture Decision Records](#4-architecture-decision-records)
5. [Runbooks](#5-runbooks)
6. [Code Documentation](#6-code-documentation)
7. [Changelog](#7-changelog)
8. [Inline Documentation](#8-inline-documentation)
9. [Documentation Maintenance](#9-documentation-maintenance)
10. [Documentation Location](#10-documentation-location)
11. [Scale Matrix](#11-scale-matrix)
12. [Documentation Checklist](#12-documentation-checklist)

---

## 1. Documentation Types

Every project produces a subset of these document types based on scale.

| Type | Audience | Location | Update Trigger |
|---|---|---|---|
| README | New contributors · evaluators | Repo root | Project scope change |
| API docs | Consumers of public interfaces | Co-located with code | Interface change |
| ADR | Future maintainers · architects | `docs/adr/` | Architectural decision made |
| Runbook | Operators · on-call engineers | `docs/runbooks/` | Operational procedure change |
| Code docs | Developers reading source | Inline with code | Public API change |
| Changelog | Users · upgraders | Repo root `CHANGELOG.md` | Every release |
| Inline comments | Developers reading source | Inline with code | Logic change in commented area |

### Required by Scale

| Type | PoC / Script | Small Project | Production System |
|---|---|---|---|
| README | Minimal (purpose + run) | Full structure | Full structure + badges |
| API docs | ✗ | Public API only | All public interfaces |
| ADR | ✗ | ✗ | Required for every architectural choice |
| Runbook | ✗ | ✗ | Required for every operational procedure |
| Code docs | ✗ | Public functions | All public API surface |
| Changelog | ✗ | Recommended | Required |
| Inline comments | Only for non-obvious logic | Non-obvious logic | Non-obvious logic + cross-references |

---

## 2. README Standards

README is the entry point. Reader decides in 30 seconds whether project is relevant.

### Required Sections (in order)

| # | Section | Content |
|---|---|---|
| 1 | Title + one-line description | What this project does — one sentence |
| 2 | Status badges | Build · coverage · version · license (production only) |
| 3 | Overview | 2–5 sentences expanding the one-liner. Problem → solution |
| 4 | Quick Start | Minimum steps from clone to working state. ≤ 5 commands |
| 5 | Installation | Full installation with prerequisites, all platforms |
| 6 | Usage | Primary use cases with commands/invocations |
| 7 | Configuration | All configurable values, defaults, environment variables |
| 8 | Architecture | Brief system description; link to ADRs for depth |
| 9 | Contributing | How to set up dev environment, run tests, submit changes |
| 10 | License | License type + link to LICENSE file |

### README Rules

- Title = project name. ✗ marketing taglines · ✗ version numbers in title.
- One-liner goes directly under title — no blank lines, no badges between.
- Quick Start must work with copy-paste. Every command tested on clean machine.
- ✗ "TODO" sections in committed README. Incomplete = not committed.
- Prerequisites listed explicitly with minimum version numbers.
- All paths in README relative to repo root.
- Links to headings within same file use anchor references.
- External links use full URLs; check annually for rot.

### Badge Rules (Production Only)

| Badge | Required | Source |
|---|---|---|
| Build status | Yes | CI system |
| Test coverage | Yes | Coverage tool |
| Version/release | Yes | Package registry or Git tag |
| License | Yes | LICENSE file |
| Dependencies status | Recommended | Dependency checker |

Badges appear on one line, immediately after title + one-liner.
✗ decorative badges (stars, downloads) unless project is a public library.

---

## 3. API Documentation

API docs describe contracts consumers depend on. See `api/STANDARDS.md` for
full API design rules.

### Schema-First Principle

Documentation derives from the contract, not the implementation.
Source of truth = schema definition (OpenAPI, protobuf, GraphQL SDL, type signatures).

| Approach | Rule |
|---|---|
| Schema-first | Define schema → generate docs → implement code |
| Auto-generated | Docs generated from schema/types at build time |
| Manual supplement | Only for concepts, guides, examples — never for endpoint signatures |
| Version-coupled | Docs version matches API version exactly |

### Required Per Endpoint/Interface

| Element | Required | Notes |
|---|---|---|
| Method + path / function signature | Yes | Exact contract |
| Description | Yes | One sentence: what it does |
| Parameters (name, type, required, default) | Yes | Table format |
| Request body schema | If applicable | With required fields marked |
| Response schema | Yes | Success + error shapes |
| Error codes | Yes | All possible error responses |
| Authentication | Yes | What credentials required |
| Rate limits | If applicable | Requests per window |
| Deprecation notice | If deprecated | Migration path included |

### API Doc Rules

- Generated docs rebuild on every CI run. ✗ manually maintained endpoint lists.
- Every breaking change reflected in docs before merge.
- Doc generation failure = build failure.
- Examples live in a dedicated section, not inline with schema definitions.
- Versioned APIs maintain docs for all supported versions.
- Deprecated endpoints display prominently with sunset date + replacement.

---

## 4. Architecture Decision Records

ADRs capture the *why* behind architectural choices. They are immutable once
accepted — superseded by new ADRs, never edited retroactively.

### When to Write an ADR

| Trigger | Example |
|---|---|
| Technology selection | Chose PostgreSQL over SQLite for multi-user |
| Pattern adoption | Adopted event sourcing for audit trail |
| Structural decision | Split monolith into 3 services |
| Rejected alternative | Evaluated GraphQL, stayed with REST |
| Constraint acceptance | Accepted 5s cold start for serverless |
| Security boundary change | Moved auth from app layer to gateway |

Rule: if you debated it for more than 15 minutes, write an ADR.

### ADR Format

Every ADR follows this exact structure:

| Section | Content |
|---|---|
| Title | `ADR-NNNN: <decision title>` — sequential numbering |
| Date | ISO 8601 date of decision |
| Status | `proposed` → `accepted` → `deprecated` or `superseded by ADR-NNNN` |
| Context | Problem or situation forcing the decision. Facts only, no opinion |
| Decision | What was decided. One clear statement |
| Consequences | Positive, negative, and neutral outcomes. All three required |
| Alternatives | Options considered and why rejected. Minimum one alternative |

### ADR Rules

- File naming: `docs/adr/NNNN-short-title.md` — zero-padded 4-digit number.
- ✗ edit accepted ADRs. Write new ADR that supersedes. Update status of old.
- ADRs are reviewed in code review like any other code artifact.
- Status lifecycle: `proposed` → `accepted` → optionally `deprecated` | `superseded`.
- ✗ ADRs without alternatives section. Every decision has alternatives — document them.
- Link ADRs from README architecture section.
- ADRs reference architecture principles (see `architecture/STANDARDS.md §1`).

### Status Lifecycle

```
proposed ──→ accepted ──→ [active indefinitely]
                │
                ├──→ deprecated (no longer relevant)
                │
                └──→ superseded by ADR-NNNN (replaced by new decision)
```

✗ `rejected` status. Rejected proposals are not ADRs — they are discussion artifacts.
If a proposal is not accepted, it does not enter the ADR log.

---

## 5. Runbooks

Runbooks document operational procedures for production systems.
Written for the operator who is responding at 3 AM, not the architect.

### When to Write a Runbook

| Trigger | Example |
|---|---|
| New deployment procedure | Deploy service X to production |
| Known failure mode | Database connection pool exhaustion |
| Incident response | Service returns 503 for > 5 minutes |
| Data operation | Backfill missing records from backup |
| Scaling procedure | Scale service from 2 to 8 replicas |
| Secret rotation | Rotate API keys for external service |

### Runbook Format

| Section | Content |
|---|---|
| Title | Exact procedure name — searchable |
| Severity | `P1` (immediate) · `P2` (hours) · `P3` (days) |
| Symptoms | Observable indicators that trigger this runbook |
| Prerequisites | Access, tools, permissions required before starting |
| Steps | Numbered, copy-paste commands. Each step = one action |
| Verification | How to confirm each step succeeded |
| Rollback | How to undo if procedure fails. Required for every destructive step |
| Escalation | Who to contact if runbook does not resolve the issue |

### Runbook Rules

- Every step is one atomic action. ✗ compound steps ("do X then Y").
- Commands are literal copy-paste. ✗ pseudocode · ✗ "run the usual deploy".
- Every destructive step has a rollback step immediately following it.
- Variables in commands use `${PLACEHOLDER}` with a legend at the top.
- Runbooks tested quarterly on staging. Untested runbook = no runbook.
- Version-stamped — runbook states which system version it applies to.
- ✗ runbooks that require reading external docs to execute. Self-contained.
- Time estimates per step. Total estimated time at the top.
- Runbooks link to monitoring dashboards for verification steps.

---

## 6. Code Documentation

Doc comments exist for the public API surface. Internal implementation
does not require doc comments — clean code is self-documenting.
See `code_writing/STANDARDS.md §6` for comment rules within function bodies.

### What to Document

| Element | Doc Comment Required | Notes |
|---|---|---|
| Public function/method | Yes | Contract: inputs, outputs, errors, side effects |
| Public type/struct/class | Yes | Purpose + invariants |
| Public constant | Yes, if non-obvious | What it controls |
| Module/package | Yes | One-line purpose + responsibility boundary |
| Private function | ✗ | Only if algorithm is non-obvious |
| Private type | ✗ | Only if invariants are complex |
| Test function | ✗ | Test name describes intent |

### Doc Comment Content

| Element | Required | Example Content |
|---|---|---|
| Summary | Yes | One sentence: what it does (not how) |
| Parameters | Yes, if any | Name, type, constraints, defaults |
| Returns | Yes, if non-void | Type + what it represents |
| Errors/Exceptions | Yes, if any | Each error condition + type |
| Side effects | Yes, if any | I/O, state mutation, network calls |
| Thread safety | If concurrent | Safe/unsafe + conditions |
| Panics/aborts | If applicable | Conditions that cause hard failure |

### Doc Comment Rules

- First sentence = complete summary. Tools extract this as the short description.
- ✗ restating the function name. `/// Gets the user` on `get_user()` = waste.
- ✗ restating types. `/// Takes a string and returns an int` = waste.
- Document *why* and *when*, not *what* — the signature already says *what*.
- Doc comments describe the contract from the caller's perspective.
- ✗ implementation details in doc comments. Implementation changes; contracts persist.
- Empty doc comments (`///` with no content) are worse than no doc comment.
- Link related functions/types in doc comments using language-appropriate syntax.

---

## 7. Changelog

Track user-visible changes across releases. Follows Keep a Changelog format.

### Format

File: `CHANGELOG.md` at repo root.

Structure per version:

```
## [X.Y.Z] - YYYY-MM-DD

### Added
- New feature description

### Changed
- Existing behavior modification

### Deprecated
- Feature marked for removal

### Removed
- Feature removed in this release

### Fixed
- Bug fix description

### Security
- Vulnerability fix description
```

### Changelog Rules

- Newest version at top. Unreleased changes under `## [Unreleased]` heading.
- Every entry = one user-visible change. One line per change.
- Version numbers follow SemVer: `MAJOR.MINOR.PATCH`.
- ✗ commit hashes in changelog entries. Changelog is for humans, not machines.
- ✗ internal refactors in changelog. Only user-visible changes.
- ✗ vague entries ("various improvements", "bug fixes"). Name the specific change.
- Each entry starts with a verb: Added, Changed, Fixed, Removed, Deprecated.
- Link version headings to Git comparison URLs when hosted.
- See `git/STANDARDS.md` for deriving changelog entries from commit history.

### Version-to-Changelog Mapping

| Version Bump | Changelog Sections Expected |
|---|---|
| MAJOR (breaking) | Changed or Removed (with migration notes) |
| MINOR (feature) | Added, possibly Changed |
| PATCH (fix) | Fixed, possibly Security |

### What to Include vs Exclude

| Include | Exclude |
|---|---|
| New features | Internal refactors |
| Breaking changes | Dependency updates (unless user-visible) |
| Bug fixes | Test additions |
| Deprecations | CI/CD changes |
| Security patches | Code style changes |
| Performance improvements (user-visible) | Documentation-only changes |

---

## 8. Inline Documentation

Comments within function bodies and code blocks. Complementary to
doc comments (§6). See `code_writing/STANDARDS.md §6` for full rules.

### When Comments Add Value

| Scenario | Comment Type | Example Reason |
|---|---|---|
| Non-obvious algorithm | Explanatory | Why this approach over simpler one |
| Business rule encoding | Intent | Links to spec or requirement |
| Workaround for external bug | Context | References issue tracker |
| Performance-critical choice | Justification | Why O(n) scan instead of hash lookup |
| Regex or complex expression | Translation | Human-readable description |
| Magic number | Definition | What the value represents and why |
| Intentional fallthrough | Confirmation | `// intentional: handles both cases` |
| Cross-module dependency | Warning | "This order matters because X depends on Y" |

### When Comments Destroy Value

| Anti-pattern | Problem |
|---|---|
| Restating code in English | Noise; drifts from code |
| Commented-out code | Use version control instead |
| TODO without issue link | Becomes permanent dead comment |
| Journal comments ("changed X on date") | Use version control history |
| Closing-brace comments (`// end if`) | Indicates function too long — refactor |
| Obvious variable narration | `x = x + 1  // increment x` |
| Apology comments ("sorry for this hack") | Fix the hack or file an issue |

### Inline Comment Rules

- Comments explain *why*, not *what*. Code explains *what*.
- TODO format: `TODO(owner): description — ISSUE-NNN`. ✗ untracked TODOs.
- FIXME format: `FIXME(owner): description — ISSUE-NNN`. Same tracking requirement.
- ✗ HACK/XXX/TEMP comments. Either fix it or file an issue with a TODO.
- Comment goes on the line *before* the code it explains. ✗ trailing comments
  unless single-line annotation (e.g., struct field description).
- Commented-out code must not survive code review. Remove or restore.
- Long comments (>3 lines) → consider extracting to doc comment or ADR.

---

## 9. Documentation Maintenance

Docs updated with code changes in the same commit. Stale docs = bugs.

### Core Rules

- Documentation changes are part of the definition of done for every feature.
- Code review checks documentation alongside code. Missing doc update = review blocker.
- Every public API change triggers doc comment update (§6) + changelog entry (§7).
- Breaking changes require: doc comment update + changelog entry + migration guide.
- Stale documentation filed as bugs with same priority as code bugs.
- Docs are tested: links validated in CI, generated docs build successfully.

### Staleness Detection

| Method | What It Catches |
|---|---|
| CI link checker | Broken internal/external links |
| Doc generation build | Schema drift between code and docs |
| PR template checkbox | "Docs updated?" — forces author awareness |
| Quarterly review | Runbooks, README accuracy, ADR relevance |
| Automated diff check | Public API changed without doc comment change |

### Documentation Debt Rules

- ✗ "we'll document it later" — document now or file a tracked issue.
- Documentation issues tracked in same system as code issues.
- Documentation debt counted toward technical debt metrics.
- Undocumented public API = incomplete feature. ✗ merge without docs.

---

## 10. Documentation Location

Co-locate docs with the code they describe. Proximity reduces drift.

### Location Rules

| Document Type | Location | Rationale |
|---|---|---|
| README | Repo root | First file visitors see |
| API docs (source) | Inline with code (doc comments) | Changes with code in same commit |
| API docs (generated) | Build output · hosted site | Auto-generated, not committed |
| ADRs | `docs/adr/` | Separate from code, versioned with repo |
| Runbooks | `docs/runbooks/` | Operators know where to look |
| Changelog | Repo root `CHANGELOG.md` | Convention; tools expect this location |
| Module docs | Module directory | Co-located with module code |
| Configuration docs | README §Configuration or dedicated file | Near config definitions |
| Contribution guide | Repo root `CONTRIBUTING.md` | Convention; GitHub/GitLab auto-links |
| License | Repo root `LICENSE` | Convention; package managers expect this |

### Anti-patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Separate wiki | Drifts from code; not versioned | Move to repo `docs/` |
| Confluence/Notion as source of truth | No version control; no review process | Repo docs with links from wiki |
| Docs in different repo | Separate commit history; easy to forget | Co-locate or use submodules |
| Google Docs for technical specs | No version control; access control issues | ADRs in repo |
| README as the only doc | Grows unbounded; mixes audiences | Split into dedicated files |
| Docs committed in build output dir | Regenerated on build; causes merge conflicts | Add to `.gitignore` |

### Monorepo Documentation

- Root README: project overview + navigation to packages.
- Each package: own README with package-specific docs.
- Shared ADRs at root `docs/adr/` for cross-cutting decisions.
- Package-specific ADRs at `packages/<name>/docs/adr/`.
- ✗ duplicating information between root and package docs. Link instead.

---

## 11. Scale Matrix

Apply documentation rules proportionally to project scale.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| README | Purpose + how to run | Full structure (§2) | Full structure + badges |
| API docs | ✗ | Public API doc comments | Full generated docs + portal |
| ADRs | ✗ | ✗ | Required for every arch decision |
| Runbooks | ✗ | ✗ | Required for every ops procedure |
| Code docs | ✗ | Public function doc comments | Full public API surface |
| Changelog | ✗ | Recommended | Required; enforced in CI |
| Inline comments | Non-obvious logic only | Non-obvious logic | Non-obvious + cross-references |
| Link checking | ✗ | Manual | Automated in CI |
| Doc generation | ✗ | Optional | Required; failure = build failure |
| Quarterly review | ✗ | ✗ | Required; tracked |
| PR doc checkbox | ✗ | Recommended | Required in PR template |
| Contribution guide | ✗ | Recommended | Required |

### Scale Transitions

- PoC → Small: add README full structure, public API doc comments, CHANGELOG.
- Small → Production: add ADRs, runbooks, CI doc validation, PR template
  doc checkbox, quarterly review cadence. Backfill existing undocumented
  decisions as ADRs.

---

## 12. Documentation Checklist

### New Project

- [ ] README created with all required sections (§2)
- [ ] LICENSE file present
- [ ] Quick Start tested on clean machine
- [ ] All prerequisites listed with version numbers
- [ ] CHANGELOG.md initialized (if small+ scale)
- [ ] CONTRIBUTING.md created (if production scale)
- [ ] `docs/` directory structure established
- [ ] Doc generation configured in build (if production scale)

### New Feature

- [ ] Public API doc comments written (§6)
- [ ] README updated if feature changes usage or configuration
- [ ] CHANGELOG.md `[Unreleased]` section updated
- [ ] ADR written if architectural decision was made (§4)
- [ ] Runbook written if new operational procedure introduced (§5)
- [ ] Existing docs reviewed for accuracy after change

### New Release

- [ ] `[Unreleased]` section renamed to version number + date
- [ ] All changelog entries are specific (✗ vague descriptions)
- [ ] Breaking changes have migration notes
- [ ] API docs regenerated and published
- [ ] Runbooks verified against current system version
- [ ] README badges reflect current state

### Code Review — Documentation Check

- [ ] Public API changes have doc comment updates
- [ ] No commented-out code surviving review
- [ ] TODOs/FIXMEs have issue tracker links
- [ ] Inline comments explain *why*, not *what*
- [ ] No stale docs introduced by the change
- [ ] Links tested (internal anchors + external URLs)
- [ ] Changelog entry present for user-visible changes

### Quarterly Maintenance

- [ ] All external links validated (automated or manual)
- [ ] Runbooks tested on staging environment
- [ ] ADRs reviewed — deprecated decisions marked
- [ ] README accuracy verified against current state
- [ ] Generated docs match current codebase
- [ ] Documentation debt issues triaged