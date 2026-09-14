# Code Writing Standards

> Rules for how individual identifiers, functions, statements, and files are written inside the structure architecture and design define.

**ID** `code_writing` · **Tier** Foundation · **Version** 1.0
**Owns** identifier naming · function style + size · variables + constants · control flow · loops · comment discipline · complexity thresholds · file internal structure · formatting + readability
**Defers to** layer model · purity · CQS · idempotency → [architecture](../architecture/STANDARDS.md) · patterns · abstraction · rule of three · module surface → [design](../design/STANDARDS.md) · file + directory names · file placement → [directory](../directory/STANDARDS.md) · error taxonomy · result types → [error_handling](../error_handling/STANDARDS.md) · doc comment content · API docs → [documentation](../documentation/STANDARDS.md) · reuse promotion · duplication budget · unit kinds → [primitives](../primitives/STANDARDS.md) · language syntax · idiom · formatter config → language standards
**Load with** [architecture](../architecture/STANDARDS.md) · [design](../design/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Naming](#2-naming)
3. [Functions](#3-functions)
4. [Variables and Constants](#4-variables-and-constants)
5. [Control Flow](#5-control-flow)
6. [Loops and Iteration](#6-loops-and-iteration)
7. [Comments](#7-comments)
8. [Complexity](#8-complexity)
9. [File Internals](#9-file-internals)
10. [Readability](#10-readability)
11. [Anti-Patterns](#11-anti-patterns)
12. [Scale Matrix](#12-scale-matrix)
13. [Checklist](#13-checklist)

---

## 1. Principles

| # | Principle |
|---|---|
| 1 | Code is read far more than written. Optimize for the reader |
| 2 | Name explains **what** · type explains **shape** · comment explains **why** |
| 3 | The reader predicts behavior from the signature alone, without reading the body |
| 4 | Every construct has a threshold. Cross it → split, never justify |
| 5 | Explicit over implicit. Visible behavior over hidden magic |
| 6 | Naming scope split: this standard governs **identifiers in code**; file and directory names → [directory](../directory/STANDARDS.md) |

---

## 2. Naming

### Rules

| Rule | Detail |
|---|---|
| Reveal intent | Name states what it holds or does — the reader never guesses |
| Searchable | Unique enough to find by text search across the codebase |
| Pronounceable | Speakable in conversation without spelling it out |
| ✗ abbreviations | Full words ; **except** universally known: `id` · `url` · `db` · `config` · `ctx` · `err` · `msg` · `args` · `opts` |
| ✗ type encoding | ✗ `strName` · ✗ `iCount` · ✗ `lstItems` — the type system carries the type |
| ✗ noise words | ✗ `data` · `info` · `temp` · `misc` · `stuff` · `manager` |
| One word per concept | Pick `fetch` **or** `get` **or** `retrieve` — one verb per operation, project-wide |
| ✗ disinformation | Name ✗ implies behavior the code does not have. `validate()` that also mutates → rename or split |

### By Kind

| Kind | Convention | Examples |
|---|---|---|
| Functions / methods | Verb-first, names the action | `compute_stats` · `validate_schema` · `parse_header` |
| Booleans | Question form, reads as true/false | `is_valid` · `has_header` · `can_retry` |
| Predicates | `is_` · `has_` · `can_` prefix | `is_empty` · `has_permission` |
| Collections | Plural noun | `users` · `error_messages` · `file_paths` |
| Single items | Singular noun | `user` · `error_message` · `file_path` |
| Constants | Names the fixed value + its unit | `MAX_RETRY_COUNT` · `DEFAULT_TIMEOUT_MS` |
| Types / classes | Noun naming the entity | `AnalysisResult` · `ConnectionPool` · `ParseError` |
| Callbacks / handlers | `on_` prefix \| `_handler` suffix | `on_complete` · `error_handler` |
| Factory functions | `create_` \| `build_` prefix | `create_connection` · `build_report` |
| Conversions | `to_` \| `from_` prefix | `to_json` · `from_csv` |

### Scope-Length Rule

Short scope → short name. Long scope → long descriptive name.

| Scope | Name length |
|---|---|
| Loop counter, ≤ 3-line body | `i` · `k` · `v` acceptable |
| Local variable, single function | Medium: `user_count` · `raw_text` |
| Module-level or exported | Descriptive: `max_concurrent_workers` · `default_output_format` |

---

## 3. Functions

Function classification (logic vs shell) and purity → [architecture](../architecture/STANDARDS.md) §4. This section governs the body.

### Thresholds

| Property | Rule |
|---|---|
| Responsibility | One thing. Describing it needs "and" → split |
| Line count | Target ≤ 30. Investigate at 50. **Mandatory split at 80** |
| Nesting depth | Max 3 levels. Deeper → extract the inner block to a named function |
| Parameter count | Max 3. More → group into a structured type |
| Return points | Early returns preferred over deep nesting. Multiple returns allowed |
| Abstraction level | One level per body. ✗ mixing orchestration with low-level parsing |

### Guard Clauses

Validate → reject early → run the main logic at the lowest indentation. ✗ wrapping the entire body in an `if` block for a precondition.

### Ordering Within a File

| Order | Category |
|---|---|
| 1 | Public API functions — the reader sees the contract first |
| 2 | High-level private functions called by the public API |
| 3 | Low-level helpers — implementation detail last |

Callers appear above callees. The reader moves top-down: entry point → helpers.

### Parameters

| Rule | Detail |
|---|---|
| ✗ boolean parameters | `process(data, True)` is unreadable at the call site → named enum or two functions |
| ✗ stringly-typed parameters | Known-set values use enums or constants · ✗ raw strings |
| Optional parameters carry defaults | Caller omits what it does not care about |
| Output parameters | ✗ — return the value instead |

---

## 4. Variables and Constants

### Declaration

| Rule | Detail |
|---|---|
| Declare close to first use | ✗ declaring everything at the top of the scope |
| Minimize scope | Block-level where block-level suffices · ✗ function-level |
| Immutable by default | Declare `const`/`final`/`readonly`. Mutable only when mutation is required |
| One purpose per variable | One concept for its whole lifetime. ✗ reusing a variable for a second meaning |
| Initialize at declaration | ✗ declare now, assign later |

### Constants

| Rule | Detail |
|---|---|
| ✗ magic numbers | Every literal number except `0`, `1`, `-1` becomes a named constant |
| ✗ magic strings | Every literal string used for comparison or configuration becomes a named constant |
| Constants grouped at file top | After imports, before types |
| Units in the name | `TIMEOUT_MS` · `MAX_SIZE_BYTES` · `RETRY_DELAY_SECONDS` — never ambiguous |

### Explanatory Variables

Break complex expressions into named steps. A well-named temporary is documentation the compiler checks.

`if (a.x > b.x && a.y < b.y && c.valid())` → extract `is_in_bounds` · `is_ready` → `if is_in_bounds and is_ready`.

---

## 5. Control Flow

### Booleans

| Rule | Detail |
|---|---|
| Positive conditions | `if is_valid` over `if not is_invalid` — ✗ double negatives |
| Extract complex conditions | Any condition with 2+ operators becomes a named boolean |
| Cheap checks first | Order short-circuit chains by cost and likelihood |

### Branching

| Rule | Detail |
|---|---|
| ✗ nested ternary | One level max. Two → if/else block |
| Exhaustive matching | Branching on a type or enum handles every variant |
| Fail on unknown | Default branch on a known-set type raises · ✗ silently passes |
| ✗ else after return | If-branch returns → the `else` is dead weight, remove it |
| ✗ empty branches | `if (x) {} else { work() }` → invert the condition |

### Absence

✗ compare against null directly in inner-layer logic. Handle absence structurally — pattern matching, optional chaining, or a guard clause. Explicit-absence contract → [architecture](../architecture/STANDARDS.md) §4.

### Failure

Raise, return, or propagate per the error taxonomy → [error_handling](../error_handling/STANDARDS.md). ✗ swallow an error to keep a branch tidy · ✗ empty catch blocks.

---

## 6. Loops and Iteration

### Preference Order

| Priority | Approach | When |
|---|---|---|
| 1 | Declarative (map · filter · reduce) | Transforming a collection · no index needed |
| 2 | For-each / for-in | Element access · no index needed |
| 3 | Indexed for loop | Index required by the logic, not just for access |
| 4 | While loop | Termination condition is not count-based |
| 5 | Infinite loop + break | Event loops · retry loops with a complex exit |

### Rules

| Rule | Detail |
|---|---|
| One responsibility per loop body | Complex body → extract to a function |
| ✗ mutate the collection being iterated | ✗ add or remove items mid-iteration |
| Bound every loop | Every loop has a known termination. While loops carry a max-iteration guard |
| ✗ deep nesting | Nested loop body > 5 lines → extract the inner loop |
| Accumulator pattern | Build the result in a local accumulator, return at the end · ✗ mutating external state in the body |
| Early exit | `continue` at the top to skip irrelevant items · `break` to leave — both reduce nesting |

---

## 7. Comments

Doc-comment format, API reference content, and ADRs → [documentation](../documentation/STANDARDS.md). This section governs when a comment is permitted at all.

### Hierarchy

Try each in order; comment only when the ones above fail.

| Priority | Approach |
|---|---|
| 1 | Make the code obvious — rename · restructure · extract |
| 2 | Encode it in the type — compiler-verified |
| 3 | Doc comment on the public API |
| 4 | Inline comment explaining **why** |

### Permitted

| Comment | When |
|---|---|
| **Why** | Non-obvious business reason · workaround · external constraint |
| **Warning** | Performance trap · subtle bug potential · non-obvious side effect |
| **TODO** | Known incomplete work — carries a ticket or issue reference |
| **Legal** | License or copyright, only where required |

### ✗ Never

| Anti-pattern | Example |
|---|---|
| Restating the code | `// increment counter` above `counter += 1` |
| Journal comments | `// Added by John on 2024-03-15` — version control owns history |
| Closing-brace comments | `} // end if` — needing them means the function is too long |
| Commented-out code | Delete it. Version control is the backup |
| Divider comments | `// ===== Section =====` — use functions to create sections |
| Mandated boilerplate | ✗ a doc comment on every function — only the public API needs one |

### Rules

- A comment that could become a function name → extract the function.
- A comment explaining a complex condition → extract a named boolean.
- Code and comment must agree. A stale comment is worse than no comment.

---

## 8. Complexity

### Cyclomatic Complexity

| Score | Action |
|---|---|
| 1–5 | Simple — no action |
| 6–10 | Review — consider splitting |
| 11–15 | **Must split** — the function does too much |
| 16+ | Architectural problem — redesign the approach |

### Reduction Techniques

| Technique | Effect |
|---|---|
| Guard clause + early return | Removes nesting · reduces branch count |
| Extract function | Moves a branch into a named, testable unit |
| Lookup table / map | Replaces an if/else chain with data-driven dispatch |
| Strategy / polymorphism | Replaces type-switching with dispatch |
| State machine | Replaces conditional state tracking → [design](../design/STANDARDS.md) §8 |

### Cognitive Load

| Test | Requirement |
|---|---|
| No scrolling | Function fits in one screen |
| No cross-referencing | Function understood without reading other functions |
| Predictable | Behavior inferable from the name alone |
| Visible effects | All side effects identifiable at a glance, or absent |

### Call Depth

A single call chain reaches a leaf within 4 levels. Deeper → flatten the chain or reconsider the decomposition.

### Simplicity

After it works: can it be done with fewer lines, fewer branches, fewer abstractions, fewer files? The simplest solution meeting current requirements wins. Complexity is justified by current requirements · ✗ by anticipated ones. Speculative generality and rule-of-three → [design](../design/STANDARDS.md) §6.

---

## 9. File Internals

File placement, file names, and directory structure → [directory](../directory/STANDARDS.md).

### Size

| Lines | Action |
|---|---|
| ≤ 200 | Ideal — one concept, easy to navigate |
| 200–400 | Acceptable — review whether it splits |
| 400–600 | Split — the file covers multiple concepts |
| 600+ | **Mandatory split** — architectural issue |

### Section Order

Every source file, in this order:

| Order | Section |
|---|---|
| 1 | File doc comment — only if the file's purpose is non-obvious |
| 2 | Imports — grouped: standard library → third-party → internal |
| 3 | Constants |
| 4 | Type definitions |
| 5 | Public functions — the module's API |
| 6 | Private functions — implementation detail |

### Rules

| Rule | Detail |
|---|---|
| One concept per file | Two unrelated groups of functions → two files |
| ✗ unused imports | Every import is referenced |
| ✗ wildcard imports | Import named symbols only |
| ✗ circular imports | Two files importing each other → extract the shared dependency into a third |
| Import groups separated by a blank line | Standard → external → internal |

---

## 10. Readability

### Formatting

| Rule | Detail |
|---|---|
| Consistent indentation | One style per project — spaces **or** tabs, ✗ mixed |
| Line length | Target ≤ 100 characters. Hard cap 120 |
| Blank lines | One between functions. Two between top-level sections. ✗ multiple blank lines inside a function body |
| ✗ horizontal alignment | Aligning values across lines is fragile and produces noisy diffs |
| Vertical density | Related lines adjacent; unrelated lines separated by one blank line |
| Formatter is authoritative | Formatting is enforced by tooling · ✗ argued in review |

### Reading Rules

| Rule | Detail |
|---|---|
| Left-to-right, top-to-bottom | The reader never jumps around to follow the flow |
| Newspaper rule | High-level at the top, detail at the bottom |
| Positive logic | Express what IS true · ✗ what ISN'T false |
| Symmetry | Parallel operations written in parallel form |
| Explicit over implicit | Clear call over operator overloading or hidden magic |

### Diff Hygiene

- Trailing commas in multi-line lists — adding an item is a one-line diff.
- One argument per line for long signatures; one item per line for multi-line collections.
- ✗ reformatting unchanged lines in the same commit as a logic change.

---

## 11. Anti-Patterns

### Code Smells

| Smell | Symptom | Fix |
|---|---|---|
| Long function | > 50 lines | Extract sub-functions |
| Deep nesting | > 3 levels | Guard clauses · extract function |
| Long parameter list | > 3 parameters | Group into a structured type |
| Feature envy | Function touches another module's data more than its own | Move the function to that module |
| Data clump | The same group of variables passed together repeatedly | Extract a type |
| Primitive obsession | Strings/ints where a domain type belongs | Create the named type |
| Shotgun surgery | One change forces edits across many files | Consolidate the related logic |
| God function | One function orchestrating everything | Decompose into pipeline stages |
| Dead code | Unreachable branches · unused functions | Delete — version control is the backup |
| Copy-paste | Duplicated blocks with minor variations | Extract at the third occurrence |

### Naming Smells

| Smell | Example | Fix |
|---|---|---|
| Generic name | `data` · `result` · `temp` · `handler` | Name the specific thing |
| Misleading name | `validate()` that also transforms | Rename or split |
| Inconsistent verbs | `get_user` · `fetch_account` · `retrieve_order` | Pick one verb, use it everywhere |
| Type-encoded name | `user_list` · `name_string` | Drop the type suffix |
| Single letter in long scope | `x` used across 20 lines | Descriptive name |

### Logic Smells

| Smell | Symptom | Fix |
|---|---|---|
| Boolean blindness | Returning `true`/`false` where a richer type conveys meaning | Return an enum or result type |
| Stringly typed | Strings for status · type · mode | Define an enum or constant set |
| Flag argument | Boolean parameter switching behavior | Split into two functions |
| Hidden temporal coupling | Functions must be called in order but nothing enforces it | Make the pipeline explicit — output of A is input of B |
| Side-effect surprise | Name suggests a query but the function mutates | Rename, or separate command from query |
| Swallowed failure | Empty catch block · ignored return code | Propagate → [error_handling](../error_handling/STANDARDS.md) |

---

## 12. Scale Matrix

Thresholds in §3 · §8 · §9 · §10 never relax. Only enforcement and documentation depth vary.

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Formatter | Optional | Enforced in CI | Enforced in CI + pre-commit hook |
| Linter | Warnings visible | Warnings block the build | Warnings block · custom project rules |
| Complexity gate | Advisory | CI fails above 15 | CI fails above 10 |
| Doc comments | None required | Every public function | Every public function + module doc |
| Dead code | Tolerated | Deleted before merge | CI detects and blocks |
| Naming consistency | Best effort | Reviewed at merge | Enforced vocabulary list per project |

---

## 13. Checklist

- [ ] Every name reveals intent; no `data` · `info` · `temp` · `misc` (§2, §11)
- [ ] No abbreviations outside the allowed set (§2)
- [ ] One verb per concept across the project (§2, §11)
- [ ] No type encoded in any identifier (§2, §11)
- [ ] Name length matches scope length (§2)
- [ ] No function exceeds 80 lines; target ≤ 30 (§3)
- [ ] No function nests deeper than 3 levels (§3)
- [ ] No function takes more than 3 parameters (§3)
- [ ] No boolean parameters (§3, §11)
- [ ] Guard clauses first; main logic at lowest indentation (§3)
- [ ] Public functions appear above the private helpers they call (§3, §9)
- [ ] Every function body sits at one abstraction level (§3)
- [ ] Every variable is immutable unless mutation is required (§4)
- [ ] Every variable declared at first use, in the smallest scope (§4)
- [ ] Zero magic numbers (except 0, 1, -1) and zero magic strings (§4)
- [ ] Every constant carrying a quantity names its unit (§4)
- [ ] Conditions are positive; no double negatives (§5)
- [ ] Every branch on a type or enum is exhaustive; unknown → error (§5)
- [ ] No error swallowed to keep a branch tidy (§5, §11)
- [ ] Every loop has a known bound (§6)
- [ ] No collection mutated during its own iteration (§6)
- [ ] Every comment explains why, never what (§7)
- [ ] Zero commented-out code, journal comments, or divider comments (§7)
- [ ] No function exceeds cyclomatic complexity 15 (§8)
- [ ] Call chains reach a leaf within 4 levels (§8)
- [ ] No file exceeds 600 lines; target ≤ 400 (§9)
- [ ] File follows section order: imports → constants → types → public → private (§9)
- [ ] Zero unused imports, wildcard imports, or circular imports (§9)
- [ ] Line length ≤ 120 characters (§10)
- [ ] Diff contains only changed lines — no drive-by reformatting (§10)
