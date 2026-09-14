# LLM Evaluation Standards

> Rules for measuring LLM application quality — eval set construction, grader selection, scoring, gates, regression detection, and keeping evals honest as the system changes.

**ID** `llm/evaluation` · **Tier** Domain · **Version** 1.0
**Owns** eval set construction · case provenance + holdout discipline · grader taxonomy + selection · LLM-as-judge rules · scoring + variance reporting · eval gates + regression detection · component vs end-to-end evals · eval set maintenance + staleness · human review protocol · adversarial + red-team eval cases
**Defers to** prompt registry · model pinning · output contracts · degradation · cost budgets → [llm](STANDARDS.md) · injection · tool authorization · PII → [llm/safety](SAFETY.md) · quality dimensions · grading rubrics · peak comparator · failure taxonomy → [expectation](../expectation/STANDARDS.md) · test pyramid · tier classification · flake budget · coverage → [testing](../testing/STANDARDS.md) · dataset versioning · leakage · split strategy · experiment tracking → [ml](../ml/STANDARDS.md) · CI stage wiring → [cicd](../cicd/STANDARDS.md) · maturity levels · evidence rules → [maturity](../maturity/STANDARDS.md) · metric plumbing · dashboards → [observability](../observability/STANDARDS.md)
**Load with** [llm](STANDARDS.md) · [expectation](../expectation/STANDARDS.md) · [testing](../testing/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Eval Set Construction](#2-eval-set-construction)
3. [Graders](#3-graders)
4. [Component Evals](#4-component-evals)
5. [Scoring](#5-scoring)
6. [Gates](#6-gates)
7. [Eval Set Maintenance](#7-eval-set-maintenance)
8. [Human Review](#8-human-review)
9. [Adversarial Cases](#9-adversarial-cases)
10. [Anti-Patterns](#10-anti-patterns)
11. [Checklist](#11-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| An unevaluated prompt is unshipped | No eval set → no baseline → no way to detect the regression a change causes |
| Evals are tests | Versioned, run in CI, gate the build → [testing](../testing/STANDARDS.md) |
| Cases come from reality | Production traffic and real failures, ✗ cases invented to match the prompt you already wrote |
| Grade the property, ✗ the phrasing | A grader that rewards a specific wording measures style drift |
| Per-case deltas, ✗ only aggregates | An average that holds while cases invert is a masked regression |
| A score without variance is a guess | Non-deterministic systems report run count and spread → [llm §11](STANDARDS.md#11-determinism) |
| The eval set decays | A set that stops predicting live behavior is stale and is repaired, ✗ trusted (§7) |

---

## 2. Eval Set Construction

| Rule | Detail |
|---|---|
| Minimum viable set | 20 cases before a prompt ships; 100+ before it carries production traffic. Below 20, a single case moves the score more than a real regression |
| Sourced from traffic | Cases are sampled from real inputs. Synthetic cases fill known gaps, are labeled `synthetic`, and never exceed half the set |
| Every case has an origin | `production` · `incident` · `synthetic` · `adversarial`, with a link to the source where one exists |
| Every production incident becomes a case | A failure that reached a user is a permanent eval case before the fix is merged |
| Stratified, ✗ uniform | Cases cover the input distribution: common paths, long tail, edge lengths, each supported language and locale |
| Hard cases are marked | A difficulty label lets a regression on hard cases be read separately from an overall shift |
| Expected output is a property set | Required entities, forbidden content, schema, ranges — ✗ a single golden string, except where the output is genuinely exact |
| Versioned with the prompt | Eval set ID and version are recorded in the registry entry → [llm §3](STANDARDS.md#3-prompts-as-artifacts) |
| Holdout is never tuned on | A reserved split is scored but never inspected case-by-case during prompt iteration → [ml §4](../ml/STANDARDS.md#4-data-preparation) |

Tiering by cost — the full set is not run on every commit:

| Tier | Size | Runs |
|---|---|---|
| Smoke | 10–20 cases, all critical | Every commit touching a prompt |
| Full | Entire set | Before release, and on any model pin change |
| Holdout | Reserved split | Release only. Inspected in aggregate |

---

## 3. Graders

Select the cheapest grader that measures the property. Escalate only when the cheaper one cannot.

| Grader | Measures | Use when |
|---|---|---|
| Schema | Output conforms to the declared contract | Always, for program-consumed output → [llm §7](STANDARDS.md#7-structured-output) |
| Exact match | Byte equality | Output is genuinely canonical — an ID, an enum, a classification label |
| Set / field match | Required entities present, forbidden absent, fields in range | Extraction, classification, structured generation |
| Programmatic invariant | A property checked by code — arithmetic, referential integrity, valid SQL, compiling code | The property is mechanically checkable |
| Similarity | Embedding or n-gram distance to a reference | Paraphrase is acceptable and a reference exists |
| LLM-as-judge | Rubric-scored subjective quality | No cheaper grader captures the property (§3 rules below) |
| Human | Rubric-scored by a person | The judge itself is unvalidated, or the stakes warrant it (§8) |

LLM-as-judge rules:

- The judge prompt is itself a registry entry with a version, a pinned model, and its own eval set. An unversioned judge silently re-grades history.
- The judge is validated against human labels before use: report agreement on a labeled sample, and re-validate when the judge's model pin changes.
- Judge on a rubric with discrete levels and stated criteria → [expectation](../expectation/STANDARDS.md) owns the rubric form. ✗ a bare 1–10 score.
- The judge sees the case input and the property set, ✗ which system produced the output, ✗ the previous score.
- ✗ judge with the same model version under test where a cheaper grader exists — self-preference inflates the score.
- Pairwise comparison beats absolute scoring for ranking two prompt versions; positions are swapped across runs to cancel order bias.
- A judge score is never the sole gate on a safety-relevant property (§9).

---

## 4. Component Evals

An end-to-end score cannot localize a regression. Components are evaluated independently.

| Component | Measured | Metric |
|---|---|---|
| Retriever | Are the right chunks returned | Recall@k · precision@k · MRR → [llm §6](STANDARDS.md#6-retrieval-grounding) |
| Chunker + index | Does the chunking preserve answerable spans | Answerable-span coverage |
| Router / classifier | Is the task sent to the right prompt or model | Confusion matrix, per-class recall |
| Generator | Given correct context, is the answer correct | Grounded accuracy with context supplied |
| Grounding | Does the output cite only supplied chunks | Unsupported-claim rate |
| Tool selection | Right tool, right arguments | Tool-choice accuracy · argument validity → [llm/safety §5](SAFETY.md#5-tool-authorization) |
| End-to-end | Does the user get a correct answer | Task success rate |

Rules:

- A drop in end-to-end score is attributed to a component before any prompt is edited.
- The generator is evaluated with gold context as well as retrieved context. The gap between the two is the retriever's cost.
- Each component has its own gate. An end-to-end pass with a regressed component is a deferred failure.

---

## 5. Scoring

| Rule | Detail |
|---|---|
| Report per-case, then aggregate | The case table is the artifact. The aggregate is a summary of it |
| Run count is reported | Non-deterministic cases run n ≥ 3. A single run is a sample, ✗ a score |
| Variance is reported | Standard deviation or min/max per case. A case whose score spans the gate threshold is unstable and is fixed or marked |
| Pass rate, ✗ mean score | For gated properties report the fraction of cases passing their property set. Means hide bimodal failure |
| Segment the aggregate | By difficulty, origin, language, and input length. A uniform total across diverging segments is uninformative |
| Cost and latency are scored | Every eval run records tokens, cost, and p95 latency per case → [llm §10](STANDARDS.md#10-token-and-cost-budgets) |
| Results are committed | Baseline scores live with the prompt version in version control, ✗ in a dashboard that is overwritten |
| Absent evidence is never a pass | A case that errored or timed out is a failure, ✗ excluded from the denominator → [maturity §4](../maturity/STANDARDS.md#4-numeric-evidence) |

---

## 6. Gates

| Gate | Rule |
|---|---|
| No regression on gated properties | Every gated metric ≥ baseline, within reported variance |
| Critical cases are absolute | Cases marked critical pass at 100%. ✗ traded against an aggregate gain |
| Per-case inversion is reported | Any case that passed at baseline and now fails is listed by name in the gate output, even when the aggregate rises |
| Cost gate | p95 tokens and cost per task within the declared budget → [llm §10](STANDARDS.md#10-token-and-cost-budgets) |
| Latency gate | p95 latency within the declared budget → [performance](../performance/STANDARDS.md) |
| Safety gate | Adversarial case pass rate at 100% for blocking categories (§9) |
| Accepted regression is written down | A deliberate trade is recorded with the reason, the new baseline, and an owner. ✗ a silently lowered threshold |
| Gate runs in CI | The eval gate is a pipeline stage, ✗ a step someone remembers → [cicd](../cicd/STANDARDS.md) |

A gate that has never failed is unverified. Confirm each gate fails on a deliberately broken prompt before trusting it.

---

## 7. Eval Set Maintenance

| Rule | Detail |
|---|---|
| Live-vs-eval drift is monitored | Live quality metrics are compared to eval expectations → [llm §12](STANDARDS.md#12-observability). Divergence means the set is stale, ✗ that live is wrong |
| Staleness triggers repair | A set that no longer predicts live behavior gets new cases from current traffic before the next prompt change |
| Saturation triggers hardening | A set scoring ≥ 95% across recent versions has stopped discriminating. Add harder cases, ✗ celebrate |
| Cases are never deleted to pass | Removing a failing case is a regression disguised as a fix. Retire a case only when the capability itself is retired, with the reason recorded |
| Contamination is assumed | A published benchmark may be in the model's training data. Proprietary cases from your own traffic are the trustworthy signal |
| Set changes are versioned | Adding, editing, or retiring cases bumps the eval set version and re-establishes the baseline |
| Re-baseline on pin change | A new model pin re-runs the full set and records a new baseline before any prompt edit → [llm §13](STANDARDS.md#13-model-migration) |
| Labels are audited | A sample of expected outputs is re-checked periodically. A wrong label teaches the gate the wrong thing |

---

## 8. Human Review

| Rule | Detail |
|---|---|
| Rubric first | Reviewers score against the same discrete rubric the judge uses → [expectation](../expectation/STANDARDS.md) |
| Blind to source | Reviewers do not know which prompt version or model produced an output |
| Agreement is measured | Inter-rater agreement is reported. Low agreement means the rubric is ambiguous, ✗ that reviewers are careless |
| Human labels calibrate the judge | The labeled sample is the ground truth an LLM judge is validated against (§3) |
| Sampled, ✗ exhaustive | Human review covers a stratified sample sized to the decision, with disagreements adjudicated |
| Reviewers see the input | Scoring an output without its input measures fluency |

---

## 9. Adversarial Cases

Adversarial cases are a permanent, always-run part of the eval set — ✗ a one-time red-team exercise.

| Category | Cases assert |
|---|---|
| Prompt injection | Instructions embedded in untrusted content are not followed → [llm/safety §3](SAFETY.md#3-untrusted-content-boundary) |
| Indirect injection | Instructions in retrieved documents, tool results, or file contents are not followed |
| Data exfiltration | System instructions, other tenants' data, and credentials are not emitted |
| Tool abuse | Output does not induce a tool call beyond the caller's authority → [llm/safety §5](SAFETY.md#5-tool-authorization) |
| Jailbreak | Role-play, encoding, and multi-turn escalation do not lift declared restrictions |
| Overrefusal | Benign in-scope requests are not refused. An unmeasured refusal rate degrades into uselessness |
| Hallucination under absence | Empty or irrelevant retrieval produces an abstention, ✗ a fabrication → [llm §6](STANDARDS.md#6-retrieval-grounding) |
| PII leakage | Sensitive input does not reappear in output destined for another party |

Rules:

- Blocking categories gate at 100%. A single pass-through is a release blocker, ✗ a percentage.
- Every real injection or jailbreak found in production becomes a permanent case the same day.
- Adversarial cases are re-run on every model pin change — a defense tuned to one model version is not a property of the next.
- Overrefusal is measured alongside every restriction added. A restriction with no overrefusal measurement is untested.

---

## 10. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Eval set written after the prompt | Cases encode what the prompt already does | Cases from real traffic and failures (§2) |
| Single-run scoring | Variance read as signal | n ≥ 3 with variance reported (§5) |
| Mean score as the gate | Bimodal failure hidden | Pass rate against property sets (§5) |
| Aggregate-only reporting | Per-case inversions invisible | Per-case delta table (§6) |
| Deleting failing cases | Regression disguised as a fix | Fix the prompt or record the accepted regression (§7) |
| Judge with no eval set | Ungraded grader, silently drifting | Judge is a versioned prompt with its own evals (§3) |
| Judge on the model under test | Self-preference inflates the score | Different model, or a cheaper grader (§3) |
| Public benchmark as the gate | Contamination, and it does not measure your task | Proprietary cases from your traffic (§7) |
| Exact-string expectations everywhere | Permanently flaky | Property sets (§2) |
| Adversarial testing as a launch milestone | Defenses regress silently after launch | Permanent always-run cases (§9) |
| Adding restrictions without measuring refusal | Product becomes useless while scoring "safe" | Overrefusal cases (§9) |
| End-to-end score only | Regression cannot be localized | Component evals (§4) |

---

## 11. Checklist

- [ ] Every production prompt has a versioned eval set with committed baseline scores
- [ ] At least 20 cases before ship, 100+ before production traffic
- [ ] Cases carry an origin label; synthetic cases are under half the set
- [ ] Every production incident has become a permanent eval case
- [ ] A holdout split exists and is never inspected case-by-case during iteration
- [ ] The cheapest adequate grader is used per property; schema grading is always applied to structured output
- [ ] Any LLM judge is a versioned prompt with a pinned model, its own eval set, and measured agreement against human labels
- [ ] Components are evaluated independently: retriever, router, generator, grounding, tool selection
- [ ] Non-deterministic cases run n ≥ 3 with variance reported
- [ ] Errored and timed-out cases count as failures, not exclusions
- [ ] Gates cover quality, per-case inversion, cost, latency, and safety
- [ ] Every gate has been observed to fail on a deliberately broken prompt
- [ ] Accepted regressions are written down with reason, new baseline, and owner
- [ ] Live metrics are compared against eval expectations; drift triggers set repair
- [ ] A set scoring ≥ 95% is hardened with new cases rather than left in place
- [ ] Adversarial cases are permanent, always-run, and gate at 100% for blocking categories
- [ ] Overrefusal is measured alongside every restriction added
- [ ] The full eval set is re-run and re-baselined on every model pin change
