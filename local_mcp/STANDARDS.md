# Local MCP Standards

> Architecture, repository structure, and engine/server split for self-hosted MCP servers driven by a local LLM.

**ID** `local_mcp` · **Tier** Domain · **Version** 1.0
**Owns** MCP architecture · self-hosted execution principle · engine/server split · repo + tier structure · MCP naming · MCP dependency policy
**Defers to** tool schema · annotations · patch protocol · token budget → [TOOLS.md](TOOLS.md) · state · receipts · transports · resource tiers → [RUNTIME.md](RUNTIME.md) · testing · install · distribution · docs → [DELIVERY.md](DELIVERY.md) · layering + dependency direction → [architecture](../architecture/STANDARDS.md) · Python idiom + packaging → [python](../python/STANDARDS.md) · license policy · vetting gate · supply chain · lock files → [dependencies](../dependencies/STANDARDS.md) · offline-first HTML output · theming → [html_generation](../html_generation/STANDARDS.md) · generic layout + naming → [directory](../directory/STANDARDS.md)
**Load with** [TOOLS.md](TOOLS.md) · [RUNTIME.md](RUNTIME.md) · [DELIVERY.md](DELIVERY.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Core Mental Model](#2-core-mental-model)
3. [MCP Primitives](#3-mcp-primitives)
4. [Self-Hosted Execution](#4-self-hosted-execution)
5. [Language and Runtime Selection](#5-language-and-runtime-selection)
6. [Repository Structure](#6-repository-structure)
7. [The Three-Tier Split](#7-the-three-tier-split)
8. [Engine and Server Separation](#8-engine-and-server-separation)
9. [Engine Sub-Modules](#9-engine-sub-modules)
10. [Import Strategy](#10-import-strategy)
11. [Naming Conventions](#11-naming-conventions)
12. [Dependency Policy](#12-dependency-policy)
13. [Prohibitions](#13-prohibitions)
14. [Checklist](#14-checklist)

---

## 1. Principles

Two constraints drive every rule in this standard and its three companions.

| # | Constraint | Statement |
|---|---|---|
| 1 | Hardware | 8 GB GPU · 9B local model · real data → no context overflow · no data corruption · no developer needed to install |
| 2 | Sovereignty | All execution local. ✗ data leaves machine · ✗ API keys · ✗ cloud subscription · ✗ third-party uptime dependency |

Failure modes these rules exist to prevent:

| Failure | Prevented by |
|---|---|
| Tool schemas overflow context | Tool count discipline → [TOOLS.md](TOOLS.md) |
| Tools return full datasets | Surgical read protocol → [TOOLS.md](TOOLS.md) |
| One tool does too much | Four-tool pattern → [TOOLS.md](TOOLS.md) |
| Silent data corruption | Snapshot-before-write → [RUNTIME.md](RUNTIME.md) |
| Data leaves the machine | Self-hosted execution (§4) |
| Install too complex | Self-updating config → [DELIVERY.md](DELIVERY.md) |

---

## 2. Core Mental Model

An MCP server is a structured API called by a language model with JSON arguments, returning JSON results. ✗ chat assistant · ✗ script runner · ✗ AI agent. It is a deterministic function executor.

| Actor | Job |
|---|---|
| Model | Understand intent · choose tools · generate arguments · decide next step |
| Server | Validate input · execute operation · return structured result |

Server ✗ crosses into model's job: ✗ AI inference inside tools · ✗ "smart" behavior guessing intent. Deterministic in → deterministic out.

---

## 3. MCP Primitives

| Primitive | Use when | Rule |
|---|---|---|
| Tool | Model calls it to do work | Primary primitive — every rule in this standard set targets tools |
| Resource | Model references it for stable context (schema, reference data) | Only when data cannot change between calls ; can change → must be a tool |
| Prompt | User needs a starting workflow template | Most servers need none |

---

## 4. Self-Hosted Execution

Every tool executes its core operation on local resources: local CPU · RAM · disk · subprocesses.

**The test:** can this tool complete its primary operation with the machine disconnected from the internet? No → it violates this standard.

| Permitted | ✗ Not permitted as primary execution |
|---|---|
| Local files · databases · subprocesses (FFmpeg, Tesseract) | Paid third-party APIs (OpenAI, AWS, GCP) |
| Locally-run services (Postgres, Docker, MLflow) | OAuth / API-key requirements |
| One-time network download with local cache | Sending user data to external servers |
| Graceful degradation when the network is absent | Depending on a cloud service being online |

Network access permitted only for:

1. One-time model/asset download on first run, cached locally
2. Tools whose stated purpose is network operation (scraper, feed reader, crawler)
3. Telemetry — disabled by default

Document every exception in the tool docstring and README.

---

## 5. Language and Runtime Selection

Libraries dictate language, ✗ preference, ✗ fashion. Choose the language where the problem is already solved locally.

| Domain | Language | Primary local libraries |
|---|---|---|
| Document editing (docx, xlsx, pptx) | Python | python-docx · openpyxl · python-pptx |
| PDF manipulation | Python | PyMuPDF · pdfplumber · reportlab |
| Data analytics | Python | polars · duckdb · pandas · ydata-profiling |
| Machine learning | Python | scikit-learn · XGBoost · LightGBM · FLAML |
| Deep learning | Python | PyTorch · ONNX Runtime |
| Image processing | Python | Pillow · OpenCV · scikit-image |
| Audio processing | Python | librosa · pydub |
| Video processing | Python | MoviePy · FFmpeg (subprocess) |
| OCR | Python | easyocr · surya · pytesseract |
| Browser automation | Python \| TypeScript | playwright |
| Database (SQL) | Python \| TypeScript | duckdb · sqlite3 · psycopg2 |
| System / OS automation | Python \| Go | psutil · subprocess ; Go for single binary |
| Web scraping | Python | playwright · BeautifulSoup · httpx |
| File system operations | Go \| Rust | Single binary · no runtime · fastest |
| Web API wrappers | TypeScript | Best for JSON-heavy REST |
| Geospatial | Python | geopandas · shapely · rasterio |
| Time series | Python | statsforecast · sktime · neuralprophet |
| Security tools | Python \| Rust | cryptography · bandit · detect-secrets |

Python runtime rules (idiom + packaging → [python](../python/STANDARDS.md)):

| Rule | Value | Reason |
|---|---|---|
| Python pin | `==3.12.*` in `pyproject.toml` · `.python-version` = `3.12` | Strict pin ; `>=3.12` — a CI runner upgrading to 3.13 breaks silently |
| Package manager | `uv`, `required-version = ">=0.5"` | JIT dependency resolution on first run |
| ✗ package managers | pip directly in production · conda · poetry for new projects | — |
| MCP framework pin | `fastmcp>=2.0,<3.0` | Tool-registration API changed across majors → tools register but are never served |
| Lint + format | `ruff` configured in root `pyproject.toml` · line-length 120 · target `py312` · exclude `*.ipynb` | One tool replaces black · isort · flake8 · pylint |

---

## 6. Repository Structure

Monorepo is the default when more than one server shares a domain or pipeline: one repo · one lockfile · one CI pipeline · one install script.

Monorepo layout:

    {project-name}/
    ├── shared/                  code shared by ALL servers — never duplicate
    │   ├── version_control.py   snapshot / rollback
    │   ├── patch_validator.py   validate op arrays before applying
    │   ├── file_utils.py        path resolution · atomic writes · CSV reader
    │   ├── platform_utils.py    OS detection · constrained-mode flags
    │   ├── progress.py          ok / fail / info / warn / undo helpers
    │   ├── receipt.py           operation receipt log
    │   ├── html_theme.py        shared HTML/CSS/Plotly theme + offline JS
    │   └── html_layout.py       responsive CSS constants · chart layout
    ├── servers/
    │   └── {domain}_{tier}/     e.g. data_basic, ml_medium, office_advanced
    │       ├── server.py        FastMCP setup + tool definitions (thin)
    │       ├── engine.py        pure domain logic (zero MCP imports)
    │       ├── _{tier}_helpers.py   shared imports · constants · helpers
    │       ├── _{tier}_*.py     sub-modules grouped by function (§9)
    │       └── pyproject.toml
    ├── tests/
    │   ├── fixtures/            real test data, committed
    │   └── test_{server}.py
    ├── install/
    │   ├── install.sh           POSIX sh — Linux / macOS
    │   ├── install.bat          Windows CMD
    │   └── mcp_config_writer.py writes AI-client config files
    ├── .github/workflows/       ci.yml · release.yml
    ├── pyproject.toml           root workspace
    ├── uv.lock
    ├── .python-version
    ├── CLAUDE.md
    └── README.md

Single-server layout flattens `servers/{name}/` to the repo root, keeping `shared/` · `tests/` · `install/` unchanged.

---

## 7. The Three-Tier Split

Every server targets exactly one complexity tier. ✗ mix tiers in one server. Tier choice directly controls how many tool schemas the local model reasons about at once.

| Tier | Scope | Examples | Tool count | Loading |
|---|---|---|---|---|
| 1 — Basic | CRUD · direct ops on individual nodes. ✗ multi-step pipelines · ✗ cross-element ops | read paragraph · load file · inspect schema · list processes | 6–8 | Must stand alone — simple tasks never need tier 2 or 3 |
| 2 — Medium | Structured + pipeline ops: formulas · conditional logic · template fill · batch transform | fill template · profiling pipeline · train with CV · transcode batch | 5–7 | Loadable with tier 1 ; combined total ≤ 15 tools |
| 3 — Advanced | Layout · visual · export · optimization · complex cross-element interaction | export PDF · generate dashboard · hyperparameter tuning · model export | 5–6 | Standalone — dedicated sessions |

Tier assignment:

| Question | Tier |
|---|---|
| Reads or writes a single named node (row, cell, file, record, frame)? | 1 |
| Applies a structured pipeline, rule, or multi-step transform? | 2 |
| Changes visual appearance, export format, or optimizes a model/asset? | 3 |
| Spans all three? | Split into multiple tools, one per tier |

---

## 8. Engine and Server Separation

Every server has exactly two logic files.

| File | Contains | ✗ Contains |
|---|---|---|
| `engine.py` | Pure domain logic · path resolution · snapshot · validation · domain libraries | Any MCP or FastMCP import |
| `server.py` | FastMCP setup · tool registration · annotations · docstrings · `main()` transport wiring | Any domain logic |

Rules:

- Any line touching domain data → `engine.py`. Any line touching the MCP protocol → `server.py`.
- Each `server.py` tool body is one line: return the engine call. Body > 2 lines → it holds logic that belongs in `engine.py`.
- Tests import `engine.py` directly, never a running server → [DELIVERY.md](DELIVERY.md).

---

## 9. Engine Sub-Modules

`engine.py` past ~400–500 lines → split into focused sub-modules; `engine.py` becomes a router. **No file exceeds 1,000 lines** — hard limit, enforced at review.

Sub-module rules:

| Rule | Detail |
|---|---|
| Prefix | `_{tier_abbr}_` — `_basic_`, `_medium_`, `_adv_` — avoids name collisions |
| Grouping | By what the code does (io · transform · analysis · charts · report), ✗ by which tool calls it |
| Imports | Zero MCP imports — same rule as `engine.py`. Relative imports within package |
| Helpers module | `_{tier}_helpers.py` centralizes shared imports · constants (algorithm sets, dir names, limits) · private utilities (`_error`, `_check_memory`) with an `__all__` re-export list |
| Router | Fully split `engine.py` = imports + `__all__` only. Partial router (small inline read-only functions + imported large ones) is acceptable while under 1,000 lines |
| Test visibility | Tests still import from `engine.py` — sub-module structure is invisible to tests |

File size targets:

| File | Target lines | Hard limit |
|---|---|---|
| `engine.py` (thin router) | 30–50 | 1,000 |
| `engine.py` (partial router) | 200–400 | 1,000 |
| `_{tier}_helpers.py` | 150–500 | 1,000 |
| Other sub-modules | 150–800 | 1,000 |
| `server.py` | 50–150 | 300 |

---

## 10. Import Strategy

**✗ lazy function-body imports for heavy scientific libraries.** On Windows the Defender real-time scanner inspects every `.pyc` on first access; scipy and statsmodels carry 200+ compiled modules. A lazy import inside a function body means the first call after every server restart (LM Studio restarts servers per session) triggers a multi-minute scan that appears as a hang.

Correct pattern: **module-level import inside `try/except ImportError`**, setting the module reference to `None` and a `_{LIB}_OK` flag on failure. The scan cost is paid once at server startup, before user interaction.

Guard calls with `is not None` checks on the module variable, ✗ with the boolean flag — a type checker cannot narrow `None | module` through a boolean, so flag-guarded calls fail type check. Early-exit guard: module `is None` → return error dict naming the install command.

| Library type | Import style |
|---|---|
| Core scientific (scipy · numpy · statsmodels · sklearn) | Module-level with `_OK` flag |
| Always-needed domain lib (pandas · PIL · cv2) | Module-level, unconditional |
| Optional domain extension (geopandas · torch · plotly) | Lazy in function body — permitted only when most tools still work without it |
| Standard library | Module-level, unconditional |

✗ re-execute a module from disk inside a tool function via `importlib.util.exec_module` — it bypasses the module cache and re-runs the whole module on every call.

---

## 11. Naming Conventions

| Entity | Convention | Examples |
|---|---|---|
| Server directory | `servers/{domain}_{tier}/` | `data_basic` · `ml_medium` · `office_advanced` |
| MCP tool function | `verb_noun` snake_case | `read_dataset` · `search_rows` · `fill_nulls` · `restore_version` |
| Engine function | snake_case verb | `apply_patch` · `train_classifier` |
| Class | PascalCase | `PatchValidator` · `VersionControl` |
| Constant | UPPER_SNAKE_CASE | `MAX_ROWS` · `DEFAULT_TEST_SIZE` |
| Private helper | Leading underscore | `_apply_single_op` · `_resolve_strategy` |
| Optional-dep module ref | Leading underscore + `_OK` flag | `_scipy_stats` · `_SCIPY_OK` |
| Sub-module | `_{tier_abbr}_{function}.py` | `_adv_charts.py` · `_basic_io.py` |

Allowed tool verbs: `read` · `list` · `search` · `get` · `inspect` · `set` · `fill` · `drop` · `rename` · `replace` · `insert` · `delete` · `add` · `update` · `move` · `train` · `export` · `apply` · `restore` · `run` · `generate`

Patch op names use the same `verb_noun` form with a narrower verb set → [TOOLS.md](TOOLS.md).

---

## 12. Dependency Policy

License policy · allowed license tiers · vetting gate · supply chain · lock files → [dependencies](../dependencies/STANDARDS.md). ✗ restate any license tier here. MCP-specific mechanics only, below.

| MCP-specific rule | Detail |
|---|---|
| Offline install | Every runtime dependency must resolve and install from the lockfile with no post-install network fetch beyond the package index. A library that downloads assets at first use must cache them locally and degrade gracefully (§4) |
| Reproducible startup | Server launch runs a lockfile-frozen sync on every start → identical dependency set on every restart. ✗ unpinned resolution at launch |
| Framework pin | `fastmcp` pinned to a major range — a silent registration-API change serves zero tools with no error (§5) |
| Dev tooling | `pytest>=9.0` · `ruff>=0.9` in the dev dependency group — ruff replaces black · isort · flake8 · pylint |
| Weight of the tree | A dependency that inflates first-run install past the client's connection timeout breaks the install contract → [DELIVERY.md](DELIVERY.md) |

Libraries prohibited in MCP servers, for MCP-specific reasons:

| Library | Reason |
|---|---|
| `win32com` · `pywin32` | Windows-only → breaks the cross-platform contract |
| `Spire.*` · `Aspose.*` | Proprietary + per-seat licensed → users cannot self-host it freely. License tiering itself → [dependencies](../dependencies/STANDARDS.md) |
| Any cloud SDK as primary execution engine (`boto3` for ML, `google-cloud-*`) | Violates self-hosted execution (§4) |

---

## 13. Prohibitions

Absolute. Any code that violates one is a defect.

| # | ✗ Never | Owner |
|---|---|---|
| 1 | Print to stdout in any server or engine module — stdout is the MCP channel | [RUNTIME.md](RUNTIME.md) |
| 2 | Return a plain string, list, `None`, or boolean from a tool — always a dict | [TOOLS.md](TOOLS.md) |
| 3 | Write data without calling `snapshot()` first — no exception for "small changes" | [RUNTIME.md](RUNTIME.md) |
| 4 | Swallow exceptions silently — every exception becomes an error dict | [TOOLS.md](TOOLS.md) |
| 5 | Return full file contents or raw arrays from a write tool | [TOOLS.md](TOOLS.md) |
| 6 | Fall back to returning everything when a search finds nothing — return empty list + hint | [TOOLS.md](TOOLS.md) |
| 7 | Exceed 10 tools in one server — split at finer tier granularity | [TOOLS.md](TOOLS.md) |
| 8 | Put business logic in `server.py` | §8 |
| 9 | Hardcode token or size limits as magic numbers — call the `get_max_*()` helpers | [RUNTIME.md](RUNTIME.md) |
| 10 | Build file paths by string concatenation | [RUNTIME.md](RUNTIME.md) |
| 11 | Write a tool that both reads and writes in one call | [TOOLS.md](TOOLS.md) |
| 12 | Add a dependency without clearing it through the vetting gate | [dependencies](../dependencies/STANDARDS.md) |
| 13 | Require terminal commands from the user to install | [DELIVERY.md](DELIVERY.md) |
| 14 | Use a cloud API as primary execution engine | §4 |
| 15 | Return raw model weights, pixel arrays, or audio buffers — return paths + stats | [TOOLS.md](TOOLS.md) |
| 16 | Ship a tool that cannot run offline ; network access is its stated purpose | §4 |
| 17 | `eval()` or `exec()` on user input — parse with an AST allowlist | [RUNTIME.md](RUNTIME.md) |
| 18 | Pass user strings into a subprocess with `shell=True` | [RUNTIME.md](RUNTIME.md) |
| 19 | Use a user-provided path without resolving + validating it first | [RUNTIME.md](RUNTIME.md) |
| 20 | Mix async and sync tool definitions without verifying framework compatibility | [RUNTIME.md](RUNTIME.md) |
| 21 | Return `None` from an async tool | [TOOLS.md](TOOLS.md) |
| 22 | Re-execute a module from disk via `importlib.util.exec_module` inside a tool | §10 |
| 23 | Require a GPU inside an MCP tool — VRAM constrains the LLM, not tool execution | [RUNTIME.md](RUNTIME.md) |
| 24 | Use `git pull` in a launch command — fetch + reset instead | [DELIVERY.md](DELIVERY.md) |
| 25 | Guard a broken clone by checking only the directory — check the `.git` subfolder | [DELIVERY.md](DELIVERY.md) |
| 26 | Write generated output beside server source or into system temp | [RUNTIME.md](RUNTIME.md) |
| 27 | Use a project-specific env var name instead of `MCP_CONSTRAINED_MODE` | [RUNTIME.md](RUNTIME.md) |
| 28 | Call the dataframe library's CSV reader directly — route through the shared reader | [RUNTIME.md](RUNTIME.md) |
| 29 | Embed the charting JS bundle inline in HTML output | [html_generation](../html_generation/STANDARDS.md) |
| 30 | Create a snapshot before validating an op array — leaves orphaned backups | [TOOLS.md](TOOLS.md) |
| 31 | Lazy function-body imports for scipy · statsmodels · numpy · sklearn | §10 |
| 32 | Guard optional-dependency calls with a boolean flag instead of `is not None` | §10 |
| 33 | Apply a numeric aggregation to a column without coercing to numeric first | [RUNTIME.md](RUNTIME.md) |
| 34 | Parse dates with a single fixed format string or with no format at all | [RUNTIME.md](RUNTIME.md) |
| 35 | Default `output_path` to the input file in a transform or write tool | [RUNTIME.md](RUNTIME.md) |
| 36 | Omit `"output_path"` from the response of any tool that writes a file | [RUNTIME.md](RUNTIME.md) |

---

## 14. Checklist

- [ ] Every tool completes its primary operation with the network disconnected
- [ ] Every network exception is documented in the tool docstring and README
- [ ] Language chosen by local library availability, not preference
- [ ] `requires-python = "==3.12.*"` — strict pin, not `>=`
- [ ] `fastmcp` pinned to a major range (`>=2.0,<3.0`)
- [ ] `uv` is the package manager; `pip` · `conda` · `poetry` absent
- [ ] `shared/` code is not duplicated into any server package
- [ ] Server directory is `servers/{domain}_{tier}/`
- [ ] Server targets exactly one tier; tool count within that tier's range
- [ ] `engine.py` has zero MCP imports
- [ ] Every `server.py` tool body is a single call into `engine.py`
- [ ] No file exceeds 1,000 lines; `server.py` under 300
- [ ] Sub-modules are prefixed `_{tier_abbr}_` and grouped by function
- [ ] Tests import `engine.py`, not a running server
- [ ] scipy · statsmodels · numpy · sklearn imported at module level with an `_OK` flag
- [ ] Optional-dependency calls guarded by `is not None`, not by boolean flag
- [ ] No `importlib.util.exec_module` inside any function body
- [ ] Tool names are `verb_noun` with a verb from the approved list
- [ ] Every dependency cleared the vetting gate in `dependencies/STANDARDS.md`
- [ ] Every runtime dependency installs from the lockfile with no post-install fetch
- [ ] No prohibited library (`pywin32`, `Spire.*`, `Aspose.*`, cloud SDK as engine)
- [ ] No violation of any item in §13
