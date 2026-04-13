# Code Writing Standards

Rules for writing clean, readable, maintainable code across all languages.
This standard governs how individual lines, functions, and files are written —
not how systems are structured (→ `architecture/STANDARDS.md`) or how
patterns are applied (→ `design/STANDARDS.md`).

---

## Table of Contents

1. [Naming](#1-naming)
2. [Functions](#2-functions)
3. [Variables & Constants](#3-variables--constants)
4. [Conditionals & Control Flow](#4-conditionals--control-flow)
5. [Loops & Iteration](#5-loops--iteration)
6. [Comments & Self-Documentation](#6-comments--self-documentation)
7. [Complexity Management](#7-complexity-management)
8. [Abstraction & Reuse](#8-abstraction--reuse)
9. [File Organization](#9-file-organization)
10. [Readability](#10-readability)
11. [Anti-Patterns](#11-anti-patterns)
12. [Code Writing Checklist](#12-code-writing-checklist)

---

## 1. Naming

### General Rules

| Rule | Description |
|---|---|
| Reveal intent | Name describes what it holds or does — reader never guesses |
| Searchable | Unique enough to find with text search across codebase |
| Pronounceable | Can be spoken in conversation without spelling out |
| No abbreviations | Full words ; except universally known: `id`, `url`, `db`, `config`, `ctx`, `err`, `msg`, `args`, `opts` |
| No type encoding | ✗ `strName` · ✗ `iCount` · ✗ `lstItems` — let the type system handle types |
| No noise words | ✗ `data` · ✗ `info` · ✗ `temp` · ✗ `misc` · ✗ `utils` (unless genuinely a utility module at Tier 0) |
| Consistent vocabulary | One word per concept across entire project: pick `fetch` or `get` or `retrieve` — not all three |

### Naming by Kind

| Kind | Convention | Examples |
|---|---|---|
| Functions/methods | Verb-first, describes action | `compute_stats` · `validate_schema` · `parse_header` |
| Booleans | Question form, reads as true/false | `is_valid` · `has_header` · `can_retry` |
| Collections | Plural noun | `users` · `error_messages` · `file_paths` |
| Single items | Singular noun | `user` · `error_message` · `file_path` |
| Constants | Describes the fixed value | `MAX_RETRY_COUNT` · `DEFAULT_TIMEOUT_MS` |
| Types/classes | Noun, describes the entity | `AnalysisResult` · `ConnectionPool` · `ParseError` |
| Callbacks/handlers | `on_` prefix or `_handler` suffix | `on_complete` · `error_handler` |
| Factory functions | `create_` or `build_` prefix | `create_connection` · `build_report` |
| Conversion functions | `to_` or `from_` prefix | `to_json` · `from_csv` |
| Predicates | `is_` · `has_` · `can_` prefix | `is_empty` · `has_permission` |

### Scope-Length Rule

| Scope | Name length |
|---|---|
| Loop counter (3-line loop) | Short ok: `i`, `k`, `v` |
| Local variable (single function) | Medium: `user_count`, `raw_text` |
| Module-level / exported | Descriptive: `max_concurrent_workers`, `default_output_format` |

Short scope → short name. Long scope → long descriptive name.

---

## 2. Functions

Architecture defines function contracts (→ `architecture/STANDARDS.md §4`).
This section governs how the function body is written.

### Size & Focus

| Rule | Threshold |
|---|---|
| Single responsibility | One function does one thing. If you use "and" to describe it, split it. |
| Line count | Target ≤ 30 lines. Investigate at 50. Mandatory split at 80. |
| Nesting depth | Maximum 3 levels. If deeper → extract inner block to named function. |
| Parameter count | Maximum 3 parameters. More → group into a structured type. |
| Return points | Prefer early returns over deep nesting. Multiple returns ok. |

### Guard Clauses

Handle invalid/edge cases first, return early. Main logic stays at
the lowest nesting level. ✗ wrapping entire function body in an
if-block for a precondition.

Pattern: validate → reject early → proceed with clean logic.

### Function Ordering Within File

| Order | Category | Rationale |
|---|---|---|
| 1 | Public API functions | Reader sees the contract first |
| 2 | High-level private functions | Called by public API |
| 3 | Low-level helper functions | Implementation details last |

Reader follows top-down: entry point → helpers → utilities.
Callers appear above callees.

### Pure vs Impure

Mark or separate pure functions (no side effects, deterministic) from
impure functions (I/O, state mutation, randomness). Pure functions
are easier to test, reason about, compose, and parallelize.

### Single Level of Abstraction

Each function operates at one abstraction level. ✗ mixing high-level
orchestration with low-level string parsing in the same function body.
If a line is at a different abstraction level than its neighbors →
extract it to a named function.

---

## 3. Variables & Constants

### Declaration Rules

| Rule | Description |
|---|---|
| Declare close to use | Variable declared immediately before first use, not at top of scope |
| Minimize scope | Smallest possible scope. ✗ function-level variable when block-level suffices |
| Immutable by default | Declare as constant/readonly/final. Make mutable only when mutation required. |
| One purpose | Each variable holds one concept for its entire lifetime. ✗ reusing variable for different meaning. |
| Meaningful initialization | Every variable initialized at declaration. ✗ declare now, assign later. |

### Constants

| Rule | Description |
|---|---|
| ✗ magic numbers | Every literal number (except 0, 1, -1) gets a named constant |
| ✗ magic strings | Every literal string used for comparison or configuration → named constant |
| Constants at module top | All constants grouped at file top, after imports |
| Units in name | `TIMEOUT_MS` · `MAX_SIZE_BYTES` · `RETRY_DELAY_SECONDS` — never ambiguous units |

### Temporary Variables

Use explanatory variables to break complex expressions into named steps.
A well-named temporary variable is documentation that the compiler checks.

✗ `if (a.x > b.x && a.y < b.y && c.valid())` — opaque
→ Extract: `is_in_bounds = a.x > b.x and a.y < b.y` · `is_ready = c.valid()`

---

## 4. Conditionals & Control Flow

### Guard Clause Pattern

Handle failure/edge cases first with early returns. Main path at
lowest indentation. Every function reads as: reject bad input →
do the work → return result.

### Boolean Expression Rules

| Rule | Description |
|---|---|
| Positive conditions | `if is_valid` over `if not is_invalid` — avoid double negatives |
| Extract complex conditions | Named boolean variable for any condition with 2+ operators |
| No boolean parameters | ✗ `process(data, True)` — unreadable at call site. Use named arguments, enums, or separate functions |
| Short-circuit intentionally | Put cheap/likely checks first in boolean chains |

### Branching Rules

| Rule | Description |
|---|---|
| ✗ nested ternary | One level of ternary/inline-if is max. Two levels → use if/else block. |
| Exhaustive matching | When branching on type/enum, handle every variant. ✗ silent default fallthrough. |
| ✗ else after return | If the if-branch returns, the else block is unnecessary — remove it. |
| ✗ empty branches | No `if (x) {} else { doThing() }` — invert the condition. |
| Fail on unknown | Default/else case in switches on known types → error, not silent pass |

### Null/None Handling

Follows architecture principle #15 (explicit absence). At the code
level: never compare against null directly in core logic. Use the
language's pattern matching, optional chaining, or guard clauses to
handle absence structurally.

---

## 5. Loops & Iteration

### Preference Order

| Priority | Approach | When |
|---|---|---|
| 1 | Declarative (map, filter, reduce) | Transforming collections — no index needed |
| 2 | For-each / for-in | Iterating with element access, no index needed |
| 3 | Indexed for loop | Index required for logic (not just access) |
| 4 | While loop | Termination condition not count-based |
| 5 | Infinite loop + break | Event loops, retry loops with complex exit |

### Rules

| Rule | Description |
|---|---|
| Single responsibility | Loop body does one thing. Complex body → extract to function. |
| ✗ mutate collection during iteration | Never add/remove items from collection being iterated |
| Bound every loop | Every loop has a known termination. While loops → maximum iteration guard. |
| ✗ deep nesting | Nested loop body > 5 lines → extract inner loop to function |
| Accumulator pattern | Build result in a local accumulator, return at end. ✗ modifying external state in loop body. |
| Early exit | Use break/continue to reduce nesting. Skip irrelevant items with `continue` at top. |

---

## 6. Comments & Self-Documentation

### Comment Hierarchy

| Priority | Approach | Description |
|---|---|---|
| 1 | Make code obvious | Rename, restructure, extract — eliminate need for comment |
| 2 | Type annotations | Types document the contract — compiler-verified |
| 3 | Function/method docs | Public API gets doc comments: what it does, what it returns |
| 4 | Inline comments | Explain why, not what. Only when code cannot express the reason. |

### When to Comment

| Comment | When |
|---|---|
| **Why** comment | Non-obvious business reason, workaround, constraint |
| **Warning** comment | Performance trap, subtle bug potential, non-obvious side effect |
| **TODO** comment | Known incomplete work — include ticket/issue reference |
| **Legal** comment | License, copyright — only when required |

### ✗ Never Comment

| Anti-pattern | Example |
|---|---|
| Restating the code | `// increment counter` above `counter += 1` |
| Journal comments | `// Added by John on 2024-03-15` — use version control |
| Closing brace comments | `} // end if` — if you need these, function is too long |
| Commented-out code | Delete it. Version control has history. |
| Divider comments | `// ====== Section ======` — use functions to create sections |
| Mandated boilerplate | ✗ every function requires a doc comment — only public API needs it |

### Self-Documenting Code Principles

- Name explains what. Type explains shape. Comment explains why.
- If a comment could become a function name → extract the function.
- If a comment explains a complex condition → extract to named boolean.
- Code and comment must agree. Stale comment worse than no comment.

---

## 7. Complexity Management

### Cyclomatic Complexity

| Threshold | Action |
|---|---|
| 1–5 | Simple — no action needed |
| 6–10 | Review — consider splitting |
| 11–15 | Must split — function doing too much |
| 16+ | Architectural problem — redesign the approach |

### Reducing Complexity

| Technique | Effect |
|---|---|
| Guard clauses + early return | Eliminates nesting, reduces branch count |
| Extract function | Moves a branch into a named, testable unit |
| Lookup table / map | Replaces if/else chains with data-driven dispatch |
| Polymorphism / strategy | Replaces type-switching with dispatch |
| State machine | Replaces complex conditional state tracking |

### Cognitive Load Rules

- Reader understands function without scrolling → function fits in view
- Reader understands function without reading other functions → self-contained
- Reader predicts function behavior from name alone → well-named
- Reader identifies all side effects immediately → clearly marked or absent

### Dependency Depth

Any single function call chain (A calls B calls C calls D) should not
exceed 4 levels before reaching a leaf function. Deeper → flatten the
chain or reconsider the decomposition.

---

## 8. Abstraction & Reuse

### Rule of Three

✗ abstract after first duplication. Two similar blocks → leave them.
Three similar blocks → now extract. Premature abstraction creates
wrong abstractions that are harder to fix than duplication.

### Abstraction Rules

| Rule | Description |
|---|---|
| Earn the abstraction | 3+ call sites before extracting shared function |
| Name the abstraction | If you cannot name it clearly, it is not a real concept — don't extract |
| Flat over nested | Prefer composing flat functions over deeply nested wrappers |
| ✗ speculative generality | ✗ "might need this later" — build for current requirements only |
| Delete over deprecate | Unused code → delete. ✗ keep "just in case" — version control is the backup. |

### DRY Boundaries

DRY applies within a module. Across modules, some duplication is
acceptable and often preferable to coupling. Two modules duplicating
5 lines is better than both depending on a shared utility for those
5 lines.

| Scope | DRY threshold |
|---|---|
| Within function | Immediate — no duplication in same function |
| Within module | Extract at 3 occurrences |
| Across modules | Extract only if the concept is a genuine shared domain concept |
| Across projects | Only if it belongs in a shared library with its own versioning |

### YAGNI

✗ build for hypothetical future requirements. Every abstraction,
configuration option, or extension point must serve a current,
demonstrated need. Removing speculative code later is harder than
adding needed code when the need arises.

### Simplicity Test

After writing a solution, ask: can this be done with less? Fewer
lines, fewer branches, fewer abstractions, fewer files. The simplest
solution that meets requirements wins. Complexity must be justified
by current requirements — never by anticipated ones.

---

## 9. File Organization

### File Size

| Threshold | Action |
|---|---|
| ≤ 200 lines | Ideal — single concept, easy to navigate |
| 200–400 lines | Acceptable — review if it can be split |
| 400–600 lines | Split — file covers multiple concepts |
| 600+ lines | Mandatory split — architectural issue |

### File Structure Order

Every source file follows this order:

| Order | Section |
|---|---|
| 1 | File doc comment (if needed — purpose of this file) |
| 2 | Imports / dependencies — grouped by: standard lib → third-party → internal |
| 3 | Constants |
| 4 | Type definitions / data structures |
| 5 | Public functions (the module's API) |
| 6 | Private functions (implementation details) |

### One Concept Per File

Each file owns one concept: one type with its methods, one logical
group of related functions, or one feature slice. If a file has two
unrelated groups of functions → split into two files.

### Import Hygiene

- Import only what is used. ✗ wildcard imports. ✗ unused imports.
- Group imports with blank line separators: standard → external → internal.
- ✗ circular imports — if two files import each other, extract shared
  dependencies into a third file or restructure.

---

## 10. Readability

### Formatting Principles

| Rule | Description |
|---|---|
| Consistent indentation | One style per project — spaces or tabs, never mixed |
| Line length | Target ≤ 100 characters. Hard cap at 120. |
| Blank line discipline | One blank line between functions. Two blank lines between sections/classes. ✗ multiple blank lines inside function body. |
| Horizontal alignment | ✗ aligning values across lines — fragile to edits, creates noisy diffs |
| Vertical density | Related lines together, unrelated lines separated by one blank line |

### Readability Rules

| Rule | Description |
|---|---|
| Left-to-right, top-to-bottom | Code reads in natural order. ✗ reader jumping around to understand flow. |
| Positive logic | Express conditions as what IS true, not what ISN'T false |
| Newspaper rule | High-level at top, details at bottom — like a news article |
| Symmetry | Parallel structures use parallel code. Similar operations written similarly. |
| Explicit over implicit | Visible behavior over hidden magic. Clear call over operator overloading. |

### Diff-Friendly Code

Write code that produces clean, minimal diffs when changed:
- Trailing commas in multi-line lists — adding item = 1-line diff
- Each argument on its own line for long signatures
- Each item on its own line for multi-line collections
- ✗ reformatting unchanged lines in the same commit as logic changes

---

## 11. Anti-Patterns

### Code Smells

| Smell | Symptom | Fix |
|---|---|---|
| Long function | > 50 lines | Extract sub-functions |
| Deep nesting | > 3 levels | Guard clauses · extract function |
| Long parameter list | > 3 params | Group into structured type |
| Feature envy | Function accesses another module's data more than its own | Move function to the data's module |
| Data clump | Same group of variables passed together repeatedly | Extract into a type/struct |
| Primitive obsession | Using strings/ints where a domain type belongs | Create a named type |
| Shotgun surgery | One change requires edits across many files | Consolidate related logic |
| God function | One function that orchestrates everything | Decompose into pipeline stages |
| Dead code | Unreachable branches, unused functions | Delete — version control is backup |
| Copy-paste code | Duplicated blocks with minor variations | Extract shared logic (rule of three) |

### Naming Smells

| Smell | Example | Fix |
|---|---|---|
| Generic name | `data` · `result` · `temp` · `handler` | Name the specific thing |
| Misleading name | `validate()` that also transforms | Rename or split |
| Inconsistent naming | `get_user` · `fetch_account` · `retrieve_order` | Pick one verb, use everywhere |
| Encoding type | `user_list` · `name_string` | Drop the type suffix |
| Single letter (long scope) | `x` used across 20 lines | Use descriptive name |

### Logic Smells

| Smell | Description | Fix |
|---|---|---|
| Boolean blindness | Returning `true`/`false` when a richer type conveys meaning | Return enum or result type |
| Stringly typed | Using strings for status, type, mode when enum exists | Define enum/constant set |
| Hidden temporal coupling | Functions must be called in specific order but nothing enforces it | Make the pipeline explicit — output of A is input of B |
| Flag arguments | Boolean arg changes function behavior | Split into two functions |
| Side effect surprise | Function name suggests query but modifies state | Rename or separate command from query |

---

## 12. Code Writing Checklist

### Every Function

- [ ] Name reveals intent — reader predicts behavior without reading body
- [ ] ≤ 30 lines, ≤ 3 nesting levels, ≤ 3 parameters
- [ ] Single responsibility — described without "and"
- [ ] Guard clauses first, main logic at lowest indentation
- [ ] Operates at single abstraction level
- [ ] Pure if in Tier 0–2 (→ `architecture/STANDARDS.md §4`)

### Every Variable

- [ ] Named for what it holds, not how it's computed
- [ ] Declared close to first use, smallest possible scope
- [ ] Immutable by default — mutable only when required
- [ ] No magic numbers or strings — named constants

### Every File

- [ ] ≤ 400 lines, single concept
- [ ] Follows standard section order: imports → constants → types → public → private
- [ ] No unused imports, no circular imports
- [ ] Public API appears first, implementation details last

### Every Change

- [ ] Simpler solution not possible — complexity justified
- [ ] No speculative abstractions — every abstraction serves current need
- [ ] Self-documenting — comments explain why, not what
- [ ] No dead code, no commented-out code
- [ ] Diff is clean — only changed lines appear in diff
