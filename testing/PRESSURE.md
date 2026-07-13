# Testing Pressure Standards

> System-level testing for the worst day: sustained load to the breaking point, cascading and simultaneous failures, and an active adversary probing a running system.

**ID** `testing/pressure` · **Tier** Core · **Version** 1.0
**Owns** stress · endurance · capacity · multi-fault survival · cascading failure · thundering herd · chaos engineering · penetration testing · manual red-team boundary · custom pressure harness · pressure infrastructure
**Defers to** pyramid · size classes · coverage gate · contract tests · flake budget → [STANDARDS.md](STANDARDS.md) · single-fault injection · adversarial input generation · recovery verification · observability assertions → [REALITY.md](REALITY.md) · threat model · vulnerability severity model · authn/authz rules · secrets → [security](../security/STANDARDS.md) · pipeline stages · deploy gates · rollback automation → [cicd](../cicd/STANDARDS.md) · infrastructure provisioning · cost · backup + DR → [devops](../devops/STANDARDS.md) · SLO definition · alert design → [observability](../observability/STANDARDS.md) · latency budgets · profiling → [performance](../performance/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [REALITY.md](REALITY.md) · [security](../security/STANDARDS.md) · [devops](../devops/STANDARDS.md)

---

## Table of Contents

1. [Scope](#1-scope)
2. [Principles](#2-principles)
3. [Pressure](#3-pressure)
4. [Survival](#4-survival)
5. [Penetration](#5-penetration)
6. [Custom Harness](#6-custom-harness)
7. [Manual Red-Team Boundary](#7-manual-red-team-boundary)
8. [Pipeline and Gating](#8-pipeline-and-gating)
9. [Infrastructure](#9-infrastructure)
10. [Scale Matrix](#10-scale-matrix)
11. [Checklist](#11-checklist)

---

## 1. Scope

Per-operation correctness under reality lives in [REALITY.md](REALITY.md): one fault, one adversarial input, one clock skew against one function. This standard covers the **assembled system under pressure** — load saturating, dependencies cascading, many things failing at once, an attacker actively probing.

| [REALITY.md](REALITY.md) — per operation | PRESSURE.md — whole system |
|---|---|
| Per-operation latency budget (§13) | Sustained load to the breaking point |
| Single fault injection (§3) | Multi-fault + cascading failure |
| Input-boundary adversarial (§4) | Full-system penetration — auth · authz · session · exfil |
| Race stress (§5, ~100 ops) | Capacity stress (10K–100K+ ops) |
| Passive state accumulation (§8) | Endurance under active sustained load |
| Recovery from a single fault (§11) | Survival across chained dependency loss |

- Requires **dedicated infrastructure** (§9) and runs **nightly + pre-release**, ✗ per-commit.
- Audience is SRE + security review, ✗ standard PR review.
- Required from L3+ per the confidence ladder → [STANDARDS.md](STANDARDS.md).

---

## 2. Principles

| Principle | Rule |
|---|---|
| Find the breaking point | Production needs known limits. ✗ "we think it handles N" — measure it |
| Multi-fault is the normal case | Real outages are 3+ failures interleaved. Test combinations, ✗ singles only |
| Pen tests are continuous | Run every nightly. Adversaries ✗ wait for the quarterly audit |
| Custom-built, ✗ bolted on | Tests live in the repo using the project framework (§6). ✗ external scanners as primary defense |
| Observation > assertion | Pressure tests measure response curves; pass/fail is one signal among many |
| Reproducible failure | Every failure found becomes a permanent regression test in the [STANDARDS.md](STANDARDS.md) suite |
| Pressure = production-shaped | Synthetic load mirrors production traffic distribution, ✗ uniform RPS |
| Survival is a property, ✗ a feature | Designed in via architecture, proven by these tests |

### Non-negotiables

- Run against a production-shaped environment — sandboxed but full-stack. ✗ test doubles in production code paths.
- ✗ pressure-test against production. Staging | dedicated load environment only.
- Every failure spawns a permanent regression test (§14 effectiveness audit → [REALITY.md](REALITY.md)).
- Pen tests against own systems only. Authorization documented before any run.
- Findings tracked with: severity · reproducer · owner · resolution SLO.

---

## 3. Pressure

Sustained heavy load. Three sub-dimensions:

| Sub-dimension | Question answered | Stop condition |
|---|---|---|
| Stress | What is the breaking point? | First sustained SLO violation or crash |
| Endurance | Does it stay healthy under sustained load? | Completes N hours without degradation |
| Capacity | What load can we serve at SLO with headroom? | Peak QPS where p99 stays within SLO |

### Stress

Push load past expected peak until the system breaks; find the bottleneck.

Measure: throughput ceiling (max RPS before SLO violation) · latency curve (p50 · p95 · p99 · p99.9 vs load) · error-rate curve (where errors begin, how they scale) · resource-saturation order (which of CPU · memory · FDs · DB conns · queue caps first) · failure mode at the limit (graceful degrade · timeout · crash · cascade) · recovery after overload (load drops → return to baseline?).

- Ramp load gradually (100 → 1K → 10K → 100K RPS over minutes). ✗ instant peak — it hides which limit hits first.
- Run with full observability — every metric, log, trace. A stress run is a data-collection event, ✗ a pass/fail.
- Document the bottleneck per run: "caps at 47K RPS; next bottleneck is the DB connection pool at 200 connections."
- Stress run ✗ blocks the pipeline by default. **Regression > 20% from baseline blocks** (§8).
- Production capacity = stress peak / 2 (50% headroom). Operating beyond requires explicit risk acceptance.

### Endurance

Sustained load over hours/days. Catches slow-burn failure invisible in short runs.

| Failure mode | Test |
|---|---|
| Memory leak under load | N-hour run at 70% capacity → RSS ✗ trends upward |
| Connection / FD leak | N-hour run → pool + FD count stable |
| Cache poisoning | N-hour run with evicting traffic → hit rate stable |
| Performance degradation | N-hour run → p99 drift < 10% |
| Background task pileup | N-hour run → queue depth bounded |
| Log volume / disk fill | N-hour run → log rotation works under load |
| Token / session exhaustion | N-hour run → auth subsystem ✗ exhaust |
| Time-of-day effects | Run across midnight + day boundaries → clock-rollover handled |

- Min duration: production **24 h** · staging **4 h** · per-release **1 h** sample.
- Load level: **70% of stress-tested peak** (sustainable production target).
- Monitoring throughout — periodic snapshots of every saturation metric.
- Endurance failure = **P1**, fix before release. ✗ "watch for now."
- Nightly for production-tier. Weekly minimum.

### Capacity

Find the SLO-conformant peak QPS with a safety margin.

| Output | Target |
|---|---|
| Peak QPS at SLO | RPS where p99 ≤ documented SLO **and** error rate ≤ 0.1% |
| Headroom-required QPS | Peak × 0.5 — operate below this in production |
| Bottleneck inventory | Ranked list: 1st, 2nd, … |
| Scaling efficiency | RPS per added compute unit — linear · sublinear · broken? |

- Capacity number is **published** — every team operating the system knows it.
- Re-measured on every release touching the request path. **Drift > 15% triggers investigation** (§8).
- Runs against fully production-shaped infra: same instance type · DB tier · cache · network topology. Half-scale gives half-truth.
- Capacity regression blocks release for production-tier projects.

---

## 4. Survival

Multi-fault, cascading, and chaos scenarios. Asks: *what happens when bad things happen together?*

| Category | Description |
|---|---|
| Multi-fault | 2+ independent faults at once (DB slow + cache miss + dep timeout) |
| Cascading | A fails → triggers B → triggers C (queue backs up → timeouts cascade upstream) |
| Region / zone loss | Entire AZ or region unreachable |
| Dependency cliff | Critical dependency returns 100% errors for N minutes |
| Slow-cascade | One slow dependency degrades the pipeline via queue buildup |
| Thundering herd | All clients retry at once after recovery → wave overwhelms the recovered service |
| Split brain | Network partition with both halves accepting writes |
| Time-of-failure shift | Failure during deploy · during migration · during traffic spike |

### Required survival tests by level

| Level (→ [STANDARDS.md](STANDARDS.md)) | Required |
|---|---|
| L3+ | Multi-fault: top 5 dependency-pair combinations |
| L4+ | + cascading: 3-deep dependency chain · thundering herd · slow cascade |
| L5 | + chaos: random fault injection · region loss · split brain · failure-during-deploy |

### Chaos engineering

Random fault injection in a production-shaped environment; discovers unknown unknowns.

Chaos actions: kill instance (random pod/process) · network partition (random AZ/service) · latency injection (random p99 spike) · packet loss (random % on random link) · clock skew (±N s on random node) · disk slow (I/O latency on random instance) · DNS failure (random service) · resource starvation (CPU/memory pressure on random node).

- Survival tests run in a **dedicated environment**, ✗ shared CI. Need isolated network + control of the injection layer (§9).
- Each scenario has a documented expected outcome: graceful degrade · partial unavailable · full unavailable. ✗ "see what happens."
- Multi-fault matrix: top 5 critical dependencies × 5 fault modes = **25 single-fault tests** + selected multi-fault combinations.
- Cascading test: drive to the brink, trigger one more fault → verify ✗ catastrophic collapse.
- Chaos suite runs nightly in pre-prod. Findings: **P1 if user-facing**, P2 if internal degrade only.
- ✗ chaos in production until: nightly pre-prod chaos ran 30+ days clean · automated rollback proven (→ [cicd](../cicd/STANDARDS.md)) · on-call accepts the game-day exercise.
- Game days: quarterly manual chaos exercises with the full team.
- Every survival failure becomes a permanent regression test in the nightly suite.

### Recovery from survival

Pairs with recovery verification (→ [REALITY.md](REALITY.md)). After any scenario:

- All cleared faults → system returns to baseline within the documented SLO.
- ✗ data loss · ✗ duplicate effect · ✗ orphaned state.
- Pending operations complete or fail with a structured error — ✗ hang.
- Operator-visible signal that the scenario occurred (alert fired · receipt written).

---

## 5. Penetration

Full-system attack simulation. Distinct from input-boundary adversarial testing (→ [REALITY.md](REALITY.md)). Threat model + vulnerability severity model + authn/authz rules → [security](../security/STANDARDS.md); this standard owns **running the attack against the assembled system**.

| Category | Examples |
|---|---|
| Authentication | Token forgery · brute force · password-reset abuse · 2FA bypass · session fixation · auth timing attacks |
| Authorization | Vertical privilege escalation · IDOR (horizontal) · forced browsing · API role bypass · tenant boundary crossing |
| Session | Hijack · prediction · CSRF · cookie tampering · token replay · session-not-invalidated-on-logout |
| Data exfiltration | Mass enumeration · pagination abuse · search abuse · export-endpoint abuse · debug endpoints · GraphQL introspection in prod |
| Server-side | SSRF · XXE · template injection · deserialization · path traversal · upload-then-execute · ZIP slip |
| Logic flaws | Race-condition exploits (double-spend) · workflow bypass · price manipulation · state-machine skipping |
| Side channels | Timing attacks · cache attacks · error-message leak · enumeration via response time |
| Supply chain | Dependency confusion · typosquatting · poisoned cache · malicious post-install |
| Infrastructure | Exposed cloud metadata · open ports · misconfigured TLS · default creds · public buckets |

### Required by level

| Level (→ [STANDARDS.md](STANDARDS.md)) | Required categories |
|---|---|
| L3 | Auth · authz · session · server-side · infrastructure |
| L4 | + data exfiltration · logic flaws |
| L5 | + side channels · supply chain · annual external red-team for novel classes (§7) |

Pattern: **setup adversarial actor → execute attack vector → assert defense holds → assert detection signal emitted** (→ [REALITY.md](REALITY.md)).

| Defense aspect | Asserted |
|---|---|
| Block | Attack ✗ achieves its goal — request rejected with a structured error |
| Detect | Defensive signal emitted: log · metric · alert · receipt |
| Audit | Attempt recorded for review |
| Rate-limit | Repeat attempts trigger rate limit · lockout · CAPTCHA |
| ✗ silent failure | Detection ✗ blocks legitimate traffic |

### Rules

- Target own systems only. Authorization documented in the repo (`tests/pentest/AUTHORIZATION.md`).
- Every test asserts **both** (a) attack blocked **and** (b) detection signal emitted. Block-without-detection = a future blind spot.
- Findings classified by severity (→ [security](../security/STANDARDS.md), else CVSS): Critical · High · Medium · Low.
- **Critical / High block release. Medium = sprint deadline. Low = backlog** (§8).
- Corpus version-controlled. New CVE in a dependency or a new attack class → corpus grows within **7 days** for production-tier.
- ✗ test against production · ✗ test systems you ✗ own · ✗ leave probes running unattended.
- Runs nightly in staging. Pre-release run mandatory. Every real security incident → reproducer added permanently (→ [REALITY.md](REALITY.md)).

### Auth / authz assertion set

| Test | Asserts |
|---|---|
| Token without signature | ✗ accepted |
| Expired token | ✗ accepted |
| Token signed with `none` algo | ✗ accepted (alg-confusion) |
| Token from a different tenant | ✗ accepted |
| Password reset for another user via parameter swap | ✗ accepted · ✓ logged |
| Brute force | Lockout / rate-limit triggers · alert fires |
| Session valid after logout | ✗ valid |
| Session valid after password change | ✗ valid |
| User A reads User B's resource via direct ID | ✗ accessible (IDOR blocked) |
| Read-only user mutates via API | ✗ permitted |
| Tenant A queries Tenant B records | ✗ permitted |
| Role parameter in request body honored | ✗ honored (server-side authz only) |
| Hidden admin endpoint reachable without admin role | ✗ accessible |

---

## 6. Custom Harness

All pressure · survival · penetration tests are built in the project's own testing framework. ✗ external tools as primary defense.

| External-tool approach | Custom approach |
|---|---|
| Attack/load patterns in tool config | Encoded as code, beside production code |
| Tool update changes semantics silently | Test changes go through PR review |
| Coverage = the vendor's coverage | Coverage matches your system's surface |
| Hard to gate in CI | Same framework as unit/integration — gates trivially |
| Reports in a tool dashboard | Receipts + signals in your observability stack |
| ✗ versioned with code · vendor lock-in | Version-locked · portable · lives forever |

### Rules

- Tests live in repo: `tests/pressure/` · `tests/survival/` · `tests/pentest/`, using the project's main testing framework.
- ✗ external load generators (k6 · JMeter · Gatling) as the **source of truth** — ad-hoc exploration only; capacity numbers come from custom tests.
- ✗ external scanners (Burp · ZAP · Nessus · Nuclei · Metasploit) as the **gating** test — discovery aid only; gating happens via custom tests in repo.
- Harness lives in `tests/harness/`, treated as production code (typed · tested · reviewed).
- Test vectors (attack payloads · load profiles) are data files in repo: `tests/pressure/profiles/*.yaml` · `tests/pentest/vectors/*.yaml`. Reviewable · diff-able · version-locked.
- Published attack-vector libraries (OWASP cheat sheets · CVE PoCs) imported as **inert data** into the corpus. ✗ executed via vendor tooling — re-implemented in the project framework.
- New attack class published → vector added within **7 days** for production-tier.

### Harness components — `tests/harness/`

| Component | Responsibility |
|---|---|
| Load generator | Request streams matching a profile (RPS curve · request mix · payload distribution) |
| Fault injector | Inject network · disk · process · clock faults at configured points |
| Attack runner | Execute pen-test vectors against the running system, collect responses |
| Observer | Capture metrics · logs · traces during the test, persist to artifacts |
| Reporter | Aggregate into machine-readable output (JSON/JUnit) for CI |
| Scenario composer | Combine load + faults + attacks into multi-faceted scenarios |

Tradeoffs, accepted for systems where "CI green = ship" matters: higher upfront cost than buying tools · lower coverage breadth at the start (corpus grows from zero — mitigated by importing published vectors as data) · engineers must understand attack/load patterns deeply enough to encode them (institutional knowledge stays in the codebase).

---

## 7. Manual Red-Team Boundary

Automation handles ~80% of pen-test classes; the remaining ~20% requires humans.

| Automatable (✓) | Requires manual red-team (✗ automated alone) |
|---|---|
| OWASP Top 10 (most categories) | Business-logic flaws — require understanding of *intent* |
| Auth / authz / session flaws | Multi-step novel exploits crossing 5+ systems |
| Server-side flaws (SSRF · XXE · injection · traversal) | Social engineering · phishing resistance |
| Known CVE reproducers in dependencies | Physical · hardware attacks |
| Config drift (TLS · headers · CORS · CSP) | Zero-days (by definition unknown to the corpus) |
| Surface enumeration (ports · debug · admin paths) | Adversarial creativity |
| Rate-limit / lockout enforcement | Cryptographic protocol flaws (needs a cryptanalyst) |
| Token / cookie security properties | Insider-threat scenarios (behavioral) |

### Rules

- Production-tier schedules manual red-team **annually** minimum. Critical systems quarterly.
- Scope documented in advance. Findings classified like automated (Critical · High · Medium · Low).
- Every manual finding becomes an automated test — the corpus learns from each engagement.
- ✗ replace automated pen tests with manual red-team. Manual covers what automation can't, ✗ a substitute for daily checks.
- Internal vs external: internal yearly · external every 2 years for L5 production.

---

## 8. Pipeline and Gating

Pressure tests have different infrastructure needs than unit/integration. Pipeline **stage wiring · runners · deploy-gate mechanics** → [cicd](../cicd/STANDARDS.md); this section owns the **suite-to-frequency strategy and the gate thresholds**.

| Test type | Suite | Frequency | Runner |
|---|---|---|---|
| Stress (per release) | Pre-release | Weekly + per release | Dedicated load runner |
| Endurance (1 h sample) | Pre-release | Per release | Dedicated load runner |
| Endurance (full N-hour) | Nightly | Nightly (production-tier) | Dedicated load runner |
| Capacity baseline | Pre-release | Per release | Production-shaped infra |
| Survival single-fault matrix | Nightly | Nightly | Pre-prod |
| Survival multi-fault | Nightly | Weekly (full matrix) | Pre-prod |
| Chaos (random injection) | Nightly | Nightly (L5) | Pre-prod |
| Pen test (auth/authz/session) | Nightly | Nightly | Staging |
| Pen test (full corpus) | Pre-release | Per release | Staging |
| Manual red-team | Out-of-band | Annual / quarterly | Coordinated engagement |

### Gate thresholds

| Failure | Action |
|---|---|
| Stress regression > 20% | Block release · investigate before promotion |
| Capacity regression > 15% | Block release |
| Endurance failure | Block release · P1 fix |
| Survival single-fault | Block release |
| Survival multi-fault | Block if user-facing · investigate if internal-only |
| Chaos finding | Track · fix next sprint · ✗ block unless severity High+ |
| Pen test Critical / High | Block release |
| Pen test Medium | Sprint deadline · ✗ block release |
| Pen test Low | Backlog |

---

## 9. Infrastructure

Pressure tests need infrastructure shared CI runners can't provide. Provisioning · cost accounting · backup/DR → [devops](../devops/STANDARDS.md).

| Environment | Requirements |
|---|---|
| Dedicated load runner | Sustained CPU + memory, ✗ shared with build/test · network-isolated segment · production-shaped target (same instance type · DB tier · cache · topology) · full observability + profile capture · long-retention result store (90+ days) · one pressure test per environment (coordinator/lock) · reset between runs (DB wipe · cache flush · queue drain) |
| Pen test environment | Staging mirrors production auth · authz · session · TLS · headers · isolated from production (✗ shared DB · ✗ shared secrets · ✗ shared network reach) · synthetic data only · attack-traffic-aware monitoring (✗ pollute production alerting) · reset on demand |
| Survival environment | Multi-zone topology mirroring production · fault-injection layer (network proxy · process supervisor · disk shim, per-host) · production-shaped synthetic load during chaos · rollback to baseline within minutes |

### Cost by tier

- PoC / Small: ✗ dedicated infra. Run ad-hoc on a laptop or a single CI job.
- Production-tier: dedicated load + pen + survival environments mandatory. Cost ~10–20% of production infra spend — far cheaper than the outage these tests prevent.

---

## 10. Scale Matrix

| Aspect | Prototype | Production | Scale |
|---|---|---|---|
| Stress (§3) | ✗ required | Find peak QPS once | Per-release · trend tracked |
| Endurance (§3) | ✗ required | 1 h sample per release | Nightly N-hour run |
| Capacity (§3) | ✗ required | Annual measurement | Per-release re-measurement |
| Multi-fault (§4) | ✗ required | Top 3 dependency pairs | Top 5 × full matrix |
| Cascading (§4) | ✗ required | ✗ required | Required L4+ |
| Chaos (§4) | ✗ required | ✗ required | Required L5 nightly |
| Game days (§4) | ✗ required | Annual | Quarterly |
| Pen — auth/authz (§5) | ✗ required | Per release | Nightly |
| Pen — full corpus (§5) | ✗ required | Per release | Nightly |
| Manual red-team (§7) | ✗ required | ✗ required | Annual internal · biannual external (L5) |
| Custom harness (§6) | ✗ required | Minimal load gen | Full harness (load · fault · attack · observe · report) |
| External tools (§6) | OK ad-hoc | OK for discovery · ✗ gating | ✗ gating · ad-hoc only |
| Dedicated infra (§9) | Laptop / shared CI | Single dedicated runner | Full dedicated environments |

Prototype → Production: pick top 3 workflows · stress + capacity once · document peak · add auth/authz pen tests. Production → Scale: build the custom harness · dedicated infra · nightly chaos + pen · annual red-team · capacity per release. ✗ skip steps · ✗ "we'll add survival tests after launch" — outages happen on day 1.

---

## 11. Checklist

### Baseline

- [ ] Stress test run · peak QPS at SLO documented (§3)
- [ ] Capacity number published to every team operating the system (§3)
- [ ] Bottleneck inventory documented, top 3 ranked (§3)
- [ ] Endurance run · N hours at 70% capacity · no degradation (§3)
- [ ] Multi-fault matrix top 5 dependency pairs run · outcomes documented (§4)
- [ ] Pen corpus seeded: auth · authz · session · server-side flaws (§5)
- [ ] Every pen test asserts both attack-blocked and detection-signal-emitted (§5)
- [ ] Custom harness built: load · fault · attack · observe · report (§6)
- [ ] Tests + vectors live in repo, version-locked · no external tool as the gate (§6)
- [ ] Dedicated infrastructure provisioned (§9)
- [ ] Gate thresholds wired: stress 20% · capacity 15% · pen Critical/High (§8)

### Per release

- [ ] Stress regression within 20% of baseline (§8)
- [ ] Capacity regression within 15% of baseline (§8)
- [ ] Endurance 1 h sample green (§3)
- [ ] Multi-fault matrix run · no new failures (§4)
- [ ] Pen corpus run · no new Critical/High findings (§5)
- [ ] New pressure scenarios added for new features (§2)

### Nightly (production-tier)

- [ ] Endurance N-hour run green (§3)
- [ ] Chaos suite run · findings triaged within 24 h (§4)
- [ ] Pen full corpus run · findings triaged (§5)
- [ ] Survival multi-fault sample run (§4)

### Periodic

- [ ] Quarterly game day · team participates · findings recorded (§4)
- [ ] Annual internal red-team · external per L5 cadence (§7)
- [ ] Year's findings converted to permanent automated tests (§2)
- [ ] Pressure-test infra audited for drift from production (§9)
