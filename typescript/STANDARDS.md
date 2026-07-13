# TypeScript Standards

> Type system, module, async, null, and error rules for every TypeScript source file.

**ID** `typescript` · **Tier** Language · **Version** 1.0
**Owns** type system · interface vs type · module system · async patterns · null handling · TS error mechanism
**Defers to** build config · project structure · lint · runtime validation → [typescript/TOOLING.md](TOOLING.md) · error taxonomy · boundaries · recovery → [error_handling](../error_handling/STANDARDS.md) · test pyramid · coverage · mocking policy → [testing](../testing/STANDARDS.md) · layering · tier model → [architecture](../architecture/STANDARDS.md) · function length · naming → [code_writing](../code_writing/STANDARDS.md)
**Load with** [typescript/TOOLING.md](TOOLING.md) · [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md)

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
9. [Anti-Patterns](#9-anti-patterns)
10. [Checklist](#10-checklist)

---

## 1. Type System

`strict: true` non-negotiable. Zero `any`. Flags live in [TOOLING.md §1](TOOLING.md#1-tsconfig).

`strict: true` enables: `strictNullChecks` · `strictFunctionTypes` · `strictBindCallApply` · `strictPropertyInitialization` · `noImplicitAny` · `noImplicitThis` · `alwaysStrict` · `useUnknownInCatchVariables`. ✗ disable any of them individually.

### 1.1 `unknown`, ✗ `any`

| Scenario | ✗ Wrong | ✓ Correct |
|---|---|---|
| Unknown input | `any` | `unknown` + type guard |
| JSON parse result | `JSON.parse(s) as any` | `JSON.parse(s) as unknown` → validate |
| Third-party untyped | `(lib as any).method()` | declaration file \| `@ts-expect-error` + ticket |
| Callback parameter | `(x: any) => …` | `(x: unknown) => …` + narrowing |

Sole exception: `any` inside `.d.ts` wrapping an untyped dependency when the type is genuinely unknowable at compile time.

### 1.2 Discriminated Unions

Every union of object types carries a literal discriminant field. One discriminant name per project (`kind` | `type` | `status`) — ✗ mix. Exhaustive `switch` over the discriminant + `switch-exhaustiveness-check` → adding a variant breaks the build at every handler.

```typescript
type Result =
  | { kind: "ok"; value: string }
  | { kind: "error"; error: Error };
```

### 1.3 Narrowing

| Priority | Technique | When |
|---|---|---|
| 1 | Discriminated union `switch` | Object variants with discriminant |
| 2 | `in` operator | Duck-typed shapes |
| 3 | Type predicate `v is T` | Reusable narrowing |
| 4 | `instanceof` | Class hierarchies only |
| 5 | `typeof` | Primitives only |

Type predicates must validate at runtime — a predicate that lies is worse than `any`.

```typescript
function isUser(v: unknown): v is User {
  return typeof v === "object" && v !== null && "id" in v && "name" in v;
}
```

### 1.4 `satisfies` over Annotation or Assertion

`satisfies` checks a value against a type while keeping the narrow inferred literal type. Use it for config objects, route tables, and const maps.

```typescript
const routes = { home: "/" } satisfies Record<string, `/${string}`>;  // ✓ checked; home is "/"
const routes: Record<string, string> = { home: "/" };                 // ✗ widens home to string
const routes = { home: 1 } as Record<string, string>;                 // ✗ assertion checks nothing
```

### 1.5 Branded Types

Domain identifiers get brands — passing a `UserId` where an `OrderId` is required becomes a compile error.

```typescript
type UserId = string & { readonly __brand: "UserId" };
type OrderId = string & { readonly __brand: "OrderId" };

function toUserId(id: string): UserId { return id as UserId; }  // ← the only `as` allowed
```

Brand at the validation boundary only — the `as` cast lives inside the constructor, nowhere else.

### 1.6 Readonly by Default

`readonly` on every field not deliberately mutated. `readonly T[]` | `ReadonlyArray<T>` for array parameters a function does not mutate. `as const` for literal tables.

---

## 2. Interface vs Type

| Use case | Keyword | Reason |
|---|---|---|
| Object shape (public contract) | `interface` | Extensible · better error messages |
| Union | `type` | Interfaces cannot express unions |
| Intersection · mapped · conditional | `type` | Interfaces cannot compose these |
| Standalone function signature | `type` | Cleaner |
| Class contract (`implements`) | `interface` | `implements` targets interfaces |
| Primitive alias · branded type | `type` | Interfaces cannot alias primitives |

One project, one convention for object shapes — ✗ mix `interface` and `type` for the same job.

✗ declaration merging in application code. Merging is for library augmentation only.

```typescript
// ✗ Shape silently split across files
interface Config { port: number; }
interface Config { host: string; }

// ✓ Single definition
interface Config { port: number; host: string; }
```

---

## 3. Module System

### 3.1 ESM, ✗ CommonJS

| Rule | Detail |
|---|---|
| Format | ESM `import`/`export`. ✗ `require()` in application code |
| `package.json` | `"type": "module"` |
| `module` / `moduleResolution` | `NodeNext` (Node) \| `Preserve`+`Bundler` (bundled) |
| Import specifiers | `NodeNext` requires the extension: `import { x } from "./foo.js"` |
| `verbatimModuleSyntax` | `true` — emit follows the source exactly; `import type` mandatory for types |
| CJS interop | Tier 3 adapters wrapping legacy dependencies only |

### 3.2 Type-Only Imports

`verbatimModuleSyntax: true` makes `import type` load-bearing: a value import of a type-only module emits a runtime import that can fail or create a cycle.

```typescript
import type { User } from "@/models/user.js";  // ✓ erased at emit
import { type Role, parseRole } from "@/models/role.js"; // ✓ mixed, inline type
```

### 3.3 Import Order

1. Node built-ins (`node:` prefix mandatory — `node:fs/promises`, ✗ `fs`)
2. External packages
3. Internal aliases (`@/…`)
4. Relative (`./…`)

Type-only imports sort last within their group. Enforce with lint, ✗ by hand.

### 3.4 Barrels

| Rule | Detail |
|---|---|
| One barrel per module boundary | `src/models/index.ts` |
| Export public API only | Internal helpers stay unexported |
| Max depth 2 | `src/index.ts` → `src/module/index.ts`. ✗ deeper chains |
| ✗ logic in a barrel | `export { X } from "./x.js"` statements only |
| ✗ default exports | Named exports exclusively |

### 3.5 ✗ Circular Imports

Cycles = architectural violation → [architecture](../architecture/STANDARDS.md). Detect with `import/no-cycle` (`maxDepth: 5`). Fix by extracting shared types to a lower tier — ✗ by reordering imports.

---

## 4. Async Patterns

### 4.1 `async`/`await`

| Rule | Detail |
|---|---|
| Default style | `async`/`await`. ✗ `.then()` chains in application code |
| `.then()` allowed | Callback adapter layers · microtask-scheduling internals |
| `new Promise()` | Wrapping callback APIs in Tier 3 adapters only |
| `Promise.all` / `allSettled` | Use freely with `await` — parallelism is idiomatic |

### 4.2 ✗ Fire-and-Forget

Every promise is awaited, returned, or explicitly voided with a documented reason. Enforced by `@typescript-eslint/no-floating-promises: "error"`.

```typescript
sendAnalytics(event);                          // ✗ unhandled rejection risk
await sendAnalytics(event);                    // ✓
void sendAnalytics(event).catch(logError);     // ✓ background; loss acceptable
```

### 4.3 Cancellation

Every async operation crossing an I/O boundary accepts an `AbortSignal`. ✗ un-cancellable network calls, timers, or streams in long-lived processes.

```typescript
async function fetchUser(id: string, signal?: AbortSignal): Promise<Response> {
  return fetch(`/api/users/${id}`, { signal: signal ?? AbortSignal.timeout(5_000) });
}
```

`AbortSignal.timeout(ms)` for deadlines · `AbortSignal.any([a, b])` to combine caller cancellation with a deadline.

### 4.4 Concurrency

| Combinator | Use when |
|---|---|
| `Promise.all` | All must succeed — fail fast on first rejection |
| `Promise.allSettled` | Need every result regardless of failures |
| `Promise.race` | Timeout · first responder |
| `Promise.any` | First success from redundant sources |

✗ unbounded parallelism over a collection. Bound it.

```typescript
async function mapConcurrent<T, R>(
  items: readonly T[],
  fn: (item: T) => Promise<R>,
  concurrency: number,
): Promise<R[]> {
  const results: R[] = [];
  const running = new Set<Promise<void>>();
  for (const item of items) {
    const p = fn(item).then((r) => { results.push(r); });
    running.add(p);
    void p.finally(() => running.delete(p));
    if (running.size >= concurrency) await Promise.race(running);
  }
  await Promise.all(running);
  return results;
}
```

### 4.5 Async Construction

✗ `async` constructors — not valid TypeScript. Private constructor + static async factory.

```typescript
class Database {
  private constructor(private readonly pool: Pool) {}
  static async create(cfg: DbConfig): Promise<Database> { return new Database(await createPool(cfg)); }
}
```

---

## 5. Null Handling

`strictNullChecks` always on. Every nullable value typed `T | null` | `T | undefined`.

Pick ONE absence value per project:

- `undefined` = not provided / optional field absent
- `null` = explicitly empty / known absence

✗ mix both to mean the same thing.

### 5.1 `??`, ✗ `||`

```typescript
const city = user?.address?.city;      // ✓ optional chaining
const port = config.port ?? 3000;      // ✓ nullish coalescing — respects 0, "", false
const port = config.port || 3000;      // ✗ falsy trap — breaks when port = 0
```

### 5.2 ✗ Non-Null Assertion

| Context | `x!` allowed |
|---|---|
| Test files (`*.test.ts`) | Yes — fixture data known populated |
| Immediately after `Map.has()` guard on the same path | Yes |
| Everywhere else | ✗ — narrow, `??`, or `if` |

```typescript
const name = map.get(key)!;                    // ✗ unguarded
const name = map.get(key) ?? throwMissing(key); // ✓
```

---

## 6. Enum vs Union

✗ `enum` in new code. Union of string literals — zero runtime cost, full narrowing, structurally compatible with JSON.

```typescript
type Status = "active" | "inactive" | "suspended";  // ✓
enum Status { Active, Inactive, Suspended }         // ✗ opaque at runtime
```

| Need | Construct |
|---|---|
| Fixed set of values | `type X = "a" \| "b"` |
| Iterable list + type | `const VALUES = ["a", "b"] as const; type X = (typeof VALUES)[number]` |
| Bit flags / numeric arithmetic | Numeric `const enum` — the only defensible enum |
| Anything else | ✗ `enum` |

```typescript
const ROLES = ["admin", "editor", "viewer"] as const;
type Role = (typeof ROLES)[number];

function isRole(v: string): v is Role {
  return (ROLES as readonly string[]).includes(v);
}
```

`const enum` restrictions: ✗ in published libraries (breaks `isolatedModules`) · ✗ string `const enum` → use a literal union.

---

## 7. Function Types

| Rule | Detail |
|---|---|
| Parameter types | Always explicit |
| Return type — exported function | Always explicit — documents contract, catches drift |
| Return type — internal function | Inference allowed |
| Arrow vs declaration | Declarations for named exports; arrows for callbacks and inline |
| Max positional parameters | 3. Beyond 3 → options object |

```typescript
function createUser(name: string, email: string, role: string, active: boolean): User;  // ✗
function createUser(options: CreateUserOptions): User;                                  // ✓
```

### 7.1 Generics

Constrain every generic. ✗ bare `<T>` unless genuinely universal.

```typescript
function merge<T>(a: T, b: T): T;                                    // ✗ accepts anything
function merge<T extends Record<string, unknown>>(a: T, b: Partial<T>): T; // ✓
```

`extends` to bound · `keyof` for key access · `infer` sparingly. A generic used exactly once in the signature is not a generic — replace it with the concrete type.

### 7.2 Overloads

Overloads only when the return type varies by input. Constant return type → union or optional parameter instead. The implementation signature is not callable by consumers.

```typescript
function parse(input: string): ParsedText;
function parse(input: Buffer): ParsedBinary;
function parse(input: string | Buffer): ParsedText | ParsedBinary { /* … */ }
```

---

## 8. Error Handling

Taxonomy, boundaries, and recovery policy → [error_handling](../error_handling/STANDARDS.md). This section owns only the TypeScript mechanism.

### 8.1 Typed Error Classes

```typescript
abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly statusCode: number;
  constructor(message: string, options?: { cause?: unknown }) {
    super(message, options);       // `cause` is native — ✗ hand-roll a cause field
    this.name = new.target.name;
  }
}

class NotFoundError extends AppError {
  readonly code = "NOT_FOUND";
  readonly statusCode = 404;
}
```

### 8.2 `Result<T, E>` vs `throw`

| Failure | Mechanism |
|---|---|
| Expected business failure (validation, not found, conflict) | `Result<T, E>` |
| Unexpected programmer error (invariant broken) | `throw` |
| I/O boundary failure | `try/catch` at the boundary → return `Result` |
| Impossible branch | `assertNever(x)` |

```typescript
type Result<T, E = Error> =
  | { readonly kind: "ok"; readonly value: T }
  | { readonly kind: "error"; readonly error: E };

const ok = <T>(value: T): Result<T, never> => ({ kind: "ok", value });
const err = <E>(error: E): Result<never, E> => ({ kind: "error", error });

function assertNever(x: never): never {
  throw new Error(`Unreachable: ${JSON.stringify(x)}`);
}
```

### 8.3 `catch` Receives `unknown`

`useUnknownInCatchVariables` (via `strict`) types every caught value as `unknown`. Narrow before touching properties — a thrown value is not necessarily an `Error`. Every `catch` handles, transforms, or propagates; ✗ swallow.

```typescript
try { await riskyOp(); }
catch (e) {                                             // e: unknown
  if (e instanceof AppError) return err(e);
  return err(new InternalError("riskyOp failed", { cause: e }));
}

try { riskyOp(); } catch { /* empty */ }                // ✗ silent
try { riskyOp(); } catch (e) { console.log(e); }        // ✗ logged, not handled
```

---

## 9. Anti-Patterns

### 9.1 Assertions

| Pattern | Verdict | Fix |
|---|---|---|
| `x as T` without validation | ✗ critical | Type guard or schema |
| `x as any` | ✗ critical | `unknown` + narrowing |
| `x as unknown as T` (double) | ✗ critical | Type model is broken — redesign |
| `x satisfies T` | ✓ | Checked, keeps literal type |
| `x as const` | ✓ | Literal inference |
| `x as T` inside a branding constructor | ✓ | Contained, validated |

### 9.2 Implicit `any` Sources

| Source | Caught by |
|---|---|
| `function f(x) {}` | `noImplicitAny` |
| `catch (e)` | `useUnknownInCatchVariables` |
| `obj[key]` | `noPropertyAccessFromIndexSignature` |
| `arr[i]` returning `T` not `T \| undefined` | `noUncheckedIndexedAccess` |
| `JSON.parse(s)` | Nothing — parse as `unknown`, then validate |

### 9.3 Table

| Anti-pattern | Issue | Fix |
|---|---|---|
| `@ts-ignore` | Silences every error on the line | `@ts-expect-error` + ticket — fails when the error disappears |
| Default exports | Import names drift across call sites | Named exports only |
| `namespace` | Legacy, ✗ ESM-compatible | Modules |
| `enum` | Runtime artifact, poor narrowing | String literal union |
| `Function` type | Accepts any callable | Explicit signature |
| `Object` / `{}` | Accepts almost anything | `Record<string, unknown>` or a real shape |
| `export let x` | Mutable live binding | `export const` or accessor function |
| Class holding pure data | Ceremony with no invariant | `interface` + plain object |
| Blanket `Partial<T>` | Hides which fields are required | Purpose-specific optional fields |
| Conditional type nested > 2 levels | Unreadable · slow compiler | Simplify the model or use a typed library |

---

## 10. Checklist

- [ ] `strict: true` — no flag disabled individually
- [ ] Zero `any` outside a `.d.ts` wrapping an untyped dependency
- [ ] Every union of object types has a literal discriminant
- [ ] Type predicates validate at runtime
- [ ] `satisfies` used for config/route/const tables — ✗ widening annotation, ✗ bare assertion
- [ ] Domain identifiers are branded; the `as` cast lives only in the constructor
- [ ] One convention chosen for `interface` vs `type`, applied uniformly
- [ ] ESM: `"type": "module"` · `verbatimModuleSyntax` · `import type` on type-only imports
- [ ] Node built-ins imported with `node:` prefix
- [ ] Zero circular imports (`import/no-cycle` clean)
- [ ] Zero default exports; barrels contain no logic
- [ ] Zero floating promises — awaited, returned, or `void` with a `.catch`
- [ ] Every I/O call accepts an `AbortSignal` or carries a timeout
- [ ] Concurrency over a collection is bounded
- [ ] One absence value (`null` or `undefined`) chosen project-wide
- [ ] `??` used for defaults, never `||`
- [ ] Zero non-null assertions outside tests and immediate guards
- [ ] Zero `enum` outside numeric bit flags
- [ ] Every generic constrained
- [ ] Every exported function has an explicit return type
- [ ] Functions take ≤ 3 positional parameters
- [ ] Errors extend a base `AppError` with `code` + `statusCode`; `cause` uses the native option
- [ ] Expected failures return `Result<T, E>`; `throw` reserved for programmer errors
- [ ] Every `catch` narrows `unknown` before use and handles, transforms, or propagates
- [ ] Zero `@ts-ignore` — `@ts-expect-error` with a ticket where unavoidable
