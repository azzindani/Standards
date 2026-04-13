# Expectation Standards

How to write expectation documents — the north-star comparators that
define what peak output looks like. Standards govern process (how to
build). Expectations govern outcome (what excellence looks like).

A system can follow every standard and still produce mediocre results.
Expectations close this gap by defining measurable quality bars,
failure taxonomies, and benchmark targets that drive testing and
evaluation against "what would a peak expert produce?"

---

## Table of Contents

1. [Standards vs Expectations](#1-standards-vs-expectations)
2. [The Peak Comparator Model](#2-the-peak-comparator-model)
3. [Expectation Document Structure](#3-expectation-document-structure)
4. [Quality Dimensions](#4-quality-dimensions)
5. [Grading & Scoring](#5-grading--scoring)
6. [Failure Taxonomy](#6-failure-taxonomy)
7. [Benchmark Targets](#7-benchmark-targets)
8. [Expectation-Driven Testing](#8-expectation-driven-testing)
9. [Writing Rules](#9-writing-rules)
10. [Anti-Patterns](#10-anti-patterns)
11. [Checklist](#11-checklist)

---

## 1. Standards vs Expectations

| Aspect | Standards | Expectations |
|---|---|---|
| Question answered | "How do we build?" | "What does excellent look like?" |
| Focus | Process, rules, constraints | Outcome, quality, behavior |
| Verifies | Code correctness, architecture compliance | Output quality, user value, expert-level results |
| Failure mode caught | Structural bugs, bad patterns | Mediocre output, missed goals, wrong thing built correctly |
| When applied | During development | During evaluation, testing, acceptance |
| Changes when | Process improves | Understanding of excellence deepens |

Standards without expectations → correct but mediocre systems.
Expectations without standards → excellent vision, unreliable execution.
Both together → reliable systems that produce excellent outcomes.

### Relationship to Other Standards

Expectations sit above all other standards as the quality ceiling:

```
Expectations (what peak output looks like)
    ↑ validates outcome of
Standards (how to build correctly)
    ↑ governs process of
Code (the implementation)
```

Every project has standards. Production-grade projects add expectations
for each critical output domain.

---

## 2. The Peak Comparator Model

### Governing Principle

> "What would a peak expert produce, minus their limitations?"

Every expectation document defines excellence by describing what the
best human expert in that domain would deliver — then identifies where
a system can exceed human limitations (speed, consistency, memory,
scale) while matching human strengths (judgment, creativity, nuance).

### Three Components

| Component | Purpose | Example |
|---|---|---|
| Peak behavior | What excellence looks like | "Every claim grounded in evidence" |
| Human limitation | What even experts get wrong | "Confidence calibration is unreliable" |
| System advantage | Where system exceeds human | "Cardinal confidence via objective metrics" |

### Expectation Domains

One expectation document per critical output domain of the project.

| Domain type | What it defines | Example file |
|---|---|---|
| Output quality | What delivered results look like | `REPORT_EXPECTATION.md` |
| Cognitive process | How the system reasons/decides | `HUMAN_EXPECTATION.md` |
| Organizational | How multi-agent coordination works | `CORPORATE_EXPECTATION.md` |
| Platform | How infrastructure behaves | `PLATFORM_EXPECTATION.md` |
| Development | How the project evolves over time | `DEVELOPMENT_EXPECTATION.md` |
| Interface | How the user experience feels | `UI_EXPECTATION.md` |

Not every project needs all domains. Start with the domain that
defines the project's primary value delivery.

---

## 3. Expectation Document Structure

Every expectation document follows this skeleton:

| Section | Purpose | Required |
|---|---|---|
| 1. Peak behavior definition | What excellence looks like in this domain | Yes |
| 2. Quality dimensions | Measurable axes of quality | Yes |
| 3. Grading rubric | How to score each dimension | Yes |
| 4. Failure taxonomy | Named failure modes with detection | Yes |
| 5. Benchmark targets | Minimum / target / stretch per dimension | Yes |
| 6. Human limitation map | What experts get wrong + system countermeasure | Domain-specific |
| 7. Design principles | Inviolable rules for this domain | Yes |
| 8. Edge cases | How the system behaves in unusual situations | Production only |
| 9. Implementation gaps | Known shortfalls vs the expectation | Active development |
| 10. Configuration | Tunable parameters that affect quality | If applicable |

### Ordering Principle

Peak behavior first — reader understands what excellence looks like
before learning how to measure it. Measurement comes second.
Failure modes third. Benchmarks last.

---

## 4. Quality Dimensions

### Defining Dimensions

Every expectation document declares 5–12 measurable quality dimensions
specific to its domain. Each dimension must be:

| Requirement | Description |
|---|---|
| Measurable | Numeric score (0.0–1.0 or 1–5 scale) |
| Independent | Scoring one dimension does not determine another |
| Observable | Evaluated from the output alone |
| Actionable | Low score suggests specific fix |
| Domain-relevant | Directly tied to what "peak" means in this domain |

### Universal Dimensions (applicable across domains)

| Dimension | Measures |
|---|---|
| Accuracy | Factual correctness of output |
| Completeness | All requirements addressed, no gaps |
| Grounding | Claims backed by evidence or source |
| Structure | Organization, hierarchy, navigability |
| Actionability | Output enables next step without interpretation |
| Conciseness | Optimal density — not bloated, not sparse |
| Honesty | Uncertainty explicit, confidence calibrated |

### Domain-Specific Dimensions (examples)

| Domain | Additional dimensions |
|---|---|
| Report output | Timeliness, citation quality, professional tone |
| Cognitive process | Planning depth, bias mitigation, tool utilization |
| Platform | Latency, availability, security posture |
| UI | Responsiveness, accessibility, visual consistency |
| Development | Velocity, debt ratio, measurement coverage |

---

## 5. Grading & Scoring

### Scoring Scales

| Scale | When to use |
|---|---|
| 0.0–1.0 continuous | Automated metrics (grounding score, confidence) |
| 1–5 integer | Human evaluation rubric (expert review) |
| Pass/Fail binary | Gate checks (schema valid, security scan clean) |
| Tier classification | Threshold-based: Strong ≥0.8 · Acceptable ≥0.6 · Weak ≥0.3 · Critical <0.3 |

### Rubric Design Rules

For human-evaluated dimensions (1–5 scale):

| Score | Meaning |
|---|---|
| 5 | Peak expert — could not meaningfully improve |
| 4 | Professional — minor improvements possible |
| 3 | Acceptable — meets requirements, not impressive |
| 2 | Below standard — notable gaps or issues |
| 1 | Unacceptable — fundamental problems |

Rules:
- Each score level has concrete behavioral description, not adjective
- Descriptions specific to domain, not generic
- Score 3 = meets requirements. Not "average."
- Evaluator scores without seeing other outputs (absolute, not relative)

### Composite Scoring

When combining multiple dimensions into single quality score:

- Assign weights reflecting importance to peak quality
- Weighted sum normalized to 0.0–1.0
- Document weights explicitly — hidden weights = hidden assumptions
- No dimension exceeds 40% weight (prevents single-dimension dominance)
- Validate: composite correlates with human "overall impression" (r > 0.7)

---

## 6. Failure Taxonomy

Every expectation document defines named failure modes — what bad
looks like, how to detect, how to recover.

### Failure Classification Fields

| Field | Description |
|---|---|
| Name | Short identifier (Hallucination, Scope Drift, etc.) |
| Definition | What went wrong — one sentence |
| Detection | Metric, signal, or symptom that reveals this failure |
| Severity | Impact: Critical / High / Medium / Low |
| Recovery | Action when detected |
| Prevention | What prevents this failure upstream |

### Universal Failure Modes

| Failure | Definition | Detection |
|---|---|---|
| Hallucination | Claims not supported by evidence | Grounding score < threshold |
| Omission | Important requirements unaddressed | Completeness < threshold |
| Scope drift | Output answers wrong question | Goal alignment < threshold |
| Overconfidence | High confidence on incorrect output | Stated vs actual confidence gap |
| Staleness | Outdated information when fresh available | Temporal freshness check |
| Partial delivery | Task incomplete, missing sections | Completion ratio < 1.0 |
| Gold plating | Excessive output beyond requirements | Conciseness score < threshold |

Domain-specific failures added per expectation document. Taxonomy is
exhaustive — if a failure can occur, it has a name and detection method.

---

## 7. Benchmark Targets

### Three-Tier Target Model

| Tier | Meaning | Use |
|---|---|---|
| Minimum | Below this = unacceptable, blocks release | Quality gate |
| Target | Expected production quality | Normal operation |
| Stretch | Peak achievable quality | Optimization goal |

### Benchmark Table Format

| Dimension | Minimum | Target | Stretch |
|---|---|---|---|
| Grounding score | ≥ 0.6 | ≥ 0.8 | ≥ 0.9 |
| Accuracy (1–5) | ≥ 3.0 | ≥ 3.8 | ≥ 4.3 |
| Completeness | ≥ 0.7 | ≥ 0.85 | ≥ 0.95 |

### Rules

- Minimum = hard gate — below minimum → rejected or flagged
- Target = design point — system tuned to reliably achieve
- Stretch = continuous improvement goal — not required, but pursued
- Benchmarks calibrated from baseline measurement, not aspiration
- Refresh quarterly as system improves
- New benchmarks start conservative, tighten over time

---

## 8. Expectation-Driven Testing

### The Testing Gap

Traditional testing verifies correctness (does it work?).
Expectation testing verifies quality (does it produce excellent results?).

| Test type | Verifies | Driven by |
|---|---|---|
| Unit test | Function correctness | Code + standards |
| Integration test | Module interaction | Architecture standards |
| Contract test | API boundary | API standards |
| **Expectation test** | **Output quality** | **Expectation document** |

### Expectation Test Flow

```
Define scenario → Produce output → Score dimensions →
Check benchmarks → Classify failures → Compare to baseline
```

### Evaluation Approaches

| Approach | When | Cost | Reliability |
|---|---|---|---|
| Automated metrics | Every build | Low | High for measurable dimensions |
| Human rubric scoring | Periodic + release | High | Gold standard |
| Baseline comparison | Every build | Low | Catches regression |
| A/B comparison | Major changes | Medium | Comparative quality |
| Blind evaluation | Calibration | High | Eliminates bias |

### Baseline Protocol

1. Run N diverse scenarios (N ≥ 50 for statistical significance)
2. Score all quality dimensions
3. Compute mean, median, P25, P75, P95 per dimension
4. Set minimum = P25, target = median, stretch = P75
5. Store as `BASELINES.md`
6. Refresh quarterly or after major system changes

---

## 9. Writing Rules

### Density

Follow same density principles as all standards
(→ `agent/STANDARDS.md §2–3`). Tables over prose. Measurable
over subjective.

### Specificity

Every statement evaluable. Test: can an evaluator score output
without asking for clarification?

| ✗ Vague | Specific |
|---|---|
| "Output should be high quality" | "Grounding score ≥ 0.8, zero fabricated claims" |
| "Reports should be well-structured" | "Quality badge → summary → evidence → appendices, in order" |
| "System should be fast" | "P99 < 5s standard tasks, < 30s complex" |

### Versioning

- Expectation documents use semver
- Quality dimensions additive — ✗ remove existing dimensions
- Benchmark targets can tighten, not loosen without justification
- Breaking changes documented with rationale

### Size Targets

| Type | Target | Hard cap |
|---|---|---|
| Simple domain | 200–400 lines | 600 |
| Complex domain | 400–800 lines | 1200 |

---

## 10. Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Aspirational only | "Be perfect" with no metrics | Add dimensions + benchmarks |
| No failure taxonomy | Only defines success | Define named failures with detection |
| Untestable | Quality described but not evaluable | Make every dimension scorable |
| Static benchmarks | Targets never update | Refresh quarterly from baselines |
| Missing baseline | Targets set without measurement | Run baseline protocol first |
| Single-dimension | Only accuracy, ignores honesty/completeness | 5–12 independent dimensions |
| Subjective rubric | "Good" vs "great" without behaviors | Concrete per-score descriptions |
| No recovery path | Identifies failures without remediation | Every failure needs detection + recovery |
| Expectation drift | Document says X, evaluated on Y | Review with every major release |

---

## 11. Checklist

### New Expectation Document

- [ ] Peak behavior defined — what excellence looks like
- [ ] 5–12 quality dimensions, each measurable and independent
- [ ] Grading rubric with concrete per-score descriptions
- [ ] Failure taxonomy: every known failure named with detection + recovery
- [ ] Benchmark targets: minimum / target / stretch per dimension
- [ ] Design principles: inviolable rules for this domain
- [ ] Versioned (semver)
- [ ] Every statement evaluable without asking questions

### Existing Expectation Review

- [ ] Baselines measured — targets reflect reality, not aspiration
- [ ] Benchmarks refreshed within last quarter
- [ ] Failure taxonomy complete — recent failures all named
- [ ] Quality dimensions independent — no redundancy
- [ ] Expectation tests exist for each dimension
- [ ] Composite score correlates with human judgment (r > 0.7)
