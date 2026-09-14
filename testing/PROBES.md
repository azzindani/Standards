# Probe Testing Standards

> Rules for probes — tests that exercise a running deployment the way a user does, assert on the response and the emitted logs together, and stand in for manual QA.

**ID** `testing/probes` · **Tier** Core · **Version** 1.0
**Owns** probe definition + boundary against health checks · probe taxonomy · dual assertion (response + log) · probe as a release gate · continuous probe scheduling · probe data + side-effect policy · environment placement · failure triage + noise budget · probe coverage of user journeys · probe authoring from incidents
**Defers to** pyramid · size classes · tier classification · coverage gate · flake budget · mocking policy → [testing](STANDARDS.md) · reality dimensions · faults · adversarial input · what tests assert on signals → [testing/reality](REALITY.md) · load · soak · chaos · penetration → [testing/pressure](PRESSURE.md) · health check semantics · SLOs · alert design · metrics · log levels + content → [observability](../observability/STANDARDS.md) · log store · correlation keys · verbosity modes · query surface → [observability/logs](../observability/LOGS.md) · quality dimensions · rubrics · failure taxonomy → [expectation](../expectation/STANDARDS.md) · level model · absent-evidence rule → [maturity](../maturity/STANDARDS.md) · gate placement in the pipeline · deploy stages → [cicd](../cicd/STANDARDS.md) · environments · rollback · incident response → [devops](../devops/STANDARDS.md) · credential storage · test account policy → [security](../security/STANDARDS.md) · eval sets for model-backed behavior → [llm/evaluation](../llm/EVALUATION.md)
**Load with** [testing](STANDARDS.md) · [observability/logs](../observability/LOGS.md) · [maturity](../maturity/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [What a Probe Is](#2-what-a-probe-is)
3. [Taxonomy](#3-taxonomy)
4. [Dual Assertion](#4-dual-assertion)
5. [Authoring](#5-authoring)
6. [Data and Side Effects](#6-data-and-side-effects)
7. [Placement](#7-placement)
8. [Scheduling](#8-scheduling)
9. [Gates](#9-gates)
10. [Triage](#10-triage)
11. [Coverage](#11-coverage)
12. [Anti-Patterns](#12-anti-patterns)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Probes replace manual QA, ✗ unit tests | They cover what a person clicking through would have caught, on a real deployment |
| The response alone is half the answer | A correct-looking response over a broken internal path is the failure mode probes exist to catch (§4) |
| Every probe is a user's question | "Can someone log in and see their data" — ✗ "does `/health` return 200" |
| Ran and green, or it proves nothing | A probe suite that has not run against this deployment is absent evidence → [maturity](../maturity/STANDARDS.md) |
| Noise destroys the signal | A probe that cries wolf is turned off within a week, taking its real coverage with it (§10) |
| Probes are code | Versioned, reviewed, owned, and deleted when the journey they cover is retired |
| Production probes touch production | Which means their data and side effects are designed, ✗ improvised (§6) |

---

## 2. What a Probe Is

A probe runs against a **deployed, running** system over its real interface, asserts on the response **and** on the signals the system emitted, and reports a machine-readable outcome.

Boundaries against neighbours:

| Not a probe | Difference |
|---|---|
| Health check | The system reporting on itself, cheap and constant. A probe exercises a journey from outside → [observability §7](../observability/STANDARDS.md#7-health-checks) |
| Integration test | Runs in CI against a composed environment, may use fixtures and fakes. A probe runs against a deployment, with no internal seams available → [testing](STANDARDS.md) |
| E2E test | Runs on a build in the pipeline. A probe runs on an environment, repeatedly, after the pipeline finished |
| Load test | Measures behavior under volume. A probe measures correctness at one request → [testing/pressure](PRESSURE.md) |
| Smoke test | A probe subset run once after deploy. Smoke is a schedule (§8), ✗ a different kind of test |

Rules:

- A probe uses only interfaces a real client has: the public API, the UI, the CLI, the queue. ✗ reach into the database to verify, except where a §4 assertion has no other source.
- A probe's failure names the journey, the step, the environment, and the correlation key of the run it produced → [observability/logs §4](../observability/LOGS.md#4-correlation).
- A probe that cannot fail is not a test. Each one is verified to fail against a deliberately broken target before it is trusted.

---

## 3. Taxonomy

| Kind | Asserts |
|---|---|
| Availability | The entry point answers within its budget, with the expected shape |
| Journey | A multi-step user path completes: sign in → act → observe the result |
| Contract | Live responses still satisfy the published schema → [api](../api/STANDARDS.md) |
| Data integrity | A write is readable, correct, and consistent across the paths that expose it |
| Idempotency | Repeating the operation with the same key produces one effect |
| Permission | A caller lacking rights is refused — and the refusal is audited → [security](../security/STANDARDS.md) |
| Dependency | Each external dependency is reachable, and its degradation is visible before a user sees it |
| Recovery | The documented recovery path works: retry succeeds, fallback engages, circuit closes → [testing/reality §11](REALITY.md#11-recovery-verification) |
| Freshness | Data a user sees is within its stated staleness budget |
| Cost | The journey's resource and token consumption stays inside budget → [llm §10](../llm/STANDARDS.md#10-token-and-cost-budgets) |

Rules:

- Every critical journey has at least an availability probe and a journey probe.
- Permission probes are written for every role boundary, including the negative case. An untested denial is an assumed one.
- A probe kind absent for a shipped surface is a coverage gap, recorded as such (§11), ✗ silently missing.

---

## 4. Dual Assertion

A probe asserts on the response **and** on what the system logged while producing it. Either alone passes a system that is quietly broken.

| Assert on the response | Assert on the log |
|---|---|
| Status, shape, schema conformance | The expected `event` sequence occurred, in order |
| Field values and invariants | No `error`-level record appeared on a passing path |
| Latency within budget | No silent fallback, retry storm, or degraded-mode record |
| Correct refusal for the negative case | The refusal was audited with the expected code |
| Idempotent repeat yields one effect | Exactly one state-change record, ✗ two |

Rules:

- The probe retrieves the log records by the correlation key it sent or received, ✗ by scanning a window and guessing which are its own → [observability/logs §7](../observability/LOGS.md#7-query-surface).
- Assert on `event` and `code`, never on message prose → [testing/reality §10](REALITY.md#10-observability-assertions).
- A green response over an error-level record is a **failure**. That combination is the single most valuable thing a probe reports: it means the system is failing without telling anyone.
- An expected error path asserts the error record exists. Absence of the record is as much a failure as the wrong behavior.
- Where verbosity is raisable per run, the probe requests the verbosity its assertions need → [observability/logs §5](../observability/LOGS.md#5-verbosity-modes), ✗ relies on production's default.
- A probe that cannot reach the logs asserts on the response only, and declares itself half-covered. ✗ let the gap read as full coverage.

---

## 5. Authoring

| Rule | Detail |
|---|---|
| Written from the journey, ✗ the code | Derived from what a user does. A probe written by reading the implementation tests the implementation's assumptions |
| One journey per probe | A probe asserting six journeys reports one failure for six causes |
| Named for the question | "checkout completes with a saved card" — ✗ "test_api_3" |
| Deterministic | Same inputs, same verdict. Non-deterministic dependencies are pinned, seeded, or asserted as ranges |
| Self-contained | Creates what it needs, asserts, cleans up (§6). ✗ depend on another probe having run first |
| Budgeted | Wall-clock budget per probe; exceeding it is a failure, ✗ a slow pass |
| Fails loudly and specifically | The failure message names the step, the expectation, the actual, and the correlation key |
| Every incident becomes a probe | A failure that reached a user gets a probe reproducing it before the fix is closed → [devops](../devops/STANDARDS.md) |

---

## 6. Data and Side Effects

| Rule | Detail |
|---|---|
| Dedicated identities | Probes run as marked test accounts, never as a real user's account |
| Tagged records | Everything a probe creates carries a marker so it is excludable from analytics, billing, and reports |
| Cleanup is part of the probe | Created state is removed, or expires, by the probe's own action — ✗ by a cleanup job nobody monitors |
| Cleanup failure is a failure | An uncleaned probe run reports, ✗ leaks quietly until the table is full |
| Irreversible actions are stubbed at the edge | Payments, emails, messages to third parties, and destructive operations route to a sandbox in production probes |
| ✗ mutate real users' data | A probe that writes to a real account is an incident waiting for a schedule |
| Isolated from real metrics | Probe traffic is excluded from SLO, conversion, and usage metrics — its own results are tracked separately → [observability](../observability/STANDARDS.md) |
| Secrets like any other credential | Probe credentials are scoped, rotated, and stored as secrets → [security](../security/STANDARDS.md) |
| Rate-limited | Probes respect the limits real clients face, and never become the load that breaks the thing they watch |

---

## 7. Placement

| Environment | Probes run | Purpose |
|---|---|---|
| Ephemeral / PR | Journey + contract subset | Catch a break before it merges |
| Staging | Full suite | Release gate (§9) |
| Production, post-deploy | Full suite, non-destructive subset | Confirm the deploy, trigger rollback |
| Production, continuous | Availability · journey · dependency · freshness | Detect what monitoring alone misses (§8) |

Rules:

- A probe that cannot run safely in production is marked as such and runs in staging only — ✗ deleted, ✗ silently skipped.
- Staging probes run against a staging deployment shaped like production: same engine versions, same topology → [database/engines §9](../database/ENGINES.md#9-environment-parity).
- Probes run from outside the deployment's network where a real user is outside it. A probe inside the cluster does not test the edge.
- Multi-region deployments probe each region. A green probe against one region says nothing about the others.

---

## 8. Scheduling

| Trigger | Suite |
|---|---|
| Post-deploy | Full non-destructive suite, before the deploy is declared done |
| Continuous | Availability + critical journeys, at a declared interval |
| Pre-release | Full suite against staging (§9) |
| On alert | Relevant probes run on demand to confirm or clear an alert |
| On incident close | The probe reproducing the incident, to confirm the fix holds |

Rules:

- The continuous interval is set against the detection budget: how long a broken journey may go unnoticed. ✗ picked because it looked reasonable.
- Probe runs are logged like any other run, with a `run_id` and a stored verdict → [observability/logs](../observability/LOGS.md). A probe result nobody stored cannot show a trend.
- Consecutive failures escalate; a single failure retries once to separate a transient from a break — at most once, and a second failure is real.
- A probe suite that has not run inside its interval is reported as **stale**, ✗ as passing. Absent evidence is never a pass.
- Scheduled probes are monitored themselves: a scheduler that stopped firing must alert, or the silence reads as health.

---

## 9. Gates

| Gate | Rule |
|---|---|
| Release | The full probe suite passes against staging before promotion → [cicd](../cicd/STANDARDS.md) |
| Post-deploy | Failure triggers the documented rollback, automatically where rollback is automated → [devops](../devops/STANDARDS.md) |
| Critical probes are absolute | Probes marked critical pass at 100%. ✗ traded against an aggregate |
| Staleness blocks | A gate reading a result older than its interval fails, ✗ passes on the last known green |
| Half-covered is declared | A probe asserting only on the response (§4) is counted separately from a fully-asserting one |
| Maturity evidence | Probe results are the evidence for the observed level, ✗ a declaration → [maturity](../maturity/STANDARDS.md) |

---

## 10. Triage

A probe failure is a real failure until proven otherwise. "Probably flaky" is a diagnosis nobody made.

| Step | Rule |
|---|---|
| Classify | Product break · environment break · dependency break · probe defect. Recorded per failure, ✗ assumed |
| Reproduce | The failure's correlation key retrieves the full record set; the probe is re-runnable on demand against the same target |
| Fix the right thing | A probe defect is fixed as a bug in the probe, with the same urgency as a product bug |
| Noise budget | Probes have a false-positive budget like the flake budget → [testing](STANDARDS.md). Over budget → the probe is fixed or quarantined with an owner and a deadline |
| Quarantine is temporary | A quarantined probe keeps running and reporting, is excluded from the gate, and has a dated owner. ✗ an indefinite state |
| ✗ weaken the assertion to get green | Loosening a probe to stop it failing removes the coverage and keeps the cost |
| Silence is investigated | A probe that stopped reporting is treated as failing (§8) |

---

## 11. Coverage

Probe coverage is measured in journeys, ✗ in lines.

| Rule | Detail |
|---|---|
| Journey inventory | Every critical user journey is listed, with its probes named against it. A journey with no probe is a visible gap |
| Critical set defined | Which journeys are critical is a product decision, written down → [expectation](../expectation/STANDARDS.md) |
| Every role boundary | Each permission boundary has a positive and a negative probe (§3) |
| Every external dependency | Each has a probe that detects its degradation |
| Gaps are reported, ✗ omitted | An unprobed journey appears in the coverage report as unprobed. Silence reads as covered |
| Retired with the journey | A probe for a removed feature is deleted, ✗ left skipped |
| Reviewed on change | A change to a critical journey updates its probes in the same change |

---

## 12. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Probing `/health` and calling it covered | Confirms the process is up, ✗ that anything works | Journey probes (§3) |
| Asserting on the response only | Passes a system failing silently underneath | Dual assertion (§4) |
| Matching on log message text | Breaks on a wording change, misses the real signal | Assert on `event` and `code` (§4) |
| Scanning a time window for "my" logs | Picks up another run's records and reports the wrong verdict | Retrieve by correlation key (§4) |
| Probe chained to a previous probe's state | One failure cascades into a wall of red | Self-contained probes (§5) |
| Probes as a real user | A probe run corrupts real data | Dedicated tagged identities (§6) |
| Probe traffic in SLO metrics | The SLO measures the probe, not the users | Exclude and track separately (§6) |
| Running probes only at deploy | A break between deploys goes unnoticed for days | Continuous schedule (§8) |
| Stale result read as green | The gate passes on evidence from last month | Staleness fails the gate (§9) |
| "Flaky, ignore it" | The one real failure is dismissed with the noise | Classify every failure (§10) |
| Assertion loosened to stop the noise | Cost kept, coverage lost | Fix the probe or quarantine it (§10) |
| Indefinite quarantine | A permanent hole reported as a temporary one | Dated owner, or delete (§10) |
| Unprobed journeys absent from the report | The gap is invisible to everyone | Report gaps explicitly (§11) |
| Probes replacing unit tests | Slow, coarse, and they localize nothing | Probes sit above the pyramid → [testing](STANDARDS.md) |

---

## 13. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Suite | Availability on the main entry point | Every critical journey, plus permission and dependency probes | Full taxonomy (§3), per region |
| Assertion | Response only, declared half-covered | Response + log by correlation key | Plus cost and freshness budgets |
| Schedule | On deploy | Post-deploy + continuous at a detection budget | Continuous with per-journey intervals and on-alert runs |
| Gate | Advisory | Release gate + post-deploy rollback trigger | Critical probes at 100%, staleness blocks |
| Data | Manual cleanup | Tagged identities, self-cleaning, sandboxed side effects | Isolated tenant, rate-limited, fully excluded from metrics |
| Triage | Read the failure | Classified per failure, noise budget enforced | Auto-correlated with deploys and dependency status |
| Coverage | Main journey | Journey inventory with named gaps | Gap report gates the release |

---

## 14. Checklist

- [ ] Every critical user journey is listed, with the probes covering it named
- [ ] Journeys with no probe appear in the coverage report as gaps, not as silence
- [ ] Probes run against a deployed system over real client interfaces
- [ ] Every probe asserts on the response **and** on the emitted log records
- [ ] Log assertions retrieve records by correlation key and match on `event` and `code`, never on prose
- [ ] A green response accompanied by an error-level record fails the probe
- [ ] Expected error paths assert that the error record exists
- [ ] Probes asserting on the response only are counted as half-covered
- [ ] Every probe has been observed to fail against a deliberately broken target
- [ ] Each role boundary has a positive and a negative permission probe
- [ ] Each external dependency has a probe that detects its degradation
- [ ] Probes run as tagged test identities, never as real users
- [ ] Probe-created state is cleaned up by the probe, and cleanup failure is reported
- [ ] Irreversible side effects are routed to a sandbox in production probes
- [ ] Probe traffic is excluded from SLO, usage, and billing metrics
- [ ] Continuous probes run at an interval set by the detection budget
- [ ] A suite that has not run inside its interval reports as stale, not as passing
- [ ] The probe scheduler is itself monitored
- [ ] Probe results are stored with a run id so trends are readable
- [ ] The full suite gates release; failure post-deploy triggers the documented rollback
- [ ] Every failure is classified — product, environment, dependency, or probe defect
- [ ] Probes over the false-positive budget are fixed or quarantined with a dated owner
- [ ] No probe assertion has been loosened to silence a failure
- [ ] Every incident that reached a user has a probe reproducing it
