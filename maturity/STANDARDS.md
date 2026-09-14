# Maturity Standards

> How much of a system is actually proven: the levels of proof, what each level demands, and the rule that evidence reaching an agent arrives as numbers.

**ID** `maturity` · **Tier** Core · **Version** 1.0
**Owns** maturity levels · proof-breadth model · level entry criteria · numeric-evidence rule · motion + spatial metric set · resource + efficiency metric set · evidence artifact policy · maturity reporting
**Defers to** test pyramid · size classes · coverage gate · mocking → [testing](../testing/STANDARDS.md) · reality dimensions · faults · drift → [testing/REALITY.md](../testing/REALITY.md) · load · soak · chaos · survival → [testing/PRESSURE.md](../testing/PRESSURE.md) · log · metric · trace format · SLOs → [observability](../observability/STANDARDS.md) · budgets · profiling · optimization → [performance](../performance/STANDARDS.md) · environment topology · promotion mechanics · containers → [devops](../devops/STANDARDS.md) · stage definitions · runners → [cicd](../cicd/STANDARDS.md) · quality bar · comparator model → [expectation](../expectation/STANDARDS.md) · unit taxonomy · reuse → [primitives](../primitives/STANDARDS.md)
**Load with** [testing](../testing/STANDARDS.md) · [observability](../observability/STANDARDS.md) · [expectation](../expectation/STANDARDS.md)

---

## Table of Contents

