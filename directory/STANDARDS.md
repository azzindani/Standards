# Directory & Project Structure Standards

Rules for organizing files, directories, and project layout.
Language-agnostic — language-specific conventions live in their respective standards.

Composable with: Architecture Standards (tier model → directory mapping),
Code Writing Standards (file content rules), Git Standards (repository files),
CI/CD Standards (pipeline config placement).

---

## Table of Contents

1. [Root Directory Layout](#1-root-directory-layout)
2. [Source Organization by Tier](#2-source-organization-by-tier)
3. [Test Directory Structure](#3-test-directory-structure)
4. [Configuration Files](#4-configuration-files)
5. [Build & Output](#5-build--output)
6. [File Naming Conventions](#6-file-naming-conventions)
7. [Directory Naming](#7-directory-naming)
8. [Separation Rules](#8-separation-rules)
9. [Monorepo vs Multi-Repo](#9-monorepo-vs-multi-repo)
10. [Scale Matrix](#10-scale-matrix)
11. [Directory Checklist](#11-directory-checklist)

---

## 1. Root Directory Layout

Project root contains only top-level entry points, metadata, and directory anchors.
✗ source files at root · ✗ deeply nested config at root · ✗ test files at root.

### Required Root Items

| Item | Type | Purpose |
|---|---|---|
| `README.md` | File | Project overview · setup · usage |
| `src/` or language equivalent | Dir | All source code entry point |
| `tests/` | Dir | All test code entry point |
| `docs/` | Dir | Documentation beyond README |
| Config files (lock, manifest) | Files | Language package manager files |
| `.gitignore` | File | VCS exclusion rules |

### Optional Root Items

| Item | Type | When Present |
|---|---|---|
| `config/` | Dir | Multiple config files exist |
| `scripts/` | Dir | Build/dev/deploy helper scripts |
| `tools/` | Dir | Project-specific tooling |
| `data/` | Dir | Static data, fixtures, seeds |
| `examples/` | Dir | Usage examples, demos |
| `vendor/` or `third_party/` | Dir | Vendored dependencies |
| `Makefile` / `Taskfile` / equiv | File | Task runner present |
| `Dockerfile` / `compose.yaml` | File | Containerization used |
| `CHANGELOG.md` | File | Release history maintained |
| `LICENSE` | File | Open source / shared projects |
| `CLAUDE.md` | File | AI assistant instructions |

### Root Hygiene Rules

- Maximum 15 items visible at root (dirs + files). Above 15 → consolidate.
- Every root directory has clear, singular purpose. ✗ catch-all dirs (`misc/`, `stuff/`, `other/`).
- Root config files: flat, not nested. One file per tool. If tool needs a directory, use `config/`.
- Hidden files/dirs (`.` prefix) reserved for tooling config (`.gitignore`, `.env`, `.vscode/`).

---

## 2. Source Organization by Tier

Map architecture tiers (see `architecture/STANDARDS.md` §2) to directories.
Tier boundaries in code = directory boundaries on disk.

### Standard Layout

| Tier | Directory | Contains |
|---|---|---|
| 0 — Kernel | `src/kernel/` or `src/core/` | Types · constants · enums · pure utilities |
| 1 — Engine | `src/engine/` or `src/domain/` | Domain logic · transforms · validators |
| 2 — Service | `src/service/` or `src/orchestration/` | Use cases · workflow composition |
| 3 — Interface | `src/interface/` or `src/adapters/` | CLI · API · MCP · file/network/DB I/O |

### Tier Directory Rules

| Rule | Detail |
|---|---|
| One tier = one top-level dir under `src/` | ✗ mixing tiers in same directory |
| Imports follow tier order | Files in `engine/` import from `kernel/`, never from `service/` or `interface/` |
| Each tier dir may have subdirs | Subdirs group by domain concept, not by file type |
| Shared types across tiers → Tier 0 | If multiple tiers need a type, it lives in `kernel/` |

### Within-Tier Subdirectory Organization

Group by domain concept (feature/capability), not by technical role.

| Pattern | When | Example |
|---|---|---|
| Feature-based | Default — multiple features exist | `engine/parsing/`, `engine/validation/` |
| Flat | Tier has < 5 files | Files directly in `engine/` |
| Hybrid | Large tiers with cross-cutting concerns | Feature dirs + `common/` subdir |

✗ Group by file type within a tier (`models/`, `utils/`, `helpers/`). These categories grow unbounded and obscure feature boundaries.

### Interface Tier Subdirectories

Tier 3 groups by adapter type — each I/O channel gets its own subdir.

| Subdir | Purpose |
|---|---|
| `interface/cli/` | Command-line entry points |
| `interface/api/` | HTTP/REST/GraphQL handlers |
| `interface/mcp/` | MCP server tools |
| `interface/storage/` | File system · database adapters |
| `interface/external/` | Third-party API clients |

---

## 3. Test Directory Structure

Tests mirror source structure. Finding the test for any source file is mechanical, not a search.

### Mirror Rule

Every source file `src/<tier>/<feature>/<module>` has a corresponding test file at `tests/<tier>/<feature>/test_<module>` (or language-equivalent naming).

| Source Path | Test Path |
|---|---|
| `src/kernel/types` | `tests/kernel/test_types` |
| `src/engine/parsing/parser` | `tests/engine/parsing/test_parser` |
| `src/service/workflow` | `tests/service/test_workflow` |
| `src/interface/cli/main` | `tests/interface/cli/test_main` |

### Test Directory Layout

| Directory | Contains |
|---|---|
| `tests/` | Root — mirrors `src/` tier structure |
| `tests/kernel/` | Tier 0 unit tests |
| `tests/engine/` | Tier 1 unit tests |
| `tests/service/` | Tier 2 unit + integration tests |
| `tests/interface/` | Tier 3 integration tests |
| `tests/integration/` | Cross-tier integration tests |
| `tests/e2e/` | End-to-end / system tests |
| `tests/fixtures/` | Shared test data · sample files |
| `tests/conftest` or `tests/helpers` | Shared test utilities · factories |

### Test File Naming

| Convention | Rule |
|---|---|
| Prefix | `test_` prefix on file name (language-dependent; some use `_test` suffix) |
| Match source name | Test file name includes source module name |
| One test file per source file | ✗ mega test files covering multiple modules |
| Fixture files | Descriptive name matching the scenario they support |

### Test Data Placement

| Data Type | Location |
|---|---|
| Small inline data | Inside test file |
| Shared fixtures (< 1 MB) | `tests/fixtures/` |
| Large test data (> 1 MB) | `tests/fixtures/` + `.gitignore` or external fetch |
| Generated test data | Created in test setup, cleaned in teardown; ✗ committed |
| Snapshot/golden files | `tests/snapshots/` or `tests/golden/` adjacent to test |

---

## 4. Configuration Files

Where configuration lives and how it is organized on disk.
See `architecture/STANDARDS.md` §8 for cascade and loading rules.

### Placement Rules

| Config Type | Location | Committed |
|---|---|---|
| Project manifest (package.json, Cargo.toml, etc.) | Root | Yes |
| Lock file | Root | Yes |
| Tool config (linter, formatter, type checker) | Root (single file) or `config/` (multiple) | Yes |
| Environment defaults | `.env.example` at root | Yes |
| Environment secrets | `.env` at root | ✗ Never |
| Application config | `config/` dir | Yes |
| Config schema / shape definition | `src/kernel/` (Tier 0) | Yes |
| Runtime/deployment config | `config/` or `deploy/` | Depends on content |

### Config Directory Structure

When `config/` exists:

| File/Dir | Purpose |
|---|---|
| `config/default` | Base configuration — works for local dev |
| `config/production` | Production overrides |
| `config/test` | Test environment overrides |
| `config/schema` | Config validation schema (optional if in Tier 0) |

### Rules

- One config file per concern. ✗ monolithic config file covering unrelated systems.
- Config files at root only when a single file suffices. Multiple config files → `config/` dir.
- Schema/shape definitions live in source (Tier 0), not in `config/`. Config files hold values, source holds structure.
- `.env` files: `.env.example` committed with placeholder keys and no values. `.env` in `.gitignore` — always.
- Secrets ✗ in any committed file, any directory, any format. See `security/STANDARDS.md`.

---

## 5. Build & Output

Build artifacts, generated code, compiled output, and temporary files.

### Output Directories

| Directory | Contains | Committed |
|---|---|---|
| `build/` or `dist/` | Compiled/bundled output | ✗ Never |
| `out/` or `output/` | Runtime-generated output (reports, exports) | ✗ Never |
| `gen/` or `generated/` | Code generation output | Depends — see rules below |
| `coverage/` | Test coverage reports | ✗ Never |
| `tmp/` or `.cache/` | Temporary/cached files | ✗ Never |
| `vendor/` | Vendored dependencies (if strategy requires) | Language-dependent |
| `node_modules/`, `target/`, `__pycache__/` | Language-specific build/dep dirs | ✗ Never |

### Rules

- All output dirs listed in `.gitignore`. No build artifacts in version control.
- Generated code: commit only when generation cannot run during build. If CI can regenerate → ✗ commit.
- Output dir name matches its purpose. ✗ reuse `build/` for both compiled code and reports.
- Build output is fully reproducible from source. Deleting all output dirs + rebuilding = identical result.
- ✗ source code references paths inside build/output dirs. Source depends on source; build depends on source.

---

## 6. File Naming Conventions

Consistent file naming across entire project. One convention per project — no mixing.

### Case Style Selection

| Style | When | Example |
|---|---|---|
| `snake_case` | Default for most languages (Python, Rust, C, Ruby) | `user_profile.py` |
| `kebab-case` | Web projects, CSS, HTML, YAML/JSON configs | `user-profile.ts` |
| `PascalCase` | Languages where convention requires it (C#, Java class files) | `UserProfile.java` |
| `camelCase` | ✗ for file names — use only inside code | — |

Pick one per project. All source files follow it. Config files follow tool requirements.

### File Name Rules

| Rule | Detail |
|---|---|
| Descriptive, specific | Name describes content, not role. `invoice_parser` ✗ `parser` |
| No generic names | ✗ `utils`, `helpers`, `misc`, `common`, `shared` as standalone files |
| Singular nouns for modules | `user.py` ✗ `users.py` ; file represents the concept, not a collection |
| Match primary export | File name matches primary type/function/class it exports |
| No redundant prefixes | ✗ `user_model.py` in `models/` → `user.py` in `models/` |
| No abbreviations | `configuration` ✗ `cfg` · `message` ✗ `msg` ; except universally known (`db`, `http`, `api`) |
| Lowercase always | ✗ uppercase in file names ; PascalCase is only exception (see table above) |

### Special File Naming

| Type | Convention |
|---|---|
| Entry point | `main`, `app`, `cli`, `server` — clear what it launches |
| Module init | Language convention: `__init__.py`, `mod.rs`, `index.ts` |
| Test files | `test_<module>` prefix or `<module>_test` suffix — match language convention |
| Config files | Named by tool: `.eslintrc`, `pyproject.toml`, `tsconfig.json` |
| Constants/types | `types`, `constants`, `enums` — in Tier 0 only |
| Scripts | Verb-first: `setup_db`, `run_migration`, `generate_docs` |

---

## 7. Directory Naming

### Rules

| Rule | Detail |
|---|---|
| Lowercase always | ✗ uppercase or mixed-case directory names |
| `snake_case` or `kebab-case` | Match project's file naming convention |
| Singular nouns | `model/` ✗ `models/` · `test/` or `tests/` (follow language convention) |
| Maximum 3 levels deep under `src/` | `src/tier/feature/subfeature/` is the deepest allowed |
| Descriptive purpose | Name answers "what lives here?" — not "what type is it?" |
| No generic containers | ✗ `common/`, `shared/`, `misc/`, `other/`, `stuff/`, `general/` at any level |

### Singular vs Plural Exceptions

| Always Singular | Always Plural |
|---|---|
| Tier dirs: `kernel/`, `engine/`, `service/`, `interface/` | `tests/` (language convention) |
| Feature dirs: `auth/`, `parsing/`, `billing/` | `docs/` (convention) |
| Adapter dirs: `cli/`, `api/`, `storage/` | `scripts/` (convention) |
| Domain concept dirs | `examples/` (convention) |

### Depth Limits

| Level | Contains | Example Path |
|---|---|---|
| 1 | Tier or top-level purpose | `src/engine/` |
| 2 | Feature / domain concept | `src/engine/parsing/` |
| 3 | Sub-feature (rare, justified) | `src/engine/parsing/html/` |
| 4+ | ✗ Prohibited | Restructure → flatten or extract module |

Deeper nesting signals a module trying to do too much. Extract to its own top-level feature directory.

---

## 8. Separation Rules

What goes together, what stays apart. Correct separation reduces coupling and makes navigation predictable.

### Co-location Principle

Files that change together live together. Files that change independently live apart.

| Together | Apart |
|---|---|
| Feature implementation files (same feature) | Implementation + tests (separate root dirs) |
| Type definitions + functions that operate on them | Types used across features → Tier 0 |
| Feature config + feature code | Infrastructure config + application code |
| Adapter + adapter-specific types | Adapter + core domain types |

### Boundary Rules

| Boundary | Separation |
|---|---|
| Tier boundary | Physical directory separation — always |
| Feature boundary | Subdirectory separation within tier |
| I/O boundary | Tier 3 dir. ✗ I/O code in Tier 0–2 dirs |
| Test boundary | `tests/` root dir. ✗ test files mixed with source |
| Generated boundary | `gen/` or `generated/` dir. ✗ generated files mixed with authored code |
| Config boundary | Root or `config/` dir. ✗ config values embedded in source dirs |
| Script boundary | `scripts/` dir. ✗ utility scripts scattered in source tree |

### Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| `utils/` mega-directory | Unbounded growth, no cohesion | Distribute to feature dirs or Tier 0 |
| `types/` separate from logic | Splits related code artificially | Co-locate types with their operations |
| Test files next to source | Pollutes source tree, confuses tooling | Mirror structure under `tests/` |
| Config scattered in source | No single place to find settings | Centralize in `config/` or root |
| Multiple entry points at root | Unclear which to run | One entry point, or `scripts/` dir |
| Flat `src/` with 30+ files | Unnavigable, no organization | Group into tier dirs + feature subdirs |
| Nested 5+ levels deep | Excessive path lengths, navigation pain | Flatten — max 3 levels under `src/` |

---

## 9. Monorepo vs Multi-Repo

### Decision Criteria

| Factor | Monorepo | Multi-Repo |
|---|---|---|
| Team count | Single team · tightly coupled teams | Independent teams · different cadences |
| Shared code | Extensive shared kernel/libraries | Minimal sharing · API contracts only |
| Deploy coupling | Components deploy together | Components deploy independently |
| Build system | Unified build (Bazel, Nx, Turborepo) available | Standard per-project tooling |
| Scale | < 50 developers on shared code | > 50 developers or organizational boundaries |

### Monorepo Structure

```
repo/
├── packages/            ← shared libraries
│   ├── kernel/          ← shared Tier 0 (types, constants)
│   ├── common-engine/   ← shared Tier 1 (domain logic)
│   └── ui-components/   ← shared presentational code
├── apps/                ← deployable applications
│   ├── api-server/      ← each app has full tier structure inside
│   ├── web-client/
│   └── cli-tool/
├── tools/               ← build tools, code generators, scripts
├── config/              ← shared configuration
└── docs/                ← shared documentation
```

### Monorepo Rules

| Rule | Detail |
|---|---|
| Each app has internal tier structure | `apps/api-server/src/kernel/`, `apps/api-server/src/engine/`, etc. |
| Shared code lives in `packages/` | ✗ apps importing directly from other apps |
| Package dependency = explicit | Declared in manifest, not implicit path imports |
| One `tests/` per app + per package | Tests live adjacent to the code they test |
| Shared config at root | Per-app overrides inside app dir |
| Workspace-aware tooling required | Build/test/lint must understand package boundaries |

### Multi-Repo Rules

| Rule | Detail |
|---|---|
| Each repo = one deployable unit | Or one shared library with versioned releases |
| Shared code = published packages | Versioned, released, consumed via package manager |
| Contract-first communication | API specs/schemas in dedicated contract repo or embedded in provider |
| Independent CI/CD | Each repo builds, tests, deploys on its own |
| ✗ cross-repo path references | Dependencies via package manager only |
| ✗ git submodules for shared code | Use versioned packages instead — submodules create hidden coupling |

### Hybrid: Multi-Repo with Shared Standards

When multiple repos share conventions but not code:
- Standards repo (this repo) provides rules, not runtime code.
- Each project repo applies standards independently.
- Shared tooling (linters, templates) published as packages, consumed via package manager.

---

## 10. Scale Matrix

Directory structure scales with project complexity. See `architecture/STANDARDS.md` §12 for full scale rules.

### PoC / Script (1–5 files)

| Aspect | Rule |
|---|---|
| Source structure | Flat — all files at root or single `src/` dir |
| Tiers | None — single-tier acceptable |
| Tests | Single `test_` file or `tests/` dir with 1–2 files |
| Config | Inline defaults · single `.env.example` if needed |
| Nesting | Maximum 1 level |
| Root items | ≤ 5 |

### Small Project (5–30 files)

| Aspect | Rule |
|---|---|
| Source structure | `src/` with 2-tier split: logic + I/O |
| Tiers | 2 tiers minimum: `src/core/` + `src/interface/` (or equivalent) |
| Tests | `tests/` mirroring source structure |
| Config | Root config files · `.env.example` |
| Nesting | Maximum 2 levels under `src/` |
| Root items | ≤ 10 |

### Production System (30+ files)

| Aspect | Rule |
|---|---|
| Source structure | Full 4-tier `src/` layout |
| Tiers | `kernel/` · `engine/` · `service/` · `interface/` |
| Tests | Full `tests/` mirror + `integration/` + `e2e/` + `fixtures/` |
| Config | `config/` dir with environment variants · schema in Tier 0 |
| Nesting | Maximum 3 levels under `src/` |
| Root items | ≤ 15 |
| Docs | `docs/` with architecture decision records |
| Scripts | `scripts/` for build/deploy automation |

### Scale Transitions

When project crosses a scale boundary, restructure incrementally:

| Transition | Key Actions |
|---|---|
| PoC → Small | Create `src/` · split I/O from logic · add `tests/` mirror |
| Small → Production | Split into 4 tiers · add `config/` · add `scripts/` · add `docs/` |
| Single-repo → Monorepo | Extract shared code to `packages/` · move apps to `apps/` |

Apply Strangler Fig pattern (see `architecture/STANDARDS.md` §11): move files incrementally, update imports, verify tests pass at each step. ✗ big-bang restructure.

---

## 11. Directory Checklist

### New Project Setup

- [ ] Root layout follows §1 — README, src/, tests/, .gitignore present
- [ ] ≤ 15 items at root level
- [ ] Source organized by tier per §2 (appropriate to project scale)
- [ ] Test structure mirrors source per §3
- [ ] Config placement follows §4 — secrets excluded from VCS
- [ ] Build/output dirs in `.gitignore` per §5
- [ ] File naming convention chosen and applied consistently per §6
- [ ] Directory naming follows §7 — lowercase, singular, ≤ 3 levels under src/
- [ ] No anti-patterns from §8 present (no `utils/`, no mixed tiers, no scattered config)
- [ ] Monorepo/multi-repo decision made per §9 criteria

### New Module / Feature

- [ ] Placed in correct tier directory
- [ ] Feature files grouped in subdirectory (if tier has 5+ files)
- [ ] Corresponding test directory/file created in `tests/`
- [ ] No new generic dirs (`utils/`, `helpers/`, `common/`) introduced
- [ ] File names follow project convention — descriptive, no abbreviations
- [ ] Import direction respects tier model (inward only)
- [ ] No new nesting beyond 3 levels under `src/`

### Code Review — Structure Check

- [ ] New files placed in correct tier directory
- [ ] File names match naming convention
- [ ] No I/O code added to Tier 0–2 directories
- [ ] No test files mixed into source directories
- [ ] No generated files mixed with authored code
- [ ] No config values embedded in source directories
- [ ] No directory depth violations (4+ levels under `src/`)
- [ ] Root item count still ≤ 15
