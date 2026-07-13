# DevOps & Infrastructure Standards

> Infrastructure provisioning, containers, deployment, environment management, incident response, on-call, backup/DR, and cost — the operational layer that keeps a service alive.

**ID** `devops` · **Tier** Delivery · **Version** 1.0
**Owns** infrastructure-as-code + drift detection · container standards (distroless/non-root/read-only rootfs) · immutable infrastructure · 12-Factor · deployment patterns (infra mechanics) · environment management + parity · incident response (SEV levels + blameless postmortems) · **on-call rotation + escalation + paging policy** · scaling + autoscaling · **backup · DR · RTO/RPO · failover cadence** · networking + TLS · vault/secret-injection mechanics · **cost management (infra + LLM/API token spend)**
**Defers to** alert design + resource thresholds → [observability](../observability/STANDARDS.md) · secrets rotation cadence + lifecycle + token classes → [security](../security/STANDARDS.md) · deployment pipeline stages + release automation → [cicd](../cicd/STANDARDS.md) · configuration cascade + sourcing → [configuration](../configuration/STANDARDS.md) · WAL/PITR + replica lag + restore mechanics → [database](../database/STANDARDS.md) · SLO definitions + log/metric formats → [observability](../observability/STANDARDS.md) · application security + authz → [security](../security/STANDARDS.md)
**Load with** [cicd](../cicd/STANDARDS.md) · [observability](../observability/STANDARDS.md) · [security](../security/STANDARDS.md) · [configuration](../configuration/STANDARDS.md)

---

## Table of Contents

