# Local MCP Tool Standards

> Rules for designing, shaping, and budgeting the tools an MCP server exposes to a local language model.

**ID** `local_mcp/tools` · **Tier** Domain · **Version** 1.0
**Owns** tool count discipline · four-tool pattern · surgical read protocol · tool schema · annotations · patch protocol · return + error contract · token budget · LLM input resilience
**Defers to** architecture · engine/server split · tier model · naming → [STANDARDS.md](STANDARDS.md) · snapshots · receipts · constrained-mode helpers · output paths → [RUNTIME.md](RUNTIME.md) · testing · docstring CI gate → [DELIVERY.md](DELIVERY.md) · error taxonomy + boundaries → [error_handling](../error_handling/STANDARDS.md) · input validation boundary → [security](../security/STANDARDS.md) · API contract + versioning → [api](../api/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [RUNTIME.md](RUNTIME.md) · [DELIVERY.md](DELIVERY.md)

---

## Table of Contents

1. [Tool Count Discipline](#1-tool-count-discipline)
2. [The Four-Tool Pattern](#2-the-four-tool-pattern)
3. [Surgical Read Protocol](#3-surgical-read-protocol)
4. [Return Size Limits](#4-return-size-limits)
5. [Tool Schema Design](#5-tool-schema-design)
6. [Tool Annotations](#6-tool-annotations)
7. [The Patch Protocol](#7-the-patch-protocol)
8. [Return Value Contract](#8-return-value-contract)
9. [Error Handling Contract](#9-error-handling-contract)
10. [Token Budget Discipline](#10-token-budget-discipline)
11. [LLM Input Resilience](#11-llm-input-resilience)
12. [Anti-Patterns](#12-anti-patterns)
13. [Checklist](#13-checklist)

---

## 1. Tool Count Discipline

Every tool schema occupies the KV cache for the entire conversation. At 8 GB VRAM, ten tools consume ~8–10% of context before any user data arrives. Models select correctly at ≤8 tools; selection errors rise sharply at 15+.

| Target hardware | Max tools per server | Max tools loaded at once |
|---|---|---|
| 4–6 GB VRAM (≤7B model) | 6 | 6 — one server only |
| 8 GB VRAM (9B model) | 8 | 12 — tier 1 + tier 2 |
| 12–16 GB VRAM (14B model) | 10 | 16 — any two servers |
| 24 GB+ VRAM (32B+ model) | 12 | 20 |

Default open-source target = **8 GB VRAM**: 8 tools per server, 12 loaded simultaneously. Hard ceiling: **✗ exceed 10 tools in a single server** — split at finer tier granularity → [STANDARDS.md](STANDARDS.md).

Rule: fewer tools, sharper tools.

---

## 2. The Four-Tool Pattern

Every data or state-changing task follows this loop in this order. Tool design encodes it so the model is guided through it.

    LOCATE → INSPECT → PATCH → VERIFY

| Step | Action | Returns |
|---|---|---|
| LOCATE | Find the nodes needing change without reading anything else | Addresses · indices · IDs — zero content |
| INSPECT | Read only the located node(s) | One node in detail, bounded by size limits |
| PATCH | Apply the edit to only that node | Confirmation dict naming what changed |
| VERIFY | Read back only the edited node | Same tool as INSPECT — model confirms result matches intent |

VERIFY reuses the INSPECT tool. ✗ add a fourth dedicated tool for it.

---

## 3. Surgical Read Protocol

A tool that returns data returns **only the data the model asked for**. ✗ surrounding context · ✗ related data "that might be useful" · ✗ the full parent structure for convenience.

Three tool classes are mandatory in every domain:

| Class | Returns | Examples |
|---|---|---|
| Index | Structure without content | dataset schema (columns + dtypes + row count, ✗ values) · model summary (type + params + metrics, ✗ weights) · document outline (headings + indices, ✗ body) · process list (PIDs + names, ✗ memory maps) |
| Search | Matching addresses only | columns with nulls (names, ✗ columns) · rows matching a predicate (indices, ✗ rows) · files matching a glob (paths, ✗ contents) · log lines at a level (line numbers, ✗ surrounding lines) |
| Bounded read | One address, hard size cap | row range (start, end) · one column's stats · one model's metrics · one bounded log range |

✗ a search tool that falls back to returning everything when it finds nothing → return an empty list plus a hint naming the next tool.

---

## 4. Return Size Limits

Enforced in the engine, ✗ requested from the model. Constrained-mode column applies when `MCP_CONSTRAINED_MODE=1` → [RUNTIME.md](RUNTIME.md).

| Data type | Default limit | Constrained (8 GB) limit | Enforcement |
|---|---|---|---|
| DataFrame rows | 100 / call | 20 / call | Error if exceeded |
| DataFrame columns | 50 / call | 20 / call | Truncate with warning |
| Search results | 50 / call | 10 / call | `max_results` parameter |
| Log lines | 100 / call | 50 / call | Error if exceeded |
| List items (generic) | 100 / call | 40 / call | Truncate with flag |
| JSON object depth | 5 levels | 3 levels | Flatten deeper structures |
| Text paragraphs | 50 / call | 20 / call | Error if exceeded |
| Image pixels | Never raw | Never raw | Return stats + path |
| Model weights | Never raw | Never raw | Return path + summary |

Every limited response carries: `"truncated": true` · `"returned"` (count) · `"total_available"` (count) · `"hint"` naming the bounded-read tool and arguments that fetch the rest.

Every response carries `"token_estimate"` — a rough count of its own output (character length ÷ 4) so the model can budget remaining context.

---

## 5. Tool Schema Design

### Docstrings — the 80-character rule

Every tool docstring is ≤ 80 characters. Docstrings are sent to the model every turn; they are selection cues, ✗ human documentation. State what the tool does and what it returns; list enum values as bare space-separated tokens. CI enforces the limit → [DELIVERY.md](DELIVERY.md).

### Parameters

Parameters are lowercase `snake_case` nouns describing what they contain. ✗ verb-first (`get_file_path`) · ✗ abbreviations (`target_col`) · ✗ camelCase (`filePath`).

| Allowed type | Used for |
|---|---|
| `str` | Paths · names · addresses · text · enum values |
| `int` | Indices · counts · limits · seeds |
| `float` | Ratios · thresholds · percentages |
| `bool` | Flags with a sensible default |
| `list[dict]` | Patch op arrays only |
| `list[str]` | Column · file · label lists only |

| ✗ Never in a tool signature | Use instead |
|---|---|
| `Optional[T]` | `T = None` |
| `Union[T, S]` | Two tools, or one discriminated string |
| `Any` | The precise type |
| `dict` | Named scalar parameters — the model hallucinates arbitrary keys |
| Custom model classes | Primitive parameters |
| `Enum` | `str` + valid values listed in the docstring |

### Inference and dry run

Where a tool must infer intent (chart type, aggregation, date format, delimiter): infer from evidence · expose an override parameter · report what was inferred in the response.

Every write tool takes `dry_run: bool = False`. `dry_run=True` → return exactly what would change, change nothing, and set `"dry_run": true` plus `"would_change"` in the response.

---

## 6. Tool Annotations

Annotations are always set — AI clients use them to display and gate tools.

| Tool type | readOnlyHint | destructiveHint | idempotentHint | openWorldHint |
|---|---|---|---|---|
| Read · inspect · search | true | false | true | false |
| Write · patch (with snapshot) | false | false | false | false |
| Delete · drop rows | false | true | false | false |
| Network · scrape · download | false | false | false | true |
| Export · generate HTML | false | false | true | false |

`destructiveHint=true` triggers an extra confirmation prompt in most clients. Set it on every irreversible operation: `drop_column` · `delete_rows` · `purge_versions`.

---

## 7. The Patch Protocol

A tool that modifies structured data accepts a **list of operations** when the task naturally involves multiple changes. Five cleaning steps = one `apply_patch` call with 5 ops, ✗ five tool calls.

Op array format:

| Rule | Detail |
|---|---|
| `"op"` key | Always present · always first · always a **string** |
| Other keys | Operation-specific required fields, flat alongside `"op"` |
| Batch size | Maximum **50 ops** per call |
| Application | Sequential, in array order |
| Validation | **Validate the entire array before creating any snapshot or touching any file** |

### Validate before snapshot — mandatory ordering

Order is load-bearing. Getting it backwards is the most commonly violated rule in patch implementations.

1. Coerce and normalize every op (§11).
2. Collect every op name absent from the handler map. Any unknown → return an error dict listing them. **No snapshot taken. No file touched.**
3. Only after the full array validates → `snapshot()`.
4. Apply ops sequentially.

Snapshot-then-validate leaves a permanently orphaned backup file for every failed call, filling the user's disk. Validation must never have a filesystem side effect.

### Op naming

Op names are `verb_noun` snake_case: `fill_nulls` · `drop_duplicates` · `rename_column` · `replace_text` · `set_cell` · `insert_row` · `train_model` · `export_report` · `apply_transform`.

Allowed op verbs: `fill` · `drop` · `rename` · `replace` · `set` · `insert` · `delete` · `add` · `update` · `move` · `train` · `export` · `apply` · `restore`

---

## 8. Return Value Contract

Every tool returns a dict. No exception — ✗ plain string · ✗ list · ✗ `None` · ✗ boolean. Async tools included: an async engine function returns a dict on every code path.

| Field | Type | Required | Purpose |
|---|---|---|---|
| `"success"` | bool | Always — first key | Model checks it first |
| `"op"` | str | On success | Confirms which operation ran |
| `"error"` | str | On failure | Human-readable failure reason |
| `"hint"` | str | On failure | Actionable recovery instruction |
| `"backup"` | str | After any write | Path to the snapshot taken before the write |
| `"progress"` | list | Always | Step-by-step execution log → [RUNTIME.md](RUNTIME.md) |
| `"dry_run"` | bool | When `dry_run=True` | Confirms simulation mode |
| `"token_estimate"` | int | Always | Response size ÷ 4 |
| `"truncated"` | bool | On bounded reads | Always explicit, never absent |
| `"output_path"` | str | When a file is written | Absolute path — callers chain on it |
| `"output_file"` | str | When a file is written | Filename only |

Write confirmations name what changed — the operation, the target, the count affected, the value used, the backup path. Write tools confirm the write; read tools read. ✗ return raw data arrays from a write tool.

---

## 9. Error Handling Contract

**✗ raise an exception to the caller.** Every exception is caught in `engine.py` and converted to an error dict with `"success": false` · `"error"` · `"hint"`, plus `"backup"` when a snapshot was already taken. Error taxonomy and boundary theory → [error_handling](../error_handling/STANDARDS.md).

Caught exception classes at minimum: file-not-found · wrong extension · unknown column/index · out-of-memory · unknown op · catch-all.

Error message pattern: state the fact and the observed value — `File not found: {path}` · `Expected .csv file, got .{ext}` · `Column '{name}' not found. Available: {columns}` · `Insufficient RAM: need ~{n} GB, available ~{m} GB` · `Unknown op: '{op}'. Allowed: {allowed}`.

### The hint field

A hint completes the sentence "To fix this, ..." and names a specific tool to call or a specific value to check.

| ✗ Bad hint | Good hint |
|---|---|
| "Invalid input." | "Use inspect_dataset() first to verify column names and dtypes." |
| "Try again." | "Use read_rows(file, 0, 100) to preview data before patching." |
| "Not supported." | "Available strategies: mean median mode ffill bfill drop" |

Error dicts never leak connection strings · API keys · passwords · absolute system paths → [RUNTIME.md](RUNTIME.md).

---

## 10. Token Budget Discipline

The chain: GPU VRAM → model weights consume most of it → remainder = KV cache → KV cache size = effective context → token budget per call = context ÷ expected turns.

8 GB GPU with a 9B model (Q4_K_M): weights ~5.5 GB · KV cache ~1.7 GB · effective context ~10,000–12,000 tokens · per-turn content budget ~100–300 tokens after schema and history overhead.

| Budget | Ceiling |
|---|---|
| All tool schemas combined | 700 tokens — ≤8 tools × ≤80-char docstrings |
| Read tool response | 500 tokens |
| Write confirmation | 150 tokens |
| Raw arrays · pixel data · weight tensors · full file contents | Never returned at any size |

Limits are never hardcoded in engine functions — call the `get_max_*()` helpers, which read `MCP_CONSTRAINED_MODE` at call time → [RUNTIME.md](RUNTIME.md).

---

## 11. LLM Input Resilience

Local models produce inconsistent argument formatting. Tools absorb the predictable mistakes and reject the ambiguous ones with an example.

| Mistake | Example | Response |
|---|---|---|
| Params nested inside the `"op"` key | `{"op": {"col": "x", "dtype": "float"}}` | Coerce (below) |
| Alternate key name | `"operator"` for `"op"` · `"method"` for `"strategy"` | Accept both spellings silently |
| String value for a numeric param | `{"max_rows": "100"}` | Coerce to int |
| List wrapped in a list | `{"columns": [["a","b"]]}` | Flatten one level |
| Dict value for a string param | `{"file_path": {"path": "/d/f.csv"}}` | Error dict with a correct-usage example |
| Required key missing entirely | `{"column": "x"}` with no `"op"` | Infer via signature table ; else error with example |

### Dual-key acceptance

Accept both spellings of a key; document the canonical name in the docstring. ✗ error on an alternate spelling — the model is being helpful, not wrong.

### Op coercion

Before validation, normalize every op so `"op"` is a string:

1. `"op"` already a non-empty string → pass through unchanged.
2. `"op"` is a dict → merge its keys with the top-level keys (excluding `"op"`) into one flat param set.
3. Infer the op name by matching the flat param keys against a signature table of distinctive keys — `dtype` → `cast_column` · `strategy` → `fill_nulls` · `mapping` → `replace_values` · `expression` → `add_column` · `subset` → `drop_duplicates`.
4. Inference fails → pass the op through unchanged; it fails at validation with a clear error naming the allowed ops.

### Type-safe extraction

Guard against wrong types, ✗ only missing keys. A non-string `"op"` used as a dict key raises an unhashable-type error before validation can report anything useful. Check the type first, then return an error dict carrying a correct-usage example.

---

## 12. Anti-Patterns

| ✗ Anti-pattern | Fix |
|---|---|
| One tool that searches AND reads AND edits | Split into three — LOCATE · INSPECT · PATCH |
| Tool returns the full dataset so the model can "find what it needs" | Search tool returning addresses |
| Write tool that returns nothing about what changed | Confirmation dict naming the change + backup |
| One tool that trains AND evaluates AND exports | One tool per tier boundary |
| Snapshot taken before op-array validation | Validate fully, then snapshot |
| Size limits hardcoded as magic numbers | `get_max_*()` helpers |
| Docstring written for a human reader | ≤80-char selection cue |
| `dict` or `Any` in a tool signature | Named primitive parameters |
| Exception propagated out of a tool | Error dict with `"hint"` |
| Search miss returns everything | Empty list + hint |

---

## 13. Checklist

- [ ] Server exposes ≤ 10 tools (target 6–8 at the 8 GB reference target)
- [ ] Every read/write task is expressible as LOCATE → INSPECT → PATCH → VERIFY
- [ ] Index, search, and bounded-read tools all exist for the domain
- [ ] No tool returns surrounding context, parent structure, or full datasets
- [ ] Every bounded read enforces its limit in the engine, not via the model
- [ ] Every truncated response sets `"truncated"`, `"returned"`, `"total_available"`, `"hint"`
- [ ] Every response includes `"token_estimate"`
- [ ] Every tool docstring is ≤ 80 characters
- [ ] Every parameter type is in the allowed list; no `Optional`, `Union`, `Any`, `dict`, `Enum`
- [ ] Every write tool takes `dry_run: bool = False` and honours it
- [ ] Annotations set on every tool; `destructiveHint=true` on every irreversible one
- [ ] Op arrays are capped at 50 ops and applied sequentially
- [ ] Op array fully validated BEFORE any snapshot or file write
- [ ] A failed validation leaves no `.bak` file behind
- [ ] Op names use `verb_noun` with a verb from the approved list
- [ ] Every tool returns a dict on every code path, async included
- [ ] `"success"` is the first key of every response
- [ ] Every write response carries `"backup"`, `"output_path"`, `"output_file"`
- [ ] No exception escapes the engine; each becomes an error dict
- [ ] Every error dict has a `"hint"` naming a specific tool or value
- [ ] No error or progress message leaks credentials or absolute system paths
- [ ] Combined tool schemas stay under 700 tokens
- [ ] No size limit is hardcoded; all come from `get_max_*()`
- [ ] Op-array tools coerce malformed ops and accept dual-key spellings
- [ ] Non-string `"op"` values are type-checked before use as a lookup key
