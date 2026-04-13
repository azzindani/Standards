# Agent Context Engineering Standards

Rules for writing CLAUDE.md, AGENTS.md, system prompts, and other
context files that guide AI coding agents. Defines how to structure,
compress, and maintain agent instruction files for maximum context
efficiency and behavioral accuracy.

---

## Table of Contents

1. [File Types](#1-file-types)
2. [Density Principles](#2-density-principles)
3. [Context Budget](#3-context-budget)
4. [File Structure](#4-file-structure)
5. [Role & Persona](#5-role--persona)
6. [Project Context](#6-project-context)
7. [Rules & Restrictions](#7-rules--restrictions)
8. [Investigation Protocol](#8-investigation-protocol)
9. [Writing Discipline](#9-writing-discipline)
10. [Anti-Patterns](#10-anti-patterns)
11. [Checklist](#11-checklist)

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

## 3. Context Budget

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

## 4. File Structure

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

## 5. Role & Persona

Define in 1–3 lines. Include: specialization, key technologies,
primary task domain.

Format: `[Role] specializing in [technologies] for [domain].`

Rules:
- One role per agent file. ✗ conflicting personas.
- Role constrains scope — agent declines out-of-scope requests
- Technology list = what the agent reaches for first
- ✗ personality traits · ✗ tone instructions · ✗ "be helpful" — agents already are

---

## 6. Project Context

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

## 7. Rules & Restrictions

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

## 8. Investigation Protocol

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

## 9. Writing Discipline

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

## 10. Anti-Patterns

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

## 11. Checklist

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