1. [Infrastructure as Code](#1-infrastructure-as-code)
2. [Container Standards](#2-container-standards)
3. [Deployment Patterns](#3-deployment-patterns)
4. [Environment Management](#4-environment-management)
5. [Metrics Collection](#5-metrics-collection)
6. [Incident Response](#6-incident-response)
7. [Scaling Strategy](#7-scaling-strategy)
8. [Backup & Disaster Recovery](#8-backup--disaster-recovery)
9. [Networking](#9-networking)
10. [Secrets & Credentials](#10-secrets--credentials)
11. [Cost Management](#11-cost-management)
12. [Scale Matrix](#12-scale-matrix)
13. [Checklist](#13-checklist)

---

## 1. Infrastructure as Code

All infrastructure defined in version-controlled declarative files. ✗ manual provisioning · ✗ clickops · ✗ undocumented changes.

| Rule | Detail |
|---|---|
| Declarative over imperative | Describe desired state; tooling reconciles. See [architecture](../architecture/STANDARDS.md) §10 |
| Version controlled | Every infra file committed; same branching rules as app code ([git](../git/STANDARDS.md)) |
| Idempotent applies | Same config twice → identical result. ✗ side effects on re-apply |
| Reproducible | Any environment rebuildable from repo + secrets vault alone. ✗ snowflake servers |
| Immutable infra | Servers replaced, ✗ mutated in place. Rebuild + redeploy, ✗ patch running hosts |
| Modular | Reusable components per resource type. ✗ monolithic config files > 300 lines |
| Parameterized | Environment differences as variables, not separate configs |
| Drift detection | Automated compare declared vs actual state. Alert on divergence |
| Plan before apply | Every change previewed (dry-run/plan) before execution. ✗ direct apply without review |
| State management | Remote state with locking. ✗ local-only state. ✗ concurrent modification |
| Least privilege | IaC service accounts get minimum provisioning permissions |

### Change Workflow

1. Branch from `main` → modify infra code.
2. Run plan/dry-run → review diff.
3. Peer review required for production changes.
4. Apply via CI/CD pipeline. ✗ manual apply to production.
5. Verify drift detection passes post-apply. Commit state changes.

### Resource Tagging

Every provisioned resource tagged: `environment` · `service` · `team` · `cost-center` · `managed-by` · `created-date`. ✗ untagged resources in any environment above dev.

---

## 2. Container Standards

### Base Image

| Rule | Detail |
|---|---|
| Minimal base | Distroless or alpine. ✗ full OS images unless required by runtime |
| Pinned by digest | Tag with digest hash, ✗ `latest` or mutable tags in production |
| Trusted sources | Official or internal registry only. ✗ unverified third-party images |
| Regular rebuilds | Base images rebuilt ≥ monthly for security patches |
| Scanned | Every image scanned for CVEs before registry push. Block critical/high |

### Build

| Rule | Detail |
|---|---|
| Layer optimization | Least-changing layers first; frequently-changing last |
| Multi-stage builds | Build deps ✗ in final image. Compile in builder, copy artifacts only |
| Single process | One process per container ; exception: log sidecar. ✗ init systems inside |
| No secrets in layers | ✗ secrets in build args, ENV, COPY. Runtime injection only (§10) |
| Size budget | App images < 500 MB (alert if exceeded). Distroless targets < 100 MB |
| Reproducible | Same source commit → same image (content-addressable). Pin all package versions |
| Non-root | Container runs as non-root user. ✗ root in production containers |
| Read-only rootfs | Root filesystem mounted read-only. Writable volumes for data paths only |
| Health checks | Every container defines health check endpoint/command |
| Graceful shutdown | SIGTERM → drain connections → exit within termination grace period |

### Lifecycle

Build (CI on merge to `main`) → Scan (CVE + policy) → Tag (SemVer + git SHA) → Push (internal registry only) → Promote (dev → staging → production, same image, ✗ rebuild) → Retain (last 10 versions per service; purge untagged > 7 days).

---

## 3. Deployment Patterns

Deployment strategy = infra mechanics. Pipeline integration + progressive-delivery gating → [cicd](../cicd/STANDARDS.md).

| Strategy | Use When | Rollback Speed | Resource Cost |
|---|---|---|---|
| Rolling update | Default for stateless services | Medium (progressive) | 1x + surge |
| Blue-green | Zero-downtime · DB migration involved | Fast (switch route) | 2x during deploy |
| Canary | High-risk change · large user base · measurable SLIs | Fast (route shift) | 1x + canary slice |
| Recreate | Stateful singleton · versions cannot coexist | Slow (full redeploy) | 1x |
| Feature flag | Decouple deploy from release · gradual by segment | Instant (flag toggle) | 1x |

### Deployment Rules

| Rule | Detail |
|---|---|
| Immutable artifacts | Deploy exact build artifact. ✗ recompile at deploy time |
| Promotion not rebuild | Same image promoted across environments. ✗ separate builds per env |
| Automated rollback | Failed health checks → automatic rollback to last known good. ✗ manual-only |
| Deployment timeout | Every deploy has max duration. Exceeded → automatic rollback |
| One service at a time | ✗ simultaneous deploy of coupled services unless dependency-ordered |
| Drain before stop | Remove from load balancer → wait for in-flight requests → stop |
| Smoke tests | Post-deploy smoke suite runs automatically. Failure → rollback |
| Deploy log | Every deploy recorded: who, version, when, environment, outcome |

Automatic rollback triggers: health check failure > 50% within first 5 min · error rate > 2x baseline within canary window · latency p99 > 3x baseline · any critical alert fired during deployment window.

---

## 4. Environment Management

Every environment reproducible from IaC + configuration + secrets vault. ✗ environment-specific code paths — behavior differences via configuration only (cascade → [configuration](../configuration/STANDARDS.md)).

### Environment Tiers

| Tier | Environment | Data | Access |
|---|---|---|---|
| 0 | Local/dev | Synthetic/seed | Developer |
| 1 | CI | Synthetic | Pipeline |
| 2 | Staging | Anonymized copy of production | Team |
| 3 | Production | Real | Restricted |

### Parity Rules

| Rule | Detail |
|---|---|
| Architecture parity | Same topology (services, queues, DBs). ✗ skipping components in lower tiers |
| Version parity | Staging runs same dependency versions as production |
| Configuration parity | Same config structure across tiers; only values differ |
| Data shape parity | Non-production data matches production schema exactly. ✗ schema drift |
| Infrastructure parity | Same OS, runtime versions, networking model. Scale differs, architecture does not |

### Provisioning

- New environment provisioned entirely from IaC. Time to provision ≤ 1 hour for full stack.
- Teardown fully automated. ✗ orphaned resources after decommission.
- Ephemeral environments for feature branches — auto-destroy after merge or 7 days idle.
- Production-like environment for load testing — isolated from staging.
- Environment inventory maintained: active environments, purpose, owner, expiry.

---

## 5. Metrics Collection

Which infrastructure + application metrics to collect and at what interval. **Alert design rules, resource thresholds, and SLO burn-rate policy → [observability](../observability/STANDARDS.md)** — ✗ restate thresholds here.

### Infrastructure Metrics (required)

| Metric | Collection Interval |
|---|---|
| CPU utilization | 30s |
| Memory utilization | 30s |
| Disk usage | 60s |
| Disk I/O latency | 30s |
| Network throughput | 30s |
| Container restart count | Event-driven |
| Node availability | 15s |

### Application Metrics (required)

| Metric | Collection Interval |
|---|---|
| Request rate | 10s |
| Error rate (5xx) | 10s |
| Latency p50 / p95 / p99 | 10s |
| Queue depth | 30s |
| Active connections | 30s |
| Dependency health | 30s |
| Business metrics | Service-specific |

### Monitoring Architecture

- Metrics pipeline independent from application data path. Monitoring failure ✗ impacts application.
- Retention: raw metrics ≥ 15 days, downsampled ≥ 1 year.
- Dashboards: one service-overview per service + one infrastructure overview. Hierarchy: system → service → instance.
- Every collected metric feeds observability's alert + SLO layer; thresholds + escalation live there.

---

## 6. Incident Response

### Severity Levels

| Severity | Definition | Response Time | Update Cadence | Escalate After |
|---|---|---|---|---|
| SEV-1 Critical | Complete outage · data loss · security breach | 15 min | Every 30 min | 30 min unacknowledged |
| SEV-2 Major | Partial outage · degraded > 50% users · SLO breach | 30 min | Every 1 hour | 1 hour unacknowledged |
| SEV-3 Minor | Degraded < 50% users · non-critical feature down | 4 hours | Every 4 hours | 8 hours unacknowledged |
| SEV-4 Low | Cosmetic · minor degradation · workaround available | Next business day | Daily | None |

### Incident Workflow

Detect (alert/report) → Triage (severity, incident commander, comms lead) → Communicate (status page within response SLA) → Diagnose → Mitigate (restore; mitigation priority > root cause) → Resolve (confirm baseline) → Postmortem.

### On-Call

| Rule | Detail |
|---|---|
| Rotation size | ≥ 2 engineers per rotation. ✗ single point of human failure |
| Roles | Primary (first page) + secondary (backup, auto-paged if primary misses ack) |
| Cadence | Weekly shifts default. ✗ shifts > 1 week (fatigue) · ✗ back-to-back weeks for same engineer |
| Escalation path | Primary → secondary → incident commander → engineering lead. Timeouts per SEV (table above) |
| Handoff | Documented handoff each rotation: open incidents, known risks, in-flight changes, silenced alerts |
| Paging policy | Page only on SLO burn or user-facing impact. ✗ page on causes (high CPU, single node down) that have no user impact — those are tickets, not pages |
| Toil / comp limit | Track page volume; > 2 pages/shift off-hours sustained → fix the underlying noise. Off-hours paging compensated per policy |
| Runbook required | Every paging alert links to a runbook with diagnostic + mitigation steps ([observability](../observability/STANDARDS.md) owns alert-to-runbook linkage) |

### Postmortem Rules

| Rule | Detail |
|---|---|
| Blameless | Focus on systems, processes, tooling. ✗ individual blame |
| Timeline | Minute-by-minute from detection to resolution |
| Root cause | Contributing factors, not single cause. 5-whys or fault tree |
| Action items | ≥ 1 concrete item with owner + deadline, tracked to completion |
| Published | Accessible to entire engineering org |
| Recurrence check | Same root cause twice → escalate remediation to critical |

### Remediation Timelines

| Severity | Mitigation SLA | Permanent Fix SLA |
|---|---|---|
| SEV-1 | Immediate (during incident) | 5 business days |
| SEV-2 | Within 4 hours | 10 business days |
| SEV-3 | Within 1 business day | Next sprint |
| SEV-4 | Best effort | Backlog |

Postmortem completed blameless within 5 business days (SEV-1/2), 10 days (SEV-3).

---

## 7. Scaling Strategy

| Factor | Horizontal (add instances) | Vertical (add resources) |
|---|---|---|
| Stateless services | Preferred | Fallback |
| Stateful services | Requires coordination (sharding, consensus) | Preferred initially |
| Failure isolation | Instance failure = partial impact | Single point of failure |
| Scaling ceiling | Near-unlimited | Hardware limits |
| Default | ✓ Stateless workloads | ✓ Database, cache, single-writer |

### Auto-Scaling Rules

| Rule | Detail |
|---|---|
| Metric-driven | Scale on measured demand (CPU, request rate, queue depth). ✗ time-based only |
| Cooldown | Minimum 3 min between scale events. Prevents oscillation |
| Scale-up aggressive | Scale up at 70% threshold. ✗ wait until saturated |
| Scale-down conservative | Scale down at 30% sustained 10 min. Prevents premature shrink |
| Minimum instances | Production: ≥ 2 always. ✗ scale to zero in production (except batch) |
| Maximum instances | Hard cap per service. Prevents runaway scaling + cost explosion |
| Health-aware | New instance passes health check before receiving traffic |

### Capacity Planning

- Quarterly review: current utilization vs projected growth. Headroom target: 40% spare at peak.
- Load-test before scaling assumptions; verify linear scaling holds. Identify bottleneck resource per service.
- Document scaling limits (at what load each service degrades). Pre-provision for known traffic events.

---

## 8. Backup & Disaster Recovery

Sole owner of backup cadence, DR patterns, RTO/RPO, and failover testing. `database` keeps only WAL/PITR + replica lag + restore mechanics and defers cadence/RTO/RPO here.

### Backup Requirements

| Data Class | Frequency | Retention | Encryption |
|---|---|---|---|
| Database (transactional) | Continuous (WAL/replication) + daily full | 30 days incremental · 1 year full | At rest + in transit |
| Database (analytical) | Daily full | 90 days | At rest + in transit |
| Object storage / files | Daily incremental · weekly full | 90 days incremental · 1 year full | At rest + in transit |
| Configuration / secrets | On every change (version controlled) | Indefinite (git history) | Encrypted at rest |
| Container images | Retained in registry (§2) | Per registry policy | Registry-managed |

### Backup Rules

| Rule | Detail |
|---|---|
| Automated | All backups automated. ✗ manual procedures as primary strategy |
| Tested | Restore tested ≥ monthly for critical data, quarterly for all data |
| Offsite | Stored in separate region/AZ from primary |
| Monitored | Job success/failure monitored. Alert on failure |
| Immutable | Production backups immutable for retention period. ✗ overwrite/delete before expiry |
| Documented | Restore procedure is a runbook; tested by on-call, not just backup team |

### RTO / RPO Targets

| Tier | RPO (max data loss) | RTO (max downtime) | Example |
|---|---|---|---|
| Critical | < 1 min (synchronous replication) | < 15 min | Payment, auth |
| High | < 15 min | < 1 hour | Core APIs, user-facing services |
| Standard | < 1 hour | < 4 hours | Internal tools, batch jobs |
| Low | < 24 hours | < 24 hours | Dev environments, analytics |

### Disaster Recovery Patterns

| Pattern | Use When | RPO | RTO | Cost |
|---|---|---|---|---|
| Active-active multi-region | Critical tier · zero tolerance | ~0 | Minutes | High (2x+) |
| Active-passive failover | High tier · cost-constrained | Minutes | 15–60 min | Medium (standby) |
| Pilot light | Standard tier · infrequent DR | Minutes–hours | 1–4 hours | Low (minimal standby) |
| Backup and restore | Low tier · long recovery acceptable | Hours | Hours–day | Lowest (storage) |

**DR failover tested ≥ semi-annually** (large production: monthly drill). ✗ untested DR plan counts as no plan.

---

## 9. Networking

### Service Discovery

- Registry-based: services register at startup, deregister on shutdown; health-checked entries only.
- DNS-based discovery or service mesh. ✗ hardcoded IPs/hostnames in application code.
- Client-side caching with TTL ≤ 30s; stale cache → re-resolve.
- Graceful failover: unreachable endpoint → retry next healthy. See [architecture](../architecture/STANDARDS.md) §1 (circuit breaker).

### Load Balancing

- Layer 7 preferred for HTTP (path/header routing). ✗ route to instances failing health checks.
- Connection draining on removal: stop new, drain existing within grace period.
- ✗ sticky sessions unless required by stateful protocol — prefer stateless design.
- Rate limits at load balancer per client/API key. Protect backend from overload.

### TLS / SSL

| Rule | Detail |
|---|---|
| TLS everywhere | All service-to-service encrypted. ✗ plaintext in any environment above dev |
| TLS 1.2 minimum | ✗ TLS 1.0/1.1/SSLv3. Prefer TLS 1.3 |
| Certificate automation | Auto-provisioned + auto-renewed. ✗ manual certificate management |
| Certificate monitoring | Alert ≥ 30 days before expiry |
| mTLS internal | Mutual TLS between services when using service mesh |
| Termination point | At load balancer or sidecar proxy, ✗ in application code |

### DNS & Segmentation

- Service records TTL ≤ 300s (fast failover). Separate DNS zones per environment. DNS changes via IaC (§1), ✗ manual edits.
- Production network isolated from non-production. ✗ shared VPC/VLAN. Database tier ✗ internet-accessible — application tier mediates.
- Egress restricted: whitelist outbound destinations. Default deny, explicit allow per service pair. See [security](../security/STANDARDS.md).

---

## 10. Secrets & Credentials

Infrastructure secrets managed through centralized vault. ✗ secrets in source · env files in repo · container images · CI/CD config files. Vault + injection **mechanics** live here; **rotation cadence + lifecycle + token classes → [security](../security/STANDARDS.md)**.

### Vault Rules

| Rule | Detail |
|---|---|
| Centralized store | Single source of truth (vault service). ✗ scattered across config files |
| Access-controlled | Per-service, per-environment policies. Service A ✗ reads Service B secrets |
| Audit logged | Every read/write/list logged with actor, timestamp, resource |
| Encrypted at rest | Vault storage encrypted with managed keys; key rotation automated |
| Dynamic secrets | Prefer short-lived dynamic credentials (DB, cloud IAM). ✗ long-lived static when dynamic available |
| Lease-based | Secrets have TTL. Application re-fetches/renews before expiry |

### Injection Patterns

| Pattern | Use When |
|---|---|
| Environment variable at runtime | Orchestrator injects from vault at pod start |
| Sidecar/init container | Vault agent fetches secrets, writes to shared volume |
| Application vault client | App authenticates to vault, fetches secrets directly |
| Mounted secret volume | Orchestrator mounts secret as file; app reads path |

✗ baking secrets into images. ✗ passing secrets via command-line arguments (visible in process list). Rotation frequencies + token lifetimes → [security](../security/STANDARDS.md).

---

## 11. Cost Management

### Infrastructure Cost

| Rule | Detail |
|---|---|
| Measured allocation | Requests/limits based on measured utilization, ✗ estimates. Profile before sizing |
| Right-size quarterly | Review CPU/memory vs actual usage; adjust over-provisioned |
| Utilization targets | Compute 50–70% average. < 30% over-provisioned. > 80% under-provisioned |
| Reserved vs spot | Stable baseline → reserved/committed. Fault-tolerant batch → spot. ✗ spot for latency-sensitive |
| Tagged costs | All resources tagged (§1). Costs attributable to team + service |
| Budget alerts | Alert at 80% + 100% of monthly budget per team/service |
| Anomaly detection | Alert on cost increase > 20% day-over-day without matching traffic increase |
| Unit economics | Track cost-per-request / cost-per-user. Unit cost stable or decreasing as scale grows |

### LLM / API Token Spend

First-class cost class for agent + ML systems. `agent` and `ml` cross-reference here, ✗ restate.

| Rule | Detail |
|---|---|
| Budget caps | Per-request **and** per-tenant token/spend caps enforced. Exceed → reject or degrade, ✗ silently overspend |
| Cost as a metric | Cost per 1k tokens (input + output separately) tracked as a first-class metric alongside latency/error rate |
| Spend burn-rate alerts | Alert on spend burn-rate (projected month-end vs budget), not only end-of-month total |
| Cheaper-model routing | Route to the cheapest model meeting the quality bar; reserve premium models for tasks that need them |
| Attribution | Token spend tagged per tenant/feature/request-class. Unattributed spend ✗ allowed above dev |
| Cache + batch | Cache/deduplicate identical prompts; batch where the API supports it, to cut cost per unit of work |

### Cleanup

- Unused resources scanned weekly; idle > 14 days → flagged for deletion.
- Non-production environments auto-scaled to zero or shut down outside business hours.
- Orphaned resources (unattached volumes, unused IPs, stale snapshots) cleaned weekly.
- Old container images purged per retention policy (§2). Expired feature-branch environments destroyed automatically (§4).

---

## 12. Scale Matrix

| Rule | Side Project / PoC | Small Production | Large Production |
|---|---|---|---|
| IaC (§1) | Scripts or manual ok | IaC for all infra; local state ok | Full IaC · remote state · drift detection · peer review |
| Containers (§2) | Any base; no scanning | Minimal base · scanning on build | Distroless · signed · enforced size budgets |
| Deployment (§3) | Manual deploy ok | Rolling update via CI/CD | Canary/blue-green · automated rollback · smoke tests |
| Environments (§4) | Local + production | Dev + staging + production | Full tier model · ephemeral envs · parity enforced |
| Metrics (§5) | Basic health check | Infra + application metrics collected | Full metric set feeding observability alert/SLO layer |
| Incident + on-call (§6) | Fix when noticed | Severity levels · postmortems SEV-1/2 · informal on-call | Full workflow · ≥ 2-engineer rotation · all postmortems |
| Scaling (§7) | Single instance | Manual scaling; min 2 instances | Auto-scaling · capacity planning · load testing |
| Backup & DR (§8) | Manual backup | Automated daily backups · quarterly restore test | Continuous replication · multi-region · monthly DR drill |
| Networking (§9) | Direct connections | TLS everywhere · basic segmentation | Service mesh · mTLS · network policies · L7 LB |
| Secrets (§10) | Environment variables | Centralized vault · no static creds in code | Dynamic secrets · injection mechanics · audit logging |
| Cost (§11) | Not needed | Tagged resources · monthly review · token caps if LLM | Full unit economics · token burn-rate alerts · automated cleanup |

### Scale Transition

Graduate incrementally (strangler fig, [architecture](../architecture/STANDARDS.md) §11). Priority order: 1. Secrets (security risk) · 2. Backup & DR (data-loss risk) · 3. Metrics feeding observability (visibility) · 4. IaC (reproducibility) · 5. Deployment automation (reliability) · 6. Everything else.

---

## 13. Checklist

### New Service — Infrastructure Setup

- [ ] Infrastructure defined in IaC, committed to version control (§1)
- [ ] All resources tagged: environment, service, team, cost-center, managed-by (§1)
- [ ] Container image: minimal base, non-root, read-only rootfs, health check, within size budget (§2)
- [ ] Image scanned; no critical/high findings (§2)
- [ ] Deployment strategy selected with automated rollback (§3)
- [ ] All environments provisioned from IaC; parity validated (§4)
- [ ] Infrastructure + application metrics collected; wired to observability alert/SLO layer (§5)
- [ ] Incident severity levels assigned; escalation path defined (§6)
- [ ] On-call rotation established: ≥ 2 engineers, primary + secondary, handoff documented (§6)
- [ ] Paging policy: page only on SLO burn / user-facing impact (§6)
- [ ] Scaling limits defined: min instances, max instances, scale triggers (§7)
- [ ] Backup configured and first restore test passed (§8)
- [ ] RTO/RPO tier assigned and validated (§8)
- [ ] TLS on all endpoints; certificates auto-renewed (§9)
- [ ] Network segmentation enforced; egress restricted (§9)
- [ ] Secrets in vault; no static credentials in code or config (§10)
- [ ] Cost tags applied; budget alert configured; token caps set if LLM/API spend (§11)

### Ongoing Operations

- [ ] Monthly: cost review + right-sizing; restore test for critical-tier data (§8, §11)
- [ ] Quarterly: capacity planning; resource right-sizing (§7, §11)
- [ ] Semi-annually: DR failover drill (§8)
- [ ] Per incident: blameless postmortem within SLA; action items tracked (§6)

### Pre-Production Gate

- [ ] All "New Service" items completed
- [ ] Load test passed at 2x expected peak traffic (§7)
- [ ] DR failover tested at least once (§8)
- [ ] Runbooks written for all paging alerts (§6)
- [ ] Deployment runbook written and rehearsed (§3)
- [ ] Cost projection reviewed and approved (§11)
