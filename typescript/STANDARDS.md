# TypeScript Standards

Rules for TypeScript projects: type system, modules, async, error handling,
build configuration, testing, and tooling. Language-specific companion to
general standards.

Composable with: `architecture/STANDARDS.md` (tier model, principles),
`code_writing/STANDARDS.md` (general quality), `api/STANDARDS.md` (type contracts),
`error_handling/STANDARDS.md` (error boundaries), `testing/STANDARDS.md` (test strategy).

---

## Table of Contents

1. [Type System](#1-type-system)
2. [Interface vs Type](#2-interface-vs-type)
3. [Module System](#3-module-system)
4. [Async Patterns](#4-async-patterns)
5. [Null Handling](#5-null-handling)
6. [Enum vs Union](#6-enum-vs-union)
7. [Function Types](#7-function-types)
8. [Error Handling](#8-error-handling)
9. [Build Configuration](#9-build-configuration)
10. [Project Structure](#10-project-structure)
11. [Testing](#11-testing)
12. [Linting & Formatting](#12-linting--formatting)
13. [Runtime Validation](#13-runtime-validation)
14. [Anti-Patterns](#14-anti-patterns)
15. [Checklist](#15-checklist)

---

## 1. Type System

Strict mode required in every project. Zero tolerance for `any`.

### 1.1 Strict Mode — Non-Negotiable Settings

```jsonc
// tsconfig.json — minimum required strict flags
{
  "compilerOptions": {
    "strict": true,                    // enables all below
    "noUncheckedIndexedAccess": true,  // arr[i] returns T | undefined
    "exactOptionalProperties": true,   // ✗ undefined assigned to optional
    "noPropertyAccessFromIndexSignature": true
  }
}
```

`strict: true` enables: `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`,
`strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`,
`alwaysStrict`, `useUnknownInCatchVariables`.

### 1.2 ✗ `any` — Use `unknown` Instead

| Scenario | ✗ Wrong | ✓ Correct |
|---|---|---|
| Unknown input | `any` | `unknown` + type guard |
| JSON parse result | `JSON.parse(s) as any` | `JSON.parse(s) as unknown` → validate |
| Third-party untyped | `(lib as any).method()` | Write declaration file or `@ts-expect-error` with ticket |
| Callback parameter | `(x: any) => ...` | `(x: unknown) => ...` + narrowing |

Allowed exception: `any` in `.d.ts` files wrapping untyped third-party libraries —
only when type is genuinely unknowable at compile time.

### 1.3 Discriminated Unions

Every union of object types must include a literal discriminant field.

```typescript
// ✓ Discriminated — exhaustive checking works
type Result =
  | { kind: "ok"; value: string }
  | { kind: "error"; error: Error };

function handle(r: Result) {
  switch (r.kind) {
    case "ok":    return r.value;
    case "error": throw r.error;
    // default: compile error if new variant added (with noFallthroughCasesInSwitch)
  }
}
```

Discriminant field name conventions: `kind`, `type`, or `status`. Pick one per project, use everywhere.

### 1.4 Type Narrowing

Prefer narrowing in this order:

| Priority | Technique | When |
|---|---|---|
| 1 | Discriminated union `switch` | Object variants with `kind` field |
| 2 | `in` operator | Duck-typing object shapes |
| 3 | Type predicate function | Reusable narrowing logic |
| 4 | `instanceof` | Class hierarchies only |
| 5 | `typeof` | Primitives only (`string`, `number`, `boolean`) |

Type predicates must validate at runtime — ✗ lie about types:

```typescript
// ✓ Predicate validates truthfully
function isUser(v: unknown): v is User {
  return typeof v === "object" && v !== null && "id" in v && "name" in v;
}
```

### 1.5 Branded / Opaque Types

Use branded types for domain identifiers to prevent accidental mixing.

```typescript
type UserId = string & { readonly __brand: unique symbol };
type OrderId = string & { readonly __brand: unique symbol };

function createUserId(id: string): UserId { return id as UserId; }

// Compile error: UserId ✗ assignable to OrderId
function getOrder(id: OrderId): Order { /* ... */ }
getOrder(createUserId("abc")); // ← type error
```

---

## 2. Interface vs Type

### 2.1 Decision Table

| Use Case | Keyword | Reason |
|---|---|---|
| Object shape (public API contract) | `interface` | Extensible, better error messages |
| Union type | `type` | Interfaces cannot represent unions |
| Intersection / mapped / conditional | `type` | Interfaces cannot compose these |
| Function signature (standalone) | `type` | Cleaner syntax |
| Class implementation contract | `interface` | `implements` only works with interfaces |
| Primitive alias / branded type | `type` | Interfaces cannot alias primitives |

### 2.2 Consistency Rule

One project, one convention for object shapes. If `interface` chosen for object shapes,
use `interface` for all object shapes — ✗ mix. `type` used only for unions, intersections,
mapped types, and aliases.

### 2.3 ✗ Interface Merging in Application Code

Declaration merging is for library augmentation only. ✗ rely on implicit merge
in application code — leads to scattered definitions.

```typescript
// ✗ Implicit merge — shape split across files
interface Config { port: number; }
interface Config { host: string; } // merges silently

// ✓ Single definition
interface Config { port: number; host: string; }
```

---

## 3. Module System

### 3.1 ESM Over CommonJS

| Rule | Detail |
|---|---|
| Module format | ESM (`import`/`export`). ✗ `require()` in application code |
| `package.json` | `"type": "module"` |
| tsconfig `module` | `"NodeNext"` or `"ESNext"` |
| File extensions in imports | Required for NodeNext: `import { x } from "./foo.js"` |
| CommonJS interop | Allowed only in Tier 3 adapters wrapping legacy dependencies |

### 3.2 Barrel Exports

```typescript
// src/models/index.ts — barrel file
export { User } from "./user.js";
export { Order } from "./order.js";
```

| Rule | Detail |
|---|---|
| One barrel per module boundary | `src/models/index.ts`, `src/services/index.ts` |
| ✗ Re-export everything | Export only public API — internal helpers stay unexported |
| ✗ Deep barrel nesting | `src/index.ts` re-exporting `src/models/index.ts` re-exporting `src/models/user/index.ts` = ✗ |
| Max depth | Two levels: `src/index.ts` → `src/module/index.ts` |

### 3.3 ✗ Circular Imports

Circular imports = architectural violation. See `architecture/STANDARDS.md` §3 (Dependency Rules — Acyclic Graph).

Detection: enable `import/no-cycle` ESLint rule with `maxDepth: 5`. Fix by extracting shared types to a lower tier.

### 3.4 Import Organization

Order (enforced by `eslint-plugin-import` or `@trivago/prettier-plugin-sort-imports`):

```typescript
// 1. Node built-ins
import { readFile } from "node:fs/promises";

// 2. External packages
import { z } from "zod";

// 3. Internal absolute (path aliases)
import { Config } from "@/config.js";

// 4. Internal relative
import { validate } from "./validate.js";

// 5. Type-only imports (always last within each group)
import type { User } from "@/models/user.js";
```

`type` keyword required on type-only imports — enables tree-shaking and prevents runtime import of type-only modules.

---

## 4. Async Patterns

### 4.1 `async`/`await` Over Raw Promises

| Rule | Detail |
|---|---|
| Default async style | `async`/`await` — ✗ raw `.then()` chains in application code |
| `.then()` allowed | Library internals optimizing microtask scheduling; callback adapter layers |
| `Promise.all` / `Promise.allSettled` | Use freely with `await` — parallel execution is idiomatic |
| `new Promise()` constructor | Allowed only to wrap callback-based APIs in Tier 3 adapters |

### 4.2 ✗ Fire-and-Forget

Every `Promise` must be `await`ed, returned, or explicitly voided with documentation.

```typescript
// ✗ Fire-and-forget — unhandled rejection risk
sendAnalytics(event);

// ✓ Awaited
await sendAnalytics(event);

// ✓ Explicit void with documented reason
void sendAnalytics(event).catch(logError); // background: analytics loss acceptable
```

ESLint rule: `@typescript-eslint/no-floating-promises: "error"`.

### 4.3 Error Handling in Async

```typescript
// ✓ try/catch at the async boundary — not inside pure logic
async function fetchUser(id: string): Promise<Result<User, FetchError>> {
  try {
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) return { kind: "error", error: new FetchError(res.status) };
    const data: unknown = await res.json();
    return { kind: "ok", value: parseUser(data) };
  } catch (e) {
    return { kind: "error", error: FetchError.fromUnknown(e) };
  }
}
```

Rules:
- `catch` clauses receive `unknown` (enforced by `useUnknownInCatchVariables`)
- Narrow caught errors before accessing properties
- Return typed `Result` rather than re-throwing — see §8

### 4.4 Concurrent Operations

| Operation | Use When |
|---|---|
| `Promise.all` | All must succeed — fail-fast on first rejection |
| `Promise.allSettled` | Need results from all regardless of failures |
| `Promise.race` | Timeout patterns, first-responder |
| `Promise.any` | First success from multiple sources |

✗ Unbounded parallelism. Limit concurrent operations with a semaphore or pool:

```typescript
async function mapConcurrent<T, R>(
  items: T[],
  fn: (item: T) => Promise<R>,
  concurrency: number
): Promise<R[]> {
  const results: R[] = [];
  const executing = new Set<Promise<void>>();
  for (const item of items) {
    const p = fn(item).then((r) => { results.push(r); });
    executing.add(p);
    p.finally(() => executing.delete(p));
    if (executing.size >= concurrency) await Promise.race(executing);
  }
  await Promise.all(executing);
  return results;
}
```

### 4.5 Async Initialization

✗ `async` constructors (not valid TypeScript). Use static factory methods:

```typescript
class Database {
  private constructor(private pool: Pool) {}

  static async create(config: DbConfig): Promise<Database> {
    const pool = await createPool(config);
    return new Database(pool);
  }
}
```

---

## 5. Null Handling

Ref: `architecture/STANDARDS.md` principle #15 — represent absence explicitly, never null.

### 5.1 `strictNullChecks` — Always On

Enabled by `strict: true`. ✗ disable independently. Every nullable value must be
explicitly typed as `T | null` or `T | undefined`.

Convention:
- `undefined` = value not provided / optional field absent
- `null` = value explicitly set to empty / known absence
- Pick one per project as the "absence" value — ✗ mix both carelessly

### 5.2 Optional Chaining and Nullish Coalescing

```typescript
// ✓ Optional chaining for deep access
const city = user?.address?.city;

// ✓ Nullish coalescing for defaults (respects 0, "", false)
const port = config.port ?? 3000;

// ✗ Logical OR for defaults — falsy trap
const port = config.port || 3000; // breaks when port = 0
```

### 5.3 ✗ Non-Null Assertion Abuse

`!` operator (`x!`) suppresses null checks. Allowed only in:

| Context | Allowed |
|---|---|
| Test files (`.test.ts`, `.spec.ts`) | Yes — test data known to be populated |
| After `Map.has()` check on same line | Yes — guard is immediate |
| Everywhere else | ✗ — use narrowing, `??`, or `if` check |

```typescript
// ✗ Non-null assertion without guard
const name = map.get(key)!;

// ✓ Guard + assertion on same path
if (map.has(key)) {
  const name = map.get(key)!; // safe: has() just confirmed
}

// ✓ Better: avoid entirely
const name = map.get(key) ?? throwMissing(key);
```

### 5.4 Optional Parameters vs Overloads

Prefer optional parameters for simple cases. Use overloads when return type varies
by presence of argument.

```typescript
// ✓ Optional parameter — same return type
function find(id: string, includeDeleted?: boolean): Promise<User | null>;

// ✓ Overload — return type depends on argument
function get(id: string): Promise<User | null>;
function get(id: string, required: true): Promise<User>;
function get(id: string, required?: boolean): Promise<User | null> {
  const user = await findById(id);
  if (required && !user) throw new NotFoundError(id);
  return user;
}
```

---

## 6. Enum vs Union

### 6.1 String Literal Unions Over Enums

```typescript
// ✓ Preferred — zero runtime cost, works with type narrowing
type Status = "active" | "inactive" | "suspended";

// ✗ Numeric enum — opaque at runtime, no reverse mapping safety
enum Status { Active, Inactive, Suspended }
```

### 6.2 Decision Table

| Use Case | Construct | Reason |
|---|---|---|
| Fixed set of string values | `type X = "a" \| "b"` | Zero runtime, full narrowing |
| Need iterable list of values | `const values = ["a", "b"] as const` + `type X = typeof values[number]` | Runtime array + type |
| Bit flags / numeric operations | `const enum Flags { A = 1, B = 2, C = 4 }` | Only valid numeric enum use |
| ✗ General purpose | `enum` | Avoid — unexpected runtime behavior |

### 6.3 `as const` for Exhaustive Value Sets

```typescript
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number]; // "admin" | "editor" | "viewer"

function isRole(v: string): v is Role {
  return (ROLES as readonly string[]).includes(v);
}
```

### 6.4 `const enum` — Restrictions

`const enum` inlines values at compile time. Rules:
- ✗ Use in libraries (breaks `--isolatedModules`, `--preserveConstEnums`)
- Allowed in application code only when bit-flag arithmetic needed
- ✗ String `const enum` — use string literal union instead
