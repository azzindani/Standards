# Standards Router

> Catalog of every standard and the rule for which ones a given project loads.

**ID** `router` · **Tier** Meta · **Version** 1.0
**Owns** standard catalog · tier model · project-type routing · load order
**Defers to** file structure → [TEMPLATE.md](TEMPLATE.md) · authoring rules → [CLAUDE.md](CLAUDE.md)
**Load with** [TEMPLATE.md](TEMPLATE.md)

---

## Table of Contents

1. [How Routing Works](#1-how-routing-works)
2. [Load Order](#2-load-order)
3. [Always-On Set](#3-always-on-set)
4. [Catalog](#4-catalog)
5. [Routes by Project Type](#5-routes-by-project-type)
6. [Routes by Surface](#6-routes-by-surface)
7. [Conflict Resolution](#7-conflict-resolution)
8. [Contested Topics](#8-contested-topics)
9. [Adding a Standard](#9-adding-a-standard)
10. [Checklist](#10-checklist)

---

## 1. How Routing Works

A project never loads all standards. It loads the **Always-On Set** (§3) plus every route that matches a surface or domain it actually has (§5, §6).

| Step | Action |
|---|---|
| 1 | Load Always-On Set — applies to every project regardless of type |
| 2 | Add the language route for each language in the repo |
| 3 | Add the surface route for each interface the system exposes (HTTP API, DB, CLI, web UI) |
| 4 | Add the domain route if the project is in a covered problem space (ML, pipeline, MCP, agent) |
| 5 | Resolve conflicts by tier precedence (§7) |

Routing is additive and idempotent. A standard loaded twice is loaded once.

---

## 2. Load Order

Load order matters: later tiers assume earlier tiers are in effect, and conflict resolution (§7) is tier-directional.

```text
Foundation → Core → Delivery → Interface → Domain → Language
```

| Tier | Question it answers | Loaded |
|---|---|---|
| Foundation | How is the system structured? | Always |
| Core | How do we prove it works and keep it safe? | Always |
| Delivery | How does it reach production? | Always |
| Interface | How does the outside world talk to it? | Per surface |
| Domain | What does this problem space demand? | Per domain |
| Language | What is idiomatic here? | Per language |

---

## 3. Always-On Set

Non-negotiable. Every project, every size, from first commit.

| Standard | Why always |
|---|---|
| [architecture](architecture/STANDARDS.md) | Layering + dependency rules govern all code |
| [design](design/STANDARDS.md) | Module + abstraction rules govern all modules |
| [directory](directory/STANDARDS.md) | Layout + naming govern all files |
| [code_writing](code_writing/STANDARDS.md) | Readability + function style govern all functions |
| [error_handling](error_handling/STANDARDS.md) | Every system fails; failure is not optional |
| [testing](testing/STANDARDS.md) | Untested code is unproven code |
| [security](security/STANDARDS.md) | Validation boundary + secrets apply to all input |
| [observability](observability/STANDARDS.md) | Unobservable production is unoperable production |
| [configuration](configuration/STANDARDS.md) | Every project has environments and secrets |
| [dependencies](dependencies/STANDARDS.md) | Every project has a supply chain |
| [documentation](documentation/STANDARDS.md) | Undocumented systems decay |
| [git](git/STANDARDS.md) | Every project has history |
| [cicd](cicd/STANDARDS.md) | Manual delivery is unrepeatable delivery |
| [code_review](code_review/STANDARDS.md) | Unreviewed code is unowned code |
| [workflow](workflow/STANDARDS.md) | Idea → PoC → production lifecycle |

Scale relief: at **Prototype** scale, `cicd` reduces to lint+test on push and `code_review` to self-review. The standard is still loaded — its Scale Matrix says what applies.

---

## 4. Catalog

### Meta

| Standard | Owns |
|---|---|
| [TEMPLATE.md](TEMPLATE.md) | Standard file structure · header schema · CI contract |
| [ROUTER.md](ROUTER.md) | Catalog · tier model · routing |
| [CLAUDE.md](CLAUDE.md) | Authoring + density rules for this repo |

### Foundation

| Standard | Owns |
|---|---|
| [architecture/STANDARDS.md](architecture/STANDARDS.md) | Layer model · dependency rules · state · concurrency · extension |
| [design/STANDARDS.md](design/STANDARDS.md) | Design patterns · module design · abstraction rules |
| [directory/STANDARDS.md](directory/STANDARDS.md) | Project layout · file organization · naming |
| [code_writing/STANDARDS.md](code_writing/STANDARDS.md) | Clean code · readability · function style · naming |

### Core

| Standard | Owns |
|---|---|
| [testing/STANDARDS.md](testing/STANDARDS.md) | Pyramid · classification · coverage · mocking · contract tests |
| [testing/REALITY.md](testing/REALITY.md) | Reality dimensions · faults · concurrency · time · drift |
| [testing/PRESSURE.md](testing/PRESSURE.md) | Load · soak · chaos · survival · penetration |
| [error_handling/STANDARDS.md](error_handling/STANDARDS.md) | Error types · boundaries · recovery · reporting |
| [security/STANDARDS.md](security/STANDARDS.md) | Validation boundary · secrets · access control · supply chain |
| [observability/STANDARDS.md](observability/STANDARDS.md) | Structured logging · metrics · traces · SLOs · health |
| [performance/STANDARDS.md](performance/STANDARDS.md) | Budgets · profiling · caching · optimization |
| [configuration/STANDARDS.md](configuration/STANDARDS.md) | Cascade · environment · secrets · feature flags |
| [dependencies/STANDARDS.md](dependencies/STANDARDS.md) | Versioning · isolation · wrappers · lock files |
| [documentation/STANDARDS.md](documentation/STANDARDS.md) | Code docs · API docs · ADRs · runbooks |
| [expectation/STANDARDS.md](expectation/STANDARDS.md) | Peak comparator · quality dimensions · failure taxonomy |

### Delivery

| Standard | Owns |
|---|---|
| [git/STANDARDS.md](git/STANDARDS.md) | Branching · commits · tags · history |
| [cicd/STANDARDS.md](cicd/STANDARDS.md) | Build · test · lint · deploy · release stages |
| [code_review/STANDARDS.md](code_review/STANDARDS.md) | Review criteria · approval flow · feedback style |
| [devops/STANDARDS.md](devops/STANDARDS.md) | Infrastructure · containers · deployment · monitoring |
| [workflow/STANDARDS.md](workflow/STANDARDS.md) | Idea → PoC → production lifecycle · task management |

### Interface

| Standard | Owns |
|---|---|
| [api/STANDARDS.md](api/STANDARDS.md) | API design · protocols · contracts · versioning |
| [database/STANDARDS.md](database/STANDARDS.md) | Schema design · migrations · queries · transactions |
| [cli/STANDARDS.md](cli/STANDARDS.md) | Argument parsing · output format · exit codes · help |
| [web/STANDARDS.md](web/STANDARDS.md) | Routing · middleware · state · auth · frontend/backend |

### Domain

| Standard | Owns |
|---|---|
| [local_mcp/STANDARDS.md](local_mcp/STANDARDS.md) | MCP architecture · engine/server split · repo structure |
| [local_mcp/TOOLS.md](local_mcp/TOOLS.md) | Tool schema · annotations · patch protocol · token budget |
| [local_mcp/RUNTIME.md](local_mcp/RUNTIME.md) | State · receipts · transports · resource tiers |
| [local_mcp/DELIVERY.md](local_mcp/DELIVERY.md) | MCP testing · install · distribution · docs |
| [data_pipeline/STANDARDS.md](data_pipeline/STANDARDS.md) | ETL · data validation · schema enforcement · batch |
| [ml/STANDARDS.md](ml/STANDARDS.md) | Model lifecycle · experiment tracking · data versioning |
| [agent/STANDARDS.md](agent/STANDARDS.md) | CLAUDE.md · AGENTS.md · context engineering · density |
| [html_generation/STANDARDS.md](html_generation/STANDARDS.md) | Offline-first HTML output · module structure · security |
| [html_generation/THEMING.md](html_generation/THEMING.md) | Theme system · CSS architecture · UX patterns |
| [html_generation/CHARTS.md](html_generation/CHARTS.md) | Chart integration · dashboards · interactive controls |

### Language

| Standard | Owns |
|---|---|
| [python/STANDARDS.md](python/STANDARDS.md) | Style · typing · packaging · venvs · tooling |
| [rust/STANDARDS.md](rust/STANDARDS.md) | Ownership · crate structure · error handling · unsafe |
| [go/STANDARDS.md](go/STANDARDS.md) | Package layout · interfaces · error returns · concurrency |
| [typescript/STANDARDS.md](typescript/STANDARDS.md) | Types · modules · async patterns · null handling |
| [typescript/TOOLING.md](typescript/TOOLING.md) | Build config · project structure · lint · runtime validation |
| [shell/STANDARDS.md](shell/STANDARDS.md) | Script structure · error handling · variables · functions |
| [shell/HARDENING.md](shell/HARDENING.md) | Portability · file ops · security · testing |
| [sql/STANDARDS.md](sql/STANDARDS.md) | Query style · schema conventions · migration format |

---

## 5. Routes by Project Type

Always-On Set (§3) is implied in every row — only the additions are listed.

| Project type | Add |
|---|---|
| Python CLI tool | `python` · `cli` · `performance` |
| Python data pipeline | `python` · `data_pipeline` · `database` · `sql` · `performance` |
| MCP server | `local_mcp/*` · `python` (or `typescript`) · `cli` · `performance` |
| Web app (TS front + back) | `typescript/*` · `web` · `api` · `database` · `sql` · `performance` · `devops` |
| REST/gRPC service (Go/Rust) | `go` \| `rust` · `api` · `database` · `sql` · `performance` · `devops` |
| ML project | `python` · `ml` · `data_pipeline` · `database` · `performance` |
| Shell tooling | `shell/*` |
| Report / dashboard generator | `html_generation/*` · `python` (or `typescript`) |
| Agent / LLM system | `agent` · `expectation` · `local_mcp/*` (if tool-serving) |
| Library / SDK | language route · `api` (public surface = contract) · `documentation` |

---

## 6. Routes by Surface

Add per surface the system actually exposes. A system with three surfaces loads three routes.

| Surface | Add | Trigger |
|---|---|---|
| HTTP / gRPC API | `api` · `security` · `performance` | Any network-callable endpoint |
| Persistent store | `database` · `sql` | Any durable state beyond files |
| Command line | `cli` | Any user-invoked binary or entrypoint |
| Browser UI | `web` · `html_generation/*` | Any rendered UI |
| Deployed service | `devops` · `observability` · `testing/PRESSURE.md` | Anything with uptime expectations |
| Public package | `dependencies` · `documentation` · `api` | Anything others import |
| Batch / scheduled job | `data_pipeline` · `observability` | Anything running unattended |
| Model artifact | `ml` | Anything with trained weights |

---

## 7. Conflict Resolution

When two loaded standards give conflicting rules for the same decision:

| Precedence | Rule |
|---|---|
| 1 | **Specific beats general.** Language + Domain override Foundation + Core on syntax and idiom |
| 2 | **General beats specific on safety.** Foundation + Core override Language + Domain on correctness, security, error handling — a language idiom never licenses an unsafe boundary |
| 3 | **Stricter wins.** Two thresholds for the same metric → the tighter one applies |
| 4 | **Owner wins.** The standard whose `**Owns**` header covers the topic is authoritative; the other is stale → fix it |

A genuine unresolvable conflict is a repo bug. Fix the standards; ✗ pick a side per-project.

---

## 8. Contested Topics

Topics that multiple standards are tempted to claim. The **Owner** states the rule. Everyone else declares `**Defers to**`, cross-references, and keeps only their listed delta. ✗ restate the owner's rule.

| Topic | Owner | Everyone else keeps only |
|---|---|---|
| Secrets — rotation cadence · derived-values · lifecycle · token classes | [security](security/STANDARDS.md) | configuration: cascade + sourcing · devops: vault/injection mechanics · cicd: pipeline secret scoping · git: never-commit rule |
| Authn/authz — RBAC/ABAC model · token lifetimes · default-deny | [security](security/STANDARDS.md) | api: API-specific patterns · web: cookie attributes · CSRF · frontend gating |
| Pagination · N+1 | [database](database/STANDARDS.md) | performance: detection + profiling · sql: query syntax · api: cursor + envelope contract |
| Semver · changelog format · release tagging | [git](git/STANDARDS.md) | cicd: release automation · documentation: changelog rendering · cli: compatibility promise |
| Backup · DR · RTO/RPO · failover cadence | [devops](devops/STANDARDS.md) | database: WAL/PITR · replica lag · restore mechanics |
| Alert design rules · resource thresholds | [observability](observability/STANDARDS.md) | devops: which infra metrics to collect |
| License policy · allowed license tiers | [dependencies](dependencies/STANDARDS.md) | every other standard: cross-reference only |
| Coverage thresholds · mocking policy · pyramid | [testing](testing/STANDARDS.md) | language standards: framework choice + invocation only |
| Offline-first HTML output · theming | [html_generation](html_generation/STANDARDS.md) | local_mcp: cross-reference only |
| Input validation boundary | [security](security/STANDARDS.md) | each standard: its own injection vectors |
| Accessibility (WCAG) · i18n/l10n | [web](web/STANDARDS.md) | html_generation: cross-reference only |
| Cost — infra spend · LLM token spend | [devops](devops/STANDARDS.md) | agent + ml: cross-reference only |

### Resolved contradictions

These were conflicting across standards. The value below is now authoritative — ✗ reintroduce the loser.

| Topic | Ruling |
|---|---|
| Access-token lifetime | Browser/user-facing ≤ 15 min + refresh-token rotation · service-to-service ≤ 1 h. Two classes, both stated in `security` |
| Secret rotation cadence | Long-lived service-account credentials ≤ 90 days · ephemeral CI/deploy tokens ≤ 24 h. Two classes, both stated in `security` |
| Resource alert thresholds | CPU > 85% · memory > 90% · disk > 85%, sustained 10 min. Stated in `observability` |
| DR failover test cadence | ≥ semi-annually (stricter of the two prior values wins) |
| Coverage gate | Tiered **branch** coverage by tier — ✗ flat line-coverage gate. Stated in `testing` |
| LGPL | Permitted with caution — dynamic linking only. ✗ flat ban |
| OFFSET pagination | Keyset by default · OFFSET only on datasets < 10K rows (stricter of the two prior values wins) |

---

## 9. Adding a Standard

1. Confirm no existing standard's `**Owns**` already covers the topic. Overlap → extend that standard.
2. Copy [TEMPLATE.md](TEMPLATE.md) §9 skeleton into `<domain>/STANDARDS.md`.
3. Assign a tier (§2). Tier decides load rules — get it right.
4. Declare `**Owns**` precisely. Every topic it claims must be removed from other standards and replaced with a cross-reference.
5. Register in the Catalog (§4) and in at least one route (§5 or §6). An unrouted standard is never loaded.
6. `python3 tools/validate.py` must pass.

---

## 10. Checklist

- [ ] Project loads the complete Always-On Set
- [ ] One language route loaded per language present in the repo
- [ ] One surface route loaded per interface the system exposes
- [ ] Domain route loaded if the project is in a covered problem space
- [ ] Load order respects Foundation → Core → Delivery → Interface → Domain → Language
- [ ] No standard claims a topic another standard already `**Owns**`
- [ ] Every standard in the repo appears in the Catalog (§4)
- [ ] Every standard appears in at least one route (§5 or §6)
- [ ] Conflicts resolved by tier precedence (§7), not by per-project preference
- [ ] No standard restates a contested topic owned by another (§8)
- [ ] No standard reintroduces a resolved contradiction (§8)
- [ ] `python3 tools/validate.py` passes
