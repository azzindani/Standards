# Development Workflow Standards

> The idea-to-production lifecycle: phase gates, task management, technical debt, and AI-assisted development — *when* each standard applies, not *how* each works.

**ID** `workflow` · **Tier** Delivery · **Version** 1.0
**Owns** development lifecycle (idea → PoC → MVP → production → maintenance) · phase transition criteria · task decomposition + management · technical-debt tracking + repayment · AI-assisted development workflow · standards-application-by-phase mapping · lifecycle decision-record timing
**Defers to** project-type + surface routing → [ROUTER](../ROUTER.md) · full ADR format → [documentation](../documentation/STANDARDS.md) · branching per phase → [git](../git/STANDARDS.md) · scale definitions + tier model → [architecture](../architecture/STANDARDS.md) · per-domain rules → each standard's own `Owns`
**Load with** [architecture](../architecture/STANDARDS.md) · [git](../git/STANDARDS.md) · [documentation](../documentation/STANDARDS.md) · [ROUTER](../ROUTER.md)

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
14. [Checklist](#14-checklist)

---

## 1. Development Lifecycle

Five sequential phases: **Idea → PoC → MVP → Production → Maintenance**. Every project enters at Idea. PoC skippable if concept proven. ✗ skip Idea — undirected work produces waste.

| Phase | Focus | Exit Output |
|---|---|---|
| Idea | Problem statement · feasibility · scope · acceptance criteria | Go / no-go decision |
| PoC | Throwaway-ok · time-boxed · validates one hypothesis | Confirmed / rejected + evidence |
| MVP | Architecture applied · production-quality code | First user-facing version |
| Production | Full standards · monitoring · ops readiness | Live service |
| Maintenance | Sustain · evolve · retire | Ongoing reliability |

Phase applies at every scale — scale determines rigor (§13), not whether phases apply. Project routing by type/surface → [ROUTER](../ROUTER.md).

### Duration Expectations

| Phase | Typical | Hard Time-Box |
|---|---|---|
| Idea | 1–4 hours | 1 day |
| PoC | 1–3 days | 1 week |
| MVP | 1–4 weeks | Scope-dependent |
| Production | Ongoing | Release cadence |
| Maintenance | Ongoing | Until retirement |

- Each phase produces explicit artifacts before advancing. Transitions require criteria met (§7).
- Work without a defined phase = untracked work. ✗ untracked work. Document current phase in README or tracker.

---

## 2. Idea Phase

Define *what* problem exists, *whether* solving it is feasible, *what* success looks like. ✗ writing code in Idea phase.

### Required Artifacts

| Artifact | Content |
|---|---|
| Problem statement | One paragraph: who has the problem, what it is, impact of not solving |
| Feasibility check | Technical constraints, dependencies, unknowns, risks |
| Scope boundary | In scope · explicitly out of scope |
| Acceptance criteria | Measurable conditions defining "done" for MVP |
| Scale classification | PoC / Small / Production per [architecture](../architecture/STANDARDS.md) §12 |

### Feasibility Check

Evaluate before committing resources: **Technical** (buildable with known tools?) · **Data** (available + accessible?) · **Integration** (required APIs exist + allow access?) · **Performance** (meets latency/throughput?) · **Security** (handles sensitive data safely?) · **Effort** (proportional to value?).

### Rules

- ✗ proceed to PoC with unresolved blocking unknowns.
- Acceptance criteria specific + measurable — ✗ "works well" · ✗ "fast enough".
- Scope boundary is a contract. Additions require re-scoping.
- Time-box Idea. Feasibility unclear after 1 day → reject or escalate.

---

## 3. PoC Phase

Validate one specific technical hypothesis with minimum effort. PoC code is throwaway. ✗ building features — only proving concept.

### PoC Contract

| Field | Requirement |
|---|---|
| Hypothesis | Single sentence: "We believe [X] because [Y]" |
| Success criteria | Binary pass/fail, no partial credit |
| Time-box | Fixed duration, agreed before starting |
| Scope | Narrowest possible — one question answered |
| Output | Written conclusion: confirmed / rejected / inconclusive + evidence |

### Rules

- Time-box is sacred. Box expires → write conclusion with available evidence.
- PoC code lives in separate branch/directory. ✗ PoC code in `main`. Branch per PoC ([git](../git/STANDARDS.md)).
- ✗ applying architecture standards to PoC — speed matters, structure does not.
- PoC proves concept → new MVP codebase. ✗ evolving PoC code into production.
- Hypothesis rejected → document why, kill or re-scope at Idea. Multiple PoCs allowed (sequential or parallel).

---

## 4. MVP Phase

Build minimum feature set with production-quality code and architecture applied. MVP is the first version users interact with.

### MVP Requirements

| Requirement | Detail |
|---|---|
| Architecture | Tier model applied per scale ([architecture](../architecture/STANDARDS.md) §2) |
| Core features only | Acceptance criteria from Idea — nothing more |
| Error handling | Errors as data, user-facing messages, no crashes ([error_handling](../error_handling/STANDARDS.md)) |
| Testing | Core-path tests, critical edge cases ([testing](../testing/STANDARDS.md)) |
| Configuration | Sensible defaults, zero-config for default use case |
| Documentation | README with setup, usage, known limitations |

### Rules

- "Minimum" = removing anything further breaks acceptance criteria. ✗ feature creep.
- Quality is production-grade — MVP is not "rough draft with bugs". Performance optimization deferred unless acceptance criteria include performance targets.
- Apply architecture, code_writing, error_handling standards from day one.
- ✗ shipping MVP without tests for core paths. ✗ deferring security — input validation + secrets from MVP.
- Technical debt incurred during MVP documented (§9). MVP branch follows [git](../git/STANDARDS.md).

---

## 5. Production Phase

Full standards applied, operational readiness, monitoring, documentation complete. Production = users depend on it.

### Production Requirements

| Category | Requirement |
|---|---|
| Architecture | Full tier model, all dependency rules enforced |
| Testing | Full pyramid: unit · integration · contract ([testing](../testing/STANDARDS.md)) |
| Error handling | Full taxonomy, recovery strategies, circuit breakers ([error_handling](../error_handling/STANDARDS.md)) |
| Observability | Structured logging, health checks, metrics ([observability](../observability/STANDARDS.md)) |
| Security | Validation boundary, access control, secrets ([security](../security/STANDARDS.md)) |
| Configuration | Full cascade, environment separation ([configuration](../configuration/STANDARDS.md)) |
| Documentation | API docs, runbooks, decision records ([documentation](../documentation/STANDARDS.md)) |
| CI/CD | Automated build, test, lint, deploy pipeline ([cicd](../cicd/STANDARDS.md)) |
| DevOps | Containers, deploy, monitoring, on-call, backup/DR ([devops](../devops/STANDARDS.md)) |
| Performance | Budgets defined, profiling baseline captured ([performance](../performance/STANDARDS.md)) |

### Operational Readiness

Before declaring production-ready: deployment automated + repeatable · rollback procedure tested · monitoring alerts configured for critical failures · on-call/response process defined (even if solo) · backup/recovery tested if applicable · load/stress tested against expected usage.

### Rules

- Every catalog standard applies at Production (§11 for full matrix).
- ✗ "production" without monitoring — unmonitored systems are experiments. ✗ manual deployment as sole method.
- Breaking changes follow evolution protocol ([architecture](../architecture/STANDARDS.md) §11).

---

## 6. Maintenance Phase

Sustain reliability, manage evolution, control entropy. Most of a project's lifetime is maintenance — first-class work.

### Activities & Cadence

| Activity | Cadence | Priority |
|---|---|---|
| Bug triage | On report | By severity (below) |
| Dependency updates | Weekly check, monthly apply | Medium |
| Security patches | On advisory | Critical — immediate |
| Feature requests | On request | Evaluated against roadmap |
| Tech debt repayment | Per sprint/cycle | Scheduled (§9) |
| Documentation sync | On code change | Tied to PR/commit |

### Bug Severity

| Severity | Definition | Response | Resolution |
|---|---|---|---|
| Critical | System down, data loss, security breach | Immediate | Hours |
| High | Major feature broken, workaround exists | Same day | 1–2 days |
| Medium | Minor feature broken, low impact | 1–2 days | 1 week |
| Low | Cosmetic, inconvenience, edge case | Next cycle | Best effort |

### Rules

- Dependency update protocol: check weekly → read changelogs for breaking changes → update in isolation (one per commit) → run full suite → pin exact versions ([dependencies](../dependencies/STANDARDS.md)).
- Feature request rejected if: out of scope · too niche · cost exceeds value · introduces architectural compromise · better as a separate module.
- ✗ ignoring maintenance — entropy wins by default. Every bug triaged + classified within response time.
- Retirement: project no longer serves purpose → archive, document migration path, remove from active systems.

---

## 7. Phase Transition Criteria

Transition requires *all* criteria met. Partial → remain in current phase.

| Transition | Required (all) |
|---|---|
| Idea → PoC | Problem statement · feasibility complete (no blocking unknowns) · scope defined · hypothesis formulated · time-box agreed |
| PoC → MVP | Hypothesis confirmed · written conclusion + evidence · acceptance criteria refined · scale confirmed · architecture approach selected · ✗ PoC code carried forward |
| MVP → Production | All acceptance criteria met · architecture standards applied · core-path tests passing · error handling implemented · security baseline (validation + secrets) · README · tech debt documented · code review completed |
| Production → Maintenance | Full pyramid in place · monitoring + alerting configured · CI/CD operational · runbook written · rollback tested · performance baseline captured · documentation current |

### Transition Rules

- Phase transition is an explicit decision, ✗ gradual drift. Document transition date + who approved.
- Failed transition → list unmet criteria, create tasks, stay in current phase.
- Regression (Production → MVP quality) → halt new features, fix before continuing.

---

## 8. Task Management

Every task follows: identify → decompose → estimate → execute → verify.

| Principle | Rule |
|---|---|
| Single responsibility | One task = one deliverable outcome |
| Size limit | Completable in ≤ 1 day. Larger → decompose |
| Independence | Workable in any order where possible |
| Verifiability | Testable "done" condition |
| Traceability | Links to parent goal/feature/bug |

### Definition of Done

Done = ALL of: code compiles/runs · tests written + passing for new/changed behavior · existing tests still pass · code reviewed (or self-reviewed for solo) · docs updated if behavior changed · no new warnings · committed with descriptive message.

### Priority

| Priority | Definition | Action |
|---|---|---|
| P0 — Critical | System broken, data at risk | Drop everything, fix now |
| P1 — High | Major functionality impaired | Next task, before new features |
| P2 — Medium | Important, not urgent | Scheduled in current cycle |
| P3 — Low | Nice to have | Backlog, when capacity allows |
| P4 — Wishlist | Speculative | Tracked, not scheduled |

- Every non-trivial task tracked (issue tracker, TODO, board): title, description, priority, acceptance criteria, assignee.
- ✗ working on untracked tasks — invisible work creates invisible debt.
- Stale tasks (no activity 30+ days) → re-evaluate. Blocked 7+ days → escalate or re-scope.

---

## 9. Technical Debt

Technical debt = gap between current implementation and what standards require. Intentional debt (documented, time-boxed) acceptable. Accidental debt (undocumented, unplanned) is failure.

### Types & Detection

| Debt Type | Detection |
|---|---|
| Architecture (missing tier separation, wrong dependency direction) | Architecture review |
| Test (missing tests, low coverage, flaky) | Coverage reports, CI |
| Documentation (outdated, missing runbooks) | Doc review, onboarding friction |
| Dependency (outdated, unused libraries) | Dependency audit |
| Performance (known slow paths, missing budgets) | Profiling, monitoring |
| Security (unvalidated inputs, hardcoded secrets) | Security scans, review |

Every debt item tracked with: description (what + where) · impact (what breaks if unfixed) · effort (S/M/L/XL) · phase incurred · repayment deadline.

### Repayment Rules

- Allocate 15–20% of each cycle to debt repayment.
- ✗ ignoring debt indefinitely — debt with no repayment plan = negligence.
- Debt older than 3 cycles without progress → escalate to P1.
- New features ✗ if they increase debt in already-indebted areas.
- Every PR/commit incurring debt documents it. Repayment tasks follow the same Definition of Done (§8).

---

## 10. AI-Assisted Development

AI generates — human verifies. AI output is a draft until validated against standards. ✗ shipping unreviewed AI-generated code.

### Effective Usage

| Practice | Rule |
|---|---|
| Context management | Provide relevant files, standards, constraints upfront |
| Task scoping | One clear task per interaction. ✗ multi-goal prompts |
| Incremental generation | Request code in pieces, verify each. ✗ generating whole systems at once |
| Standards enforcement | Include relevant STANDARDS.md in context — AI follows rules it can see |
| Review rigor | AI-generated code gets the same review as human code — no exceptions |

### Verification (every AI artifact)

Correctness (tests pass, logic verified) · standards compliance (architecture, code_writing, error_handling) · security (no hardcoded secrets, input validation, no injection) · dependencies (no phantom packages) · completeness (edge cases + error paths) · readability (comprehensible without AI context).

### Strengths vs Weaknesses

| Leverage | Verify Carefully |
|---|---|
| Boilerplate, repetitive patterns | Novel architecture decisions |
| Test generation from specs | Security-critical logic |
| Well-defined refactors | Cross-module integration |
| Documentation drafts | Performance-sensitive paths |
| Code review + bug detection | Business rule correctness |

### Rules

- AI-generated code passes all CI checks before merge — no "AI wrote it" exemption.
- ✗ using AI to circumvent standards. AI output conflicts with standards → standards win.
- Document when AI generated significant portions (decision record or commit message).
- AI hallucinations (non-existent APIs, phantom deps) → verify every import, every call. Provide focused context, not the entire codebase.

---

## 11. Standards Application by Phase

Which standards apply at each phase. "Full" = all rules. "Partial" = core rules, advanced deferred. "—" = not applicable. Routing by project type/surface → [ROUTER](../ROUTER.md); this maps by lifecycle phase.

| Standard | Idea | PoC | MVP | Production | Maintenance |
|---|---|---|---|---|---|
| `architecture` | Scale classification | — | Full tier model | Full | Full |
| `design` · `directory` | — | — | Core / layout | Full | Full |
| `code_writing` | — | — | Full | Full | Full |
| `testing` | — | — | Core paths | Full pyramid | Full pyramid |
| `error_handling` | — | — | Errors as data | Full taxonomy | Full |
| `observability` | — | — | Basic logging | Full (logs · metrics · health) | Full |
| `security` | Threat assessment | — | Validation · secrets | Full | Full |
| `api` · `database` | — | — | Contract / schema | Full | Full |
| `configuration` | — | — | Defaults + file | Full cascade | Full |
| `dependencies` | — | — | Lock files · pinning | Full wrapping | Full |
| `git` | — | Branch per PoC | Branching model | Full workflow | Full |
| `cicd` | — | — | Build + test | Full pipeline | Full |
| `documentation` | Problem statement | PoC conclusion | README + setup | Full (API · runbooks · ADRs) | Kept current |
| `performance` | — | — | — | Budgets · profiling | Monitored |
| `devops` | — | — | — | Full (containers · deploy · monitor · on-call) | Full |
| `code_review` | — | — | Self-review minimum | Full review flow | Full |
| `workflow` | Full | Full | Full | Full | Full |

- PoC intentionally skips most standards — speed over structure. MVP is where architecture standards become mandatory.
- ✗ deferring security past MVP — vulnerabilities compound. Production requires *every* standard; gaps = tech debt (§9).

---

## 12. Decision Records

Lightweight records for significant technical choices. Full ADR format → [documentation](../documentation/STANDARDS.md). This section defines *when* + *what* to record.

### When to Record

Technology choice (language, framework, DB, cloud) · architecture choice (tier structure, communication pattern, data flow) · trade-off accepted · rejected alternative · standard deviation · significant dependency adoption.

### Record Format (Lightweight)

| Field | Content |
|---|---|
| Title | Short descriptive title |
| Date | YYYY-MM-DD |
| Phase | Idea / PoC / MVP / Production / Maintenance |
| Status | Proposed / Accepted / Deprecated / Superseded by DR-XXX |
| Context | 1–2 sentences: situation prompting the decision |
| Decision | 1–2 sentences: what was decided |
| Alternatives | Bullets: considered + rejected |
| Consequences | Bullets: known trade-offs + impacts |

### Rules

- Decisions immutable once accepted. New decisions supersede old ones.
- Store in repo (`docs/decisions/`), numbered sequentially: `DR-001`, `DR-002`.
- ✗ retroactive records for unjustified choices — record at decision time. Review during phase transitions — still valid?
- PoC decisions informal (commit message). MVP+ decisions are formal records.

---

## 13. Scale Matrix

Workflow rigor by scale. Aligns with [architecture](../architecture/STANDARDS.md) §12.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Idea phase | Mental model, quick notes | Written problem statement | Full artifacts (§2) |
| PoC phase | Optional — concept may be obvious | Single hypothesis | Multiple hypotheses if needed |
| MVP phase | Skip — PoC is the deliverable | Core features + tests | Full acceptance criteria |
| Task tracking | Personal notes | Issue tracker or TODO | Full board + priority |
| Definition of done | "It works" | Code + tests + docs | Full DoD (§8) |
| Technical debt | Accept freely | Track, repay when painful | 15–20% cycle allocation |
| Decision records | Commit messages | Lightweight per §12 | Full ADR format |
| Code review | Self-review | Self + occasional peer | Mandatory peer review |
| AI verification | Quick sanity check | Standards compliance check | Full verification matrix (§10) |
| Phase transitions | Implicit | Explicit but lightweight | Formal criteria (§7) |
| Maintenance | Fix if broken | Periodic dependency updates | Full cadence (§6) |

Scale transition (per [architecture](../architecture/STANDARDS.md) §12): identify gaps → create tasks (§8) → apply incrementally via strangler fig, ✗ big-bang rewrites → declare complete when all target criteria met.

---

## 14. Checklist

### Phase Gates

- [ ] Current phase documented in README or tracker
- [ ] Idea: problem statement · feasibility · scope · measurable acceptance criteria · scale classified
- [ ] PoC: hypothesis + binary success criteria + time-box; code in separate branch/directory; written conclusion
- [ ] PoC code ✗ carried into MVP — new codebase
- [ ] MVP: architecture applied · core-path tests · error handling · input validation + secrets · README · debt documented
- [ ] Production: full pyramid · observability · security · CI/CD · devops · performance budgets · rollback tested · monitoring configured
- [ ] Every phase transition is an explicit, dated, approved decision (§7)

### Task & Debt

- [ ] Every non-trivial task tracked with priority + acceptance criteria (§8)
- [ ] Definition of Done met before a task is closed (§8)
- [ ] Technical debt tracked with impact, effort, repayment deadline (§9)
- [ ] 15–20% of each cycle allocated to debt repayment (§9)
- [ ] No new feature increases debt in an already-indebted area (§9)

### AI-Assisted

- [ ] Relevant standards provided in AI context; task scoped to one objective (§10)
- [ ] AI output reviewed for correctness, standards compliance, security (§10)
- [ ] Every import + dependency verified (no phantom packages) (§10)
- [ ] AI-generated code passes all CI checks before merge (§10)

### Records & Maintenance

- [ ] Decision records created at decision time for significant choices (§12)
- [ ] MVP+ decisions in formal records, numbered sequentially (§12)
- [ ] Maintenance cadence active: bug triage · dependency updates · security advisories (§6)
- [ ] Documentation matches current code (§6)
