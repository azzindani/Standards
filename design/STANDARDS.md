# Design Standards

> Rules for shaping modules, interfaces, abstractions, and patterns inside the structure architecture defines.

**ID** `design` · **Tier** Foundation · **Version** 1.0
**Owns** SOLID · coupling · cohesion · design pattern selection · interface contracts · composition · abstraction rules · module design · state machines · data flow patterns
**Defers to** layer model · dependency direction · CQS · idempotency · extension registry · interface versioning → [architecture](../architecture/STANDARDS.md) · function body style · parameter count · identifier naming → [code_writing](../code_writing/STANDARDS.md) · file + directory layout → [directory](../directory/STANDARDS.md) · error taxonomy · result types · retry policy → [error_handling](../error_handling/STANDARDS.md) · public API versioning · wire contracts → [api](../api/STANDARDS.md) · test doubles · seams → [testing](../testing/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Coupling and Cohesion](#2-coupling-and-cohesion)
3. [Pattern Selection](#3-pattern-selection)
4. [Interface Design](#4-interface-design)
5. [Composition](#5-composition)
6. [Abstraction Rules](#6-abstraction-rules)
7. [Module Design](#7-module-design)
8. [State Machines](#8-state-machines)
9. [Data Flow Patterns](#9-data-flow-patterns)
10. [Anti-Patterns](#10-anti-patterns)
11. [Scale Matrix](#11-scale-matrix)
12. [Checklist](#12-checklist)

---

## 1. Principles

SOLID, language-agnostic. Each = one enforceable rule.

| Principle | Rule |
|---|---|
| Single Responsibility | Every module has exactly one reason to change — one owner, one purpose, one axis of change |
| Open-Closed | Extend by adding code (new module · new handler · new variant) · ✗ by modifying working code |
| Liskov Substitution | Every implementation of an interface is usable wherever that interface is expected · ✗ special-case checks on concrete type |
| Interface Segregation | Consumers depend only on the methods they call — split fat interfaces (§4) |
| Dependency Inversion | High-level modules depend on abstractions; low-level modules implement them. Direction enforcement → [architecture](../architecture/STANDARDS.md) |

### SRP Violation Signals

| Signal | Diagnosis |
|---|---|
| Module imported by unrelated features | Responsibility too broad |
| Change in feature A forces change in module B | Shared responsibility |
| Module has multiple "sections" with different concerns | Responsibilities merged |
| Module name contains "and", "manager", or "utils" | Catch-all bucket → split |

### Open-Closed Strategies

| Strategy | Mechanism |
|---|---|
| Registry | New capability registers itself — dispatcher unchanged. See [architecture](../architecture/STANDARDS.md) §9 |
| Strategy injection | Caller supplies behavior as argument — engine unchanged |
| Plugin interface | New module implements a known interface — host discovers it |
| Event / hook | New handler subscribes to an existing event — emitter unchanged |

---

## 2. Coupling and Cohesion

### Coupling Spectrum

Acceptable at the top, prohibited at the bottom.

| Level | Type | Meaning | Verdict |
|---|---|---|---|
| 1 | Data | Modules share primitive data via arguments | Preferred |
| 2 | Stamp | Modules share structured data (records · structs) via arguments | Acceptable |
| 3 | Control | Caller passes a flag/enum that alters callee behavior | Minimize → separate functions |
| 4 | External | Modules share an external format, protocol, or interface | Acceptable at the outermost layer only |
| 5 | Common | Modules share global or module-level mutable state | ✗ prohibited |
| 6 | Content | Module reaches into another's internals | ✗ prohibited always |

### Coupling Thresholds

| Metric | Healthy | Warning | Violation |
|---|---|---|---|
| Direct imports per module | ≤ 5 | 6–10 | > 10 — module knows too much |
| Fan-out (outgoing deps) | ≤ 7 | 8–12 | > 12 — decompose |
| Fan-in (incoming dependents) | Any | Watch for change amplification | Change breaks > 3 dependents → stabilize the interface |
| Dependency chain depth | ≤ 4 hops | 5–6 | > 6 — flatten or add a facade |
| Circular dependencies | 0 | 0 | Any cycle = architecture violation |

### Cohesion Spectrum

Strongest at the top.

| Level | Type | Meaning | Target |
|---|---|---|---|
| 1 | Functional | Every element serves one well-defined task | Required for inner layers |
| 2 | Sequential | Output of one element feeds the next | Acceptable |
| 3 | Communicational | Elements operate on the same data | Acceptable in data transforms |
| 4 | Temporal | Elements run at the same time (init · cleanup) | Acceptable for lifecycle only |
| 5 | Logical | Elements do similar things, selected by a flag | Refactor into separate functions |
| 6 | Coincidental | Elements grouped arbitrarily ("utils" · "helpers") | ✗ prohibited — redistribute |

### Rules

- Every module targets functional or sequential cohesion.
- `utils` · `helpers` · `common` · `misc` modules = cohesion failure. Redistribute each function to its domain module.
- Two functions in a module that never change together and serve different callers → split the module.
- A function called by every module → candidate for the innermost layer.

---

## 3. Pattern Selection

✗ apply patterns preemptively. Each pattern solves one structural problem — use it only when that problem exists.

### Catalog

| Kind | Pattern | Use when | ✗ Use when | Layer |
|---|---|---|---|---|
| Creational | Factory function | Construction requires a decision (type selection · config-dependent assembly) | A plain constructor suffices | engine · service |
| Creational | Builder | Many optional parameters · multi-step construction | ≤ 3 parameters → direct construction | engine · service |
| Creational | Prototype / Clone | Producing variants of a complex pre-configured object | Object is cheap to construct from scratch | kernel · engine |
| Structural | Adapter | External library's interface ✗ match the internal contract | You control both sides — change the source | interface |
| Structural | Facade | Complex subsystem needs one entry point | Subsystem has ≤ 2 public functions | service |
| Structural | Decorator | Adding logging · caching · retry without modifying the original | Behavior is core to the function — put it inside | service · interface |
| Structural | Composite | Tree structures where leaf and branch share an interface | Structure is a flat list → iterate | engine |
| Behavioral | Strategy | Algorithm varies by context; caller selects at runtime | Only one algorithm exists — YAGNI | engine · service |
| Behavioral | Observer / Pub-Sub | Multiple independent consumers react to one event | One consumer → call it directly | service · interface |
| Behavioral | State machine | ≥ 3 states with constrained transitions (§8) | ≤ 2 states → boolean + branch | engine · service |
| Behavioral | Command | Operations must be queued, undone, logged, or replayed | Fire-and-forget with no undo | service |
| Behavioral | Iterator | Custom traversal without exposing internals | Built-in iteration suffices | kernel · engine |
| Behavioral | Chain of responsibility | First matching handler in an ordered chain processes the request | Exact handler known at call time | service |

### Selection Table

| Problem | First choice | Alternative |
|---|---|---|
| Which concrete type to create? | Factory function | Builder (multi-step) |
| External interface ✗ match mine | Adapter | Facade (simplifying a whole subsystem) |
| Add cross-cutting behavior | Decorator | Middleware chain (request/response pipelines) |
| Behavior varies by context | Strategy passed as argument | Registry lookup (open-ended set) |
| Multiple reactions to one event | Observer / Pub-Sub | Event bus (crossing module boundaries) |
| Object has lifecycle states | State machine (§8) | Enum + exhaustive match (simple transitions) |
| Complex construction, many options | Builder | Config struct (all options known upfront) |
| Need undo / replay | Command | Event sourcing (full history required) |

---

## 4. Interface Design

Interface = the contract between caller and callee: module public APIs, abstract interfaces, traits, protocols.

### Contract Rules

| Rule | Detail |
|---|---|
| Explicit over implicit | Every requirement, constraint, and side effect visible in the signature or type |
| Minimal surface | Expose the fewest operations callers need — helpers stay private |
| Stable contracts | The interface changes less often than the implementation. Stability requirement scales with dependent count |
| Consumer-driven | Shaped by what callers need · ✗ by what the implementation can offer |
| ✗ leaking internals | Parameter types, return types, and errors reveal nothing about the implementation mechanism |

### Segregation

| Rule | Detail |
|---|---|
| Split by consumer role | Consumer A uses methods 1–3, consumer B uses 4–5 → two interfaces |
| Max 5 methods per interface | Larger → split by cohesion. **Exception:** lifecycle interfaces (init · run · stop · cleanup) |
| ✗ marker interfaces with zero methods | Use type tags or enums |
| ✗ god interfaces consumed by all | Decompose into focused role interfaces |

### Shape

| Rule | Detail |
|---|---|
| Typed return | Structured type for complex results · ✗ raw collections |
| Consistent shape | All functions in a module family return compatible types |
| ✗ mixed return types | Function returns type A or type B depending on input → split into two functions |
| Fallible operations | Return a success-or-error union · ✗ null for failure. Taxonomy → [error_handling](../error_handling/STANDARDS.md) |
| Parameter ergonomics | Count limits · ✗ boolean parameters · ✗ stringly-typed parameters → [code_writing](../code_writing/STANDARDS.md) |

### Evolution

| Rule | Detail |
|---|---|
| Additive changes only | New optional fields/methods added without breaking callers |
| New fields carry defaults | Existing callers work unchanged |
| ✗ remove or rename without deprecation | Deprecation windows → [architecture](../architecture/STANDARDS.md) §10 |
| Breaking change → version the interface | `v2` coexists with `v1` through the migration window |

---

## 5. Composition

Default mechanism for reuse. ✗ inheritance.

### Composition vs Inheritance

| Criterion | Composition | Inheritance |
|---|---|---|
| Relationship | "has-a" · "uses-a" | "is-a", strictly taxonomic |
| Coupling | Loose — components swappable | Tight — child bound to parent internals |
| Flexibility | Any combination of behaviors | Single chain · combinatorial explosion |
| Testability | Each component tested in isolation | Must test through the hierarchy |
| Default | Yes | Only for true type hierarchies, ≤ 2 levels deep |

### Mechanisms

| Mechanism | How | Best for |
|---|---|---|
| Function composition | Output of f → input of g | Data transforms in inner layers |
| Delegation | Holder forwards calls to a collaborator | Behavior reuse without inheritance |
| Mixins / traits | Attach behavior bundles to a type | Cross-cutting capabilities (serializable · comparable) |
| Higher-order functions | Function takes a function | Strategy injection · callbacks · middleware |
| Config struct injection | Behavior-controlling config passed as data | Parameterized modules |

### Rules

| Rule | Detail |
|---|---|
| Max 2 inheritance levels | Deeper → refactor to composition |
| ✗ diamond inheritance | Use trait/interface composition even where the language permits it |
| Free functions over method hierarchies | Free functions compose across types; methods lock to one type |
| Each composed piece independently testable | Piece untestable alone → coupling too tight |
| Compose at construction time | Wire components in factory/init · ✗ runtime re-wiring unless the system is an explicit plugin host |

### Delegation

| Rule | Detail |
|---|---|
| Hold an interface reference · ✗ a concrete type | Enables swapping implementations |
| Delegator's public API differs from the delegate's | It adds, filters, or transforms · ✗ pass-through-only wrapper |
| One delegate per concern | ✗ a single delegate covering unrelated concerns |

### Middleware / Pipeline

| Rule | Detail |
|---|---|
| One concern per middleware | Logging · auth · validation · rate-limiting each stand alone |
| Order declared explicitly | In configuration or registration · ✗ implicit through import order |
| Uniform signature | Every stage takes input → returns output or passes to next |
| ✗ silent stage skipping | Short-circuit is explicit with a clear signal |

---

## 6. Abstraction Rules

Under-abstraction → duplication. Over-abstraction → indirection without value.

### Rule of Three

✗ abstract on the first occurrence. ✗ abstract on the second. Abstract on the third — the pattern is proven and the shape is known.

**Exception:** abstractions mandated by architecture (layer boundaries · I/O adapters) are created on first need.

### Decision Table

| Situation | Action |
|---|---|
| Identical logic duplicated 3+ times | Extract a shared function/module |
| Same logic duplicated twice | Leave it — duplication is cheaper than the wrong abstraction |
| Similar-but-not-identical logic across modules | ✗ force into one abstraction with flags — keep separate |
| External dependency used across modules | Wrap in an adapter (architecture mandate) |
| Complex subsystem with many internals | Expose a facade · keep internals private |
| Single-use helper | Inline unless it clarifies intent at the call site |

### When ✗ to Abstract

| Situation | Reason |
|---|---|
| One implementation and no planned variant | Indirection without value — use the concrete type |
| Wrapper exposes the same API as the library it wraps | Pass-through adds nothing — abstract only when the API must differ |
| "For testing" is the only reason | Use test doubles or injection → [testing](../testing/STANDARDS.md) |
| Abstraction name is vaguer than the concrete name | It obscures rather than clarifies |

### Leaky Abstraction

| Rule | Detail |
|---|---|
| Callers ✗ handle implementation-specific errors | Abstraction translates errors into its own vocabulary |
| Callers ✗ set implementation-specific settings | Abstraction maps generic config onto implementation detail |
| Swapping the implementation requires zero caller changes | Caller must change → the abstraction is leaky |
| Cost documented | Abstraction hiding O(n) behind an O(1)-looking API documents the cost |

### YAGNI

Every abstraction, config option, and extension point serves a current, demonstrated need. ✗ build for hypothetical requirements — removing speculative code later costs more than adding needed code when the need appears.

---

## 7. Module Design

Module = unit of import, compilation, or deployment (file · package · crate · namespace). Modules are the primary design unit; functions are implementation detail within them.

### Responsibility

| Rule | Detail |
|---|---|
| One domain concept per module | `user_auth` · `order_processing` · `price_calculation` · ✗ `user_stuff` |
| Name = noun (entity) or verb-phrase (action) | `payment_gateway` · `validate_input` · ✗ `utils` · ✗ `misc` · ✗ `common` |
| Change-frequency alignment | Elements that change together live together; elements that change independently live apart |
| Size 100–400 lines | < 50 → likely belongs inside another module. > 500 → split by sub-responsibility |

### Public Surface

| Rule | Detail |
|---|---|
| Explicit exports | Module declares what is public — everything else is internal by default |
| Max 7 public functions | Beyond 7 → the module has multiple responsibilities |
| ✗ internal types in public signatures | Parameter and return types are part of the public contract |
| Single import path | Public API reachable from the module root — ✗ deep imports into internal paths |

### Internal Structure

| Rule | Detail |
|---|---|
| Public functions first | Reader sees the contract before implementation detail |
| Private helpers near their caller | ✗ scattered across the file |
| One level of internal decomposition | Public functions + private helpers. ✗ nested sub-modules unless the module is a package |

### Cohesion Test

Ask: "If I delete this module, what breaks?"

| Answer | Diagnosis |
|---|---|
| One feature breaks | High cohesion — correct |
| Multiple unrelated features break | Multiple responsibilities → split |
| Nothing breaks | Dead code → delete the module |
| Everything breaks | It is an innermost-layer module — verify it belongs there |

---

## 8. State Machines

Use when an entity has ≥ 3 distinct states with constrained transitions.

### When to Use

| Situation | State machine? |
|---|---|
| 2 states (on/off · active/inactive) | ✗ No — boolean + branch |
| ≥ 3 states with defined transitions | Yes |
| Invalid transitions must be impossible by construction | Yes |
| Same input → different output depending on state | Yes |
| Temporal lifecycle (created → processing → completed → archived) | Yes |
| Status held as a string, compared ad-hoc across the codebase | Yes — refactor now |

### Rules

| Rule | Detail |
|---|---|
| States are an enum or union type | ✗ string literals · ✗ integer codes |
| All valid transitions enumerated | Transition table covering every state × event pair |
| Invalid transition = error | Raises or returns an error immediately · ✗ silent no-op |
| Each state carries its own data | `Processing{started_at, progress}` · `Completed{result, duration}` · ✗ nullable fields meaning "not applicable here" |
| Entry/exit actions declared with the transition | ✗ hidden in unrelated code |
| Current state always queryable | Reading the state ✗ triggers a transition |
| ✗ implicit states | `if running and has_error` is a hidden state — name it (`FailedWhileRunning`) |
| Terminal states marked | States with no outgoing transition are explicit |
| Persist state + transition history | Current state alone is insufficient for debugging |
| Machine lives in the engine layer | Transition function is pure: (state, event) → (state, actions). Actions execute at the outermost layer |

Every machine is defined by one transition table with columns: current state · event · next state · guard · action.

---

## 9. Data Flow Patterns

Selection depends on coupling, timing, and cardinality.

| Pattern | Topology | Timing | Coupling | Best for |
|---|---|---|---|---|
| Pipeline | Linear A → B → C | Sync | Low (data only) | Transforms · ETL · validation chains |
| Request-Response | Point-to-point A ↔ B | Sync | Medium (interface) | API calls · service invocation |
| Event / Pub-Sub | Fan-out A → {B, C, D} | Async | Low (event schema) | Notifications · audit · cross-module reactions |
| Command Queue | Buffered A → [queue] → B | Async | Low (command schema) | Task scheduling · work distribution · rate smoothing |
| Streaming | Continuous source →→ sink | Continuous | Medium (protocol) | Real-time data · log processing · live metrics |
| Callback / Hook | Inverted: B calls A's function | Sync | Medium (signature) | Plugin points · middleware · lifecycle hooks |

### Selection Criteria

| Criterion | Pipeline | Request-Response | Event / Pub-Sub | Command Queue |
|---|---|---|---|---|
| Producer knows consumer? | Yes (next stage) | Yes (target) | No | No |
| Consumer count | 1 per stage | 1 | 0–N | 1–N workers |
| Failure isolation | Stage-level | Caller handles | Subscriber-level | Worker-level |
| Backpressure | Natural (sync) | Natural (sync) | Explicit mechanism required | Queue depth limit |
| Ordering | Strict sequential | N/A | Per-producer | FIFO per queue |

### Per-Pattern Rules

| Pattern | Rule |
|---|---|
| Pipeline | Each stage: single input type → single output type. Pipeline contract → [architecture](../architecture/STANDARDS.md) §4 |
| Pipeline | Stages independently testable — feed test data in, assert output, no harness |
| Pipeline | Stage order declared in the orchestrator · ✗ implicit through import order |
| Pipeline | ✗ stage skipping on runtime flags — each stage handles its own "nothing to do" case and passes data through |
| Pipeline | Failure policy declared per pipeline: stop-on-first vs accumulate-all |
| Event | Events are immutable facts · ✗ modified after emission |
| Event | Event schema lives in the innermost layer — producers and consumers depend on the schema · ✗ on each other |
| Event | Subscriber failure ✗ affects the publisher — publisher emits and continues |
| Event | Ordering guaranteed per producer only; cross-producer ordering requires explicit sequencing |
| Event | Failed events route to a dead-letter queue · ✗ silently dropped |
| Request-Response | Response type agreed before implementation — contract-first |
| Request-Response | Timeout on every request · ✗ unbounded waits |
| Request-Response | Retry only on idempotent operations → [architecture](../architecture/STANDARDS.md) §4 |
| Request-Response | Error response shares the success structure — caller handles one response type |

---

## 10. Anti-Patterns

| Anti-pattern | Symptom | Fix |
|---|---|---|
| Speculative pattern | Pattern chosen "for future flexibility" with no current need | Remove it until the need exists |
| Single-variant abstraction | Factory creates exactly one type · Strategy has one implementation · Observer has one subscriber | Direct construction · inline the algorithm · direct call |
| Decorator tower | Decorator chain > 3 deep | Merge decorators or redesign |
| Pass-through wrapper | Wrapper exposes the delegate's API unchanged | Delete the wrapper |
| Utils bucket | Module named `utils` · `helpers` · `common` · `misc` | Redistribute each function to its domain module |
| God interface | One interface consumed by every module | Split by consumer role (§4) |
| Flag-driven behavior | Enum/boolean argument selecting unrelated code paths | Separate functions or Strategy |
| Stringly-typed state | Status tracked as a string with scattered comparisons | State machine (§8) |
| Nullable-field state | Struct with fields that are "only valid in some states" | Per-state data (§8) |
| Anemic abstraction | Interface whose name is vaguer than the concrete type it hides | Use the concrete type |
| Deep inheritance | Hierarchy > 2 levels | Refactor to composition (§5) |

---

## 11. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| SOLID (§1) | SRP at function level | SRP at module level · OCP for extension points | Full SOLID enforced at review |
| Coupling (§2) | Data coupling only | Fan-out measured · common coupling eliminated | Coupling metrics gate the build |
| Patterns (§3) | ✗ patterns — direct code | Factory · Strategy where the problem exists | Full vocabulary as problems arise |
| Interfaces (§4) | Implicit — function signatures | Explicit module exports | Typed interfaces · versioned contracts |
| Composition (§5) | Functions calling functions | Delegation · higher-order functions | Middleware chains · plugin systems |
| Abstraction (§6) | Inline everything | Rule of three | Facades for subsystems · documented costs |
| Module design (§7) | Single file | Modules by domain concept | ≤ 7 public functions enforced |
| State machines (§8) | Boolean flags | Enum-based state | Full transition table + history persisted |
| Data flow (§9) | Direct calls | Pipeline for transforms | Pipeline + Pub-Sub + Command Queue |

### Transition Triggers

| From → To | Trigger |
|---|---|
| Prototype → Production | Maintained > 1 month · > 1 contributor · or > 5 modules |
| Production → Scale | External users · real data · reliability guarantees · or > 20 modules |

---

## 12. Checklist

- [ ] Every module has one named responsibility (§1, §7)
- [ ] No module named `utils` · `helpers` · `common` · `misc` (§2, §7)
- [ ] Zero common coupling — no shared mutable module-level state (§2)
- [ ] Fan-out ≤ 7 direct dependencies per module (§2)
- [ ] Dependency chain depth ≤ 4 hops (§2)
- [ ] Zero circular dependencies (§2)
- [ ] Every pattern applied solves an existing problem, not a hypothetical one (§3)
- [ ] No Factory/Strategy/Observer with exactly one variant (§3, §10)
- [ ] Every interface has ≤ 5 methods, lifecycle interfaces excepted (§4)
- [ ] Interfaces shaped by consumer needs, not implementation capability (§4)
- [ ] No implementation detail leaks through return types or errors (§4, §6)
- [ ] Fallible operations return a success-or-error union, never null (§4)
- [ ] Interface changes are additive; new fields carry defaults (§4)
- [ ] Inheritance depth ≤ 2 levels (§5)
- [ ] Every composed piece is independently testable (§5)
- [ ] Delegation targets interfaces, not concrete types (§5)
- [ ] Middleware order declared explicitly (§5)
- [ ] Every abstraction justified by rule-of-three or architecture mandate (§6)
- [ ] No pass-through wrapper that adds nothing (§6, §10)
- [ ] Swapping any implementation requires zero caller changes (§6)
- [ ] Module public surface ≤ 7 functions, all exports explicit (§7)
- [ ] Deleting the module would break exactly one feature (§7)
- [ ] Entities with ≥ 3 states use a state machine with an enumerated transition table (§8)
- [ ] Invalid state transitions raise an error, never a silent no-op (§8)
- [ ] No state represented by a string or by nullable "sometimes valid" fields (§8, §10)
- [ ] Every pipeline declares its failure policy (§9)
- [ ] Events are immutable, schema-defined, and dead-lettered on failure (§9)
- [ ] Every request has an explicit timeout (§9)
- [ ] No anti-pattern from §10 present in the change
