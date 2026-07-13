# Directory Standards

> Rules for where files and directories live, what they are named, and how project layout scales.

**ID** `directory` · **Tier** Foundation · **Version** 1.0
**Owns** root layout · source organization · test tree layout · build/output placement · file naming · directory naming · separation rules · repository topology
**Defers to** identifier naming inside code → [code_writing](../code_writing/STANDARDS.md) · layer model · dependency direction → [architecture](../architecture/STANDARDS.md) · module responsibility · cohesion → [design](../design/STANDARDS.md) · config cascade · env precedence · secret storage → [configuration](../configuration/STANDARDS.md) · test strategy · coverage → [testing](../testing/STANDARDS.md) · ignore rules · history → [git](../git/STANDARDS.md) · pipeline definitions → [cicd](../cicd/STANDARDS.md) · doc content → [documentation](../documentation/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Root Layout](#2-root-layout)
3. [Source Organization](#3-source-organization)
4. [Test Tree](#4-test-tree)
5. [Configuration Placement](#5-configuration-placement)
6. [Build and Output](#6-build-and-output)
7. [File Naming](#7-file-naming)
8. [Directory Naming](#8-directory-naming)
9. [Separation Rules](#9-separation-rules)
10. [Repository Topology](#10-repository-topology)
11. [Anti-Patterns](#11-anti-patterns)
12. [Scale Matrix](#12-scale-matrix)
13. [Checklist](#13-checklist)

---

## 1. Principles

| # | Principle |
|---|---|
| 1 | Layer boundaries in code = directory boundaries on disk. Layer model → [architecture](../architecture/STANDARDS.md) §2 |
| 2 | Location is derivable. A reader predicts a file's path from its purpose without searching |
| 3 | Group by domain concept · ✗ by technical role |
| 4 | Files that change together live together; files that change independently live apart |
| 5 | Every directory answers "what lives here?" with one word. No catch-alls |
| 6 | Generated ✗ mixed with authored. Test ✗ mixed with source. Config ✗ mixed with logic |
| 7 | Naming scope split: this standard governs **file and directory names**; identifiers inside code → [code_writing](../code_writing/STANDARDS.md) |

---

## 2. Root Layout

Root holds entry points, metadata, and directory anchors. ✗ source files at root · ✗ test files at root.

### Required

| Item | Type | Purpose |
|---|---|---|
| `README.md` | File | Project overview · setup · usage |
| `src/` or language equivalent | Dir | All source code |
| `tests/` | Dir | All test code |
| `.gitignore` | File | VCS exclusion rules |
| Package manifest + lock file | Files | Dependency declaration + pinning |

### Optional

| Item | Present when |
|---|---|
| `docs/` | Documentation exceeds README |
| `config/` | More than one config file exists |
| `scripts/` | Build/dev/deploy helper scripts exist |
| `tools/` | Project-specific tooling exists |
| `data/` | Static data · fixtures · seeds exist |
| `examples/` | Usage examples shipped |
| `vendor/` \| `third_party/` | Dependencies vendored |
| `Makefile` \| `Taskfile` | Task runner used |
| `Dockerfile` \| `compose.yaml` | Containerization used |
| `CHANGELOG.md` | Release history maintained |
| `LICENSE` | Shared or open-source project |
| `CLAUDE.md` \| `AGENTS.md` | AI agent instructions maintained |

### Rules

- Max 15 visible items at root (dirs + files). Above 15 → consolidate.
- Every root directory has one singular purpose. ✗ `misc/` · ✗ `stuff/` · ✗ `other/`.
- Root config files are flat, one file per tool. Tool needing a directory → `config/`.
- Dot-prefixed entries reserved for tooling config (`.gitignore` · `.env` · `.github/`).
- One entry point. Multiple runnable entry points → `scripts/` or a single dispatching CLI.

---

## 3. Source Organization

### Layer → Directory

| Layer | Directory | Contains |
|---|---|---|
| Inner | `src/kernel/` \| `src/core/` | Types · constants · enums · pure utilities |
| Mid-inner | `src/engine/` \| `src/domain/` | Domain logic · transforms · validators |
| Mid-outer | `src/service/` \| `src/orchestration/` | Use cases · workflow composition |
| Outer | `src/interface/` \| `src/adapters/` | CLI · API · MCP · file · network · DB I/O |

Layer count and names follow the system's own gradient (→ [architecture](../architecture/STANDARDS.md) §2). Directory structure mirrors it exactly — one layer, one top-level directory under `src/`.

### Rules

| Rule | Detail |
|---|---|
| One layer = one top-level dir under `src/` | ✗ mixing layers in the same directory |
| Imports follow layer order | Files in `engine/` import from `kernel/` · ✗ from `service/` or `interface/` |
| Subdirs group by domain concept | ✗ group by file type (`models/` · `utils/` · `helpers/`) — these grow unbounded and hide feature boundaries |
| Types shared across layers → innermost dir | Multiple layers need a type → it lives in `kernel/` |

### Within-Layer Structure

| Pattern | When |
|---|---|
| Flat — files directly in the layer dir | Layer has < 5 files |
| Feature subdirectories | Default — multiple features exist |
| Feature subdirs + one shared subdir | Large layer with genuine cross-cutting types |

### Outer-Layer Subdirectories

Group by I/O channel — one subdir per adapter type.

| Subdir | Purpose |
|---|---|
| `interface/cli/` | Command-line entry points |
| `interface/api/` | HTTP · REST · GraphQL · gRPC handlers |
| `interface/mcp/` | MCP server tools |
| `interface/storage/` | Filesystem · database adapters |
| `interface/external/` | Third-party API clients |

---

## 4. Test Tree

Tests mirror source. Locating the test for any source file is mechanical · ✗ a search.

### Mirror Rule

`src/<layer>/<feature>/<module>` → `tests/<layer>/<feature>/test_<module>` (or the language's equivalent naming).

| Source | Test |
|---|---|
| `src/kernel/types` | `tests/kernel/test_types` |
| `src/engine/parsing/parser` | `tests/engine/parsing/test_parser` |
| `src/interface/cli/main` | `tests/interface/cli/test_main` |

### Layout

| Directory | Contains |
|---|---|
| `tests/<layer>/` | Unit tests mirroring each source layer |
| `tests/integration/` | Cross-layer integration tests |
| `tests/e2e/` | End-to-end / system tests |
| `tests/fixtures/` | Shared test data · sample files |
| `tests/snapshots/` \| `tests/golden/` | Snapshot / golden files |
| `tests/conftest` \| `tests/helpers` | Shared test utilities · factories |

Test classification and pyramid ratios → [testing](../testing/STANDARDS.md).

### Rules

| Rule | Detail |
|---|---|
| One test file per source file | ✗ mega test files spanning multiple modules |
| Test file name contains the source module name | `test_<module>` prefix or `<module>_test` suffix — follow language convention |
| Small inline data lives in the test file | Anything shared → `tests/fixtures/` |
| Fixtures > 1 MB | `.gitignore` them + fetch externally, or generate in setup |
| Generated test data | Created in setup · removed in teardown · ✗ committed |

---

## 5. Configuration Placement

Placement on disk only. Cascade order · environment precedence · secret handling → [configuration](../configuration/STANDARDS.md).

| Artifact | Location | Committed |
|---|---|---|
| Package manifest · lock file | Root | Yes |
| Tool config (lint · format · types) | Root (single file) \| `config/` (multiple) | Yes |
| Environment template | `.env.example` at root | Yes |
| Environment secrets | `.env` at root | ✗ Never |
| Application config values | `config/` | Yes |
| Config schema / shape definition | `src/kernel/` (innermost layer) | Yes |
| Deployment config | `config/` \| `deploy/` | Only if it holds no secrets |

### Rules

- One config file per concern. ✗ one monolithic file spanning unrelated systems.
- Config at root only while a single file suffices. Two or more → `config/`.
- Schema lives in source, values live in config files. ✗ schema in `config/`.
- `.env.example` is committed with placeholder keys and empty values. `.env` is in `.gitignore` — always.
- Secrets ✗ in any committed file, any directory, any format → [security](../security/STANDARDS.md).

---

## 6. Build and Output

| Directory | Contains | Committed |
|---|---|---|
| `build/` \| `dist/` | Compiled / bundled output | ✗ Never |
| `out/` \| `output/` | Runtime-generated output (reports · exports) | ✗ Never |
| `gen/` \| `generated/` | Code-generation output | Only if generation cannot run during build |
| `coverage/` | Coverage reports | ✗ Never |
| `tmp/` \| `.cache/` | Temporary / cached files | ✗ Never |
| `node_modules/` · `target/` · `__pycache__/` | Language build + dependency dirs | ✗ Never |
| `vendor/` | Vendored dependencies | Only if the vendoring strategy requires it |

### Rules

- Every output directory is listed in `.gitignore`. ✗ build artifacts in version control.
- CI can regenerate it → ✗ commit it.
- One output directory per purpose. ✗ reuse `build/` for both compiled code and reports.
- Build output is fully reproducible: delete all output dirs → rebuild → identical result.
- ✗ source code referencing paths inside build/output dirs. Source depends on source; build depends on source.

---

## 7. File Naming

One case convention per project. ✗ mixing.

| Style | Use for | Example |
|---|---|---|
| `snake_case` | Default (Python · Rust · C · Ruby) | `user_profile.py` |
| `kebab-case` | Web · CSS · HTML · YAML/JSON config | `user-profile.ts` |
| `PascalCase` | Only where the language mandates it (C# · Java class files) | `UserProfile.java` |
| `camelCase` | ✗ never for file names | — |

### Rules

| Rule | Detail |
|---|---|
| Descriptive and specific | Name describes content · ✗ role. `invoice_parser` · ✗ `parser` |
| ✗ generic names | ✗ `utils` · `helpers` · `misc` · `common` · `shared` as standalone files |
| Singular nouns for modules | `user` · ✗ `users` — the file is the concept, not a collection |
| Match the primary export | File name matches the main type/function it exports |
| ✗ redundant prefixes | ✗ `user_model` inside `models/` → `user` |
| ✗ abbreviations | `configuration` · ✗ `cfg` ; `message` · ✗ `msg` ; **except** universally known: `db` · `http` · `api` · `id` |
| Lowercase | ✗ uppercase in file names ; **except** PascalCase where mandated above |

### Special Files

| Type | Convention |
|---|---|
| Entry point | `main` · `app` · `cli` · `server` — names what it launches |
| Module init | Language convention: `__init__.py` · `mod.rs` · `index.ts` |
| Test files | `test_<module>` prefix \| `<module>_test` suffix |
| Tool config | Named by the tool: `pyproject.toml` · `tsconfig.json` · `.eslintrc` |
| Types / constants | `types` · `constants` · `enums` — innermost layer only |
| Scripts | Verb-first: `setup_db` · `run_migration` · `generate_docs` |

---

## 8. Directory Naming

| Rule | Detail |
|---|---|
| Lowercase always | ✗ uppercase · ✗ mixed-case directory names |
| `snake_case` \| `kebab-case` | Match the project's file naming convention |
| Singular nouns | `model/` · ✗ `models/` — except the plural conventions below |
| Descriptive purpose | Name answers "what lives here?" · ✗ "what type is it?" |
| ✗ generic containers | ✗ `common/` · `shared/` · `misc/` · `other/` · `stuff/` · `general/` at any level |
| Max 3 levels under `src/` | `src/<layer>/<feature>/<subfeature>/` is the deepest permitted |

### Plural Exceptions

Plural is correct only where convention fixes it: `tests/` · `docs/` · `scripts/` · `examples/` · `packages/` · `apps/`. Everything else is singular — layer dirs (`kernel/` · `engine/` · `service/` · `interface/`), feature dirs (`auth/` · `parsing/` · `billing/`), adapter dirs (`cli/` · `api/` · `storage/`).

### Depth

| Level | Contains | Example |
|---|---|---|
| 1 | Layer or top-level purpose | `src/engine/` |
| 2 | Feature / domain concept | `src/engine/parsing/` |
| 3 | Sub-feature — rare, justified | `src/engine/parsing/html/` |
| 4+ | ✗ prohibited | Flatten, or extract to its own top-level feature dir |

Depth beyond 3 signals a module doing too much.

---

## 9. Separation Rules

### Co-location

| Together | Apart |
|---|---|
| Files of the same feature | Implementation ↔ tests (separate root dirs) |
| Type definitions + the functions that operate on them | Types used across features → innermost layer |
| Feature config + feature code | Infrastructure config ↔ application code |
| Adapter + adapter-specific types | Adapter ↔ core domain types |

### Boundaries

| Boundary | Separation |
|---|---|
| Layer | Physical directory separation — always |
| Feature | Subdirectory within the layer |
| I/O | Outer layer dir only. ✗ I/O code in inner-layer dirs |
| Test | `tests/` root. ✗ test files mixed into source |
| Generated | `gen/` \| `generated/`. ✗ generated files mixed with authored code |
| Config | Root \| `config/`. ✗ config values embedded in source dirs |
| Script | `scripts/`. ✗ utility scripts scattered through the source tree |

---

## 10. Repository Topology

### Decision

| Factor | Monorepo | Multi-repo |
|---|---|---|
| Teams | Single team · tightly coupled teams | Independent teams · different cadences |
| Shared code | Extensive shared kernel/libraries | Minimal sharing · API contracts only |
| Deploy coupling | Components ship together | Components ship independently |
| Build system | Workspace-aware build available | Standard per-project tooling |
| Headcount on shared code | < 50 developers | > 50 developers or hard org boundaries |

### Monorepo Layout

| Directory | Contains |
|---|---|
| `packages/` | Shared libraries — each with its own layer structure and `tests/` |
| `apps/` | Deployable applications — each with a full internal layer structure |
| `tools/` | Build tools · code generators · scripts |
| `config/` | Shared configuration; per-app overrides live inside the app dir |
| `docs/` | Shared documentation |

| Rule | Detail |
|---|---|
| Each app has a full internal layer structure | `apps/<app>/src/kernel/` · `apps/<app>/src/engine/` · … |
| Shared code lives in `packages/` | ✗ an app importing directly from another app |
| Package dependencies declared in the manifest | ✗ implicit path imports across packages |
| One `tests/` per app and per package | Tests live with the code they cover |
| Workspace-aware tooling required | Build · test · lint must understand package boundaries |

### Multi-repo Rules

| Rule | Detail |
|---|---|
| One repo = one deployable unit \| one versioned library | ✗ two deployables in one repo |
| Shared code = published, versioned packages | Consumed through the package manager |
| Contract-first communication | API specs live with the provider or in a dedicated contract repo |
| Independent CI/CD per repo | Each repo builds, tests, deploys on its own |
| ✗ cross-repo path references | Dependencies through the package manager only |
| ✗ git submodules for shared code | Submodules create hidden coupling — use versioned packages |

---

## 11. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| `utils/` mega-directory | Unbounded growth · zero cohesion | Redistribute to feature dirs or the innermost layer |
| `types/` split from its logic | Splits code that changes together | Co-locate types with their operations; only cross-layer types go inward |
| Test files beside source | Pollutes the source tree · confuses tooling | Mirror the source structure under `tests/` |
| Config scattered through source | No single place to find settings | Centralize in root or `config/` |
| Multiple entry points at root | Unclear what to run | One entry point, or `scripts/` |
| Flat `src/` with 30+ files | Unnavigable · no layer boundary | Group into layer dirs + feature subdirs |
| Nesting 4+ levels deep | Long paths · navigation pain | Flatten — max 3 levels under `src/` |
| Grouping by file type | `models/` · `views/` · `helpers/` hide feature boundaries | Group by domain concept |
| Build artifacts committed | Diff noise · merge conflicts · stale binaries | `.gitignore` every output dir |
| Layer dir importing outward | Directory layout no longer reflects architecture | Fix the import — directories are the enforcement surface |

---

## 12. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Source structure | Flat — single dir | `src/` with 2 layers: core + boundary | Full layer stack under `src/` |
| Layer dirs | None | `src/core/` + `src/interface/` | `kernel/` · `engine/` · `service/` · `interface/` |
| Test tree | 1–2 test files | `tests/` mirroring source | Full mirror + `integration/` + `e2e/` + `fixtures/` |
| Config | Inline defaults + `.env.example` | Root config files | `config/` with environment variants · schema in innermost layer |
| Nesting under `src/` | ≤ 1 level | ≤ 2 levels | ≤ 3 levels |
| Root items | ≤ 5 | ≤ 10 | ≤ 15 |
| Docs | README only | README + `docs/` | `docs/` with decision records |
| Scripts | None | Task runner file | `scripts/` for build + deploy automation |

### Transitions

| Transition | Actions |
|---|---|
| Prototype → Production | Create `src/` · split I/O from logic · add `tests/` mirror |
| Production → Scale | Split into full layer dirs · add `config/` · add `scripts/` · add `docs/` |
| Single repo → Monorepo | Extract shared code to `packages/` · move apps to `apps/` |

Restructure incrementally — move files, update imports, tests green at each step. ✗ big-bang restructure. Strangler Fig → [architecture](../architecture/STANDARDS.md) §10.

---

## 13. Checklist

- [ ] ≤ 15 items visible at root (§2)
- [ ] `README.md` · `src/` · `tests/` · `.gitignore` · manifest + lock file all present at root (§2)
- [ ] Zero source files and zero test files at root (§2)
- [ ] Exactly one entry point, or entry points collected in `scripts/` (§2)
- [ ] Each architecture layer maps to exactly one top-level dir under `src/` (§3)
- [ ] No directory mixes two layers (§3)
- [ ] Subdirectories group by domain concept, not by file type (§3, §11)
- [ ] Every source file has a mirrored test path under `tests/` (§4)
- [ ] No test file lives beside source (§4, §9)
- [ ] `.env` is gitignored; `.env.example` is committed with empty values (§5)
- [ ] Config schema lives in source; config files hold only values (§5)
- [ ] Zero secrets in any committed file (§5)
- [ ] Every build/output directory is gitignored (§6)
- [ ] No source file references a path inside a build/output dir (§6)
- [ ] One file-naming case convention, applied to every source file (§7)
- [ ] No file named `utils` · `helpers` · `misc` · `common` · `shared` (§7, §11)
- [ ] No abbreviations in file names outside the allowed set (§7)
- [ ] All directory names lowercase and singular, except the fixed plural conventions (§8)
- [ ] Nesting under `src/` ≤ 3 levels (§8)
- [ ] No generic container directory at any level (§8, §11)
- [ ] Generated files never mixed with authored files (§9)
- [ ] Monorepo: apps never import from other apps; shared code sits in `packages/` (§10)
- [ ] Multi-repo: no cross-repo path references, no submodules for shared code (§10)
- [ ] No anti-pattern from §11 present in the change
