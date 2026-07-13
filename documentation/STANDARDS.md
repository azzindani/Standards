# Documentation Standards

> How a project writes, places, and maintains every document — README, API docs, ADRs, runbooks, and comments — so the docs stay true to the code.

**ID** `documentation` · **Tier** Core · **Version** 1.0
**Owns** Diátaxis mode discipline · README contract · API-doc sourcing · ADR format + lifecycle · runbook format · doc comments · inline comments · docs-as-code · doc-rot prevention · doc location
**Defers to** semver + changelog format + categories → [git](../git/STANDARDS.md) · release automation → [cicd](../cicd/STANDARDS.md) · API contract design → [api](../api/STANDARDS.md) · in-function comment mechanics → [code_writing](../code_writing/STANDARDS.md) · architecture principles ADRs cite → [architecture](../architecture/STANDARDS.md) · runbook alert thresholds → [observability](../observability/STANDARDS.md) · file placement → [directory](../directory/STANDARDS.md)
**Load with** [git](../git/STANDARDS.md) · [api](../api/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Diátaxis: The Four Modes](#2-diátaxis-the-four-modes)
3. [Documentation Types by Scale](#3-documentation-types-by-scale)
4. [README Contract](#4-readme-contract)
5. [API Documentation](#5-api-documentation)
6. [Architecture Decision Records](#6-architecture-decision-records)
7. [Runbooks](#7-runbooks)
8. [Doc Comments](#8-doc-comments)
9. [Inline Comments](#9-inline-comments)
10. [Changelog and Release Notes](#10-changelog-and-release-notes)
11. [Docs-as-Code and Maintenance](#11-docs-as-code-and-maintenance)
12. [Documentation Location](#12-documentation-location)
13. [Anti-Patterns](#13-anti-patterns)
14. [Scale Matrix](#14-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Principles

| # | Rule |
|---|---|
| 1 | Documentation is a deliverable, ✗ an afterthought |
| 2 | A doc that lies is worse than no doc — it costs a reader trust and time |
| 3 | Docs live with the code and change in the same commit — proximity fights drift |
| 4 | Docs are reviewed in the diff, like code |
| 5 | An undocumented public API is an incomplete feature — ✗ merge it |
| 6 | Derive from the source of truth (schema, code, history); ✗ hand-maintain what can be generated |
| 7 | One document serves one Diátaxis mode — mixing modes is the core failure (§2) |

---

## 2. Diátaxis: The Four Modes

Every document serves exactly one of four user needs. Mixing modes in one document is the central documentation failure — it serves none of them well.

| Mode | Serves | User is | Answers | Example |
|---|---|---|---|---|
| Tutorial | Learning | A newcomer, being taught | "Teach me by doing" | Getting-started walkthrough |
| How-to guide | A task | A user with a goal | "How do I achieve X?" | "How to rotate the signing key" |
| Reference | Looking up | A user who knows the goal | "What exactly is X?" | API reference, config keys |
| Explanation | Understanding | A user who wants context | "Why is it this way?" | ADR, architecture overview |

### Mode Rules

| Rule | Detail |
|---|---|
| One mode per document | ✗ a tutorial that drifts into API reference; ✗ a reference padded with rationale |
| Learning vs doing are separate | A tutorial teaches; a how-to executes a known task — ✗ conflate them |
| Reference is dry and complete | Describes the machinery; ✗ teaches, ✗ persuades |
| Explanation carries the "why" | Rationale, trade-offs, and history go here (and in ADRs, §6), ✗ in reference |
| Link across modes | A how-to links to the reference it uses; a tutorial links to explanation — ✗ inline the other mode |

---

## 3. Documentation Types by Scale

| Type | Mode | Audience | Location | Update trigger |
|---|---|---|---|---|
| README | Mixed entry point | Contributors · evaluators | Repo root | Project scope change |
| API docs | Reference | Interface consumers | Co-located with code | Interface change |
| ADR | Explanation | Future maintainers | `docs/adr/` | Architectural decision |
| Runbook | How-to | Operators · on-call | `docs/runbooks/` | Ops procedure change |
| Doc comment | Reference | Developers reading source | Inline | Public API change |
| Changelog | Reference | Users · upgraders | Repo root `CHANGELOG.md` | Every release |
| Inline comment | Explanation | Developers reading source | Inline | Logic change |

| Type | Prototype | Production | Scale |
|---|---|---|---|
| README | Purpose + run | Full structure | Full + badges |
| API docs | ✗ | Public API | All public interfaces |
| ADR | ✗ | Every architectural choice | + backfilled decisions |
| Runbook | ✗ | Every ops procedure | + tested quarterly |
| Doc comments | ✗ | Public functions | Full public surface |
| Changelog | ✗ | Recommended | Required, CI-enforced |

---

## 4. README Contract

The README is the entry point. A reader decides in 30 seconds whether the project is relevant.

### Sections, in order

| # | Section | Content |
|---|---|---|
| 1 | Title + one-liner | What it does — one sentence, directly under the title |
| 2 | Badges | Build · coverage · version · license (production only) |
| 3 | Overview | 2–5 sentences: problem → solution |
| 4 | Quick Start | Clone to working state in ≤ 5 commands, copy-paste-able |
| 5 | Installation | Full install: prerequisites with min versions, all platforms |
| 6 | Usage | Primary use cases with commands |
| 7 | Configuration | Configurable values, defaults, env vars |
| 8 | Architecture | Brief; links to ADRs for depth |
| 9 | Contributing | Dev setup, tests, how to submit changes |
| 10 | License | Type + link to LICENSE |

### Rules

- Title = project name. ✗ marketing taglines · ✗ version numbers in the title.
- One-liner directly under the title — no blank line, no badge between.
- Quick Start works by copy-paste, tested on a clean machine.
- ✗ "TODO" sections in a committed README — incomplete = not committed.
- Prerequisites list explicit minimum version numbers. Paths relative to repo root.
- Badges on one line after the one-liner. ✗ decorative badges (stars, downloads) unless a public library.

---

## 5. API Documentation

API docs are **reference mode** and describe contracts consumers depend on. API contract design → [api](../api/STANDARDS.md).

### Schema-First

Documentation derives from the contract, ✗ the implementation. Source of truth = the schema (OpenAPI · protobuf · GraphQL SDL · type signatures).

| Rule | Detail |
|---|---|
| Schema-first | Define schema → generate docs → implement code |
| Auto-generated | Docs regenerate from schema/types at build time |
| Manual supplement | Only for concepts, guides, examples — never for endpoint signatures |
| Version-coupled | Doc version matches API version exactly |

### Required per Endpoint/Interface

Method + path / signature · one-sentence description · parameters (name · type · required · default) · request body schema (required fields marked) · response schema (success + error shapes) · error codes · authentication · rate limits (if any) · deprecation notice with migration path (if deprecated).

### Rules

- Generated docs rebuild every CI run — ✗ hand-maintained endpoint lists. Doc-generation failure = build failure.
- Every breaking change reflected in docs before merge.
- Examples live in a dedicated section, ✗ inline with schema definitions.
- Versioned APIs keep docs for every supported version; deprecated endpoints show a sunset date + replacement.

---

## 6. Architecture Decision Records

ADRs are **explanation mode** — they capture the *why* behind an architectural choice. Immutable once accepted: superseded by a new ADR, ✗ edited retroactively.

### When to Write

| Trigger | Example |
|---|---|
| Technology selection | PostgreSQL over SQLite for multi-user |
| Pattern adoption | Event sourcing for the audit trail |
| Structural decision | Split monolith into 3 services |
| Rejected alternative | Evaluated GraphQL, stayed with REST |
| Constraint acceptance | Accept 5 s cold start for serverless |
| Security boundary change | Move auth from app to gateway |

Rule: debated for more than 15 minutes → write an ADR.

### Format

Every ADR has these fields: **Title** (`ADR-NNNN: <decision>`, sequential) · **Date** (ISO 8601) · **Status** · **Context** (the forcing problem, facts only) · **Decision** (one clear statement) · **Consequences** (positive, negative, and neutral — all three) · **Alternatives** (options considered and why rejected, minimum one).

### Rules

| Rule | Detail |
|---|---|
| File naming | `docs/adr/NNNN-short-title.md`, zero-padded 4 digits |
| Immutable | ✗ edit an accepted ADR — write a superseding ADR, update the old one's status |
| Reviewed like code | ADRs go through code review |
| Status lifecycle | `proposed` → `accepted` → optionally `deprecated` \| `superseded by ADR-NNNN` |
| ✗ rejected status | A non-accepted proposal never enters the ADR log — it is a discussion artifact |
| Alternatives mandatory | ✗ an ADR without an alternatives section |
| Linked | Referenced from the README architecture section; cites [architecture](../architecture/STANDARDS.md) principles |

---

## 7. Runbooks

Runbooks are **how-to mode**, written for the operator responding at 3 AM, ✗ the architect. Every alert links to a runbook — an alert with no runbook is an incomplete alert. Alert thresholds → [observability](../observability/STANDARDS.md).

### When to Write

New deployment procedure · known failure mode (pool exhaustion) · incident response (503 > 5 min) · data operation (backfill from backup) · scaling procedure · secret rotation.

### Format

Fields: **Title** (searchable) · **Severity** (`P1` immediate · `P2` hours · `P3` days) · **Symptoms** (observable triggers) · **Prerequisites** (access, tools) · **Steps** (numbered, one atomic action each) · **Verification** (how to confirm each step) · **Rollback** (undo for every destructive step) · **Escalation** (who to contact).

### Rules

- Every step is one atomic action — ✗ compound steps ("do X then Y").
- Commands are literal copy-paste — ✗ pseudocode, ✗ "run the usual deploy".
- Every destructive step is immediately followed by its rollback step.
- Variables use `${PLACEHOLDER}` with a legend at the top.
- Tested quarterly on staging — an untested runbook is not a runbook.
- Self-contained — ✗ require reading external docs to execute. Version-stamped; links to monitoring dashboards for verification.

---

## 8. Doc Comments

Doc comments document the **public API surface** (reference mode). Internal implementation is self-documenting through clean code. In-function comment mechanics → [code_writing](../code_writing/STANDARDS.md).

| Element | Doc comment | Notes |
|---|---|---|
| Public function/method | Yes | Contract: inputs, outputs, errors, side effects |
| Public type/class | Yes | Purpose + invariants |
| Public constant | If non-obvious | What it controls |
| Module/package | Yes | One-line purpose + responsibility boundary |
| Private function/type | ✗ | Only if the algorithm/invariant is non-obvious |
| Test function | ✗ | The name states the intent |

Content, when present: summary (one sentence, what not how) · parameters · returns · errors/exceptions · side effects · thread safety (if concurrent) · panic/abort conditions.

### Rules

- First sentence = a complete summary; tools extract it as the short description.
- ✗ restate the name (`/// Gets the user` on `get_user()`) · ✗ restate types.
- Document *why* and *when*, ✗ *what* — the signature already says what.
- Describe the contract from the caller's perspective; ✗ implementation details (they change, contracts persist).
- An empty doc comment is worse than none. Link related functions/types.

---

## 9. Inline Comments

Comments inside function bodies (explanation mode). Full mechanics → [code_writing](../code_writing/STANDARDS.md).

| Comment adds value | Comment destroys value |
|---|---|
| Non-obvious algorithm — why this approach | Restating code in English |
| Business rule — links to spec | Commented-out code (use version control) |
| Workaround — references the issue tracker | TODO without an issue link |
| Performance choice — why O(n) over a hash | Journal comments ("changed X on date") |
| Magic number — what it means and why | Closing-brace comments (`// end if`) |
| Intentional fallthrough — confirmation | Apology comments ("sorry for this hack") |

### Rules

- Comments explain *why*; code explains *what*.
- `TODO(owner): description — ISSUE-NNN` and `FIXME(owner): … — ISSUE-NNN`. ✗ untracked TODOs.
- ✗ HACK/XXX/TEMP comments — fix it or file an issue with a TODO.
- Comment on the line *before* the code, ✗ trailing (except a single-line field annotation).
- Commented-out code must not survive review. A comment over 3 lines → consider a doc comment or an ADR.

---

## 10. Changelog and Release Notes

The changelog **format** — semver bands, and the Added/Changed/Deprecated/Removed/Fixed/Security categories — is owned by [git](../git/STANDARDS.md). ✗ restate the taxonomy here. This section covers only the documentation-side concerns.

| Concern | Rule |
|---|---|
| Location | `CHANGELOG.md` at the repo root — the conventional path tools expect |
| Who updates it | The author of a user-visible change, in the same PR — ✗ a release-time scramble |
| When | Every entry lands under `## [Unreleased]`; a release renames that heading to the version + date |
| Audience | Written for humans — ✗ commit hashes, ✗ internal refactors, ✗ vague "various improvements" |
| Release notes rendering | Generated from the changelog; each version heading links to the git comparison URL |
| Migration notes | A breaking change ships with an upgrade path in the release notes |
| Source | Entries derived from history — see [git](../git/STANDARDS.md) for deriving them from commits |

Every entry names one user-visible change in one line, starting with a verb. Deriving categories and version bands → [git](../git/STANDARDS.md).

---

## 11. Docs-as-Code and Maintenance

Docs are updated in the same commit as the code. Stale docs are bugs.

| Rule | Detail |
|---|---|
| Definition of done | A feature is not done until its docs are updated |
| Reviewed in the diff | Missing doc update blocks the review |
| Public API change → doc + changelog | Both, in the same PR |
| Breaking change → doc + changelog + migration guide | All three |
| Stale docs filed as bugs | Same priority as code bugs |
| Docs are tested | CI validates links; generated docs must build |

### Staleness Detection

| Method | Catches |
|---|---|
| CI link checker | Broken internal/external links |
| Doc-generation build | Schema drift between code and docs |
| PR template checkbox | "Docs updated?" — forces author awareness |
| Automated diff check | Public API changed without a doc-comment change |
| Quarterly review | Runbook, README, and ADR accuracy |

Debt rules: ✗ "document it later" — document now or file a tracked issue. Doc debt counts toward technical debt. An undocumented public API is an incomplete feature.

---

## 12. Documentation Location

Co-locate docs with the code they describe; proximity reduces drift. File placement conventions → [directory](../directory/STANDARDS.md).

| Document | Location |
|---|---|
| README | Repo root |
| API docs (source) | Inline doc comments |
| API docs (generated) | Build output / hosted site (✗ committed) |
| ADRs | `docs/adr/` |
| Runbooks | `docs/runbooks/` |
| Changelog | Repo root `CHANGELOG.md` |
| Contribution guide | Repo root `CONTRIBUTING.md` |
| License | Repo root `LICENSE` |

| Anti-pattern | Problem | Fix |
|---|---|---|
| Separate wiki as source of truth | Drifts; not versioned; no review | Repo `docs/`, link from the wiki |
| Google Docs for technical specs | No version control, access issues | ADRs in the repo |
| Docs in a different repo | Separate history; easy to forget | Co-locate or use submodules |
| README as the only doc | Grows unbounded; mixes audiences | Split into dedicated files |
| Docs committed in the build output dir | Regenerated on build; merge conflicts | `.gitignore` it |

Monorepo: root README gives overview + navigation; each package has its own README; cross-cutting ADRs at root `docs/adr/`, package-specific at `packages/<name>/docs/adr/`. ✗ duplicate between root and package docs — link instead.

---

## 13. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Mixing Diátaxis modes | A doc serving four needs serves none | One mode per document (§2) |
| Hand-maintained API endpoint list | Drifts from the real contract | Generate from the schema (§5) |
| Editing an accepted ADR | Rewrites history; loses the decision trail | Supersede with a new ADR (§6) |
| Runbook with no runbook link on the alert | On-call has no procedure at 3 AM | Every alert links to a runbook (§7) |
| Restating semver/changelog taxonomy here | Duplicates the owner; the two drift | Cross-reference [git](../git/STANDARDS.md) (§10) |
| Doc comment restating the signature | Pure noise; drifts from code | Document why/when, not what (§8) |
| "Document it later" | Later never comes; the API ships undocumented | Document now or file an issue (§11) |
| Wiki as source of truth | Unversioned, unreviewed, drifts | Repo docs, link from the wiki (§12) |

---

## 14. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| README | Purpose + run | Full structure (§4) | Full + badges |
| API docs | ✗ | Public API doc comments | Generated docs + portal |
| ADRs | ✗ | Every architectural decision | + backfilled decisions |
| Runbooks | ✗ | Every ops procedure | + tested quarterly |
| Doc comments | ✗ | Public functions | Full public surface |
| Changelog | ✗ | Recommended | Required, CI-enforced |
| Link checking | ✗ | Manual | Automated in CI |
| Doc generation | ✗ | Optional | Required; failure = build failure |
| PR doc checkbox | ✗ | Recommended | Required in the PR template |

Transitions: PoC → Production — add full README, public API doc comments, CHANGELOG, ADRs, runbooks, CI doc validation, PR doc checkbox, quarterly review; backfill undocumented decisions as ADRs.

---

## 15. Checklist

- [ ] Every document serves exactly one Diátaxis mode
- [ ] README present with all required sections in order
- [ ] README Quick Start works by copy-paste on a clean machine
- [ ] No "TODO" sections in the committed README
- [ ] API docs generated from the schema; the endpoint list is not hand-maintained
- [ ] Doc-generation failure fails the build
- [ ] Every breaking API change reflected in docs before merge
- [ ] ADR written for every decision debated more than 15 minutes
- [ ] ADRs carry context, decision, all-three consequences, and alternatives
- [ ] Accepted ADRs are never edited — superseded instead
- [ ] Every alert links to a runbook
- [ ] Runbook steps are atomic, copy-paste literal, with a rollback per destructive step
- [ ] Runbooks tested quarterly on staging
- [ ] Every public function, type, and module has a doc comment
- [ ] Doc comments state why/when, never restate the signature
- [ ] Inline comments explain why; TODOs/FIXMEs carry an issue link
- [ ] No commented-out code survives review
- [ ] Changelog lives at repo root and is updated by the change author in the same PR
- [ ] Changelog defers semver bands and categories to git; no taxonomy restated here
- [ ] Breaking changes ship with migration notes
- [ ] Docs updated in the same commit as the code; reviewed in the diff
- [ ] CI validates all links; generated docs build successfully
- [ ] Docs co-located with code; no external wiki as source of truth
