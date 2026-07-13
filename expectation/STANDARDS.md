# Expectation Standards

> How to write the north-star comparators that define what peak output looks like — the quality bar standards do not set.

**ID** `expectation` · **Tier** Core · **Version** 1.0
**Owns** peak comparator model · quality dimensions · grading rubrics · failure taxonomy · benchmark targets · expectation-driven evaluation · the quality bar
**Defers to** coverage · pyramid · mocking policy · test classification → [testing](../testing/STANDARDS.md) · load · soak · chaos execution → [testing/PRESSURE.md](../testing/PRESSURE.md) · density + authoring rules → [agent](../agent/STANDARDS.md) · latency/throughput budgets → [performance](../performance/STANDARDS.md)
**Load with** [testing](../testing/STANDARDS.md) · [agent](../agent/STANDARDS.md)

---

## Table of Contents

1. [Standards vs Expectations](#1-standards-vs-expectations)
2. [The Peak Comparator Model](#2-the-peak-comparator-model)
3. [Document Structure](#3-document-structure)
4. [Quality Dimensions](#4-quality-dimensions)
5. [Grading and Scoring](#5-grading-and-scoring)
6. [Failure Taxonomy](#6-failure-taxonomy)
7. [Benchmark Targets](#7-benchmark-targets)
8. [Expectation-Driven Evaluation](#8-expectation-driven-evaluation)
9. [Writing Rules](#9-writing-rules)
10. [Anti-Patterns](#10-anti-patterns)
11. [Checklist](#11-checklist)

---

## 1. Standards vs Expectations

Standards govern **process** (how to build). Expectations govern **outcome** (what excellence looks like). A system can follow every standard and still produce mediocre results; expectations close that gap.

| Aspect | Standards | Expectations |
|---|---|---|
| Question | "How do we build?" | "What does excellent look like?" |
| Focus | Process, rules, constraints | Outcome, quality, behavior |
| Verifies | Correctness, architecture compliance | Output quality, user value, expert-level results |
| Failure caught | Structural bugs, bad patterns | Mediocre output, wrong thing built correctly |
| Applied during | Development | Evaluation, testing, acceptance |
| Changes when | The process improves | Understanding of excellence deepens |

Standards without expectations → correct but mediocre systems. Expectations without standards → excellent vision, unreliable execution. Both → reliable systems that produce excellent outcomes.

Expectations sit above all other standards as the quality ceiling: **expectations** validate the outcome of the **standards**, which govern the process of the **code**. Every project has standards; production-grade projects add expectations for each critical output domain.

Testing owns coverage, the pyramid, and mocking policy → [testing](../testing/STANDARDS.md). Expectation owns the quality **bar** and the rubrics — the two compose: a test asserts the code runs; an expectation test asserts the output is excellent (§8).

---

## 2. The Peak Comparator Model

### Governing Principle

> "What would a peak expert produce, minus their limitations?"

Every expectation document defines excellence by describing what the best human expert would deliver — then identifies where a system exceeds human limits (speed, consistency, memory, scale) while matching human strengths (judgment, creativity, nuance).

### Three Components

| Component | Purpose | Example |
|---|---|---|
| Peak behavior | What excellence looks like | "Every claim grounded in evidence" |
| Human limitation | What even experts get wrong | "Confidence calibration is unreliable" |
| System advantage | Where the system exceeds the human | "Cardinal confidence via objective metrics" |

### Expectation Domains

One expectation document per critical output domain. ✗ every project needs all of them — start with the domain that defines the project's primary value delivery.

| Domain | Defines | Example file |
|---|---|---|
| Output quality | What delivered results look like | `REPORT_EXPECTATION.md` |
| Cognitive process | How the system reasons/decides | `HUMAN_EXPECTATION.md` |
| Organizational | How multi-agent coordination works | `CORPORATE_EXPECTATION.md` |
| Platform | How infrastructure behaves | `PLATFORM_EXPECTATION.md` |
| Development | How the project evolves | `DEVELOPMENT_EXPECTATION.md` |
| Interface | How the UX feels | `UI_EXPECTATION.md` |

---

## 3. Document Structure

Every expectation document follows this skeleton. Peak behavior first — the reader learns what excellence is before how to measure it. Measurement second, failure modes third, benchmarks last.

| # | Section | Required |
|---|---|---|
| 1 | Peak behavior definition | Yes |
| 2 | Quality dimensions | Yes |
| 3 | Grading rubric | Yes |
| 4 | Failure taxonomy | Yes |
| 5 | Benchmark targets (minimum / target / stretch) | Yes |
| 6 | Human limitation map | Domain-specific |
| 7 | Design principles (inviolable rules) | Yes |
| 8 | Edge cases | Production only |
| 9 | Implementation gaps vs the expectation | Active development |
| 10 | Configuration (quality-affecting parameters) | If applicable |

---

## 4. Quality Dimensions

Every expectation document declares **5–12** measurable dimensions specific to its domain. Each must be:

| Requirement | Description |
|---|---|
| Measurable | Numeric score (0.0–1.0 or 1–5) |
| Independent | Scoring one does not determine another |
| Observable | Evaluable from the output alone |
| Actionable | A low score suggests a specific fix |
| Domain-relevant | Tied directly to what "peak" means here |

### Universal Dimensions

| Dimension | Measures |
|---|---|
| Accuracy | Factual correctness |
| Completeness | All requirements addressed, no gaps |
| Grounding | Claims backed by evidence or source |
| Structure | Organization, hierarchy, navigability |
| Actionability | Output enables the next step without interpretation |
| Conciseness | Optimal density — not bloated, not sparse |
| Honesty | Uncertainty explicit, confidence calibrated |

### Domain-Specific Examples

| Domain | Additional dimensions |
|---|---|
| Report output | Timeliness, citation quality, professional tone |
| Cognitive process | Planning depth, bias mitigation, tool utilization |
| Platform | Latency, availability, security posture |
| UI | Responsiveness, accessibility, visual consistency |
| Development | Velocity, debt ratio, measurement coverage |

---

## 5. Grading and Scoring

### Scales

| Scale | When to use |
|---|---|
| 0.0–1.0 continuous | Automated metrics (grounding score, confidence) |
| 1–5 integer | Human rubric (expert review) |
| Pass/Fail binary | Gate checks (schema valid, scan clean) |
| Tier classification | Strong ≥ 0.8 · Acceptable ≥ 0.6 · Weak ≥ 0.3 · Critical < 0.3 |

### Rubric (1–5, human-evaluated)

| Score | Meaning |
|---|---|
| 5 | Peak expert — could not meaningfully improve |
| 4 | Professional — minor improvements possible |
| 3 | Acceptable — meets requirements, not impressive |
| 2 | Below standard — notable gaps or issues |
| 1 | Unacceptable — fundamental problems |

Rules:

- Each score level carries a concrete behavioral description, ✗ an adjective, specific to the domain.
- Score 3 = meets requirements, ✗ "average."
- The evaluator scores without seeing other outputs — absolute, ✗ relative.

### Composite Scoring

- Assign weights reflecting importance to peak quality; weighted sum normalized to 0.0–1.0.
- Document weights explicitly — hidden weights are hidden assumptions.
- ✗ any dimension over 40% weight — prevents single-dimension dominance.
- Validate: the composite correlates with human "overall impression" at r > 0.7.

---

## 6. Failure Taxonomy

Every expectation document names its failure modes — what bad looks like, how to detect it, how to recover. The taxonomy is exhaustive: if a failure can occur, it has a name and a detection method.

| Field | Description |
|---|---|
| Name | Short identifier (Hallucination, Scope Drift) |
| Definition | What went wrong — one sentence |
| Detection | Metric, signal, or symptom revealing it |
| Severity | Critical / High / Medium / Low |
| Recovery | Action when detected |
| Prevention | What stops it upstream |

### Universal Failure Modes

| Failure | Definition | Detection |
|---|---|---|
| Hallucination | Claims unsupported by evidence | Grounding score < threshold |
| Omission | Important requirements unaddressed | Completeness < threshold |
| Scope drift | Output answers the wrong question | Goal alignment < threshold |
| Overconfidence | High confidence on incorrect output | Stated vs actual confidence gap |
| Staleness | Outdated info when fresh exists | Temporal freshness check |
| Partial delivery | Incomplete, missing sections | Completion ratio < 1.0 |
| Gold plating | Excessive output beyond requirements | Conciseness score < threshold |

Domain-specific failures are added per document.

---

## 7. Benchmark Targets

### Three-Tier Model

| Tier | Meaning | Use |
|---|---|---|
| Minimum | Below this = unacceptable, blocks release | Quality gate |
| Target | Expected production quality | Normal operation |
| Stretch | Peak achievable quality | Optimization goal |

Example table:

| Dimension | Minimum | Target | Stretch |
|---|---|---|---|
| Grounding score | ≥ 0.6 | ≥ 0.8 | ≥ 0.9 |
| Accuracy (1–5) | ≥ 3.0 | ≥ 3.8 | ≥ 4.3 |
| Completeness | ≥ 0.7 | ≥ 0.85 | ≥ 0.95 |

Rules:

- Minimum = a hard gate — below it → rejected or flagged.
- Target = the design point the system is tuned to reliably achieve.
- Stretch = a continuous-improvement goal, pursued not required.
- Benchmarks are calibrated from baseline measurement, ✗ aspiration. Start conservative, tighten over time, refresh quarterly.

---

## 8. Expectation-Driven Evaluation

Traditional testing verifies correctness (does it work?). Expectation testing verifies quality (does it produce excellent results?). Test execution and coverage → [testing](../testing/STANDARDS.md); this section adds only the quality-scoring layer.

| Test type | Verifies | Driven by |
|---|---|---|
| Unit | Function correctness | Code + [testing](../testing/STANDARDS.md) |
| Integration | Module interaction | [architecture](../architecture/STANDARDS.md) |
| Contract | API boundary | [api](../api/STANDARDS.md) |
| **Expectation** | **Output quality** | **This standard** |

### Evaluation Flow

Define scenario → produce output → score each dimension → check against benchmarks → classify any failures → compare to baseline.

### Evaluation Approaches

| Approach | When | Cost | Reliability |
|---|---|---|---|
| Automated metrics | Every build | Low | High for measurable dimensions |
| Human rubric scoring | Periodic + release | High | Gold standard |
| Baseline comparison | Every build | Low | Catches regression |
| A/B comparison | Major changes | Medium | Comparative quality |
| Blind evaluation | Calibration | High | Eliminates bias |

### Baseline Protocol

1. Run N diverse scenarios (N ≥ 50 for statistical significance).
2. Score all quality dimensions.
3. Compute mean, median, P25, P75, P95 per dimension.
4. Set minimum = P25, target = median, stretch = P75.
5. Store as `BASELINES.md`.
6. Refresh quarterly or after major system changes.

---

## 9. Writing Rules

### Density

Follow the same density principles as all standards → [agent](../agent/STANDARDS.md). Tables over prose. Measurable over subjective.

### Specificity

Every statement must be evaluable. Test: can an evaluator score the output without asking for clarification?

| ✗ Vague | Specific |
|---|---|
| "Output should be high quality" | "Grounding score ≥ 0.8, zero fabricated claims" |
| "Reports should be well-structured" | "Quality badge → summary → evidence → appendices, in order" |
| "System should be fast" | "P99 < 5 s standard tasks, < 30 s complex" |

### Versioning

- Expectation documents use semver.
- Quality dimensions are additive — ✗ remove an existing dimension.
- Benchmark targets tighten, ✗ loosen without justification.
- Breaking changes documented with rationale.

### Size Targets

| Type | Target | Hard cap |
|---|---|---|
| Simple domain | 200–400 lines | 600 |
| Complex domain | 400–800 lines | 1200 |

---

## 10. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Aspirational only | "Be perfect" with no metrics | Add dimensions + benchmarks |
| No failure taxonomy | Defines only success | Name failures with detection |
| Untestable | Quality described, not evaluable | Make every dimension scorable |
| Static benchmarks | Targets never update | Refresh quarterly from baselines |
| Missing baseline | Targets set without measurement | Run the baseline protocol first |
| Single-dimension | Only accuracy, ignores honesty/completeness | 5–12 independent dimensions |
| Subjective rubric | "Good" vs "great" without behaviors | Concrete per-score descriptions |
| No recovery path | Names failures without remediation | Every failure needs detection + recovery |
| Expectation drift | Document says X, evaluated on Y | Review with every major release |

---

## 11. Checklist

- [ ] Peak behavior defined — what excellence looks like in this domain
- [ ] 5–12 quality dimensions, each measurable and independent
- [ ] Every dimension observable from the output alone
- [ ] Grading rubric with a concrete per-score behavioral description
- [ ] Score 3 defined as "meets requirements", not "average"
- [ ] Composite weights documented; no dimension exceeds 40% weight
- [ ] Failure taxonomy: every known failure named with detection + recovery
- [ ] Benchmark targets set: minimum / target / stretch per dimension
- [ ] Benchmarks calibrated from a measured baseline, not aspiration
- [ ] Baseline protocol run over N ≥ 50 scenarios and stored
- [ ] Benchmarks refreshed within the last quarter
- [ ] Design principles stated as inviolable rules for the domain
- [ ] Defers coverage, pyramid, and mocking policy to testing
- [ ] Expectation tests exist for each dimension
- [ ] Composite score correlates with human judgment at r > 0.7
- [ ] Every statement is evaluable without asking questions
- [ ] Document is versioned with semver; dimensions are additive-only
