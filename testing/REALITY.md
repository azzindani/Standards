# Testing Reality Standards

> The reality dimensions a test suite must simulate — faults, adversarial input, concurrency, resource limits, time, state accumulation, drift — plus the assertions and audits that prove the suite actually catches bugs.

**ID** `testing/reality` · **Tier** Core · **Version** 1.0
**Owns** reality dimension model · fault injection · adversarial input generation technique · concurrency tests · resource-exhaustion tests · time + determinism rules · state-accumulation tests · drift + replay · observability assertions · recovery verification · mutation testing · performance-regression tests · test effectiveness audit
**Defers to** pyramid · size classes · tier classification · coverage gate · mocking · contract tests · flake budget → [STANDARDS.md](STANDARDS.md) · load · soak · chaos · survival · penetration → [PRESSURE.md](PRESSURE.md) · threat model · injection taxonomy · validation boundary → [security](../security/STANDARDS.md) · error taxonomy · error shape → [error_handling](../error_handling/STANDARDS.md) · log · metric · trace · receipt formats · SLO definitions → [observability](../observability/STANDARDS.md) · performance budgets · profiling · caching → [performance](../performance/STANDARDS.md) · pipeline stages · runners → [cicd](../cicd/STANDARDS.md) · quality bar · benchmark rubrics → [expectation](../expectation/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [PRESSURE.md](PRESSURE.md) · [observability](../observability/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Dimension Map](#2-dimension-map)
3. [Faults](#3-faults)
4. [Adversarial Inputs](#4-adversarial-inputs)
5. [Concurrency](#5-concurrency)
6. [Resources](#6-resources)
7. [Time and Determinism](#7-time-and-determinism)
8. [State Accumulation](#8-state-accumulation)
9. [Drift and Replay](#9-drift-and-replay)
10. [Observability Assertions](#10-observability-assertions)
11. [Recovery Verification](#11-recovery-verification)
12. [Mutation Testing](#12-mutation-testing)
13. [Performance Regression Tests](#13-performance-regression-tests)
14. [Effectiveness Audit](#14-effectiveness-audit)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Correctness is one dimension, ✗ the whole test | A suite proving only "right answer on good input" proves the system works on its best day |
| One pattern, every dimension | **Inject condition → assert behavior → assert recovery** (where recovery applies) |
| Deterministic injection | Faults, schedules, clocks, seeds are controlled. A nondeterministic reality test is a flaky test → [STANDARDS.md](STANDARDS.md) |
| Inject at the boundary | Conditions injected via test doubles, proxies, shims, harnesses. ✗ `if TESTING:` branches inside production code |
| Silent success is failure | Every dimension asserts the operator-visible signal, ✗ only the return value (§10) |
| Dimensions required by tier | Which dimensions a module owes is set by its tier → [STANDARDS.md](STANDARDS.md) |
| The suite is itself under test | Mutation (§12) + effectiveness audit (§14) measure whether the tests catch anything |

---

## 2. Dimension Map

| Dimension | Catches | Required from | Suite |
|---|---|---|---|
| Faults (§3) | Network blips · dependency failure · outage | L3 | Integration |
| Adversarial (§4) | Malformed input · encoding attacks · size bombs | L3 | Unit + nightly fuzz |
| Concurrency (§5) | Races · deadlocks · lost updates · ordering | L3 | Unit (race detector) + nightly stress |
| Resources (§6) | OOM · disk full · FD + pool exhaustion | L4 | Integration (with limits) + nightly leak |
| Time + determinism (§7) | Clock skew · timezone · DST · nondeterminism | L4 | Unit + lint |
| State accumulation (§8) | Memory leaks · cache poison · counter overflow | L4 | Nightly long-run |
| Drift + replay (§9) | Schema drift · dependency drift · traffic shift | L5 | Pre-merge + pre-production |
| Observability (§10) | Silent failures · missing receipts | L4 | Alongside parent test |
| Recovery (§11) | ✗ return to baseline after fault clears | L3 | Integration (paired with §3) |
| Mutation (§12) | Tests that pass but catch nothing | L5 | Nightly / weekly |
| Performance (§13) | Latency regression | L4 | Nightly |

Confidence levels (L0–L5) + per-tier requirements → [STANDARDS.md](STANDARDS.md). Which pipeline stage runs each suite → [cicd](../cicd/STANDARDS.md). System-level dimensions (pressure · survival · penetration) → [PRESSURE.md](PRESSURE.md).

---

## 3. Faults

Every external dependency fails. Test the response, ✗ hope.

| Dependency | Faults to inject |
|---|---|
| Network (HTTP · gRPC) | Timeout · connection refused · DNS failure · TLS failure · slow response · partial response · 5xx · rate limit |
| Database | Connection lost · query timeout · deadlock · constraint violation · replica lag · disk full |
| File system | Permission denied · disk full · path missing · file locked · slow I/O |
| Message queue | Publish failure · consumer crash · duplicate delivery · out-of-order · partition unavailable |
| Third-party API | Every HTTP error · malformed response · schema change · auth failure · quota exceeded |
| Cache | Miss · stale · eviction · connection lost |
| Clock | Skew · jump backward · jump forward · stop |

- Every shell function has a fault-test pair: **inject → assert structured error · clear → assert recovery (§11)**.
- Faults injected at the adapter boundary via a fault-injection layer (test double · network proxy · FS shim). ✗ flags inside production code.
- Deterministic: fault timing seeded. ✗ random fault timing in the per-commit suite.
- Naming: `fault_<dependency>_<failure_mode>_<expected_response>` → [STANDARDS.md](STANDARDS.md).
- Every fault test asserts: structured error returned (shape → [error_handling](../error_handling/STANDARDS.md)) · log emitted · metric incremented · receipt written (§10). ✗ swallow.
- Retry behavior asserted explicitly: max attempts · backoff · jitter · circuit breaker opens after threshold.
- Partial failure: half a batch succeeds, half fails → both reported. ✗ all-or-nothing reporting of a partial result.
- Coverage: T2 → every downstream dependency. T3 → every external boundary carries the full fault matrix above.

---

## 4. Adversarial Inputs

Testing technique only. Threat model · injection taxonomy · what makes an input dangerous → [security](../security/STANDARDS.md). This section owns **how to generate and assert**.

| Category | Generator produces |
|---|---|
| Malformed | Truncated · extra trailing bytes · wrong magic bytes · invalid UTF-8 |
| Boundary explosion | Empty · 1 byte · max-size · max+1 · max×2 · negative · zero · NaN · infinity |
| Encoding | Surrogate pairs · BOM · null bytes · directional override · homoglyphs |
| Injection payloads | Corpus imported from the security standard's vector list, replayed as data |
| Type confusion | String where int expected · array where object expected · null where required |
| Size attacks | Deep nesting · zip bomb · billion laughs · huge field · huge list |
| Locale | RTL · combining characters · non-ASCII whitespace · timezone edges |
| Time values | Year 2038 · year 9999 · negative epoch · leap second · DST transition |

| Target | Categories required |
|---|---|
| Parser · decoder | All |
| Validator | Boundary · type confusion · encoding · injection |
| Public API endpoint | All |
| File loader | Malformed · size · encoding |
| Query builder · template renderer | Injection (asserted impossible by construction) |

- Every input boundary has an adversarial suite. ✗ "trusted input" exemption for any public interface.
- Asserts, for every vector: ✗ crash · structured error · log emitted · ✗ resource leak · ✗ partial write left behind.
- Defenses asserted as structural (parameterized queries · escaping libraries · schema validation), ✗ regex blacklists. Test proves the structural defense holds, ✗ that one payload was blocked.
- ≥ 1 fuzz target per parser/decoder → [STANDARDS.md](STANDARDS.md).
- Adversarial corpus version-controlled under `tests/<module>/adversarial/`. Grows on every reported security issue and every incident.

---

## 5. Concurrency

Races, deadlocks, ordering, lost updates appear only under concurrent load. Tests induce them deterministically.

| Mode | Test pattern |
|---|---|
| Race | Interleaved operations → correctness for every interleaving |
| Lost update | Concurrent writes → all reflected or conflict detected |
| Stale read | Read after write → consistency model honored |
| Deadlock | Acquisition order varies → ✗ deadlock, or detection + abort |
| Livelock | Retry storm → convergence bounded |
| Ordering | Event order varies → outcome stable |
| Partial commit | Multi-step interrupted → atomic or rolled back |
| Reentrancy | Transitive self-call → correctness |

- Any code touching shared state has a concurrency test. No exemptions for "it's only called from one place".
- Deterministic tools only: race detectors · thread sanitizers · seeded schedulers · model checkers. Race detector enabled in CI wherever the toolchain provides one.
- Stress: N concurrent × M iterations → invariants hold. Production minimum: **100 concurrent × 1000 iterations**.
- Interleaving test: pause A mid-execution, run B to completion, resume A → assert correct outcome.
- Lock-free code requires stress + property tests over operation sequences.
- ✗ `sleep()` to force an ordering. Use barriers · channels · latches.
- ✗ a flaky concurrency test. Deterministic or deleted.
- Distributed systems: partition scenarios — split-brain · partial reachability · message reorder. Multi-fault combinations → [PRESSURE.md](PRESSURE.md).

---

## 6. Resources

Production runs out of memory, disk, FDs, connections, and queue space. Degrade gracefully, ✗ crash.

| Resource | Scenario |
|---|---|
| Memory | Near cap · OOM mid-operation |
| Disk | Full at write · full mid-stream · inode exhaustion |
| File descriptors | Cap reached · leak detection |
| Connections | Pool exhausted · peer limit reached |
| Queue · buffer | Full · backpressure · oldest dropped |
| CPU | Throttled · saturated · single core |
| Network | Throttled · packet loss · high latency |
| Threads · goroutines | Pool exhausted · spawn limit |

- Each boundary asserts graceful degradation: structured error · backpressure applied · circuit opens · receipt logged. ✗ uncaught exception · ✗ silent data loss.
- Limits set explicitly in the test (cgroup · ulimit · runtime flag). ✗ rely on the dev machine's defaults — they are always more generous than production.
- Leak test: N iterations → resource usage returns to baseline within a documented tolerance.
- Recovery: hit the limit → relieve it → system resumes (§11).
- Run with monitoring on — assert saturation metrics were emitted (§10).
- Sustained load to the breaking point is a different question → [PRESSURE.md](PRESSURE.md).

---

## 7. Time and Determinism

Time, timezones, ordering, and randomness are the four sources of nondeterminism. Tests control all four.

| Failure | Test |
|---|---|
| Timezone drift | Logic at every UTC offset → outcome stable |
| DST transition | Operation at spring-forward and fall-back |
| Clock skew | Inject skew → assert correctness |
| Clock jump | Forward and backward → invariants hold |
| Year boundary | Year change · 2038 · 9999 |
| Leap second | Where the platform exposes it |
| TTL expiry | Stale cache handled |
| Token expiry | Exactly at expiry · one tick past |

### Determinism rules — production code

- ✗ read the wall clock without injection. Time arrives as an argument | an injected clock.
- ✗ generate randomness without injection. Source injected, seeded in tests.
- ✗ generate UUIDs without injection. Source injected.
- ✗ depend on map/dict iteration order where order matters. Sort, or use an ordered structure.
- ✗ floating-point equality. Compare with an epsilon whose tolerance is documented.
- Violations are **lint-time errors**, ✗ runtime surprises. Lint wiring → [cicd](../cicd/STANDARDS.md).

### Determinism rules — test code

- Frozen clock by default. Time advances only via an explicit `advance(duration)` call.
- Seeded random. Seed printed on failure.
- Canonical ordering asserted — sort before compare where order is incidental.
- Random test order run regularly to catch hidden ordering dependencies → [STANDARDS.md](STANDARDS.md).

---

## 8. State Accumulation

Long-running processes leak. Short tests never see it. Catch slow-burn failure before production does.

| Failure | Test |
|---|---|
| Memory leak | N iterations → RSS returns to baseline within tolerance |
| FD leak | N iterations → FD count stable |
| Connection leak | N iterations → pool size stable |
| Cache poison | Bad value persists past TTL → detected or evicted |
| Counter overflow | Counter at max, +1 → wraparound handled |
| Log flood | Repeated error → log rate-limited |
| State drift | Periodic snapshot → invariants hold |
| Task pileup | Long scheduled run → backlog bounded |

- Long-run test: **N ≥ 1000 iterations | M ≥ 1 h wall time**, sampled periodically.
- Nightly suite, ✗ per-commit — it will never fit the commit budget.
- Baseline captured from a clean start. Tolerance documented per resource. ✗ an undocumented "looks fine" threshold.
- Failures investigated within **7 days**. ✗ tolerated indefinitely — a leak is a scheduled outage.
- Every cache has an eviction test + a size-bound assertion. Every counter has an overflow test.
- Accumulation *under active sustained load* → [PRESSURE.md](PRESSURE.md).

---

## 9. Drift and Replay

Schemas, dependencies, and traffic shift under a system that has not changed. Replay catches drift before users do.

| Drift source | Detection |
|---|---|
| Schema | Schema diff against migration history, every migration |
| API contract | Contract test against the published spec → [STANDARDS.md](STANDARDS.md) |
| Dependency | Lock-file diff + behavior test on every update |
| Traffic pattern | Replay production traces against the new build |
| Data distribution | Property tests over production-shaped samples |
| Config | Cross-environment config comparison |

- L5 production-tier maintains a replay corpus. Captured anonymized — **PII scrubbed at capture, ✗ at replay**. The scrubber itself is tested.
- Corpus refreshed weekly · **≥ 1000 representative requests** · version-controlled in a separate large-object store.
- Replay runs in a pre-production environment. ✗ replay against production.
- Replay asserts no regression in behavior, latency, or error rate versus the previous build.
- Replay failure blocks promotion. Dependency drift triggers the full suite + a replay run.

---

## 10. Observability Assertions

Tests assert on emitted signals, ✗ only on return values. A silent failure is an uncaught bug that reaches a user first. Signal **format** (field names · levels · metric types · receipt schema) → [observability](../observability/STANDARDS.md). This section owns **that you assert, and on what**.

| Signal | Asserted on |
|---|---|
| Structured log | Every error path · every state change |
| Metric | Every outcome — success · failure · retry · fallback |
| Trace span | Every external call · every async boundary |
| Receipt | Every business-meaningful action |
| Event | Every documented domain event |

- Contract tests carry an observability contract: documented signals on documented events → [STANDARDS.md](STANDARDS.md).
- Error path asserts all three: structured log · metric incremented · receipt written.
- Retry path asserts: retry log · retry metric · backoff observable.
- Fault tests (§3) assert the degradation is visible to an operator **before** it is visible to a user.
- ✗ assert on log message prose — it is not a contract. Assert on structured fields (level · code · the field values that encode behavior).
- Receipt assertion pattern: operation runs → receipt exists with operation id · input hash · output hash · timestamp · status → retrievable by the documented path → survives restart.

---

## 11. Recovery Verification

Every fault test pairs with a recovery test. Injecting a fault and asserting an error proves half the system.

| Condition cleared | Recovery asserted |
|---|---|
| Network restored | Pending operations resume, or retry succeeds |
| DB back online | Pool reconnects, queries resume |
| Disk freed | Writes resume, queue drains |
| Dependency back up | Circuit closes, traffic resumes |
| Load drops | Throttling lifts, backpressure clears |
| Process restarted | State recovered from durable store · ✗ data loss |

- Paired with the §3 fault test: same scenario, fault cleared mid-test.
- Asserts: metrics return to baseline · pending work completes · ✗ data loss · ✗ duplicate work.
- Crash recovery, required for every durable-state operation: kill mid-operation → restart → state consistent.
- Idempotency verified — a retry ✗ duplicates the effect.
- Recovery time bounded by the documented SLO (SLO definition → [observability](../observability/STANDARDS.md)).
- Recovery from *chained* dependency loss → [PRESSURE.md](PRESSURE.md).

---

## 12. Mutation Testing

The coverage-quality check: a mutator alters the code (flip an operator · delete a statement · change a constant) → run the tests → the mutant is **killed** if a test fails, **survives** if every test still passes. A surviving mutant is a hole in the suite that branch coverage cannot see.

| Mutator | Detects |
|---|---|
| Conditional flip (`==`→`!=`, `<`→`<=`) | Branch assertions that assert nothing |
| Constant replacement | Hardcoded values never checked |
| Statement deletion | Dead code · untested side effect |
| Return-value swap | Untested return path |
| Boundary shift | Off-by-one |
| Logical operator swap | Logic gaps |

- Score = killed / generated (equivalent mutants excluded). Target **≥ 80% for T0–T1** at production tier. L5 gate: T0 90% · T1 80% → [STANDARDS.md](STANDARDS.md).
- Nightly | weekly. ✗ per-commit — mutation runs are minutes-to-hours.
- Surviving mutant → add a test | mark equivalent with a recorded reason | delete the unreachable code. ✗ leave it unclassified.
- High branch coverage with a low mutation score = a suite that executes code and asserts nothing. Mutation score is the arbiter, coverage % is not.
- Prototype scale: optional, spot-check critical modules only.

---

## 13. Performance Regression Tests

Per-operation timing assertions. ✗ load testing (→ [PRESSURE.md](PRESSURE.md)). Budget **values**, profiling method, and optimization rules → [performance](../performance/STANDARDS.md); this section owns how a budget becomes a test.

| Add a perf test | ✗ Skip |
|---|---|
| Operation has an SLA | Internal utility with no timing requirement |
| User-visible latency | One-time migration script |
| Past regression | Stable, constant-time operation |
| Cost scales with input size | Constant-time operation |

- Budget stated explicitly per operation: `operation X < N ms at input size M`. Per-operation, ✗ an aggregate suite time.
- Wall clock measured on consistent hardware (a CI runner, ✗ a laptop). ✗ compare a number across hardware classes.
- Separate suite — perf tests never slow the per-commit run. Nightly.
- Baseline tracked over time. **Regression > 20% from baseline = failing test**, ✗ a warning.
- Budget breach = failing test. Raising a budget requires a recorded decision, ✗ an edit.

Reference shape — authoritative budgets live in [performance](../performance/STANDARDS.md):

| Operation | Input | Budget |
|---|---|---|
| Parse config | 100 entries | < 50 ms |
| Validate batch | 1000 records | < 200 ms |
| Transform dataset | 10K rows | < 1 s |
| Full pipeline | Reference input | < 5 s |

---

## 14. Effectiveness Audit

The suite is a hypothesis: "these tests catch the bugs that matter." The audit tests the hypothesis against reality.

| Input | Source |
|---|---|
| Production incidents | Incident tracker, trailing quarter |
| Customer-reported bugs | Support tracker |
| Hotfix commits | Git history |
| Rollbacks | Deploy log |
| Surviving mutants (§12) | Mutation report |

Procedure, in order:

1. Per incident, ask: which test type *would have* caught this?
2. Classify: **gap** (test type missing) · **flaw** (test exists, ineffective) · **architecture** (code untestable as written).
3. Act: add the test · strengthen the assertion · refactor for testability.
4. Track which dimension caught the most real bugs → invest there next quarter.
5. Feed anonymized incident inputs into the adversarial corpus (§4) and the replay corpus (§9).

- Production-tier: audit quarterly, mandatory. Small projects: annually.
- Findings become test-debt items, prioritized alongside features. ✗ a document nobody reads.
- ✗ blame retrospective. Gap-finding only.
- A new class of incident → this standard gets a new required test type. The standard is self-improving or it is stale.
- Audit result verifies the project's claimed confidence level → [STANDARDS.md](STANDARDS.md). An unaudited L4 claim is an L2 suite with ambition.

---

## 15. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Faults (§3) | ✗ required | Every critical dependency | Every external boundary · full matrix |
| Adversarial (§4) | ✗ required | Every public API | Every input boundary · corpus grown on incidents |
| Concurrency (§5) | ✗ required | All shared-state code | + race detector in CI · 100 × 1000 stress |
| Resources (§6) | ✗ required | Every T3 boundary | All boundaries + nightly leak run |
| Time (§7) | Best effort | Clock injected · lint enforced | Full matrix: skew · DST · jump · year boundary |
| State accumulation (§8) | ✗ required | Caches + pools | Nightly long-run, N ≥ 1000 · 1 h |
| Drift + replay (§9) | ✗ required | Schema diff per migration | Full replay corpus, weekly refresh |
| Observability (§10) | ✗ required | Error paths assert signals | Every path asserts signals |
| Recovery (§11) | ✗ required | Paired with critical faults | Paired with every fault |
| Mutation (§12) | Spot-check | T0–T1 ≥ 80% | Gates release at L5 |
| Performance (§13) | ✗ required | Critical operations | Full budget table · nightly baseline |
| Audit (§14) | ✗ required | Annual | Quarterly |

Priority order when adding dimensions: faults → adversarial → concurrency → observability → recovery → resources → state → replay → mutation. ✗ skip to mutation testing while faults go untested.

---

## 16. Checklist

- [ ] Every shell function has a fault test paired with a recovery test (§3, §11)
- [ ] Faults injected at the adapter boundary, ✗ via flags in production code (§3)
- [ ] Fault tests assert structured error + log + metric + receipt (§3, §10)
- [ ] Retry behavior asserted: max attempts · backoff · jitter · circuit breaker (§3)
- [ ] Every input boundary has an adversarial suite · no "trusted input" exemptions (§4)
- [ ] Adversarial corpus version-controlled and grown on every incident (§4)
- [ ] Every shared-state path has a deterministic concurrency test · race detector on in CI (§5)
- [ ] Production stress meets 100 concurrent × 1000 iterations (§5)
- [ ] Resource limits set explicitly in tests, ✗ inherited from the dev machine (§6)
- [ ] Leak tests return every resource to baseline within a documented tolerance (§6, §8)
- [ ] No wall clock, randomness, or UUID generation without injection — enforced by lint (§7)
- [ ] Tests run on a frozen clock and a seeded RNG; seed printed on failure (§7)
- [ ] Long-run test at N ≥ 1000 iterations | 1 h runs nightly (§8)
- [ ] Replay corpus ≥ 1000 requests, PII scrubbed at capture, refreshed weekly (§9)
- [ ] Replay runs pre-production and blocks promotion on regression (§9)
- [ ] Error and retry paths assert emitted signals, ✗ log prose (§10)
- [ ] Crash-mid-operation → restart → state consistent, for every durable-state operation (§11)
- [ ] Mutation score ≥ 80% for T0–T1 · surviving mutants classified (§12)
- [ ] Performance budgets stated per operation · regression > 20% fails the build (§13)
- [ ] Effectiveness audit run on schedule · findings tracked as test debt (§14)
- [ ] Each incident this quarter classified gap | flaw | architecture (§14)
