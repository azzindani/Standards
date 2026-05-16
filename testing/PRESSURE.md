# Pressure · Survival · Penetration Testing Standards

System-level testing that pushes beyond per-operation correctness.
Asks: *Can the system survive its worst day?* — sustained heavy load,
cascading dependency failures, simultaneous faults, and active adversaries.

Pairs with `testing/STANDARDS.md` (extends reality dimensions) and
`cicd/STANDARDS.md` (executes via dedicated pressure runners).

Composable with: Architecture · Security · Observability · DevOps.

---

## Table of Contents

1. [Why a Separate Standard](#1-why-a-separate-standard)
2. [Pressure Philosophy](#2-pressure-philosophy)
3. [Reality Dimension: Pressure](#3-reality-dimension-pressure)
4. [Reality Dimension: Survival](#4-reality-dimension-survival)
5. [Reality Dimension: Penetration](#5-reality-dimension-penetration)
6. [Custom Test Automation](#6-custom-test-automation)
7. [Manual Red-Team Boundary](#7-manual-red-team-boundary)
8. [Pipeline Integration](#8-pipeline-integration)
9. [Pressure Test Infrastructure](#9-pressure-test-infrastructure)
10. [Scale Matrix](#10-scale-matrix)
11. [Pressure Testing Checklist](#11-pressure-testing-checklist)

---

## 1. Why a Separate Standard

`testing/STANDARDS.md` covers **per-operation correctness under reality** — does this function behave correctly when faults arrive, inputs are adversarial, time skews, resources tighten? This standard covers **system-level behavior under pressure** — does the assembled system survive when load saturates, dependencies cascade, multiple things fail at once, or an attacker actively probes?

| `testing/STANDARDS.md` | `testing/PRESSURE.md` |
|---|---|
| Per-operation budgets (§25 perf) | Sustained load to breaking point |
| Single fault injection (§10) | Multi-fault + cascading failures |
| Input-boundary adversarial (§11) | System-level penetration (auth · authz · session · exfil) |
| Race detection stress (§12, ~100 ops) | Capacity stress (10K–100K+ ops) |
| State accumulation (§15, passive iter) | Endurance under active sustained load |
| Recovery from single fault (§18) | Survival across chained dependency loss |

Pressure testing requires **dedicated infrastructure** (sustained-load runners, isolated targets, observation harness) and **runs differently** (nightly + pre-release, not per-commit). Different audience: SRE/security-focused review, not standard PR review.

---

## 2. Pressure Philosophy

| Principle | Rule |
|---|---|
| Find the breaking point | Production needs known limits. ✗ "we think it handles N." Measure it. |
| Multi-fault is the normal case | Real outages are 3+ failures interleaved. Test combinations, ✗ only singles. |
| Pen tests are continuous | Run every nightly. Adversaries don't wait for quarterly audits. |
| Custom-built, not bolted on | Tests live in repo using project framework. ✗ external scanners as primary defense (see §6). |
| Observation > assertion | Pressure tests measure system response curves; pass/fail is one signal among many. |
| Reproducible failure | Every found failure becomes a permanent regression test. |
| Pressure = production-shaped | Synthetic load mirrors production traffic distribution, not uniform RPS. |
| Survival is a property, ✗ feature | Designed-in via architecture (`architecture/STANDARDS.md`), proven by these tests. |

### Non-Negotiables

- Pressure tests run against a production-shaped environment — sandboxed but full-stack, ✗ test doubles in production code paths.
- ✗ pressure-test against production. Always staging or dedicated load environment.
- Every pressure-test failure spawns a permanent regression test in `testing/STANDARDS.md` suite.
- Pen tests against own systems only. Authorization documented before run.
- Findings tracked with: severity · reproducer · owner · resolution SLO.

---

## 3. Reality Dimension: Pressure

Sustained heavy load. Three sub-dimensions:

| Sub-Dimension | Question Answered | Stop Condition |
|---|---|---|
| Stress | What is the breaking point? | First sustained SLO violation or crash |
| Endurance | Does it stay healthy under sustained load? | Run completes N hours without degradation |
| Capacity | What load can we serve at SLO with headroom? | Find peak QPS where p99 still within SLO |

### Stress Tests

Push load past expected peak until system breaks. Find the bottleneck.

| What to Measure | Why |
|---|---|
| Throughput ceiling | Max RPS sustainable before SLO violation |
| Latency curve | p50 · p95 · p99 · p99.9 vs load level |
| Error rate curve | Where errors begin · how they scale |
| Resource saturation order | Which resource caps first (CPU · memory · FDs · DB conns · queue) |
| Failure mode at limit | Graceful degrade · timeout · crash · cascade |
| Recovery after overload | Load drops → does system return to baseline? |

### Stress Rules

- Ramp load gradually (e.g., 100 → 1000 → 10K → 100K RPS over minutes), ✗ instant peak — instant peak hides which limit hits first.
- Run with full observability — every metric, every log, every trace. Stress test = data collection event, ✗ pass/fail.
- Document the bottleneck per stress run. Output = "system caps at 47K RPS; next bottleneck is DB connection pool at 200 connections."
- Stress run ✗ blocks pipeline by default. Regression > 20% from baseline = blocks.
- Production capacity = stress-test peak / 2 (50% headroom). Operating beyond that requires explicit risk acceptance.

### Endurance Tests

Sustained load over hours/days. Catches slow-burn failures invisible in short runs.

| Failure Mode | Test |
|---|---|
| Memory leak under load | N-hour run at 70% capacity, RSS ✗ trends upward |
| Connection / FD leak | N-hour run, pool/FD count stable |
| Cache poisoning | N-hour run with cache-evicting traffic, hit rate stable |
| Performance degradation | N-hour run, p99 latency drift < 10% |
| Background task pileup | N-hour run, queue depth bounded |
| Log volume / disk fill | N-hour run, log rotation works under load |
| Token / session exhaustion | N-hour run, auth subsystem ✗ exhaust |
| Time-of-day effects | Run across midnight, day boundaries — clock-rollover handling |

### Endurance Rules

- Min duration: production = 24h · staging = 4h · per-release = 1h sample.
- Load level: 70% of stress-tested peak (sustainable production target).
- Monitoring required throughout — periodic snapshots of every saturation metric.
- Endurance failure = P1 — fix before release. Endurance regressions ✗ "watch for now."
- Run in nightly suite for production-tier projects. Weekly minimum.

### Capacity Tests

Find SLO-conformant peak QPS with safety margin.

| Output | Target |
|---|---|
| Peak QPS at SLO | RPS where p99 latency ≤ documented SLO and error rate ≤ 0.1% |
| Headroom-required QPS | Peak QPS × 0.5 — operate-below this in production |
| Bottleneck inventory | Ranked list: 1st bottleneck, 2nd bottleneck, etc. |
| Scaling efficiency | RPS per added compute unit — linear, sublinear, broken? |

### Capacity Rules

- Capacity number is published — every team operating the system knows it.
- Capacity re-measured on every release that touches request path. Capacity drift > 15% triggers investigation.
- Capacity test runs against fully production-shaped infra: same instance type, same DB tier, same cache, same network topology. Half-scale capacity tests give half-truth answers.
- Capacity regressions block release for production-tier projects.

---

## 4. Reality Dimension: Survival

Multi-fault, cascading, and chaos scenarios. Asks: *what happens when bad things happen together?*

### Failure Categories

| Category | Description |
|---|---|
| Multi-fault | 2+ independent faults at the same time (DB slow + cache miss + dep timeout) |
| Cascading | A fails → triggers B fail → triggers C fail (queue backs up → timeouts cascade upstream) |
| Region / zone loss | Entire AZ or region unreachable |
| Dependency cliff | Critical dep returns 100% errors for N minutes |
| Slow-cascade | One slow dep degrades whole pipeline through queue buildup |
| Thundering herd | All clients retry simultaneously after recovery — wave overwhelms recovered service |
| Split brain | Network partition with both halves accepting writes |
| Time-of-failure shift | Failure during deploy · during DB migration · during traffic spike |

### Required Survival Tests

| Tier | Required Tests |
|---|---|
| L3+ (per `testing/STANDARDS.md §1`) | Multi-fault: top 5 dep-pair combinations |
| L4+ | + cascading: 3-deep dependency chain · thundering herd · slow cascade |
| L5 | + chaos: random fault injection · region loss · split brain · failure-during-deploy |

### Chaos Engineering

Random fault injection in production-shaped environment. Discovers unknown unknowns.

| Chaos Action | Fault Injected |
|---|---|
| Kill instance | Random pod/process termination |
| Network partition | Random AZ or service partition |
| Latency injection | Random p99 spike on random dependency |
| Packet loss | Random % drop on random link |
| Clock skew | ±N seconds on random node |
| Disk slow | I/O latency injection on random instance |
| DNS failure | Resolution failure for random service |
| Resource starvation | CPU / memory pressure on random node |

### Survival Rules

- Survival tests run in dedicated environment, ✗ shared CI. Need isolated network + control over injection layer.
- Each survival scenario has documented expected outcome: graceful degrade · partial unavailable · full unavailable. ✗ "see what happens."
- Multi-fault matrix: top 5 critical dependencies × 5 fault modes = 25 single-fault tests + selected multi-fault combinations.
- Cascading test: drive system to brink, then trigger one more fault — verify ✗ catastrophic collapse.
- Chaos suite runs nightly in pre-prod. Findings = P1 if user-facing impact, P2 if internal degrade only.
- ✗ chaos in production until: nightly chaos in pre-prod has run for 30+ days clean · automated rollback proven (`cicd/STANDARDS.md §13`) · on-call rotation accepts game-day exercise.
- Game days: quarterly manual chaos exercises with full team, build muscle memory.
- Every survival failure becomes a permanent regression test — multi-fault scenario added to nightly suite forever.

### Recovery from Survival Tests

Pairs with `testing/STANDARDS.md §18` recovery. After survival scenario:

- All cleared faults → system returns to baseline within documented SLO.
- ✗ data loss · ✗ duplicate-effect · ✗ orphaned state.
- Pending operations either complete or fail with structured error — never hang.
- Operator-visible signal that scenario occurred (alert fired, receipt written).

---

## 5. Reality Dimension: Penetration

Adversarial system-level testing. Distinct from `testing/STANDARDS.md §11` (input-boundary adversarial) — this is full-system attack simulation.

### Categories

| Category | Examples |
|---|---|
| Authentication | Token forgery · brute force · password reset abuse · 2FA bypass · session fixation · timing attacks on auth |
| Authorization | Privilege escalation (vertical) · IDOR (horizontal) · forced browsing · API role bypass · tenant boundary crossing |
| Session management | Session hijack · session prediction · CSRF · cookie tampering · token replay · session-not-invalidated-on-logout |
| Data exfiltration paths | Mass enumeration · pagination abuse · search abuse · export-endpoint abuse · debug endpoints · GraphQL introspection in prod |
| Server-side flaws | SSRF · XXE · template injection · deserialization · path traversal · upload-then-execute · ZIP slip |
| Logic flaws | Race-condition exploits (e.g., double-spend) · workflow bypass · price manipulation · state-machine skipping |
| Side channels | Timing attacks · cache attacks · error-message info leak · enumeration via response time |
| Supply chain | Dependency confusion · typosquatting · poisoned cache · malicious post-install |
| Infrastructure | Exposed metadata services (cloud) · open ports · misconfigured TLS · default creds · S3 public buckets |

### Required Penetration Tests

| Tier (per `testing/STANDARDS.md §1`) | Required Categories |
|---|---|
| L3 | Auth · authz · session · server-side flaws · infrastructure |
| L4 | + data exfiltration · logic flaws |
| L5 | + side channels · supply chain · annual external red-team for novel attack classes (§7) |

### Pen Test Patterns

Each pen test follows: **Setup adversarial actor → execute attack vector → assert defense holds → assert detection signal emitted (`testing/STANDARDS.md §17`)**.

| Defense Aspect | Asserted |
|---|---|
| Block | Attack ✗ achieves goal — request rejected with structured error |
| Detect | Defensive signal emitted: log · metric · alert · receipt |
| Audit | Attempted attack recorded for review |
| Rate-limit | Repeat attempts trigger rate limit · lockout · CAPTCHA |
| ✗ silent failure | Successful detection ✗ blocks legitimate traffic |

### Penetration Rules

- Pen tests target own systems only. Authorization documented in repo (e.g., `tests/pentest/AUTHORIZATION.md`).
- Each test asserts both: (a) attack blocked AND (b) detection signal emitted. Block-without-detection = future blind spot.
- Findings classified by severity (`security/STANDARDS.md` if present, else CVSS): Critical · High · Medium · Low.
- Critical/High pen findings = block release. Medium = sprint deadline. Low = backlog.
- Pen test corpus version-controlled. New CVE in dependency or new class of attack → corpus grows.
- ✗ test against production · ✗ test against systems you don't own · ✗ leave probes running unattended.
- Pen test runs nightly in staging. Pre-release run mandatory.
- Every real-world security incident → reproducer added to pen test corpus permanently (`testing/STANDARDS.md §27`).

### Auth-Specific Pen Tests

| Test | Asserts |
|---|---|
| Token without signature accepted? | ✗ accepted |
| Expired token accepted? | ✗ accepted |
| Token signed with `none` algo? | ✗ accepted (alg confusion attack) |
| Token from different tenant? | ✗ accepted |
| Password reset for other user via parameter swap? | ✗ accepted, ✓ logged |
| Brute force protection? | Lockout / rate-limit triggers · alert fires |
| Session valid after logout? | ✗ valid |
| Session valid after password change? | ✗ valid |

### Authz-Specific Pen Tests

| Test | Asserts |
|---|---|
| User A reads User B's resource via direct ID? | ✗ accessible (IDOR blocked) |
| Read-only user mutates via API? | ✗ permitted |
| Tenant A queries Tenant B records? | ✗ permitted |
| Role parameter in request body honored? | ✗ honored (server-side authz only) |
| Hidden admin endpoints discoverable? | ✗ accessible without admin role |

---

## 6. Custom Test Automation

All pressure · survival · penetration tests built in the project's own testing framework. ✗ external tools as primary defense.

### Why Custom

| External Tool Approach | Custom Approach |
|---|---|
| Encodes attack/load patterns in tool config | Encodes them as code, alongside production code |
| Tool updates may change semantics silently | Test changes go through PR review |
| Tool's coverage = vendor's coverage | Coverage matches your system's actual surface |
| Hard to integrate into CI gating | Same framework as unit/integration — gates trivially |
| Reports live in tool dashboards | Receipts + signals in your observability stack |
| ✗ versioned with code | Tests version-locked with code |
| Vendor lock-in | Portable, lives forever |

### Rules

- All pressure/survival/pen tests live in repo: `tests/pressure/` · `tests/survival/` · `tests/pentest/`.
- Tests use the project's main testing framework (same as unit/integration).
- ✗ external load generators (k6, JMeter, Gatling) as the *source of truth*. May be used for ad-hoc exploration; production capacity numbers come from custom tests.
- ✗ external scanners (Burp, ZAP, Nessus, Nuclei, Metasploit) as the gating CI test. May be used as discovery aids during development; gating happens via custom tests in repo.
- Custom test harness lives in `tests/harness/` — load generator · fault injector · attack vectors · observation collector. Treated as production code (typed · tested · reviewed).
- Test vectors (attack payloads, load profiles) are data files in repo: `tests/pressure/profiles/*.yaml` · `tests/pentest/vectors/*.yaml`. Reviewable, diff-able, version-locked.
- Common attack-vector libraries (e.g., OWASP cheat sheets, CVE PoCs) may be *imported* as inert data into the corpus. ✗ executed via vendor tooling — re-implemented in project framework.
- New attack class published → vector added to corpus within 7 days for production-tier projects.

### What Belongs in `tests/harness/`

| Component | Responsibility |
|---|---|
| Load generator | Produce request streams matching configured profile (RPS curve, request mix, payload distribution) |
| Fault injector | Inject network · disk · process · clock faults at configured points |
| Attack runner | Execute pen-test vectors against running system, collect responses |
| Observer | Capture metrics, logs, traces during test; persist to test artifacts |
| Reporter | Aggregate results into machine-readable format (JSON/JUnit) for CI |
| Scenario composer | Combine load + faults + attacks into multi-faceted scenarios |

### Tradeoffs Acknowledged

- **Higher upfront cost** than buying tools — accept this for systems where "CI green = ship" matters.
- **Lower coverage breadth at start** — custom corpus grows from zero. Mitigation: import published attack vectors as data, build the runner once, vectors accumulate.
- **Skill required** — engineers must understand attack/load patterns deeply enough to encode them. This is also a benefit (institutional knowledge stays in the team and the codebase).

---

## 7. Manual Red-Team Boundary

Automation handles ~80% of pen-test classes. The remaining ~20% requires humans.

### What Automated Pen Tests Cover (✓)

| Class | Automatable |
|---|---|
| OWASP Top 10 (most categories) | ✓ |
| Auth / authz / session flaws | ✓ |
| Common server-side flaws (SSRF · XXE · injection · path traversal) | ✓ |
| Known CVE reproducers in dependencies | ✓ |
| Configuration drift (TLS · headers · CORS · CSP) | ✓ |
| Surface enumeration (open ports · debug endpoints · admin paths) | ✓ |
| Rate-limit / lockout enforcement | ✓ |
| Token / cookie security properties | ✓ |
| Common race-condition exploits with known patterns | ✓ |

### What Requires Manual Red-Team (✗ automated alone)

| Class | Why Manual |
|---|---|
| Business-logic flaws | Require understanding of *intent*, ✗ specs. "Workflow X shouldn't allow Y in state Z" |
| Multi-step novel exploits | Chained attacks crossing 5+ systems need creativity |
| Social engineering / phishing resistance | Requires human-in-loop |
| Physical security · hardware attacks | Out of automated scope |
| Zero-days in dependencies | By definition unknown to corpus |
| Adversarial creativity | Humans find what automated patterns miss |
| Cryptographic protocol flaws | Domain expertise — requires cryptanalyst |
| Insider-threat scenarios | Behavioral, not code-detectable |

### Rules

- Production-tier projects schedule manual red-team annually minimum. Critical systems quarterly.
- Manual red-team scope documented in advance. Findings classified same as automated (Critical · High · Medium · Low).
- Every manual red-team finding becomes an automated test — corpus learns from each engagement.
- ✗ replace automated pen tests with manual red-team. Manual = covers what automation can't, ✗ substitute for daily checks.
- Internal vs external red-team: internal yearly, external every 2 years for L5 production.

---

## 8. Pipeline Integration

Pressure tests have different infrastructure needs than unit/integration. See `cicd/STANDARDS.md §5 · §15`.

### Suite Mapping

| Test Type | CI/CD Suite | Frequency | Runner |
|---|---|---|---|
| Stress (per release) | Pre-release | Weekly + per release | Dedicated load runner |
| Endurance (1h sample) | Pre-release | Per release | Dedicated load runner |
| Endurance (full N-hour) | Nightly | Nightly (production-tier) | Dedicated load runner |
| Capacity baseline | Pre-release | Per release | Production-shaped infra |
| Survival single-fault matrix | Nightly | Nightly | Pre-prod environment |
| Survival multi-fault | Nightly | Weekly (full matrix) | Pre-prod environment |
| Chaos (random injection) | Nightly | Nightly (L5) | Pre-prod environment |
| Pen test (auth/authz/session) | Nightly | Nightly | Staging |
| Pen test (full corpus) | Pre-release | Per release | Staging |
| Manual red-team | Out-of-band | Annual / quarterly | Coordinated engagement |

### Pipeline Gating

| Failure | Action |
|---|---|
| Stress regression > 20% | Block release · investigate before promotion |
| Capacity regression > 15% | Block release |
| Endurance failure | Block release · P1 fix |
| Survival single-fault | Block release |
| Survival multi-fault | Block release if user-facing impact · investigate if internal-only |
| Chaos finding | Track · fix in next sprint · ✗ block unless severity High+ |
| Pen test Critical / High | Block release |
| Pen test Medium | Sprint deadline · ✗ block release |
| Pen test Low | Backlog |

---

## 9. Pressure Test Infrastructure

Pressure tests need infrastructure that shared CI runners can't provide.

### Dedicated Load Runner Requirements

| Requirement | Detail |
|---|---|
| Sustained CPU + memory | ✗ shared with build/test workloads · sized for stress profile |
| Network isolation | Separate network segment · ✗ contend with regular CI traffic |
| Production-shaped target | Same instance type · DB tier · cache · topology as production |
| Observability stack | Full metrics · logs · traces · profile capture · resource monitoring |
| Result persistence | Long-retention storage for trend analysis (90+ days) |
| Concurrent test prevention | One pressure test per environment at a time — coordinator/lock |
| Reset between runs | Database wipe · cache flush · queue drain · clean baseline |

### Pen Test Environment Requirements

| Requirement | Detail |
|---|---|
| Staging mirrors production | Same auth · authz · session · TLS · headers config |
| Isolated from production | ✗ shared databases · ✗ shared secrets · ✗ shared network reach |
| Synthetic data only | Production-shaped distributions, ✗ real customer data |
| Attack-traffic-aware monitoring | Detection signals visible to test, ✗ pollute production alerting |
| Reset on demand | Wipe back to known-good state between runs |

### Survival Environment Requirements

| Requirement | Detail |
|---|---|
| Multi-zone topology | Mirrors production zone/region layout to test partition scenarios |
| Fault-injection layer | Network proxy · process supervisor · disk shim — controllable per-host |
| Production-shaped traffic | Synthetic load matching production distribution running during chaos |
| Rollback capability | Test environment recoverable to baseline within minutes |

### Cost Tradeoff

Dedicated infrastructure costs real money. Scale by tier:

- PoC / Small: ✗ dedicated infra. Pressure tests run ad-hoc on laptop or single CI job.
- Production-tier: dedicated load + pen + survival environments mandatory. Cost ~10–20% of production infra spend. Far cheaper than the outage these tests prevent.

---

## 10. Scale Matrix

| Aspect | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Stress (§3) | ✗ required | Find peak QPS once | Per-release · trend tracked |
| Endurance (§3) | ✗ required | 1h sample per release | Nightly N-hour run |
| Capacity (§3) | ✗ required | Annual measurement | Per-release re-measurement |
| Multi-fault (§4) | ✗ required | Top 3 dep pairs | Top 5 × full matrix |
| Cascading (§4) | ✗ required | ✗ required | Required L4+ |
| Chaos (§4) | ✗ required | ✗ required | Required L5 nightly |
| Game days (§4) | ✗ required | Annual | Quarterly |
| Pen — auth/authz (§5) | ✗ required | Per release | Nightly |
| Pen — full corpus (§5) | ✗ required | Per release | Nightly |
| Manual red-team (§7) | ✗ required | ✗ required | Annual (internal) · biannual (external) for L5 |
| Custom harness (§6) | ✗ required | Minimal load gen | Full harness (load · fault · attack · observe · report) |
| External tools (§6) | OK for ad-hoc | OK for discovery, ✗ gating | ✗ gating · ad-hoc only |
| Dedicated infra (§9) | Laptop / shared CI | Single dedicated runner | Full dedicated environments |

### Transitions

PoC → Small: pick top 3 user workflows, run stress + capacity once, document peak. Add basic pen tests for auth/authz.

Small → Production: build custom harness · dedicated infra · nightly chaos + pen · annual red-team · capacity per release.

✗ skip steps. ✗ "we'll add survival tests after launch." Outages happen on day 1.

---

## 11. Pressure Testing Checklist

### Initial Pressure Baseline

- [ ] Stress test run — peak QPS at SLO documented
- [ ] Capacity number published to all teams operating system
- [ ] Bottleneck inventory documented (top 3 ranked)
- [ ] Endurance test run — N hours at 70% capacity, no degradation
- [ ] Multi-fault matrix top 5 dep pairs run — outcomes documented
- [ ] Pen test corpus seeded: auth · authz · session · server-side flaws
- [ ] Custom harness components built: load · fault · attack · observe · report (§6)
- [ ] Dedicated infrastructure provisioned (§9)
- [ ] Pipeline gates wired per §8

### Per Release

- [ ] Stress regression check — within 20% of baseline
- [ ] Capacity regression check — within 15% of baseline
- [ ] Endurance 1h sample green
- [ ] Multi-fault matrix run — no new failures
- [ ] Pen test corpus run — no new Critical/High findings
- [ ] New pressure-test scenarios added for new features

### Nightly (Production-Tier)

- [ ] Endurance N-hour run green
- [ ] Chaos suite run · findings triaged within 24h
- [ ] Pen test full corpus run · findings triaged
- [ ] Survival multi-fault sample run

### Quarterly

- [ ] Game day exercise · team participates · findings recorded
- [ ] Capacity re-baselined if infra/scale changed
- [ ] Pen test corpus reviewed — new attack classes added
- [ ] Pressure-test infra audited for drift from production

### Annual (Production-Tier)

- [ ] Internal manual red-team conducted
- [ ] External red-team conducted (L5 only · biannual acceptable)
- [ ] All findings from year converted to permanent automated tests
- [ ] Pressure test costs reviewed against incident-prevented value
