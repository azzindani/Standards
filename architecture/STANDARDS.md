# Architecture Standards

Core architectural principles · all projects · all languages.
Defines system structure — not code style, testing, or deployment (see respective standards).

Derived from: N-Tier Layered · OS Protection Rings · Clean Architecture · Unix Philosophy ·
Functional Core/Imperative Shell · Erlang/OTP · Actor Model · ECS · Microkernel ·
Linux Kernel · DDD · Contract-First · Rust Ownership · ACID · Copy-on-Write filesystems ·
TCP/IP · MapReduce · Circuit Breaker · Kubernetes reconciliation.

Composable with: design/ · testing/ · cicd/ · directory/ · code_writing/ · language-specific standards.

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Layer Model](#2-layer-model)
3. [Dependency Rules](#3-dependency-rules)
4. [Function Architecture](#4-function-architecture)
5. [Module Boundaries](#5-module-boundaries)
6. [State Architecture](#6-state-architecture)
7. [Error Architecture](#7-error-architecture)
8. [Configuration Architecture](#8-configuration-architecture)
9. [Concurrency Architecture](#9-concurrency-architecture)
10. [Extension Architecture](#10-extension-architecture)
11. [Evolution Architecture](#11-evolution-architecture)
12. [Scale Matrix](#12-scale-matrix)
13. [Architecture Checklist](#13-architecture-checklist)

---

## 1. Core Principles

Universal structural rules. Each traces to proven architecture.
Techniques (CoW · WAL · circuit breaker · backpressure) live in their respective sections —
principles here are structural, not implementational.

| # | Principle | Origin | Purpose |
|---|---|---|---|
| 1 | Single input → single output | Unix | Composability |
| 2 | Function does I/O or logic · ✗ both | Functional Core | Testability |
| 3 | Module owns its state exclusively | Actor Model | Isolation |
| 4 | Fail fast · supervisor recovers | Erlang/OTP | Reliability |
| 5 | Compose features · ✗ inherit | ECS | Flexibility |
| 6 | Core does minimum · services do rest | Microkernel | Stability |
| 7 | Dependencies point inward only | Clean/Onion | Maintainability |
| 8 | I/O lives at boundary edge only | Hexagonal | Swappability |
| 9 | Contract before implementation | Contract-First | Clarity |
| 10 | Domain owns its vocabulary | DDD | Scalability |
| 11 | Universal data format between stages | Unix | Interoperability |
| 12 | Features = self-contained slices | Vertical Slice | Modularity |
| 13 | Register capabilities · ✗ hardcode | Linux Kernel | Extensibility |
| 14 | One owner per resource at any time | Rust Ownership | Safety |
| 15 | Explicit absence · ✗ null | Rust/Haskell | Correctness |
| 16 | Retriable operations are idempotent | HTTP/REST | Retryability |
| 17 | Plain data structures over objects | Clojure | Transparency |
| 18 | Separate what-to-do from how-to-do | Linux Kernel | Adaptability |
| 19 | Command or query · not both (default) | CQS | Clarity |
| 20 | Unidirectional flow per pipeline | Flux/Elm | Predictability |
| 21 | Design types + schema first | Haskell/SQL | Type-driven |
| 22 | Explicit resource budgets | OS Resource Mgmt | Bounded resources |

Every decision traces to ≥1 principle. Violations documented with rationale +
which principles conflict.

---

## 2. Layer Model

Based on OS protection rings (Ring 0 = kernel → Ring N = userspace) and N-tier layered architecture.
Concentric model retained — fixed ring count removed. Two invariants; everything between = system-specific.

### Invariants

| Position | Rule | I/O |
|---|---|---|
| **Innermost** | Pure: types · constants · enums · pure utilities | ✗ never |
| **Outermost** | Boundary: adapters · CLI · API · MCP · file/network/DB | Yes — all I/O here |
| **Between** | As many layers as system needs · each progressively closer to I/O | No |

### Spectrum, Not Tiers

Layers form a **gradient** from pure-core to I/O-boundary. ✗ fixed count. ✗ prescribed names.
Systems define their own layers based on complexity. Reference points for common layers:

| Reference | Typical role | Examples |
|---|---|---|
| Inner | Domain types · shared constants · pure utilities | Type definitions · formatters · math |
| Mid-inner | Domain transforms · validators · business rules | Price calculator · schema validator |
| Mid-outer | Use cases · workflow composition · coordination | Order pipeline · report generator |
| Outer | I/O adapters · external integrations | HTTP handler · DB client · file reader |

Names are project-specific — the gradient rule is universal.

### Recursive Structure

Every subsystem is itself a layer stack. Parent sees only subsystem's outermost layer.

```
System
├── Subsystem A (2 layers):  types+logic | boundary
├── Subsystem B (4 layers):  domain types | rules | orchestration | API
└── Subsystem C (5 layers):  core | validation | logic | coordination | adapters
```

### Rules

- Layer count = what complexity demands. ✗ arbitrary cap.
- All I/O in outermost layer exclusively. Inner layers receive + return data only.
- Innermost layer = only what every module needs. Fat core = fragile core.
- Subsystem internals invisible to parent — outermost layer is sole interface.
- Adjacent layers do similar work → merge them.

---

## 3. Dependency Rules

### Direction

Outer layers depend on inner layers · ✗ reverse.

| Direction | Status |
|---|---|
| Outer → inner (inward) | Allowed |
| Same layer (lateral) | Allowed between declared peers only |
| Inner → outer (outward) | ✗ prohibited always |

### Peer Protocol

Peer modules at same layer: declare shared interface or contract. Both depend on
shared abstraction · ✗ on each other directly. Peer relationship documented in module declaration.

### Acyclic Graph

Full dependency graph = DAG. A depends on B → B ✗ depends on A — directly or transitively.

### Third-Party Isolation

Wrap externals at **risk boundaries**: unstable API · likely to swap · critical path.
Inner layers ✗ call third-party directly — thin adapter at outermost layer.
Stable foundational libraries (language stdlib · mature utilities) used directly.

### Version Discipline

Pin exact versions in lock files. Ranges in project metadata. Update deliberately · ✗ automatically.

---

## 4. Function Architecture

### Pipeline Contract

| Aspect | Rule |
|---|---|
| Arguments | Minimize positional args · structured input for 4+ parameters |
| Return | Single output — one type · one value |
| Side effects | None in inner layers · boundary layer only |
| Naming | Verb-first: `compute_x` · `validate_x` · `parse_x` |

### Classification

Every function = one of two types:

| Type | Layer | I/O | Purpose |
|---|---|---|---|
| Logic function | Inner | No | Pure transform: data in → data out |
| Shell function | Boundary | Yes | Reads/writes externals · calls logic functions |

I/O + transform in one function → split into shell + logic.

### Command-Query Separation

Default: function changes state OR returns data · ✗ both. State-changing functions
return status/receipt only. Query functions produce no side effects.

**Exception:** atomic operations (pop · getOrCreate · compareAndSwap) requiring
both mutation + return for correctness. Document explicitly.

### Explicit Absence

✗ null/nil/None for "no value." Use language's explicit absence type
(Option · Maybe · Optional · Result). Where language lacks type-level
enforcement — document absence contracts at function boundary.

### Idempotency

Retriable operations must be idempotent — second call = same result as first.
Enables safe retries · crash recovery · replay.

Inherently non-idempotent operations (send notification · charge payment):
require at-most-once delivery or idempotency key.

### Type-Driven Design

Define data types before writing functions. Types represent domain.
Functions = transformations between types.

### Data Over Objects

Prefer plain data structures (structs · records · maps · tuples) over objects
with hidden state. Data = transparent · serializable · printable · comparable.

### Return Contract

Complex results → structured types · ✗ raw collections. Simple operations → primitives.

---

## 5. Module Boundaries

### Public API

Every module declares public interface explicitly. Undeclared = internal · ✗ consumed externally.

### Isolation

| Rule | Description |
|---|---|
| Public API only | Modules communicate through declared public functions |
| ✗ internal access | ✗ reach into another module's private functions or state |
| Data via arguments | Pass through function calls · ✗ shared variables |
| ✗ global mutables | No module-level mutable state accessible externally |

### Module Lifecycle

Complex modules implement: **init** (register capabilities · allocate resources) →
**cleanup** (release resources · deregister).

---

## 6. State Architecture

### Immutability Default

Inner-layer functions ✗ mutate input. Return new data. Caller's data unchanged after call.

### Ownership

Every resource (data · connection · handle) has one owner at any point. Transfer
explicit — sender stops accessing after transfer. Shared read = wide; write = exclusive · ✗ concurrent.

Module owns its state exclusively. Two modules need same data → pass explicitly.

| Pattern | When |
|---|---|
| Pass as argument | Default |
| Return + re-pass | State transforms across pipeline |
| Module-local cache | Performance optimization · one module only |
| Persistent store | Cross-session state · boundary layer only |

### Unidirectional Flow

Data flows one direction per pipeline — input → output through layer stack.
Data ✗ cycles back within same pipeline. Feedback = new invocation · ✗ backward reference.

### Single Source of Truth

Every piece of data has one authoritative location. Derived data = computed · ✗ stored copy that drifts.

### Techniques (apply where scoped)

| Technique | Scope | Mechanic | Origin |
|---|---|---|---|
| **Copy-on-Write** | Persistent or shared data mutation | Write new → atomically switch reference · crash-safe | ZFS |
| **Write-Ahead Log** | Durable state needing crash recovery | Log intent before executing · log = source of truth | Database WAL |
| **Content-Addressable ID** | Artifact storage · cache · dedup | Identify by content hash · ✗ by name/location | Git/IPFS |

---

## 7. Error Architecture

### Classification

| Error type | Strategy |
|---|---|
| Programmer error | Fail fast · crash · fix code |
| Data error | Return in result · ✗ throw |
| Environment error | Raise · supervisor handles |
| Partial failure | Accumulate all · continue · report complete |

### Layer Boundaries

| Layer | Behavior |
|---|---|
| Inner layers | Returns or raises errors · ✗ catches |
| Mid layers | Catches domain errors → structured results |
| Outermost layer | Catches environment errors → user-facing messages |

### Error as Data

Domain logic returns errors in result structure · ✗ throwing exceptions.
Result carries data + errors; caller decides handling.

### Partial Failure

Batch operations ✗ stop on first error. Process everything possible ·
accumulate all failures · return complete success/failure report.

### Circuit Breaker

External dependency fails repeatedly → stop calling. N consecutive failures →
circuit opens → calls return failure immediately · ✗ wait/timeout.
Cooldown → one probe. Success → close circuit · resume.

| Scale | Open after | Cooldown |
|---|---|---|
| Small project | 5 failures | 30s |
| Production | 3–10 (configurable) | 10–60s (configurable) |

### Graceful Degradation

Component unavailable → system reduces capability · ✗ crashes entirely.
Non-critical features become unavailable. Critical path continues.
System reports degraded state.

---

## 8. Configuration Architecture

### Cascade (highest priority wins)

| Priority | Source |
|---|---|
| 1 (highest) | Runtime arguments |
| 2 | Environment variables |
| 3 | Configuration file |
| 4 (lowest) | Code defaults |

### Rules

- Config schema (shape) → innermost layer. Config loading (I/O) → outermost layer.
- Config values flow inward as function arguments · ✗ global reads from inner layers.
- Every value has sensible default. Zero-config runs default use case.
- Secrets ✗ in committed files. Enter via environment at boundary · ✗ flow past boundary —
  pass derived values (authenticated clients · connections).

---

## 9. Concurrency Architecture

### Default

Sequential single-threaded. Add concurrency when measured performance requires it.

### Model Selection

| Workload | Model |
|---|---|
| I/O-bound | Async / non-blocking |
| CPU-bound | Process-level parallelism |
| Mixed batch | Thread pool |
| Real-time stream | Async + queues |

### Split-Process-Combine

Large workloads → decompose into independent chunks · process each independently ·
combine at orchestration layer. Each chunk self-contained — carries everything needed ·
returns complete partial result.

### Backpressure

Downstream slower → upstream slows down · ✗ buffer unboundedly. Every queue/buffer
has explicit max size. Limit reached → producer blocks or drops with signal ·
✗ silent accumulation.

### Resource Budgets

Every concurrent operation has explicit limits: max time (timeout) · max memory ·
max queue depth · max worker pool size. Unbounded consumption = architectural violation.

### Rules

- ✗ shared mutable state between workers — own copy or immutable reference.
- Every concurrent operation has explicit timeout.
- Results collected into single accumulator at coordination layer · ✗ inside workers.

---

## 10. Extension Architecture

### Registration Pattern

Extensible systems use registry. Modules register capabilities at startup.
Orchestrator resolves at runtime. New capability = new module that registers ·
zero changes to existing code.

### Feature Self-Containment

Adding feature X ✗ requires modifying module Y (unless Y = registry or entry point).
Violation → coupling problem.

### Composition Over Inheritance

Build capabilities as independent · attachable units. Combine through composition.
✗ inheritance hierarchies — rigid coupling · combinatorial explosion.

### Policy / Mechanism Separation

Engine provides mechanisms (how). Caller provides policy (what) through config
or arguments. Engine ✗ decides business rules — executes them.

### Reconciliation Loop

**Scoped to:** stateful systems managing desired vs. actual state.
Continuously compare actual against desired. Differ → corrective action automatically.
Self-correcting — transient failures repaired without intervention.

---

## 11. Evolution Architecture

### Versioned Interfaces

Public API changes → old signature remains for defined deprecation window.
Old forwards to new. New consumers use new interface.

| Scale | Deprecation window |
|---|---|
| Small project | Next release |
| Production | 1–2 release cycles or 90 days |

### Breaking Change Protocol

1. Document what breaks + why.
2. Provide migration path (old → new).
3. Deprecation warning before removal.

### Strangler Fig

Replace incrementally · ✗ rewrite:
1. Build new alongside old.
2. Route new features → new module.
3. Migrate existing gradually.
4. Remove old when nothing references it.

### Open-Closed

Modules open for extension · closed for modification.
Add behavior ✗ requires changing existing working code.

---

## 12. Scale Matrix

Apply proportionally. Layer count = what system needs · ✗ fixed.

| Rule | PoC / Script | Small Project | Production System |
|---|---|---|---|
| Layers (§2) | Flat — no layers | 2 (core + boundary) | Full recursive stack |
| Function contract (§4) | Informal | Typed in/out | Full contracts + CQS |
| Module boundaries (§5) | Single file | Explicit exports | Registration pattern |
| State management (§6) | Mutable ok | Immutable in core | CoW + WAL where needed |
| Error handling (§7) | Fail fast only | Error as data | Accumulation + circuit breaker |
| Configuration (§8) | Hardcoded | File + defaults | Full cascade |
| Concurrency (§9) | Sequential | Pool if needed | Backpressure + budgets |
| Dependencies (§3) | Direct use | Wrap critical deps | Wrap at risk boundaries |
| Extension (§10) | Not needed | Composition | Registration + reconciliation |

### Scale Transition

Project graduates → apply new rules incrementally via Strangler Fig (§11). ✗ rewrite — evolve.

---

## 13. Architecture Checklist

### New Project

- [ ] Determine scale (PoC / Small / Production)
- [ ] Define layer structure appropriate to scale
- [ ] Identify innermost layer contents
- [ ] Define types + data structures before logic
- [ ] Establish data format for inter-module communication
- [ ] Define module boundaries + public APIs
- [ ] Confirm all I/O in boundary layer
- [ ] Confirm unidirectional flow per pipeline
- [ ] Set configuration defaults (zero-config works)
- [ ] Verify dependency graph = DAG · inward only
- [ ] Define resource budgets for production scale

### New Module

- [ ] Public API declared explicitly
- [ ] Every function classified: I/O or logic
- [ ] CQS applied (atomic exceptions documented)
- [ ] Pipeline contract: minimize args · single output
- [ ] ✗ outward layer imports
- [ ] Lateral deps → peer protocol declared
- [ ] Module owns state · ✗ shared mutables
- [ ] Absence represented explicitly
- [ ] Retriable operations are idempotent

### New Feature

- [ ] Self-contained · ✗ edits to unrelated modules
- [ ] Uses registration if system extensible
- [ ] ✗ I/O in inner layers
- [ ] Conforms to existing layer structure
- [ ] Degradation path defined for failure scenarios
