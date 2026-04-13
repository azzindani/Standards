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

Central standards library for all projects. Each standard = one directory + one `STANDARDS.md`. Standards are composable — projects load multiple standards by combining relevant files. All standards language-agnostic ; language-specific standards in dedicated directories.

## Writing Rules

- Target 400–500 lines per standard. Hard cap 800.
- Zero code examples — pure rules, patterns, tables. Language-specific examples → language-specific standards only.
- Every sentence = rule | clarification of rule. ✗ motivation paragraphs · ✗ tutorials · ✗ "why this matters"
- Tables over prose. One-liner rules over paragraphs.
- Cross-reference other standards by relative path: `See architecture/STANDARDS.md §4`
- Every standard has: TOC · numbered sections · checklist at end · scale matrix if applicable
- Brainstorm with user before writing. Explore prior art, extract principles from proven systems, identify what belongs vs what belongs in other standards.
- Write incrementally — section by section, not full file in one shot. ✗ write long content in single tool call — breaks on timeout. Write header + first sections → edit/append remaining sections in subsequent calls.

## Standards Catalog

### General (language-agnostic)

| # | Directory | Standard | Status |
|---|---|---|---|
| 1 | `architecture/` | System structure · tier model · 29 core principles | Done |
| 2 | `design/` | Design patterns · module design · abstraction rules | Planned |
| 3 | `directory/` | Project layout · file organization · naming | Done |
| 4 | `code_writing/` | Clean code · readability · function style · naming | Planned |
| 5 | `testing/` | Test pyramid · contract tests · coverage strategy | Done |
| 6 | `error_handling/` | Error types · boundaries · recovery · reporting | Planned |
| 7 | `observability/` | Structured logging · receipts · metrics · health | Done |
| 8 | `security/` | Validation boundary · secrets · access control · input | Done |
| 9 | `api/` | API design · protocols · contracts · versioning · serialization | Done |
| 10 | `database/` | Schema design · migrations · queries · transactions | Done |
| 11 | `configuration/` | Cascade · environment · secrets · feature flags | Planned |
| 12 | `dependencies/` | Versioning · isolation · wrappers · lock files | Done |
| 13 | `git/` | Branching · commits · tags · workflows · history | Done |
| 14 | `cicd/` | Build · test · lint · deploy · release stages | Done |
| 15 | `documentation/` | Code docs · API docs · decision records · runbooks | Planned |
| 16 | `performance/` | Profiling · budgets · optimization · caching | Planned |
| 17 | `devops/` | Infrastructure · containers · deployment · monitoring | Planned |
| 18 | `code_review/` | Review criteria · approval flow · feedback style | Planned |
| 19 | `workflow/` | Idea → PoC → production lifecycle · task management | Planned |

### Language-Specific

| # | Directory | Standard | Status |
|---|---|---|---|
| 20 | `python/` | Style · typing · packaging · virtual envs · tooling | Planned |
| 21 | `rust/` | Ownership idioms · crate structure · error handling · unsafe | Planned |
| 22 | `go/` | Package layout · interfaces · error returns · concurrency | Planned |
| 23 | `typescript/` | Types · modules · async patterns · build config | Planned |
| 24 | `shell/` | Script structure · error handling · portability | Planned |
| 25 | `sql/` | Query style · schema conventions · migration format | Planned |

### Domain-Specific

| # | Directory | Standard | Status |
|---|---|---|---|
| 26 | `local_mcp/` | MCP server development · tool design · engine/server split | Done |
| 27 | `html_generation/` | Charts · dashboards · theming · offline-first output | Done |
| 28 | `data_pipeline/` | ETL · data validation · schema enforcement · batch | Planned |
| 29 | `cli/` | Argument parsing · output format · exit codes · help | Planned |
| 30 | `web/` | Routing · middleware · state · auth · frontend/backend | Planned |
| 31 | `ml/` | Model lifecycle · experiment tracking · data versioning | Planned |

## Cross-Reference Map

```
architecture ← foundation for all standards
├── design ← code_writing · testing · error_handling
├── directory ← all language-specific · all domain-specific
├── api ← database · web · local_mcp
├── testing ← cicd · code_review
├── security ← api · database · web · devops
├── git ← cicd · workflow · code_review
└── workflow ← references all standards as lifecycle phases
```

## File Structure

```
Standards/
├── CLAUDE.md                    ← this file
├── README.md
├── architecture/STANDARDS.md    ← done
├── design/STANDARDS.md
├── directory/STANDARDS.md
├── code_writing/STANDARDS.md
├── testing/STANDARDS.md
├── error_handling/STANDARDS.md
├── observability/STANDARDS.md
├── security/STANDARDS.md
├── api/STANDARDS.md
├── database/STANDARDS.md
├── configuration/STANDARDS.md
├── dependencies/STANDARDS.md
├── git/STANDARDS.md
├── cicd/STANDARDS.md
├── documentation/STANDARDS.md
├── performance/STANDARDS.md
├── devops/STANDARDS.md
├── code_review/STANDARDS.md
├── workflow/STANDARDS.md
├── python/STANDARDS.md
├── rust/STANDARDS.md
├── go/STANDARDS.md
├── typescript/STANDARDS.md
├── shell/STANDARDS.md
├── sql/STANDARDS.md
├── local_mcp/STANDARDS.md       ← done
├── html_generation/STANDARDS.md ← done
├── data_pipeline/STANDARDS.md
├── cli/STANDARDS.md
├── web/STANDARDS.md
└── ml/STANDARDS.md
```

## Git

- Branch: `claude/project-coding-standards-ByG4r`
- Commit after each standard completed or significantly updated
- Push after commit
- ✗ create PR unless user explicitly asks
