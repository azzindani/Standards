# Local MCP Delivery Standards

> How an MCP server is tested, built, installed, distributed, and documented for a non-technical local user.

**ID** `local_mcp/delivery` · **Tier** Domain · **Version** 1.0
**Owns** MCP test delta · MCP CI delta · self-updating install model · client config registration · README + CLAUDE.md contract · domain reference table
**Defers to** architecture · engine/server split → [STANDARDS.md](STANDARDS.md) · tool schema · patch protocol → [TOOLS.md](TOOLS.md) · snapshots · transports · constrained mode → [RUNTIME.md](RUNTIME.md) · pyramid · coverage thresholds · mocking policy · fixtures discipline → [testing](../testing/STANDARDS.md) · pipeline stages · caching · gates · release automation → [cicd](../cicd/STANDARDS.md) · branching · tagging · semver → [git](../git/STANDARDS.md) · doc types · ADRs · runbooks → [documentation](../documentation/STANDARDS.md) · license policy · lock files → [dependencies](../dependencies/STANDARDS.md)
**Load with** [STANDARDS.md](STANDARDS.md) · [TOOLS.md](TOOLS.md) · [RUNTIME.md](RUNTIME.md)

---

## Table of Contents

1. [Test Target](#1-test-target)
2. [MCP Contract Tests](#2-mcp-contract-tests)
3. [Fixtures](#3-fixtures)
4. [Cross-Platform Test Pitfalls](#4-cross-platform-test-pitfalls)
5. [CI Delta](#5-ci-delta)
6. [Release](#6-release)
7. [The Install Model](#7-the-install-model)
8. [Launch Command Rules](#8-launch-command-rules)
9. [Client Registration](#9-client-registration)
10. [README Contract](#10-readme-contract)
11. [Agent and Code Documentation](#11-agent-and-code-documentation)
12. [Domain Reference Table](#12-domain-reference-table)
13. [Checklist](#13-checklist)

---

## 1. Test Target

Pyramid · classification · coverage thresholds · mocking policy → [testing](../testing/STANDARDS.md). MCP-specific target selection only:

**Tests import `engine.py` directly and call its functions. ✗ spin up an MCP server process for a unit test.** The engine is pure domain logic with zero MCP imports ([STANDARDS.md](STANDARDS.md)) precisely so that it is testable without a protocol harness. Sub-module structure is invisible to tests — they import from `engine.py` only.

The protocol layer gets exactly two integration checks, not a suite:

| Check | Asserts |
|---|---|
| stdio smoke test | Server starts · lists tools · a read-only tool executes and returns valid JSON · stdout carries protocol frames only |
| HTTP smoke test | Server starts on `--transport http` · rejects an unauthenticated request · a read-only tool executes |

---

## 2. MCP Contract Tests

Beyond the domain assertions, every write tool is tested against the contract that the model depends on. Each row is a required test case per write tool:

| # | Test | Asserts |
|---|---|---|
| 1 | Success | Operation completes · `"success": true` |
| 2 | Content correct | Read the written node back and verify content |
| 3 | Snapshot created | A new `.bak` exists in `.mcp_versions/` |
| 4 | Backup surfaced | `"backup"` key present in the response |
| 5 | Dry run | `dry_run=True` returns `"would_change"` and does **not** modify the file |
| 6 | Progress present | `"progress"` array in the response |
| 7 | Wrong file type | Error dict with a hint naming the expected extension |
| 8 | File not found | Error dict with an actionable hint |
| 9 | Index or column out of range | Error dict listing the available options |
| 10 | Constrained mode | `MCP_CONSTRAINED_MODE=1` enforces the smaller limits |
| 11 | **No orphaned snapshot** | An invalid op array creates **no** `.bak` file — validation precedes snapshot ([TOOLS.md](TOOLS.md)) |

Read tools additionally test truncation at the limit and the presence of `"truncated"` · `"total_available"` · `"hint"`.

Every tool is tested for a success case and a file-not-found case at minimum.

---

## 3. Fixtures

Fixture discipline → [testing](../testing/STANDARDS.md). MCP servers additionally require real-world messiness, committed to the repo, in three categories:

| Fixture | Contains |
|---|---|
| `simple` | Clean data · minimal edge cases |
| `messy` | Nulls · type mismatches · encoding variants (BOM, cp1252) · malformed rows · duplicate rows |
| `large` | Enough rows to trigger truncation and exercise constrained mode |

The `messy` fixture is what proves the shared reader's fallback chain ([RUNTIME.md](RUNTIME.md)). A server whose tests only use clean data is untested against the files users actually have.

---

## 4. Cross-Platform Test Pitfalls

| Pitfall | Rule |
|---|---|
| Windows temp dirs sit under home | The test temp directory resolves under the user's home on Windows, so `resolve_path()` does **not** reject it. A path-traversal rejection test must use a genuinely outside-home path, chosen per platform |
| macOS native libraries | OpenMP-linked libraries (XGBoost, LightGBM) fail to import on macOS without `libomp` — install it in the macOS CI job (§5) |
| Timestamp collisions | Coarse Windows clock resolution makes back-to-back snapshots collide — the collision-guard test must run on Windows CI, not only Linux |

---

## 5. CI Delta

Pipeline stages · gates · caching · artifact handling · release automation → [cicd](../cicd/STANDARDS.md). MCP-specific additions:

| Requirement | Value | Why MCP-specific |
|---|---|---|
| OS matrix | All three: Linux · macOS · Windows, `fail-fast: false` | Users install on all three; Windows carries Defender, path-length, and clock-resolution behaviour no other runner reproduces |
| Constrained mode in CI env | `MCP_CONSTRAINED_MODE=1` | The small-limit path is the one shipping to 8 GB users — it must be the path CI exercises |
| Import root in CI env | Repo root on the module search path | `shared/` imports resolve locally but fail on CI without it |
| macOS native step | Install `libomp` before dependency sync, conditional on the macOS runner | Without it, OpenMP-linked imports fail outright |
| Docstring gate | A script that walks every registered tool and fails the build on a docstring over 80 characters | The 80-char rule ([TOOLS.md](TOOLS.md)) is invisible to linters — it needs its own gate |
| Type-check scope | The full server package, including `_{tier}_*` sub-modules | Sub-module splits silently escape a narrower type-check path |
| Notebook exclusion | Configured in the project file, ✗ as a CLI flag | A flag applies to CI only; config applies to CI and every contributor |

`fail-fast: false` is load-bearing: one platform failing must not hide failures on the other two.

---

## 6. Release

Tagging · semver → [git](../git/STANDARDS.md). Release automation → [cicd](../cicd/STANDARDS.md).

MCP delta: the release job runs the **full three-OS matrix first** and only then publishes. A server that fails on Windows must never be taggable, because Windows is the majority install target. Pre-release tags (`-rc`, `-beta`, `-alpha`) publish as prereleases automatically.

---

## 7. The Install Model

The install target is a user with no terminal fluency. **✗ require terminal commands to install.**

The canonical mechanism is a **self-updating client config entry**: the AI client's config holds the full bootstrap command. On every launch it clones the repo if absent, fetches and resets to the remote head, syncs dependencies from the lockfile, and starts the server. No separate install step exists. `install.sh` / `install.bat` are convenience wrappers, not the primary path.

Install location — always, without asking the user to choose:

| OS | Path |
|---|---|
| Windows | `%USERPROFILE%\.mcp_servers\{REPO_NAME}` |
| macOS | `~/.mcp_servers/{REPO_NAME}` |
| Linux | `~/.mcp_servers/{REPO_NAME}` |

First launch installs all dependencies (2–5 minutes) and can exceed the client's ~60-second connection timeout. Two mitigations, both required: the README documents a one-line pre-install command, and it documents that pressing **Restart** in the client's server panel completes the install on the second attempt.

---

## 8. Launch Command Rules

| Rule | Detail |
|---|---|
| Clone guard | Check for the `.git` subfolder, ✗ only the directory. A directory without `.git` is a broken partial clone → remove it, then clone fresh |
| Update method | Fetch, then hard-reset to the fetched head. **✗ `git pull`** — it fails on a detached HEAD or a dirty tree; fetch + reset never does |
| Dependency sync | Lockfile sync on every launch — JIT install keeps users current with no separate step. ✗ call `pip` in a launch command |
| Env var | `MCP_CONSTRAINED_MODE` — the fixed name. ✗ a project-specific alternative ([RUNTIME.md](RUNTIME.md)) |
| Timeout | `600000` ms (10 minutes) — covers first-run clone plus install |
| Shell | PowerShell with `-NoProfile -ExecutionPolicy Bypass` on Windows; `bash -c` on macOS/Linux |
| Quiet flags | Every git and sync command runs quiet — their stdout would otherwise reach the client before the protocol handshake |

---

## 9. Client Registration

A project that ships an automated config writer obeys:

- Parse the existing config with a tolerant JSON reader — client config files legally contain comments and trailing commas
- **Append-only** — ✗ modify or remove an entry the writer did not create
- Idempotent — running it twice is safe and changes nothing the second time
- Write strict, valid JSON
- Write atomically (temp + rename) — a half-written config bricks the user's AI client

Client config locations:

| Client | macOS | Windows |
|---|---|---|
| LM Studio | `~/Library/Application Support/LM Studio/mcp.json` | `%APPDATA%\LM Studio\mcp.json` |
| Claude Desktop | `~/Library/Application Support/Claude/claude_desktop_config.json` | `%APPDATA%\Claude\claude_desktop_config.json` |
| Cursor | `~/.cursor/mcp.json` | `~/.cursor/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` | `~/.codeium/windsurf/mcp_config.json` |

---

## 10. README Contract

Doc types · structure conventions → [documentation](../documentation/STANDARDS.md). Every MCP server README carries these sections, in this order:

1. Title + one-line description ending in: self-hosted · no cloud APIs · no API keys
2. **File-path-only warning** — present whenever tools take file arguments; the user must pass a path, ✗ use the client's attachment button
3. Features — tool count per tier · the LOCATE → INSPECT → PATCH → VERIFY loop · version control · receipt log · constrained mode
4. Quick install — requirements · platform support table · first-run note · config block · numbered client steps
5. Available tools — one table per tier: tool name · purpose
6. Configuration — environment variable table
7. Uninstall — remove the client entry · delete the install directory
8. Architecture — directory tree
9. Development — local test commands
10. License

README rules:

| Rule | Detail |
|---|---|
| Tested-platform honesty | State exactly which platform was verified by hand and which are CI-only. ✗ imply hand-verification that did not happen |
| Python version wording | "Python 3.12 or higher" — exact wording |
| Hardware claims | RAM only. ✗ GPU model · CPU model · disk specs |
| Library lists | ✗ name libraries in the feature list — features are capabilities, not dependencies |
| Timeout note | The first-run timeout + Restart-button instruction is always present |
| Local-execution note | Always present: no data leaves the machine · effective context on 8 GB with a 9B model is ~10,000–12,000 tokens · run one focused task per session, then start a fresh chat · fewer loaded tools means more context for real work |

---

## 11. Agent and Code Documentation

Every repo an AI coding agent works in carries a `CLAUDE.md` covering: project overview · repository structure · architecture principles (engine/server split · tool count limits · surgical read · snapshot-before-write · self-hosted execution) · domain-specific tool design rules · the prohibitions list · a progress tracker.

Two docstring registers, ✗ interchangeable:

| Location | Register |
|---|---|
| Tool docstring in `server.py` | ≤ 80 characters · machine-readable selection cue for the model ([TOOLS.md](TOOLS.md)) |
| Engine function docstring | Full human-readable explanation: what it does · that it snapshots · what the returned dict contains · that it never raises |

---

## 12. Domain Reference Table

Maps a domain to a compliant local execution engine — every entry satisfies the self-hosted execution principle ([STANDARDS.md](STANDARDS.md)).

| Domain | Server name | Primary local engine |
|---|---|---|
| Document editing | `office_basic` | python-docx · openpyxl · python-pptx |
| PDF processing | `pdf_basic` | PyMuPDF · pdfplumber · reportlab |
| Data analytics | `data_basic` / `_medium` / `_advanced` | polars · duckdb · pandas · ydata-profiling |
| SQL analytics | `sql_basic` | DuckDB · SQLite |
| Machine learning | `ml_basic` / `_medium` / `_advanced` | scikit-learn · XGBoost · LightGBM |
| Deep learning | `dl_basic` | PyTorch · ONNX Runtime |
| OCR | `ocr_basic` | easyocr · surya · pytesseract |
| Image processing | `image_basic` | Pillow · OpenCV · scikit-image |
| Video processing | `video_basic` | MoviePy · FFmpeg (subprocess) |
| Web scraping | `web_basic` | Playwright · BeautifulSoup · httpx |
| System monitoring | `sys_basic` | psutil · py-cpuinfo |
| Geospatial | `geo_basic` | geopandas · shapely · rasterio |

---

## 13. Checklist

- [ ] Tests import `engine.py` directly; no unit test spins up a server process
- [ ] stdio and HTTP smoke tests exist and assert a clean protocol channel
- [ ] Every write tool has all 11 contract tests from §2
- [ ] A test proves an invalid op array leaves no `.bak` file behind
- [ ] Every read tool has a truncation test asserting `"truncated"` and `"total_available"`
- [ ] Fixtures include `simple`, `messy`, and `large` categories, committed to the repo
- [ ] The `messy` fixture carries encoding variants and malformed rows
- [ ] Path-traversal tests use a genuinely outside-home path per platform
- [ ] CI matrix runs Linux, macOS, and Windows with `fail-fast: false`
- [ ] CI sets `MCP_CONSTRAINED_MODE=1` and the repo root on the import path
- [ ] CI installs `libomp` on the macOS runner when OpenMP libraries are used
- [ ] CI fails the build on any tool docstring over 80 characters
- [ ] CI type-checks the full server package including `_{tier}_*` sub-modules
- [ ] Notebook exclusion is configured in the project file, not as a CLI flag
- [ ] Release runs the full three-OS matrix before publishing
- [ ] Install requires zero terminal commands from the user
- [ ] Launch command guards on the `.git` subfolder, not the directory
- [ ] Launch command uses fetch + hard reset, never `git pull`
- [ ] Launch command sets a 10-minute timeout and syncs from the lockfile
- [ ] Install path is `~/.mcp_servers/{REPO_NAME}`; the user is never asked to choose
- [ ] Config writer is append-only, idempotent, and writes atomically
- [ ] README follows the §10 section order and carries the first-run timeout note
- [ ] README states honestly which platforms were hand-verified vs CI-only
- [ ] `CLAUDE.md` exists and carries the prohibitions list
- [ ] Tool docstrings and engine docstrings use their correct separate registers
