# Testing Standards

Rules for testing all projects, all languages. Goal: tests so realistic
that CI green = ship-confident. Verifies not just that code is wired
correctly, but that the system survives the conditions of reality —
faults, adversaries, concurrency, resource limits, time, drift.

Pairs with `cicd/STANDARDS.md` — every reality dimension here names which
CI/CD stage runs it; every CI/CD stage names which dimension it gates.
Extends with `testing/PRESSURE.md` — system-level stress, endurance,
survival, and penetration testing for production-tier projects.

Composable with: Architecture · Code Writing · Error Handling ·
Observability · Security · Dependencies · language-specific standards.

---

## Table of Contents

1. [Confidence Ladder](#1-confidence-ladder)
2. [Two Spines: Pyramid + Reality](#2-two-spines-pyramid--reality)
3. [Test Pyramid](#3-test-pyramid)
4. [Test Classification by Tier](#4-test-classification-by-tier)
5. [Unit Test Rules](#5-unit-test-rules)
6. [Integration Test Rules](#6-integration-test-rules)
7. [E2E + Scenario Tests](#7-e2e--scenario-tests)
8. [Contract Tests](#8-contract-tests)
9. [Property-Based + Fuzzing](#9-property-based--fuzzing)
10. [Reality Dimension: Faults](#10-reality-dimension-faults)
11. [Reality Dimension: Adversarial Inputs](#11-reality-dimension-adversarial-inputs)
12. [Reality Dimension: Concurrency](#12-reality-dimension-concurrency)
13. [Reality Dimension: Resources](#13-reality-dimension-resources)
14. [Reality Dimension: Time + Determinism](#14-reality-dimension-time--determinism)
15. [Reality Dimension: State Accumulation](#15-reality-dimension-state-accumulation)
16. [Reality Dimension: Drift + Replay](#16-reality-dimension-drift--replay)
17. [Observability Assertions](#17-observability-assertions)
18. [Recovery Verification](#18-recovery-verification)
19. [Mutation Testing](#19-mutation-testing)
20. [Test Naming + Organization](#20-test-naming--organization)
21. [Mocking Rules](#21-mocking-rules)
22. [Coverage Strategy](#22-coverage-strategy)
23. [Test Data](#23-test-data)
24. [Test Independence](#24-test-independence)
25. [Performance Tests](#25-performance-tests)
26. [Cross-Platform Tests](#26-cross-platform-tests)
27. [Test Effectiveness Audit](#27-test-effectiveness-audit)
28. [Scale Matrix](#28-scale-matrix)
29. [Testing Checklist](#29-testing-checklist)

---

## 1. Confidence Ladder

Test suite composition → deployment confidence. Makes "CI green = ship" an explicit contract per tier.

| Level | Suite Includes | Deployment Stance |
|---|---|---|
| L0 — Smoke | Manual run-through | Local only · ✗ ship |
| L1 — Wired | Unit + happy-path integration | Internal demo |
| L2 — Correct | + Contract + property + edges | Dev |
| L3 — Robust | + Faults + adversarial + concurrency | Staging |
| L4 — Real | + Resources + time + state + observability | Production with monitoring |
| L5 — Self-evident | + Mutation + replay + drift | Production, ship without manual review |

### Rules

- Every project declares target level (`.confidence-level` file | pipeline config).
- Pipeline gates by declared level (`cicd/STANDARDS.md §5`). ✗ deploy beyond level until tests added.
- Production-tier targets L4 min. L5 for systems where bug = revenue/data/trust loss.
- Level ratchets — ✗ decrease without explicit review.
- Claim verifies against §27 Effectiveness Audit.

---

## 2. Two Spines: Pyramid + Reality

Tests classified on two orthogonal axes: **Pyramid** (size of unit under test, §3–§9) · **Reality** (real-world condition simulated, §10–§18). Every meaningful test sits at one (pyramid, reality) cell.

### Reality Dimension Map

| Dimension | Catches | Required Level | Pipeline Suite |
|---|---|---|---|
| Correctness (§3–§9) | Logic bugs, contract drift, edges | L1 | Unit + Integration |
| Faults (§10) | Network blips, dep failures, outages | L3 | Integration |
| Adversarial (§11) | Malformed input, fuzz, encoding attacks | L3 | Unit + Nightly fuzz |
| Concurrency (§12) | Races, deadlocks, ordering | L3 | Unit (race detector) + Nightly stress |
| Resources (§13) | OOM, disk full, FD exhaustion | L4 | Integration (with limits) + Nightly leak |
| Time + Determinism (§14) | Clock skew, timezone, nondeterminism | L4 | Unit + Lint |
| State Accumulation (§15) | Memory leaks, cache poison, drift | L4 | Nightly long-run |
| Drift + Replay (§16) | Schema drift, traffic shifts | L5 | Pre-merge + Pre-prod |
| Observability (§17) | Silent failures, missing receipts | L4 | Alongside parent test |
| Recovery (§18) | ✗ recover after fault clears | L3 | Integration (paired with §10) |
| Mutation (§19) | Tests pass but ✗ catch bugs | L5 | Nightly | Weekly |

Every reality dimension test pattern: **Inject condition → assert behavior → assert recovery (where applicable)**.

Pipeline mapping → suite to CI/CD stage: see `cicd/STANDARDS.md §5` (Test Stage). Cross-platform matrix: see `cicd/STANDARDS.md §15`. Lint-time determinism enforcement: see `cicd/STANDARDS.md §3`.

### System-Level Reality Dimensions

Three additional dimensions live in `testing/PRESSURE.md` because they require dedicated infrastructure and run differently from per-commit tests:

| Dimension | Catches | Required Level |
|---|---|---|
| Pressure (`PRESSURE.md §3`) | Capacity limits · slow-burn under load · scaling cliff | L4 |
| Survival (`PRESSURE.md §4`) | Multi-fault · cascading · region loss · chaos | L4–L5 |
| Penetration (`PRESSURE.md §5`) | Auth bypass · privilege escalation · exfil paths · logic flaws | L3+ |

---

## 3. Test Pyramid

| Layer | Proportion | Speed | Scope |
|---|---|---|---|
| Unit | 70% | < 10ms each | Single function, single path |
| Integration | 20% | < 500ms each | Module/tier boundary |
| E2E + Scenario | 10% | < 5s each | Full user-facing workflow |

- Pyramid inverts = architecture problem. Too many E2E = logic buried in I/O.
- Bug fix adds test at lowest possible layer. Unit > integration > E2E.
- Flaky test deleted | fixed in 24h. ✗ skip · ✗ retry-3-times · ✗ indefinite quarantine.
- Suite budget: unit < 5 min · integration + E2E adds < 10 min · total < 15 min.
- Reality tests live across pyramid layers — fault test can be unit (in pure code) or integration (at adapter boundary).

---

## 4. Test Classification by Tier

Maps to architecture tier model (`architecture/STANDARDS.md §2`).

| Tier | What | Test Type | I/O |
|---|---|---|---|
| 0 — Kernel | Types · constants · pure utilities | Unit | ✗ Never |
| 1 — Engine | Domain logic · transforms · validators | Unit | ✗ Never |
| 2 — Service | Orchestration · composition · workflow | Unit + Integration | ✗ Never (inject fakes) |
| 3 — Interface | Adapters · CLI · API · file/net/DB | Integration + E2E | Yes — sandboxed |

### Required Reality Dimensions per Tier

| Dimension | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| Correctness | ✓ | ✓ | ✓ | ✓ |
| Adversarial | ✓ if parser/validator | ✓ | ✓ | ✓ |
| Concurrency | — | ✓ if mutable | ✓ if orchestrates | ✓ if shared resource |
| Faults | — | — | ✓ | ✓ |
| Resources | — | — | ✓ if buffers/caches | ✓ |
| Time | ✓ if time-dep | ✓ if time-dep | ✓ | ✓ |
| State accumulation | — | — | ✓ if caches | ✓ if connections/pools |
| Observability | — | — | ✓ | ✓ |
| Recovery | — | — | ✓ | ✓ |

### Function Type → Strategy

Per `architecture/STANDARDS.md §4` — every function is logic | shell.

- **Logic** (T0–T2): direct call, data in → data out. ✗ mocks.
- **Shell** (T3): sandboxed I/O. Mock only outside-project services.

---

## 5. Unit Test Rules

Single function · single scenario · single assertion target.

| Allowed | ✗ Forbidden |
|---|---|
| Call function with arguments | File system access |
| Assert return value | Network calls |
| Assert error structure | Database queries |
| Assert emitted events/logs (§17) | Shared mutable state |
| Test boundary values | Sleeping / waiting on wall clock |

### Rules

- Each test creates own input. ✗ rely on data from another test.
- Run in any order → same results. ✗ global setup mutating shared state.
- T0–T1: ✗ mocks. If needed, function has design problem (`architecture/STANDARDS.md §4`).
- T2: hand-written fakes for lower-tier interfaces. ✗ mock libraries. T3: see §21.

| Target | Priority |
|---|---|
| T0 utilities | Every function, every edge |
| T1 domain logic | Every public function, all branches |
| T1 validators | Valid · invalid · boundary · adversarial (§11) |
| T1 transforms | Empty · single · many · malformed |
| T2 orchestration | Happy · error accumulation · partial failure · fault injection (§10) |

---

## 6. Integration Test Rules

Components work together across boundaries.

| Boundary | Example |
|---|---|
| Tier | T3 adapter calls T2 service with real wiring |
| Module | A's public API consumed by B |
| Data format | Serialization → deserialization round-trip |
| External resource | Real FS, test DB, sandboxed HTTP |

| Component | Approach |
|---|---|
| Own DB / FS / modules | Real — test instance, wipe/temp/clean between |
| Third-party APIs · external services | Mock at adapter boundary, deterministic |
| Time/clock | Inject (§14) |
| External faults | Fault-injection layer (§10) |

### Rules

- Test contract between components, ✗ internal implementation.
- One boundary per test. ✗ duplicate unit coverage — unit covers logic, integration covers wiring.
- Sandboxed resources fresh per test | suite. ✗ shared test DBs across parallel runs.
- External-service tests in separate suite, marked.
- Boundary pattern per public API: valid → output · invalid → structured error · boundary (empty · max · unicode · null-equiv) → graceful · fault during call (§10) → error + recovery path.

---

## 7. E2E + Scenario Tests

E2E: full workflow entry-to-output. Scenario: realistic data distributions + multi-step journeys. Together close "tests pass, production breaks" gap.

| Test | Purpose |
|---|---|
| E2E | Single user-level operation end-to-end |
| Scenario | Multi-step journey, realistic data, timing, branching |

| Write | ✗ Skip |
|---|---|
| Critical user workflow | Internal utilities |
| Revenue/data-loss path | Display variations |
| Multi-module orchestration | Already covered by unit + integration |
| Production-incident regression | Exploratory one-offs |

### Rules

- Max 20 E2E per project. More → push logic down.
- E2E budget: < 5s. Exceeding = redesign.
- Fully assembled system, sandboxed externals. ✗ E2E against production.
- Verify observable output (files · API responses · stdout · emitted events) + observability (§17). ✗ internal state.
- Scenarios: 3–10 steps with realistic timing · production-shaped data distributions · branching (success · validation fail · timeout · retry) · named per journey (`scenario_new_user_first_purchase_with_discount`) · min 1 per critical workflow · nightly suite.
- Structure: **Arrange → Act → Assert → Cleanup**. Cleanup runs even on failure.

---

## 8. Contract Tests

Lock public API behavior. Survive refactors — internal restructuring ✗ breaks contract tests.

| Target | Assertion |
|---|---|
| Signature | Declared input/output types |
| Behavior | Specific input → specific output |
| Error contract | Invalid → structured error, ✗ crash |
| Absence | Missing → explicit absence, ✗ null |
| Idempotency | Same input twice → same output (`architecture/STANDARDS.md §4`) |
| Observability contract | Documented signals on documented events (§17) |
| Fault contract | Documented response (timeout · retry · fallback) (§10) |

### Rules

- One contract test file per module public API. References only public API.
- ✗ break on implementation changes. Break = either refactor broke contract (bug) or test was testing implementation (fix test).
- API changes → update contract first, then implementation. Contract-first per `architecture/STANDARDS.md §1`.
- Unit suite for T0–T2 (fast, no I/O). Integration suite for T3.

---

## 9. Property-Based + Fuzzing

Property-based: random valid inputs, verify invariants. Fuzzing: malformed/adversarial bytes (§11), verify ✗ crash. Both complement example-based, ✗ replace.

| Use | ✗ Not Suitable |
|---|---|
| Pure functions, wide input space | I/O-dependent |
| Round-trips (encode/decode) | UI workflows |
| Parsers · encoders · decoders | Tests requiring specific fixtures |
| Math/algebraic | Complex preconditions |
| Data structure ops | Integration with external services |

| Invariant | Example |
|---|---|
| Round-trip | `decode(encode(x)) == x` |
| Idempotency | `f(f(x)) == f(x)` |
| Monotonicity | Adding never decreases count |
| Preservation | Transform preserves size · sum · key set |
| Commutativity | `merge(a,b) == merge(b,a)` where order irrelevant |
| No crash | ✗ crashes on any valid input |
| No crash adversarial | ✗ crashes on any byte sequence within size bound (§11) |

### Rules

- Min 100 cases per property. Default 1000 production.
- Seeded generation. Seed logged on failure.
- Failing case found → add as permanent example test.
- Unit suite — must stay fast. Expensive generation → reduce count, ✗ skip.
- Fuzzing runs in separate suite — longer budget (5 min per target), nightly.
- Crash in fuzzing = P1 bug. ✗ ignore.

---

## 10. Reality Dimension: Faults

Every external dependency fails. Test the response.

| Dependency | Faults to Inject |
|---|---|
| Network (HTTP, gRPC) | Timeout · connection refused · DNS fail · TLS fail · slow response · partial response · 5xx · rate limit |
| Database | Connection lost · query timeout · deadlock · constraint violation · replica lag · disk full |
| File system | Permission denied · disk full · path missing · file locked · slow I/O |
| Message queue | Publish fail · consumer crash · duplicate delivery · out-of-order · partition unavailable |
| Third-party API | All HTTP errors · malformed response · schema change · auth fail · quota exceeded |
| Cache | Miss · stale · eviction · connection lost |
| Clock | Skew · jump backward · jump forward · stop |

### Rules

- Every shell function has fault test pair: **inject → assert structured error · clear → assert recovery (§18)**.
- Faults injected at adapter boundary via fault-injection layer (test double, network proxy, FS shim). ✗ flags inside production code.
- Deterministic — seeded fault timing, ✗ random.
- Naming: `fault_<dependency>_<failure_mode>_<expected_response>`.
- Test asserts: structured error · log emitted · metric incremented · receipt written (§17). ✗ swallow.
- Retry behavior: max attempts · backoff · jitter · circuit breaker opens.
- Partial failure: half batch succeeds, half fails — both reported, ✗ all-or-nothing.
- Coverage: T2 every downstream dep · T3 every external boundary has full matrix above.

---

## 11. Reality Dimension: Adversarial Inputs

Hostile, broken, weird sources. Test what spec doesn't cover.

| Category | Examples |
|---|---|
| Malformed | Truncated · extra trailing data · wrong magic bytes · invalid UTF-8 |
| Boundary explosion | Empty · 1 byte · max-size · max+1 · max*2 · negative · zero · NaN · infinity |
| Encoding attacks | UTF-8 surrogate pairs · BOM · null bytes · directional override · homoglyphs |
| Injection | SQL · shell · path traversal · template · header injection · LDAP · NoSQL |
| Type confusion | String where int expected · array where object expected · null where required |
| Size attacks | Deep nesting · zip bomb · billion laughs · huge field · huge list |
| Locale | RTL · combining chars · non-ASCII whitespace · timezone edge cases |
| Time | Year 2038 · year 9999 · negative epoch · leap second · DST transition |

### Required Per Target

| Target | Categories |
|---|---|
| Parser/decoder | All |
| Validator | Boundary · type confusion · encoding · injection |
| Public API endpoint | All |
| File loader | Malformed · size · encoding |
| Query builder | Injection (impossible by construction) |
| Template renderer | Injection · encoding |

### Rules

- Every input boundary has adversarial suite. ✗ "trusted input" exemption for public APIs.
- Asserts: ✗ crash · structured error · log emitted · ✗ resource leak.
- Fuzz harness (§9) per parser/decoder. Min 1 fuzz target each.
- Injection prevented structurally (parameterized queries, escaping libs), ✗ regex blacklists. Tests verify.
- Adversarial corpus version-controlled. Grown on every reported security issue.

---

## 12. Reality Dimension: Concurrency

Races, deadlocks, ordering, lost updates — only under concurrent load. Tests induce deterministically.

| Mode | Test Pattern |
|---|---|
| Race | Interleaved ops → correctness for all interleavings |
| Lost update | Concurrent writes → all reflected or detected |
| Stale read | Read after write → consistency model honored |
| Deadlock | Acquisition order varies → ✗ deadlock or detection |
| Live lock | Retry storm → convergence bounded |
| Ordering | Event order varies → outcome stable |
| Partial commit | Multi-step interrupted → atomic or rollback |
| Reentrancy | Self-call transitive → correctness |

### Rules

- Any shared-state code has concurrency test.
- Use deterministic tools: race detectors (Go `-race`, ThreadSanitizer), seeded schedulers, model checkers.
- Stress: N concurrent × M iterations → invariants hold.
- Interleaving tests: pause A mid-exec, run B fully, resume A → correct outcome.
- Lock-free code requires stress + property tests on op sequences.
- ✗ `sleep()` to force ordering. Use barriers, channels, latches.
- ✗ flaky concurrency test. Deterministic or deleted.
- Race detector required in CI when toolchain supports.
- Production stress min: 100 concurrent × 1000 iterations.
- Distributed: partition scenarios — split-brain, partial reachability, message reorder.

---

## 13. Reality Dimension: Resources

Production exhausts memory, disk, FDs, connections, queues. Degrade gracefully, ✗ crash.

| Resource | Scenario |
|---|---|
| Memory | Near cap · OOM mid-op |
| Disk | Full at write · full mid-stream · inode exhaustion |
| FDs | Cap reached · leak detection |
| Connections | Pool exhausted · peer limit |
| Queue/buffer | Full · backpressure · oldest dropped |
| CPU | Throttled · saturated · single-core |
| Network | Throttled · packet loss · high latency |
| Threads/goroutines | Pool exhausted · spawn limit |

### Rules

- Each boundary asserts graceful degradation: structured error · backpressure · circuit open · receipt logged. ✗ uncaught exception · ✗ silent loss.
- Limits set explicitly in test (cgroup, ulimit, runtime flag). ✗ rely on dev machine defaults.
- Leak tests: N iterations, resource use returns to baseline.
- Recovery: hit limit → relieve → system resumes (§18).
- Run with monitoring on — verify saturation metrics emitted (§17).

---

## 14. Reality Dimension: Time + Determinism

Time, timezones, ordering, randomness = nondeterminism. Tests control them.

| Failure | Test |
|---|---|
| Timezone drift | Logic at every UTC offset, outcome stable |
| DST transition | Op at spring-forward / fall-back |
| Clock skew | Inject skew, assert correctness |
| Clock jump | Forward/backward → invariants hold |
| Year boundary | Year change · 2038 · 9999 |
| Leap second | If platform exposes |
| TTL expiry | Stale cache handling |
| Token expiry | Exact expiry · just past |

### Determinism Rules (Production Code)

- ✗ wall-clock without injection. Time as arg | injected clock.
- ✗ random without injection. Source injected, seeded in tests.
- ✗ UUID without injection. Source injected.
- ✗ assume map/dict iteration order where it matters. Sort or use ordered.
- ✗ floating-point equality. Epsilon with documented tolerance.
- Violations = lint-time error, ✗ runtime.

### Determinism in Tests

- Frozen clock default. Advance via `clock.advance(duration)`.
- Seeded random. Seed logged on failure.
- Assert canonical orderings — sort before compare where order incidental.
- Random test order regularly (§24) catches hidden ordering deps.

---

## 15. Reality Dimension: State Accumulation

Long-running systems leak — memory, FDs, caches poison, counters overflow. Catch slow-burn failures.

| Failure | Test |
|---|---|
| Memory leak | N iters, RSS returns to baseline within tolerance |
| FD leak | N iters, FD count stable |
| Connection leak | N iters, pool size stable |
| Cache poison | Bad value persists past TTL → detected or evicted |
| Counter overflow | Counter at max, +1 → wraparound handled |
| Log flood | Repeated error → log rate-limited |
| State drift | Periodic snapshot, invariants hold |
| Task pileup | Long-run scheduled, backlog bounded |

### Rules

- Long-run: N ≥ 1000 iterations | M ≥ 1h wall time, sampled.
- Nightly suite, ✗ per-commit.
- Baseline from clean start. Tolerance documented per resource.
- Failures investigated within 7 days. ✗ tolerated indefinitely.
- Caches have eviction tests + size-bound assertions.
- Counters have overflow tests.

---

## 16. Reality Dimension: Drift + Replay

Schema, deps, traffic patterns drift. Replay catches drift before users.

| Drift Source | Detection |
|---|---|
| Schema | Schema diff vs migration history (every migration) |
| API contract | Contract test vs published spec (§8) |
| Dependency | Lock file diff + behavior test on update |
| Traffic pattern | Replay production traces against new build |
| Data distribution | Property tests on production samples |
| Config | Cross-env config comparison |

### Rules

- L5 production-tier maintains replay corpus. Captured anonymized — PII scrubbed at capture, ✗ at replay. Scrubbing tested.
- Corpus refreshed weekly, min 1000 representative requests, version-controlled separately (large binary store).
- Replay in pre-production env. ✗ against production. Asserts no regression in behavior, latency, error rate.
- Failures investigated before promotion. Dep drift triggers full suite + replay.

---

## 17. Observability Assertions

Tests assert on logs · metrics · traces · receipts, ✗ just returns. Silent failure = uncaught bug.

| Output | When |
|---|---|
| Structured log | Every error path, every state change |
| Metric | Every outcome (success · fail · retry · fallback) |
| Trace span | Every external call, every async boundary |
| Receipt | Every business-meaningful action (`observability/STANDARDS.md`) |
| Event | Every documented domain event |

### Rules

- Contract tests (§8) include observability contract: documented signals on documented events.
- Error path: structured log · metric incremented · receipt written.
- Retry path: retry log · retry metric · backoff observable.
- Fault tests (§10) assert degradation visible to operator before user.
- ✗ assert on log message prose. Assert on structured fields (level · code · field values where they encode behavior).
- Receipt pattern: op runs → receipt with op id · input hash · output hash · timestamp · status → retrievable via documented path → persists past restart.

---

## 18. Recovery Verification

Every fault test pairs with recovery. System returns to known-good when fault clears.

| Cleared | Recovery Asserted |
|---|---|
| Network restored | Pending ops resume or retry succeeds |
| DB back online | Pool reconnects, queries resume |
| Disk freed | Writes resume, queue drains |
| Dep back up | Circuit closes, traffic resumes |
| Load drops | Throttling lifts, backpressure clears |
| Process restart | State recovered from durable store, ✗ data loss |

### Rules

- Paired with §10 fault test. Same scenario, fault cleared mid-test.
- Asserts: baseline metrics · pending work completes · no data loss · no duplicate work.
- Crash recovery (any durable-state op): kill mid-op → restart → state consistent.
- Idempotency verified — retry ✗ duplicates effect.
- Recovery time bounded by documented SLO.

---

## 19. Mutation Testing

Mutator alters code (flip op · delete · change constant) → run tests → ✓ if fail, ✗ if pass (gap).

| Mutator | Detects |
|---|---|
| Conditional flip (`==`→`!=`, `<`→`<=`) | Branch coverage gaps |
| Constant replacement | Hardcoded value gaps |
| Statement deletion | Dead code · untested side effect |
| Return swap | Untested return path |
| Boundary shift | Off-by-one |
| Logical op swap (`&&`→`\|\|`) | Logic gaps |

### Rules

- Score = killed / generated. Target ≥ 80% T0–T1 production.
- Equivalent mutants excluded.
- Nightly | weekly — too slow per-commit.
- Surviving mutants: add test | mark equivalent | delete unreachable.
- L5: gates release for T0–T1.
- PoC/Small: optional, spot-check critical only.

---

## 20. Test Naming + Organization

### Naming

```
test_<function>_<scenario>_<outcome>
fault_<dependency>_<failure_mode>_<expected_response>
scenario_<journey>_<branch>
property_<function>_<invariant>
fuzz_<target>
```

| Rule | ✓ | ✗ |
|---|---|---|
| Describe behavior | `test_validate_email_missing_at_returns_error` | `test_validate_email_1` |
| State outcome | `test_parse_date_empty_returns_none` | `test_parse_date_edge` |
| ✗ implementation/numbering | — | `test_uses_regex` · `test_case_47` |

### Layout + Suites

Suite → pipeline stage mapping in `cicd/STANDARDS.md §5`.

| Path | Contents · Lifecycle |
|---|---|
| `tests/<module>/test_*.ext` | Mirror source tree |
| `tests/<module>/faults/` | Fault tests (§10) |
| `tests/<module>/properties/` · `fuzz/` | Property + fuzz (§9) |
| `tests/<module>/adversarial/` | Corpus, version-controlled, grown on incidents |
| `tests/scenarios/` | Multi-step journeys (§7) |
| `tests/replay/` | Replay corpus, weekly refresh, separate store |
| `tests/fixtures/` | Static reference, version-controlled |
| `tests/tmp/` | Generated, gitignored, per-test cleanup |
| `tests/helpers/` | Test-only, ✗ imported by production |

| Suite | Contents | Frequency |
|---|---|---|
| Unit | T0–T2 unit · property · contract · fast adversarial | Every commit |
| Integration | Boundary · fault · concurrency unit · resource (limits) · observability · recovery | Every commit |
| E2E | User workflows | Pre-merge |
| Scenario · Long-run · Fuzz · Performance | Per §7 · §15 · §9 · §25 | Nightly |
| Mutation | T0–T1 production | Nightly | Weekly |
| Replay | Production traces | Pre-prod deploy |

---

## 21. Mocking Rules

Last resort. Over-mocking = tests pass with broken code.

| Context | Status |
|---|---|
| T0–T1 unit | ✗ Forbidden |
| T2 unit | Hand-written fakes for lower-tier interfaces |
| T3 unit | Mock external (network, third-party) |
| Integration | Mock only outside-project resources |
| E2E · Contract · Faults | ✗ Forbidden — sandboxed real or fault-injection layer |

| Type | Definition | Use |
|---|---|---|
| Fake | Working impl with shortcuts (in-memory DB) | T2 · integration |
| Stub | Canned responses, no logic | T3 external boundaries |
| Mock w/ verification | Records calls, asserts interaction | ✗ Avoid — tests implementation |

### Rules

- ✗ mock what you own. Real impl | hand-written fake.
- Mock only outside control: third-party · external services · clock (via injection).
- ✗ auto-generated mock libs. Explicit fakes implementing contract.
- Needs 3+ mocks → split function (`architecture/STANDARDS.md §4`).
- Mocked behavior matches real. Real changes → update mock immediately.
- ✗ mock data access for T0–T1. Data arrives as arguments.

---

## 22. Coverage Strategy

Path exercise metric. Meaningful coverage = behavior + reality dimensions, ✗ line count.

| Metric | Use | Target / Threshold |
|---|---|---|
| Branch | Decision paths | Primary — T0 95% · T1 90% · T2 80% · T3 60% |
| Function | Public API | T0–T1 100% · T2 90% · T3 70% |
| Mutation (§19) | Test effectiveness | L5: T0 90% · T1 80% |
| Behavioral | Scenarios (auth fail · retry · partial batch) | Tracked manually, ✗ percentage |
| Fault (§10) | Fault matrix per dep | 100% required deps |
| Line | Reachability | Secondary |

### Rules

- ✗ chase percentage. 80% meaningful > 95% superficial.
- Drops trigger investigation, ✗ automatic block. New code without tests = signal.
- ✗ tests written to increase coverage. Every test verifies meaningful behavior.
- Exclude: test code · generated · config boilerplate · dependency wrappers.
- CI report + trend tracked. Sustained decline = problem.
- Behavioral coverage reviewed quarterly per module.

### Low-Coverage Signals

| Pattern | Cause |
|---|---|
| Low T0–T1 | Missing tests — fix immediately |
| Low T3 | Expected — I/O heavy |
| High T3, low T1 | Logic in I/O — refactor |
| PR drops | New code without tests |

---

## 23. Test Data

- Deterministic. ✗ random except seeded property/fuzz.
- Purpose-built per scenario. ✗ shared "golden" datasets across unrelated tests.
- ✗ production data in tests. Privacy · brittleness · nondeterminism.
- Scenario tests (§7) use production-shaped synthetic distributions.
- Fixtures read-only during tests. Generated data deterministic-seeded.
- Date/time hardcoded constants — ✗ `now()` (§14).
- Paths platform-agnostic via stdlib (§26).

### Factory Pattern

One factory per domain type · returns valid by default · per-field overrides · factories compose.

### Fixture Locations

See §20 layout table — `fixtures/` (static) · `<module>/adversarial/` (corpus) · `replay/` (weekly) · `tmp/` (generated, per-test) · inline (small, specific).

---

## 24. Test Independence

Every test isolated. ✗ shared state · ✗ ordering dep · ✗ side effect leak.

| Rule | Violation |
|---|---|
| Each test creates own data | B reads data from A |
| Each test cleans own resources | Temp files accumulate |
| Pass individually | Suite passes, alone fails |
| Pass any order | C depends on B |
| Pass parallel | Two tests write same file |
| ✗ shared mutable state | Module-level var modified |

| Mechanism | Use |
|---|---|
| Fresh instance per test | Default |
| Temp dir per test | FS tests, unique dir, teardown |
| Transaction rollback | DB tests |
| Process isolation | Env var / global modifiers |
| Snapshot/restore | Large data |

### Detecting Violations

Random order (catches hidden deps) · parallel run (catches shared state) · isolated run (catches missing setup). All run regularly.

---

## 25. Performance Tests

Operations within budget. ✗ load testing (→ `devops/STANDARDS.md`).

| Add | ✗ Skip |
|---|---|
| Has SLA | Internal utility, no timing |
| User-visible data | One-time migration |
| Past regression | Stable history |
| Scales with input | Constant-time |

### Rules

- Explicit budget: `op X < N ms for input M`. Per-operation, ✗ aggregate.
- Wall clock on consistent hardware (CI runner, ✗ laptop).
- Separate suite, ✗ slow regular runs. Track baseline. Alert regression > 20%.

| Operation | Input | Budget |
|---|---|---|
| Parse config | 100 entries | < 50ms |
| Validate batch | 1000 records | < 200ms |
| Transform dataset | 10K rows | < 1s |
| Full pipeline | Reference | < 5s |

Budget breach = failing test.

---

## 26. Cross-Platform Tests

Production runs Windows · macOS · Linux. Tests run all target platforms. CI matrix per `cicd/STANDARDS.md §15`.

| Failure Mode | Test |
|---|---|
| Path separator (`/` vs `\`) | Built via stdlib `path.join`, tested per OS |
| Line endings (`\n` vs `\r\n`) | Explicit normalization, both tested |
| Case sensitivity | macOS HFS+ insensitive · Linux sensitive — both |
| Path length | Windows MAX_PATH 260 · long paths · UNC |
| Reserved names | Windows: CON · PRN · AUX · NUL · COM1-9 · LPT1-9 |
| File locking | Windows mandatory · Unix advisory |
| Permissions | POSIX bits vs Windows ACLs |
| Process | fork/exec vs CreateProcess · signal diffs |
| Shell | bash · zsh · PowerShell · cmd — invocation differs |
| Unicode in paths | Per filesystem |
| Time resolution | Windows 100ns · POSIX ns — tolerance per platform |
| Encoding | UTF-8 (Linux/macOS) · UTF-16/codepage (Windows) |

### Rules

- Every target OS runs full unit + integration suite. CI matrix enforces.
- Platform-specific code has platform-specific tests, OS-gated.
- Stdlib path/io abstractions, ✗ raw separators.
- Shell scripts have cross-platform equivalents | OS-skip with explicit marker.
- Container tests Linux-runners-only, documented.
- Fixture paths use `/`, joined at runtime. ✗ checked-in `\`.

---

## 27. Test Effectiveness Audit

Self-improving standard. Quarterly: did tests catch what mattered?

| Input | Source |
|---|---|
| Production incidents | Incident tracker last quarter |
| Customer bugs | Support tracker |
| Hotfix commits | Git history |
| Rollbacks | Deploy log |
| Surviving mutants (§19) | Mutation report |

### Process

1. Per incident: which test type *would have* caught it?
2. Classify: **gap** (missing) · **flaw** (exists, ineffective) · **architecture** (untestable).
3. Action: add test · strengthen · refactor.
4. Track which reality dimension caught most bugs — invest there.
5. Update adversarial + replay corpora with anonymized incident inputs.

### Rules

- Production-tier: quarterly audit mandatory. Small: annual.
- Findings = test-debt items, prioritized alongside features.
- ✗ blame retrospective. Pure gap-finding.
- New incident class → standard updated to require corresponding test type.

---

## 28. Scale Matrix

Testing depth scales with project complexity. See `architecture/STANDARDS.md §12`.

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Confidence target (§1) | L0–L1 | L2–L3 | L4–L5 |
| Pyramid (§3–§4) | Informal | Unit + integration · T0–T1 | Full ratios · all tiers |
| Unit (§5) | Core only | Public functions | All + edges |
| Integration (§6) | ✗ required | Module boundaries | All boundaries |
| E2E + Scenario (§7) | ✗ required | Critical E2E only | All workflows + scenario per workflow |
| Contract (§8) | ✗ required | ✗ required | All public APIs |
| Property + Fuzz (§9) | ✗ required | Parsers + serializers (property) | All pure wide-input · fuzz per parser |
| Faults (§10) | ✗ required | Critical deps | All external deps |
| Adversarial (§11) | ✗ required | Public APIs | All input boundaries |
| Concurrency (§12) | ✗ required | Shared-state code | All + race detector + stress |
| Resources (§13) | ✗ required | ✗ required | All boundaries |
| Time/determinism (§14) | Best effort | Inject clock | Full enforcement + lint |
| State accumulation (§15) | ✗ required | ✗ required | Long-run nightly |
| Drift / replay (§16) | ✗ required | Schema diff only | Full replay corpus |
| Observability (§17) | ✗ required | Error path only | All paths assert signals |
| Recovery (§18) | ✗ required | Critical only | Paired with every fault |
| Mutation (§19) | ✗ required | Spot-check | T0–T1 gating |
| Naming + org (§20) | Informal · same file | Consistent · mirrored tree | Strict · full structure |
| Mocking (§21) | Pragmatic | Tier rules | Strict · ✗ overuse |
| Coverage (§22) | ✗ tracked | T0–T1 | Full + thresholds |
| Data (§23) | Inline | Factories | Full factory + fixtures |
| Independence (§24) | Best effort | No shared state | Random + parallel safe |
| Performance (§25) | ✗ required | Critical ops | Full budget table |
| Cross-platform (§26) | One OS | Two OS | All target OS matrix |
| Effectiveness audit (§27) | ✗ required | Annual | Quarterly |

### Transitions

PoC → Small: unit + integration · linter · independence · factories.
Small → Production: reality dimensions in priority — faults → adversarial → concurrency → observability → recovery → resources → state → replay → mutation. System-level dimensions per `testing/PRESSURE.md §10`.

Incremental alongside features. ✗ "testing sprint" after the fact. T0–T1 first → integration at boundaries → reality dimensions per criticality → system-level pressure when production-tier.

---

## 29. Testing Checklist

### New Project

- [ ] Confidence target declared (L0–L5, §1)
- [ ] Test tree mirrors source · suites defined (§20)
- [ ] Naming convention · data strategy · coverage thresholds set
- [ ] CI runs unit + integration every commit · OS matrix configured (§26)
- [ ] Determinism rules enforced via lint (§14)

### New Module

- [ ] Unit tests every public function · edges (empty · max · invalid · absent)
- [ ] Adversarial tests on input boundaries (§11)
- [ ] Contract tests on public API (production-tier, §8)
- [ ] Integration tests for tier/module boundaries
- [ ] Fault test per external dep (§10) · paired recovery (§18)
- [ ] Concurrency tests if shared state (§12)
- [ ] Observability assertions on error paths (§17)
- [ ] ✗ mocks in T0–T1 · all tests pass in isolation + random order

### New Function

- [ ] Classified logic | shell (`architecture/STANDARDS.md §4`)
- [ ] Logic → unit data-in/data-out · shell → integration sandboxed + fault
- [ ] Name describes behavior · boundary values tested
- [ ] Error paths return structured error · log · metric
- [ ] Time/random/UUID injected if used (§14)

### Bug Fix

- [ ] Failing test first — reproduces bug, lowest layer
- [ ] Reality dimension classified · adversarial/replay corpus updated if input-driven
- [ ] Fix applied, test passes, no regressions

### Pre-Release

- [ ] All suites pass: unit · integration · E2E · scenario · fuzz · long-run
- [ ] Coverage thresholds met · mutation score ≥ threshold (L5)
- [ ] No flaky tests · perf budgets met · contract tests pass
- [ ] Replay corpus green (L5) · cross-platform matrix green (§26)
- [ ] Effectiveness audit current (production-tier, §27)
- [ ] Pressure / survival / pen test gates green per `testing/PRESSURE.md §8` (production-tier)
