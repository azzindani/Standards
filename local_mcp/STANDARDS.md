# STANDARDS.md — General-Purpose MCP Server Development Standards

This document defines the complete standard for building open-source MCP
(Model Context Protocol) servers with local execution engines. It is derived from
real architectural decisions, real failure modes, and real hardware constraints
encountered while building production-grade MCP tooling across multiple domains:
document editing, data analytics, machine learning, media processing, system
automation, and more.

These standards apply to any MCP server regardless of domain. They are not optional
guidelines. They are the rules that determine whether a server works reliably on
constrained hardware with a local LLM — or at all.

---

## Table of Contents

1. [Why these standards exist](#1-why-these-standards-exist)
2. [The core mental model](#2-the-core-mental-model)
3. [MCP Primitives — Tools, Resources, and Prompts](#3-mcp-primitives--tools-resources-and-prompts)
4. [The self-hosted execution principle](#4-the-self-hosted-execution-principle)
5. [Language and runtime selection](#5-language-and-runtime-selection)
6. [Repository structure](#6-repository-structure)
7. [The three-tier split](#7-the-three-tier-split)
8. [Tool count discipline](#8-tool-count-discipline)
9. [The four-tool pattern](#9-the-four-tool-pattern)
10. [Surgical read protocol](#10-surgical-read-protocol)
11. [Tool schema design](#11-tool-schema-design)
12. [Tool annotations](#12-tool-annotations)
13. [The patch protocol](#13-the-patch-protocol)
14. [Engine and server separation](#14-engine-and-server-separation)
15. [Engine sub-module pattern](#15-engine-sub-module-pattern)
16. [Return value contract](#16-return-value-contract)
17. [Error handling contract](#17-error-handling-contract)
18. [Security considerations](#18-security-considerations)
19. [State and version control](#19-state-and-version-control)
20. [Token budget discipline](#20-token-budget-discipline)
21. [Hardware tiers and resource constraints](#21-hardware-tiers-and-resource-constraints)
22. [Progress output](#22-progress-output)
23. [Long-running operations and async](#23-long-running-operations-and-async)
24. [Live state and reload](#24-live-state-and-reload)
25. [Operation receipt log](#25-operation-receipt-log)
26. [Output generation pattern](#26-output-generation-pattern)
27. [Shared data I/O standards](#27-shared-data-io-standards)
28. [LLM input resilience](#28-llm-input-resilience)
29. [Testing standards](#29-testing-standards)
30. [Cross-platform compatibility](#30-cross-platform-compatibility)
31. [Multi-client compatibility](#31-multi-client-compatibility)
32. [Transport modes](#32-transport-modes)
33. [Installation and distribution](#33-installation-and-distribution)
34. [Naming conventions](#34-naming-conventions)
35. [Dependency policy](#35-dependency-policy)
36. [CI/CD requirements](#36-cicd-requirements)
37. [Documentation requirements](#37-documentation-requirements)
38. [What to never do](#38-what-to-never-do)
39. [Checklist — new server from scratch](#39-checklist--new-server-from-scratch)
40. [Checklist — new tool in existing server](#40-checklist--new-tool-in-existing-server)
41. [Domain reference table](#41-domain-reference-table)

---

## 1. Why These Standards Exist

Most MCP servers fail on local hardware because: tool schemas overflow the context window, tools return full datasets, single tools do too much, no version control means silent data corruption, external APIs leak data, and install is too complex.

These standards exist to prevent all of these failures by design, not by luck.

The two target constraints that drive every decision in this document:

> **Constraint 1 (hardware):** A user with an 8GB GPU, running a 9B parameter local
> model, doing real work on real data, must be able to use these tools without hitting
> context limits, without corrupting data, and without needing a developer to set it up.

> **Constraint 2 (sovereignty):** All execution happens locally. No data leaves the
> user's machine. No API keys. No cloud subscriptions. No dependency on a third-party
> server being up. The tool runs on the user's hardware using the user's resources.

Every rule in this document traces back to one or both of these constraints.

---

## 2. The Core Mental Model

An MCP server is a **structured API that a language model calls with JSON arguments
and receives JSON results from**. It is not a chat assistant. It is not a script
runner. It is not an AI agent. It is a deterministic function executor.

The model provides intelligence — deciding what to call, in what order, with what
arguments. The MCP server provides execution — doing the operation reliably, returning
structured confirmation, never guessing.

```
Model's job:        understand intent, choose tools, generate arguments, decide next step
MCP server's job:   validate input, execute operation, return structured result
```

The server must never cross into the model's job. No AI inference inside tools. No
"smart" behavior that guesses what the user probably meant. Deterministic in, deterministic out.

---

## 3. MCP Primitives

**Tools** are the primary primitive — called by the model with JSON arguments, returning JSON results. Everything in this standard is about tools.

**Resources** expose stable, re-readable context (schemas, reference data) without a tool call. Use only when data does not change between calls. If it can change, it must be a tool.

**Prompts** are reusable workflow templates. Most servers do not need them.

```
Model needs to call it to do work          → Tool
Model needs to reference it for context    → Resource
User needs a starting workflow template    → Prompt
```

---

## 4. The Self-Hosted Execution Principle

This is the founding principle that distinguishes this standard from cloud-first MCP
servers.

### What it means

Every tool in every server must execute its core operation using local resources:
local CPU, local GPU, local RAM, local disk, local processes. The tool must not
require an internet connection to perform its primary function.

**Permitted:** local files, databases, subprocesses (FFmpeg, Tesseract, etc.), locally-run services (Postgres, Docker, MLflow). One-time network downloads with local caching are acceptable if the tool degrades gracefully without them.

**Not permitted as primary execution:** paid third-party APIs (OpenAI, AWS, Google Cloud, etc.), OAuth/API key requirements, sending user data to external servers, depending on a cloud service being online.

### The test

Ask this question for every tool: **"Can this tool complete its primary operation
with the machine disconnected from the internet?"** If the answer is no, the tool
violates this standard.

### Exceptions

Network access is permitted for:
- One-time model/asset downloads on first run (with local caching)
- Tools explicitly scoped to network operations (web scraper, feed reader, sitemap
  crawler) where network access is the stated purpose
- Optional telemetry that is disabled by default

Document every exception clearly in the tool's docstring and in the README.

---

## 5. Language and Runtime Selection

### The rule: libraries dictate language, not preference

Choose the language that has the best library support for your domain. Not the
language you prefer. Not the language that is fashionable. The language where the
problem is already solved locally.

| Domain | Recommended language | Primary local libraries |
|---|---|---|
| Document editing (docx, xlsx, pptx) | Python | python-docx, openpyxl, python-pptx |
| PDF manipulation | Python | PyMuPDF, pdfplumber, reportlab |
| Data analytics | Python | polars, duckdb, pandas, ydata-profiling |
| Machine learning | Python | scikit-learn, XGBoost, LightGBM, FLAML |
| Deep learning / GPU | Python | PyTorch, ONNX Runtime |
| Image processing | Python | Pillow, OpenCV, scikit-image |
| Audio processing | Python | librosa, pydub |
| Video processing | Python | MoviePy, FFmpeg (subprocess) |
| OCR | Python | easyocr, surya, pytesseract |
| Browser automation | Python or TypeScript | playwright-python or playwright (Node) |
| Database (SQL) | Python or TypeScript | duckdb, sqlite3, psycopg2 |
| System / OS automation | Python or Go | psutil, subprocess; Go single binary |
| Web scraping | Python | playwright, BeautifulSoup, httpx |
| File system operations | Go or Rust | Single binary, no runtime, fastest |
| Web API wrappers | TypeScript | Best for JSON-heavy REST APIs |
| Geospatial | Python | geopandas, shapely, rasterio |
| Time series | Python | statsforecast, sktime, neuralprophet |
| Security tools | Python or Rust | cryptography, bandit, detect-secrets |

### Python setup

Pin Python to `3.12`. Use `uv` as the package manager. Never use pip directly in
production. Never use conda. Never use poetry for new projects.

```
# .python-version
3.12
```

```toml
# pyproject.toml
[project]
requires-python = "==3.12.*"    # strict pin — never >=3.12
```

Strict pinning (`==3.12.*`) prevents accidental breakage when a CI runner upgrades
to 3.13. Users running 3.11 get a clear error rather than silent failures.

Pin `fastmcp` version in `pyproject.toml`. The FastMCP API surface has changed
between major versions. Breaking changes in the tool registration API have caused
silent failures where tools appear to register but are never served.

```toml
[project]
dependencies = [
    "fastmcp>=2.0,<3.0",
    ...
]
```

Require `uv` version `>=0.5` in every project so JIT dependency resolution
(just-in-time install on first run) works reliably:

```toml
[tool.uv]
required-version = ">=0.5"
```

Configure `ruff` in the root `pyproject.toml` for consistent linting and formatting:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
exclude = ["*.ipynb"]      # exclude notebooks from linting

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP"]
ignore = ["E402"]
```

---

## 6. Repository Structure

### Monorepo is the default for multi-server projects

If you are building more than one MCP server that share a domain or pipeline
(e.g., data profiler + data cleaner + statistical analysis, or Word + Excel +
PowerPoint), use a monorepo with a workspace. One repo, one lockfile, one CI
pipeline, one install script.

### Monorepo layout

```
{project-name}/
│
├── shared/                         # code shared by ALL servers — never duplicate
│   ├── __init__.py
│   ├── version_control.py          # snapshot / rollback
│   ├── patch_validator.py          # validate op arrays before applying
│   ├── file_utils.py               # path resolution, atomic writes, CSV reading
│   ├── platform_utils.py           # OS detection, hardware mode flags
│   ├── progress.py                 # ok/fail/info/warn/undo progress helpers
│   ├── receipt.py                  # operation receipt log
│   ├── html_theme.py               # shared HTML/CSS/Plotly theme + offline JS
│   └── html_layout.py              # responsive CSS constants, chart layout helpers
│
├── servers/
│   ├── {domain}_{tier}/            # e.g. data_basic, ml_basic, office_basic
│   │   ├── __init__.py
│   │   ├── server.py               # FastMCP setup + tool definitions (thin)
│   │   ├── engine.py               # pure domain logic (no MCP imports)
│   │   ├── _{tier}_helpers.py      # sub-module: shared imports + constants + helpers
│   │   ├── _{tier}_*.py            # sub-modules: grouped by function (see §15)
│   │   └── pyproject.toml
│   │
│   ├── {domain}_medium/
│   │   └── ...
│   │
│   └── {domain}_advanced/
│       └── ...
│
├── tests/
│   ├── fixtures/                   # real test data, committed to repo
│   ├── conftest.py
│   └── test_{server_name}.py
│
├── install/
│   ├── install.sh                  # Linux / macOS — POSIX sh compatible
│   ├── install.bat                 # Windows CMD
│   └── mcp_config_writer.py        # writes to AI client config files
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  # lint + test on push/PR (all platforms)
│       └── release.yml             # build + publish on tag push
│
├── pyproject.toml                  # root workspace
├── uv.lock
├── .python-version
├── .gitattributes
├── .editorconfig
├── CLAUDE.md
├── STANDARDS.md
└── README.md
```

### Single-server flat layout

```
{server-name}/
├── server.py
├── engine.py
├── shared/
├── tests/
│   ├── fixtures/
│   └── test_engine.py
├── install/
│   ├── install.sh
│   └── install.bat
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## 7. The Three-Tier Split

Every MCP server targets a specific complexity tier. Never mix tiers in one server.
This is the most important structural decision because it directly controls how many
tools the local model has to reason about at once.

### Tier 1 — Basic (CRUD and direct operations)

Tools that read data and perform simple create/update/delete operations on individual
nodes. No complex transformations. No multi-step pipelines. No cross-element
operations.

Examples: read paragraph, load file, inspect schema, list processes, read metadata.

**Tool count target: 6–8 tools.** Must stand alone — a user doing simple tasks should never need tier 2 or 3.

### Tier 2 — Medium (structured and pipeline operations)

Tools that perform multi-step structured operations — formulas, conditional logic,
template filling, batch transforms, pipeline stages.

Examples: fill template, run profiling pipeline, train with cross-validation, execute multi-step job, transcode batch.

**Tool count target: 5–7 tools.** Can be loaded alongside tier 1. Combined total ≤ 15 tools.

### Tier 3 — Advanced (layout, visual, export, optimization)

Tools that deal with visual layout, formatting, model optimization, export operations,
and complex cross-element interactions. These require more context to use correctly
and are rarely needed alongside tier 1 operations.

Examples: export to PDF, generate dashboard, hyperparameter tuning, model export, video rendering.

**Tool count target: 5–6 tools.** Load standalone — used in dedicated sessions.

### Decision tree for tier assignment

```
Does the tool read or write a single named node (row, cell, file, record, frame)?
  Yes → Tier 1

Does the tool apply a structured pipeline, rule, or multi-step transform?
  Yes → Tier 2

Does the tool change visual appearance, export format, or optimize a model/asset?
  Yes → Tier 3

Does the tool span all three concerns?
  → Split it into multiple tools, one per tier
```

---

## 8. Tool Count Discipline

### Hard limits by hardware target

| Target hardware | Max tools per server | Max tools loaded simultaneously |
|---|---|---|
| 4–6 GB VRAM (≤7B model) | 6 | 6 (one server only) |
| 8 GB VRAM (9B model) | 8 | 12 (tier 1 + tier 2) |
| 12–16 GB VRAM (14B model) | 10 | 16 (any two servers) |
| 24 GB+ VRAM (32B+ model) | 12 | 20 |

The general open-source target is **8 GB VRAM**. Design for 8 tools per server,
12 tools maximum loaded simultaneously.

### Why tool count matters

Every tool schema sits in the KV cache for the entire conversation. At 8 GB VRAM, ten tools consume ~8–10% of context before any user data arrives. Beyond tokens, models make correct tool selections reliably at ≤8 tools; errors increase noticeably at 15+.

**The rule: fewer tools, sharper tools.**

---

## 9. The Four-Tool Pattern

Every data or state-changing task follows this exact four-step loop. Encode this in
your tool design so the model is guided through it naturally.

```
LOCATE  →  INSPECT  →  PATCH  →  VERIFY
```

### Step 1: LOCATE

Find the node(s) that need changing without reading everything else.
Returns addresses, indices, IDs — zero actual content.

### Step 2: INSPECT

Read only the located node(s) to understand current state.
Returns one node in detail, bounded by size limits.

### Step 3: PATCH

Apply the targeted edit to only that node.
Returns a confirmation dict with what changed.

### Step 4: VERIFY

Read back only the edited node to confirm the change applied correctly.
Same read tool as Step 2 — model confirms result matches intent.

### Example — data analytics domain

```
User: "Fix the missing values in the revenue column of sales_q3.csv"

Round 1 (LOCATE):   search_columns(file="sales_q3.csv", has_nulls=True)
                    → {"columns": ["revenue", "discount"], "null_counts": {"revenue": 23}}

Round 2 (INSPECT):  read_column_stats(file="sales_q3.csv", column="revenue")
                    → {"mean": 4200, "median": 3800, "null_count": 23, "dtype": "float64"}

Round 3 (PATCH):    fill_nulls(file="sales_q3.csv", column="revenue", strategy="median")
                    → {"success": true, "filled": 23, "value_used": 3800, "backup": "..."}

Round 4 (VERIFY):   read_column_stats(file="sales_q3.csv", column="revenue")
                    → {"mean": 4190, "median": 3800, "null_count": 0, "dtype": "float64"}
```

### Anti-patterns that violate this pattern

- A tool that searches AND reads AND edits in one call → split into three
- A tool that returns the full dataset so the model can "find what it needs"
- A tool that writes without returning what changed
- A tool that trains a model and also evaluates and also exports in one call

---

## 10. Surgical Read Protocol

### The fundamental rule

A tool that returns data must return **only the data the model asked for**. Not
surrounding context. Not related data "that might be useful". Not the full parent
structure for convenience.

This is the most important performance decision in the entire server.

### Mandatory tool classes for every domain

**Index tool** — returns structure without content:

```python
# Returns keys, addresses, counts, metadata — zero actual content
get_dataset_schema()        # column names + dtypes + row count, not values
get_model_summary()         # model type + params + metrics, not weights
get_document_outline()      # heading text + indices, not body text
list_processes()            # PIDs + names, not memory maps
list_image_metadata()       # filenames + dimensions + format, not pixels
```

**Search tool** — scans content, returns matching addresses:

```python
# Returns matches with addresses — caller reads only those
search_columns(has_nulls=True)          # column names, not full columns
search_rows(where="revenue > 10000")    # row indices, not full rows
search_files(pattern="*.csv")           # file paths, not file contents
search_logs(level="ERROR")              # line numbers, not surrounding lines
```

**Bounded read tool** — reads a specific address with a hard size limit:

```python
# Returns exactly one node or a bounded slice
read_rows(file, start, end)             # bounded row range
read_column_stats(file, column)         # stats for one column, not all rows
read_model_metrics(model_path)          # metrics dict, not full predictions
read_log_range(path, start, end)        # bounded lines, hard cap enforced
```

### Return size limits by data type

Enforce these limits in the engine, not in the model.

| Data type | Default limit | 8 GB mode limit | Enforcement |
|---|---|---|---|
| DataFrame rows | 100 per call | 20 per call | Error if exceeded |
| DataFrame columns | 50 per call | 20 per call | Truncate with warning |
| Search results | 50 per call | 10 per call | `max_results` parameter |
| Log lines | 100 per call | 50 per call | Error if exceeded |
| List items (generic) | 100 per call | 40 per call | Truncate with flag |
| JSON object depth | 5 levels | 3 levels | Flatten deeper structures |
| Text paragraphs | 50 per call | 20 per call | Error if exceeded |
| Image array pixels | Never raw | Never raw | Always return stats/path |
| Model weights | Never raw | Never raw | Always return path + summary |

Every tool response that was limited must include:

```python
{
    "truncated": True,
    "returned": 20,
    "total_available": 5000,
    "hint": "Use read_rows(file, start, end) to read specific row ranges."
}
```

### The token_estimate field

Every tool response must include a rough token count of its own output:

```python
response["token_estimate"] = len(str(response)) // 4
```

This is for the model to budget remaining context window capacity.

---

## 11. Tool Schema Design

### Docstring length — the 80-character rule

Every `@mcp.tool()` docstring must be 80 characters or fewer. These are sent to the
model on every turn. They are not documentation for humans — they are selection cues.

```python
# Good — 55 characters, unambiguous
"""Profile dataset columns. Returns stats and null counts."""

# Good — 61 characters
"""Train classifier on CSV. Returns accuracy, F1, model path."""

# Bad — 98 characters
"""This tool analyzes the dataset and returns detailed statistical information
about each column including mean, median, and missing value counts."""
```

Test this in CI: `assert len(tool.__doc__) <= 80`.

### Parameter naming

Parameters are lowercase `snake_case` nouns that describe what they contain.

```python
# Correct
file_path: str
column_name: str
model_path: str
target_column: str
max_results: int
test_size: float
dry_run: bool

# Wrong — verb-first
get_file_path: str
target_col: str       # abbreviation

# Wrong — camelCase
filePath: str
columnName: str
```

### Allowed parameter types

Only use these types in tool function signatures:

- `str` — paths, names, addresses, text, enum values as strings
- `int` — indices, counts, limits, seeds
- `float` — ratios, thresholds, percentages
- `bool` — flags with sensible defaults
- `list[dict]` — only for patch op arrays
- `list[str]` — only for column lists, file lists, label lists

Never use:

- `Optional[T]` — use `T = None` instead
- `Union[T, S]` — split into two tools or use a discriminated string
- `Any` — always type precisely
- `dict` — too vague; model hallucinates arbitrary keys
- Custom Pydantic models in tool signatures
- `Enum` — use `str` with valid values documented in the docstring

### Enum values in docstrings

```python
@mcp.tool()
def fill_nulls(
    file_path: str,
    column_name: str,
    strategy: str,       # "mean", "median", "mode", "ffill", "bfill", "drop"
    dry_run: bool = False,
) -> dict:
    """Fill null values in column. strategy: mean median mode ffill bfill drop."""
```

### Smart inference

Where a tool must infer intent (chart type, aggregation, date format, delimiter), infer from evidence, expose an override parameter, and include what was inferred in the response.

### The dry_run parameter

Every write tool must have `dry_run: bool = False`. When `True`, the tool returns
exactly what it would change without changing anything. This is the primary
trust-building feature for new users running destructive operations.

```python
if dry_run:
    return {
        "success": True,
        "dry_run": True,
        "would_change": description_of_changes,
        "token_estimate": ...,
    }
```

---

## 12. Tool Annotations

FastMCP and the MCP protocol support tool annotations that help AI clients display
and reason about tools correctly. Always set these.

```python
from fastmcp import FastMCP

mcp = FastMCP("server-name")

@mcp.tool(
    annotations={
        "readOnlyHint": True,       # does not modify any state
        "destructiveHint": False,   # does not destroy data
        "idempotentHint": True,     # safe to call multiple times
        "openWorldHint": False,     # does not interact with external services
    }
)
def read_column_stats(file_path: str, column: str) -> dict:
    """Stats for one column: mean median std min max nulls unique top."""
    return engine.read_column_stats(file_path, column)
```

### Annotation rules by tool type

| Tool type | readOnlyHint | destructiveHint | idempotentHint | openWorldHint |
|---|---|---|---|---|
| Read / inspect / search | True | False | True | False |
| Write / patch (with snapshot) | False | False | False | False |
| Delete / drop rows | False | True | False | False |
| Network / scrape / download | False | False | False | True |
| Export / generate HTML | False | False | True | False |

`destructiveHint=True` should trigger an extra confirmation prompt in most AI
clients. Use it for `drop_column`, `delete_rows`, `purge_versions`.

---

## 13. The Patch Protocol

### When to use a patch protocol

Any tool that modifies structured data should accept a **list of operations** rather
than a single operation when the task naturally involves multiple changes. A dataset
with 5 cleaning steps should be processed in one `apply_patch` call with 5 ops, not
5 separate tool calls.

### Standard op array format

```python
[
    {
        "op": "fill_nulls",
        "column": "revenue",
        "strategy": "median"
    },
    {
        "op": "drop_duplicates",
        "subset": ["customer_id", "date"]
    },
    {
        "op": "rename_column",
        "from": "rev",
        "to": "revenue_usd"
    }
]
```

Rules:
- `"op"` is always the first key and always a **string**
- All other fields are operation-specific required fields
- Maximum 50 ops per batch
- Ops are applied sequentially
- **Validate entire array before creating any snapshot or modifying any file**

### Validate before snapshot — mandatory ordering

This is the most commonly violated rule in patch implementations:

```python
# WRONG — snapshot before validation; leaves orphaned .bak on bad op names
backup = snapshot(str(path))
for op in ops:
    if op.get("op") not in handler_map:
        return {"error": "Unknown op", "backup": backup}   # orphaned backup!

# CORRECT — validate all ops first, then snapshot only on confirmed valid input
unknown = [op.get("op") for op in ops if op.get("op") not in handler_map]
if unknown:
    return {"success": False, "error": f"Unknown ops: {unknown}"}  # no snapshot

backup = snapshot(str(path))   # only reached after full validation
```

Every failed validation call that creates a snapshot leaves a permanently orphaned
`.mcp_versions/*.bak` file. Over time this fills the user's disk. The fix is
unconditional: validate fully before touching the filesystem.

### Op naming convention

Op names are `verb_noun` snake_case:

```
fill_nulls        drop_duplicates     rename_column
replace_text      set_cell            insert_row
train_model       export_report       apply_transform
```

Allowed verbs: `fill`, `drop`, `rename`, `replace`, `set`, `insert`, `delete`,
`add`, `update`, `move`, `train`, `export`, `apply`, `restore`

---

## 14. Engine and Server Separation

### The mandatory split

Every server has exactly two files for logic:

**`engine.py`** — pure domain logic, zero MCP imports:

```python
# engine.py imports
from pathlib import Path
from shared.version_control import snapshot
from shared.patch_validator import validate_ops
from shared.platform_utils import get_max_rows, is_constrained_mode
# domain library imports (polars, sklearn, Pillow, psutil, etc.)

# engine.py does NOT import:
# from mcp import ...
# from fastmcp import ...
```

**`server.py`** — thin MCP wrapper, zero domain logic:

```python
from mcp.server.fastmcp import FastMCP
from . import engine

mcp = FastMCP("server-name")

@mcp.tool()
def tool_name(param: str) -> dict:
    """Short description under 80 chars."""
    return engine.tool_name(param)    # one line only

def main() -> None:
    mcp.run()
```

**The rule:** Any line that touches domain data belongs in `engine.py`. Any line
that touches the MCP protocol belongs in `server.py`. If a tool body in `server.py`
is more than two lines, it has logic that belongs in `engine.py`.

---

## 15. Engine Sub-Module Pattern

When `engine.py` grows beyond ~400–500 lines, split it into focused sub-modules.
The engine entry point becomes a thin router. **No single file should exceed
1,000 lines.** This is a hard limit enforced during code review.

### Sub-module layout

```
servers/data_advanced/
├── server.py              ← MCP wrapper (unchanged)
├── engine.py              ← thin router: imports from sub-modules, re-exports
├── _adv_helpers.py        ← shared imports, constants, utility functions
├── _adv_io.py             ← file loading, export, format conversion
├── _adv_transform.py      ← data cleaning, patching, aggregations
├── _adv_analysis.py       ← statistics, outlier detection, profiling
├── _adv_charts.py         ← chart generation (bar, pie, line, scatter, etc.)
├── _adv_dashboard.py      ← dashboard HTML assembly
└── _adv_report.py         ← EDA report HTML assembly
```

### Sub-module naming rules

- Prefix with `_{tier_abbr}_` to avoid name collisions (e.g. `_basic_`, `_medium_`,
  `_adv_`)
- Group by what the code does, not by what tool calls it
- Sub-modules have zero MCP imports (same rule as `engine.py`)
- Use relative imports within the package: `from ._adv_helpers import _error`

### The helpers sub-module pattern

Every server package has a `_{tier}_helpers.py` that centralizes all shared imports, constants (algorithm sets, directory names, limits), and private utility functions (`_error`, `_check_memory`, etc.) with an `__all__` re-export list.

### The thin router pattern

When `engine.py` is fully split, it becomes a thin router — just imports and
`__all__`:

```python
# engine.py — thin router (~30–50 lines)
"""my_server engine — domain logic. Zero MCP imports."""

from ._basic_helpers import _error          # only if used directly
from ._basic_train import train_classifier, train_regressor
from ._basic_predict import get_predictions, restore_version
from ._basic_inspect import inspect_dataset, read_column_profile

__all__ = [
    "inspect_dataset", "read_column_profile",
    "train_classifier", "train_regressor",
    "get_predictions", "restore_version",
]
```

Alternatively, `engine.py` can be a **partial router** — keeping small inline
functions (e.g., read-only inspect tools under ~50 lines each) while importing
larger functions from sub-modules. This is acceptable when it keeps engine.py
under 1,000 lines and avoids creating sub-modules with only one small function.

### File size guidelines

| File | Target lines | Hard limit |
|---|---|---|
| `engine.py` (thin router) | 30–50 | 1,000 |
| `engine.py` (partial router) | 200–400 | 1,000 |
| `_{tier}_helpers.py` | 150–500 | 1,000 |
| Other sub-modules | 150–800 | 1,000 |
| `server.py` | 50–150 | 300 |

Tests still import from `engine.py` — sub-module structure is invisible to tests.

### Module-level imports with optional-dependency flags

**Do not use lazy function-body imports for heavy libraries on Windows.**

The previous advice in this standard recommended lazy imports inside function bodies
for heavy dependencies (scipy, statsmodels, torch, etc.). That advice is **wrong on
Windows** and has been revised.

**Why function-body lazy imports are harmful on Windows:**

On Windows, the Defender real-time scanner inspects every `.pyc` file on first
access. Libraries like scipy and statsmodels have 200+ compiled modules. A lazy
import inside a function body means that on every server restart (LM Studio restarts
servers per session), the first call to that function triggers a multi-minute Defender
scan, appearing as a hang to the user.

**The correct pattern: module-level import with optional-dependency flag:**

```python
# At module level — pays the Defender scan cost once at server startup
# (which is before user interaction and therefore invisible to the user)
try:
    from scipy import stats as _scipy_stats
    from scipy.stats import linregress as _linregress
    _SCIPY_OK = True
except ImportError:
    _scipy_stats = None   # type: ignore
    _linregress = None    # type: ignore
    _SCIPY_OK = False

try:
    import statsmodels.api as _sm  # type: ignore[import-untyped]
    _STATSMODELS_OK = True
except ImportError:
    _sm = None   # type: ignore
    _STATSMODELS_OK = False
```

**Guard functions with `is not None` checks, not boolean flags:**

Pyright cannot narrow `None | module` type through a boolean variable. Use direct
`is not None` checks to get correct type narrowing:

```python
# Wrong — pyright cannot narrow through boolean flag
if _SCIPY_OK:
    result = _scipy_stats.shapiro(data)   # pyright: reportOptionalCall error

# Correct — pyright narrows through is not None
if _scipy_stats is not None:
    result = _scipy_stats.shapiro(data)   # pyright: OK

# Correct for early-exit guards
def my_tool(...) -> dict:
    if _sm is None or _vif is None:
        return {"success": False, "error": "statsmodels not installed",
                "hint": "Install: uv add statsmodels"}
    sm = _sm          # pyright now knows sm is not None
    vif = _vif
    # ... use sm and vif freely
```

**Exception: truly optional, large packages (geopandas, ydata_profiling, torch)**

Libraries that are optional domain extensions — not always installed, very large,
and not needed by most tools in the server — may still use lazy function-body
imports. The criterion is: if the library is absent, most tools still work normally.

```python
# Acceptable lazy import — geopandas is not always installed
def enrich_with_geo(file_path: str, geo_file_path: str, ...) -> dict:
    try:
        import geopandas as gpd
    except ImportError:
        return {"success": False, "error": "geopandas not installed",
                "hint": "Install: uv add geopandas"}
    ...
```

**Rule of thumb:**

| Library type | Import style |
|---|---|
| Core scientific (scipy, numpy, statsmodels, sklearn) | Module-level with flag |
| Always-needed domain lib (pandas, PIL, cv2) | Module-level unconditional |
| Optional domain extension (geopandas, torch, plotly) | Lazy in function body |
| Standard library (pathlib, json, datetime) | Module-level unconditional |

---

## 16. Return Value Contract

### Every tool returns a dict

No exceptions. Never return a plain string, list, `None`, or boolean.

```python
{"success": True, "op": "fill_nulls", ...}
{"success": False, "error": "...", "hint": "..."}
```

### Required fields in every response

| Field | Type | When required | Purpose |
|---|---|---|---|
| `"success"` | `bool` | Always | Model checks this first |
| `"op"` | `str` | On success | Confirms which operation ran |
| `"error"` | `str` | On failure | Human-readable failure reason |
| `"hint"` | `str` | On failure | Actionable recovery instruction |
| `"backup"` | `str` | After any write | Path to snapshot taken before write |
| `"progress"` | `list` | Always | Step-by-step execution log |
| `"dry_run"` | `bool` | When dry_run=True | Confirms simulation mode |
| `"token_estimate"` | `int` | Always | `len(str(response)) // 4` |
| `"truncated"` | `bool` | On bounded reads | Always explicit, never absent |

### What to include in write confirmations

```python
{
    "success": True,
    "op": "fill_nulls",
    "column": "revenue",
    "filled": 23,
    "value_used": 3800.0,
    "backup": ".mcp_versions/sales_q3_2026-03-25T14-30-00Z.bak",
    "progress": [...],
    "token_estimate": 87
}
```

Write tools confirm the write. Read tools read. Never return raw data arrays from a write tool.

---

## 17. Error Handling Contract

### Never raise exceptions to the caller

All exceptions are caught in `engine.py` and converted to error dicts.

```python
def train_classifier(file_path: str, target: str, model: str) -> dict:
    backup = None
    try:
        path = resolve_path(file_path)
        backup = snapshot(str(path))
        # ... do work ...
        return {"success": True, ...}
    except FileNotFoundError:
        return {
            "success": False,
            "error": f"File not found: {file_path}",
            "hint": "Check that file_path is absolute and the file exists.",
        }
    except MemoryError:
        return {
            "success": False,
            "error": "Insufficient RAM to load dataset.",
            "hint": "Use read_rows() with a bounded range or increase system RAM.",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "backup": backup,
            "hint": "Use restore_version to undo if a snapshot was taken.",
        }
```

### Standard error message patterns

```python
f"File not found: {path}"
f"Expected .csv file, got .{ext}"
f"Column '{name}' not found. Available: {', '.join(columns)}"
f"Insufficient RAM: need ~{required_gb:.1f} GB, available ~{available_gb:.1f} GB"
f"Unknown op: '{op}'. Allowed: {', '.join(allowed_ops)}"
```

### The hint field rules

The hint must complete the sentence "To fix this, ..." and must name a specific
tool to call or a specific value to check.

```python
# Bad hints
"hint": "Invalid input."
"hint": "Try again."

# Good hints
"hint": "Use inspect_dataset() first to verify column names and dtypes."
"hint": "Set device='cpu' if no GPU is available."
"hint": f"Available strategies: mean, median, mode, ffill, bfill, drop"
"hint": "Use read_rows(file, 0, 100) to preview data before patching."
```

---

## 18. Security Considerations

### Path traversal prevention

All file paths from tool parameters must be validated before use:

```python
def resolve_path(file_path: str, allowed_extensions: tuple[str, ...] = ()) -> Path:
    path = Path(file_path).resolve()
    try:
        path.relative_to(Path.home().resolve())    # reject paths outside home
    except ValueError:
        raise ValueError(f"Path outside allowed directory: {file_path}")
    if allowed_extensions and path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Extension {path.suffix!r} not allowed.")
    return path
```

Never use raw `file_path` strings in `open()`, `pd.read_csv()`, or subprocess calls
without resolving and validating first. Add `resolve_path()` to
`shared/file_utils.py`.

### Subprocess injection prevention

For servers that spawn subprocesses (FFmpeg, Tesseract, LibreOffice, etc.), never
pass user-provided strings directly into shell commands:

```python
# Wrong — shell injection risk
subprocess.run(f"ffmpeg -i {input_path} {output_path}", shell=True)

# Correct — argument list, no shell
subprocess.run(
    ["ffmpeg", "-i", str(input_path), str(output_path)],
    shell=False,
    capture_output=True,
    timeout=300,
)
```

Always set `shell=False`. Always pass an argument list. Always set `timeout`.
Always `capture_output=True` to avoid stdout leakage.

### Expression evaluation — no eval()

For servers that accept user-defined expressions (column calculations, filter
expressions, formula strings), never use `eval()` or `exec()`. Parse the expression
tree manually:

```python
# Wrong
result = eval(user_expression)

# Correct — parse and validate against allowed operations
ALLOWED_OPS = {"+", "-", "*", "/"}
result = _safe_eval_expr(user_expression, df.columns, ALLOWED_OPS)
```

Implement `_safe_eval_expr` in the engine using AST parsing with an allowlist of
operations.

### Sensitive data in responses

Never include connection strings, API keys, passwords, or full system paths in tool
responses. Use `Path(x).name` for file references in progress messages. Redact
credentials in error messages.

---

## 19. State and Version Control

### The snapshot rule

**Every tool that modifies persistent data must snapshot before writing.**

This applies to:
- Files on disk (datasets, documents, models, configs)
- Database records (include `before_state` in response)
- Generated outputs that took significant compute to produce

`snapshot()` in `shared/version_control.py` copies the file to `.mcp_versions/{stem}_{UTC_timestamp}{ext}.bak` and returns the backup path.

### Atomic snapshot implementation

Implement snapshot with temp-file + atomic rename to prevent partial backups:

```python
def snapshot(file_path: str) -> str:
    path = Path(file_path)
    versions_dir = path.parent / ".mcp_versions"
    versions_dir.mkdir(exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    backup_name = f"{path.stem}_{timestamp}.bak"
    backup_path = versions_dir / backup_name

    # Windows datetime resolution is coarser than microseconds — collision guard
    counter = 1
    while backup_path.exists():
        backup_name = f"{path.stem}_{timestamp}_{counter}.bak"
        backup_path = versions_dir / backup_name
        counter += 1

    # Write to temp in same directory, then atomic rename
    fd, tmp = tempfile.mkstemp(dir=versions_dir)
    try:
        os.close(fd)
        shutil.copy2(str(path), tmp)
        shutil.move(tmp, str(backup_path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return str(backup_path)
```

### Output path safety rule — never default to the input file

**Transform and write tools must never default `output_path` to the input file.**

The common pattern below is a defect — when `output_path` is omitted, the original
file is silently overwritten even though a snapshot was taken:

```python
# WRONG — original file overwritten by default
out = resolve_path(output_path) if output_path else path
df.to_csv(str(out), index=False)
```

The correct default is a derived sibling filename beside the input:

```python
# CORRECT — original file preserved by default
if output_path:
    out = resolve_path(output_path)
else:
    out = path.parent / f"{path.stem}_filtered{path.suffix}"
df.to_csv(str(out), index=False)
```

Choose a suffix that describes the operation: `_filtered`, `_merged`, `_imputed`,
`_reshaped`, `_features`, `_cleaned`, `_customized`, etc.

The original is only overwritten when the caller **explicitly** passes `output_path`
pointing back to the source file. In that case, `snapshot()` still fires as the
safety net.

**Always return `"output_path": str(out)` in the response dict** so the caller can
read the result without guessing the derived filename:

```python
result = {
    "success": True,
    "output_file": out.name,    # filename only
    "output_path": str(out),    # absolute path — callers must use this
    ...
}
```

**Audit pattern** — search for this anti-pattern in any engine:

```bash
grep -rn "if output_path else path" servers/
grep -rn "if out_path else path" servers/
```

Every hit is a potential silent data-loss bug.

### The companion state file pattern

For complex files, maintain a companion JSON state file:

```
sales_q3.csv
sales_q3.csv.mcp_state.json    ← companion
```

```json
{
    "version": 3,
    "file": "sales_q3.csv",
    "last_modified": "2026-03-25T14:30:00Z",
    "schema": {"revenue": "float64", "customer_id": "int64"},
    "known_stats": {"revenue": {"mean": 4190, "null_count": 0}},
    "patches": [
        {"version": 1, "ts": "2026-03-25T10:00Z", "ops": 2},
        {"version": 2, "ts": "2026-03-25T14:30Z", "ops": 1}
    ]
}
```

### Restore tool — mandatory in tier 1

Every tier 1 server must include `restore_version`:

```python
@mcp.tool()
def restore_version(file_path: str, timestamp: str) -> dict:
    """Restore file to a previous snapshot by timestamp."""
    return engine.restore_version(file_path, timestamp)
```

### Confirming explicit destructive writes

For operations with no undo (external API side effects, irreversible transforms),
add an explicit confirm parameter:

```python
def delete_all_nulls(file_path: str, confirm: bool = False) -> dict:
    if not confirm:
        return {
            "success": False,
            "error": "This operation permanently deletes rows. Pass confirm=True to proceed.",
            "hint": "Use dry_run=True first to preview what would be deleted.",
        }
```

---

## 20. Token Budget Discipline

### The VRAM → context window → token budget chain

```
GPU VRAM
  └→ Model weights occupy most of VRAM
       └→ Remaining VRAM = KV cache
            └→ KV cache size = effective context window
                 └→ Token budget per call = context / expected_turns
```

On 8 GB GPU with 9B model (Q4_K_M):
- Model weights: ~5.5 GB
- Available KV cache: ~1.7 GB
- Effective context: ~10,000–12,000 tokens
- Per-turn content budget: ~100–300 tokens after schema + history overhead

### Budget rules

1. Tool schemas: keep under 700 tokens total (≤8 tools, ≤80 char docstrings)
2. Read tool responses: under 500 tokens
3. Write confirmations: under 150 tokens
4. Never return raw arrays, pixel data, weight tensors, or full file contents

### The hardware mode flag

Every server reads a `MCP_CONSTRAINED_MODE` environment variable **at call time**,
not at import time:

```python
# shared/platform_utils.py
import os

def is_constrained_mode() -> bool:
    return os.environ.get("MCP_CONSTRAINED_MODE", "0") == "1"

def get_max_rows() -> int:
    return 20 if is_constrained_mode() else 100

def get_max_results() -> int:
    return 10 if is_constrained_mode() else 50

def get_max_depth() -> int:
    return 3 if is_constrained_mode() else 5
```

Reading at call time (not module import time) means:
- Test monkeypatching of `os.environ` works without reloading modules
- Environment changes after startup are honored
- CI can set `MCP_CONSTRAINED_MODE=1` in env and tests enforce smaller limits

The installer sets `MCP_CONSTRAINED_MODE=1` automatically on machines with ≤8 GB
VRAM. Never hardcode limits in engine functions — always call these helpers.

---

## 21. Hardware Tiers and Resource Constraints

### CPU-first execution principle

**MCP tools must run entirely on CPU.** GPU is used by the local LLM for inference
only — the MCP server never requires a GPU to function. This distinction is critical:

- The VRAM constraints below are about **LLM model capacity**, not about tool
  execution requirements
- All domain libraries (pandas, scikit-learn, XGBoost, Pillow, etc.) must work with
  their CPU builds — never require `cuda=True` or CUDA-specific packages
- `MCP_CONSTRAINED_MODE` controls response sizes and row limits, not compute paths
- A user with no GPU at all (CPU-only machine) must be able to run any MCP tool

This means:
- Do not import or depend on CUDA, ROCm, or Metal GPU libraries in any engine file
- Do not call `torch.cuda.is_available()` to decide whether to run
- If a domain genuinely requires a GPU (deep learning inference), document it
  explicitly as a domain exception and still provide a CPU fallback path

### Design for constrained — test on standard — document for high-end

Write code for the most constrained hardware and let users with more benefit
automatically through the absence of artificial limits.

### LLM model and context reference

These constraints are about the local LLM running in the AI client — they determine
how many tool schemas fit and how much context is available per turn.

| VRAM | Model family | Quant | Context | Max tools |
|---|---|---|---|---|
| 4 GB | 3–4B models | Q4_K_M | ~5K tokens | 5 |
| 6 GB | 7B models | Q4_K_M | ~7K tokens | 6 |
| 8 GB | 9B models | Q3_K_S | ~12K tokens | 8 |
| 12 GB | 9B models | Q8_0 | ~20K tokens | 10 |
| 16 GB | 14B models | Q4_K_M | ~24K tokens | 12 |
| 24 GB | 32B models | Q4_K_M | ~32K tokens | 15 |

### Resource-aware execution

For compute-heavy domains (ML training, video processing, large dataset profiling),
tools must check available resources before starting and fail fast with a helpful
message:

```python
import psutil

def check_memory(required_gb: float) -> dict | None:
    available = psutil.virtual_memory().available / 1e9
    if available < required_gb:
        return {
            "success": False,
            "error": f"Need ~{required_gb:.1f} GB RAM, only {available:.1f} GB available.",
            "hint": "Use a row-sampled subset with read_rows(file, 0, 10000) first.",
        }
    return None
```

### The README hardware statement

Include this in every MCP server README:

> **A note on local execution and context limits:**
> This server runs entirely on your hardware — no data leaves your machine. On 8 GB
> VRAM with a 9B model, your effective context window is approximately 10,000–12,000
> tokens. This server is designed to stay within that budget through surgical read
> tools. For best results, run one focused task per session, then start a fresh chat.
> Fewer loaded tools means more context for your actual work.

---

## 22. Progress Output

### The rule

Every tool response includes a `"progress"` array. Never print to stdout.
All visible output goes in the progress array.

```python
{
    "success": True,
    "progress": [
        {"icon": "✔", "msg": "Loaded sales_q3.csv",           "detail": "5,000 rows × 12 cols"},
        {"icon": "✔", "msg": "Detected 23 nulls in revenue",  "detail": "0.46% of column"},
        {"icon": "✔", "msg": "Filled with median",            "detail": "value: 3800.0"},
        {"icon": "✔", "msg": "Saved sales_q3.csv",            "detail": "snapshot created"},
    ],
    "token_estimate": 95
}
```

Use `ok / fail / info / warn / undo` from `shared/progress.py`. Never construct progress dicts by hand. Always use `Path(x).name` in messages — never full absolute paths.

---

## 23. Long-Running Operations and Async

Sync blocking is fine for operations under ~30 seconds. For longer operations, use `async def` tools with `asyncio.create_subprocess_exec` and an explicit `timeout`. Do not mix sync and async tool definitions without verifying FastMCP compatibility. Include `"elapsed_seconds"` in the response and intermediate `info()` progress entries for operations that take more than a few seconds.

---

## 24. Live State and Reload

For servers that edit files open in other applications, implement best-effort reload notification in `shared/live_edit.py` (AppleScript on macOS, COM/shadow file on Windows, poll on Linux). Never fail the main write operation because reload failed — return `info("File saved — reopen to see changes")` instead.

---

## 25. Operation Receipt Log

Every server that writes data maintains a persistent receipt log alongside modified
files:

```
sales_q3.csv
sales_q3.csv.mcp_receipt.json    ← receipt
```

```json
[
    {
        "ts": "2026-03-25T14:30:00Z",
        "tool": "fill_nulls",
        "args": {"column": "revenue", "strategy": "median"},
        "result": "filled 23 nulls",
        "backup": ".mcp_versions/sales_q3_2026-03-25T14-30-00Z.bak"
    }
]
```

### shared/receipt.py

```python
def append_receipt(file_path: str, tool: str, args: dict, result: str,
                   backup: str | None) -> None:
    """Append one record to receipt log. Never raises."""

def read_receipt_log(file_path: str) -> list[dict]:
    """Read full receipt log for a file."""
```

`append_receipt` must never raise — it wraps all I/O in try/except and silently
drops the record on failure rather than crashing the main operation.

Every tier 1 server includes a `read_receipt` tool:

```python
@mcp.tool()
def read_receipt(file_path: str) -> dict:
    """Read operation history for a file. Returns log entries."""
    return engine.read_receipt_log(file_path)
```

---

## 26. Output Generation Pattern

Some servers generate file outputs as their primary artifact: HTML reports, charts,
PDF exports, generated dashboards. This section defines the standard for these tools.

### The output generation contract

Output-generating tools must:
1. Accept an `output_path: str = ""` parameter — empty string means auto-generate
   beside the input file
2. Accept `open_after: bool = True` — auto-open in the default application after
   generating
3. Return `"output_path"` (absolute path) and `"output_name"` (filename only) in
   the response
4. Never stream raw bytes through the MCP channel — always write to disk and return
   the path

```python
@mcp.tool()
def generate_report(
    file_path: str,
    output_path: str = "",    # "" = auto-generate name beside input
    open_after: bool = True,  # open in browser/app after generation
    theme: str = "dark",      # "dark" | "light" | "device"
) -> dict:
    """Generate HTML report for dataset. Opens in browser."""
    return engine.generate_report(file_path, output_path, open_after, theme)
```

### Default output location — input file first

When `output_path=""`, use this priority order:

1. **Explicit path** — when the caller passes a non-empty `output_path`
2. **Same directory as input file** — when an input file is provided
3. **User's Downloads folder** — fallback when no input file context exists (pure generation tools)

Implement in `shared/file_utils.py`:

```python
from pathlib import Path

def get_default_output_dir(input_path: str | None = None) -> Path:
    """Return the default output directory. Input file's parent if provided, else ~/Downloads."""
    if input_path:
        p = Path(input_path).resolve()
        if p.parent.exists():
            return p.parent
    return Path.home() / "Downloads"
```

### Auto-naming convention

```python
def _resolve_output_path(
    input_path: Path | None,
    suffix: str,
    output_path: str,
    ext: str = ".html",
) -> Path:
    if output_path:
        return Path(output_path).resolve()
    base_dir = get_default_output_dir(str(input_path) if input_path else None)
    stem = input_path.stem if input_path else suffix
    return base_dir / f"{stem}_{suffix}{ext}"
```

Standard suffixes: `_eda`, `_dashboard`, `_report`, `_chart`, `_distribution`,
`_profile`.

### HTML output standards

For HTML outputs (charts, reports, dashboards):
- Use a shared `html_theme.py` module for CSS variables, viewport meta, and Plotly
  template
- Support dark/light/device themes via CSS custom properties
- Use responsive CSS with `rem` units and `clamp()` for fluid scaling — no hardcoded
  pixel breakpoints
- All charts must be `responsive: true` and `autosize: true` in their Plotly config
- Wrap wide tables in `<div style="overflow-x:auto">` to prevent horizontal overflow

### Offline-first Plotly — mandatory for HTML outputs

**Never embed Plotly.js inline** (`include_plotlyjs=True`). The inline bundle is
3.5 MB of JavaScript. On Windows, writing a 4 MB+ HTML file triggers Windows
Defender scanning on every save, causing 2-minute hangs.

**The correct pattern: copy Plotly once per output directory, use `"directory"` mode:**

```python
# shared/html_theme.py

import shutil
from pathlib import Path

def _ensure_plotly_js(output_dir: Path) -> str:
    """Copy plotly.min.js to output_dir once. Returns 'directory' or 'cdn'."""
    target = output_dir / "plotly.min.js"
    if target.exists():
        return "directory"          # already there — reuse
    try:
        import plotly as _plotly
        src = Path(_plotly.__file__).parent / "package_data" / "plotly.min.js"
        if src.exists():
            shutil.copy2(str(src), str(target))
            return "directory"      # local file copy succeeded
    except Exception:
        pass
    return "cdn"                    # silent fallback to CDN


def save_chart(fig, output_path: Path, ...) -> None:
    include_js = _ensure_plotly_js(output_path.parent)
    html = fig.to_html(
        include_plotlyjs=include_js,    # "directory" → <script src="plotly.min.js">
        full_html=True,
        config={"responsive": True, "displayModeBar": True},
    )
    atomic_write_text(str(output_path), html)
```

**Why this works:**
- First chart in a directory: copies `plotly.min.js` (~3.5 MB, <100 ms), writes small HTML
- Subsequent charts in same directory: reuse the existing file, only write small HTML
- HTML file stays under 200 KB — no Defender trigger
- Falls back silently to CDN if the plotly package file is missing
- Offline capable: once the JS is copied, all charts work without internet

### Opening files after generation

```python
def _open_file(path: Path) -> None:
    """Open generated file in default app. Best-effort, never fails."""
    try:
        webbrowser.open(f"file://{path.resolve()}")
    except Exception:
        try:
            if sys.platform == "win32":
                subprocess.Popen(["start", str(path.resolve())], shell=True)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path.resolve())])
            else:
                subprocess.Popen(["xdg-open", str(path.resolve())])
        except Exception:
            pass   # non-critical; report was still generated
```

---

## 27. Shared Data I/O Standards

### The single CSV reader rule

**Never call `pd.read_csv()` directly in server or engine code.** Route all CSV
reads through `shared/file_utils.read_csv()`. This single entry point handles:

1. **Encoding fallback chain** — utf-8 → utf-8-sig (BOM) → cp1252 (Windows/Excel) → latin-1
2. **Bad-line tolerance** — on tokenization errors (mismatched field counts from
   unescaped commas), retries with `on_bad_lines='skip'`
3. **Column name normalization** — strips leading/trailing whitespace from column names
4. **Consistent low_memory handling** — always `low_memory=False`

```python
# shared/file_utils.py

_ENCODING_FALLBACKS = ("utf-8-sig", "cp1252", "latin-1")

def read_csv(
    file_path: str,
    encoding: str = "utf-8",
    separator: str = ",",
    max_rows: int = 0,
) -> pd.DataFrame:
    """Read CSV with automatic encoding fallback and bad-line tolerance."""
    kwargs: dict = {"sep": separator, "low_memory": False}
    if max_rows > 0:
        kwargs["nrows"] = max_rows

    def _try_encs(extra: dict) -> pd.DataFrame:
        kw = {**kwargs, **extra}
        try:
            return pd.read_csv(file_path, encoding=encoding, **kw)
        except UnicodeDecodeError:
            pass
        for enc in _ENCODING_FALLBACKS:
            if enc == encoding:
                continue
            try:
                return pd.read_csv(file_path, encoding=enc, **kw)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(file_path, encoding="latin-1", **kw)

    try:
        df = _try_encs({})
    except Exception as exc:
        if "tokeniz" in str(exc).lower() or "field" in str(exc).lower():
            df = _try_encs({"on_bad_lines": "skip"})   # skip malformed rows
        else:
            raise

    df.columns = df.columns.str.strip()
    return df
```

**Why this matters:** A CSV from Excel may have a UTF-8 BOM. A CSV from a legacy
system may be cp1252. A CSV with a free-text field may have an unescaped comma on
one row. Any of these will hard-fail a bare `pd.read_csv()` call. The shared
reader handles all three silently.

### Numeric coercion before aggregation

CSV files frequently have numeric columns read as string dtype (from mixed content,
leading spaces, or non-numeric sentinel values). Always coerce before numeric
operations:

```python
# Wrong — crashes on string-typed numeric column
grouped = df.groupby(group_by)[agg_column].mean()

# Correct — coerce first, warn on NaN-producing values
numeric_funcs = {"sum", "mean", "min", "max"}
if agg_func in numeric_funcs:
    df[agg_column] = pd.to_numeric(df[agg_column], errors="coerce")
    non_numeric = int(df[agg_column].isna().sum())
    if non_numeric:
        progress.append(warn(
            f"Coerced '{agg_column}' to numeric",
            f"{non_numeric} non-numeric values → NaN"
        ))

grouped = df.groupby(group_by)[agg_column].agg(agg_func)
```

Apply this pattern in every function that performs `mean`, `sum`, `min`, `max`,
`std`, or any numeric aggregation on a user-supplied column name.

### Date parsing — always use format="mixed"

Never parse dates with a single fixed format string or without `format=`:

```python
# Wrong — fails on mixed date formats; dateutil fallback is slow row-by-row
df[date_col] = pd.to_datetime(df[date_col])

# Wrong — fails if even one row has a different format
df[date_col] = pd.to_datetime(df[date_col], format="%Y-%m-%d")

# Correct — vectorised C parser, handles mixed formats, coerces unparseable to NaT
df[date_col] = pd.to_datetime(df[date_col], format="mixed", dayfirst=False, errors="coerce")
```

`format="mixed"` uses pandas' fast C parser while tolerating per-row format
variation. `dayfirst=False` ensures ambiguous dates like `01/02/03` are read as
MM/DD/YY (US convention) rather than DD/MM/YY. `errors="coerce"` turns unparseable
values into NaT rather than raising.

### Atomic file writes

Never write output files directly — always temp-file + rename:

```python
# shared/file_utils.py
def atomic_write_text(path: str, content: str, encoding: str = "utf-8") -> None:
    target = Path(path)
    fd, tmp = tempfile.mkstemp(dir=target.parent, suffix=target.suffix)
    try:
        with os.fdopen(fd, "w", encoding=encoding) as f:
            f.write(content)
        shutil.move(tmp, str(target))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
```

---

## 28. LLM Input Resilience

Local LLMs produce inconsistent argument formatting. Unlike API calls where the
caller controls the schema, an LLM working with natural language instructions will
frequently use alternate key names, nest parameters incorrectly, or omit required
fields. Tools must be resilient to these patterns.

### The dual-key pattern

Many LLM-generated arguments use alternate key names for the same concept. Accept
both spellings:

```python
# In filter/condition dicts — LLMs use both "op" and "operator" interchangeably
op = cond.get("op", "") or cond.get("operator", "")

# In patch ops — accept both "strategy" and "method"
strategy = op.get("strategy", "") or op.get("method", "")
```

Document the canonical key name in the docstring but accept the alternate silently.
Do not raise an error for alternate spellings — the LLM is being helpful, not wrong.

### The op-coercion pattern

LLMs sometimes nest parameters inside the `"op"` key instead of alongside it:

```json
// LLM produced (wrong):
{"op": {"column": "price", "dtype": "float"}, "patch": true}

// Expected (correct):
{"op": "cast_column", "column": "price", "dtype": "float"}
```

Detect and repair this before validation:

```python
# Distinctive parameter sets that uniquely identify each op
_OP_SIGNATURES: list[tuple[frozenset[str], str]] = [
    (frozenset({"dtype"}),                "cast_column"),
    (frozenset({"strategy"}),             "fill_nulls"),
    (frozenset({"mapping"}),              "replace_values"),
    (frozenset({"expression"}),           "add_column"),
    (frozenset({"method", "lower", "upper"}), "cap_outliers"),
    (frozenset({"subset"}),               "drop_duplicates"),
]

def _coerce_op(raw: dict) -> dict:
    """Normalise a malformed op dict so 'op' is always a string."""
    op_val = raw.get("op", "")
    if isinstance(op_val, str) and op_val:
        return raw  # already correct

    # Extract params from the nested dict or top-level keys
    if isinstance(op_val, dict):
        params = {**op_val}
        for k, v in raw.items():
            if k not in ("op", "patch"):
                params.setdefault(k, v)
    else:
        params = {k: v for k, v in raw.items() if k not in ("op", "patch")}

    # Infer op name from distinctive params
    param_keys = frozenset(params.keys())
    inferred = ""
    for sig_keys, op_name in _OP_SIGNATURES:
        if sig_keys & param_keys:
            inferred = op_name
            break

    return {"op": inferred, **params}


# Apply before any validation:
ops = [_coerce_op(o) for o in ops]
```

The signature table maps distinctive parameter keys to op names. `dtype` uniquely
identifies `cast_column`; `strategy` uniquely identifies `fill_nulls`; etc.
If inference fails (no distinctive params), the op passes through unchanged and
fails at the validation stage with a clear error message.

### Type-safe field extraction

When extracting fields from LLM-provided dicts, always guard against wrong types,
not just missing keys:

```python
# Wrong — crashes if LLM passes "op" as a dict (unhashable type)
handler = handler_map.get(op.get("op", ""))

# Correct — validate type before use
op_name = op.get("op", "")
if not isinstance(op_name, str):
    return {
        "success": False,
        "error": f"'op' must be a string, got {type(op_name).__name__}",
        "hint": f"Example: {{\"op\": \"cast_column\", \"column\": \"price\", \"dtype\": \"float\"}}",
    }
```

### LLM formatting mistake reference

These are the most common mistakes local LLMs make with tool arguments:

| Mistake | Example | Correct fix |
|---|---|---|
| Nested params in "op" key | `{"op": {"col": "x", "dtype": "float"}}` | `_coerce_op()` |
| Wrong key name | `{"operator": "contains"}` | Accept both keys |
| String value for numeric param | `{"max_rows": "100"}` | `int()` coerce |
| List wrapped in another list | `{"columns": [["a", "b"]]}` | Flatten one level |
| Dict value for string param | `{"file_path": {"path": "/data/f.csv"}}` | Error with example |
| Missing required key entirely | `{"column": "x"}` (no "op") | `_coerce_op()` inference |

Build coercion and dual-key acceptance for the first three patterns into every
pipeline tool. The last three warrant a clear error with a correct usage example
rather than silent repair.

---

## 29. Testing Standards

### Test engine, not server

Tests import and call `engine.py` directly. Never spin up an MCP server process.

```python
# Correct
from servers.data_basic.engine import fill_nulls, search_columns

def test_fill_nulls(tmp_path, csv_fixture):
    f = tmp_path / "sales.csv"
    shutil.copy(csv_fixture, f)
    result = fill_nulls(str(f), "revenue", "median")
    assert result["success"] is True
    assert result["filled"] == 23
    assert ".mcp_versions" in result["backup"]
```

### Real fixture data

Fixtures must include real-world messiness. Required categories:
- `simple` — clean data, minimal edge cases
- `messy` — nulls, type mismatches, encoding issues, duplicate rows
- `large` — enough rows to test truncation and constrained mode

### What to test for every write operation

1. **Success** — operation completes, `"success": True`
2. **Content correct** — read back the written node, verify content
3. **Snapshot created** — `.mcp_versions/` has a new `.bak` file
4. **Backup in response** — `"backup"` key present
5. **Dry run** — `dry_run=True` returns `"would_change"` without modifying file
6. **Progress present** — `"progress"` array in response
7. **Wrong file type** — error dict with correct hint
8. **File not found** — error dict with correct hint
9. **Index/column out of range** — error dict with available options in hint
10. **Constrained mode** — `MCP_CONSTRAINED_MODE=1` enforces smaller limits
11. **No orphaned snapshot on validation failure** — invalid ops must NOT create .bak files

### Coverage requirements

| Module | Minimum coverage |
|---|---|
| `shared/` | 100% |
| `engine.py` | ≥ 90% |
| Error paths | All documented conditions tested |
| Happy paths | All tools tested |

### CI must run on all three platforms

```yaml
strategy:
  fail-fast: false
  matrix:
    os: [ubuntu-22.04, macos-latest, windows-latest]
```

Use `macos-latest` (not `macos-13`). Set `fail-fast: false` so all platforms run
even if one fails — you need to see all failures, not just the first.

### Cross-platform test pitfalls

**Windows `tmp_path` is under home:** On Windows CI, pytest's `tmp_path` resolves
to a directory under the user's home (e.g., `C:\Users\runneradmin\AppData\Local\Temp\...`).
This means `resolve_path()` will NOT reject it as "outside home directory". Tests
that check path-traversal rejection must use a truly outside-home path:

```python
def test_path_outside_home(self):
    import sys
    outside = "/etc/outside.csv" if sys.platform != "win32" else "C:\\outside.csv"
    r = some_tool(outside)
    assert r["success"] is False
```

**macOS native libraries:** Tests that import XGBoost, LightGBM, or other C++
libraries will fail on macOS unless `libomp` is installed. See §36 for the CI fix.

---

## 30. Cross-Platform Compatibility

### The path rule — pathlib everywhere

```python
# Wrong
path = base_dir + "/" + filename

# Correct
path = Path(base_dir) / filename
```

### Line endings

```
# .gitattributes
* text=auto eol=lf
*.bat text eol=crlf
*.cmd text eol=crlf
```

### Shell scripts — POSIX sh, not bash

`install.sh` must use `#!/bin/sh` and POSIX-compatible syntax.

### stdout is the MCP protocol channel

Never write to stdout in any engine or server module. Any `print()` statement
corrupts the MCP stdio channel.

```python
# Wrong
print("Processing file...")

# Correct — all logs go to stderr
import logging
logger = logging.getLogger(__name__)
logger.debug("Processing file...")
```

Configure in `server.py`:

```python
import sys, logging
logging.basicConfig(stream=sys.stderr, level=logging.WARNING)
```

### macOS native library dependencies

C++ libraries that use OpenMP (XGBoost, LightGBM, etc.) require `libomp` on
macOS. This is installed via `brew install libomp`. Without it, Python `import`
fails with `Library not loaded: @rpath/libomp.dylib`. The CI workflow must
include this step for macOS runners — see §36.

### Windows long paths

```python
if sys.platform == "win32" and len(str(path)) > 200:
    path = Path("\\\\?\\" + str(path.resolve()))
```

### Windows Defender and large file writes

Windows Defender's real-time scanner checks files on write. Files larger than ~1 MB
trigger a noticeable scan delay (seconds to minutes). Mitigations:

- **HTML output:** Never embed large JS bundles inline; use offline-first Plotly
  pattern (§26) to keep HTML under 200 KB
- **Snapshot files:** Write to temp then rename (atomic); Defender scans the final
  target, not the temp file during write
- **Module imports:** Use module-level imports (§15) so Defender scans `.pyc` files
  at server startup, not during user interaction

### Atomic file writes

```python
import tempfile, shutil
with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, dir=path.parent) as tmp:
    # write to tmp
    tmp_path = tmp.name
shutil.move(tmp_path, path)
```

---

## 31. Multi-Client Compatibility

Server code is identical regardless of AI client. The only difference is the config
file location. `mcp_config_writer.py` in `install/` handles client differences.
Standard mcp.json entry format is defined in §33.

---

## 32. Transport Modes

### Every server supports two modes

**stdio** (default) — for local AI clients:

```
uv run --directory servers/my_server my-server
```

**HTTP** — for remote or multi-user access:

```
uv run --directory servers/my_server my-server --transport http --port 8765
```

```python
def main() -> None:
    # stdio (default) or HTTP
    if args.transport == "http":
        mcp.run(transport="streamable-http", host="127.0.0.1", port=args.port, path="/mcp")
    else:
        mcp.run()
```

HTTP auth tokens must be generated by the installer (32+ random hex chars), stored in config, never hardcoded.

---

## 33. Installation and Distribution

### The self-updating mcp.json pattern

MCP servers use a **self-updating mcp.json** entry: the AI client's config file
contains the full bootstrap command. On every launch it clones the repo if missing,
pulls the latest, installs dependencies, and starts the server — no separate
install step needed.

This is the primary install mechanism. `install.sh` / `install.bat` exist as
convenience scripts but the mcp.json pattern is the canonical path.

### Standard install path

```
Windows:  %USERPROFILE%\.mcp_servers\{REPO_NAME}
macOS:    ~/.mcp_servers/{REPO_NAME}
Linux:    ~/.mcp_servers/{REPO_NAME}
```

Always clone into `.mcp_servers/` in the user's home directory. Never ask the user
to choose an install location.

### Standard mcp.json entry — Windows (PowerShell)

```json
{
  "mcpServers": {
    "{server_name}": {
      "command": "powershell",
      "args": [
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command",
        "$d = Join-Path $env:USERPROFILE '.mcp_servers\\{REPO_NAME}'; $g = Join-Path $d '.git'; if (!(Test-Path $g)) { if (Test-Path $d) { Remove-Item -Recurse -Force $d }; git clone https://github.com/{owner}/{REPO_NAME}.git $d --quiet } else { Set-Location $d; git fetch origin --quiet; git reset --hard FETCH_HEAD --quiet }; Set-Location (Join-Path $d 'servers\\{tier}'); uv sync --quiet; uv run python server.py"
      ],
      "env": { "MCP_CONSTRAINED_MODE": "0" },
      "timeout": 600000
    }
  }
}
```

### Standard mcp.json entry — macOS / Linux (bash)

```json
{
  "mcpServers": {
    "{server_name}": {
      "command": "bash",
      "args": [
        "-c",
        "d=\"$HOME/.mcp_servers/{REPO_NAME}\"; if [ ! -d \"$d/.git\" ]; then rm -rf \"$d\"; git clone https://github.com/{owner}/{REPO_NAME}.git \"$d\" --quiet; else cd \"$d\" && git fetch origin --quiet && git reset --hard FETCH_HEAD --quiet; fi; cd \"$d/servers/{tier}\"; uv sync --quiet; uv run python server.py"
      ],
      "env": { "MCP_CONSTRAINED_MODE": "0" },
      "timeout": 600000
    }
  }
}
```

### mcp.json rules

- **Clone guard:** check for `.git` subfolder, not just the directory. A directory
  without `.git` means a broken partial clone — remove it before re-cloning.
- **Update method:** `git fetch origin --quiet; git reset --hard FETCH_HEAD` — not
  `git pull`. Pull fails on detached HEAD or dirty state; fetch + reset never does.
- **Dep sync:** `uv sync --quiet` runs on every launch. JIT install means users
  always have the right dependencies without a separate install step.
- **Env var:** always `MCP_CONSTRAINED_MODE` — never project-specific names.
- **Timeout:** always `600000` (10 minutes) to cover first-run clone + install.
- **No `pip install`:** uv handles everything. Never call `pip` in the launch command.

### First-run pre-install (README recommendation)

The first launch installs all dependencies, which takes 2–5 minutes. To avoid the
60-second LM Studio connection timeout, recommend running this once in a terminal
before connecting:

```powershell
# Windows — pre-install
$d = Join-Path $env:USERPROFILE '.mcp_servers\{REPO_NAME}'
if (!(Test-Path $d)) { git clone https://github.com/{owner}/{REPO_NAME}.git $d }
Set-Location $d; uv sync
```

```sh
# macOS / Linux — pre-install
d="$HOME/.mcp_servers/{REPO_NAME}"
[ ! -d "$d" ] && git clone https://github.com/{owner}/{REPO_NAME}.git "$d"
cd "$d" && uv sync
```

If the user skips this and LM Studio times out: press **Restart** in the MCP Servers
panel — it will reconnect and complete the install on the second attempt.

### mcp_config_writer.py rules

For projects that include an automated config writer:

- Parse existing config with `json5` (handles comments and trailing commas)
- Append-only — never modify or remove existing entries
- Idempotent — safe to run twice
- Write with `json.dumps()` — strict valid JSON output
- Atomic write (temp file + rename)
- Use the standard mcp.json entry format above (PowerShell for Windows, bash for
  macOS/Linux)

### AI client config file locations

| Client | Config (macOS) | Config (Windows) |
|---|---|---|
| LM Studio | `~/Library/Application Support/LM Studio/mcp.json` | `%APPDATA%\LM Studio\mcp.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` |

---

## 34. Naming Conventions

### Server directories

```
servers/{domain}_{tier}/    # data_basic, ml_medium, office_advanced, media_basic
```

### Python identifiers

```python
# Functions — snake_case verb
read_dataset()
apply_patch()
train_classifier()

# Classes — PascalCase
PatchValidator
VersionControl

# Constants — UPPER_SNAKE_CASE
MAX_ROWS = 100
DEFAULT_TEST_SIZE = 0.2

# Private helpers — leading underscore
_apply_single_op()
_resolve_strategy()

# Optional-dependency module references — leading underscore + _OK flag
_scipy_stats = None   # type: ignore
_SCIPY_OK = False
```

### MCP tool function names — verb_noun

```
read_dataset        list_columns        search_rows
fill_nulls          drop_duplicates     rename_column
train_classifier    export_model        apply_patch
restore_version     read_receipt        inspect_dataset
```

Allowed verbs: `read`, `list`, `search`, `get`, `inspect`, `set`, `fill`, `drop`,
`rename`, `replace`, `insert`, `delete`, `add`, `update`, `move`, `train`, `export`,
`apply`, `restore`, `run`, `generate`


---

## 35. Dependency Policy

### Approved licenses

- MIT, Apache 2.0, BSD 2-Clause / 3-Clause, ISC, PSF

**Not permitted:** GPL / LGPL, commercial / proprietary, unlicensed

### Vetting checklist before adding any library

- License is in the approved list
- Last release within 12 months
- No known CVEs via `uv audit`
- Does not pull in an unnecessarily large dependency tree
- No existing approved alternative
- Pinned in `pyproject.toml` with minimum version (`>=x.y.z`)

### Required dev dependencies

Every project must include these in `[dependency-groups] dev`:

```toml
[dependency-groups]
dev = [
    "pytest>=9.0",
    "ruff>=0.9",
]
```

`ruff` handles both linting and formatting. No need for `black`, `isort`, `flake8`,
or `pylint` — ruff replaces all of them.

### Prohibited libraries

```
win32com / pywin32     — Windows only
Spire.*                — commercial license
Aspose.*               — commercial license
Any cloud SDK used as primary execution engine (boto3 for ML, google-cloud-*, etc.)
```

---

## 36. CI/CD Requirements

### CI workflow (`ci.yml`)

Name the file `ci.yml` (not `test.yml`). Trigger on all pushes and PRs.

```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:
    branches: ["**"]

jobs:
  test:
    name: Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-22.04, macos-latest, windows-latest]

    env:
      MCP_CONSTRAINED_MODE: "1"
      PYTHONPATH: "."

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4      # always v4 — not v3
        with:
          python-version: "3.12"

      - name: Install native dependencies (macOS)
        if: runner.os == 'macOS'
        run: brew install libomp
        # Required for XGBoost, LightGBM, and other C++ libraries
        # that depend on OpenMP. Without this, import fails with
        # "Library not loaded: @rpath/libomp.dylib"

      - name: Install dependencies
        run: uv sync --frozen

      - name: Lint
        run: uv run ruff check .

      - name: Format check
        run: uv run ruff format --check .

      - name: Type check
        run: uv run pyright servers/ shared/

      - name: Verify tool docstrings
        run: uv run python verify_tool_docstrings.py

      - name: Run tests
        run: uv run python -m pytest tests/ -q --tb=short
```

### Critical CI lessons learned

**`PYTHONPATH: "."`** is required so that `shared/` imports resolve correctly
when tests are run from the repo root. Without it, `from shared.progress import ok`
fails on CI even when it works locally.

**macOS runner names:** Use `macos-latest` — not `macos-13`. GitHub Actions
deprecated specific macOS version tags. Using `macos-13` causes the error
`The configuration 'macos-13-us-default' is not supported`.

**macOS native libraries:** XGBoost, LightGBM, and other C++ libraries that use
OpenMP require `brew install libomp` on macOS runners. Add this as a conditional
step (`if: runner.os == 'macOS'`).

**Notebook exclusion:** If the repo contains Jupyter notebooks (`.ipynb`), exclude
them from ruff in `pyproject.toml`:

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
exclude = ["*.ipynb"]
```

Without this, ruff treats notebook cells as Python source and reports hundreds of
false-positive import ordering errors. Do **not** rely on a CLI flag (`--exclude`);
configure it in `pyproject.toml` so it applies to both local and CI runs.

**`pyright` on sub-modules:** When using the sub-module pattern (§15), ensure
`pyright` covers the full `servers/{name}/` directory, which includes
`_adv_helpers.py`, `_adv_charts.py`, etc.

**`pyright` and optional-dependency flags:** Pyright cannot narrow `None | module`
through a boolean variable. Use `is not None` checks, not `if _SCIPY_OK:` boolean
flags, when calling optional-dependency functions. See §15 for the full pattern.

### Release workflow (`release.yml`)

Trigger on version tags (`v*`). Run the full CI matrix first, then create a
GitHub release with auto-generated changelog.

```yaml
name: Release

on:
  push:
    tags:
      - "v*"

permissions:
  contents: write

jobs:
  ci:
    name: Test (${{ matrix.os }})
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-22.04, macos-latest, windows-latest]

    env:
      MCP_CONSTRAINED_MODE: "1"
      PYTHONPATH: "."

    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          python-version: "3.12"
      - name: Install native dependencies (macOS)
        if: runner.os == 'macOS'
        run: brew install libomp
      - run: uv sync --frozen
      - run: uv run ruff check .
      - run: uv run ruff format --check .
      - run: uv run pyright servers/ shared/
      - run: uv run python verify_tool_docstrings.py
      - run: uv run python -m pytest tests/ -q --tb=short

  release:
    name: Create Release
    needs: ci
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - name: Extract tag
        id: tag
        run: echo "version=${GITHUB_REF#refs/tags/}" >> "$GITHUB_OUTPUT"
      - name: Generate changelog
        id: changelog
        run: |
          PREV_TAG=$(git tag --sort=-creatordate | head -2 | tail -1)
          if [ -z "$PREV_TAG" ] || [ "$PREV_TAG" = "${{ steps.tag.outputs.version }}" ]; then
            LOG=$(git log --oneline --no-decorate | head -50)
          else
            LOG=$(git log --oneline --no-decorate "${PREV_TAG}..HEAD" | head -50)
          fi
          echo "$LOG" > /tmp/changelog.txt
      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: ${{ steps.tag.outputs.version }}
          name: ${{ steps.tag.outputs.version }}
          body_path: /tmp/changelog.txt
          draft: false
          prerelease: ${{ contains(steps.tag.outputs.version, '-rc') || contains(steps.tag.outputs.version, '-beta') || contains(steps.tag.outputs.version, '-alpha') }}
          generate_release_notes: true
```

Supports prerelease tags automatically: `v1.0.0-rc1`, `v1.0.0-beta`, etc.

### Ruff configuration in `pyproject.toml`

```toml
[tool.ruff]
line-length = 120
target-version = "py312"
exclude = ["*.ipynb"]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "UP"]
```

Include `ruff>=0.9` as a dev dependency so all contributors use the same version.

### verify_tool_docstrings.py

```python
import ast, pathlib, sys

errors = []
for f in pathlib.Path("servers").rglob("server.py"):
    tree = ast.parse(f.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            has_tool = any(
                (isinstance(d, ast.Attribute) and d.attr == "tool") or
                (isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                 and d.func.attr == "tool")
                for d in node.decorator_list
            )
            if has_tool:
                doc = ast.get_docstring(node) or ""
                if len(doc) > 80:
                    errors.append(f"{f}:{node.lineno} {node.name}: {len(doc)} chars > 80")

if errors:
    print("\n".join(errors))
    sys.exit(1)
```

---

## 37. Documentation Requirements

### README.md required sections

Use this exact section order. Every MCP server README must follow this structure.

```
# {Project Name}

{One-line description}: self-hosted, no cloud APIs, no API keys.

## Important: File Path Only          ← always present for data/file tools
{warning block about not using attachment buttons}

## Features
- **{N} tools** across {T} tiers: basic ({n1}), medium ({n2}), advanced ({n3})
- LOCATE → INSPECT → PATCH → VERIFY workflow
- Automatic version control / operation receipt logging
- Constrained mode for lower-memory machines
- {domain-specific features}

## Quick Install (LM Studio)

> **Tested on Windows 11** with LM Studio 0.4.x and uv 0.5+.

### Requirements

- **Git** — `git --version`
- **Python 3.12 or higher** — `python --version`
- **uv** — `uv --version` (install guide link)
- **LM Studio** with a model that supports tool calling (Gemma 4, Qwen 3.5, etc.)
- {any domain-specific prerequisite}

### Platform Support

| Platform | Status |
|---|---|
| Windows | Tested — real-world verified (Windows 11) |
| macOS   | Untested — CI/CD pipeline passes |
| Linux   | Untested — CI/CD pipeline passes |

> Real-world usage has only been verified on Windows. macOS and Linux are supported
> by design and pass the automated CI pipeline, but have not been tested by hand.

### First Run

The first launch clones the repo and installs dependencies (~{size}).
Subsequent launches are instant.

> **Pre-install recommended:** To avoid the 60-second LM Studio connection timeout
> on first launch, run this once in PowerShell before connecting:
> ```powershell
> $d = Join-Path $env:USERPROFILE '.mcp_servers\{REPO_NAME}'
> if (!(Test-Path $d)) { git clone {REPO_URL} $d }
> Set-Location $d; uv sync
> ```
> If you skip this step and LM Studio times out, press **Restart** in the MCP
> Servers panel — it will reconnect immediately.

### Steps

1. Open LM Studio → **Developer** tab (`</>` icon) or find via **Integrations**
2. Find **mcp.json** or **Edit mcp.json** → click to open
3. Paste this config:

{mcp.json block — Windows PowerShell format from §33}

4. Wait for the blue dot next to each server
5. Start chatting — the model will see all {N} tools

### macOS / Linux

Replace `powershell` / `args` with:

{mcp.json block — bash format from §33}

Repeat for each tier, adjusting the server directory in the path.

## Available Tools          ← tier tables with tool name, purpose
## Configuration            ← MCP_CONSTRAINED_MODE, env variable table
## Uninstall                ← remove from client + delete directory
## Architecture             ← directory tree
## Development              ← local test commands
## License
```

### README rules

- **"Tested on Windows 11"** — always present; macOS/Linux CI-only caveat always present
- **Python 3.12 or higher** — exact wording; never "Python 3.x+" or "Python >= 3.11"
- **No hardware specs beyond RAM** — never mention GPU model, CPU model, or disk specs
- **No library lists** — features list mentions capabilities, not library names
- **LM Studio timeout note** — always present, always same wording about Restart button
- **uv install guide link** — always `https://docs.astral.sh/uv/getting-started/installation/`

### CLAUDE.md — required in every repo

Every repository that an AI coding agent will work in must have a `CLAUDE.md`
containing:
- Project overview and goals
- Repository structure
- Architecture principles (engine/server split, tool count limits, surgical read,
  snapshot-before-write, self-hosted execution)
- Domain-specific tool design rules
- What the AI must never do
- Progress tracker with checkboxes

### In-code documentation

```python
# Tool docstrings — ≤ 80 chars, machine-readable selection cues
"""Fill null values in column. strategy: mean median mode ffill bfill drop."""

# Engine function docstrings — full human-readable explanation
def fill_nulls(file_path: str, column: str, strategy: str,
               dry_run: bool = False) -> dict:
    """
    Fill null values in the specified column using the given strategy.
    Snapshots the file before writing.
    Supports dry_run to preview changes without modifying the file.

    Returns:
        dict with "success", "filled" (count), "value_used", "backup",
        "progress", "token_estimate"
    Raises:
        Never — all exceptions caught and returned as error dicts
    """
```

---

---

## 38. What to Never Do

These are absolute prohibitions. Any code that violates them is a defect.

1. **Print to stdout in any server or engine module.**
   Stdout is the MCP channel. Any print statement corrupts it.

2. **Return a plain string, list, None, or boolean from a tool.**
   Always return a dict.

3. **Write to data without calling `snapshot()` first.**
   No exceptions for "small changes" or "non-destructive edits".

4. **Swallow exceptions silently.**
   Every exception becomes an error dict with `"success": False`, `"error"`,
   and `"hint"`.

5. **Return full file contents or raw data arrays from a write tool.**
   Write tools confirm the write. Read tools read.

6. **Fall back to returning everything when a search finds nothing.**
   Return an empty list and a helpful hint.

7. **Exceed 10 tools in a single server.**
   Split into more servers at finer tier granularity.

8. **Put business logic in server.py.**
   Tool functions in `server.py` are one-liners calling `engine.py`.

9. **Hardcode token or size limits as magic numbers.**
   Always call `get_max_rows()`, `get_max_results()` from `platform_utils.py`.

10. **Use string concatenation for file paths.**
    Always use `pathlib.Path / operator`.

11. **Write a tool that both reads and writes in a single call.**
    LOCATE and INSPECT are separate from PATCH.

12. **Add a dependency without checking its license.**
    GPL dependencies are never permitted.

13. **Make the installer require terminal commands from the user.**
    Zero terminal interaction after download.

14. **Use a cloud API as the primary execution engine.**
    The self-hosted execution principle is non-negotiable.

15. **Return raw model weights, pixel arrays, or audio buffers.**
    Return paths, summaries, and stats. Never raw binary-equivalent data.

16. **Make a tool that cannot run offline.**
    Unless network access is the explicit stated purpose of the tool.

17. **Use `eval()` or `exec()` on user-provided input.**
    Parse expressions manually using AST with an operation allowlist.

18. **Pass user-provided strings into `subprocess.run()` with `shell=True`.**
    Always use argument lists and `shell=False`. Always set `timeout`.

19. **Use user-provided file paths without calling `resolve_path()` first.**
    Path traversal is a real attack vector even in local tools.

20. **Mix async and sync tool definitions without verifying framework compatibility.**
    Either all tools are sync or you have an async-aware server setup.

21. **Return `None` from an async tool.**
    Async engine functions must return a dict in all code paths.

22. **Re-execute a module from disk inside a tool function using `importlib.util.exec_module`.**
    This bypasses Python's `sys.modules` cache and re-runs the entire module on
    every call. Use `importlib.import_module` (cached) or — better — direct
    module-level imports at startup.

23. **Require a GPU inside an MCP tool.**
    MCP tools run on CPU. VRAM constraints are about the LLM model, not tool
    execution. Never call `torch.cuda.is_available()` to decide whether to run a
    tool operation.

24. **Use `git pull` in a mcp.json launch command.**
    Use `git fetch origin --quiet; git reset --hard FETCH_HEAD` instead. `git pull`
    fails on detached HEAD and dirty states.

25. **Check only the directory when guarding against broken clones in mcp.json.**
    Always check for the `.git` subfolder. A directory without `.git` is a broken
    partial clone — remove it before re-cloning.

26. **Write generated output files next to the server source code or in a temp dir.**
    When an input file is provided, save beside it. Fall back to ~/Downloads only
    when there is no input file. Never write to the repo directory or system temp.

27. **Use a project-specific environment variable name instead of `MCP_CONSTRAINED_MODE`.**
    All MCP servers use `MCP_CONSTRAINED_MODE`. No project-specific alternatives.

28. **Call `pd.read_csv()` directly in server or engine code.**
    Route all CSV reads through `shared/file_utils.read_csv()` for consistent
    encoding fallback and bad-line tolerance. Scattered direct calls will fail on
    real-world files with encoding issues or malformed rows.

29. **Embed Plotly.js inline in HTML output (`include_plotlyjs=True`).**
    The 3.5 MB bundle triggers Windows Defender on every write and makes charts
    unusable offline. Use the offline-first directory pattern from §26.

30. **Create a snapshot before validating op arrays.**
    Validation failures after a snapshot leave orphaned `.bak` files. Validate
    the complete op array first; snapshot only after all ops are confirmed valid.

31. **Use lazy function-body imports for scipy, statsmodels, numpy, or sklearn.**
    On Windows, these trigger Defender `.pyc` scans on every server restart.
    Use module-level imports with `_SCIPY_OK` / `_STATSMODELS_OK` flags (§15).

32. **Guard optional-dependency calls with a boolean flag variable.**
    Pyright cannot narrow `None | module` through a boolean. Use `is not None`
    checks directly on the module variable so type narrowing works correctly.

33. **Apply numeric aggregations (mean, sum, min, max) to a column without coercing
    to numeric first.**
    CSVs read as string dtype silently crash on aggregation. Always call
    `pd.to_numeric(col, errors='coerce')` before numeric operations (§27).

34. **Parse dates with a single fixed format string or without `format=`.**
    Use `format="mixed"` with `dayfirst=False` and `errors="coerce"` for all
    full-column datetime conversions (§27).

35. **Default `output_path` to the input file in a transform or write tool.**
    When `output_path` is omitted, write to a derived sibling file
    (`{stem}_filtered.csv`, `{stem}_merged.csv`, etc.). Only overwrite the
    input when the caller explicitly passes `output_path` pointing back to the
    source. Taking a snapshot does not make silent overwrite acceptable — the
    user still loses their original in-place (§19).

36. **Omit `"output_path"` from the response of any tool that writes a file.**
    Callers must be able to chain tools without guessing the derived filename.
    Always include both `"output_file"` (name only) and `"output_path"`
    (absolute path) in the response dict.

---

## 39. Checklist — New Server from Scratch

### Discovery
- [ ] Define the domain clearly
- [ ] Define the tier (Basic / Medium / Advanced)
- [ ] List all tools — count before writing any code
- [ ] Confirm tool count ≤ 10 (target 6–8)
- [ ] Identify the surgical read tools (`search_*`, `inspect_*`, `list_*`)
- [ ] Identify write tools — confirm each has a snapshot before write
- [ ] Choose language based on local library availability
- [ ] Confirm all required libraries have approved licenses
- [ ] Verify every tool can run offline (self-hosted execution test)

### Setup
- [ ] Create `servers/{domain}_{tier}/`
- [ ] Create `__init__.py`
- [ ] Create `pyproject.toml` with `requires-python = "==3.12.*"` and `shared` dependency
- [ ] Pin `fastmcp>=2.0,<3.0` in `pyproject.toml`
- [ ] Add to workspace `pyproject.toml` members list
- [ ] `uv sync` — no errors

### Shared modules
- [ ] `shared/version_control.py` — snapshot() uses atomic temp+rename, collision guard
- [ ] `shared/patch_validator.py` — tested
- [ ] `shared/file_utils.py` — `resolve_path()`, `read_csv()` with encoding fallback + bad-line retry, `atomic_write_text()`
- [ ] `shared/platform_utils.py` — reads env at call time, not import time
- [ ] `shared/progress.py` — ok/fail/info/warn/undo helpers
- [ ] `shared/receipt.py` — append_receipt / read_receipt_log, never raises
- [ ] `shared/html_theme.py` — `_ensure_plotly_js()` for offline-first charts (if generating HTML)

### Engine
- [ ] `engine.py` with zero MCP imports
- [ ] Surgical read tools implemented first
- [ ] Every tool returns dict with `"success"` as first key
- [ ] Every write tool validates all ops BEFORE calling `snapshot()`
- [ ] Every write tool calls `snapshot()` before writing
- [ ] Every write tool includes `"backup"` in return dict
- [ ] Every write tool includes `"dry_run"` path
- [ ] Every tool response includes `"progress"` array
- [ ] Every tool response includes `"token_estimate"`
- [ ] Bounded reads use `get_max_*()` helpers (called at execution time)
- [ ] No `print()` statements anywhere
- [ ] `restore_version` delegates to `shared.version_control`
- [ ] All file path inputs validated through `resolve_path()` before use
- [ ] No `eval()` or `exec()` on user-provided input
- [ ] Subprocess calls use argument lists with `shell=False` and `timeout`
- [ ] All CSV reads go through `shared.file_utils.read_csv()`
- [ ] All date parsing uses `format="mixed", dayfirst=False, errors="coerce"`
- [ ] All numeric aggregations coerce column with `pd.to_numeric(..., errors="coerce")` first
- [ ] Heavy optional libs (scipy, statsmodels) imported at module level with `_OK` flag
- [ ] Optional-dependency guards use `is not None` checks, not boolean flags
- [ ] No `importlib.util.exec_module()` inside any function body
- [ ] Pipeline/batch tools use `_coerce_op()` or equivalent LLM resilience pattern

### Server
- [ ] `server.py` with FastMCP setup
- [ ] One `@mcp.tool()` per tool, each body is `return engine.func(params)`
- [ ] Every docstring ≤ 80 characters
- [ ] All parameters typed with allowed types
- [ ] Tool annotations set (`readOnlyHint`, `destructiveHint`, etc.)
- [ ] `--transport` and `--port` CLI args in `main()`
- [ ] `project.scripts` entry in `pyproject.toml`

### Tests
- [ ] `tests/fixtures/` with real data (simple + messy + large)
- [ ] `tests/test_{server_name}.py`
- [ ] Test every tool: success case
- [ ] Test every tool: file-not-found error
- [ ] Test every write tool: snapshot created
- [ ] Test every write tool: `"backup"` in response
- [ ] Test every write tool: `dry_run=True` does not modify file
- [ ] Test every write tool: invalid op names do NOT create snapshots
- [ ] Test every bounded read: truncation at limit
- [ ] Test `restore_version`: file reverts correctly
- [ ] Run with `MCP_CONSTRAINED_MODE=1`: limits enforced
- [ ] Path-outside-home tests use cross-platform paths (see §29)
- [ ] Test CSV with encoding issues: reads correctly via shared reader
- [ ] Test CSV with malformed rows: reads with rows skipped, no crash
- [ ] `uv run pytest` — all pass
- [ ] `uv run pyright servers/{name}/` — no errors (covers sub-modules too)
- [ ] `uv run ruff check .` — no errors
- [ ] `uv run ruff format --check .` — no reformatting needed

### CI/CD
- [ ] `.github/workflows/ci.yml` — lint + format + type-check + test (all 3 platforms)
- [ ] `.github/workflows/release.yml` — CI + release on tag push
- [ ] macOS step: `brew install libomp` (if using XGBoost/LightGBM)
- [ ] `PYTHONPATH: "."` set in CI env
- [ ] `MCP_CONSTRAINED_MODE: "1"` set in CI env
- [ ] `pyproject.toml` ruff config excludes notebooks if present
- [ ] CI passes on all three platforms (Ubuntu, macOS, Windows)

### Distribution and installation
- [ ] mcp.json entry uses Windows PowerShell format from §33
- [ ] mcp.json entry uses bash format for macOS/Linux from §33
- [ ] Clone guard checks `.git` subfolder, not just directory existence
- [ ] Update method is `git fetch origin + git reset --hard FETCH_HEAD`
- [ ] Install path is `~/.mcp_servers/{REPO_NAME}`
- [ ] Env var is `MCP_CONSTRAINED_MODE` (not a project-specific name)
- [ ] Timeout is `600000`
- [ ] Pre-install PowerShell block in README (clone + uv sync)
- [ ] Pre-install bash block in README for macOS/Linux
- [ ] Add to `install/mcp_config_writer.py` registry
- [ ] Test on clean machine or VM: mcp.json entry clones, installs, and starts server

### Review
- [ ] `verify_tool_docstrings.py` — all ≤ 80 chars
- [ ] No file exceeds 1,000 lines (engine sub-module split if needed)
- [ ] Output-generating tools default to input file's directory, then ~/Downloads if no input file
- [ ] Manual test in LM Studio (9B model) — four-tool loop works
- [ ] Manual test in Claude Desktop — tools appear and execute
- [ ] 10-step task test — context window not exceeded
- [ ] README follows the required section order from §37
- [ ] Update `CLAUDE.md` progress tracker

---

## 40. Checklist — New Tool in Existing Server

- [ ] Server tool count will not exceed 10 after adding
- [ ] Tool name follows `verb_noun` snake_case convention
- [ ] Verb is in the approved verb list
- [ ] Write engine function in `engine.py` first (no MCP imports)
- [ ] Engine function returns dict with `"success"` as first key
- [ ] Engine function calls `resolve_path()` as first operation on any file path
- [ ] Engine function validates file extension after resolve
- [ ] Engine function validates all ops/inputs BEFORE calling `snapshot()`
- [ ] Engine function calls `snapshot()` if it writes
- [ ] Engine function includes `"backup"` in write responses
- [ ] Engine function includes `"dry_run"` path if it writes
- [ ] Engine function calls `append_receipt()` after every write
- [ ] Engine function includes `"progress"` array
- [ ] Engine function includes `"token_estimate"`
- [ ] Engine function catches all exceptions → error dict
- [ ] Error dict includes `"hint"` with actionable recovery (names a specific tool)
- [ ] Engine function uses `get_max_*()` helpers for bounded returns
- [ ] No `print()` statements
- [ ] No `eval()` or `exec()` on user-provided input
- [ ] Subprocess calls use `shell=False` and `timeout` (if applicable)
- [ ] Tool can run offline (self-hosted execution principle)
- [ ] CSV reads use `shared.file_utils.read_csv()`, not `pd.read_csv()` directly
- [ ] Date parsing uses `format="mixed", dayfirst=False, errors="coerce"`
- [ ] Numeric aggregations coerce column with `pd.to_numeric(errors='coerce')` first
- [ ] Optional dependencies imported at module level with `_OK` flag and `is not None` guards
- [ ] If tool accepts op arrays: uses `_coerce_op()` or dual-key pattern for LLM resilience
- [ ] Add `@mcp.tool()` in `server.py` calling engine function
- [ ] Tool docstring ≤ 80 characters
- [ ] Tool annotations set (`readOnlyHint`, `destructiveHint`, etc.)
- [ ] All parameters have allowed type annotations
- [ ] Optional parameters have primitive defaults
- [ ] Output-generating tools: default output goes to input file's directory, then ~/Downloads
- [ ] Output-generating tools: use `get_default_output_dir()` from `shared/file_utils.py`
- [ ] Output-generating HTML tools: use `_ensure_plotly_js()` for offline-first charts
- [ ] Transform/write tools: default `output_path` is a derived sibling name, never the input path
- [ ] Transform/write tools: response dict includes both `"output_file"` (name) and `"output_path"` (absolute)
- [ ] Audit: `grep -rn "if output_path else path"` returns no hits in new engine code
- [ ] Add success test
- [ ] Add file-not-found / missing data failure test
- [ ] Add snapshot-created test (write tools)
- [ ] Add no-snapshot-on-validation-failure test (write tools with op arrays)
- [ ] Add `dry_run=True` test (write tools)
- [ ] Add progress array test
- [ ] `uv run pytest tests/test_{server_name}.py` — all pass
- [ ] `uv run ruff check servers/{name}/`
- [ ] `uv run pyright servers/{name}/`
- [ ] `verify_tool_docstrings.py` — ≤ 80 chars confirmed

---

## 41. Domain Reference Table

This table maps domains to their local execution engines, giving a quick reference
for building new servers that comply with the self-hosted execution principle.

| Domain | Server name pattern | Primary local engine |
|---|---|---|
| Document editing | `office_basic` | python-docx, openpyxl, python-pptx |
| PDF processing | `pdf_basic` | PyMuPDF, pdfplumber, reportlab |
| Data analytics | `data_basic/medium/advanced` | polars, duckdb, pandas, ydata-profiling |
| SQL analytics | `sql_basic` | DuckDB, SQLite |
| Machine learning | `ml_basic/medium/advanced` | scikit-learn, XGBoost, LightGBM |
| Deep learning | `dl_basic` | PyTorch, ONNX Runtime |
| OCR | `ocr_basic` | easyocr, surya, pytesseract |
| Image processing | `image_basic` | Pillow, OpenCV, scikit-image |
| Video processing | `video_basic` | MoviePy, FFmpeg (subprocess) |
| Web scraping | `web_basic` | Playwright, BeautifulSoup, httpx |
| System monitoring | `sys_basic` | psutil, py-cpuinfo |
| Geospatial | `geo_basic` | geopandas, shapely, rasterio |

---

*Version: 6.1*
*Derived from: MCP_Microsoft_Office STANDARDS.md v1.1, expanded and battle-tested
through MCP_Data_Analyst and MCP_Machine_Learning development.*
*v5.0 additions: self-updating mcp.json standard (§33), CPU-first execution principle
(§21), Downloads-first output path (§26), strict Python 3.12 pin, setup-uv@v4,
pyright + docstring verify in CI, unified MCP_CONSTRAINED_MODE env var.*
*v6.1 additions: §19 output path safety rule (never default to input file in transform
tools; always return "output_path" in response); §38 prohibitions #35–36 (silent
overwrite, missing output_path in response); §40 checklist items for transform tools.*
*v6.0 additions: §27 Shared Data I/O Standards (single CSV reader, numeric coercion,
date parsing, atomic writes); §28 LLM Input Resilience (_coerce_op, dual-key pattern,
_OP_SIGNATURES, type-safe extraction); §15 revised import strategy (module-level with
flags replaces lazy imports on Windows; pyright narrowing via is not None); §19
atomic snapshot with Windows collision guard; §26 offline-first Plotly (_ensure_plotly_js,
directory mode, CDN fallback); §13 validate-before-snapshot rule; §38 new prohibitions
28–34; checklists updated with new rules throughout.*
*This document should be linked from every MCP server project's README and CLAUDE.md.*
*When these standards conflict with a specific project's CLAUDE.md, the project's
CLAUDE.md takes precedence for that project. These are the defaults.*