1. [Proof Model](#1-proof-model)
2. [Levels](#2-levels)
3. [Level Entry Criteria](#3-level-entry-criteria)
4. [Numeric Evidence Rule](#4-numeric-evidence-rule)
5. [Motion and Spatial Metrics](#5-motion-and-spatial-metrics)
6. [Resource and Efficiency Metrics](#6-resource-and-efficiency-metrics)
7. [Evidence Artifacts](#7-evidence-artifacts)
8. [Baselines and Regression](#8-baselines-and-regression)
9. [Reporting](#9-reporting)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Proof Model

Maturity = **breadth of proof**, ✗ percentage of one proof.

| Claim | Status |
|---|---|
| Coverage percentage | One measurement at one level. Necessary, ✗ sufficient |
| Test count | ✗ evidence. A thousand tests of one dimension prove one dimension |
| Breadth of conditions survived | The measurement that tracks maturity |

A system at 95% coverage with unit tests only is less proven than one at 70% that has survived load, chaos, and evaluation against real data. Coverage measures lines executed; maturity measures conditions survived.

Rules:

- Maturity is computed from evidence present, ✗ declared by the team.
- Absent evidence = level not reached. A skipped dimension is never assumed to pass.
- Level is a floor, ✗ a badge: reaching level 4 requires every level 0–3 criterion still passing.
- A regression that removes evidence lowers the level. Levels move both directions.

---

## 2. Levels

Six levels. Each adds a class of condition the previous could not see.

| Level | Name | Proof present | Blind to |
|---|---|---|---|
| 0 | Compiles | Build · lint · format · type check | Everything behavioral |
| 1 | Unit-proven | Unit tests · coverage gate | Integration · environment · real data |
| 2 | Assembled | Container builds · services start · integration tests pass | User-facing behavior · appearance |
| 3 | Observed | E2E · endpoint contract · visual · accessibility · real fixtures | Behavior under pressure |
| 4 | Pressured | Load · stress to failure · chaos · evaluation against real data | Timing · responsiveness · resource cost |
| 5 | Measured | Motion + latency + resource metrics captured, budgeted, enforced | — |

Level 5 is not "finished". It is the level at which regressions in timing and cost are caught by the same mechanism that catches logic regressions.

---

## 3. Level Entry Criteria

Entry is evidence-based. Each row is verifiable by an automated check.

| Level | Required evidence |
|---|---|
| 0 | Build succeeds · linter clean · formatter clean · type check clean |
| 1 | Unit suite green · coverage at or above the gate → [testing](../testing/STANDARDS.md) |
| 2 | Image builds from a clean context · services reach healthy · integration suite green |
| 3 | E2E suite green · every declared endpoint exercised for status + schema · visual baseline recorded · accessibility check clean · fixtures derived from real data with secrets stripped |
| 4 | Load profile executed · stress run recorded the failure point, ✗ only a pass at target · chaos scenarios survived → [testing/PRESSURE.md](../testing/PRESSURE.md) · evaluation suite scored against real data |
| 5 | Motion metrics (§5) captured with a committed baseline · resource metrics (§6) captured · budgets enforced in the pipeline · comparison runs on every change |

Rules:

- A level requires **all** rows, ✗ a majority.
- Evidence older than the current commit's dependency set is stale for levels 4–5; re-capture, ✗ carry forward.
- A gate that is configured but never executed provides no evidence.
- Stress that only confirms a target load was met is incomplete: level 4 requires the breaking point, ✗ the pass mark.

---

## 4. Numeric Evidence Rule

Evidence consumed by an automated reviewer — an agent, a gate, a diff — arrives as numbers with units.

Rationale is capability, ✗ preference: models reason over static 2D input. Video and animation cannot be read frame-accurately at acceptable cost, so any property that lives in motion is reduced to scalars before it reaches the reviewer.

| Evidence form | Role |
|---|---|
| Scalar with unit | Primary. Comparable · thresholdable · diffable |
| Structured record of scalars | Primary. A time series is a list of scalars |
| Screenshot · video · trace file | Supporting artifact only. Referenced by a finding, ✗ the finding |
| Prose description of behavior | ✗ evidence. Unmeasurable, uncomparable |

Rules:

- Every metric carries an explicit unit. A bare number is ✗ a measurement.
- Every metric carries the capture conditions: hardware class · concurrency · dataset size · build profile. A number without conditions is uncomparable.
- Comparisons are numeric. "Looks smoother" is ✗ a result.
- A property that cannot be reduced to a number is recorded as an open gap, ✗ asserted as passing.
- Reduction is transport-neutral: the same metric set describes a browser frame, a rendered scene, and a physical actuator. Capture backends differ; the schema ✗ change.

Spatial and 3D properties follow the same reduction — position · displacement · velocity · angle · depth are scalars. A reviewer that cannot see a scene can still reason about its numbers.

---

## 5. Motion and Spatial Metrics

Minimum set for any system with visible movement, animation, or interactive response.

| Metric | Unit | Meaning |
|---|---|---|
| `frame_interval_p50` · `_p95` · `_p99` | ms | Time between presented frames |
| `frames_dropped` | count | Frames missed against the target interval |
| `jank_events` | count | Intervals exceeding twice the target |
| `input_latency_p50` · `_p95` · `_p99` | ms | Input event to visible response |
| `time_to_first_paint` | ms | Navigation to first pixel |
| `time_to_interactive` | ms | Navigation to input responsiveness |
| `layout_shift_cumulative` | unitless | Unexpected positional movement |
| `animation_duration_actual` | ms | Measured, compared against declared |

Spatial extension, when the system renders or controls a scene:

| Metric | Unit | Meaning |
|---|---|---|
| `displacement_per_frame` | units | Movement magnitude between frames |
| `velocity_p95` | units/s | Peak sustained movement rate |
| `angular_error` | degrees | Deviation from intended orientation |
| `depth_error` | units | Deviation from intended depth placement |
| `trajectory_deviation` | units | Distance from the intended path |

Rules:

- Target interval is declared, ✗ inferred. 60 fps → 16.7 ms; the budget references the declaration.
- Percentiles are required for latency and interval. A mean conceals exactly the stalls users notice.
- Capture runs at a declared hardware class. Cross-class comparison is invalid.
- Missing metric = missing evidence for level 5, ✗ a zero.

---

## 6. Resource and Efficiency Metrics

Minimum set for cost and headroom. Format and collection → [observability](../observability/STANDARDS.md) · budgets and thresholds → [performance](../performance/STANDARDS.md).

| Metric | Unit | Meaning |
|---|---|---|
| `cpu_seconds` | s | Processor time consumed by the unit of work |
| `memory_peak` | MB | Peak resident set |
| `disk_read` · `disk_write` | MB | Volume moved |
| `network_in` · `network_out` | MB | Volume transferred |
| `wall_time` | ms | Elapsed time for the unit of work |
| `work_per_cpu_second` | units/s | Throughput per unit of processor time |
| `cost_per_request` | currency | Where infrastructure cost is attributable |

Throttled capture is required at level 5: the same workload under constrained CPU, constrained memory, and constrained network. A system measured only on unconstrained hardware has unknown behavior on the hardware users have.

Rules:

- Resource metrics are captured per stage, ✗ only for the whole run. A whole-run number cannot locate a regression.
- Constraint levels are declared and stable across runs, else comparison is invalid.
- Efficiency is a ratio, ✗ an absolute. Raw speed improvement with worse throughput per unit resource is a regression.

---

## 7. Evidence Artifacts

| Artifact | Retention | Purpose |
|---|---|---|
| Metric record (scalars + conditions) | Permanent, versioned with the commit | The evidence |
| Committed baseline | Permanent, one per environment per route | The comparison target |
| Screenshot · video · trace | Until the next green run on that route | Diagnosis after a numeric failure |
| Raw capture logs | Until the metric record is written | Intermediate |

Rules:

- The metric record is committed | stored in the project's own store. An artifact that exists only in a CI run is ✗ evidence.
- Supporting artifacts are referenced by the metric record, ✗ the reverse.
- Secrets discovered in captured traffic, fixtures, or logs are removed before the record is written, ✗ afterwards.
- Fixtures derived from real data record their derivation and their stripping step.
- An artifact that cannot be reproduced by re-running the declared capture is ✗ evidence.

---

## 8. Baselines and Regression

| Rule | Detail |
|---|---|
| Baseline scope | One per environment per route per hardware class. A single global baseline is meaningless |
| Baseline creation | Explicit action, ✗ automatic on first run. An accidental baseline encodes a bad state as correct |
| Comparison | Every change compares against the baseline for its environment |
| Budget | Declared per metric as an absolute threshold | a percentage delta. Both may apply |
| Failure | Exceeding a budget fails the gate. ✗ warn-only for level 5 |
| Baseline move | Deliberate, reviewed, and recorded with the reason. ✗ move a baseline to clear a red gate |
| Noise | A metric whose run-to-run variance exceeds its budget is ✗ usable as a gate — widen the budget | stabilize the capture, and record which |

Regression direction is declared per metric. Lower is better for latency; higher is better for throughput. A gate that does not know the direction cannot fail correctly.

---

## 9. Reporting

Every maturity report answers three questions, in this order.

| Question | Content |
|---|---|
| What level is this system at? | Single integer 0–5, computed from evidence present |
| What is missing for the next level? | The specific rows of §3 with no evidence |
| What regressed? | Metrics outside budget, with the delta and the baseline they were compared against |

Rules:

- The level is computed, ✗ asserted. A report claiming a level without the evidence rows is invalid.
- Missing evidence is named specifically. "More testing needed" is ✗ a finding; "no chaos scenarios executed" is.
- A report is machine-readable first, rendered second. The consumer is an automated reviewer.
- Level, gaps, and regressions are reported every run, ✗ on request. A maturity number nobody sees changes nothing.

---

## 10. Anti-Patterns

| Anti-pattern | Symptom | Correction |
|---|---|---|
| Coverage as maturity | High percentage, one test class | Measure breadth (§1) |
| Declared level | Team asserts a level with no evidence rows | Compute from evidence (§9) |
| Mean-only latency | Averages reported, stalls invisible | Report percentiles (§5) |
| Video as evidence | A recording attached as the result | Reduce to scalars; recording is supporting (§4) |
| Unconditioned number | Metric with no hardware class or dataset size | Record capture conditions (§4) |
| Accidental baseline | First run silently becomes the target | Baseline creation is explicit (§8) |
| Baseline laundering | Baseline moved to clear a red gate | Move deliberately, with a recorded reason (§8) |
| Pass-mark stress | Load test confirms the target, never finds the limit | Stress to failure, record the breaking point (§3) |
| Unconstrained-only capture | Measured on fast hardware only | Capture throttled (§6) |
| Absolute-only efficiency | Faster but costlier accepted as an improvement | Efficiency is a ratio (§6) |
| Warn-only gate | Budget exceeded, build green | Level 5 budgets fail (§8) |
| Stale evidence | Level 5 claimed on metrics from an older dependency set | Re-capture (§3) |

---

## 11. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Required level | 1 | 3 | 5 |
| Motion metrics | Optional | Captured on primary routes | Captured on every route · budgeted |
| Resource metrics | Optional | Captured per stage | Per stage · throttled · efficiency ratios |
| Baseline scope | None | Per environment | Per environment · per route · per hardware class |
| Budget enforcement | None | Warn | Fail |
| Evidence retention | Latest run | Versioned with the commit | Versioned · reproducible · audited |
| Stress requirement | None | Target load confirmed | Breaking point recorded |
| Real-data evaluation | None | Fixtures from real data | Scored evaluation suite |
| Report cadence | On request | Every pipeline run | Every run · level regression blocks merge |

---

## 12. Checklist

- [ ] Maturity level is computed from evidence present, never asserted
- [ ] Every level 0–N criterion still passes, not only the newest level's
- [ ] Absent evidence is treated as level not reached, never as a pass
- [ ] Every metric carries an explicit unit
- [ ] Every metric carries its capture conditions — hardware class, concurrency, dataset size, build profile
- [ ] No comparison rests on a prose description of behavior
- [ ] Screenshots, video, and traces appear only as supporting artifacts, never as the finding
- [ ] Motion metrics report percentiles for latency and frame interval, not means
- [ ] Target frame interval is declared, not inferred
- [ ] Spatial properties, where present, are reduced to scalars
- [ ] Resource metrics are captured per stage, not only per run
- [ ] Throttled capture exists at level 5
- [ ] Efficiency is reported as a ratio, not an absolute
- [ ] Stress runs record the breaking point, not only a pass at target
- [ ] Fixtures from real data record their derivation and secret-stripping step
- [ ] Secrets found in captures are removed before the metric record is written
- [ ] Every metric record is reproducible by re-running its declared capture
- [ ] Baselines are scoped per environment, route, and hardware class
- [ ] Baseline creation is an explicit action, never automatic on first run
- [ ] No baseline was moved to clear a failing gate
- [ ] Every gated metric declares its regression direction
- [ ] No metric with variance exceeding its budget is used as a gate
- [ ] Level 5 budget violations fail the build rather than warn
- [ ] Every report names missing evidence specifically
- [ ] Level, gaps, and regressions are reported on every run
