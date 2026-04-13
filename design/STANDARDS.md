# Design Standards

Rules for software design decisions: pattern selection, coupling management,
interface contracts, composition, abstraction, module design, state machines,
and data flow. Language-agnostic — applies to all projects, all languages.

Built on: architecture/STANDARDS.md foundation (tier model, core principles,
function contracts). Complements code_writing/STANDARDS.md (implementation-level
rules) and testing/STANDARDS.md (verification strategy).

---

## Table of Contents

1. [SOLID Principles](#1-solid-principles)
2. [Coupling and Cohesion](#2-coupling-and-cohesion)
3. [Design Pattern Selection](#3-design-pattern-selection)
4. [Interface Design](#4-interface-design)
5. [Composition Patterns](#5-composition-patterns)
6. [Abstraction Levels](#6-abstraction-levels)
7. [Module Design](#7-module-design)
8. [State Machine Patterns](#8-state-machine-patterns)
9. [Data Flow Patterns](#9-data-flow-patterns)
10. [Scale Matrix](#10-scale-matrix)
11. [Design Checklist](#11-design-checklist)

---

## 1. SOLID Principles

Language-agnostic formulation. Each principle = one enforceable rule.

| Principle | Rule |
|---|---|
| Single Responsibility (SRP) | Every module/class/function has exactly one reason to change — one owner, one purpose, one axis of change |
| Open-Closed (OCP) | Extend behavior by adding new code (new module, new handler, new variant) — ✗ modifying existing working code |
| Liskov Substitution (LSP) | Every implementation of an interface is usable wherever that interface is expected — ✗ special-case checks on concrete type |
| Interface Segregation (ISP) | Consumers depend only on methods they call — split fat interfaces into focused ones; See §4 |
| Dependency Inversion (DIP) | High-level modules depend on abstractions, not concrete implementations — low-level modules implement those abstractions; See architecture/STANDARDS.md §3 |

### SRP Violation Signals

| Signal | Indicates |
|---|---|
| Module imported by unrelated features | Responsibility too broad |
| Change in feature A forces change in module B | Shared responsibility |
| Module has multiple "sections" with different concerns | Multiple responsibilities merged |
| Module name contains "and" or "manager" or "utils" | Catch-all bucket — split it |

### OCP Implementation Strategies

| Strategy | Mechanism |
|---|---|
| Registry pattern | New capability registers itself — zero changes to dispatcher; See architecture/STANDARDS.md §10 |
| Strategy/policy injection | Caller provides behavior as argument — engine unchanged |
| Plugin interface | New module implements known interface — host discovers automatically |
| Event/hook system | New handler subscribes to existing event — emitter unchanged |

---

## 2. Coupling and Cohesion

### Coupling Spectrum

From acceptable (top) to prohibited (bottom):

| Level | Type | Description | Verdict |
|---|---|---|---|
| 1 | Data coupling | Modules share only primitive data via function arguments | Preferred |
| 2 | Stamp coupling | Modules share structured data (records, structs) via arguments | Acceptable |
| 3 | Control coupling | Caller passes flag/enum that alters callee behavior | Minimize — prefer separate functions |
| 4 | External coupling | Modules share external format, protocol, or interface | Acceptable at Tier 3 boundaries |
| 5 | Common coupling | Modules share global/module-level mutable state | Prohibited; See architecture/STANDARDS.md §6 |
| 6 | Content coupling | Module reaches into another's internals | Prohibited — always |

### Coupling Measurement

| Metric | Healthy | Warning | Violation |
|---|---|---|---|
| Import count per module | ≤ 5 direct imports | 6–10 | > 10 — module knows too much |
| Fan-out (outgoing dependencies) | ≤ 7 | 8–12 | > 12 — decompose |
| Fan-in (incoming dependents) | Any | Watch for change amplification | If change breaks > 3 dependents → stabilize interface |
| Depth of dependency chain | ≤ 4 hops | 5–6 | > 6 — flatten or introduce facade |
| Circular dependencies | 0 | 0 | Any cycle = architecture violation; See architecture/STANDARDS.md §3 |

### Cohesion Spectrum

From strongest (top) to weakest (bottom):

| Level | Type | Description | Target |
|---|---|---|---|
| 1 | Functional | Every element contributes to a single well-defined task | Required for Tier 0–1 |
| 2 | Sequential | Output of one element feeds input of next (pipeline) | Acceptable |
| 3 | Communicational | Elements operate on same data | Acceptable in data transforms |
| 4 | Temporal | Elements execute at same time (init, cleanup) | Acceptable only for lifecycle |
| 5 | Logical | Elements do similar things selected by flag | Refactor into separate functions |
| 6 | Coincidental | Elements grouped arbitrarily ("utils", "helpers") | Prohibited — redistribute |

### Cohesion Rules

- Every module targets functional or sequential cohesion.
- `utils` / `helpers` / `common` modules = cohesion failure. Redistribute each function to its domain module.
- If two functions in a module never change together and serve different callers → split module.
- If a function is called by every module → candidate for Tier 0 kernel.

---

## 3. Design Pattern Selection

✗ apply patterns preemptively. Each pattern solves a specific structural problem — use only when that problem exists.

### Creational Patterns

| Pattern | Use When | ✗ Use When | Tier |
|---|---|---|---|
| Factory function | Construction requires decisions (type selection, config-dependent assembly) | Simple constructor suffices | 1–2 |
| Builder | Object requires many optional parameters; construction is multi-step | ≤ 3 parameters — use direct construction | 1–2 |
| Prototype / Clone | Creating variants of complex pre-configured objects | Object is simple to construct from scratch | 0–1 |

### Structural Patterns

| Pattern | Use When | ✗ Use When | Tier |
|---|---|---|---|
| Adapter | Integrating external library whose interface doesn't match internal contract | You control both sides — change the source | 3 |
| Facade | Simplifying complex subsystem into single entry point | Subsystem has ≤ 2 public functions | 2 |
| Decorator | Adding behavior (logging, caching, retry) without modifying original | Behavior is core to the function — put it inside | 2–3 |
| Composite | Tree structures where leaf and branch share same interface | Structure is flat list — use iteration | 1 |

### Behavioral Patterns

| Pattern | Use When | ✗ Use When | Tier |
|---|---|---|---|
| Strategy | Algorithm varies by context; caller selects behavior at runtime | Only one algorithm exists — YAGNI | 1–2 |
| Observer / Pub-Sub | Multiple independent consumers react to same event; decoupled notification | Only one consumer — call it directly | 2–3 |
| State machine | Object has distinct states with defined transitions; behavior changes per state; See §8 | ≤ 2 states — use boolean + if/else | 1–2 |
| Command | Operations must be queued, undone, logged, or replayed | Fire-and-forget with no undo | 2 |
| Iterator | Custom traversal over collection without exposing internals | Language's built-in iteration suffices | 0–1 |
| Chain of responsibility | Request processed by first matching handler in ordered chain | Exact handler known at compile/call time | 2 |

### Pattern Selection Decision Table

| Problem | First Choice | Alternative |
|---|---|---|
| "Which concrete type to create?" | Factory function | Builder (if multi-step) |
| "External interface doesn't match mine" | Adapter | Facade (if simplifying entire subsystem) |
| "Need to add cross-cutting behavior" | Decorator | Middleware chain (for request/response pipelines) |
| "Behavior varies by context" | Strategy (passed as argument) | Registry lookup (if open-ended) |
| "Multiple reactions to one event" | Observer / Pub-Sub | Event bus (if crossing module boundaries) |
| "Object has lifecycle states" | State machine (§8) | Enum + match/switch (if transitions are simple) |
| "Complex construction with many options" | Builder | Config struct (if all options known upfront) |
| "Need undo/replay" | Command | Event sourcing (if full history required) |

### Anti-Pattern Signals

| Signal | Problem | Fix |
|---|---|---|
| Pattern wraps single concrete type with no variants | Over-abstraction | Remove pattern, use concrete type directly |
| Factory creates exactly one type | Unnecessary indirection | Direct construction |
| Observer has exactly one subscriber | Over-engineering | Direct function call |
| Strategy has exactly one implementation | Premature generalization | Inline the algorithm |
| Decorator chain > 3 deep | Complexity exceeds benefit | Merge decorators or redesign |
| Pattern chosen "for future flexibility" with no current need | YAGNI violation | Remove until needed |

---

## 4. Interface Design

An interface = the contract between caller and callee. Applies to module public APIs, abstract interfaces, trait/protocol definitions, and function signatures.

### Contract Rules

| Rule | Description |
|---|---|
| Explicit over implicit | Every requirement, constraint, and side effect visible in signature or type |
| Minimal surface | Expose fewest functions/methods needed — internal helpers stay private |
| Stable contracts | Interface changes less frequently than implementation; stability = number of dependents |
| Consumer-driven | Interface shaped by what callers need, not what implementation can offer |
| No leaking internals | Return types, parameter types, and errors reveal nothing about implementation mechanism |

### Interface Segregation

| Rule | Rationale |
|---|---|
| Split by consumer role | If consumer A uses methods 1–3, consumer B uses methods 4–5 → two interfaces |
| Maximum 5 methods per interface | Larger → split by cohesion; exception: lifecycle interfaces (init/run/stop/cleanup) |
| ✗ marker interfaces with zero methods | Use type tags or enums instead |
| ✗ "god interfaces" consumed by all | Decompose into focused role interfaces |

### Dependency Inversion Application

| Layer | Depends On | Implemented By |
|---|---|---|
| Tier 2 (Service) | Abstract interface defined in Tier 1 | Tier 3 adapter |
| Tier 1 (Engine) | Types/contracts from Tier 0 | Tier 1 concrete logic |
| Tier 3 (Interface) | Nothing above it depends on Tier 3 | Implements abstractions defined lower |

Flow: High-level code defines what it needs (interface in Tier 1–2). Low-level code (Tier 3) provides concrete implementation. Dependency points inward; implementation detail stays outer. See architecture/STANDARDS.md §3.

### Parameter Design

| Rule | Details |
|---|---|
| Positional arguments: max 1 | See architecture/STANDARDS.md §4 |
| Configuration: use config struct | Group related options into typed struct — ✗ boolean flag explosion |
| Optional parameters: sensible defaults | Caller omits what they don't care about |
| ✗ boolean parameters | Replace with enum or named options — `mode=STRICT` not `strict=true` |
| ✗ stringly-typed parameters | Use enums, types, constants — ✗ raw strings for known-set values |

### Return Type Design

| Rule | Details |
|---|---|
| Typed return | Structured type for complex results; See architecture/STANDARDS.md §4 |
| Result type for fallible operations | Return success-or-error union — ✗ null returns for failure |
| Consistent shape | All functions in a module family return compatible types |
| ✗ mixed return types | Function returns type A or type B based on input → split into two functions |

### Evolution Rules

| Rule | Details |
|---|---|
| Additive changes only | New optional fields/methods added without breaking callers |
| ✗ removing or renaming without deprecation | One release cycle with deprecation warning; See architecture/STANDARDS.md §11 |
| Version interface if breaking | `v2` interface coexists with `v1` during migration |
| Default values for new fields | Existing callers work without changes |

---

## 5. Composition Patterns

Composition = building complex behavior from simple, independent pieces. Default mechanism for code reuse — ✗ inheritance. See architecture/STANDARDS.md §5 (Principle 5: compose features, don't inherit).

### Composition vs Inheritance Decision

| Criterion | Composition | Inheritance |
|---|---|---|
| Relationship | "has-a" or "uses-a" | "is-a" (strict taxonomic) |
| Coupling | Loose — components swappable | Tight — child coupled to parent internals |
| Flexibility | Mix any combination of behaviors | Single chain, combinatorial explosion for variants |
| Testability | Each component testable in isolation | Must test through hierarchy |
| Default choice | Yes | Only for true type hierarchies (≤ 2 levels) |

### Composition Mechanisms

| Mechanism | How It Works | Best For |
|---|---|---|
| Function composition | Output of f → input of g; pipeline chaining | Data transforms, Tier 0–1 |
| Delegation | Object holds reference to collaborator; forwards calls | Behavior reuse without inheritance |
| Mixins / Traits | Attach behavior bundles to types | Cross-cutting capabilities (serializable, comparable) |
| Higher-order functions | Function accepts function as argument | Strategy injection, callbacks, middleware |
| Config struct injection | Pass behavior-controlling config as data | Parameterized modules |

### Composition Rules

| Rule | Description |
|---|---|
| Max 2 levels of inheritance | Deeper hierarchies → refactor to composition |
| Prefer functions over method hierarchies | Free functions composable across types; methods locked to one type |
| ✗ diamond inheritance | If language allows, still avoid — use trait/interface composition instead |
| Each composed piece independently testable | If piece can't be tested alone → coupling too tight |
| Compose at construction time | Wire components together in factory/init — ✗ runtime dynamic re-wiring unless explicitly designed for plugin systems |

### Delegation Pattern

Use delegation when one module needs behavior from another without coupling to its type hierarchy:

| Rule | Description |
|---|---|
| Delegator holds interface reference, not concrete type | Enables swapping implementations |
| Delegator's public API differs from delegate's | Delegator adds, filters, or transforms — ✗ pass-through-only delegation (pointless wrapper) |
| One delegate per concern | ✗ single delegate handling multiple unrelated concerns |

### Middleware / Pipeline Composition

For request-response or data-transform pipelines:

| Rule | Description |
|---|---|
| Each middleware = one concern | Logging, auth, validation, rate-limiting — each separate |
| Middleware order explicit | Declared in configuration or registration, not implicit |
| Each middleware receives input, returns output (or passes to next) | Same function signature for all stages |
| ✗ middleware that skips stages silently | Short-circuit must be explicit with clear signal |

---

## 6. Abstraction Levels

Abstraction = hiding implementation detail behind a stable interface. Under-abstraction causes duplication. Over-abstraction causes indirection without value.

### Rule of Three

✗ abstract on first occurrence. ✗ abstract on second occurrence. Abstract on third occurrence — when the pattern is proven and the shape is clear. Before three occurrences, you don't know the real abstraction boundary.

Exception: abstractions mandated by architecture (tier boundaries, I/O adapters) are created on first need.

### Abstraction Decision Table

| Situation | Action |
|---|---|
| Same logic duplicated 3+ times with identical structure | Extract into shared function/module |
| Same logic duplicated 2 times | Leave duplicated — duplication cheaper than wrong abstraction |
| Similar-but-not-identical logic across modules | ✗ force into one abstraction with flags — keep separate |
| External dependency used in multiple modules | Wrap in adapter (architecture mandate); See architecture/STANDARDS.md §3 |
| Complex subsystem with many internal functions | Expose facade; keep internals private; See §3 (Facade) |
| Single-use helper function | Inline unless it clarifies intent at call site |

### Abstraction Level Consistency

Every function body operates at one abstraction level. ✗ mix high-level orchestration with low-level detail in same function.

| Signal | Problem | Fix |
|---|---|---|
| Function calls high-level `process_order()` and low-level `str.split(",")` in same body | Mixed abstraction levels | Extract low-level ops into named function |
| Function contains both business rule and data formatting | Tier mixing | Split into Tier 1 (rule) + Tier 2 (orchestration) or Tier 3 (formatting) |
| Comments explaining "what this block does" | Block is an unnamed abstraction | Extract to named function — name replaces comment |

### When NOT to Abstract

| Situation | Why |
|---|---|
| Abstraction has only one implementation and no planned variants | Indirection without value — use concrete type |
| Abstraction wraps library with identical API | Pass-through wrapper adds nothing — abstract only if API must differ |
| "For testing purposes" as sole reason | Use other test strategies (dependency injection, test doubles) |
| Abstraction name is vaguer than concrete name | Abstraction obscures rather than clarifies — keep concrete |

### Leaky Abstraction Rules

| Rule | Description |
|---|---|
| Callers never handle implementation-specific errors | Abstraction translates errors to its own vocabulary |
| Callers never configure implementation-specific settings | Abstraction maps generic config to implementation detail |
| Swapping implementation requires zero caller changes | If callers must change → abstraction is leaky |
| Performance characteristics documented | Abstractions that hide O(n) behind O(1)-looking API must document cost |

---

## 7. Module Design

Module = unit of deployment, compilation, or import (file, package, crate, namespace). Modules are the primary unit of design — functions are implementation detail within modules.

### Single Responsibility at Module Level

| Rule | Description |
|---|---|
| One domain concept per module | `user_auth`, `order_processing`, `price_calculation` — not `user_stuff` |
| Name = noun (domain entity) or verb-phrase (action) | `payment_gateway`, `validate_input` — ✗ `utils`, `misc`, `common` |
| Change frequency alignment | Elements that change together live together; elements that change independently live apart |
| Module size: 100–400 lines typical | < 50 → likely belongs inside another module; > 500 → split by sub-responsibility |

### Public API Surface

| Rule | Description |
|---|---|
| Explicit exports | Module declares what is public — everything else is internal by default |
| Minimal surface area | Expose only what external callers need; fewer public functions = more freedom to refactor internals |
| Public functions: max 7 per module | Beyond 7 → module likely has multiple responsibilities |
| ✗ exposing internal types in public signatures | Return types and parameter types are part of module's public contract |
| Re-export from index/root | Module's public API accessible from single import path |

### Internal Structure

| Rule | Description |
|---|---|
| Private helpers clustered near their caller | Reader finds helper near usage — ✗ scattered across file |
| Public functions at top of file | Caller sees API first, implementation detail later |
| One level of internal decomposition | Module has public functions + private helpers. ✗ nested sub-modules within a module unless module is a package |
| Constants at file top | After imports, before functions |

### Module Dependency Rules

| Rule | Description |
|---|---|
| Import only public API of other modules | ✗ deep imports reaching into internal paths |
| Depend on interface, not implementation | When crossing tier boundaries; See §4 (Dependency Inversion) |
| Acyclic dependency graph | If A imports B, B never imports A — directly or transitively; See architecture/STANDARDS.md §3 |
| Shared types live in Tier 0 | Types needed by multiple modules → extract to kernel; See architecture/STANDARDS.md §2 |

### Module Cohesion Test

Ask: "If I delete this module, what breaks?" Answer reveals the module's responsibility.

| Answer | Assessment |
|---|---|
| One feature/capability breaks | Good — high cohesion |
| Multiple unrelated features break | Bad — module has multiple responsibilities, split it |
| Nothing breaks | Dead code — remove the module |
| Everything breaks | Module is Tier 0 kernel — verify it belongs there |

---

## 8. State Machine Patterns

State machine = entity with defined states, transitions between states, and behavior that varies per state. Use when an entity has ≥ 3 distinct states with constrained transitions.

### When to Use

| Situation | Use State Machine? |
|---|---|
| Entity has 2 states (on/off, active/inactive) | No — boolean + if/else suffices |
| Entity has 3+ states with defined transitions | Yes |
| Invalid state transitions must be prevented at design level | Yes |
| Behavior differs per state (same input → different output) | Yes |
| Entity has temporal lifecycle (created → processing → completed → archived) | Yes |
| Status tracked as string with ad-hoc comparisons scattered across code | Refactor to state machine |

### State Machine Rules

| Rule | Description |
|---|---|
| States defined as enum/union type | ✗ string literals · ✗ integer codes — compiler-checked types only |
| All valid transitions defined explicitly | Transition table or match/switch covering every state × event combination |
| Invalid transitions = error, not silent no-op | Attempting illegal transition raises/returns error immediately |
| Each state carries its own data | State `Processing` holds `{started_at, progress}` — state `Completed` holds `{result, duration}` — ✗ nullable fields for "not applicable in this state" |
| Entry/exit actions explicit | Side effects on entering/leaving state declared alongside transition, not hidden in unrelated code |
| Current state always queryable | External code can ask "what state?" without triggering transition |

### Transition Table Format

Define all transitions as a table (conceptual or literal data structure):

| Current State | Event | Next State | Guard Condition | Action |
|---|---|---|---|---|
| Idle | Start | Running | Input valid | Initialize resources |
| Running | Complete | Succeeded | Result present | Store result |
| Running | Fail | Failed | Error present | Log error |
| Running | Cancel | Cancelled | — | Release resources |
| Failed | Retry | Running | Retry count < max | Reset, re-initialize |
| Succeeded | Archive | Archived | — | Move to cold storage |

### State Machine Design Rules

| Rule | Description |
|---|---|
| No implicit states | If code checks `if running and has_error` → that is a hidden state. Make it explicit (`FailedWhileRunning`) |
| Terminal states are explicit | States with no outgoing transitions clearly marked |
| Persistence: store state + transition history | Current state alone insufficient for debugging — keep log of transitions |
| State machine lives in Tier 1 | Pure logic — transition function takes (current_state, event) → (new_state, actions). I/O for actions executed in Tier 3 |

---

## 9. Data Flow Patterns

How data moves through the system. Selection depends on coupling requirements, timing, and cardinality. See architecture/STANDARDS.md §1 (Principle 25: unidirectional data flow).

### Pattern Selection Table

| Pattern | Topology | Timing | Coupling | Best For |
|---|---|---|---|---|
| Pipeline | Linear: A → B → C | Synchronous | Low (data only) | Data transforms, ETL, validation chains |
| Request-Response | Point-to-point: A ↔ B | Synchronous | Medium (interface) | API calls, function calls, service invocations |
| Event / Pub-Sub | Fan-out: A → {B, C, D} | Asynchronous | Low (event schema only) | Notifications, audit, cross-module reactions |
| Command Queue | Buffered: A → [queue] → B | Asynchronous | Low (command schema only) | Task scheduling, work distribution, rate smoothing |
| Streaming | Continuous: source →→→ sink | Continuous | Medium (protocol) | Real-time data, log processing, live metrics |
| Callback / Hook | Inverted: B calls A-provided function | Synchronous | Medium (function signature) | Plugin points, middleware, lifecycle hooks |

### Pipeline Pattern Rules

| Rule | Description |
|---|---|
| Each stage: single input type → single output type | See architecture/STANDARDS.md §4 (pipeline contract) |
| Stages are independently testable | Pass test data in, assert output — no pipeline harness needed |
| Stage order explicit | Declared in orchestrator (Tier 2), not implicit through import order |
| ✗ stage skipping based on runtime flags | Each stage handles its own "nothing to do" case and passes data through |
| Error in one stage → pipeline stops or accumulates | Decision explicit per pipeline; See architecture/STANDARDS.md §7 (partial failure) |

### Event / Pub-Sub Rules

| Rule | Description |
|---|---|
| Events are immutable facts | Published events ✗ modified after emission — they represent what happened |
| Event schema defined in Tier 0 | Shared vocabulary — producers and consumers depend on schema, not on each other |
| Subscriber failure ✗ affects publisher | Publisher emits and continues — subscriber errors isolated |
| Event ordering guaranteed within single producer | Cross-producer ordering requires explicit sequencing |
| Dead letter handling | Events that fail processing routed to dead letter queue/log — ✗ silently dropped |

### Request-Response Rules

| Rule | Description |
|---|---|
| Caller defines expected response type | Contract-first — response shape agreed before implementation; See architecture/STANDARDS.md §1 (Principle 9) |
| Timeout on every request | No unbounded waits — every call has explicit timeout; See architecture/STANDARDS.md §9 |
| Retry with idempotency | Safe retries require idempotent operations; See architecture/STANDARDS.md §4 |
| Error response same structure as success | Caller handles one response type — error info embedded, not thrown |

### Data Flow Selection Criteria

| Criterion | Pipeline | Request-Response | Event / Pub-Sub | Command Queue |
|---|---|---|---|---|
| Producer knows consumer? | Yes (next stage) | Yes (target) | No | No |
| Consumer count | 1 per stage | 1 | 0–N | 1–N workers |
| Failure isolation | Stage-level | Caller handles | Subscriber-level | Worker-level |
| Backpressure | Natural (sync) | Natural (sync) | Requires explicit mechanism | Queue depth limit |
| Ordering guarantee | Strict (sequential) | N/A | Per-producer | FIFO per queue |

---

## 10. Scale Matrix

Apply design rules proportionally to project scale. See architecture/STANDARDS.md §12 for architecture-level scale matrix.

| Design Area | PoC / Script | Small Project | Production System |
|---|---|---|---|
| SOLID (§1) | SRP at function level | SRP at module level · OCP for extensible parts | Full SOLID enforcement |
| Coupling (§2) | Data coupling sufficient | Measure fan-out · eliminate common coupling | Full coupling metrics · review gate |
| Patterns (§3) | ✗ patterns — direct code | Strategy · Factory where needed | Full pattern vocabulary as problems arise |
| Interfaces (§4) | Implicit (function signatures) | Explicit module exports | Typed interfaces · versioned contracts |
| Composition (§5) | Functions calling functions | Delegation · higher-order functions | Full composition · middleware chains · plugin systems |
| Abstraction (§6) | Inline everything | Rule of three | Tiered abstractions · facade for subsystems |
| Module design (§7) | Single file | Modules by domain concept | Full module boundaries · max 7 public functions |
| State machines (§8) | Boolean flags | Enum-based state | Full state machine with transition table |
| Data flow (§9) | Direct function calls | Pipeline for transforms | Pipeline + Pub-Sub + Command Queue as needed |

### Scale Transition Triggers

| From → To | Trigger |
|---|---|
| PoC → Small | Project maintained > 1 month · has > 1 contributor · or > 5 modules |
| Small → Production | Serves external users · handles real data · requires reliability guarantees · or > 20 modules |

---

## 11. Design Checklist

### New Module

- [ ] Module has single, named responsibility (§1 SRP, §7)
- [ ] Public API surface ≤ 7 functions (§7)
- [ ] All exports explicitly declared (§7)
- [ ] No circular dependencies (§2, architecture/STANDARDS.md §3)
- [ ] Fan-out ≤ 7 direct dependencies (§2)
- [ ] ✗ `utils` / `helpers` / `common` naming (§2 cohesion)
- [ ] Types shared across modules live in Tier 0 (§7, architecture/STANDARDS.md §2)

### New Interface / Contract

- [ ] Shaped by consumer needs, not implementation capabilities (§4)
- [ ] ≤ 5 methods per interface (§4)
- [ ] No implementation details leak through return types or errors (§4, §6)
- [ ] Boolean parameters replaced with enums (§4)
- [ ] Return types structured, not raw collections (§4, architecture/STANDARDS.md §4)
- [ ] Evolution plan: additive-only changes, deprecation path (§4)

### Pattern Application

- [ ] Pattern solves existing problem, not hypothetical one (§3)
- [ ] No pattern wrapping single concrete type (§3 anti-patterns)
- [ ] Strategy/Observer/Factory has ≥ 2 implementations (§3)
- [ ] Decorator chain ≤ 3 deep (§3)
- [ ] State machine used when ≥ 3 states with constrained transitions (§8)

### Composition

- [ ] Inheritance depth ≤ 2 levels (§5)
- [ ] Each composed piece independently testable (§5)
- [ ] Delegation targets interfaces, not concrete types (§5)
- [ ] Middleware order explicitly declared (§5)

### Abstraction

- [ ] Abstraction justified by rule-of-three or architecture mandate (§6)
- [ ] Abstraction level consistent within each function body (§6)
- [ ] Swapping implementation requires zero caller changes (§6)
- [ ] No pass-through wrappers that add nothing (§6)

### Data Flow

- [ ] Data flows one direction — no cycles (§9, architecture/STANDARDS.md §6)
- [ ] Pipeline stages independently testable (§9)
- [ ] Events are immutable facts with schema in Tier 0 (§9)
- [ ] Every async call has explicit timeout (§9, architecture/STANDARDS.md §9)
- [ ] Failure handling strategy explicit per flow (§9)
