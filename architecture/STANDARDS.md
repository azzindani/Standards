# Architecture Standards

Core architectural principles for all projects, all languages.
This standard defines how systems are structured — not how code is
written, tested, or deployed. Those belong in their respective standards.

Derived from: Layered N-Tier, Clean Architecture, Unix Philosophy,
Functional Core/Imperative Shell, Actor Model, Erlang/OTP, ECS,
Microkernel, Linux Kernel, DDD, and Contract-First Design.

Composable with: Design Standards, Testing Standards, CI/CD Standards,
Directory Standards, Code Writing Standards, and language-specific standards.

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Tier Model](#2-tier-model)
3. [Dependency Rules](#3-dependency-rules)
4. [Function Architecture](#4-function-architecture)
5. [Module Boundaries](#5-module-boundaries)
6. [State Architecture](#6-state-architecture)
7. [Error Architecture](#7-error-architecture)
8. [Configuration Architecture](#8-configuration-architecture)
9. [Concurrency Architecture](#9-concurrency-architecture)
10. [Extension Architecture](#10-extension-architecture)
11. [Evolution Architecture](#11-evolution-architecture)
12. [Project Scale Matrix](#12-project-scale-matrix)
13. [Architecture Checklist](#13-architecture-checklist)

---

## 1. Core Principles

Thirteen rules. Each derived from a proven architecture.

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

Every architectural decision must trace back to at least one principle.
If a decision violates a principle, document why.

---

## 2. Tier Model

All projects use inward-dependency layered tiers.

| Tier | Name | Contains | I/O Allowed |
|---|---|---|---|
| 0 | Kernel | Types, constants, enums, pure utilities | No |
| 1 | Engine | Domain logic, transforms, validators | No |
| 2 | Service | Orchestration, use cases, workflow composition | No |
| 3 | Interface | Adapters: CLI, API, MCP, file/network/database I/O | Yes |

### Kernel Scope Rule

Tier 0 contains only what every module in the project needs. If only
some modules need it, it belongs in Tier 1 or higher. A fat kernel is
a fragile kernel.

Tier 0 candidates: type definitions, data structures, constants, enums,
pure utility functions (math, string, formatting), configuration schema
(the shape, not the values).

### I/O Boundary Rule

All I/O operations live exclusively in Tier 3. Tiers 0–2 receive data
as arguments and return data as results. They never read files, open
connections, write to disk, or print to output.

If a function in Tier 0–2 needs data from an external source, Tier 3
reads it first and passes it in as an argument.

---

## 3. Dependency Rules

### Direction

Higher tiers depend on lower tiers. Never reverse.

| Direction | Status |
|---|---|
| Tier 3 → Tier 2 → Tier 1 → Tier 0 | Allowed |
| Any tier → same tier (lateral) | Prohibited unless declared as peers |
| Any tier → higher tier (outward) | Prohibited — always |

### Acyclic Graph

The full dependency graph across all modules must be a directed acyclic
graph (DAG). If module A depends on module B, module B must never depend
on module A — directly or transitively.

### Third-Party Isolation

External libraries and frameworks are wrapped at tier boundaries. Core
logic (Tier 0–1) never calls third-party code directly. A thin adapter
at the boundary allows the library to be swapped without touching core
logic. Exception: language standard library is used directly.

### Version Discipline

Pin exact versions in lock files. Use ranges in project metadata.
Update dependencies deliberately, not automatically.

---

## 4. Function Architecture

### Pipeline Contract

Every function follows the pipeline pattern for composability:

| Aspect | Rule |
|---|---|
| Required arguments | Maximum 1 positional argument |
| Optional arguments | Must have sensible defaults |
| Return | Single output — one type, one value |
| Side effects | None in Tiers 0–2. Permitted in Tier 3 only |
| Naming | Verb-first: `compute_x`, `validate_x`, `parse_x` |

### Classification

Every function is one of two types. Never both.

| Type | Tier | I/O | Purpose |
|---|---|---|---|
| Logic function | 0, 1, 2 | No | Pure transform: data in, data out |
| Shell function | 3 | Yes | Reads/writes external resources, calls logic functions |

If a function performs I/O AND transforms data, split it into two
functions — one shell, one logic.

### Return Contract

Complex results use structured types (structs, records, data classes),
not raw collections. The caller must know the shape of the return value
without reading the implementation. Simple operations may return
primitives.

---

## 5. Module Boundaries

### Public API

Every module explicitly declares its public interface. Everything not
declared is internal and must not be consumed by other modules.

### Isolation Rules

| Rule | Description |
|---|---|
| Public API only | Modules communicate exclusively through declared public functions |
| No internal access | Never reach into another module's private functions or state |
| Data via arguments | Pass data through function calls, not shared variables |
| No global mutables | No module-level mutable state accessible from outside |

### Module Lifecycle

Complex modules implement a standard lifecycle contract:
- **Init**: register capabilities, allocate resources
- **Cleanup**: release resources, deregister

---

## 6. State Architecture

### Immutability Default

Functions in Tiers 0–2 never mutate their input. Always return new data.
The caller's data remains unchanged after any function call.

### Ownership

Each module owns its state exclusively. No global mutable state shared
between modules. If two modules need the same data, pass it explicitly.

| Pattern | When to use |
|---|---|
| Pass as argument | Default — data flows through function calls |
| Return and re-pass | State transforms across pipeline stages |
| Module-local cache | Performance optimization within one module only |
| Persistent store | Cross-session state, Tier 3 only |

### Single Source of Truth

Every piece of data has exactly one authoritative location. If data
is derived, compute it — don't store a second copy that can drift.

### Snapshot Before Mutation

Any Tier 3 operation that modifies persistent state must capture a
snapshot or delta before the write. This enables undo, audit, and
crash recovery.

---

## 7. Error Architecture

### Classification

| Error type | Strategy |
|---|---|
| Programmer error | Fail fast, crash immediately, fix the code |
| Data error | Return error in result, don't throw |
| Environment error | Throw/raise, let supervisor level handle |
| Partial failure | Accumulate errors, continue processing, report all |

### Boundaries

Errors are caught and handled at tier boundaries, not inside core logic.

| Tier | Behavior |
|---|---|
| 0–1 (logic) | Returns or raises errors. Does NOT catch. |
| 2 (service) | Catches domain errors. Translates to structured results. |
| 3 (interface) | Catches environment errors. Translates to user-facing messages. |

### Error as Data

Domain logic prefers returning errors as part of the result structure
rather than throwing exceptions. The result carries both the data and
any errors, allowing the caller to decide how to handle them.

### Partial Failure

Batch operations never stop on the first error. Process everything
possible, accumulate all failures, return a complete report of
successes and failures together.

---

## 8. Configuration Architecture

### Cascade Order (highest priority wins)

| Priority | Source |
|---|---|
| 1 (highest) | Runtime arguments |
| 2 | Environment variables |
| 3 | Configuration file |
| 4 (lowest) | Code defaults |

### Rules

- Configuration schema (the shape) lives in Tier 0.
- Configuration loading (file I/O) lives in Tier 3.
- Configuration values flow inward as function arguments, never as
  global reads from within core logic.
- Every configuration value has a sensible default. A project must
  run with zero configuration for its default use case.
- Secrets never appear in committed files. They enter through
  environment variables at Tier 3 and never flow inward past Tier 3 —
  pass derived values (authenticated clients, connections) instead.

---

## 9. Concurrency Architecture

### Default

Sequential single-threaded execution. Add concurrency only when
measured performance requires it.

### Model Selection

| Workload type | Concurrency model |
|---|---|
| I/O-bound (file, network) | Async / non-blocking |
| CPU-bound (compute, transform) | Process-level parallelism |
| Mixed batch (many independent items) | Thread pool |
| Real-time streaming | Async with queues |

### Rules

- Never share mutable state between concurrent workers.
- Each worker receives its own copy or an immutable reference.
- Worker pool sizes are bounded by hardware constraints.
- Every concurrent operation has an explicit timeout.
- Results from workers are collected into a single accumulator at
  Tier 2 (orchestration level), never assembled inside workers.

---

## 10. Extension Architecture

### Registration Pattern

Extensible systems use a registry. Modules register their capabilities
at startup. The orchestrator resolves capabilities at runtime. Adding
a new capability means adding one new module that registers itself —
zero changes to existing code.

### Feature Self-Containment

Each feature is a self-contained unit. Adding feature X must not require
modifying module Y (unless Y is the registry or entry point). If it
does, the architecture has a coupling problem.

### Composition Over Inheritance

Build capabilities as independent, attachable units. Combine them
through composition. Avoid inheritance hierarchies — they create rigid
coupling and make feature combinations combinatorially explosive.

---

## 11. Evolution Architecture

### Versioned Interfaces

When a module's public API changes, the old signature remains available
for one release cycle. Old interface forwards to new implementation.
New consumers use the new interface.

### Breaking Change Protocol

1. Document what breaks and why.
2. Provide a migration path (old → new).
3. Deprecation warning for one cycle before removal.

### Strangler Fig Pattern

Replace systems incrementally, not all at once:
1. Build the new module alongside the old.
2. Route new features to the new module.
3. Gradually migrate existing features.
4. Remove the old module when nothing references it.

### Open-Closed Principle

Modules are open for extension, closed for modification. Adding
behavior should not require changing existing working code.

---

## 12. Project Scale Matrix

Apply rules proportionally to project complexity.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Tier model (§2) | Flat — no tiers | 2 tiers (logic + I/O) | Full 4 tiers |
| Function contract (§4) | Informal | Single-in/single-out | Full typed contracts |
| Module boundaries (§5) | Single file | Explicit exports | Registration pattern |
| Immutability (§6) | Optional | Required in core | Required everywhere |
| Error handling (§7) | Fail fast only | Error as data in core | Full accumulation |
| Configuration (§8) | Hardcoded defaults | File + defaults | Full cascade |
| Concurrency (§9) | Sequential only | Pool if needed | Measured and tuned |
| Dependencies (§3) | Direct use ok | Wrap critical deps | Wrap all externals |
| Extension (§10) | Not needed | Composition | Full registration |

### Scale Transition

When a project graduates from one scale to the next, apply the new
rules incrementally using the Strangler Fig pattern (§11). Never
rewrite — evolve in place.

---

## 13. Architecture Checklist

### New Project

- [ ] Determine project scale (PoC / Small / Production)
- [ ] Define tier structure appropriate to scale
- [ ] Identify Tier 0 kernel contents
- [ ] Establish universal data format for inter-function communication
- [ ] Define module boundaries and public APIs
- [ ] Confirm all I/O is in Tier 3
- [ ] Set configuration defaults
- [ ] Verify dependency graph is a DAG — inward only

### New Module

- [ ] Public API declared explicitly
- [ ] Every function classified as I/O or logic
- [ ] Pipeline contract: single input, single output
- [ ] No lateral or outward tier imports
- [ ] Module owns its state — no shared mutables

### New Feature

- [ ] Self-contained — no edits to unrelated modules
- [ ] Uses registration if system is extensible
- [ ] No I/O introduced below Tier 3
- [ ] Conforms to existing tier structure
