# Code Review Standards

> How code changes are reviewed: what to check, how to communicate, when to approve — the review process itself, not how code is written or committed.

**ID** `code_review` · **Tier** Delivery · **Version** 1.0
**Owns** review criteria + priority order · PR size limits · feedback style · comment-type taxonomy · approval flow + required-approver counts · review-speed SLAs · disagreement escalation · AI-assisted review policy
**Defers to** commit format + branching + history + PR merge mechanics → [git](../git/STANDARDS.md) · test-coverage adequacy → [testing](../testing/STANDARDS.md) · security review criteria + threat model → [security](../security/STANDARDS.md) · tier boundaries + dependency direction → [architecture](../architecture/STANDARDS.md) · readability + naming + function size → [code_writing](../code_writing/STANDARDS.md) · CI gates + pipeline → [cicd](../cicd/STANDARDS.md) · API contract + versioning → [api](../api/STANDARDS.md)
**Load with** [git](../git/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md) · [testing](../testing/STANDARDS.md) · [cicd](../cicd/STANDARDS.md)

---

## Table of Contents

1. [Review Philosophy](#1-review-philosophy)
2. [PR Size](#2-pr-size)
3. [Review Criteria](#3-review-criteria)
4. [Review Checklist](#4-review-checklist)
5. [Feedback Style](#5-feedback-style)
6. [Comment Types](#6-comment-types)
7. [Approval Flow](#7-approval-flow)
8. [Review Speed](#8-review-speed)
9. [Automated Checks](#9-automated-checks)
10. [Review Scope](#10-review-scope)
11. [Handling Disagreements](#11-handling-disagreements)
12. [AI-Assisted Review](#12-ai-assisted-review)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Review Philosophy

| Principle | Rule |
|---|---|
| Review code, not people | Comments address the change, never the author's skill or character |
| Correctness first | Does it do what it claims? All other criteria secondary |
| Clarity second | Can the next person understand this without asking the author? |
| Shared ownership | Reviewer shares responsibility for merged code — review as if you'll maintain it |
| Teaching opportunity | Reviews transfer knowledge; prefer explanations over directives |
| Bias to action | If two approaches are roughly equal, approve the author's choice |
| ✗ Gatekeeping | Reviews unblock progress. ✗ use reviews to impose personal style preferences |
| ✗ Rubber-stamping | Every approval = reviewer verified correctness · readability · test coverage |
| Approve on net improvement | Approve when the change **definitely improves overall code health**, even if imperfect. ✗ withhold approval pending unrelated polish |
| Incremental improvement | Code need not be perfect — it must be better than before. Perfection is not the merge bar |
| Timely response | Pending reviews block teammates. Respond within 1 business day; treat requests as high-priority interrupts |

---

## 2. PR Size

Owner of PR size across the repo — `git` PR mechanics defer here for size + reviewer counts. Small PRs review faster, review better; target the ~200-line sweet spot, ceiling ≤ 400.

| Metric | Target | Hard Limit | Notes |
|---|---|---|---|
| Lines changed (added + modified) | ≤ 400 (aim ~200) | 800 | Excludes generated files, lock files, migrations |
| Files changed | ≤ 10 | 20 | Excludes test fixtures, snapshots |
| Commits per PR | 1–5 | 10 | Each commit = logical unit |
| Review time per PR | 15–30 min | 60 min | If longer → PR too large |

**Split rules:**

| Situation | Required Action |
|---|---|
| PR exceeds 800 lines changed | Split before review. ✗ exceptions without tech lead approval |
| Refactor + feature in same PR | Split into refactor PR (merged first) + feature PR |
| Large migration or rename | Separate PR; mechanical changes reviewed differently than logic |
| New module + integration | Module PR first → integration PR second |
| Test backfill + new feature | Test backfill PR first → feature PR second |

**Allowed exceptions (must document in PR description):**

- Generated code (protobuf, OpenAPI, schema-derived)
- Dependency lock file updates
- Large-scale automated refactors (rename, reformatting)
- Database migrations with no logic changes

---

## 3. Review Criteria

Ordered by priority — reviewer checks top-to-bottom, stops at first critical failure.

| Priority | Criterion | Question to Answer | Cross-Reference |
|---|---|---|---|
| P0 | Correctness | Does the code do what the PR description claims? | — |
| P0 | Security | Any injection, auth bypass, secret exposure, unsafe input? | `security/STANDARDS.md` |
| P1 | Architecture compliance | Does it respect tier boundaries, dependency direction, module ownership? | `architecture/STANDARDS.md` |
| P1 | Error handling | Are errors caught, typed, propagated correctly? Silent swallowing? | `error_handling/STANDARDS.md` |
| P1 | Test coverage | Are new paths tested? Changed paths re-tested? Edge cases covered? | `testing/STANDARDS.md` |
| P2 | Readability | Clear names, small functions, obvious flow, minimal nesting? | `code_writing/STANDARDS.md` |
| P2 | Performance | Obvious N+1, unbounded allocations, missing pagination, hot-path allocations? | `performance/STANDARDS.md` |
| P3 | API contract | Breaking changes documented? Versioning correct? Schema valid? | `api/STANDARDS.md` |
| P3 | Observability | Structured logging at boundaries? Metrics for new operations? | `observability/STANDARDS.md` |
| P4 | Style consistency | Matches project conventions? Linter-clean? | `code_writing/STANDARDS.md` |
| P4 | Documentation | Public APIs documented? Decision records for non-obvious choices? | `documentation/STANDARDS.md` |

P0 = blocks merge, always. P1 = blocks merge unless justified. P2–P4 = non-blocking suggestions unless pattern is pervasive.

---

## 4. Review Checklist

Per-review checklist mapped to standards. Reviewer verifies each row against the diff.

| # | Check | Verify | Standard |
|---|---|---|---|
| 1 | PR description matches actual changes | Diff aligns with stated intent; no undocumented behavioral changes | `git/STANDARDS.md` |
| 2 | No secrets or credentials in diff | ✗ API keys · tokens · passwords · private keys in code or config | `security/STANDARDS.md` |
| 3 | Input validation at trust boundaries | All external input validated/sanitized before use | `security/STANDARDS.md` |
| 4 | Error paths handled | No silent swallowing · errors typed · propagation correct · user-facing messages clear | `error_handling/STANDARDS.md` |
| 5 | Tests exist for new behavior | New code paths have tests · changed behavior has updated tests | `testing/STANDARDS.md` |
| 6 | Tests pass (CI green) | All automated checks pass before human review begins | `cicd/STANDARDS.md` |
| 7 | Dependency direction respected | No upward/lateral imports violating tier model | `architecture/STANDARDS.md` §3 |
| 8 | No state leakage | Module state stays within module boundary · no global mutation | `architecture/STANDARDS.md` §6 |
| 9 | Function size and complexity | Functions ≤ 40 lines · single responsibility · max 3 nesting levels | `code_writing/STANDARDS.md` |
| 10 | Naming clarity | Names reveal intent · no abbreviations except well-known domain terms | `code_writing/STANDARDS.md` |
| 11 | No dead code added | ✗ commented-out code · ✗ unused imports · ✗ unreachable branches | `code_writing/STANDARDS.md` |
| 12 | Breaking API changes flagged | Version bumped · migration path documented · deprecation warnings added | `api/STANDARDS.md` |
| 13 | Database changes safe | Migrations reversible · no locking writes on large tables · schema documented | `database/STANDARDS.md` |
| 14 | Logging at boundaries | Operations log entry/exit with structured context · no sensitive data in logs | `observability/STANDARDS.md` |
| 15 | Configuration externalized | ✗ hardcoded environment-specific values · config follows cascade | `configuration/STANDARDS.md` |

---

## 5. Feedback Style

| Rule | Detail |
|---|---|
| Be specific | Reference exact line, variable, or function. ✗ "this looks wrong" |
| Be actionable | State what to change and why. ✗ "fix this" without direction |
| Suggest alternatives | When rejecting an approach, propose at least one concrete alternative |
| Explain the principle | Link feedback to a standard or principle, not personal preference |
| One concern per comment | Each comment addresses one issue. ✗ compound comments mixing multiple problems |
| Use questions for ambiguity | "Is this intentional?" preferred over "This is wrong" when unsure |
| Acknowledge good work | Highlight clean patterns, clever solutions, thorough tests |
| ✗ Sarcasm or condescension | Tone is professional, constructive, direct |
| ✗ "You" language for problems | "This function mutates state" not "You wrote a function that mutates state" |
| Scope feedback to the diff | ✗ requesting pre-existing code changes unrelated to the PR |

**Comment structure (recommended):**

`[Type] Observation → Impact → Suggestion`

- **Observation**: What the reviewer sees in the diff
- **Impact**: What problem it causes or risk it creates
- **Suggestion**: Specific action to resolve

---

## 6. Comment Types

Every review comment carries a type prefix. This eliminates ambiguity about whether a comment blocks merge.

| Type | Prefix | Blocks Merge | Meaning |
|---|---|---|---|
| Blocking | `[blocking]` | Yes | Must fix before merge. Correctness, security, or architectural violation |
| Non-blocking | `[nit]` or `[suggestion]` | No | Improvement idea. Author decides whether to adopt |
| Question | `[question]` | Maybe | Reviewer needs clarification. Blocks if answer reveals a defect |
| Praise | `[praise]` | No | Positive reinforcement of good pattern or approach |
| Future | `[future]` | No | Worth addressing in a follow-up PR, not this one |
| FYI | `[fyi]` | No | Context for the author — related info, upcoming changes, gotchas |

**Rules for type usage:**

| Rule | Detail |
|---|---|
| Every comment has a type prefix | ✗ ambiguous comments without classification |
| Blocking requires justification | State which standard or principle is violated |
| Blocking count threshold | > 5 blocking comments → likely PR scope too large → suggest split |
| Nits are optional to address | Author may decline nits with brief rationale |
| Questions have 24h response window | If unanswered after 24h, reviewer decides whether it blocks |
| Praise is not filler | Only praise genuinely good patterns. ✗ "looks good" as praise |

---

## 7. Approval Flow

### Required Approvals

| Project Type | Min Approvals | Who Can Approve |
|---|---|---|
| Solo / personal project | 0 (self-review) | Author performs self-review using §4 checklist |
| Team project (2–5 devs) | 1 | Any team member ; not the author |
| Team project (6+ devs) | 2 | At least 1 domain owner for touched modules |
| Security-sensitive change | 2 | At least 1 security-aware reviewer |
| Architecture change | 2 | At least 1 senior/lead with architecture authority |
| Hotfix (production incident) | 1 | Any team member; post-merge full review within 24h |

### Approval Rules

| Rule | Detail |
|---|---|
| Approval = verified | Approving means reviewer checked §4 items, not just read the diff |
| Stale approval | New force-push invalidates prior approvals — re-review required |
| Conditional approval | "Approve with nits" = approved if nits addressed; no re-review needed |
| Self-review for solo projects | Author waits ≥ 1 hour before self-reviewing. Fresh eyes catch more |
| ✗ Approval without reading diff | Approval = reviewer read every changed line |
| ✗ Merge without required approvals | CI blocks merge unless approval count met |
| CODEOWNERS enforcement | If project uses CODEOWNERS, matching reviewers automatically required |

### Who Reviews What

| Change Type | Required Reviewer Profile |
|---|---|
| Business logic | Domain expert for that module |
| Infrastructure / DevOps | Ops-experienced team member |
| Database schema | Database-aware reviewer |
| Public API surface | API design reviewer |
| Security-relevant | Security-trained reviewer |
| Cross-module refactor | Architecture-level reviewer |

---

## 8. Review Speed

Outer bound: a review request gets a first response within **1 business day** — never sit on a pending review longer. Targets below are tighter during work hours.

| Metric | Target | Escalation |
|---|---|---|
| First response (comment or approve) | ≤ 4 hours work hours · ≤ 1 business day absolute | If missed → reviewer reassigned or author pings |
| Follow-up round | ≤ 2 hours after author updates | Faster for small changes |
| Total review-to-merge | ≤ 1 business day | If exceeded → daily standup escalation |
| Hotfix review | ≤ 1 hour | On-call reviewer; post-merge review for thoroughness |

**Speed rules:**

| Rule | Detail |
|---|---|
| Reviews are high-priority | Review requests rank above feature work in priority queue |
| Batch reviews | If assigned multiple, review in FIFO order; do not cherry-pick |
| ✗ Blocking velocity | If reviewer unavailable for > 4h, reassign. ✗ let PR rot |
| Small PRs first | PRs under 100 lines get reviewed first — fast to review, fast to merge |
| Timezone handoff | For distributed teams, assign reviewers in overlapping timezone windows |
| WIP/Draft PRs | No review obligation until marked ready. Author owns timeline for drafts |

---

## 9. Automated Checks

Machines handle deterministic checks. Humans handle judgment. ✗ waste human reviewer time on what CI catches.

### Machine Checks (CI gates — must pass before human review)

| Check | Tool Category | Blocks Review |
|---|---|---|
| Compilation / build | Language compiler, build system | Yes |
| Linting / formatting | Language linter, formatter | Yes |
| Unit tests | Test runner | Yes |
| Integration tests | Test runner | Yes |
| Type checking | Static type checker | Yes |
| Security scanning | SAST, dependency audit | Yes |
| Coverage threshold | Coverage reporter | Yes ; if below project minimum |
| PR size check | Custom CI step | Warning ; blocks at hard limit (800 lines) |
| Commit message format | Git hook / CI | Yes ; per `git/STANDARDS.md` |
| License compliance | License scanner | Yes ; for dependency changes |

### Human Checks (judgment-dependent — cannot be automated)

| Check | Why Human Required |
|---|---|
| Correctness of business logic | Requires domain understanding |
| Architecture compliance | Requires system-level context beyond single file |
| Naming quality | Requires understanding of domain vocabulary and intent |
| Error handling strategy | Requires knowledge of failure modes and recovery expectations |
| Performance in context | Requires understanding of data volumes and access patterns |
| API design quality | Requires user empathy and backward-compatibility judgment |
| Test quality (not just coverage) | Requires evaluating whether tests assert the right things |
| Security threat modeling | Requires understanding attack surfaces and trust boundaries |

### CI-Review Integration

| Rule | Detail |
|---|---|
| CI runs before review assignment | ✗ assign reviewer while build is red |
| CI status visible in PR | Reviewer sees pass/fail at a glance |
| Failed CI = author fixes first | ✗ request review on failing PR |
| CI re-runs on every push | Stale green status not trusted |
| Flaky test policy | Author is not responsible for pre-existing flaky tests; flag and skip with ticket |

---

## 10. Review Scope

| Rule | Detail |
|---|---|
| Review the diff, not the file | Focus on changed lines and their immediate context (±10 lines) |
| Exception: architecture changes | If PR modifies module boundaries, dependency graph, or tier structure → review affected modules holistically |
| Exception: security-sensitive files | Auth, crypto, input validation, permissions → review entire file for consistency |
| Follow the data flow | Trace changed function calls upstream/downstream to verify correctness at boundaries |
| New files get full review | Every line of a new file is in scope — no "existing code" excuse |
| Deleted code review | Verify nothing depends on deleted code. Check for orphaned tests, config, docs |
| Test files | Review tests with same rigor as production code. Tests encode expected behavior |
| Config/infra changes | Review for environment correctness, secret handling, resource limits |

### Out of Scope (✗ request in current PR review)

| Item | Correct Action |
|---|---|
| Pre-existing code issues unrelated to PR | File separate issue/ticket |
| Style preferences not in project standard | Propose standard change in separate PR |
| Speculative future concerns | Tag as `[future]` comment, do not block |
| Refactoring code author did not touch | Separate refactoring PR |

---

## 11. Handling Disagreements

Disagreements are normal. Unresolved disagreements that block merges are not.

### Escalation Path

| Step | Action | Time Limit |
|---|---|---|
| 1 | Author and reviewer discuss in PR comments | 1 business day |
| 2 | Move to synchronous conversation (call, pair session) | 30 min |
| 3 | Bring in a third team member for tiebreaker opinion | 4 hours |
| 4 | Tech lead or architecture owner makes final call | Same day |

### Decision Rules

| Rule | Detail |
|---|---|
| Facts over opinions | Disagreements resolved by referencing standards, measurements, or documented principles |
| Author default | When no standard applies and impact is low → author's choice wins |
| Reviewer default | When a standard is clearly violated → reviewer's objection stands |
| Time-box debates | ✗ multi-day comment threads. If unresolved after step 1 → escalate |
| Document the decision | Non-obvious resolution recorded as PR comment or ADR |
| ✗ Blocking on style | Style disagreements that are not in a written standard → non-blocking |
| ✗ Relitigating settled decisions | Once decided, move forward. Revisit in retro, not in next PR |
| Disagree and commit | After escalation decision, both parties move forward without passive resistance |

---

## 12. AI-Assisted Review

AI review tools augment human review. ✗ replace human judgment.

### Allowed AI Review Uses

| Use | Rules |
|---|---|
| First-pass scan | AI identifies obvious issues (style, simple bugs, missing tests) before human review |
| Pattern detection | AI flags known anti-patterns, security smells, complexity hotspots |
| Documentation generation | AI drafts PR summaries, change descriptions for human verification |
| Test gap analysis | AI identifies untested code paths for human to evaluate relevance |
| Dependency risk assessment | AI flags vulnerable or unmaintained dependencies |

### AI Review Constraints

| Constraint | Detail |
|---|---|
| Human reviews every AI finding | AI findings are suggestions, not verdicts. Human verifies before marking blocking |
| AI cannot approve PRs | Only human reviewers count toward required approval count |
| AI false-positive rate tracked | If AI generates > 30% false positives → recalibrate or disable |
| AI review runs in CI | AI review = automated check, not substitute for human pass |
| ✗ AI-only review | Every PR gets human reviewer eyes regardless of AI findings |
| ✗ Blind trust in AI "all clear" | AI passing does not reduce human review diligence |
| Sensitive code excluded | Auth, crypto, financial logic → human-only review. AI may miss subtle flaws |

### AI + Human Review Workflow

`CI passes → AI review runs → AI findings added as comments → Human reviewer reviews diff + AI findings → Human approves/requests changes`

AI review happens between CI and human review. Human is final authority.

---

## 13. Scale Matrix

How review practices adapt to project size and team composition.

| Dimension | Solo / Hobby | Small Team (2–5) | Mid Team (6–15) | Large Team (16+) |
|---|---|---|---|---|
| Required approvals | 0 (self-review) | 1 | 2 | 2 + CODEOWNERS |
| Review turnaround | Self-paced | ≤ 4h | ≤ 4h | ≤ 4h (assigned reviewer) |
| PR size limit | 800 lines | 400 lines | 400 lines | 300 lines |
| CI gates before review | Lint + tests | Full CI | Full CI + security scan | Full CI + security + AI review |
| Comment type prefixes | Optional | Recommended | Required | Required + enforced |
| CODEOWNERS file | Not needed | Optional | Recommended | Required |
| Review assignment | Self | Manual or round-robin | Automated round-robin | Automated with load balancing |
| Disagreement escalation | N/A | Direct discussion | Third-party tiebreak | Tech lead authority |
| AI-assisted review | Optional | Optional | Recommended | Required as first pass |
| Post-merge review (hotfix) | Optional | Within 24h | Within 24h | Within 8h |
| Review metrics tracked | None | Optional | Recommended | Required (turnaround, rounds, PR size) |
| Self-review wait time | ≥ 1h | N/A | N/A | N/A |

---

## 14. Checklist

Quick-reference for every review. Reviewer walks through before approving.

### Author Checklist (before requesting review)

- [ ] PR description explains what changed and why
- [ ] PR size within limits (≤ 400 lines target, ≤ 800 hard cap)
- [ ] All CI checks pass (build, lint, test, security)
- [ ] Self-reviewed diff at least once
- [ ] Tests added/updated for new/changed behavior
- [ ] No secrets, credentials, or tokens in diff
- [ ] No commented-out code or debug statements
- [ ] Breaking changes documented in PR description
- [ ] Related issues/tickets linked

### Reviewer Checklist (during review)

- [ ] Read PR description first — understand intent before reading code
- [ ] Verify CI is green before starting review
- [ ] Check correctness: does code match stated intent? (§3 P0)
- [ ] Check security: no injection, auth bypass, secret exposure? (§3 P0)
- [ ] Check architecture: tier boundaries, dependency direction respected? (§3 P1)
- [ ] Check error handling: no silent swallowing, proper propagation? (§3 P1)
- [ ] Check test coverage: new paths tested, edge cases covered? (§3 P1)
- [ ] Check readability: clear names, small functions, obvious flow? (§3 P2)
- [ ] Check performance: no N+1, unbounded allocations, hot-path issues? (§3 P2)
- [ ] All comments prefixed with type: `[blocking]` `[nit]` `[question]` `[praise]` (§6)
- [ ] Blocking comments reference a standard or principle (§6)
- [ ] Reviewed only the diff scope (unless architecture change) (§10)

### Approval Checklist (before approving)

- [ ] All blocking comments resolved
- [ ] All questions answered (or confirmed non-blocking)
- [ ] CI still green after author's latest push
- [ ] Required approval count will be met with this approval (§7)
- [ ] Confident this code is production-ready
