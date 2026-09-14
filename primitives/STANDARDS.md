# Primitives Standards

> Rules for building systems from small reusable units — what qualifies as a primitive, how parts compose into components, and how a unit earns reuse.

**ID** `primitives` · **Tier** Foundation · **Version** 1.0
**Owns** unit taxonomy · primitive qualification · part/component/composite model · promotion path · reuse contract · primitive registry · duplication budget · primitive versioning + deprecation · project tool conventions
**Defers to** layer model · dependency direction · module boundaries → [architecture](../architecture/STANDARDS.md) · SOLID · coupling · cohesion · abstraction rules · pattern selection → [design](../design/STANDARDS.md) · function size · identifier naming · complexity thresholds → [code_writing](../code_writing/STANDARDS.md) · file placement · directory naming → [directory](../directory/STANDARDS.md) · error taxonomy · result types → [error_handling](../error_handling/STANDARDS.md) · coverage thresholds · test doubles → [testing](../testing/STANDARDS.md) · package versioning · lock files → [dependencies](../dependencies/STANDARDS.md) · public wire contracts → [api](../api/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [design](../design/STANDARDS.md) · [directory](../directory/STANDARDS.md)

---

## Table of Contents

1. [Unit Model](#1-unit-model)
2. [Qualification Rules](#2-qualification-rules)
3. [Promotion Path](#3-promotion-path)
4. [Reuse Contract](#4-reuse-contract)
5. [Composition Rules](#5-composition-rules)
6. [Primitive Registry](#6-primitive-registry)
7. [Duplication Budget](#7-duplication-budget)
8. [Versioning and Deprecation](#8-versioning-and-deprecation)
9. [Testing Primitives](#9-testing-primitives)
10. [Agent Construction Rules](#10-agent-construction-rules)
11. [Project Tools](#11-project-tools)
12. [Anti-Patterns](#12-anti-patterns)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Unit Model

Four unit kinds. Each kind is defined by what it depends on, ✗ by size.

| Kind | Depends on | Reuse scope | Owns state |
|---|---|---|---|
| Primitive | Language + stdlib only | Every project | ✗ |
| Part | Primitives only | Every component in the project | ✗ |
| Component | Parts + primitives | One domain | Scoped, declared |
| Composite | Components | One application | Application state |

Dependency direction is one-way: `Composite → Component → Part → Primitive`. A unit never depends on a kind above it.

| Rule | Detail |
|---|---|
| Direction | Downward only. Primitive importing a Part → build failure |
| Sibling calls | Part → Part allowed ; cycles forbidden |
| Skipping | Composite → Primitive allowed. Skipping levels is ✓, inverting is ✗ |
| Kind declared | Every unit declares its kind in its module header |

A unit's kind never changes silently. Changing kind = promotion (§3) | demotion, both recorded.

---

## 2. Qualification Rules

A unit is a **primitive** only when every row holds. One failure → it is a Part | Component.

| Test | Requirement |
|---|---|
| Dependency | Language + standard library only. Zero third-party imports |
| State | Stateless, or state fully owned by caller and passed in |
| Determinism | Same input → same output. No clock, no randomness, no I/O ; injected explicitly |
| Domain neutrality | Names contain zero domain nouns. `retry_with_backoff` ✓ · `retry_invoice_fetch` ✗ |
| Substitutability | Replaceable by any implementation honoring the signature |
| Failure surface | Errors returned, never raised across the boundary as side effects |
| Size | Fits one reviewer's working memory — one screen of logic |

A **part** relaxes exactly one row: it depends on primitives. Every other row still holds.

A **component** owns declared state and domain vocabulary. Determinism relaxes; I/O allowed at declared boundaries.

Kind is determined by the strictest row a unit fails, ✗ by author preference.

---

## 3. Promotion Path

Code earns reuse. It is never born reusable.

Lifecycle: Local code → extracted Part → promoted Primitive.

| Stage | Trigger | Required before advancing |
|---|---|---|
| Local | First implementation, inside one component | — |
| Part | Second call site needs identical logic | Extract · name without domain nouns · own tests |
| Primitive | Third call site, in a second component | Strip third-party deps · full qualification (§2) · registry entry (§6) |

Rules:

- Two call sites justify a Part. Three across two components justify a Primitive. ✗ promote on speculation.
- Promotion is a dedicated change. ✗ promote and change behavior in one commit.
- Promotion adds tests, never only moves them. The promoted unit is tested standalone.
- Demotion is legal: a primitive with one remaining call site moves back into that caller.
- A unit that cannot be promoted without a third-party dependency stays a Part permanently. This is a valid terminal state.

Cross-project promotion (Primitive → shared library) requires two consuming projects, ✗ one.

---

## 4. Reuse Contract

Every reusable unit publishes a contract. The contract is the unit's only public surface.

| Element | Requirement |
|---|---|
| Signature | Explicit types on every input and output. ✗ untyped containers as public parameters |
| Preconditions | Stated as validation the unit performs, ✗ as documentation the caller must read |
| Postconditions | Stated as the return type. Partial success → explicit variant, ✗ null |
| Failure modes | Enumerated and exhaustive. Caller can match every case |
| Side effects | Declared. A unit with undeclared side effects is defective, ✗ merely undocumented |
| Configuration | Passed as arguments. ✗ read environment, global state, or files inside a primitive |
| Concurrency | Thread-safety stated explicitly. Silence means unsafe |

Contract stability:

- Contract changes are breaking changes, regardless of call-site count.
- Adding an optional parameter with a default is non-breaking. Reordering, renaming, retyping is breaking.
- A caller never reaches past the contract into internals. Internals are private by default.

---

## 5. Composition Rules

Build order is fixed: search for an existing unit → compose existing units → write new code last.

| Step | Action | Failure to follow |
|---|---|---|
| 1 | Search registry (§6) for a unit answering the need | Duplicate primitive enters the tree |
| 2 | Compose two | more existing units | Logic reimplemented at a higher level |
| 3 | Write new local code | Premature abstraction |

Composition constraints:

| Rule | Detail |
|---|---|
| Depth | Composition chain ≤ 4 levels deep. Deeper → a missing intermediate Part |
| Fan-in | A unit called by > 12 call sites is a dependency hub — freeze its contract, version it (§8) |
| Fan-out | A Part importing > 7 primitives is doing two jobs — split it |
| Glue | Code that only adapts one unit to another belongs in the caller, ✗ in a new primitive |
| Wrapping | ✗ wrap a primitive solely to rename it. Rename the primitive | call it directly |
| Partial use | Calling a unit and using < half its output → the unit is over-scoped, split it |

Composition never mutates a lower unit to serve one caller. A caller needing different behavior passes different arguments | uses a different unit.

---

## 6. Primitive Registry

Every project maintains one machine-readable index of its reusable units. Unregistered units are invisible and will be duplicated.

| Field | Content |
|---|---|
| `id` | Stable slug. Never reused after deletion |
| `kind` | primitive · part · component |
| `path` | Source location |
| `signature` | Full public contract (§4) |
| `deps` | Units this one depends on, by id |
| `call_sites` | Count, refreshed by tooling ✗ by hand |
| `version` | Semver of the contract (§8) |
| `status` | active · frozen · deprecated |
| `owner` | Team | person accountable for the contract |

Registry rules:

- Generated by tooling from source, ✗ hand-maintained. A hand-maintained registry drifts within one sprint.
- Registry generation runs in CI. A unit in source but absent from the registry fails the build.
- Search before write is a required step (§5) and is enforced by review, ✗ by trust.
- Registry is the input to duplication detection (§7).

Cross-project: a shared primitive library publishes the same registry shape so consuming projects resolve by `id`, ✗ by path.

---

## 7. Duplication Budget

Duplication is measured, budgeted, and paid down. It is never assumed to be zero.

| Metric | Threshold |
|---|---|
| Identical logic blocks across units | 0 above 20 lines |
| Near-identical blocks (≥ 85% similarity) | ≤ 3 per 10k LOC · each carries a tracked promotion task |
| Primitives with overlapping purpose | 0. Two units answering one question → merge | delete one |
| Unregistered reusable-looking units | 0 |

Rules:

- Detection runs in CI against the registry (§6), ✗ as a manual review step.
- A near-duplicate discovered twice becomes a promotion task (§3), not a third copy.
- Copying a unit across project boundaries is allowed once. The second copy triggers shared-library promotion.
- Deliberate duplication is legal when the two copies are expected to diverge — record the decision, ✗ leave it implicit.

---

## 8. Versioning and Deprecation

A unit's version tracks its contract (§4), ✗ its implementation.

| Change | Version effect |
|---|---|
| Implementation rewrite, contract identical | No bump |
| Optional parameter added with default | Minor |
| New failure variant added | Minor ; callers match exhaustively → Major |
| Signature change · rename · retype · reorder | Major |
| Behavior change under an unchanged signature | Major — the worst kind, and the easiest to ship by accident |

Deprecation sequence, in order:

1. Mark `deprecated` in the registry with the replacement `id`.
2. Emit a deprecation signal at every call site the toolchain can reach.
3. Migrate call sites. Migration is the deprecator's work, ✗ the callers'.
4. Delete when `call_sites` reaches 0.

✗ delete a unit while any call site remains. ✗ leave a unit deprecated across more than two release cycles.

Frozen units: a hub (§5, fan-in > 12) is marked `frozen`. Frozen contracts change by addition only.

---

## 9. Testing Primitives

Reusable units carry a higher test bar than call-site code, because a defect multiplies by call-site count. Thresholds and doubles → [testing](../testing/STANDARDS.md).

| Kind | Additional requirement beyond project baseline |
|---|---|
| Primitive | Tested standalone with zero project fixtures · every failure variant exercised · property tests where input space is enumerable |
| Part | Tested standalone with primitives real, ✗ mocked |
| Component | Tested at its declared boundary · state transitions covered |

Rules:

- A primitive's tests import nothing from the project. A test needing project context proves the unit is a Part.
- Promotion (§3) without added standalone tests is rejected in review.
- A bug found in a primitive gets a regression test in the primitive, ✗ only at the call site where it surfaced.
- Contract tests belong to the unit, ✗ to consumers. Consumers test their own composition.

---

## 10. Agent Construction Rules

Rules for coding agents building under this model. Agents duplicate more than humans because they cannot see the whole tree.

| Rule | Detail |
|---|---|
| Registry first | Query the registry (§6) before writing any function. Skipping this is the primary source of agent duplication |
| Declare kind | State the unit kind (§1) before writing the body |
| One kind per change | ✗ create a primitive, a part, and a component in one change — the dependency direction cannot be reviewed |
| Extraction is explicit | Promotion (§3) is its own commit with its own message |
| ✗ speculative primitives | An agent writing a "reusable helper" on first use violates §3 |
| Report call sites | Every new unit reports its intended call sites; zero call sites → ✗ merge |
| Long runs | Re-query the registry after any context reset. Stale in-memory knowledge of the tree is the second source of duplication |

---

## 11. Project Tools

A project tool (`dev_tool`) is a unit whose consumer is the development process rather than the product. Same taxonomy (§1), same promotion path (§3), same contract (§4) — the only difference is who calls it.

| Rule | Detail |
|---|---|
| Location | Project-local and committed. ✗ a global install, ✗ an uncommitted script on one machine |
| Authorship | Written for this project's specifics. A tool needing no project knowledge is a dependency, ✗ a project tool |
| Contract | Declared like any unit (§4): typed inputs, enumerated failures, declared side effects |
| Registration | Appears in the registry (§6) with `kind: component` and its entry point |
| Invocation | One documented entry point per tool. ✗ a tool reachable only by reading its source |
| Destructiveness | A tool that mutates source | state declares it and defaults to dry-run |
| Testing | Tested at the level its kind demands (§9). An untested tool that rewrites code is a liability |
| Promotion | A tool wanted by a second project is promoted per §3, ✗ copied |
| Retirement | Removed when its task is gone. A stale tool that silently no-ops is worse than an absent one |

Project tools are held to the same duplication budget (§7) as product code: two tools answering one question is the same defect as two primitives answering one question.

---

## 12. Anti-Patterns

| Anti-pattern | Symptom | Correction |
|---|---|---|
| Speculative primitive | Unit with one call site, written "for reuse" | Inline it back. Promote on the third call site (§3) |
| Utils drawer | `utils` · `helpers` · `common` holding unrelated units | Split by question answered; name by behavior |
| Domain leak | Primitive named for a business noun | Rename to behavior | demote to Component |
| Config reader inside a primitive | Primitive reads env | file | Pass configuration as an argument (§4) |
| Inverted dependency | Primitive imports a Part | Move shared logic down, ✗ import up (§1) |
| Wrapper tax | Every primitive wrapped once per component | Delete wrappers; call directly (§5) |
| Frozen-by-fear | Contract never changes because call-site count is unknown | Generate the registry (§6); version deliberately (§8) |
| Silent behavior change | Signature stable, behavior different | Major bump + migration (§8) |
| Registry drift | Hand-edited registry | Generate from source in CI (§6) |
| Promotion with edits | Extraction commit also changes logic | Split into two commits (§3) |
| Over-scoped unit | Callers use a fraction of the output | Split by consumer need (§5) |
| Copy across projects | Third copy of the same logic in a third repo | Shared-library promotion (§3) |

---

## 13. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Promotion trigger | 3rd call site | 3rd call site, 2 components | 2nd call site, 2 components |
| Registry | Optional, generated on demand | Generated in CI, build fails on drift | Generated in CI · published for cross-project resolution |
| Duplication budget | ≤ 10 near-duplicates per 10k LOC | ≤ 3 per 10k LOC | 0 near-duplicates · identical blocks blocked at merge |
| Primitive test bar | Standalone tests | Standalone + every failure variant | Standalone + failure variants + property tests |
| Contract versioning | Informal | Semver on every reusable unit | Semver + frozen hubs + deprecation SLA ≤ 2 cycles |
| Fan-in freeze threshold | — | > 12 call sites | > 8 call sites |
| Deprecation window | Delete freely | ≤ 2 release cycles | ≤ 2 release cycles · migration owned by deprecator |
| Cross-project sharing | Copy allowed | 2nd copy → shared library | Shared library only · copying blocked in review |

---

## 14. Checklist

- [ ] Every unit declares its kind — primitive · part · component · composite
- [ ] Dependency direction is downward only; no unit imports a kind above it
- [ ] Every primitive passes all seven qualification rows (§2)
- [ ] No primitive imports a third-party dependency
- [ ] No primitive reads environment, global state, or files
- [ ] No primitive name contains a domain noun
- [ ] No unit was promoted before its third call site across two components
- [ ] Promotion commits contain no behavior change
- [ ] Every reusable unit publishes an explicit typed contract with enumerated failure modes
- [ ] Thread-safety is stated explicitly on every reusable unit
- [ ] Registry is generated from source in CI, never hand-edited
- [ ] Every reusable unit appears in the registry with owner and version
- [ ] Search-before-write was performed and is evidenced in review
- [ ] Composition depth ≤ 4 levels
- [ ] No Part imports more than 7 primitives
- [ ] Units with fan-in above the scale threshold are marked frozen
- [ ] Near-duplicate count is within the scale-matrix budget
- [ ] No two registered units answer the same question
- [ ] Contract changes carry the correct semver bump
- [ ] No behavior change shipped under an unchanged signature
- [ ] No unit deleted while call sites remain
- [ ] No unit deprecated longer than two release cycles
- [ ] Every primitive has standalone tests importing nothing from the project
- [ ] Every failure variant of every primitive is exercised by a test
- [ ] Primitive regression tests live with the primitive, not the call site
- [ ] Every project tool is committed, registered, and has one documented entry point
- [ ] Every destructive project tool defaults to dry-run
- [ ] No project tool was copied to a second project instead of being promoted
- [ ] Agent changes query the registry before writing new units
- [ ] No unit merged with zero declared call sites
