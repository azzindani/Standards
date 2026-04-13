# Development Workflow Standards

Rules governing idea-to-production lifecycle, phase transitions, task
management, technical debt, and AI-assisted development. Every project
follows this lifecycle — scale determines rigor, not whether phases apply.

Composable with: All standards — this document defines *when* each applies.
Cross-references: `architecture/STANDARDS.md` §12 (scale matrix),
`git/STANDARDS.md` (branching per phase), `documentation/STANDARDS.md` (ADRs).

---

## Table of Contents

1. [Development Lifecycle](#1-development-lifecycle)
2. [Idea Phase](#2-idea-phase)
3. [PoC Phase](#3-poc-phase)
4. [MVP Phase](#4-mvp-phase)
5. [Production Phase](#5-production-phase)
6. [Maintenance Phase](#6-maintenance-phase)
7. [Phase Transition Criteria](#7-phase-transition-criteria)
8. [Task Management](#8-task-management)
9. [Technical Debt](#9-technical-debt)
10. [AI-Assisted Development](#10-ai-assisted-development)
11. [Standards Application by Phase](#11-standards-application-by-phase)
12. [Decision Records](#12-decision-records)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklists](#14-checklists)

---

## 1. Development Lifecycle

Five sequential phases. Every project enters at Idea. Projects may skip
PoC if concept is proven. ✗ skip Idea phase — undirected work produces waste.

```
Idea → PoC → MVP → Production → Maintenance
  │      │     │        │            │
  │      │     │        │            └─ sustain · evolve · retire
  │      │     │        └─ full standards · monitoring · ops readiness
  │      │     └─ architecture applied · production-quality code
  │      └─ throwaway-ok · time-boxed · validates concept
  └─ problem statement · feasibility · scope · acceptance criteria
```

### Phase Duration Expectations

| Phase | Typical Duration | Hard Time-Box |
|---|---|---|
| Idea | 1–4 hours | 1 day |
| PoC | 1–3 days | 1 week |
| MVP | 1–4 weeks | Scope-dependent |
| Production | Ongoing | Release cadence |
| Maintenance | Ongoing | Until retirement |

### Rules

- Each phase produces explicit artifacts before advancing.
- Phase transitions require criteria met (see §7).
- Work without a defined phase = untracked work. ✗ untracked work.
- Document current phase in project README or tracking system.

---

## 2. Idea Phase

Goal: Define *what* problem exists, *whether* solving it is feasible,
and *what* success looks like. ✗ writing code in Idea phase.

### Required Artifacts

| Artifact | Content |
|---|---|
| Problem statement | One paragraph: who has the problem, what it is, impact of not solving |
| Feasibility check | Technical constraints, dependencies, unknowns, risks |
| Scope boundary | What is in scope · what is explicitly out of scope |
| Acceptance criteria | Measurable conditions that define "done" for MVP |
| Scale classification | PoC / Small / Production per `architecture/STANDARDS.md` §12 |

### Feasibility Check

Evaluate before committing resources:

| Dimension | Question |
|---|---|
| Technical | Can this be built with known tools/languages? |
| Data | Is required data available and accessible? |
| Integration | Do required APIs/services exist and allow access? |
| Performance | Can it meet latency/throughput requirements? |
| Security | Can it handle sensitive data safely? |
| Effort | Is effort proportional to value? |

### Rules

- ✗ proceed to PoC with unresolved blocking unknowns.
- Acceptance criteria are specific and measurable — ✗ "works well" · ✗ "fast enough".
- Scope boundary is a contract. Additions require re-scoping.
- Time-box Idea phase. If feasibility unclear after 1 day → reject or escalate.

---

## 3. PoC Phase

Goal: Validate one specific technical hypothesis with minimum effort.
PoC code is throwaway. ✗ building features — only proving concept.

### PoC Contract

| Field | Requirement |
|---|---|
| Hypothesis | Single sentence: "We believe [X] because [Y]" |
| Success criteria | Binary: pass/fail conditions, no partial credit |
| Time-box | Fixed duration, agreed before starting |
| Scope | Narrowest possible — one question answered |
| Output | Written conclusion: confirmed / rejected / inconclusive + evidence |

### What PoC Is / Is Not

| PoC Is | PoC Is Not |
|---|---|
| Answering "can this work?" | Building features |
| Minimal throwaway code | Production-quality code |
| Testing one hypothesis | Exploring broadly |
| Time-boxed and disposable | Foundation for production |
| Evidence for a decision | Deliverable to users |

### Rules

- Time-box is sacred. When box expires → write conclusion with available evidence.
- PoC code lives in a separate branch or directory. ✗ PoC code in main branch.
- ✗ applying architecture standards to PoC code — speed matters, structure does not.
- PoC that proves concept → new MVP codebase. ✗ evolving PoC code into production.
- If hypothesis rejected → document why, kill project or re-scope at Idea phase.
- Multiple PoCs allowed for different hypotheses — run sequentially or in parallel.

---

## 4. MVP Phase

Goal: Build minimum feature set with production-quality code and
architecture applied. MVP is the first version users interact with.

### MVP Requirements

| Requirement | Detail |
|---|---|
| Architecture | Tier model applied per scale. See `architecture/STANDARDS.md` §2 |
| Core features only | Acceptance criteria from Idea phase — nothing more |
| Error handling | Errors as data, user-facing messages, no crashes |
| Testing | Core path tests, critical edge cases |
| Configuration | Sensible defaults, zero-config for default use case |
| Documentation | README with setup, usage, known limitations |

### MVP Boundaries

- Feature set = acceptance criteria from Idea phase. ✗ feature creep.
- "Minimum" means removing anything further breaks acceptance criteria.
- Quality is production-grade — MVP is not "rough draft with bugs".
- Performance optimization deferred unless acceptance criteria include performance targets.

### Rules

- Apply architecture standards from day one. See `architecture/STANDARDS.md`.
- Apply code writing standards. See `code_writing/STANDARDS.md`.
- Apply error handling standards. See `error_handling/STANDARDS.md`.
- ✗ shipping MVP without tests for core paths.
- ✗ deferring security for "later" — input validation and secrets handling from MVP.
- Technical debt incurred during MVP must be documented (see §9).
- MVP branch follows branching standards. See `git/STANDARDS.md`.

---

## 5. Production Phase

Goal: Full standards applied, operational readiness, monitoring, and
documentation complete. Production = users depend on it.

### Production Requirements

| Category | Requirements |
|---|---|
| Architecture | Full tier model, all dependency rules enforced |
| Testing | Full test pyramid: unit · integration · contract. See `testing/STANDARDS.md` |
| Error handling | Full error taxonomy, recovery strategies, circuit breakers. See `error_handling/STANDARDS.md` |
| Observability | Structured logging, health checks, metrics. See `observability/STANDARDS.md` |
| Security | Validation boundary, access control, secrets management. See `security/STANDARDS.md` |
| Configuration | Full cascade, environment separation. See `configuration/STANDARDS.md` |
| Documentation | API docs, runbooks, decision records. See `documentation/STANDARDS.md` |
| CI/CD | Automated build, test, lint, deploy pipeline. See `cicd/STANDARDS.md` |
| Performance | Budgets defined, profiling baseline captured. See `performance/STANDARDS.md` |

### Operational Readiness

Before declaring production-ready:

- Deployment is automated and repeatable.
- Rollback procedure exists and is tested.
- Monitoring alerts configured for critical failures.
- On-call or response process defined (even if solo developer).
- Data backup/recovery tested if applicable.
- Load/stress tested against expected usage patterns.

### Rules

- Every standard in the catalog applies at Production phase (see §11 for full matrix).
- ✗ "production" without monitoring — unmonitored systems are experiments.
- ✗ manual deployment as sole method — automation is required.
- Release process documented. See `cicd/STANDARDS.md`.
- Breaking changes follow evolution protocol. See `architecture/STANDARDS.md` §11.

---

## 6. Maintenance Phase

Goal: Sustain reliability, manage evolution, control entropy. Most of
a project's lifetime is maintenance. Treat it as first-class work.

### Maintenance Activities

| Activity | Cadence | Priority |
|---|---|---|
| Bug triage | On report | By severity (see table below) |
| Dependency updates | Weekly check, monthly apply | Medium |
| Security patches | On advisory | Critical — immediate |
| Feature requests | On request | Evaluated against roadmap |
| Tech debt repayment | Per sprint/cycle | Scheduled — see §9 |
| Performance review | Monthly | Medium |
| Documentation sync | On code change | Tied to PR/commit |

### Bug Severity Classification

| Severity | Definition | Response Time | Resolution Time |
|---|---|---|---|
| Critical | System down, data loss, security breach | Immediate | Hours |
| High | Major feature broken, workaround exists | Same day | 1–2 days |
| Medium | Minor feature broken, low impact | 1–2 days | 1 week |
| Low | Cosmetic, inconvenience, edge case | Next cycle | Best effort |

### Dependency Update Protocol

1. Check for updates weekly (automated where possible).
2. Read changelogs for breaking changes before updating.
3. Update in isolation — one dependency per commit.
4. Run full test suite after each update.
5. Pin exact versions in lock files. See `dependencies/STANDARDS.md`.

### Feature Request Evaluation

| Question | Reject If |
|---|---|
| Does it align with project scope? | No — out of scope |
| Does it benefit most users? | No — too niche |
| Is effort proportional to value? | No — cost exceeds benefit |
| Does it introduce architectural compromise? | Yes — maintain integrity |
| Can it be a separate module/plugin? | Yes — build it separately |

### Rules

- ✗ ignoring maintenance — entropy wins by default.
- Every bug report gets triaged and classified within response time.
- Dependency updates are proactive, not reactive to breakage.
- Feature requests follow evaluation criteria — ✗ accepting all requests.
- Retirement: when a project no longer serves its purpose → archive, document migration path, remove from active systems.

---

## 7. Phase Transition Criteria

Transition requires *all* criteria in the target column met. Partial → remain in current phase.

### Idea → PoC

| Criterion | Required |
|---|---|
| Problem statement written | Yes |
| Feasibility check complete (no blocking unknowns) | Yes |
| Scope boundary defined | Yes |
| PoC hypothesis formulated | Yes |
| Time-box agreed | Yes |

### PoC → MVP

| Criterion | Required |
|---|---|
| PoC hypothesis confirmed | Yes |
| Written conclusion with evidence | Yes |
| Acceptance criteria refined based on PoC findings | Yes |
| Scale classification confirmed | Yes |
| Architecture approach selected | Yes |
| ✗ PoC code carried forward | Enforced |

### MVP → Production

| Criterion | Required |
|---|---|
| All acceptance criteria met | Yes |
| Architecture standards applied | Yes |
| Core path tests passing | Yes |
| Error handling implemented | Yes |
| Security baseline met (input validation, secrets) | Yes |
| README with setup and usage | Yes |
| Tech debt documented | Yes |
| Code review completed | Yes |

### Production → Maintenance

| Criterion | Required |
|---|---|
| Full test pyramid in place | Yes |
| Monitoring and alerting configured | Yes |
| CI/CD pipeline operational | Yes |
| Operational runbook written | Yes |
| Rollback procedure tested | Yes |
| Performance baseline captured | Yes |
| All documentation current | Yes |

### Transition Rules

- Phase transition is an explicit decision, not a gradual drift.
- Document transition date and who approved it.
- Failed transition → list unmet criteria, create tasks to resolve, stay in current phase.
- Regression (Production → MVP quality) → halt new features, fix before continuing.

---

## 8. Task Management

### Task Decomposition

Every task follows: identify → decompose → estimate → execute → verify.

| Principle | Rule |
|---|---|
| Single responsibility | One task = one deliverable outcome |
| Size limit | Task completable in 1 day or less. Larger → decompose further |
| Independence | Tasks can be worked in any order where possible |
| Verifiability | Every task has a testable "done" condition |
| Traceability | Task links to parent goal/feature/bug |

### Definition of Done

A task is done when ALL of:

- Code written and compiles/runs without errors.
- Tests written and passing for new/changed behavior.
- Existing tests still passing (no regressions).
- Code reviewed (or self-reviewed for solo projects).
- Documentation updated if behavior changed.
- No new warnings introduced.
- Committed to appropriate branch with descriptive message.

### Priority Classification

| Priority | Definition | Action |
|---|---|---|
| P0 — Critical | System broken, data at risk | Drop everything, fix now |
| P1 — High | Major functionality impaired | Next task, before new features |
| P2 — Medium | Important but not urgent | Scheduled in current cycle |
| P3 — Low | Nice to have, minor improvement | Backlog, done when capacity allows |
| P4 — Wishlist | Speculative, future consideration | Tracked but not scheduled |

### Task Tracking Rules

- Every non-trivial task is tracked (issue tracker, TODO file, task board).
- Tasks have: title, description, priority, acceptance criteria, assignee.
- ✗ working on untracked tasks — invisible work creates invisible debt.
- Stale tasks (no activity 30+ days) → re-evaluate: still relevant? reprioritize or close.
- Tasks blocked 7+ days → escalate or re-scope.

---

## 9. Technical Debt

### Definition

Technical debt = gap between current implementation and what standards require.
Intentional debt (documented, time-boxed) is acceptable. Accidental debt
(undocumented, unplanned) is failure.

### Identification

| Debt Type | Example | Detection |
|---|---|---|
| Architecture debt | Missing tier separation, wrong dependency direction | Architecture review |
| Test debt | Missing tests, low coverage, flaky tests | Coverage reports, CI failures |
| Documentation debt | Outdated docs, missing runbooks | Doc review, onboarding friction |
| Dependency debt | Outdated libraries, unused dependencies | Dependency audit tools |
| Performance debt | Known slow paths, missing budgets | Profiling, monitoring |
| Security debt | Unvalidated inputs, hardcoded secrets | Security scans, code review |

### Tracking

Every debt item tracked with:

| Field | Content |
|---|---|
| Description | What is wrong and where |
| Impact | What breaks or degrades if not fixed |
| Effort | Estimated fix time (S/M/L/XL) |
| Phase incurred | When and why it was accepted |
| Repayment deadline | When it must be resolved |

### Repayment Rules

- Allocate 15–20% of each development cycle to debt repayment.
- ✗ ignoring debt indefinitely — debt with no repayment plan = negligence.
- Debt older than 3 cycles without progress → escalate to P1.
- New features ✗ if they increase debt in already-indebted areas.
- Every PR/commit that incurs debt must document it in tracking system.
- Debt repayment tasks follow same Definition of Done as feature tasks (§8).

---

## 10. AI-Assisted Development

Rules for using coding agents (LLM-based tools, copilots, code generators)
effectively within the workflow.

### Core Principle

AI generates — human verifies. AI output is a draft until validated
against standards. ✗ shipping unreviewed AI-generated code.

### Effective Usage

| Practice | Rule |
|---|---|
| Context management | Provide relevant files, standards, constraints upfront. More context → better output |
| Task scoping | One clear task per interaction. ✗ multi-goal prompts |
| Incremental generation | Request code in pieces, verify each. ✗ generating entire systems at once |
| Standards enforcement | Include relevant STANDARDS.md in context. AI follows rules it can see |
| Review rigor | AI-generated code gets same review as human code — no exceptions |

### Verification Requirements

Every AI-generated artifact must pass:

| Check | Method |
|---|---|
| Correctness | Tests pass, manual verification of logic |
| Standards compliance | Architecture, code writing, error handling standards met |
| Security | No hardcoded secrets, input validation present, no injection vectors |
| Dependencies | No unnecessary imports, no phantom packages |
| Completeness | All edge cases handled, error paths covered |
| Readability | Code comprehensible without AI context — future maintainer can follow |

### What AI Excels At / Struggles With

| AI Strengths — Leverage | AI Weaknesses — Verify Carefully |
|---|---|
| Boilerplate and repetitive patterns | Novel architecture decisions |
| Test generation from specifications | Security-critical logic |
| Refactoring well-defined transformations | Cross-module integration |
| Documentation drafts | Performance-sensitive paths |
| Code review and bug detection | Business rule correctness |
| Standards-compliant formatting | State management across boundaries |

### Rules

- AI-generated code must pass all CI checks before merge — no "AI wrote it" exemption.
- ✗ using AI to circumvent standards — AI is a tool, standards are rules.
- Document when AI generated significant portions (decision record, commit message).
- When AI output conflicts with standards → standards win. Fix or reject.
- AI hallucinations (non-existent APIs, phantom dependencies) → verify every import, every function call.
- Context window limits → provide focused context, not entire codebase.

---

## 11. Standards Application by Phase

Which standards apply at each development phase. "Full" = all rules apply.
"Partial" = core rules apply, advanced rules deferred. "—" = not applicable.

| Standard | Idea | PoC | MVP | Production | Maintenance |
|---|---|---|---|---|---|
| `architecture/` | Scale classification | — | Full tier model | Full | Full |
| `design/` | — | — | Core patterns | Full | Full |
| `directory/` | — | — | Project layout | Full | Full |
| `code_writing/` | — | — | Full | Full | Full |
| `testing/` | — | — | Core paths | Full pyramid | Full pyramid |
| `error_handling/` | — | — | Errors as data | Full taxonomy | Full |
| `observability/` | — | — | Basic logging | Full (logs · metrics · health) | Full |
| `security/` | Threat assessment | — | Input validation · secrets | Full | Full |
| `api/` | — | — | Contract-first | Full | Full |
| `database/` | — | — | Schema design · migrations | Full | Full |
| `configuration/` | — | — | Defaults + file | Full cascade | Full |
| `dependencies/` | — | — | Lock files · pinning | Full wrapping | Full |
| `git/` | — | Branch per PoC | Branching model | Full workflow | Full |
| `cicd/` | — | — | Build + test | Full pipeline | Full |
| `documentation/` | Problem statement | PoC conclusion | README + setup | Full (API · runbooks · ADRs) | Kept current |
| `performance/` | — | — | — | Budgets · profiling | Monitored |
| `devops/` | — | — | — | Full (containers · deploy · monitor) | Full |
| `code_review/` | — | — | Self-review minimum | Full review flow | Full |
| `workflow/` | Full | Full | Full | Full | Full |

### Rules

- PoC intentionally skips most standards — speed over structure.
- MVP is where architecture standards become mandatory.
- ✗ deferring security past MVP — vulnerabilities compound.
- Production requires *every* standard applied. Gaps = tech debt (§9).
- Maintenance inherits all Production standards + keeps them current.

---

## 12. Decision Records

Lightweight decision records for significant technical choices.
Full ADR format in `documentation/STANDARDS.md`. This section defines
*when* and *what* to record.

### When to Record

| Trigger | Example |
|---|---|
| Technology choice | Language, framework, database, cloud provider |
| Architecture choice | Tier structure, communication pattern, data flow |
| Trade-off accepted | Performance vs readability, scope vs deadline |
| Rejected alternative | Why option B was rejected in favor of option A |
| Standard deviation | Any intentional deviation from these standards |
| Dependency adoption | Adding significant external dependency |

### Record Format (Lightweight)

```
Title: [Short descriptive title]
Date: [YYYY-MM-DD]
Phase: [Idea | PoC | MVP | Production | Maintenance]
Status: [Proposed | Accepted | Deprecated | Superseded by DR-XXX]

Context: [1-2 sentences — what situation prompted decision]
Decision: [1-2 sentences — what was decided]
Alternatives: [Bullet list — what was considered and rejected]
Consequences: [Bullet list — known trade-offs and impacts]
```

### Rules

- Decisions are immutable once accepted. New decisions supersede old ones.
- Store decision records in project repository (e.g., `docs/decisions/`).
- Number sequentially: `DR-001`, `DR-002`, etc.
- ✗ retroactive decision records for unjustified choices — record at decision time.
- Review decision records during phase transitions — still valid?
- PoC decisions are informal (commit message sufficient). MVP+ decisions are formal records.

---

## 13. Scale Matrix

Maps workflow rigor to project scale. Aligns with `architecture/STANDARDS.md` §12.

| Workflow Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Idea phase | Mental model, quick notes | Written problem statement | Full artifacts (§2) |
| PoC phase | Optional — concept may be obvious | Single hypothesis | Multiple hypotheses if needed |
| MVP phase | Skip — PoC is the deliverable | Core features + tests | Full acceptance criteria |
| Task tracking | Personal notes | Issue tracker or TODO file | Full task board + priority |
| Definition of done | "It works" | Code + tests + docs | Full DoD (§8) |
| Technical debt | Accept freely | Track, repay when painful | 15–20% cycle allocation |
| Decision records | Commit messages | Lightweight per above | Full ADR format |
| Code review | Self-review | Self-review + occasional peer | Mandatory peer review |
| AI verification | Quick sanity check | Standards compliance check | Full verification matrix (§10) |
| Phase transitions | Implicit | Explicit but lightweight | Formal criteria (§7) |
| Maintenance | Fix if broken | Periodic dependency updates | Full maintenance cadence (§6) |

### Scale Transition

When project graduates from one scale to next (per `architecture/STANDARDS.md` §12):

1. Identify current gaps against target scale requirements.
2. Create tasks for each gap (tracked per §8).
3. Apply incrementally using Strangler Fig pattern — ✗ big-bang rewrites.
4. Declare transition complete when all target criteria met.

---

## 14. Checklists

### Idea Phase Checklist

- [ ] Problem statement written (who, what, impact)
- [ ] Feasibility check completed (all dimensions evaluated)
- [ ] Scope boundary defined (in-scope and out-of-scope explicit)
- [ ] Acceptance criteria defined (measurable, specific)
- [ ] Scale classified (PoC / Small / Production)
- [ ] Decision: proceed to PoC, proceed to MVP, or reject

### PoC Phase Checklist

- [ ] Hypothesis documented (single sentence)
- [ ] Success criteria defined (binary pass/fail)
- [ ] Time-box set and agreed
- [ ] PoC code in separate branch/directory
- [ ] Conclusion written (confirmed / rejected / inconclusive + evidence)
- [ ] Decision: proceed to MVP, re-scope, or kill

### MVP Phase Checklist

- [ ] Architecture standards applied per scale
- [ ] All acceptance criteria implemented
- [ ] Core path tests written and passing
- [ ] Error handling implemented (errors as data)
- [ ] Input validation and secrets handling in place
- [ ] Configuration defaults work (zero-config runs)
- [ ] README with setup, usage, known limitations
- [ ] Technical debt documented
- [ ] Code reviewed
- [ ] Decision: proceed to Production or iterate

### Production Phase Checklist

- [ ] Full test pyramid (unit · integration · contract)
- [ ] Observability (structured logging · health checks · metrics)
- [ ] Security standards applied (validation · access control · secrets)
- [ ] CI/CD pipeline operational (build · test · lint · deploy)
- [ ] Performance budgets defined and baselined
- [ ] Full documentation (API docs · runbooks · decision records)
- [ ] Deployment automated and repeatable
- [ ] Rollback procedure tested
- [ ] Monitoring and alerting configured
- [ ] Operational readiness review completed

### Maintenance Phase Checklist (Recurring)

- [ ] Bug triage current (no unclassified reports)
- [ ] Dependencies checked this cycle
- [ ] Security advisories reviewed
- [ ] Tech debt repayment tasks scheduled (15–20% allocation)
- [ ] Documentation matches current code
- [ ] Performance within budgets
- [ ] Monitoring and alerts functional
- [ ] Stale tasks reviewed and closed/reprioritized
- [ ] Decision records reviewed — still valid?

### AI-Assisted Development Checklist

- [ ] Relevant standards provided in AI context
- [ ] Task scoped to single clear objective
- [ ] Generated code reviewed for correctness
- [ ] Standards compliance verified
- [ ] Security checked (no secrets, input validation present)
- [ ] Dependencies verified (no phantom packages)
- [ ] Tests pass (existing + new)
- [ ] Code readable without AI context
