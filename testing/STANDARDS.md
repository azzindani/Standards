# Testing Standards

Rules for testing all projects, all languages. Defines what to test,
how to classify tests, and how testing depth scales with project
complexity. Not how to run tests (→ `cicd/STANDARDS.md`) or review
them (→ `code_review/STANDARDS.md`).

Composable with: Architecture Standards, Code Writing Standards,
CI/CD Standards, and language-specific standards.

---

## Table of Contents

1. [Test Pyramid](#1-test-pyramid)
2. [Test Classification by Tier](#2-test-classification-by-tier)
3. [Unit Test Rules](#3-unit-test-rules)
4. [Integration Test Rules](#4-integration-test-rules)
5. [E2E Test Rules](#5-e2e-test-rules)
6. [Contract Tests](#6-contract-tests)
7. [Property-Based Testing](#7-property-based-testing)
8. [Test Naming Convention](#8-test-naming-convention)
9. [Test Organization](#9-test-organization)
10. [Mocking Rules](#10-mocking-rules)
11. [Coverage Strategy](#11-coverage-strategy)
12. [Test Data](#12-test-data)
13. [Test Independence](#13-test-independence)
14. [Performance Tests](#14-performance-tests)
15. [Scale Matrix](#15-scale-matrix)
16. [Testing Checklist](#16-testing-checklist)

---

## 1. Test Pyramid

Distribution targets for a production system:

| Layer | Proportion | Speed Target | Scope |
|---|---|---|---|
| Unit | 70% | < 10ms each | Single function, single path |
| Integration | 20% | < 500ms each | Module boundary, tier boundary |
| E2E | 10% | < 5s each | Full user-facing workflow |

Rules:

- Pyramid inverts = architecture problem. Too many E2E tests signals logic buried in I/O layers.
- Every bug fix adds a test at lowest possible layer. If a unit test can catch it, ✗ write an integration test.
- Flaky tests are deleted or fixed within 24 hours. ✗ "skip" · ✗ "retry 3 times" · ✗ quarantine indefinitely.
- Test suite must complete in under 5 minutes for unit layer, 15 minutes total including integration + E2E.

---

## 2. Test Classification by Tier

Tests map directly to the architecture tier model. See `architecture/STANDARDS.md §2`.

| Tier | What to Test | Test Type | I/O in Test |
|---|---|---|---|
| 0 — Kernel | Types, constants, pure utilities | Unit | ✗ Never |
| 1 — Engine | Domain logic, transforms, validators | Unit | ✗ Never |
| 2 — Service | Orchestration, composition, workflow | Unit + Integration | ✗ Never (inject fakes) |
| 3 — Interface | Adapters, CLI, API, file/network/DB | Integration + E2E | Yes — real or sandboxed |

### Tier-Test Mapping Rules

- Tier 0–1 functions are pure (no I/O). Tests call function directly with data in, assert data out.
- Tier 2 tests verify orchestration logic by injecting Tier 1 results as arguments. Real I/O ✗ forbidden.
- Tier 3 tests exercise real adapters against sandboxed resources (temp files, test DBs, mock servers).
- Cross-tier tests (integration) verify data flows correctly across tier boundaries.

### Function Type Determines Test Strategy

Per `architecture/STANDARDS.md §4` — every function is logic or shell, never both.

| Function Type | Test Strategy |
|---|---|
| Logic (Tier 0–2) | Direct call with data. Assert return value. No mocks needed. |
| Shell (Tier 3) | Test with sandboxed I/O. Mock only external services outside project boundary. |

---

## 3. Unit Test Rules

Unit tests verify a single function's behavior for a single input scenario.

### Scope

| Allowed | ✗ Forbidden |
|---|---|
| Call function with arguments | File system access |
| Assert return value | Network calls |
| Assert error conditions | Database queries |
| Test boundary values | Shared mutable state between tests |
| Test absence handling | Sleeping / waiting |

### Isolation

- Each test creates its own input data. ✗ rely on data created by another test.
- Tests run in any order, produce same results.
- ✗ global setup that mutates shared state. Per-test setup only.

### What to Unit Test

| Target | Priority |
|---|---|
| Tier 0 pure utilities | Every function, every edge case |
| Tier 1 domain logic | Every public function, all branches |
| Tier 1 validators | Valid input, invalid input, boundary values |
| Tier 1 transforms | Empty input, single item, many items, malformed input |
| Tier 2 orchestration logic | Happy path, error accumulation, partial failure |

### Mocking in Unit Tests

- Tier 0–1: ✗ no mocks. Functions are pure — pass data in, get data out. If a unit test for Tier 0–1 needs a mock, the function has a design problem. See `architecture/STANDARDS.md §4`.
- Tier 2: inject fake implementations of lower-tier interfaces. ✗ mock libraries — use hand-written fakes that implement the same contract.
- Tier 3: see §10 Mocking Rules.

---

## 4. Integration Test Rules

Integration tests verify that components work together across boundaries.

### What Constitutes an Integration Test

| Boundary Crossed | Example |
|---|---|
| Tier boundary | Tier 3 adapter calls Tier 2 service with real wiring |
| Module boundary | Module A's public API consumed by Module B |
| Data format boundary | Serialization → deserialization round-trip |
| External resource | Real file system, test database, sandboxed HTTP |

### What to Mock vs Use Real

| Component | Approach |
|---|---|
| Own database | Real — use test instance, wipe between tests |
| Own file system | Real — use temp directory, clean up after |
| Own modules | Real — test actual wiring |
| External APIs (third-party) | Mock — deterministic, no network dependency |
| External services (auth, payment) | Mock at adapter boundary |
| Time/clock | Inject — pass timestamp as argument, ✗ read system clock in test |

### Integration Test Rules

- Test the contract between components, not internal implementation.
- Each integration test targets exactly one boundary crossing.
- Integration tests ✗ duplicate unit test coverage. If unit tests cover the logic, integration test covers only the wiring.
- Sandboxed resources are created fresh per test or per test suite. ✗ shared test databases across parallel test runs.
- Integration tests that require external services run in a separate test suite, clearly marked.

### Boundary Test Pattern

For every module public API:
1. Call through public interface with valid input → verify correct output.
2. Call with invalid input → verify structured error (not crash).
3. Call with boundary values (empty, max size, unicode, null-equivalent) → verify graceful handling.

---

## 5. E2E Test Rules

E2E tests verify complete user-facing workflows from entry point to final output.

### When to Write E2E Tests

| Write E2E | ✗ Skip E2E |
|---|---|
| Critical user workflow (happy path) | Internal utility functions |
| Revenue/data-loss path | Formatting or display variations |
| Multi-module orchestration | Anything unit + integration already covers |
| Regression for a production incident | Exploratory one-off scenarios |

### E2E Rules

- Maximum 20 E2E tests per project. If more needed, push logic down to unit/integration layer.
- Each E2E test has explicit speed budget: < 5 seconds. Exceeding budget = test redesign or architecture problem.
- E2E tests run against a fully assembled system with sandboxed external resources.
- ✗ E2E tests against production systems. Always sandboxed/test environment.
- E2E tests verify observable output (files created, API responses, CLI stdout), ✗ internal state.

### E2E Test Structure

Every E2E test follows: **Arrange → Act → Assert → Cleanup**

| Phase | Rule |
|---|---|
| Arrange | Create all preconditions: temp dirs, test data, config |
| Act | Execute single user-level operation |
| Assert | Verify observable output matches expected |
| Cleanup | Remove all created resources — even on test failure |

---

## 6. Contract Tests

Contract tests verify a module's public API behaves as documented. They survive refactors — internal restructuring ✗ breaks contract tests.

### Purpose

- Lock public API behavior so internal changes are safe.
- Detect accidental breaking changes before release.
- Serve as executable documentation of module capabilities.

### What to Contract-Test

| Target | Contract Assertion |
|---|---|
| Public function signature | Accepts declared input types, returns declared output types |
| Public function behavior | Given specific input, produces specific output |
| Error contract | Invalid input returns structured error, ✗ crash |
| Absence handling | Missing/optional inputs return explicit absence, ✗ null |
| Idempotency | Same input twice → same output (per `architecture/STANDARDS.md §4`) |

### Contract Test Rules

- One contract test file per module public API.
- Contract tests reference only public API. ✗ import internal/private functions.
- Contract tests ✗ break when implementation changes. If they do, either the refactor broke the contract (bug) or the contract test was testing implementation (fix the test).
- When public API changes, update contract tests first, then implementation. Contract-first development per `architecture/STANDARDS.md §1` principle 9.
- Contract tests run in unit test suite (fast, no I/O) for Tier 0–2 modules. Integration test suite for Tier 3 modules.

---

## 7. Property-Based Testing

Property-based tests generate random inputs and verify invariants hold across all of them. Complement — ✗ replace — example-based tests.

### When to Use

| Use Property-Based | ✗ Not Suitable |
|---|---|
| Pure functions with wide input space | I/O-dependent functions |
| Serialization/deserialization round-trips | UI workflows |
| Parsers, encoders, decoders | Tests requiring specific fixtures |
| Mathematical/algebraic operations | Tests with complex preconditions |
| Data structure operations (sort, filter, merge) | Integration with external services |

### Common Invariants

| Invariant | Example Application |
|---|---|
| Round-trip | `decode(encode(x)) == x` for all valid x |
| Idempotency | `f(f(x)) == f(x)` for normalizers, formatters |
| Monotonicity | Adding items never decreases count |
| Preservation | Transform preserves size, sum, or key set |
| Commutativity | `merge(a, b) == merge(b, a)` where order irrelevant |
| No crash | Function ✗ crashes on any valid input type |

### Rules

- Minimum 100 generated cases per property. Default 1000 for production code.
- Seed random generation so failures are reproducible. Log the seed on failure.
- When a property test finds a failing case, add that case as a permanent example-based test.
- Property tests run in unit test suite — must stay fast. If generation is expensive, reduce case count but ✗ skip.

---

## 8. Test Naming Convention

Test names describe behavior, not implementation. A failing test name tells you what broke without reading the test body.

### Pattern

```
test_<function_name>_<scenario>_<expected_outcome>
```

### Rules

| Rule | ✓ Good | ✗ Bad |
|---|---|---|
| Name describes behavior | `test_validate_email_missing_at_sign_returns_error` | `test_validate_email_1` |
| Name states expected outcome | `test_parse_date_empty_string_returns_none` | `test_parse_date_edge_case` |
| Name includes scenario | `test_merge_configs_both_empty_returns_empty` | `test_merge_configs` |
| ✗ implementation details | — | `test_uses_regex_for_validation` |
| ✗ test numbering | — | `test_case_47` |

### Naming Elements

| Element | Purpose | Required |
|---|---|---|
| Function/method name | What is being tested | Yes |
| Scenario/condition | Under what conditions | Yes |
| Expected outcome | What the result is | Yes |
| Module prefix | Disambiguate across modules | Only if needed |

---

## 9. Test Organization

### File Structure

| Convention | Rule |
|---|---|
| Test file location | Mirror source tree: `src/engine/parser.ext` → `tests/engine/test_parser.ext` |
| Test file naming | `test_` prefix: `test_<module>.ext` |
| Test data directory | `tests/fixtures/` — checked into version control |
| Generated test data | `tests/tmp/` — gitignored, cleaned after each run |
| Shared test utilities | `tests/helpers/` — test-only code, ✗ imported by production code |

### Test Suite Organization

| Suite | Contents | Run Frequency |
|---|---|---|
| Unit | Tier 0–2 tests, property tests, contract tests | Every commit |
| Integration | Tier boundary tests, module boundary tests | Every commit |
| E2E | Full workflow tests | Before merge / release |
| Performance | Benchmark tests, load tests | On demand / nightly |

### Test Data Management

- Test fixtures are minimal — smallest data that exercises the scenario.
- ✗ copy production data into fixtures. Create purpose-built test data.
- Large fixtures (> 1KB) go in `tests/fixtures/`, referenced by path.
- Small fixtures (< 1KB) live inline in the test function.
- Binary test fixtures include a comment explaining what they contain and how to regenerate.

### Test Helpers

- Shared assertion helpers reduce duplication across tests.
- Test helpers are test code — same quality standards, but ✗ tested themselves (avoid infinite recursion).
- Test helpers ✗ contain business logic. If they do, extract to production code and test that instead.

---

## 10. Mocking Rules

Mocking is a last resort, not a convenience. Over-mocking creates tests that pass with broken code.

### When Mocking is Allowed

| Context | Mocking Status |
|---|---|
| Tier 0–1 unit tests | ✗ Forbidden. Functions are pure — no mocks needed. |
| Tier 2 unit tests | Inject hand-written fakes for lower-tier interfaces |
| Tier 3 unit tests | Mock external dependencies (network, third-party APIs) |
| Integration tests | Mock only resources outside project boundary |
| E2E tests | ✗ Forbidden. Use sandboxed real resources. |
| Contract tests | ✗ Forbidden. Test real implementation. |

### Mock vs Fake vs Stub

| Type | Definition | When to Use |
|---|---|---|
| Fake | Working implementation with shortcuts (in-memory DB) | Tier 2 tests, integration tests |
| Stub | Returns canned responses, no logic | Tier 3 external service boundaries |
| Mock (with verification) | Records calls, asserts interaction | ✗ Avoid. Tests implementation, not behavior. |

### Rules

- ✗ mock what you own. If you control the code, test with the real implementation or a hand-written fake.
- Mock only what you ✗ control: third-party APIs, external services, system clock.
- ✗ mock libraries (auto-generating mocks from interfaces). Write explicit fakes that implement the contract.
- If a function needs 3+ mocks to test, the function does too much. Split it. See `architecture/STANDARDS.md §4`.
- Mocked behavior must match real behavior. When the real service changes, update mocks immediately.
- ✗ mock data access for Tier 0–1 functions. If they need data, it arrives as arguments.

---

## 11. Coverage Strategy

Coverage measures which code paths tests exercise. Meaningful coverage targets behavior, not line count.

### What to Measure

| Metric | Use For | Target |
|---|---|---|
| Branch coverage | Decision paths exercised | Primary metric |
| Line coverage | Code reachability | Secondary metric |
| Function coverage | Public API surface tested | Must be 100% for Tier 0–1 |
| Mutation coverage | Test effectiveness (do tests catch bugs?) | Spot-check critical modules |

### Coverage Rules

- ✗ chase percentage. 80% meaningful coverage > 95% superficial coverage.
- Minimum thresholds by tier:

| Tier | Branch Coverage | Function Coverage |
|---|---|---|
| 0 — Kernel | 95% | 100% |
| 1 — Engine | 90% | 100% |
| 2 — Service | 80% | 90% |
| 3 — Interface | 60% | 70% |

- Coverage drops trigger investigation, ✗ automatic blocking. New code without tests is the signal, not the number.
- ✗ write tests purely to increase coverage. Every test must verify meaningful behavior.
- Exclude from coverage measurement: test code, generated code, configuration boilerplate, dependency wrappers.
- Coverage reports run in CI. Trend tracked over time — sustained decline = problem.

### What Low Coverage Signals

| Coverage Pattern | Likely Cause |
|---|---|
| Low Tier 0–1 coverage | Missing tests — fix immediately |
| Low Tier 3 coverage | Expected — I/O heavy, harder to test |
| High Tier 3, low Tier 1 | Logic buried in I/O layer — refactor per architecture standards |
| Coverage drops on PR | New code without tests — review required |

---

## 12. Test Data

### Principles

- Tests use deterministic data. ✗ random data (except property-based tests with seeded generators).
- Test data is purpose-built for each scenario. ✗ shared "golden" datasets reused across unrelated tests.
- ✗ production data in tests. Privacy risk, brittleness, and non-determinism.

### Factory Pattern

Build test data through factory functions, not raw literals.

| Rule | Rationale |
|---|---|
| One factory per domain type | Centralized defaults, consistent creation |
| Factory returns valid instance by default | Test specifies only what differs from default |
| Factory accepts overrides for each field | Scenario-specific values without rebuilding everything |
| Factories compose | Complex objects built from simpler factories |

### Fixture Rules

| Type | Location | Lifecycle |
|---|---|---|
| Static fixtures (reference data) | `tests/fixtures/` — version controlled | Permanent |
| Generated fixtures (temp files, DBs) | `tests/tmp/` — gitignored | Created per test, deleted after |
| Inline data (small, specific) | Inside test function body | Per test |

### Rules

- Fixture files are read-only during tests. ✗ write to fixture directory.
- Generated data uses deterministic seeds. Same test run = same data every time.
- Date/time values in test data are hardcoded constants. ✗ `now()` in tests.
- File path fixtures use platform-agnostic separators or build paths programmatically.

---

## 13. Test Independence

Every test runs in isolation. ✗ shared state, ✗ execution order dependency, ✗ side effects leaking between tests.

### Rules

| Rule | Violation Example |
|---|---|
| Each test creates its own data | Test B reads data created by Test A |
| Each test cleans up its own resources | Temp files accumulate across tests |
| Tests pass when run individually | Test passes in suite, fails alone |
| Tests pass in any order | Test C depends on Test B running first |
| Tests pass when run in parallel | Two tests write to same file |
| ✗ shared mutable state | Module-level variable modified by tests |

### Isolation Mechanisms

| Mechanism | When to Use |
|---|---|
| Fresh instance per test | Default — each test sets up its own state |
| Temp directory per test | File system tests — unique dir, cleaned on teardown |
| Transaction rollback | Database tests — wrap in transaction, rollback after |
| Process isolation | Tests that modify environment variables or globals |
| Copy-on-write snapshots | Large data sets — snapshot before, restore after |

### Detecting Violations

- Run tests in random order regularly. Fixed-order-only passes = hidden dependency.
- Run tests in parallel. Failures under parallelism = shared state.
- Run each test in isolation (single test mode). Failures = missing setup.

---

## 14. Performance Tests

Performance tests verify that operations complete within budget. Not load testing — that belongs in `devops/STANDARDS.md`.

### When to Add Performance Tests

| Add Performance Test | ✗ Not Needed |
|---|---|
| Operation has explicit latency SLA | Internal utility with no timing requirement |
| Operation processes user-visible data | One-time migration script |
| Regression detected in past | Stable operation with no history of slowdown |
| Operation scales with input size | Constant-time operations |

### Performance Test Rules

- Each performance test defines explicit budget: `operation X completes in < N ms for input size M`.
- Budget thresholds are per-operation, not aggregate. ✗ "suite runs in < 10s" — useless.
- Performance tests measure wall clock time. Run on consistent hardware (CI runner, not laptop).
- Performance tests run separately from unit/integration suites. ✗ slow down regular test runs.
- Track results over time. Compare against baseline. Alert on regression > 20%.

### Budget Table Template

| Operation | Input Size | Budget | Measured |
|---|---|---|---|
| Parse config | 100 entries | < 50ms | — |
| Validate batch | 1000 records | < 200ms | — |
| Transform dataset | 10K rows | < 1s | — |
| Full pipeline | Reference dataset | < 5s | — |

Fill `Measured` column in CI. Budget breach = failing test.

---

## 15. Scale Matrix

Testing depth scales with project complexity. Apply rules proportionally.
See `architecture/STANDARDS.md §12` for full scale definitions.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Test pyramid (§1) | Informal — some tests | Unit + integration | Full pyramid with ratios |
| Tier mapping (§2) | ✗ required | Test Tier 0–1 | Test all tiers |
| Unit tests (§3) | Core logic only | All public functions | All functions + edge cases |
| Integration tests (§4) | ✗ required | Module boundaries | All boundaries + data flow |
| E2E tests (§5) | ✗ required | Critical path only | All user workflows |
| Contract tests (§6) | ✗ required | ✗ required | All public module APIs |
| Property-based (§7) | ✗ required | Parsers + serializers | All pure functions with wide input |
| Naming convention (§8) | Informal | Consistent within project | Strict pattern enforcement |
| Test organization (§9) | Same file ok | Mirrored tree | Full structure + suites |
| Mocking rules (§10) | Pragmatic | Follow tier rules | Strict — no mock overuse |
| Coverage (§11) | ✗ tracked | Track Tier 0–1 | Full tracking + thresholds |
| Test data (§12) | Inline ok | Factories for domain types | Full factory + fixture system |
| Independence (§13) | Best effort | No shared state | Random order + parallel safe |
| Performance (§14) | ✗ required | Critical operations | Full budget table |

### Scale Transitions

When graduating from PoC → Small → Production:
1. Add tests incrementally alongside feature work. ✗ "testing sprint" after the fact.
2. Prioritize Tier 0–1 unit tests first — highest value per effort.
3. Add integration tests at module boundaries next.
4. E2E and performance tests last — only when architecture is stable.

---

## 16. Testing Checklist

### New Project

- [ ] Test directory structure created mirroring source tree
- [ ] Test suites defined: unit, integration, E2E, performance
- [ ] Test naming convention agreed and documented
- [ ] Test data strategy decided: factories vs fixtures vs inline
- [ ] Coverage thresholds set per tier
- [ ] CI runs unit + integration on every commit

### New Module

- [ ] Unit tests for every public function
- [ ] Edge cases: empty input, max input, invalid input, absence
- [ ] Contract tests for public API if production-scale project
- [ ] Integration tests for tier/module boundary crossings
- [ ] ✗ mocks in Tier 0–1 tests
- [ ] All tests pass in isolation and random order

### New Function

- [ ] Function classified as logic or shell (`architecture/STANDARDS.md §4`)
- [ ] Logic function → unit test with data in, assert data out
- [ ] Shell function → integration test with sandboxed I/O
- [ ] Test name describes behavior: `test_<function>_<scenario>_<outcome>`
- [ ] Boundary values tested: zero, one, many, max, empty, absent
- [ ] Error paths tested: invalid input returns structured error

### Bug Fix

- [ ] Failing test written first — reproduces the bug
- [ ] Test added at lowest possible layer (unit > integration > E2E)
- [ ] Fix applied — test passes
- [ ] No other tests broken by the fix

### Pre-Release

- [ ] All test suites pass: unit, integration, E2E
- [ ] Coverage thresholds met per tier
- [ ] No flaky tests in suite
- [ ] Performance budgets met
- [ ] Contract tests pass — no accidental API breaks
