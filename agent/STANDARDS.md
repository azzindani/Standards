# Agent Context Engineering Standards

Rules for writing CLAUDE.md, AGENTS.md, system prompts, and other
context files that guide AI coding agents. Defines how to structure,
compress, and maintain agent instruction files for maximum context
efficiency and behavioral accuracy.

---

## Table of Contents

1. [File Types](#1-file-types)
2. [Density Principles](#2-density-principles)
3. [High-Density Engineering](#3-high-density-engineering)
4. [Context Budget](#4-context-budget)
5. [File Structure](#5-file-structure)
6. [Role & Persona](#6-role--persona)
7. [Project Context](#7-project-context)
8. [Rules & Restrictions](#8-rules--restrictions)
9. [Investigation Protocol](#9-investigation-protocol)
10. [Writing Discipline](#10-writing-discipline)
11. [Anti-Patterns](#11-anti-patterns)
12. [Checklist](#12-checklist)

---

## 1. File Types

| File | Purpose | Scope |
|---|---|---|
| `CLAUDE.md` | Project-level agent instructions | Loaded automatically per project |
| `AGENTS.md` | Multi-agent coordination rules | Agent roles, handoff protocols |
| System prompt | Session-level behavioral rules | Loaded at conversation start |
| `.cursorrules` | Cursor IDE agent context | Editor-specific rules |
| `.github/copilot-instructions.md` | Copilot context | GitHub Copilot rules |

All files follow the same density and structure principles below.

---

## 2. Density Principles

### Caveman Writing

Maximum information per token. Zero meaning lost.

**Strip:**
- Articles: `a` · `an` · `the`
- Weak modals: `should` · `would` · `may` · `might`
- Scaffolding: `make sure to` · `always remember to` · `be careful to`
- Meta: `note that` · `keep in mind` · `it is important`
- Hedging: `generally` · `typically` · `usually` · `often`
- Obvious subjects and restatements

**Operators:**

| Operator | Meaning |
|---|---|
| `→` | Leads to, use instead, results in |
| `·` | Co-required, and, with |
| `\|` | Alternative, or |
| `✗` | Never, forbidden, do not |
| `;` | Except, unless |
| `!` | Critical, must |

**Structure over prose:**
- Comparisons → tables
- Condition + action → `X → Y`
- Workflow → `A → B → C`
- Related bullets → one merged line

**Never compress (load-bearing):**
- Negations (`never` · `not` · `no`) — stripping inverts meaning
- Hard thresholds and numbers
- Exception clauses
- Code blocks and technical names
- Ordered sequences

### Density Test

Read each sentence. If removing it changes zero agent behavior → delete it.
Every line must either constrain behavior or provide actionable context.

---

## 3. High-Density Engineering

Caveman writing (§2) removes filler. High-density engineering packs
more meaning into fewer tokens using vocabulary, notation, compression,
and prompt architecture techniques.

### Vocabulary Engineering

Define project-specific terms that replace long phrases. One defined
term replaces a sentence every time it's used afterward.

| Technique | Before (tokens wasted) | After (tokens saved) |
|---|---|---|
| Named concept | "functions that take data in and return data out without side effects" | "pure function" (defined once) |
| Acronym with definition | "Architecture Decision Record" repeated 12 times | "ADR" (defined once, used 12x) |
| Domain shorthand | "the module that handles CLI, API, MCP, file I/O" | "Tier 3" (defined in architecture) |
| Compound term | "validate input at the system boundary then trust internally" | "validation boundary" |

Rules:
- Define every custom term on first use — never assume agent knows project vocabulary
- Build a vocabulary section at file top if project has 5+ custom terms
- Reuse terms from referenced standards — `Tier 0–3` from architecture, not re-explained
- ✗ invent terms that collide with established technical meanings

### Notation Systems

Create rule encodings that pack boolean logic into scannable format.

**Constraint notation:**
```
fn: 1 required arg · rest defaulted · single return · verb-first name
```
Encodes 4 rules in 1 line. Equivalent prose = 4 sentences.

**Path notation:**
```
New Rust → rust/crates/ | rust/services/
Schemas → shared/schemas.rs
Config → shared/config/
Tests → tests/ (mirror source structure)
```
Encodes file placement rules as lookup table, not paragraphs.

**Dependency notation:**
```
shared → third-party only
kernel → shared · trace_io · inference_bridge
services/* → all internal crates
```
Encodes architecture boundaries in 3 lines. Equivalent prose = full paragraph per layer.

**Status notation:**
```
✗ unwrap() | expect() in production → use ?
✗ println!() → use tracing::{info,warn,error}!()
✗ .await holding std::sync::Mutex → deadlock
```
Each line = rule + reason in one scannable row.

### Compression Techniques

**Reference compression** — point to existing definitions, don't repeat:
```
Follow architecture/STANDARDS.md (all sections)
Override: line length 120 · max function params 4
```
Two lines replaces copying 500+ lines of architecture rules.

**Inheritance** — layer project context on shared standards:
```
Base: architecture/ · code_writing/ · testing/ · git/
Lang: python/
Domain: data_pipeline/ · cli/
Project-specific overrides below.
```
Three lines declare which standards apply. Agent loads them.

**Conditional compression** — encode branching rules as tables:
```
| Condition | Action |
| bug fix | read → trace → root-cause → fix → test |
| new feature | design → implement → test → document |
| refactor | test first → change → verify tests pass |
```
Three rows replace three paragraphs of workflow prose.

**Grouped constraints** — stack related rules vertically:
```
Every public function:
  typed return · doc comment · ≥1 test · in __all__
Every file:
  ≤400 lines · one concept · standard section order
```
Two groups, 8 rules, 4 lines total.

### Prompt Engineering Techniques

**Behavioral anchoring** — state identity/role first, rules follow:
```
Senior systems engineer. Rust · PostgreSQL · distributed systems.
All code production-grade. No shortcuts.
```
Anchors all subsequent behavior to this identity.

**Negative examples** — ✗ rules are more precise than positive rules:
```
✗ guess-and-check debugging → read first, understand, then fix
✗ "works on my machine" → test in CI environment
```
Agent avoids specific failure mode, not just "be careful."

**Pattern priming** — show the structure you want the agent to follow:
```
Commit format: type(scope): description
  feat(auth): add JWT refresh token rotation
  fix(db): prevent N+1 in user query
  refactor(api): extract validation middleware
```
Three examples prime the pattern. Agent generalizes.

**Constraint stacking** — layer multiple constraints in single rule:
```
Functions: ≤30 lines · ≤3 params · ≤3 nesting · single return type · verb-first name
```
Five constraints, one scannable line.

**Escalation triggers** — define when agent stops and asks:
```
🛑 before: schema change · public API removal · new service · force-push
```
Prevents costly autonomous mistakes.

### Layered Context Architecture

Structure context in layers. Each layer has different lifetime and scope.

```
Layer 0: Standards (shared, rarely changes)
  → architecture/STANDARDS.md, code_writing/STANDARDS.md, etc.
  → Referenced, not inlined. Agent loads as needed.

Layer 1: Project CLAUDE.md (project-specific, changes per project)
  → Tech stack, boundaries, path rules, restrictions
  → 100–200 lines. Core project identity.

Layer 2: Session context (ephemeral, changes per conversation)
  → Current task, recent changes, active branch
  → Injected by the agent runtime or user. Not in files.
```

Rules:
- ✗ inline Layer 0 content into Layer 1 — reference only
- Layer 1 states only what Layer 0 does not cover or what overrides Layer 0
- Layer 2 is conversation state, not file content
- Total loaded context (Layer 0 refs + Layer 1) should not exceed ~2000 lines
  to prevent context dilution in long sessions

### Density Measurement

| Metric | Target | How to measure |
|---|---|---|
| Rules per line | ≥ 0.5 | Count actionable rules ÷ total lines |
| Tokens per rule | ≤ 30 | Average tokens per actionable constraint |
| Filler ratio | ≤ 10% | Lines with zero behavioral impact ÷ total |
| Reference ratio | ≥ 30% | Rules via reference ÷ total rules (for Layer 1) |

---

## 4. Context Budget

### Size Targets

| File type | Target | Hard cap | Rationale |
|---|---|---|---|
| CLAUDE.md (small project) | 50–100 lines | 150 | Fits fully in context |
| CLAUDE.md (large project) | 100–200 lines | 300 | Retained across turns |
| AGENTS.md | 50–100 lines | 150 | Per-agent role definitions |
| System prompt | 20–50 lines | 100 | Loaded every turn |

### Context Rot Prevention

- Shorter files retain better across long conversations
- Front-load critical rules — agents weight earlier content higher
- Group related rules — scattered rules get lost
- ✗ duplicate information already in code (types, schemas) — reference it
- Review quarterly: delete rules the agent consistently follows without prompting

---

## 5. File Structure

Every agent context file follows this order:

| Order | Section | Required |
|---|---|---|
| 1 | Role & persona (1–2 lines) | For AGENTS.md |
| 2 | Core principles (behavioral rules) | Yes |
| 3 | Project context (structure, tech stack) | Yes |
| 4 | Architecture boundaries (what depends on what) | If applicable |
| 5 | Code quality rules (style, patterns) | Yes |
| 6 | Restrictions (✗ never do) | Yes |
| 7 | Workflow rules (investigation, testing) | If applicable |
| 8 | File/path conventions | If applicable |

### Ordering Principle

Most critical rules first. Agent context may be truncated in long
sessions — rules at the top survive longest. Structure:

```
Critical behavioral rules     ← always retained
Project structure / tech      ← usually retained
Detailed conventions          ← may be compressed
Nice-to-have preferences      ← first to be lost
```

---

## 6. Role & Persona

Define in 1–3 lines. Include: specialization, key technologies,
primary task domain.

Format: `[Role] specializing in [technologies] for [domain].`

Rules:
- One role per agent file. ✗ conflicting personas.
- Role constrains scope — agent declines out-of-scope requests
- Technology list = what the agent reaches for first
- ✗ personality traits · ✗ tone instructions · ✗ "be helpful" — agents already are

---

## 7. Project Context

### What to Include

| Include | Format | Example |
|---|---|---|
| Directory structure | Tree diagram | `src/` layout, key paths |
| Tech stack | Flat list | `Rust: Tokio · Axum · sqlx` |
| Architecture boundaries | Dependency table | `shared → third-party only` |
| Key file paths | Path rules | `Schemas → shared/schemas.rs` |
| Build / run commands | Command list | `cargo build`, `uv run pytest` |

### What to Exclude

- Information derivable from code (function signatures, type definitions)
- History or changelog (use git)
- Tutorials or explanations of technologies
- Anything the agent can discover by reading files

### Staleness Rule

Every fact in the context file must be hard to derive from code alone.
If the agent can `grep` or `read` to find it → remove it from context.
Context files document constraints and decisions, not discoverable facts.

---

## 8. Rules & Restrictions

### Writing Rules

- One rule per line. Scannable, not paragraph-form.
- Positive rules first (`do X`), then restrictions (`✗ Y`)
- Each rule testable: can you look at code and verify compliance?
- ✗ vague rules: `write clean code` — unverifiable
- ✗ redundant rules: if a linter enforces it, don't write it

### Restriction Format

Use `✗` prefix for forbidden actions. Group by severity:

```
! Critical (data loss, security):
✗ hardcoded secrets — env vars only
✗ force-push to main

Operational:
✗ println/print in production — use structured logging
✗ unwrap() in production — use ? operator

Style:
✗ wildcard imports
✗ abbreviated variable names ; except i, k, v in short loops
```

### Stop-and-Ask Rules

Define actions that require human confirmation before proceeding:

```
🛑 Stop and ask before:
- Modifying migrations or schema
- Removing public API functions
- Adding new top-level modules
- Major dependency upgrades
```

---

## 9. Investigation Protocol

Guide the agent's problem-solving approach. Prevents surface-level fixes.

Recommended protocol:

```
1. Read — all relevant source files, logs, error messages
2. Trace — follow data flow end-to-end across boundaries
3. Cross-check — shared types, schemas, config for drift
4. Root cause — fix actual cause, ✗ patch downstream symptoms
5. Verify — confirm fix doesn't exist elsewhere, grep patterns
```

Rules:
- Protocol applies before any code change for bug fixes
- ✗ guess-and-check — read first, understand, then fix
- ✗ shotgun debugging — changing multiple things hoping one works

---

## 10. Writing Discipline

### Incremental Writing

Agent context files themselves follow incremental write rules:

- ✗ write full file in single tool call — breaks on timeout
- Write header + first sections → edit/append remaining
- Each write call ≤ 150 lines of new content
- Verify after each write before continuing

### Maintenance

- Update context file when project conventions change
- Remove rules that become enforced by tooling (linters, CI)
- ✗ let context file drift from actual project practices
- Review when onboarding new team member — if they need more context, file is incomplete

### Composability

When a project uses standards from a shared library (like this repo):

- CLAUDE.md references standards: `Follow architecture/STANDARDS.md`
- ✗ duplicate standard rules into CLAUDE.md — reference only
- Project-specific overrides stated explicitly: `Override: line length 120 (not 100)`
- Standards compose: list which standards apply to this project

---

## 11. Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Novel-length CLAUDE.md | Context rot, rules lost in noise | Compress to < 200 lines |
| Restating language docs | Wastes tokens on known information | Reference, don't restate |
| Personality instructions | "Be friendly" wastes tokens, no effect | Delete — focus on constraints |
| Vague rules | "Write good code" — unverifiable | Make specific and testable |
| Stale rules | Rule about removed feature | Review quarterly, delete stale |
| Duplicate with linter | Rule that CI already enforces | Let tooling handle it |
| Tutorial content | Explaining how async works | Agent already knows — state the rule only |
| Scattered restrictions | ✗ rules mixed into prose paragraphs | Group all ✗ rules together |
| Missing path conventions | Agent creates files in wrong locations | Add explicit path rules |
| No investigation protocol | Agent patches symptoms | Add read → trace → root-cause protocol |

---

## 12. Checklist

### New CLAUDE.md

- [ ] Role defined in ≤ 3 lines (if needed)
- [ ] Core principles stated (behavioral rules)
- [ ] Project structure documented (tree or key paths)
- [ ] Tech stack listed
- [ ] Architecture boundaries defined (dependency table)
- [ ] Code quality rules stated (only non-obvious ones)
- [ ] Restrictions grouped with ✗ prefix
- [ ] Stop-and-ask actions defined
- [ ] Total file ≤ 200 lines
- [ ] Every line changes agent behavior — no filler

### Review Existing CLAUDE.md

- [ ] Remove rules now enforced by CI/linter
- [ ] Remove discoverable facts (agent can read code to find them)
- [ ] Remove stale rules referencing deleted features
- [ ] Verify restrictions still apply
- [ ] Check density — can any sentence be compressed further?
- [ ] Front-loaded — most critical rules at top?
