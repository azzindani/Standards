# Architecture Standards

> Structural rules for how a system is layered, how dependencies flow, and where state, concurrency, extension, and evolution live.

**ID** `architecture` · **Tier** Foundation · **Version** 1.0
**Owns** core structural principles · layer model · dependency direction · function placement · module boundaries · state architecture · concurrency architecture · extension · evolution
**Defers to** patterns · abstraction · module internals → [design](../design/STANDARDS.md) · function body style · identifier naming → [code_writing](../code_writing/STANDARDS.md) · layer-to-directory mapping · file naming → [directory](../directory/STANDARDS.md) · error types · boundaries · recovery · reporting → [error_handling](../error_handling/STANDARDS.md) · cascade · environments · secrets · flags → [configuration](../configuration/STANDARDS.md) · versioning · lock files · wrapper policy → [dependencies](../dependencies/STANDARDS.md) · budgets · caching · profiling → [performance](../performance/STANDARDS.md) · logging · metrics · traces → [observability](../observability/STANDARDS.md) · validation boundary · access control → [security](../security/STANDARDS.md)
**Load with** [design](../design/STANDARDS.md) · [directory](../directory/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md)

---

## Table of Contents

1. [Core Principles](#1-core-principles)
2. [Layer Model](#2-layer-model)
3. [Dependency Rules](#3-dependency-rules)
4. [Function Placement](#4-function-placement)
5. [Module Boundaries](#5-module-boundaries)
6. [State Architecture](#6-state-architecture)
7. [Concurrency Architecture](#7-concurrency-architecture)
8. [Cross-Cutting Placement](#8-cross-cutting-placement)
9. [Extension Architecture](#9-extension-architecture)
10. [Evolution Architecture](#10-evolution-architecture)
11. [Anti-Patterns](#11-anti-patterns)
12. [Scale Matrix](#12-scale-matrix)
13. [Checklist](#13-checklist)

---

## 1. Core Principles

Structural rules only. Every architectural decision traces to ≥ 1 principle. Violation → document rationale + which principles conflict.

| # | Principle | Origin | Buys |
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

---

## 2. Layer Model

Concentric gradient from pure core to I/O boundary. Two invariants; everything between = system-specific.

### Invariants

| Position | Contents | I/O |
|---|---|---|
| **Innermost** | Types · constants · enums · pure utilities | ✗ never |
| **Between** | As many layers as complexity demands · each progressively closer to I/O | ✗ never |
| **Outermost** | Adapters · CLI · API · MCP · file · network · DB | Yes — all I/O here |

### Reference Layers

Names are project-specific; the gradient is universal. Reference vocabulary used across these standards:

| Layer | Role | Examples |
|---|---|---|
| `kernel` (inner) | Domain types · shared constants · pure utilities | Type definitions · formatters · math |
| `engine` (mid-inner) | Domain transforms · validators · business rules | Price calculator · schema validator |
| `service` (mid-outer) | Use cases · workflow composition · coordination | Order pipeline · report generator |
| `interface` (outer) | I/O adapters · external integrations | HTTP handler · DB client · file reader |

Layer → directory mapping → [directory](../directory/STANDARDS.md).

### Rules

- Layer count = what complexity demands. ✗ arbitrary cap · ✗ fixed count · ✗ prescribed names.
- All I/O in outermost layer exclusively. Inner layers receive + return data only.
- Innermost layer holds only what every module needs. Fat core = fragile core.
- Every subsystem is itself a layer stack. Parent sees only the subsystem's outermost layer — internals invisible.
- Adjacent layers doing similar work → merge them.

---

## 3. Dependency Rules

### Direction

| Direction | Status |
|---|---|
| Outer → inner (inward) | Allowed |
| Same layer (lateral) | Allowed between declared peers only |
| Inner → outer (outward) | ✗ prohibited always |

### Acyclic Graph

Full dependency graph = DAG. A depends on B → B ✗ depends on A, directly or transitively. Any cycle = architecture violation, ✗ a style issue.

### Peer Protocol

Peers at same layer depend on a shared abstraction · ✗ on each other directly. Peer relationship declared in the module contract.

### Third-Party Isolation

| Rule | Detail |
|---|---|
| Inner layers ✗ call third-party directly | Thin adapter at outermost layer is the only call site |
| Wrap at risk boundaries | Unstable API · likely to swap · critical path |
| Stable foundations used directly | Language stdlib · mature utilities — wrapping adds indirection without value |

Version pinning · lock files · supply-chain policy → [dependencies](../dependencies/STANDARDS.md).

---

## 4. Function Placement

Where a function lives and what it is permitted to do. Body style · size · parameter count · identifier naming → [code_writing](../code_writing/STANDARDS.md).

### Classification

Every function is exactly one of two kinds:

| Kind | Layer | I/O | Contract |
|---|---|---|---|
| Logic | Inner | ✗ none | Pure transform: data in → data out · deterministic |
| Shell | Outermost | Yes | Reads/writes externals · calls logic functions |

I/O + transform in one function → split into shell + logic.

### Pipeline Contract

| Aspect | Rule |
|---|---|
| Input | Structured input when 4+ parameters |
| Return | Single output — one type, one value |
| Side effects | ✗ in inner layers · outermost layer only |
| Complex results | Structured types · ✗ raw collections |

### Command-Query Separation

Default: a function changes state OR returns data · ✗ both. State-changing functions return status/receipt only. Query functions produce no side effects.

**Exception:** atomic operations requiring both mutation and return for correctness (`pop` · `getOrCreate` · `compareAndSwap`). Document explicitly at the call contract.

### Explicit Absence

✗ null/nil/None for "no value". Use the language's explicit absence type (Option · Maybe · Optional · Result). Language lacking type-level enforcement → document the absence contract at the function boundary.

### Idempotency

Retriable operations are idempotent — second call = same result as first. Enables safe retry · crash recovery · replay.

Inherently non-idempotent operations (send notification · charge payment) require at-most-once delivery or an idempotency key. ✗ retry without one.

### Type-Driven Design

Define data types before writing functions. Types represent the domain; functions are transformations between types. Prefer plain data structures (structs · records · maps · tuples) over objects with hidden state — data is transparent · serializable · printable · comparable.

---

## 5. Module Boundaries

Structural contract only. Module cohesion · public-surface sizing · internal ordering · patterns → [design](../design/STANDARDS.md).

| Rule | Detail |
|---|---|
| Public API declared explicitly | Undeclared = internal · ✗ consumed externally |
| Public API only | Modules communicate through declared public functions |
| ✗ internal access | ✗ reach into another module's private functions or state |
| Data via arguments | Pass through function calls · ✗ shared variables |
| ✗ global mutables | ✗ module-level mutable state reachable from outside |
| Lifecycle explicit | Complex modules implement **init** (register capabilities · allocate resources) → **cleanup** (release · deregister) |

---

## 6. State Architecture

### Immutability Default

Inner-layer functions ✗ mutate input. Return new data. Caller's data is unchanged after the call.

### Ownership

Every resource (data · connection · handle) has exactly one owner at any point. Transfer is explicit — sender stops accessing after transfer. Shared read = wide; write = exclusive · ✗ concurrent writers.

Module owns its state exclusively. Two modules need the same data → pass it explicitly.

| Pattern | When |
|---|---|
| Pass as argument | Default |
| Return + re-pass | State transforms across a pipeline |
| Module-local cache | Performance optimization · one module only |
| Persistent store | Cross-session state · outermost layer only |

### Unidirectional Flow

Data flows one direction per pipeline — input → output through the layer stack. Data ✗ cycles back within the same pipeline. Feedback = new invocation · ✗ backward reference.

### Single Source of Truth

Every piece of data has one authoritative location. Derived data is computed · ✗ stored as a copy that drifts.

### Durability Techniques

| Technique | Scope | Mechanic | Origin |
|---|---|---|---|
| Copy-on-Write | Persistent or shared data mutation | Write new → atomically switch reference · crash-safe | ZFS |
| Write-Ahead Log | Durable state needing crash recovery | Log intent before executing · log = source of truth | Database WAL |
| Content-Addressable ID | Artifact storage · cache · dedup | Identify by content hash · ✗ by name or location | Git/IPFS |

Transaction semantics · isolation levels → [database](../database/STANDARDS.md). Cache invalidation policy → [performance](../performance/STANDARDS.md).

---

## 7. Concurrency Architecture

### Default

Sequential single-threaded. Add concurrency only when measured performance requires it.

### Model Selection

| Workload | Model |
|---|---|
| I/O-bound | Async / non-blocking |
| CPU-bound | Process-level parallelism |
| Mixed batch | Thread pool |
| Real-time stream | Async + queues |

### Split-Process-Combine

Large workloads → decompose into independent chunks → process each independently → combine at the coordination layer. Each chunk is self-contained: carries everything it needs, returns a complete partial result. Results accumulate at the coordination layer · ✗ inside workers.

### Backpressure

Downstream slower → upstream slows down · ✗ buffer unboundedly. Every queue/buffer has an explicit max size. Limit reached → producer blocks or drops with a signal · ✗ silent accumulation.

### Resource Budgets

Every concurrent operation declares: max time (timeout) · max memory · max queue depth · max worker pool size. Unbounded consumption = architectural violation, ✗ a tuning issue.

### Rules

- ✗ shared mutable state between workers — own copy or immutable reference.
- Every concurrent operation has an explicit timeout. No unbounded waits.
- Worker failure ✗ corrupts the accumulator — partial results are complete or absent, never half-written.

---

## 8. Cross-Cutting Placement

Cross-cutting concerns are owned by other standards. Architecture fixes only **where in the layer model they attach**.

| Concern | Structural rule | Owner |
|---|---|---|
| Errors | Inner layers return or raise · ✗ catch. Mid layers translate domain errors into results. Outermost layer catches environment errors and renders them. One catch boundary per layer transition | [error_handling](../error_handling/STANDARDS.md) |
| Configuration | Schema (shape) lives in innermost layer. Loading (I/O) lives in outermost layer. Values flow inward as function arguments · ✗ global reads from inner layers | [configuration](../configuration/STANDARDS.md) |
| Secrets | Enter at outermost layer · ✗ flow past it — pass derived values inward (authenticated clients · open connections) | [security](../security/STANDARDS.md) |
| Validation | Untrusted input validated at the outermost layer before it reaches any inner layer. Inner layers assume validated input | [security](../security/STANDARDS.md) |
| Logging · metrics · traces | Emitted at the outermost layer and at layer transitions · ✗ inside pure logic functions | [observability](../observability/STANDARDS.md) |
| Persistence | Outermost layer only. Inner layers ✗ know the storage engine exists | [database](../database/STANDARDS.md) |
| Caching | Attaches at a layer transition, never inside a pure function | [performance](../performance/STANDARDS.md) |

### Resilience Boundaries

Structural placement of failure isolation. Retry/backoff policy and error taxonomy → [error_handling](../error_handling/STANDARDS.md).

| Mechanism | Placement | Rule |
|---|---|---|
| Circuit breaker | Outermost layer, per external dependency | N consecutive failures → open → calls fail immediately · ✗ wait for timeout. Cooldown → one probe → success closes |
| Bulkhead | Per external dependency | Separate resource pool per dependency — one saturated dependency ✗ starves the others |
| Graceful degradation | Service layer | Component unavailable → reduce capability · ✗ crash entire system. Critical path continues · degraded state reported |
| Partial failure | Batch operations | ✗ stop on first error. Process everything possible · accumulate all failures · return complete success/failure report |

| Circuit breaker setting | Prototype | Production |
|---|---|---|
| Open after | 5 consecutive failures | 3–10 (configurable) |
| Cooldown before probe | 30s | 10–60s (configurable) |

---

## 9. Extension Architecture

### Registration

Extensible systems use a registry. Modules register capabilities at startup; the orchestrator resolves at runtime. New capability = new module that registers · zero changes to existing code.

### Feature Self-Containment

Adding feature X ✗ requires modifying module Y — unless Y is the registry or the entry point. Violation = coupling problem, fix the coupling.

### Composition Over Inheritance

Build capabilities as independent, attachable units; combine by composition. ✗ inheritance hierarchies — rigid coupling · combinatorial explosion. Composition mechanics → [design](../design/STANDARDS.md).

### Policy / Mechanism Separation

Engine provides mechanisms (how). Caller provides policy (what) via config or arguments. Engine ✗ decides business rules — it executes them.

### Reconciliation Loop

Scoped to stateful systems managing desired vs actual state. Continuously compare actual against desired → differ → apply corrective action automatically. Transient failures repair without intervention.

---

## 10. Evolution Architecture

### Versioned Interfaces

Public interface changes → old signature remains for a defined deprecation window. Old forwards to new. New consumers use the new interface.

| Scale | Deprecation window |
|---|---|
| Prototype | Next release |
| Production | 1–2 release cycles or 90 days |
| Scale | ≥ 2 release cycles or 180 days · consumer migration tracked |

Externally published API versioning → [api](../api/STANDARDS.md).

### Breaking Change Protocol

1. Document what breaks + why.
2. Provide a migration path (old → new).
3. Emit a deprecation warning for the full window before removal.
4. Remove only after the window closes and no consumer references remain.

### Strangler Fig

Replace incrementally · ✗ rewrite:

1. Build new alongside old.
2. Route new features → new module.
3. Migrate existing callers gradually.
4. Remove old when nothing references it.

### Open-Closed

Modules open for extension · closed for modification. Adding behavior ✗ requires changing existing working code.

---

## 11. Anti-Patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Leaky core | Innermost layer imports an HTTP client, DB driver, or filesystem API | Move the call to the outermost layer · pass data inward |
| Inverted dependency | Inner module imports an outer module to "just reach" a helper | Move the helper inward or invert with an abstraction |
| Cyclic modules | A → B → A, directly or transitively | Extract the shared concept into an inner-layer module |
| God layer | One layer holds most of the code | Split by domain concept — layers are horizontal, features vertical |
| Ambient state | Inner layer reads a global, singleton, or env var | Pass the value as an argument from the boundary |
| Hidden I/O | "Pure" function lazily opens a file or connection on first call | Reclassify as a shell function and move it out |
| Unbounded queue | Buffer with no max size between producer and consumer | Declare max depth · block or drop with signal |
| Retry without idempotency | Retry wrapper on a non-idempotent operation | Add idempotency key or at-most-once delivery |
| Big-bang rewrite | Replacing a subsystem in one merge | Strangler Fig (§10) |
| Speculative layer | Layer added "for future flexibility" with one implementation | Delete it — add when a second implementation exists |

---

## 12. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Layers (§2) | Flat — no layers | 2: core + boundary | Full recursive stack |
| Function contract (§4) | Informal | Typed in/out | Full contracts + CQS + idempotency |
| Module boundaries (§5) | Single file | Explicit exports | Registration pattern |
| State (§6) | Mutable ok | Immutable in core | CoW · WAL where durable |
| Concurrency (§7) | Sequential | Pool if measured need | Backpressure + explicit budgets |
| Resilience (§8) | Fail fast only | Timeouts + partial failure | Circuit breaker + bulkhead + degradation |
| Third-party (§3) | Direct use | Wrap critical deps | Wrap at every risk boundary |
| Extension (§9) | Not needed | Composition | Registration + reconciliation |
| Deprecation (§10) | Next release | 1–2 cycles / 90 days | ≥ 2 cycles / 180 days |

Scale transition → apply new rules incrementally via Strangler Fig (§10). ✗ rewrite — evolve.

---

## 13. Checklist

- [ ] Every architectural decision traces to ≥ 1 principle (§1)
- [ ] Innermost layer contains zero I/O calls (§2)
- [ ] All I/O confined to the outermost layer (§2)
- [ ] Layer count justified by complexity — no speculative layers (§2, §11)
- [ ] Dependency graph is a DAG — zero cycles (§3)
- [ ] Zero inner → outer imports (§3)
- [ ] Lateral dependencies go through a declared shared abstraction (§3)
- [ ] No inner layer calls a third-party library directly (§3)
- [ ] Every function classified logic or shell — none does both (§4)
- [ ] CQS holds; every atomic exception documented (§4)
- [ ] Absence represented by an explicit type, never null (§4)
- [ ] Every retriable operation is idempotent or carries an idempotency key (§4)
- [ ] Every module declares its public API explicitly (§5)
- [ ] No module-level mutable state reachable from outside (§5)
- [ ] Every resource has exactly one owner at any point (§6)
- [ ] Data flow is unidirectional per pipeline — no cycles (§6)
- [ ] Every stored value has one authoritative source; derived data computed (§6)
- [ ] Every concurrent operation has an explicit timeout (§7)
- [ ] Every queue/buffer has an explicit max depth (§7)
- [ ] No shared mutable state between workers (§7)
- [ ] Config schema in innermost layer; config loading at boundary (§8)
- [ ] Secrets stop at the boundary — only derived values flow inward (§8)
- [ ] Error catch boundaries placed per layer transition (§8)
- [ ] Batch operations accumulate failures instead of stopping at the first (§8)
- [ ] Adding a feature required no edit to an unrelated module (§9)
- [ ] Breaking changes shipped with migration path + deprecation window (§10)
- [ ] Subsystem replacement done incrementally, not as a rewrite (§10)
- [ ] No anti-pattern from §11 present in the change
