# DevOps & Infrastructure Standards

Rules for infrastructure provisioning, deployment, environment management,
incident response, and operational resilience. Language-agnostic.

Composable with: architecture/STANDARDS.md (core principles),
security/STANDARDS.md (infrastructure security), cicd/STANDARDS.md
(deployment pipeline), observability/STANDARDS.md (monitoring integration),
configuration/STANDARDS.md (environment management).

---

## Table of Contents

1. [Infrastructure as Code](#1-infrastructure-as-code)
2. [Container Standards](#2-container-standards)
3. [Deployment Patterns](#3-deployment-patterns)
4. [Environment Management](#4-environment-management)
5. [Monitoring & Alerting](#5-monitoring--alerting)
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

All infrastructure defined in version-controlled declarative files.
✗ manual provisioning · ✗ clickops · ✗ undocumented changes.

### Core Rules

| Rule | Detail |
|---|---|
| Declarative over imperative | Describe desired state; tooling reconciles. See architecture/STANDARDS.md §10 (Reconciliation Loop) |
| Version controlled | Every infra file committed to repo; same branching rules as application code. See git/STANDARDS.md |
| Idempotent applies | Running same config twice → identical result. ✗ side effects on re-apply |
| Reproducible | Any environment rebuildable from repo + secrets vault alone. ✗ snowflake servers |
| Modular | Reusable components per resource type. ✗ monolithic config files >300 lines |
| Parameterized | Environment differences expressed as variables, not separate configs |
| Drift detection | Automated comparison: declared state vs actual state. Alert on divergence |
| Plan before apply | Every change previewed (dry-run/plan) before execution. ✗ direct apply without review |
| State management | Remote state with locking. ✗ local-only state files. ✗ concurrent state modification |
| Least privilege | IaC service accounts get minimum permissions required for provisioning |

### Change Workflow

1. Branch from main → modify infra code
2. Run plan/dry-run → review diff
3. Peer review required for production changes
4. Apply via CI/CD pipeline. ✗ manual apply to production
5. Verify drift detection passes post-apply
6. Commit state changes

### Resource Tagging

Every provisioned resource tagged with:

| Tag | Purpose |
|---|---|
| `environment` | dev / staging / production |
| `service` | Owning service name |
| `team` | Responsible team |
| `cost-center` | Budget allocation |
| `managed-by` | IaC tool identifier |
| `created-date` | Provisioning timestamp |

✗ untagged resources in any environment above dev.

---

## 2. Container Standards

### Base Image Selection

| Criteria | Rule |
|---|---|
| Minimal base | Use distroless or alpine variants. ✗ full OS images unless required by runtime |
| Pinned versions | Tag with digest hash, not `latest`. ✗ mutable tags in production |
| Trusted sources | Official images or internal registry only. ✗ unverified third-party images |
| Regular rebuilds | Base images rebuilt ≥ monthly to pull security patches |
| Scanning | Every image scanned for CVEs before registry push. Block critical/high severity |

### Image Build Rules

| Rule | Detail |
|---|---|
| Layer optimization | Least-changing layers first; frequently-changing layers last |
| Multi-stage builds | Build dependencies ✗ in final image. Compile in builder stage, copy artifacts only |
| Single process | One process per container. ✗ init systems inside containers ; exception: log sidecar |
| No secrets in layers | ✗ secrets in build args, ENV, or COPY. Use runtime injection only |
| Size budget | Application images < 500MB. Alert if exceeded. Distroless targets < 100MB |
| Reproducible builds | Same source commit → same image (content-addressable). Pin all package versions |
| Non-root execution | Container runs as non-root user. ✗ root in production containers |
| Read-only filesystem | Root filesystem mounted read-only. Writable volumes for data paths only |
| Health checks | Every container defines health check endpoint or command |
| Graceful shutdown | Handle SIGTERM → drain connections → exit within termination grace period |

### Image Lifecycle

| Stage | Action |
|---|---|
| Build | CI builds on every merge to main |
| Scan | Vulnerability scan + policy check |
| Tag | Semantic version + git SHA |
| Push | To internal registry only |
| Promote | dev → staging → production (same image, ✗ rebuild) |
| Retain | Keep last 10 versions per service. Purge untagged images > 7 days |

---

## 3. Deployment Patterns

### Strategy Selection

| Strategy | Use When | Risk | Rollback Speed | Resource Cost |
|---|---|---|---|---|
| Rolling update | Default for stateless services | Low | Medium (progressive) | 1x + surge capacity |
| Blue-green | Zero-downtime required · database migration involved | Low | Fast (switch route) | 2x during deploy |
| Canary | High-risk change · large user base · measurable SLIs | Very low | Fast (route shift) | 1x + canary slice |
| Recreate | Stateful singleton · incompatible versions cannot coexist | High | Slow (full redeploy) | 1x |
| Feature flag | Decouple deploy from release · gradual rollout by segment | Very low | Instant (flag toggle) | 1x |

See cicd/STANDARDS.md for pipeline integration of deployment strategies.

### Deployment Rules

| Rule | Detail |
|---|---|
| Immutable artifacts | Deploy exact artifact from build. ✗ recompile at deploy time |
| Promotion not rebuild | Same image/artifact promoted across environments. ✗ separate builds per env |
| Automated rollback | Failed health checks → automatic rollback to last known good. ✗ manual-only rollback |
| Deployment timeout | Every deployment has max duration. Exceeded → automatic rollback |
| One service at a time | ✗ simultaneous deployment of coupled services unless orchestrated with dependency order |
| Drain before stop | Remove instance from load balancer → wait for in-flight requests → stop |
| Smoke tests | Post-deploy smoke test suite runs automatically. Failure → rollback |
| Deploy log | Every deployment recorded: who, what version, when, which environment, outcome |

### Rollback Criteria

Automatic rollback triggers:
- Health check failure rate > 50% within first 5 minutes
- Error rate increase > 2x baseline within canary window
- Latency p99 increase > 3x baseline
- Any critical alert fired during deployment window

---

## 4. Environment Management

Every environment reproducible from IaC + configuration + secrets vault.
✗ environment-specific code paths. Behavior differences expressed through
configuration only. See configuration/STANDARDS.md for cascade rules.

### Environment Tiers

| Tier | Environment | Purpose | Data | Access |
|---|---|---|---|---|
| 0 | Local/dev | Developer workstation | Synthetic/seed | Developer |
| 1 | CI | Automated test execution | Synthetic | Pipeline |
| 2 | Staging | Pre-production validation | Anonymized copy of production | Team |
| 3 | Production | Live traffic | Real | Restricted |

### Parity Rules

| Rule | Detail |
|---|---|
| Architecture parity | All environments use same topology (services, queues, databases). ✗ skipping components in lower tiers |
| Version parity | Staging runs same versions of all dependencies as production |
| Configuration parity | Same config structure across all tiers; only values differ (endpoints, credentials, resource sizes) |
| Data shape parity | Non-production data matches production schema exactly. ✗ schema drift between environments |
| Infrastructure parity | Same OS, runtime versions, networking model. Scale differs, architecture does not |

### Provisioning Rules

- New environment provisioned entirely from IaC. Time to provision ≤ 1 hour for full stack
- Environment teardown fully automated. ✗ orphaned resources after decommission
- Ephemeral environments for feature branches — auto-destroy after merge or 7 days idle
- Production-like environment available for load testing — isolated from staging
- Environment inventory maintained: list of all active environments, their purpose, owner, expiry

---

## 5. Monitoring & Alerting

Infrastructure and application monitoring required for all production services.
See observability/STANDARDS.md for structured logging, metrics format, and
health check patterns.

### Infrastructure Metrics (required)

| Metric | Collection Interval | Alert Threshold |
|---|---|---|
| CPU utilization | 30s | > 80% sustained 5 min |
| Memory utilization | 30s | > 85% sustained 5 min |
| Disk usage | 60s | > 80% capacity |
| Disk I/O latency | 30s | > 50ms p99 sustained 2 min |
| Network throughput | 30s | > 80% link capacity |
| Container restart count | Event-driven | > 3 restarts in 10 min |
| Node availability | 15s | Any node unreachable > 1 min |

### Application Metrics (required)

| Metric | Collection Interval | Alert Threshold |
|---|---|---|
| Request rate | 10s | Deviation > 3σ from baseline |
| Error rate (5xx) | 10s | > 1% of total requests |
| Latency p50 / p95 / p99 | 10s | p99 > 2x baseline |
| Queue depth | 30s | > 80% configured max |
| Active connections | 30s | > 80% connection pool max |
| Dependency health | 30s | Any dependency unhealthy > 1 min |
| Business metrics | Service-specific | Service-specific |

### Alert Design Rules

| Rule | Detail |
|---|---|
| Actionable | Every alert has a defined response action. ✗ informational-only alerts in paging channels |
| Severity mapped | Every alert assigned severity level (§6). Severity drives notification channel |
| Deduplicated | Same root cause → one alert, not N alerts per instance |
| Auto-resolving | Alert clears when condition resolves. ✗ manual close required for transient issues |
| Runbook linked | Every paging alert links to runbook with diagnostic steps |
| SLO-based | Prefer SLO burn-rate alerts over static thresholds for user-facing metrics |
| Tuned quarterly | Review alert noise quarterly. Tune or remove alerts with > 50% false positive rate |
| Escalation path | Unacknowledged alert escalates after defined timeout (see §6) |

### Monitoring Architecture

- Metrics pipeline independent from application data path. Monitoring failure ✗ impacts application
- Retention: raw metrics ≥ 15 days, downsampled ≥ 1 year
- Dashboards: one service overview dashboard per service + one infrastructure overview
- Dashboard hierarchy: system overview → service detail → instance detail

---

## 6. Incident Response

### Severity Levels

| Severity | Definition | Response Time | Update Cadence | Escalation After |
|---|---|---|---|---|
| SEV-1 Critical | Complete service outage · data loss · security breach | 15 min | Every 30 min | 30 min unacknowledged |
| SEV-2 Major | Partial outage · degraded for >50% users · SLO breach | 30 min | Every 1 hour | 1 hour unacknowledged |
| SEV-3 Minor | Degraded for <50% users · non-critical feature down | 4 hours | Every 4 hours | 8 hours unacknowledged |
| SEV-4 Low | Cosmetic · minor degradation · workaround available | Next business day | Daily | None |

### Incident Workflow

1. **Detect** → automated alert or manual report
2. **Triage** → assign severity, incident commander, communication lead
3. **Communicate** → status page update within response time SLA
4. **Diagnose** → identify root cause or contributing factors
5. **Mitigate** → restore service (fix forward or rollback). Mitigation priority > root cause
6. **Resolve** → confirm full recovery, monitoring returns to baseline
7. **Postmortem** → blameless review within 5 business days (SEV-1/2), 10 days (SEV-3)

### Postmortem Rules

| Rule | Detail |
|---|---|
| Blameless | Focus on systems, processes, and tooling. ✗ individual blame |
| Timeline | Minute-by-minute timeline from detection to resolution |
| Root cause | Identify contributing factors, not single root cause. Use 5-whys or fault tree |
| Action items | Every postmortem produces ≥ 1 concrete action item with owner and deadline |
| Follow-through | Action items tracked to completion. Review in next team sync |
| Published | Postmortems accessible to entire engineering organization |
| Recurrence check | If same root cause appears twice → escalate remediation priority to critical |

### Remediation Timelines

| Severity | Mitigation SLA | Permanent Fix SLA |
|---|---|---|
| SEV-1 | Immediate (during incident) | 5 business days |
| SEV-2 | Within 4 hours | 10 business days |
| SEV-3 | Within 1 business day | Next sprint |
| SEV-4 | Best effort | Backlog |

---

## 7. Scaling Strategy

### Horizontal vs Vertical Selection

| Factor | Horizontal (add instances) | Vertical (add resources) |
|---|---|---|
| Stateless services | Preferred | Fallback |
| Stateful services | Requires coordination (sharding, consensus) | Preferred initially |
| Cost efficiency | Linear cost scaling | Diminishing returns at high end |
| Failure isolation | Instance failure = partial impact | Single point of failure |
| Complexity | Load balancer + service discovery required | Simple; no coordination |
| Scaling ceiling | Near-unlimited | Hardware limits |
| Default choice | ✓ Stateless workloads | ✓ Database, cache, single-writer |

### Auto-Scaling Rules

| Rule | Detail |
|---|---|
| Metric-driven | Scale on measured demand (CPU, request rate, queue depth). ✗ time-based only |
| Cooldown period | Minimum 3 min between scale events. Prevents oscillation |
| Scale-up aggressive | Scale up at 70% threshold. ✗ wait until saturated |
| Scale-down conservative | Scale down at 30% threshold sustained 10 min. Prevents premature shrink |
| Minimum instances | Production services: minimum 2 instances always. ✗ scale to zero in production (except batch) |
| Maximum instances | Hard cap defined per service. Prevents runaway scaling and cost explosion |
| Health-aware | New instance must pass health check before receiving traffic |
| Graceful drain | Instance marked for removal → drain connections → terminate |

### Capacity Planning

- Quarterly capacity review: current utilization vs projected growth
- Headroom target: 40% spare capacity at peak load
- Load test before scaling assumptions: verify linear scaling holds
- Identify bottleneck resources per service (CPU, memory, I/O, network, database connections)
- Document scaling limits: at what load does each service degrade?
- Pre-provision for known traffic events (launches, marketing campaigns)

---

## 8. Backup & Disaster Recovery

### Backup Requirements

| Data Class | Backup Frequency | Retention | Encryption |
|---|---|---|---|
| Database (transactional) | Continuous (WAL/replication) + daily full | 30 days incremental · 1 year full | At rest + in transit |
| Database (analytical) | Daily full | 90 days | At rest + in transit |
| Object storage / files | Daily incremental · weekly full | 90 days incremental · 1 year full | At rest + in transit |
| Configuration / secrets | On every change (version controlled) | Indefinite (git history) | Encrypted at rest |
| Container images | Retained in registry (§2 lifecycle) | Per registry retention policy | Registry-managed |

### Backup Rules

| Rule | Detail |
|---|---|
| Automated | All backups fully automated. ✗ manual backup procedures as primary strategy |
| Tested | Restore tested ≥ monthly for critical data, quarterly for all data |
| Offsite | Backups stored in separate region/availability zone from primary |
| Monitored | Backup job success/failure monitored. Alert on failure |
| Immutable | Production backups immutable for retention period. ✗ overwrite or delete before expiry |
| Documented | Restore procedure documented as runbook. Restore tested by on-call, not just backup team |

### RTO / RPO Targets

| Tier | RPO (max data loss) | RTO (max downtime) | Example |
|---|---|---|---|
| Critical | < 1 min (synchronous replication) | < 15 min | Payment processing, auth |
| High | < 15 min | < 1 hour | Core APIs, user-facing services |
| Standard | < 1 hour | < 4 hours | Internal tools, batch jobs |
| Low | < 24 hours | < 24 hours | Dev environments, analytics |

### Disaster Recovery Patterns

| Pattern | Use When | RPO | RTO | Cost |
|---|---|---|---|---|
| Active-active multi-region | Critical tier · zero tolerance | ~0 | Minutes | High (2x+ resources) |
| Active-passive failover | High tier · cost-constrained | Minutes | 15–60 min | Medium (standby resources) |
| Pilot light | Standard tier · infrequent DR need | Minutes–hours | 1–4 hours | Low (minimal standby) |
| Backup and restore | Low tier · acceptable long recovery | Hours | Hours–day | Lowest (storage only) |

DR failover tested ≥ annually. ✗ untested DR plan counts as no plan.

---

## 9. Networking

### Service Discovery

| Rule | Detail |
|---|---|
| Registry-based | Services register at startup, deregister on shutdown. Health-checked entries only |
| DNS or service mesh | Use DNS-based discovery or service mesh. ✗ hardcoded IPs or hostnames in application code |
| Client-side caching | Discovery results cached with TTL ≤ 30s. Stale cache → fallback to re-resolve |
| Graceful failover | Unreachable endpoint → retry next healthy endpoint. See architecture/STANDARDS.md §1 (Circuit Breaker) |

### Load Balancing

| Rule | Detail |
|---|---|
| Layer 7 preferred | Use application-layer (L7) load balancing for HTTP services. Enables path/header routing |
| Health-check gated | ✗ route traffic to instances failing health checks |
| Connection draining | On instance removal: stop new connections, drain existing within grace period |
| Sticky sessions | ✗ sticky sessions unless explicitly required by stateful protocol. Prefer stateless design |
| Rate limiting | Rate limits at load balancer level per client/API key. Protect backend from overload |

### TLS / SSL

| Rule | Detail |
|---|---|
| TLS everywhere | All service-to-service communication encrypted. ✗ plaintext in any environment above dev |
| TLS 1.2 minimum | ✗ TLS 1.0, 1.1, SSLv3. Prefer TLS 1.3 |
| Certificate automation | Certificates auto-provisioned and auto-renewed. ✗ manual certificate management |
| Certificate monitoring | Alert ≥ 30 days before expiry |
| mTLS for internal | Mutual TLS between services when using service mesh |
| Termination point | TLS terminated at load balancer or sidecar proxy, not in application code |

### DNS Rules

- TTL ≤ 300s for service records. Enables fast failover
- Separate DNS zones per environment. ✗ shared DNS between production and non-production
- DNS changes via IaC (§1). ✗ manual DNS edits
- Health-checked DNS for multi-region failover

### Network Segmentation

- Production network isolated from non-production. ✗ shared VPC/VLAN
- Database tier not directly accessible from internet. Application tier mediates all access
- Egress restricted: services whitelist outbound destinations. ✗ unrestricted outbound
- Network policies enforced: default deny, explicit allow per service pair. See security/STANDARDS.md

---

## 10. Secrets & Credentials

All infrastructure secrets managed through centralized vault.
✗ secrets in source code · ✗ secrets in environment files committed to repo ·
✗ secrets in container images · ✗ secrets in CI/CD config files.

See security/STANDARDS.md for application-level secret handling and
configuration/STANDARDS.md for secret cascade patterns.

### Vault Rules

| Rule | Detail |
|---|---|
| Centralized store | Single source of truth for secrets (vault service). ✗ scattered across config files |
| Access-controlled | Per-service, per-environment access policies. Service A ✗ reads Service B secrets |
| Audit logged | Every secret read/write/list logged with actor, timestamp, resource |
| Encrypted at rest | Vault storage encrypted with managed keys. Key rotation automated |
| Dynamic secrets | Prefer short-lived dynamic credentials (database, cloud IAM). ✗ long-lived static creds when dynamic available |
| Lease-based | Secrets have TTL. Application re-fetches or renews before expiry |

### Rotation Rules

| Secret Type | Rotation Frequency | Method |
|---|---|---|
| Database credentials | ≤ 90 days (prefer dynamic per-session) | Vault-generated, auto-rotated |
| API keys | ≤ 90 days | Dual-key rotation (new key active before old revoked) |
| TLS certificates | Auto-renewed ≥ 30 days before expiry | Certificate automation (§9) |
| Encryption keys | ≤ 1 year | Key versioning; decrypt with old, encrypt with new |
| Service account tokens | ≤ 90 days | Token refresh via identity provider |
| SSH keys | ≤ 1 year (prefer certificate-based SSH) | Re-generate and distribute via automation |

### Secret Injection Patterns

| Pattern | Use When |
|---|---|
| Environment variable at runtime | Container orchestrator injects from vault at pod start |
| Sidecar/init container | Vault agent fetches secrets, writes to shared volume |
| Application vault client | Application directly authenticates to vault, fetches secrets |
| Mounted secret volume | Orchestrator mounts secret as file. Application reads file path |

✗ baking secrets into images. ✗ passing secrets via command-line arguments (visible in process list).

---

## 11. Cost Management

### Resource Right-Sizing

| Rule | Detail |
|---|---|
| Measured allocation | Resource requests/limits based on measured utilization, not estimates. Profile before sizing |
| Right-size quarterly | Review CPU/memory allocation vs actual usage quarterly. Adjust over-provisioned resources |
| Utilization targets | Compute: 50–70% average utilization. < 30% → over-provisioned. > 80% → under-provisioned |
| Reserved capacity | Stable baseline workloads → reserved/committed pricing. Variable → on-demand/spot |
| Spot/preemptible | Fault-tolerant batch workloads → spot instances. ✗ spot for latency-sensitive services |

### Cost Monitoring

| Rule | Detail |
|---|---|
| Tagged costs | All resources tagged (§1 Resource Tagging). Costs attributable to team + service |
| Budget alerts | Alert at 80% and 100% of monthly budget per team/service |
| Anomaly detection | Alert on cost increase > 20% day-over-day without corresponding traffic increase |
| Monthly review | Monthly cost review per team. Identify top 5 cost drivers + optimization opportunities |
| Unit economics | Track cost-per-request or cost-per-user. Ensure unit cost stable or decreasing as scale increases |

### Cleanup Rules

- Unused resources identified weekly via automated scan. Resources idle > 14 days → flagged for deletion
- Non-production environments auto-scaled to zero or shut down outside business hours
- Orphaned resources (unattached volumes, unused IPs, stale snapshots) cleaned weekly
- Old container images purged per retention policy (§2)
- Expired feature-branch environments destroyed automatically (§4)

