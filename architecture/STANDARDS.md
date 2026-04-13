# Architecture & Design Standards

Standards for system architecture and code design across all projects.
Derived from: Layered N-Tier, Clean Architecture, Unix Philosophy,
Functional Core/Imperative Shell, Actor Model, Erlang/OTP, ECS,
Microkernel, Linux Kernel, DDD, and Contract-First Design.

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Structure & Layering](#2-structure--layering)
3. [Function Contract](#3-function-contract)
4. [Module Boundaries](#4-module-boundaries)
5. [Data & State](#5-data--state)
6. [Error Philosophy](#6-error-philosophy)
7. [Configuration](#7-configuration)
8. [Concurrency](#8-concurrency)
9. [Dependencies](#9-dependencies)
10. [Testing](#10-testing)
11. [Observability](#11-observability)
12. [Security](#12-security)
13. [Evolution & Migration](#13-evolution--migration)
14. [Project Scale Matrix](#14-project-scale-matrix)
15. [Checklist](#15-checklist)

---

## 1. Core Principles

Thirteen rules. Each stolen from a proven architecture.

| # | Rule | Origin | Purpose |
|---|---|---|---|
| 1 | Single input, single output | Unix | Composability |
| 2 | Functions are I/O or logic, never both | Functional Core | Testability |
| 3 | Each module owns its state, no sharing | Actor Model | Isolation |
| 4 | Fail fast, recover at supervisor level | Erlang/OTP | Reliability |
| 5 | Compose features, don't inherit | ECS | Flexibility |
| 6 | Kernel does minimum, services do the rest | Microkernel | Stability |
| 7 | Dependencies point inward only | Clean/Onion | Maintainability |
| 8 | I/O lives at the outermost edge | Hexagonal | Swappability |
| 9 | Define the contract before the implementation | Contract-First | Clarity |
| 10 | Each domain owns its own vocabulary | DDD | Scalability |
| 11 | One universal data format between stages | Unix | Interoperability |
| 12 | Features are self-contained slices | Vertical Slice | Modularity |
| 13 | Register capabilities, don't hardcode imports | Linux Kernel | Extensibility |

Every architectural and design decision must trace back to at least one of
these principles. If a decision violates a principle, document why.

---

## 2. Structure & Layering

### Tier Model

All projects use inward-dependency layered tiers. Higher tiers import from
lower tiers. Lower tiers never import from higher tiers. Lateral imports
within the same tier are prohibited unless explicitly declared as peers.

```
Tier 0 (Kernel)   → primitives, types, constants, pure utilities
Tier 1 (Engine)   → core domain logic, transforms, validators
Tier 2 (Service)  → orchestration, use cases, workflow composition
Tier 3 (Interface)→ I/O adapters: CLI, MCP, API, file readers/writers
```

### Dependency Direction

```
Tier 3 → Tier 2 → Tier 1 → Tier 0    (allowed)
Tier 0 → Tier 1                        (violation)
Tier 1 → Tier 1                        (violation — lateral)
Tier 2 → Tier 3                        (violation — outward)
```

### I/O Placement

I/O operations (file read/write, network, database, stdin/stdout) live
exclusively in Tier 3. Tiers 0-2 are pure logic — they receive data and
return data. They never open files, never make network calls.

```python
# Violation: logic tier performs I/O
def analyze(path: str) -> dict:
    df = polars.read_csv(path)    # I/O inside logic
    return compute(df)

# Correct: I/O at Tier 3, logic at Tier 1
def analyze(df: DataFrame) -> dict:        # Tier 1 — pure logic
    return compute(df)

def handle_analyze(path: str) -> dict:     # Tier 3 — I/O adapter
    df = polars.read_csv(path)
    return analyze(df)
```

### Kernel Scope Rule

Tier 0 contains only what every module in the project needs. If only some
modules need it, it belongs in Tier 1 or higher. A fat kernel is a fragile
kernel. Typical Tier 0 contents:

- Type definitions and data classes
- Constants and enums
- Pure utility functions (string manipulation, math, formatting)
- Shared configuration schema (not the config values — the shape)

---

## 3. Function Contract

### Signature Rules

Every function follows the pipeline contract:

| Rule | Requirement |
|---|---|
| Custom arguments | Maximum 1 required positional argument |
| Other arguments | Must have defaults |
| Return type | Single output (one type, one value) |
| Side effects | None in Tiers 0-1. Permitted in Tier 3 only |
| Naming | Verb-first: `compute_stats`, `validate_schema`, `parse_rows` |

```python
# Correct — pipeline-compatible
def compute_stats(df: DataFrame, precision: int = 2) -> dict:
    return {"mean": round(df.mean(), precision)}

# Violation — multiple required args break pipeline composability
def compute_stats(df: DataFrame, column: str, precision: int) -> tuple:
    ...
```

### I/O vs Logic Split

Every function is classified as one of two types. Never both.

| Type | Tier | Does I/O | Testable with | Example |
|---|---|---|---|---|
| **Logic** | 0, 1, 2 | No | Plain unit test, no mocks | `transform(df) -> df` |
| **Shell** | 3 | Yes | Integration test | `load_csv(path) -> df` |

If a function reads a file AND transforms data, split it into two functions.

### Return Value Contract

Functions return structured data, never raw primitives for complex results.

```python
# Violation — caller must guess what dict contains
def analyze(df: DataFrame) -> dict: ...

# Correct — explicit contract
@dataclass
class AnalysisResult:
    summary: dict
    anomalies: list[dict]
    row_count: int

def analyze(df: DataFrame) -> AnalysisResult: ...
```

For simple operations, primitive returns are acceptable:
`def count_nulls(df: DataFrame) -> int`

---

## 4. Module Boundaries

### Export Control

Every module explicitly declares its public API. Everything not exported is
internal and must not be imported by other modules.

```python
# module/stats.py
__all__ = ["compute_stats", "detect_anomalies"]   # public contract

def compute_stats(df): ...          # public
def detect_anomalies(df): ...       # public
def _normalize_column(col): ...     # private — not in __all__
```

### Module Isolation

Modules do not access each other's internal state. Communication happens
through function calls using the public API only.

| Allowed | Violation |
|---|---|
| `from stats import compute_stats` | `from stats import _normalize_column` |
| `result = stats.compute_stats(df)` | `stats._internal_cache.clear()` |
| Passing data as arguments | Accessing module-level variables directly |

### Registration Pattern

For extensible systems, modules register their capabilities with a central
registry instead of being hardcoded as imports. Adding a capability requires
zero changes to existing code.

```python
# registry.py (Tier 0)
_handlers = {}
def register(name: str, func: callable): _handlers[name] = func
def resolve(name: str) -> callable: return _handlers[name]

# csv_handler.py (Tier 1) — self-registers on import
register("csv", read_csv)

# parquet_handler.py (Tier 1) — self-registers on import
register("parquet", read_parquet)

# orchestrator.py (Tier 2) — resolves at runtime
handler = resolve(detect_format(path))
result = handler(path)
```

### Module Lifecycle

Complex modules implement init/cleanup for resource management:

```python
def init() -> None:       # called when module loads
    register_capabilities()
    allocate_resources()

def cleanup() -> None:    # called when module unloads
    release_resources()
    deregister()
```

---

## 5. Data & State

### Immutability Default

Functions in Tiers 0-2 never mutate their input. Always return new data.

```python
# Violation — mutates input
def clean(df: DataFrame) -> DataFrame:
    df.drop_nulls(inplace=True)      # caller's data is changed
    return df

# Correct — returns new
def clean(df: DataFrame) -> DataFrame:
    return df.drop_nulls()           # original untouched
```

### State Ownership

Each module owns its state exclusively. No global mutable state shared
between modules. If two modules need the same data, pass it explicitly.

| Pattern | Use when |
|---|---|
| Pass as argument | Default — data flows through function calls |
| Return and re-pass | State transforms across pipeline stages |
| Module-local cache | Performance optimization within one module |
| Shared database/file | Persistent state across sessions (Tier 3 only) |

### Single Source of Truth

Every piece of data has exactly one authoritative location. If data is
derived, compute it — don't store a second copy that can drift.

### Snapshot Before Mutation

Any Tier 3 operation that modifies persistent data (files, databases) must
capture a snapshot or delta before the write. This enables undo, audit,
and crash recovery.

---

## 6. Error Philosophy

### Classification

| Error type | Strategy | Example |
|---|---|---|
| **Programmer error** | Fail fast, crash, fix the code | `assert len(columns) > 0` |
| **Data error** | Return error in result, don't throw | Missing column in CSV |
| **Environment error** | Throw, let supervisor handle | Disk full, permission denied |
| **Partial failure** | Accumulate errors, continue, report | 3 of 50 files failed to parse |

### Error Boundaries

Errors are caught and handled at tier boundaries, not inside core logic.

```
Tier 1 (logic)  → raises or returns error → does NOT catch
Tier 2 (service)→ catches domain errors   → translates to result
Tier 3 (I/O)    → catches env errors      → translates to user message
```

### Error as Data (preferred for domain logic)

```python
@dataclass
class Result:
    data: dict | None
    errors: list[str]
    ok: bool

def validate(df: DataFrame) -> Result:
    errors = []
    if "date" not in df.columns:
        errors.append("Missing column: date")
    return Result(data=df if not errors else None, errors=errors, ok=not errors)
```

### Partial Failure Accumulation

Batch operations never stop on the first error. Accumulate failures,
process everything possible, return a complete report.

```python
results, failures = [], []
for file in files:
    try:
        results.append(process(file))
    except ProcessError as e:
        failures.append({"file": file, "error": str(e)})
return {"processed": results, "failed": failures}
```

---

## 7. Configuration

### Cascade Order

Configuration resolves in this priority (highest wins):

```
Runtime argument  →  overrides everything
Environment var   →  overrides file + defaults
Config file       →  overrides defaults
Code defaults     →  baseline
```

### Rules

- Config schema lives in Tier 0 (the shape, not the values).
- Config loading lives in Tier 3 (file I/O).
- Config values flow inward as function arguments, never as global reads.
- Secrets (API keys, credentials) never appear in config files committed
  to version control. Use environment variables or `.env` files in `.gitignore`.
- Every config value has a sensible default. A project must run with zero
  configuration for its default use case.

---

## 8. Concurrency

### Default Model

Use single-threaded sequential execution by default. Add concurrency only
when measured performance requires it.

### Model Selection

| Workload | Model | Tool |
|---|---|---|
| I/O-bound (file, network) | Async | `asyncio`, `aiofiles` |
| CPU-bound (compute, transform) | Process pool | `concurrent.futures.ProcessPoolExecutor` |
| Mixed batch (many independent items) | Thread pool | `concurrent.futures.ThreadPoolExecutor` |
| Real-time streaming | Async with queues | `asyncio.Queue` |

### Rules

- Never share mutable state between concurrent workers. Each worker
  receives its own copy or an immutable reference.
- Worker pools have a maximum size tied to hardware tier (see project-
  specific resource constraints).
- Every concurrent operation has an explicit timeout.
- Results from concurrent workers are collected into a single accumulator
  at the orchestration level (Tier 2), never assembled inside workers.

---

## 9. Dependencies

### Wrapper Rule

Core logic (Tiers 0-1) never calls third-party libraries directly.
Wrap external libraries in a thin adapter at Tier 1 boundary so the
library can be swapped without touching core logic.

```python
# Violation — core logic coupled to specific library
def analyze(df):
    import pandas as pd          # library locked into logic
    return pd.DataFrame.describe(df)

# Correct — wrapped at boundary
# adapters/dataframe_ops.py (Tier 1 boundary)
def describe(df) -> dict:
    return polars_describe(df)   # swap library here only
```

Exception: standard library and language built-ins are used directly.

### Version Policy

- Pin exact versions in lock files (`uv.lock`, `package-lock.json`).
- Use ranges in project metadata (`pyproject.toml`, `package.json`).
- Update dependencies deliberately, not automatically.

### Direction Enforcement

No circular dependencies between modules. If module A imports from
module B, module B must never import from module A — directly or
transitionally. Visualize the dependency graph; it must be a DAG.

---

## 10. Testing

### Test Pyramid

```
         /  E2E  \           Few — full system, slow, Tier 3
        /----------\
       / Integration \       Some — module interactions, Tier 2
      /----------------\
     /    Unit Tests     \   Many — pure functions, fast, Tier 0-1
    /______________________\
```

### What to Test Where

| Tier | Test type | Mocking allowed | What to verify |
|---|---|---|---|
| 0 (Kernel) | Unit | None | Pure logic correctness |
| 1 (Engine) | Unit | None | Transform accuracy, edge cases |
| 2 (Service) | Integration | Tier 3 adapters only | Workflow orchestration |
| 3 (Interface) | E2E | External services only | I/O correctness, format validity |

### Contract Tests

Test the boundary between modules — verify that a module's public API
behaves as documented. Contract tests survive internal refactors.

```python
def test_compute_stats_contract():
    result = compute_stats(sample_df)
    assert "mean" in result           # contract: returns dict with "mean"
    assert isinstance(result["mean"], float)
```

### Rules

- Pure functions (Tier 0-1) require zero mocking. If a test needs mocks
  for a Tier 0-1 function, the function has I/O mixed in — fix the function.
- Every public function in `__all__` has at least one test.
- Tests are independent — no shared state, no execution order dependency.

---

## 11. Observability

### Structured Logging

Use structured key-value logging, not string interpolation.

```python
# Violation
logger.info(f"Processed {count} files in {elapsed}s")

# Correct
logger.info("batch_complete", count=count, elapsed=elapsed, status="ok")
```

### Operation Receipts

Every write operation returns a receipt: what changed, before/after
values, timestamp, and status. Receipts enable audit trails, undo
support, and debugging without reproducing the operation.

```python
@dataclass
class Receipt:
    operation: str
    target: str
    timestamp: str
    before: Any
    after: Any
    status: str   # "ok" | "error" | "skipped"
```

### Health & Metrics

Long-running systems expose:
- `health()` → is the system functional right now
- `metrics()` → counters, timing, resource usage since start

---

## 12. Security

### Validation Boundary

Validate all external input at Tier 3 — the system boundary. Once data
passes validation and enters Tier 2 and below, it is trusted.

```
External input → [Tier 3: validate, sanitize] → trusted data → Tier 2-0
```

Do not re-validate inside core logic. Defensive checks deep in the stack
indicate a broken validation boundary — fix the boundary.

### Least Privilege

Each module accesses only the resources it needs:
- File operations specify exact paths, never accept arbitrary user paths
  without validation.
- Path traversal: resolve and verify all paths against an allowed root
  before any file operation.
- Subprocess calls: never pass unsanitized input to shell commands.

### Secrets

- Never hardcode secrets in source code.
- Never commit `.env` files, credentials, or key files.
- Load secrets from environment variables at Tier 3 only.
- Secrets never flow inward past Tier 3 — pass derived values
  (authenticated clients, session tokens) instead.

---

## 13. Evolution & Migration

### Versioned Interfaces

When a module's public API changes, the old signature remains available
for one release cycle. New code uses the new interface. Old interface
forwards to new implementation internally.

### Breaking Change Protocol

1. Document what breaks and why in the changelog.
2. Provide a migration path (code example of old → new).
3. Deprecation warning for one release before removal.

### Strangler Fig Pattern

When replacing a system or module, don't rewrite all at once:
1. Build the new module alongside the old one.
2. Route new features to the new module.
3. Gradually migrate existing features.
4. Remove the old module when nothing references it.

### Feature Addition Rule

Adding a feature must not require modifying existing working code. If
adding feature X requires editing module Y (which is unrelated to X),
the architecture has a coupling problem. Fix the architecture.

---

## 14. Project Scale Matrix

Not every project needs every rule. Apply rules based on project scale.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Tier model (§2) | Flat — no tiers | 2 tiers (logic + I/O) | Full 4 tiers |
| Function contract (§3) | Informal | Single-in/single-out | Full typed contracts |
| Module boundaries (§4) | Single file | `__all__` exports | Registration pattern |
| Immutability (§5) | Optional | Required in core | Required everywhere |
| Error handling (§6) | Let it crash | Error as data in core | Full accumulation |
| Configuration (§7) | Hardcoded defaults | Config file + defaults | Full cascade |
| Concurrency (§8) | Sequential only | Thread pool if needed | Measured and tuned |
| Dependency wrappers (§9) | Direct import ok | Wrap critical deps | Wrap all external deps |
| Testing (§10) | Manual verification | Unit tests for core | Full pyramid |
| Observability (§11) | Print statements | Structured logging | Logging + receipts + metrics |
| Security (§12) | Basic path validation | Validation boundary | Full security model |
| Evolution (§13) | Not applicable | Changelog | Full migration protocol |

### Scale Transition

When a project graduates from one scale to the next, apply the new
rules incrementally — don't rewrite. Use the Strangler Fig pattern
(§13) to evolve the architecture in place.

---

## 15. Checklist

### New Project

- [ ] Determine project scale (PoC / Small / Production)
- [ ] Define tier structure appropriate to scale
- [ ] Identify Tier 0 kernel contents — types, constants, pure utilities
- [ ] Establish the universal data format for inter-function communication
- [ ] Define module boundaries and public APIs
- [ ] Place all I/O in Tier 3
- [ ] Set up configuration with sensible defaults
- [ ] Verify dependency graph is a DAG with inward-only direction

### New Module

- [ ] Declare `__all__` — only public API exported
- [ ] Classify every function as I/O or logic
- [ ] Verify single-input/single-output contract
- [ ] Add unit tests for every public function
- [ ] Confirm no lateral or outward imports

### New Feature

- [ ] Feature is self-contained — no edits to unrelated modules
- [ ] If extensible, uses registration pattern
- [ ] Tests cover the new public API contract
- [ ] No new I/O introduced below Tier 3
