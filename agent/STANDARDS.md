# Agent Context Standards

> Rules for authoring the context files that steer AI coding agents — CLAUDE.md, AGENTS.md, and system prompts — for maximum behavioral accuracy at minimum token cost.

**ID** `agent` · **Tier** Domain · **Version** 1.0
**Owns** agent context file types · caveman density rules · high-density engineering · token budget · context file structure · role/persona · project-context selection · restriction format · investigation protocol · context maintenance
**Defers to** prose docs · API docs · ADRs · runbooks → [documentation](../documentation/STANDARDS.md) · repo file structure + header schema → [TEMPLATE.md](../TEMPLATE.md) · catalog + routing → [ROUTER.md](../ROUTER.md) · layer model + dependency direction → [architecture](../architecture/STANDARDS.md) · comparator model + quality dimensions → [expectation](../expectation/STANDARDS.md) · MCP tool serving → [local_mcp](../local_mcp/STANDARDS.md)
**Load with** [documentation](../documentation/STANDARDS.md) · [expectation](../expectation/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [File Types](#2-file-types)
3. [Density Rules](#3-density-rules)
4. [High-Density Engineering](#4-high-density-engineering)
5. [Layered Context](#5-layered-context)
6. [Token Budget](#6-token-budget)
7. [File Structure](#7-file-structure)
8. [Role and Persona](#8-role-and-persona)
9. [Project Context](#9-project-context)
10. [Rules and Restrictions](#10-rules-and-restrictions)
11. [Investigation Protocol](#11-investigation-protocol)
12. [Maintenance](#12-maintenance)
13. [Anti-Patterns](#13-anti-patterns)
14. [Checklist](#14-checklist)

---

## 1. Principles

A context file is a **behavioral instrument**, not documentation. Every line either constrains agent behavior or supplies context the agent cannot derive from the code.

| Principle | Rule |
|---|---|
| Maximum information per token | Density is the objective — an agent weights a dense file higher and loses less of it |
| Every line earns its place | Remove a line → if agent behavior is unchanged, the line was noise. Delete it |
| Reference, ✗ restate | Point at the owning standard; ✗ copy its rules into the context file (§5) |
| Constrain, ✗ describe | State the rule the agent must follow, ✗ explain the technology it already knows |
| Front-load the critical | Long sessions truncate context — top-of-file rules survive longest (§7) |
| Testable rules only | Every rule is verifiable against code. ✗ "write clean code" |

This standard governs agent **instruction** files. Human-facing prose, API docs, ADRs, and runbooks are owned by [documentation](../documentation/STANDARDS.md) — ✗ restate its rules here.

---

## 2. File Types

| File | Purpose | Scope |
|---|---|---|
| `CLAUDE.md` | Project-level agent instructions | Loaded automatically per project |
| `AGENTS.md` | Multi-agent coordination | Agent roles · handoff protocols |
| System prompt | Session behavioral rules | Loaded at conversation start |
| `.cursorrules` | Cursor IDE agent context | Editor-specific |
| `.github/copilot-instructions.md` | Copilot context | Copilot-specific |

All follow the same density (§3) and structure (§7) rules.

---

## 3. Density Rules

### Caveman writing

Maximum information per token, zero meaning lost.

Strip: articles (`a` · `an` · `the`) · weak modals (`should` · `would` · `may` · `might`) · scaffolding (`make sure to` · `always remember to` · `be careful to`) · meta (`note that` · `keep in mind` · `it is important`) · hedging (`generally` · `typically` · `usually` · `often`) · obvious subjects · restatements.

| Operator | Meaning |
|---|---|
| `→` | Leads to · use instead · results in |
| `·` | Co-required · and · with |
| `\|` | Alternative · or |
| `✗` | Never · forbidden · do not |
| `;` | Except · unless |
| `!` | Critical · must |

Structure over prose: comparisons → tables · condition + action → `X → Y` · workflow → `A → B → C` · related bullets → one merged line.

### ✗ compress — load-bearing

! Compressing these inverts or breaks the rule:

- Negations (`never` · `not` · `no`) — stripping the negation reverses the instruction.
- Hard thresholds and numbers.
- Exception clauses.
- Technical names and code identifiers.
- Ordered sequences.

### Density test

Read each line. If deleting it changes zero agent behavior → delete it. Every surviving line constrains behavior or supplies non-derivable context.

---

## 4. High-Density Engineering

Caveman writing (§3) removes filler. High-density engineering packs more meaning per token through vocabulary, notation, and compression.

### Vocabulary engineering

One defined term replaces a phrase on every later use.

| Technique | Before | After |
|---|---|---|
| Named concept | "functions that take data in and return data out with no side effects" | "pure function" (defined once) |
| Acronym | "Architecture Decision Record" ×12 | "ADR" (defined once, used 12×) |
| Domain shorthand | "the module handling CLI, API, MCP, file I/O" | "Tier 3" (defined in architecture) |
| Compound term | "validate input at the boundary then trust it internally" | "validation boundary" |

Rules: define every custom term on first use · build a vocabulary block at the top when a project has ≥ 5 custom terms · reuse terms from referenced standards rather than re-explaining · ✗ invent terms that collide with established technical meanings.

### Notation systems

Pack boolean logic into a scannable line instead of prose. Four proven encodings:

| Notation | Encodes | Replaces |
|---|---|---|
| Constraint line | `fn: 1 required arg · rest defaulted · single return · verb-first name` | Four sentences of function rules |
| Path lookup | `New Rust → rust/crates/` · `Schemas → shared/schemas.rs` · `Tests → tests/ (mirror source)` | A paragraph of file-placement rules |
| Dependency arrows | `shared → third-party only` · `kernel → shared · trace_io` · `services/* → all internal` | A paragraph per architecture layer |
| Status line | `✗ unwrap()/expect() in prod → use ?` · `✗ println!() → use tracing::…` | Rule + reason per scannable row |

### Compression techniques

| Technique | Mechanism |
|---|---|
| Reference compression | Point at an existing definition: `Follow architecture/STANDARDS.md` + `Override: line length 120 · max params 4`. Two lines replace 500 |
| Inheritance | Declare which standards apply as a stack: `Base: architecture · testing · git` / `Lang: python` / `Domain: data_pipeline · cli`. Three lines, agent loads them |
| Conditional compression | Branching rules as a table: `bug fix → read → trace → root-cause → fix → test`; `new feature → design → implement → test → document` |
| Grouped constraints | Stack related rules under one subject: "Every public function: typed return · doc comment · ≥1 test." Eight rules, four lines |

### Prompt techniques

| Technique | Rule |
|---|---|
| Behavioral anchoring | State identity first; rules follow and inherit it: "Senior systems engineer. Rust · PostgreSQL. All code production-grade" |
| Negative examples | A `✗` rule is more precise than a positive one: `✗ guess-and-check debugging → read first` beats "debug carefully" |
| Pattern priming | Show 2–3 examples of the desired form (commit format, naming); the agent generalizes |
| Constraint stacking | Layer constraints in one line: `Functions: ≤30 lines · ≤3 params · ≤3 nesting · verb-first name` |
| Escalation triggers | Name where the agent stops and asks: `🛑 before: schema change · public API removal · force-push` |

### Density measurement

| Metric | Target |
|---|---|
| Rules per line | ≥ 0.5 |
| Tokens per rule | ≤ 30 |
| Filler ratio (zero-behavior lines) | ≤ 10% |
| Reference ratio (rules via reference, Layer 1) | ≥ 30% |

---

## 5. Layered Context

Structure context in layers by lifetime and scope. ✗ collapse the layers into one file.

| Layer | Content | Lifetime | Placement |
|---|---|---|---|
| 0 — Standards | architecture · code_writing · testing · etc. | Rarely changes | Referenced, ✗ inlined — agent loads as needed |
| 1 — Project CLAUDE.md | Tech stack · boundaries · path rules · restrictions | Per project | 100–200 lines |
| 2 — Session | Current task · recent changes · active branch | Per conversation | Injected by runtime or user, ✗ in files |

Rules:

- ✗ inline Layer 0 content into Layer 1 — reference only. Duplicated standard rules drift out of sync.
- Layer 1 states only what Layer 0 does not cover, or what it deliberately overrides.
- Layer 2 is conversation state, never file content.
- Total loaded context (Layer 0 references + Layer 1) ≤ ~2000 lines — beyond that, context dilutes in long sessions.

---

## 6. Token Budget

| File | Target | Hard cap |
|---|---|---|
| CLAUDE.md, small project | 50–100 lines | 150 |
| CLAUDE.md, large project | 100–200 lines | 300 |
| AGENTS.md | 50–100 lines | 150 |
| System prompt | 20–50 lines | 100 |

Context-rot prevention:

- Shorter files retain better across long conversations.
- Front-load critical rules — the agent weights earlier content higher.
- Group related rules — scattered rules get lost.
- ✗ duplicate information already in code (types, schemas) — reference it.
- Review quarterly: delete rules the agent already follows without prompting.

---

## 7. File Structure

| Order | Section | Required |
|---|---|---|
| 1 | Role / persona (1–2 lines) | AGENTS.md |
| 2 | Core principles (behavioral rules) | Yes |
| 3 | Project context (structure, stack) | Yes |
| 4 | Architecture boundaries (dependency table) | If applicable |
| 5 | Code quality rules (only non-obvious) | Yes |
| 6 | Restrictions (`✗ never`) | Yes |
| 7 | Workflow (investigation, testing) | If applicable |
| 8 | File/path conventions | If applicable |

Ordering principle: most critical first. Long sessions truncate context, so the top survives longest. The gradient: critical behavioral rules (always retained) → project structure and stack (usually retained) → detailed conventions (may be compressed) → nice-to-have preferences (first lost).

---

## 8. Role and Persona

Define in 1–3 lines: specialization · key technologies · primary task domain. Form: `[Role] specializing in [technologies] for [domain]`.

| Rule | Detail |
|---|---|
| One role per file | ✗ conflicting personas |
| Role constrains scope | The agent declines out-of-scope requests |
| Tech list is the reach-for-first set | What the agent chooses by default |
| ✗ personality | ✗ tone instructions · ✗ "be helpful" — agents already are; these waste tokens with no behavioral effect |

---

## 9. Project Context

| Include | Format |
|---|---|
| Directory structure | Tree or key paths |
| Tech stack | Flat list — `Rust: Tokio · Axum · sqlx` |
| Architecture boundaries | Dependency table — `shared → third-party only` |
| Key file paths | Path rules — `Schemas → shared/schemas.rs` |
| Build / run commands | Command list |

Exclude: anything derivable from code (function signatures, type definitions) · history or changelog (git owns it) · technology tutorials · anything the agent discovers by reading a file.

Staleness rule: every fact must be hard to derive from code alone. If the agent can `grep` or read to find it → remove it. Context files record constraints and decisions, ✗ discoverable facts.

---

## 10. Rules and Restrictions

| Rule | Detail |
|---|---|
| One rule per line | Scannable, ✗ paragraph-form |
| Positive before negative | State `do X`, then `✗ Y` |
| Testable | Verifiable against code — ✗ "write clean code" |
| ✗ redundant with tooling | If a linter enforces it, ✗ write it |

Restrictions use the `✗` prefix, grouped by severity — critical (data loss, security) first, then operational, then style. Example severity ladder: critical → `✗ hardcoded secrets — env vars only` · `✗ force-push to main`; operational → `✗ print in production — structured logging` · `✗ unwrap() in production — use ?`; style → `✗ wildcard imports` · `✗ abbreviated names ; i, k, v in short loops`.

Stop-and-ask: name the actions requiring human confirmation before proceeding — modifying migrations or schema · removing public API functions · adding a top-level module · a major dependency upgrade · force-push. Mark them `🛑`.

---

## 11. Investigation Protocol

Guides problem-solving; prevents surface fixes. Recommended sequence:

read (all relevant source, logs, errors) → trace (data flow end-to-end across boundaries) → cross-check (shared types, schemas, config for drift) → root cause (fix the cause, ✗ patch the downstream symptom) → verify (confirm the fix is not already elsewhere; grep the pattern).

| Rule | Detail |
|---|---|
| Applies before any bug-fix change | Read and understand first |
| ✗ guess-and-check | Read → understand → then change |
| ✗ shotgun debugging | Changing many things hoping one works |

---

## 12. Maintenance

Context files themselves follow incremental-write discipline: ✗ write the full file in one call (breaks on timeout) · header + first sections, then edit/append · each write ≤ 150 lines · verify after each write.

| Rule | Detail |
|---|---|
| Update on convention change | Keep the file matching actual project practice |
| Prune tooling-enforced rules | Once a linter or CI enforces a rule, delete it from the file |
| ✗ drift | A file describing an out-of-date practice actively misleads the agent |
| Onboarding test | If a new team member needs more context than the file gives, the file is incomplete |

Composability with a shared standards library:

- Reference standards: `Follow architecture/STANDARDS.md`. ✗ duplicate their rules into CLAUDE.md.
- State project overrides explicitly: `Override: line length 120 (not 100)`.
- List which standards apply; they compose.

---

## 13. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Novel-length CLAUDE.md | Context rot; rules lost in noise | Compress to < 200 lines (§6) |
| Restating language docs | Tokens spent on known information | Reference, ✗ restate (§1) |
| Personality instructions | "Be friendly" — no behavioral effect | Delete; state constraints (§8) |
| Vague rules | "Write good code" is unverifiable | Make specific and testable (§10) |
| Stale rules | Rule about a removed feature | Review quarterly, delete (§12) |
| Duplicate with linter | CI already enforces it | Let tooling own it (§10) |
| Tutorial content | Explaining how async works | The agent knows — state only the rule (§1) |
| Scattered restrictions | `✗` rules buried in prose | Group all `✗` rules together (§10) |
| Missing path conventions | Agent creates files in the wrong place | Add explicit path rules (§9) |
| No investigation protocol | Agent patches symptoms | Add read → trace → root-cause (§11) |
| Inlined Layer 0 standards | Duplicated rules drift out of sync | Reference Layer 0 (§5) |

---

## 14. Checklist

- [ ] Every line constrains behavior or supplies non-derivable context
- [ ] Density rules applied — no articles, weak modals, scaffolding, or hedging
- [ ] Negations, thresholds, exceptions, technical names, and sequences left uncompressed
- [ ] Custom terms defined on first use; vocabulary block present when ≥ 5 terms
- [ ] Standards referenced, never restated (Layer 0 not inlined)
- [ ] Project overrides of a standard stated explicitly
- [ ] Role defined in ≤ 3 lines when a role is needed; no personality instructions
- [ ] Core behavioral principles stated
- [ ] Project structure and tech stack documented
- [ ] Architecture boundaries given as a dependency table where applicable
- [ ] Only non-obvious, testable code-quality rules included
- [ ] No rule duplicated with a linter or CI check
- [ ] Restrictions grouped under `✗`, ordered by severity
- [ ] Stop-and-ask actions marked with `🛑`
- [ ] Investigation protocol present (read → trace → root-cause → verify)
- [ ] No discoverable facts the agent could grep or read to find
- [ ] Critical rules front-loaded; nice-to-haves last
- [ ] File within its token budget for its type
- [ ] Human-facing documentation rules deferred to documentation/, not restated
- [ ] File reviewed against actual current project practice
