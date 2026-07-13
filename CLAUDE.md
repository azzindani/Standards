# CLAUDE.md — Standards Repository Build Rules

## Core Principles

- **Enterprise production grade by default.** Every line written here operates in a live system operators depend on. No shortcuts, no "good enough for now" — treat every change as if it ships to production today.
- **Be proactive and curious.** When a request looks simple, decompose it first: scan for gaps, latent bugs, missing tests, schema drift, and dependency issues. Fix or flag them without waiting to be asked. The user must not need to loop back with follow-up instructions.
- **Deliver smart, respect time.** Read full request, infer intent. ✗ ask back-and-forth for things reasoned from context. ✗ discuss when ask is to do. Complete task, stop. Every forced back-and-forth = failure.
- **High-density output (caveman).** All responses and docs: max information-per-token, zero meaning lost.
  - **Strip:** articles (`a/an/the`) · weak modals (`should/would/may`) · scaffolding (`make sure to`, `always remember to`, `be careful to`) · meta (`note that`, `keep in mind`, `it is important`) · hedging (`generally/typically/usually`) · obvious subjects · restatements
  - **Operators:** `→` leads-to/use-instead · `·` co-required · `|` alternative · `✗` never/forbidden · `;` except · `!` critical
  - **Structure over prose:** comparisons → tables · condition+action → `X → Y` · workflow → `A → B → C` · related bullets → one merged line
  - **✗ compress (load-bearing):** negations (`never/not/no` — stripping inverts rule) · hard thresholds · exception clauses · code blocks · technical names · ordered sequences

---

## Repository Purpose

Central standards library for all projects. Each standard = one directory + one `STANDARDS.md` (+ optional split files). Standards are composable — projects **route** to a subset, never load everything.

Three meta files govern the repo. Read them before touching any standard:

| File | Role |
|---|---|
| [TEMPLATE.md](TEMPLATE.md) | Canonical structure every standard follows. CI-enforced contract |
| [ROUTER.md](ROUTER.md) | Catalog · tier model · which standards a given project loads |
| `CLAUDE.md` | This file — how to write standards in this repo |

---

## Writing Rules

- **Hard cap 499 lines per file. Target 400–480.** Over cap → split at a natural seam per [TEMPLATE.md](TEMPLATE.md) §8. CI fails the build over cap.
- **Zero code examples** — pure rules, patterns, tables. Exception: language standards (`python/` `rust/` `go/` `typescript/` `shell/` `sql/`) may and should carry code. CI enforces this.
- Every sentence = rule | clarification of rule. ✗ motivation paragraphs · ✗ tutorials · ✗ "why this matters"
- Tables over prose. One-liner rules over paragraphs.
- **One owner per topic.** Each standard declares `**Owns**` in its header. A rule lives in exactly one file. Every other standard that touches it declares `**Defers to**` and cross-references. ✗ restate another standard's rules.
- Cross-reference by relative link: `[architecture §4](../architecture/STANDARDS.md#4-function-placement)`. Dead links fail CI.
- Every standard has the full header schema · TOC · numbered sections · checklist at end · scale matrix if applicable. See [TEMPLATE.md](TEMPLATE.md) §3–§6.
- Write incrementally — section by section, not full file in one shot. ✗ write long content in single tool call — breaks on timeout. Write header + first sections → edit/append remaining sections in subsequent calls.
- Every new standard is registered in [ROUTER.md](ROUTER.md) §4 catalog **and** at least one route (§5/§6). An unrouted standard is never loaded.

## Conformance

```bash
python3 tools/validate.py
```

Checks: line cap · header schema · ID↔directory match · tier validity · TOC↔section parity · sequential numbering · checklist present and unticked · code-block policy · dead cross-references · router registration.

Must pass before every commit. CI runs it on push and PR — see `.github/workflows/standards.yml`.

---

## Standards Catalog

All standards are complete. Tier determines when a project loads them — see [ROUTER.md](ROUTER.md) §2.

### Meta

| Directory | Standard |
|---|---|
| — | `TEMPLATE.md` · `ROUTER.md` · `CLAUDE.md` |

### Foundation — always loaded

