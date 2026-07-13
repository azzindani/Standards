# Testing Standards

> How a project proves its code works: test pyramid, size classes, tier classification, mocking policy, contract tests, and the coverage gate every language standard defers to.

**ID** `testing` · **Tier** Core · **Version** 1.0
**Owns** test pyramid · size classes · tier classification · unit/integration/E2E rules · contract tests · property-based tests · fuzzing · mocking policy · coverage gate · flake budget · test data · test independence
**Defers to** reality dimensions — faults · adversarial · concurrency · resources · time · state · drift · mutation · perf → [REALITY.md](REALITY.md) · load · soak · chaos · survival · penetration → [PRESSURE.md](PRESSURE.md) · pipeline stages · runners · where suites execute → [cicd](../cicd/STANDARDS.md) · threat model · injection taxonomy · validation boundary → [security](../security/STANDARDS.md) · error taxonomy · error shape → [error_handling](../error_handling/STANDARDS.md) · log · metric · trace formats → [observability](../observability/STANDARDS.md) · quality bar · benchmark rubrics → [expectation](../expectation/STANDARDS.md) · test framework choice + invocation → [python](../python/STANDARDS.md) · [go](../go/STANDARDS.md) · [rust](../rust/STANDARDS.md) · [typescript](../typescript/STANDARDS.md)
**Load with** [REALITY.md](REALITY.md) · [PRESSURE.md](PRESSURE.md) · [cicd](../cicd/STANDARDS.md) · [architecture](../architecture/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Confidence Ladder](#2-confidence-ladder)
3. [Test Pyramid](#3-test-pyramid)
4. [Size Classes](#4-size-classes)
5. [Classification by Tier](#5-classification-by-tier)
6. [Unit Tests](#6-unit-tests)
7. [Integration Tests](#7-integration-tests)
8. [End-to-End and Scenario Tests](#8-end-to-end-and-scenario-tests)
9. [Contract Tests](#9-contract-tests)
10. [Property-Based Tests and Fuzzing](#10-property-based-tests-and-fuzzing)
11. [Mocking Rules](#11-mocking-rules)
12. [Coverage Strategy](#12-coverage-strategy)
13. [Flaky Tests](#13-flaky-tests)
14. [Test Naming](#14-test-naming)
15. [Test Organization](#15-test-organization)
16. [Test Data](#16-test-data)
17. [Test Independence](#17-test-independence)
18. [Cross-Platform Tests](#18-cross-platform-tests)
19. [Scale Matrix](#19-scale-matrix)
20. [Checklist](#20-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| CI green = ship-confident | Suite composition defines deployment confidence (§2). Green run that does not license a deploy is a broken suite |
| Two spines | Every test sits at one (pyramid layer, reality dimension) cell. Pyramid = size of unit under test (§3). Reality = condition simulated ([REALITY.md](REALITY.md)) |
| Test behavior, ✗ implementation | Refactor with ✗ test change = correct. Refactor breaking tests without behavior change = tests bind implementation |
| Lowest layer that can catch it | Bug fix adds test at lowest possible layer. Unit → integration → E2E |
| Determinism is mandatory | Nondeterministic test = broken test. Flaky test = failing test (§13) |
| Strategy here, mechanics elsewhere | This standard says what to test and to what threshold. Where suites run in the pipeline → [cicd](../cicd/STANDARDS.md) |
| Tests are production code | Reviewed · typed · linted · refactored. Test helpers ✗ imported by production |

---

## 2. Confidence Ladder

Suite composition → deployment stance. Every project declares a target level; pipeline gates on it.

| Level | Suite includes | Deployment stance |
|---|---|---|
| L0 — Smoke | Manual run-through | Local only · ✗ ship |
| L1 — Wired | Unit + happy-path integration | Internal demo |
| L2 — Correct | + contract + property + edges | Dev |
| L3 — Robust | + faults + adversarial + concurrency | Staging |
| L4 — Real | + resources + time + state + observability assertions | Production with monitoring |
| L5 — Self-evident | + mutation + replay + drift | Production, ship without manual review |

- Target level declared in repo (`.confidence-level` file | pipeline config). Undeclared → L1 assumed. ✗ deploy beyond the declared level until that level's tests exist.
- Production-tier: L4 minimum. L5 where a bug costs revenue · data · trust.
- Level ratchets up. ✗ decrease without recorded review. Claimed level verified by effectiveness audit ([REALITY.md](REALITY.md)) — an unaudited claim is a guess.
- System-level dimensions (pressure · survival · penetration) required from L3+ → [PRESSURE.md](PRESSURE.md).

---

## 3. Test Pyramid

| Layer | Proportion | Speed | Scope |
|---|---|---|---|
| Unit | 70% | < 10 ms each | Single function, single path |
| Integration | 20% | < 500 ms each | Module / tier boundary |
| E2E + scenario | 10% | < 5 s each | Full user-facing workflow |

- Inverted pyramid = architecture problem. Too many E2E → logic buried in I/O → push logic down to T0–T1.
- Suite budget: unit < 5 min · integration + E2E adds < 10 min · total < 15 min. Over budget → humans skip it → suite dies.
- Reality tests span all layers — a fault test is a unit test in pure code, an integration test at an adapter boundary.
- Proportions are targets, ✗ gates. 60/30/10 with fast feedback beats a forced 70/20/10.

---

## 4. Size Classes

Orthogonal to the pyramid: pyramid names *what* is under test, size names *what resources the test may touch*. Every test declares its class via marker/tag/attribute. CI selects suites by class.

| Class | May touch | Forbidden | Runtime target | Hard cap |
|---|---|---|---|---|
| Small | Single process · in-memory only | ✗ network · ✗ disk · ✗ sleep · ✗ wall clock · ✗ multi-thread beyond test | < 10 ms | 1 s |
| Medium | Localhost · temp FS · test DB container · loopback socket | ✗ external network · ✗ shared env · ✗ production creds | < 500 ms | 30 s |
| Large | Full assembled system · sandboxed externals · multiple processes | ✗ production · ✗ shared mutable environment | < 5 s | 5 min |

- Test exceeding its class hard cap → failing test. ✗ raise the cap; reclassify or split.
- Small is the default. Bigger class → one-line justification at the top of the file.
- Class restrictions enforced by the harness (network + FS blocked in the small suite), ✗ by convention.
- Mapping: small ≈ unit · medium ≈ integration · large ≈ E2E + scenario. Pyramid for design, size for execution.

---

## 5. Classification by Tier

Maps to the tier model in [architecture](../architecture/STANDARDS.md).

| Tier | What | Test types | I/O |
|---|---|---|---|
| T0 — Kernel | Types · constants · pure utilities | Unit (small) | ✗ never |
| T1 — Engine | Domain logic · transforms · validators | Unit (small) | ✗ never |
| T2 — Service | Orchestration · composition · workflow | Unit + integration | ✗ never — inject fakes |
| T3 — Interface | Adapters · CLI · API · file/net/DB | Integration + E2E | Yes — sandboxed |

### Required reality dimensions per tier — definitions + rules → [REALITY.md](REALITY.md)

| Dimension | T0 | T1 | T2 | T3 |
|---|---|---|---|---|
| Correctness | ✓ | ✓ | ✓ | ✓ |
| Adversarial | ✓ if parser/validator | ✓ | ✓ | ✓ |
| Concurrency | — | ✓ if mutable | ✓ if orchestrates | ✓ if shared resource |
| Faults | — | — | ✓ | ✓ |
| Resources | — | — | ✓ if buffers/caches | ✓ |
| Time | ✓ if time-dependent | ✓ if time-dependent | ✓ | ✓ |
| State accumulation | — | — | ✓ if caches | ✓ if connections/pools |
| Observability | — | — | ✓ | ✓ |
| Recovery | — | — | ✓ | ✓ |

Every function is logic | shell ([architecture](../architecture/STANDARDS.md)). **Logic** (T0–T2) → direct call, data in → data out, ✗ mocks. **Shell** (T3) → sandboxed I/O, mock only services outside the project (§11).

---

## 6. Unit Tests

Single function · single scenario · single assertion target.

| Allowed | ✗ Forbidden |
|---|---|
| Call function with arguments | File system access |
| Assert return value | Network calls |
| Assert error structure | Database queries |
| Assert emitted signals ([REALITY.md](REALITY.md)) | Shared mutable state |
| Test boundary values | Sleeping · waiting on wall clock |

- Each test builds its own input. ✗ consume data produced by another test. Any order → same result. ✗ global setup mutating shared state.
- T0–T1: ✗ mocks. Needing one = design defect ([architecture](../architecture/STANDARDS.md)). T2: hand-written fakes for lower-tier interfaces, ✗ mock libraries.
- ✗ assert on private fields.

| Target | Required depth |
|---|---|
| T0 utilities | Every function, every edge |
| T1 domain logic | Every public function, all branches |
| T1 validators | Valid · invalid · boundary · adversarial |
| T1 transforms | Empty · single · many · malformed |
| T2 orchestration | Happy · error accumulation · partial failure · injected fault |

---

## 7. Integration Tests

Components work together across a boundary. One boundary per test.

| Boundary | Example |
|---|---|
| Tier | T3 adapter calls T2 service with real wiring |
| Module | A's public API consumed by B |
| Data format | Serialize → deserialize round-trip |
| External resource | Real FS, test DB, sandboxed HTTP |

| Component | Approach |
|---|---|
| Own DB · FS · modules | Real — test instance, wiped between tests |
| Third-party APIs · external services | Stub at adapter boundary, deterministic |
| Time / clock | Injected ([REALITY.md](REALITY.md)) |
| External faults | Fault-injection layer ([REALITY.md](REALITY.md)) |

- Test the contract between components, ✗ their internals. ✗ duplicate unit coverage — unit covers logic, integration covers wiring.
- Sandboxed resources fresh per test | per suite. ✗ share a test DB across parallel runs.
- Tests requiring a live external service live in a separate, marked suite — never gate a PR on a third party's uptime.
- Per public boundary: valid → output · invalid → structured error · boundary (empty · max · unicode · null-equivalent) → graceful · fault during call → error + recovery path.

---

## 8. End-to-End and Scenario Tests

E2E = one full workflow, entry to output. Scenario = multi-step journey with production-shaped data. Together they close the "tests pass, production breaks" gap.

| Write | ✗ Skip |
|---|---|
| Critical user workflow | Internal utilities |
| Revenue · data-loss path | Display variations |
| Multi-module orchestration | Already covered by unit + integration |
| Production-incident regression | Exploratory one-offs |

- Max 20 E2E per project. More → push logic down. E2E budget < 5 s each; exceeding = redesign, ✗ raise the budget.
- Fully assembled system, sandboxed externals. ✗ E2E against production.
- Assert observable output — files · API responses · stdout · emitted events — plus observability signals. ✗ assert internal state.
- Structure: **Arrange → Act → Assert → Cleanup**. Cleanup runs even when assertions fail.
- Scenarios: 3–10 steps · realistic timing · production-shaped data distributions · branching (success · validation fail · timeout · retry) · ≥ 1 per critical workflow · nightly suite.

---

## 9. Contract Tests

Lock the behavior of a published interface. Survive refactors — internal restructuring ✗ breaks a contract test.

| Target | Assertion |
|---|---|
| Signature | Declared input/output types |
| Behavior | Specific input → specific output |
| Error contract | Invalid input → structured error, ✗ crash |
| Absence | Missing → explicit absence, ✗ null |
| Idempotency | Same input twice → same output |
| Observability contract | Documented signals on documented events |
| Fault contract | Documented response — timeout · retry · fallback |

### Consumer-driven contracts

Required for every service-to-service boundary at L3+.

- Consumer test suite generates a contract (pact) declaring the requests it makes + responses it relies on. Published to a **broker** on every consumer CI run.
- Provider verifies against **every** consumer contract for every environment it is deployed to — before merge and before deploy.
- Deploy gate: provider ✗ deploys until the broker's verification matrix is green for the target environment. A consumer contract with no verification = red.
- Consumer contracts encode only fields the consumer actually reads. ✗ assert on the whole response body — it couples every consumer to every field.
- Provider verification runs against the real provider with stubbed downstreams. ✗ verify a provider mock against a consumer mock — that proves nothing.
- Provider outside your control → bidirectional mode: provider publishes its spec, broker diffs the consumer contract against the spec.
- Breaking change = expand → migrate consumers → contract. Removal only after the broker shows zero consumers on the old contract.
- One contract test file per module public API, referencing public API only. T0–T2 contracts run in the unit suite (no I/O); T3 in the integration suite.
- Contract break = either the refactor broke the contract (bug) or the test bound implementation (fix the test). Neither is "update the snapshot". API change → update contract first, then implementation.

---

## 10. Property-Based Tests and Fuzzing

First-class, ✗ exotic. Property-based = random *valid* inputs, verify invariants. Fuzzing = malformed/adversarial bytes, verify ✗ crash. Both complement example-based tests, ✗ replace them.

Apply to: pure functions with wide input space · round-trips · parsers · encoders · decoders · math/algebraic ops · data-structure ops. ✗ apply to: I/O-dependent code · UI workflows · fixture-specific behavior · complex preconditions · external-service integration.

| Invariant | Shape |
|---|---|
| Round-trip | `decode(encode(x))` equals `x` |
| Idempotency | `f(f(x))` equals `f(x)` |
| Monotonicity | Adding an element never decreases the count |
| Preservation | Transform preserves size · sum · key set |
| Commutativity | `merge(a,b)` equals `merge(b,a)` where order is irrelevant |
| No crash | ✗ crash on any valid input |
| No crash — adversarial | ✗ crash on any byte sequence within the size bound |

- Min 100 generated cases per property. Default 1000 at production tier. Seeded generation, seed printed on failure. ✗ unseeded randomness.
- Failing case found → add it as a permanent example test, then fix.
- Properties run in the unit suite → must stay fast. Expensive generator → reduce case count, ✗ skip the property.
- Fuzzing runs in its own suite: ≥ 5 min per target, nightly, corpus persisted between runs and version-controlled. Corpus grows on every reported input-handling defect.
- ≥ 1 fuzz target per parser · decoder · deserializer · public byte-accepting boundary.
- Crash | hang | sanitizer finding in fuzzing = P1 bug. ✗ ignore · ✗ tolerate a known-crashing input.

---

## 11. Mocking Rules

Last resort. Over-mocking → tests pass while the system is broken.

| Context | Status |
|---|---|
| T0–T1 unit | ✗ forbidden |
| T2 unit | Hand-written fakes for lower-tier interfaces |
| T3 unit | Stub external network · third-party only |
| Integration | Stub only resources outside the project |
| E2E · contract · fault tests | ✗ forbidden — sandboxed real, or fault-injection layer |

| Type | Definition | Use |
|---|---|---|
| Fake | Working implementation with shortcuts (in-memory DB) | T2 · integration |
| Stub | Canned responses, no logic | T3 external boundaries |
| Mock with verification | Records calls, asserts interaction | ✗ avoid — asserts implementation |

- ✗ mock what you own. Real implementation | hand-written fake. Mock only what is outside your control: third-party services · external systems · clock (via injection).
- ✗ auto-generated mock libraries. Explicit fakes implementing the contract.
- Function needing 3+ mocks → split it ([architecture](../architecture/STANDARDS.md)).
- Real behavior changes → fake updated in the same PR. A stale fake is a lie the suite tells daily.
- ✗ mock data access for T0–T1. Data arrives as arguments.

---

## 12. Coverage Strategy

Single source of truth for coverage gates, all languages, all repos. Language standards ✗ define their own thresholds — they cross-reference this section and state framework + invocation only.

### The gate

**Tiered branch coverage is the CI gate. ✗ flat line-coverage gate — at any percentage, in any language, in any repo.**

| Tier | Branch coverage (gate) | Function coverage (gate) |
|---|---|---|
| T0 — Kernel | ≥ 95% | 100% |
| T1 — Engine | ≥ 90% | 100% |
| T2 — Service | ≥ 80% | ≥ 90% |
| T3 — Interface | ≥ 60% | ≥ 70% |

- Gate = branch coverage, measured **per tier, per module**. Below threshold → pipeline fails. Pipeline wiring → [cicd](../cicd/STANDARDS.md).
- Line coverage is a **secondary signal**: reported, trended, never a gate · never a target · never a PR block. Line % rewards executing code; branch % rewards exercising decisions.
- Repo-wide aggregate % is a **report only**, ✗ a gate. An aggregate hides a 40% T1 core behind a mass of trivially-covered T3.
- Patch coverage: branches introduced | changed by a PR meet the tier threshold. Legacy modules below threshold are grandfathered per module with a recorded owner + expiry date. ✗ open-ended exemption.
- Thresholds ratchet up, never down. Lowering one → recorded review with a named approver.

| Other metric | Role | Threshold |
|---|---|---|
| Mutation ([REALITY.md](REALITY.md)) | Coverage-quality check | L5: T0 90% · T1 80% |
| Fault ([REALITY.md](REALITY.md)) | Fault matrix per dependency | 100% of required dependencies |
| Behavioral | Named scenarios (auth fail · retry · partial batch) | Tracked as a list, ✗ a percentage |
| Line | Secondary signal | ✗ gate · ✗ target |

### Rules

- ✗ chase the percentage. 80% meaningful > 95% superficial. High branch % + low mutation score = tests that execute code and assert nothing.
- ✗ write a test to raise coverage. Every test verifies a behavior a user or caller depends on.
- Exclusions: test code · generated code · config boilerplate · thin dependency wrappers. Exclusion list version-controlled and reviewed like source. ✗ exclude a file to pass the gate.
- Coverage drop on a PR → investigate. New code without tests → block. Behavioral coverage reviewed per module quarterly at production tier.

### Low-coverage signals

| Pattern | Cause |
|---|---|
| Low T0–T1 | Missing tests — fix immediately |
| Low T3 | Expected — I/O-heavy, thin logic |
| High T3, low T1 | Logic buried in I/O — refactor, ✗ add T3 tests |
| Sudden PR drop | New code without tests |
| High line %, low branch % | Tests walk the happy path only |

---

## 13. Flaky Tests

**A flaky test is a failing test.** Green-on-retry is ✗ green — it is an untrusted suite reporting noise.

| Rule | Detail |
|---|---|
| Definition | Result changes across runs on an identical commit |
| Detection | CI records per-test pass/fail history. Flake rate = flips / runs over the trailing 50 runs |
| Flake budget | Suite flake rate < 0.1% of test-runs. Above → suite is untrusted; flake fixes preempt feature work |
| Quarantine cap | Quarantined set ≤ 0.5% of tests. Above → release blocked |
| Quarantine window | ≤ 24 h, named owner, linked issue, test still runs (result recorded, non-gating) |
| Expiry | Unfixed at 24 h → test deleted + P2 test-debt item opened. ✗ extend · ✗ indefinite quarantine |

- ✗ auto-retry to turn a red run green — retries collect flake data only, and the run stays red. ✗ `retry(3)` decorators · ✗ skip/xfail markers hiding a flake · ✗ "re-run CI" as a merge procedure.
- Root cause classified before fix: shared state | test ordering (§17) · time | randomness · concurrency ([REALITY.md](REALITY.md)) · network dependence (§7) · resource contention. Fix the cause, ✗ the symptom.
- Concurrency test that flakes: made deterministic or deleted. Flake introduced by a PR → PR reverted, ✗ merged with a follow-up ticket.

---

## 14. Test Naming

| Pattern | Applies to |
|---|---|
| `test_<function>_<scenario>_<outcome>` | Unit · integration |
| `fault_<dependency>_<failure_mode>_<expected_response>` | Fault tests |
| `scenario_<journey>_<branch>` | Scenario tests |
| `property_<function>_<invariant>` | Property-based |
| `fuzz_<target>` | Fuzz targets |
| `contract_<consumer>_<provider>_<interaction>` | Consumer-driven contracts |

- Name states behavior + outcome: `test_validate_email_missing_at_returns_error` ✓ · `test_validate_email_1` ✗ · `test_parse_date_edge` ✗.
- ✗ name the implementation (`test_uses_regex`) · ✗ number the case (`test_case_47`).
- A failing test's name alone tells the reader what broke. Needing to read the body → rename it.

---

## 15. Test Organization

Suite → pipeline stage mapping → [cicd](../cicd/STANDARDS.md). This section owns the layout and the suite contents only.

| Path | Contents · lifecycle |
|---|---|
| `tests/<module>/test_*.<ext>` | Mirrors the source tree |
| `tests/<module>/faults/` | Fault tests ([REALITY.md](REALITY.md)) |
| `tests/<module>/properties/` · `fuzz/` | Property tests + fuzz targets (§10) |
| `tests/<module>/adversarial/` | Corpus — version-controlled, grown on every incident |
| `tests/contracts/` | Consumer-driven contracts (§9) |
| `tests/scenarios/` | Multi-step journeys (§8) |
| `tests/replay/` | Replay corpus — weekly refresh, separate large-object store |
| `tests/pressure/` · `survival/` · `pentest/` · `harness/` | System-level → [PRESSURE.md](PRESSURE.md) |
| `tests/fixtures/` | Static reference data, version-controlled |
| `tests/tmp/` · `tests/helpers/` | Generated + gitignored, cleaned per test · test-only helpers, ✗ imported by production |

| Suite | Contents | Frequency |
|---|---|---|
| Unit (small) | T0–T2 unit · property · contract · fast adversarial | Every commit |
| Integration (medium) | Boundary · fault · concurrency · resources · observability · recovery | Every commit |
| E2E (large) | User workflows | Pre-merge |
| Scenario · long-run · fuzz · performance | Per §8 · [REALITY.md](REALITY.md) · §10 | Nightly |
| Mutation | T0–T1 | Nightly / weekly |
| Replay | Production traces | Pre-production deploy |
| Pressure · survival · penetration | Per [PRESSURE.md](PRESSURE.md) | Nightly + pre-release |

---

## 16. Test Data

- Deterministic. ✗ random data except seeded property/fuzz generation (§10).
- Purpose-built per scenario. ✗ one shared "golden" dataset across unrelated tests — it couples every test to every field.
- ✗ production data in tests. Privacy · brittleness · nondeterminism. Anonymized production *traces* → replay corpus only ([REALITY.md](REALITY.md)).
- Scenario tests (§8) use production-shaped synthetic distributions, ✗ uniform toy data.
- Dates and times are hardcoded constants. ✗ `now()` in a test. Fixtures read-only during a run; generated data seeded.
- Paths built via stdlib join, ✗ raw separators (§18).
- Factory per domain type: returns a valid instance by default · per-field overrides · factories compose. Test states only the fields it cares about.

---

## 17. Test Independence

Every test isolated. ✗ shared state · ✗ ordering dependency · ✗ side-effect leak.

| Rule | Violation it prevents |
|---|---|
| Each test creates its own data | B reads data written by A |
| Each test cleans its own resources | Temp files accumulate across runs |
| Passes individually | Suite passes, single test fails alone |
| Passes in any order | C depends on B running first |
| Passes in parallel | Two tests write the same file |
| ✗ shared mutable state | Module-level variable mutated by a test |

Mechanisms: fresh instance per test (default) · unique temp dir per test, torn down · transaction rollback for DB tests · process isolation for env-var or global-state modifiers · snapshot/restore for large reference data.

Detection, run regularly: random order (catches hidden dependencies) · parallel run (catches shared state) · single-test run (catches missing setup). All three green or the suite is order-dependent.

---

## 18. Cross-Platform Tests

Production runs Windows · macOS · Linux. Tests run on every target platform. Matrix wiring → [cicd](../cicd/STANDARDS.md).

| Failure mode | Test |
|---|---|
| Path separator (`/` vs `\`) | Paths built via stdlib join, exercised per OS |
| Line endings (`\n` vs `\r\n`) | Explicit normalization, both tested |
| Case sensitivity | macOS insensitive · Linux sensitive — both |
| Path length | Windows MAX_PATH 260 · long paths · UNC |
| Reserved names | Windows: CON · PRN · AUX · NUL · COM1-9 · LPT1-9 |
| File locking | Windows mandatory · Unix advisory |
| Permissions | POSIX bits vs Windows ACLs |
| Process | fork/exec vs CreateProcess · signal differences |
| Shell | bash · zsh · PowerShell · cmd — invocation differs |
| Time resolution | Windows 100 ns · POSIX ns — tolerance per platform |
| Encoding | UTF-8 (Linux/macOS) vs UTF-16 · codepage (Windows) |
| Unicode in paths | Per filesystem, tested per OS |

- Every target OS runs the full unit + integration suite. ✗ "it works on the maintainer's laptop".
- Platform-specific code has platform-specific tests, OS-gated by marker. Shell scripts get a cross-platform equivalent | an explicit OS-skip marker. Container-only tests are Linux-runner-only, documented as such.
- Fixture paths stored with `/`, joined at runtime. ✗ commit a `\` path.

---

## 19. Scale Matrix

| Aspect | Prototype | Production | Scale |
|---|---|---|---|
| Confidence target (§2) | L0–L2 | L3–L4 | L4–L5 |
| Pyramid (§3) | Informal | Full ratios · all tiers | Full ratios · enforced budgets |
| Size classes (§4) | Untagged | Tagged · caps enforced | Tagged · harness-enforced isolation |
| Unit (§6) | Core functions | All public functions + edges | All + adversarial + property |
| Integration (§7) | ✗ required | All module + tier boundaries | All + separate external suite |
| E2E + scenario (§8) | ✗ required | Critical workflows | All workflows + scenario per workflow |
| Contract (§9) | ✗ required | All public APIs | Consumer-driven + broker + deploy gate |
| Property + fuzz (§10) | ✗ required | Parsers + serializers | All wide-input pure code · fuzz per parser |
| Mocking (§11) | Pragmatic | Tier rules enforced | Strict · fakes reviewed |
| Coverage (§12) | Reported, ✗ gated | Tier branch gate enforced | Tier branch gate + patch gate + mutation |
| Flake budget (§13) | Best effort | < 0.1% · 24 h quarantine cap | < 0.1% · quarantine ≤ 0.5% of suite |
| Organization (§15) | Same file as source | Mirrored tree · suites split | Full structure · corpora version-controlled |
| Data (§16) | Inline | Factories | Factories + fixtures + synthetic distributions |
| Independence (§17) | Best effort | ✗ shared state | Random-order + parallel enforced in CI |
| Cross-platform (§18) | One OS | Two OS | Full target matrix |

Prototype → Production: unit + integration → tier coverage gate → contract tests → independence + determinism. Production → Scale: reality dimensions in priority order ([REALITY.md](REALITY.md)) → system-level pressure ([PRESSURE.md](PRESSURE.md)). Tests grow alongside features. ✗ a "testing sprint" after the fact.

---

## 20. Checklist

- [ ] Confidence target declared in the repo (§2)
- [ ] Pyramid proportions within range · suite under 15 min total (§3)
- [ ] Every test declares a size class · no test exceeds its class hard cap (§4)
- [ ] Small suite blocks network + disk at the harness level (§4)
- [ ] Every function classified logic | shell; T0–T1 tests contain zero mocks (§5, §11)
- [ ] Unit tests build their own input · pass in any order (§6)
- [ ] Each integration test crosses exactly one boundary (§7)
- [ ] ≤ 20 E2E tests · each under 5 s · cleanup runs on failure (§8)
- [ ] Every service-to-service boundary has a consumer-driven contract published to the broker (§9)
- [ ] Provider deploy blocked until the broker verification matrix is green for the target environment (§9)
- [ ] ≥ 1 fuzz target per parser/decoder · seeded generation · seed printed on failure (§10)
- [ ] Branch coverage meets the tier gate: T0 95% · T1 90% · T2 80% · T3 60% (§12)
- [ ] No flat line-coverage gate exists in any pipeline or language config (§12)
- [ ] Coverage exclusion list version-controlled and reviewed (§12)
- [ ] Suite flake rate < 0.1% · zero tests quarantined beyond 24 h · no retry-to-green (§13)
- [ ] Test names state behavior + outcome, not implementation or index (§14)
- [ ] Test tree mirrors source · helpers never imported by production (§15)
- [ ] No production data in tests · dates hardcoded · generators seeded (§16)
- [ ] Suite green in random order, in parallel, and test-by-test in isolation (§17)
- [ ] Full unit + integration suite green on every target OS (§18)
- [ ] Reality dimensions covered per tier table (§5, [REALITY.md](REALITY.md))
- [ ] System-level gates green at production tier ([PRESSURE.md](PRESSURE.md))