| # | Directory | Standard |
|---|---|---|
| 1 | `architecture/` | Layer model · dependency rules · state · concurrency · extension · evolution |
| 2 | `design/` | Design patterns · module design · abstraction rules |
| 3 | `directory/` | Project layout · file organization · naming |
| 4 | `code_writing/` | Clean code · readability · function style · identifier naming |

### Core — always loaded

| # | Directory | Standard |
|---|---|---|
| 5 | `testing/` | Pyramid · coverage · mocking (STANDARDS.md) · reality dimensions (REALITY.md) · pressure · survival · penetration (PRESSURE.md) |
| 6 | `error_handling/` | Error types · boundaries · recovery · reporting |
| 7 | `security/` | Validation boundary · secrets · access control · supply chain |
| 8 | `observability/` | Structured logging · metrics · traces · SLOs · health |
| 9 | `performance/` | Budgets · profiling · caching · optimization |
| 10 | `configuration/` | Cascade · environment · secrets · feature flags |
| 11 | `dependencies/` | Versioning · isolation · wrappers · lock files |
| 12 | `documentation/` | Code docs · API docs · ADRs · runbooks |
| 13 | `expectation/` | Peak comparator model · quality dimensions · failure taxonomy · benchmarks |

### Delivery — always loaded

| # | Directory | Standard |
|---|---|---|
| 14 | `git/` | Branching · commits · tags · workflows · history |
| 15 | `cicd/` | Build · test · lint · deploy · release stages |
| 16 | `code_review/` | Review criteria · approval flow · feedback style |
| 17 | `devops/` | Infrastructure · containers · deployment · monitoring |
| 18 | `workflow/` | Idea → PoC → production lifecycle · task management |

### Interface — loaded per surface

| # | Directory | Standard |
|---|---|---|
| 19 | `api/` | API design · protocols · contracts · versioning · serialization |
| 20 | `database/` | Schema design · migrations · queries · transactions |
| 21 | `cli/` | Argument parsing · output format · exit codes · help |
| 22 | `web/` | Routing · middleware · state · auth · frontend/backend |

### Domain — loaded per domain

| # | Directory | Standard |
|---|---|---|
| 23 | `local_mcp/` | MCP architecture · engine/server split (STANDARDS.md) · tool design (TOOLS.md) · state · transports (RUNTIME.md) · install · distribution (DELIVERY.md) |
| 24 | `data_pipeline/` | ETL · data validation · schema enforcement · batch |
| 25 | `ml/` | Model lifecycle · experiment tracking · data versioning |
| 26 | `agent/` | CLAUDE.md · AGENTS.md · context engineering · density rules |
| 27 | `html_generation/` | Offline-first output (STANDARDS.md) · theming · CSS (THEMING.md) · charts · controls (CHARTS.md) |

### Language — loaded per language

| # | Directory | Standard |
|---|---|---|
| 28 | `python/` | Style · typing · packaging · virtual envs · tooling |
| 29 | `rust/` | Ownership idioms · crate structure · error handling · unsafe |
| 30 | `go/` | Package layout · interfaces · error returns · concurrency |
| 31 | `typescript/` | Types · modules · async (STANDARDS.md) · build · lint (TOOLING.md) |
| 32 | `shell/` | Script structure · error handling (STANDARDS.md) · portability · security (HARDENING.md) |
| 33 | `sql/` | Query style · schema conventions · migration format |

---

## Cross-Reference Map

```text
architecture ← foundation for all standards
├── design · code_writing · directory ← structure the code itself
├── error_handling ← boundaries referenced by every tier
├── api ← database · web · local_mcp
├── testing ← cicd · code_review · expectation
├── security ← api · database · web · devops · dependencies
├── observability ← devops · data_pipeline · ml
├── git ← cicd · workflow · code_review
└── workflow ← references all standards as lifecycle phases
```

Authoritative version: [ROUTER.md](ROUTER.md) §4–§6.

---

## Git

- Branch off `main`. ✗ commit directly to `main` for multi-file changes.
- Commit after each standard completed or significantly updated.
- `python3 tools/validate.py` must pass before every commit.
- Push after commit.
- ✗ create PR unless user explicitly asks.
- Release: tag `vX.Y.Z` on `main` → CI publishes a GitHub release from `CHANGELOG.md`.
