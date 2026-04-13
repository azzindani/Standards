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

---

## 7. Function Types

### 7.1 Parameter and Return Type Rules

| Rule | Detail |
|---|---|
| Parameter types | Always explicit — ✗ rely on inferred parameter types |
| Return types on public functions | Always explicit — documents contract, catches drift |
| Return types on private/internal | Inferred allowed — reduces noise when function is short |
| Arrow vs function declaration | Declarations for named exports; arrows for callbacks and inline |
| Max parameters | 3 positional. Beyond 3 → use options object |

```typescript
// ✗ Too many positional parameters
function createUser(name: string, email: string, role: string, active: boolean): User;

// ✓ Options object
interface CreateUserOptions {
  name: string;
  email: string;
  role: Role;
  active?: boolean; // default: true
}
function createUser(options: CreateUserOptions): User;
```

### 7.2 Generic Constraints

Always constrain generics. ✗ unconstrained `<T>` unless truly universal.

```typescript
// ✗ Unconstrained — accepts anything
function merge<T>(a: T, b: T): T;

// ✓ Constrained to objects
function merge<T extends Record<string, unknown>>(a: T, b: Partial<T>): T;
```

Use `extends` to bound, `keyof` for key access, `infer` sparingly.

### 7.3 Overloads

Use overloads only when return type varies by input. If return type is constant,
use a union parameter or optional parameter instead.

```typescript
// ✓ Overloads — return type changes based on input
function parse(input: string): ParsedText;
function parse(input: Buffer): ParsedBinary;
function parse(input: string | Buffer): ParsedText | ParsedBinary {
  // implementation
}
```

Implementation signature is not callable — only overload signatures are visible to callers.

### 7.4 Callbacks and Higher-Order Functions

```typescript
// ✓ Named type for reusable callbacks
type Predicate<T> = (item: T) => boolean;
type AsyncMapper<T, R> = (item: T) => Promise<R>;

// ✓ Explicit parameter types in callbacks when not inferable
const filtered = items.filter((item: User): item is ActiveUser => item.active);
```

---

## 8. Error Handling

Ref: `architecture/STANDARDS.md` §7 (Error Architecture), `error_handling/STANDARDS.md`.

### 8.1 Typed Error Classes

Every module defines its own error classes extending a base.

```typescript
abstract class AppError extends Error {
  abstract readonly code: string;
  abstract readonly statusCode: number;
  readonly timestamp = new Date();

  constructor(message: string, public readonly cause?: unknown) {
    super(message);
    this.name = this.constructor.name;
  }
}

class NotFoundError extends AppError {
  readonly code = "NOT_FOUND";
  readonly statusCode = 404;
}

class ValidationError extends AppError {
  readonly code = "VALIDATION_FAILED";
  readonly statusCode = 400;
  constructor(message: string, public readonly fields: string[]) {
    super(message);
  }
}
```

### 8.2 Result Pattern

Prefer `Result<T, E>` over throw/catch for expected failures. Reserve `throw` for
unexpected / programmer errors.

```typescript
type Result<T, E = Error> =
  | { readonly kind: "ok"; readonly value: T }
  | { readonly kind: "error"; readonly error: E };

function ok<T>(value: T): Result<T, never> {
  return { kind: "ok", value };
}

function err<E>(error: E): Result<never, E> {
  return { kind: "error", error };
}

// Usage
function parseConfig(raw: string): Result<Config, ParseError> {
  try {
    const data = JSON.parse(raw) as unknown;
    const config = validateConfig(data);
    return ok(config);
  } catch (e) {
    return err(new ParseError("Invalid config", e));
  }
}
```

### 8.3 Error Handling Decision Table

| Error Type | Mechanism | Example |
|---|---|---|
| Expected business failure | `Result<T, E>` | Validation failure, not found |
| Unexpected programmer error | `throw` | Null deref, index out of bounds |
| Async boundary error | `try/catch` returning `Result` | Network timeout, file not found |
| Exhaustive check failure | `assertNever` | Missing switch case |

```typescript
function assertNever(x: never): never {
  throw new Error(`Unexpected value: ${JSON.stringify(x)}`);
}
```

### 8.4 ✗ Swallowing Errors

```typescript
// ✗ Silent swallow
try { riskyOp(); } catch { /* empty */ }

// ✗ Logging and continuing without handling
try { riskyOp(); } catch (e) { console.log(e); }

// ✓ Handle, transform, or propagate
try {
  riskyOp();
} catch (e) {
  return err(AppError.fromUnknown(e));
}
```

---

## 9. Build Configuration

### 9.1 tsconfig.json — Required Settings

```jsonc
{
  "compilerOptions": {
    // Type safety
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalProperties": true,
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,

    // Module system
    "module": "NodeNext",           // or "ESNext" for bundled apps
    "moduleResolution": "NodeNext", // or "Bundler" for bundled apps
    "esModuleInterop": true,
    "isolatedModules": true,        // required for esbuild/swc/bun
    "verbatimModuleSyntax": true,   // enforces `import type`

    // Output
    "target": "ES2022",             // minimum — baseline for Node 18+
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",

    // Path aliases
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

### 9.2 Target and Module Matrix

| Environment | `target` | `module` | `moduleResolution` |
|---|---|---|---|
| Node 18+ (ESM) | `ES2022` | `NodeNext` | `NodeNext` |
| Node 18+ (CJS legacy) | `ES2022` | `CommonJS` | `Node` |
| Browser (bundled) | `ES2022` | `ESNext` | `Bundler` |
| Library (dual) | `ES2022` | `NodeNext` | `NodeNext` |
| Deno | `ESNext` | `ESNext` | `Bundler` |

### 9.3 Path Aliases

One alias prefix per project: `@/*` → `src/*`. ✗ multiple alias prefixes unless
monorepo with distinct packages.

Runtime resolution requires `tsx`, `tsconfig-paths`, or bundler — raw `tsc` output
does not resolve aliases. Libraries: ✗ path aliases — use relative imports for
published packages.

### 9.4 Project References (Monorepo)

```jsonc
// tsconfig.json (root)
{
  "references": [
    { "path": "packages/core" },
    { "path": "packages/api" }
  ]
}
```

Each package has own `tsconfig.json` with `composite: true`.

---

## 10. Project Structure

Follows `architecture/STANDARDS.md` §2 tier model mapped to directories.

### 10.1 `src/` Layout

```
src/
├── types/           # Tier 0 — shared types, branded types, constants
│   ├── user.ts
│   ├── errors.ts
│   └── index.ts     # barrel
├── engine/          # Tier 1 — domain logic, validators, transforms
│   ├── user.ts
│   └── index.ts
├── services/        # Tier 2 — orchestration, use cases
│   ├── user-service.ts
│   └── index.ts
├── adapters/        # Tier 3 — I/O: HTTP, DB, file, CLI
│   ├── http/
│   ├── db/
│   └── index.ts
├── config.ts        # Tier 0 — config schema
├── main.ts          # entry point (Tier 3)
└── index.ts         # public API barrel (libraries only)
```

### 10.2 File Naming

| Entity | Convention | Example |
|---|---|---|
| Source files | `kebab-case.ts` | `user-service.ts` |
| Test files | `*.test.ts` (colocated) or `__tests__/` | `user-service.test.ts` |
| Type declaration files | `*.d.ts` | `env.d.ts` |
| Constants files | `constants.ts` or within `types/` | `types/roles.ts` |
| Config files | Root of project | `tsconfig.json`, `.eslintrc.cjs` |

### 10.3 Declaration Files

| Scenario | Action |
|---|---|
| Augmenting `process.env` | `src/env.d.ts` with `declare namespace NodeJS` |
| Untyped npm package | `src/types/<package>.d.ts` with `declare module` |
| Global type augmentation | `src/types/global.d.ts` — ✗ pollute global namespace beyond env |
| Generated types (DB schema, API) | `src/generated/` — ✗ hand-edit, regenerate via scripts |

### 10.4 Barrel File Rules

- Barrel (`index.ts`) exports only public API of directory
- ✗ Logic in barrel files — only `export { X } from "./x.js"` statements
- ✗ Default exports — use named exports exclusively
- Entry point `src/index.ts` for libraries; `src/main.ts` for applications

---

## 11. Testing

Ref: `testing/STANDARDS.md` for general test strategy.

### 11.1 Framework

| Category | Tool |
|---|---|
| Test runner | Vitest (preferred) or Jest with `ts-jest` |
| Assertion | Vitest built-in or `expect` from Jest |
| Type testing | `expectTypeOf` (Vitest built-in) or `tsd` |
| Mocking | Vitest `vi.mock` / Jest `jest.mock` |
| HTTP mocking | `msw` (Mock Service Worker) |
| E2E (API) | Supertest + Vitest |

### 11.2 Type Testing

Verify complex types at the type level — catches type regressions without runtime code.

```typescript
import { expectTypeOf } from "vitest";

test("parseConfig returns Config", () => {
  expectTypeOf(parseConfig).returns.toEqualTypeOf<Result<Config, ParseError>>();
});

test("User.id is branded UserId", () => {
  expectTypeOf<User["id"]>().toEqualTypeOf<UserId>();
});
```

### 11.3 Mocking Typed Modules

```typescript
import { vi, describe, it, expect } from "vitest";
import { UserService } from "../services/user-service.js";

// ✓ Typed mock — vi.mock auto-types the module
vi.mock("../adapters/db/user-repo.js", () => ({
  findById: vi.fn().mockResolvedValue({ id: "1", name: "Test" }),
}));

// ✗ Casting to any to bypass types in mocks
// ✗ Incomplete mocks missing required interface fields
```

### 11.4 Test Organization

```typescript
describe("UserService", () => {
  describe("createUser", () => {
    it("returns ok with valid input", async () => { /* ... */ });
    it("returns error for duplicate email", async () => { /* ... */ });
    it("returns error for invalid role", async () => { /* ... */ });
  });
});
```

Rules:
- One `describe` per module/class, nested `describe` per method
- Test names describe expected behavior, not implementation
- Test pure logic (Tier 0–1) with unit tests, no mocks needed
- Test services (Tier 2) with mocked adapters
- Test adapters (Tier 3) with integration tests against real I/O

---

## 12. Linting & Formatting

### 12.1 Required Toolchain

| Tool | Purpose |
|---|---|
| `typescript-eslint` | Type-aware linting |
| `eslint` v9+ | Flat config format |
| `prettier` | Formatting (non-negotiable — ✗ manual formatting debates) |

### 12.2 ESLint — Minimum Rule Set

```typescript
// eslint.config.mjs
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: {
        projectService: true,
        tsconfigRootDir: import.meta.dirname,
      },
    },
    rules: {
      // Critical
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/strict-boolean-expressions": "error",
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/no-non-null-assertion": "warn",

      // Import discipline
      "import/no-cycle": ["error", { maxDepth: 5 }],
      "import/no-default-export": "error",

      // Naming
      "@typescript-eslint/naming-convention": [
        "error",
        { selector: "typeLike", format: ["PascalCase"] },
        { selector: "variable", format: ["camelCase", "UPPER_CASE"] },
        { selector: "function", format: ["camelCase"] },
      ],
    },
  }
);
```

### 12.3 Prettier — Required Settings

```jsonc
// .prettierrc
{
  "semi": true,
  "singleQuote": false,
  "trailingComma": "all",
  "printWidth": 100,
  "tabWidth": 2
}
```

✗ Overriding Prettier with ESLint formatting rules. Prettier owns formatting; ESLint owns logic.

### 12.4 Pre-Commit Enforcement

| Tool | Purpose |
|---|---|
| `lint-staged` | Run linters on staged files only |
| `husky` or `lefthook` | Git hook management |

```jsonc
// package.json
{
  "lint-staged": {
    "*.ts": ["eslint --fix", "prettier --write"]
  }
}
```

---

## 13. Runtime Validation

TypeScript types evaporate at runtime. All data entering Tier 3 boundaries
must be validated. Ref: `architecture/STANDARDS.md` §2 (Tier 3 — I/O boundary).

### 13.1 Validation Library

| Library | Use When |
|---|---|
| `zod` | Default choice — mature, broad ecosystem |
| `valibot` | Bundle-size sensitive (tree-shakeable) |
| `arktype` | Performance-critical with complex schemas |

### 13.2 Schema-First at Boundaries

```typescript
import { z } from "zod";

// Define schema (source of truth)
const UserSchema = z.object({
  id: z.string().uuid(),
  name: z.string().min(1).max(200),
  email: z.string().email(),
  role: z.enum(["admin", "editor", "viewer"]),
});

// Derive TypeScript type from schema — ✗ duplicate type definitions
type User = z.infer<typeof UserSchema>;

// Validate at boundary (Tier 3)
function handleCreateUser(body: unknown): Result<User, ValidationError> {
  const parsed = UserSchema.safeParse(body);
  if (!parsed.success) {
    return err(new ValidationError("Invalid user", parsed.error.issues));
  }
  return ok(parsed.data); // typed as User
}
```

### 13.3 Validation Placement

| Boundary | Validate |
|---|---|
| HTTP request body/params/query | Always — `unknown` → schema |
| Environment variables | At startup — fail fast |
| Config files (JSON/YAML) | At load time |
| Database query results | When schema could drift (generated types preferred) |
| Third-party API responses | Always — external contract can change |
| Internal function calls (Tier 0–2) | ✗ — types are sufficient; runtime checks waste cycles |

### 13.4 Environment Variable Validation

```typescript
const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]),
  PORT: z.coerce.number().int().min(1).max(65535),
  DATABASE_URL: z.string().url(),
  API_KEY: z.string().min(1),
});

// Validate at startup — process exits immediately on failure
export const env = EnvSchema.parse(process.env);
```

---

## 14. Anti-Patterns

### 14.1 Type Assertion Abuse

| Pattern | Severity | Fix |
|---|---|---|
| `x as SomeType` without validation | ✗ Critical | Validate with type guard or schema |
| `x as any` | ✗ Critical | Use `unknown` + narrowing |
| `x as unknown as Target` (double assertion) | ✗ Critical | Redesign types — indicates broken model |
| `x as const` | ✓ Allowed | Literal type inference |
| `x as T` after `is` guard | ✓ Allowed | Guard already validated |

### 14.2 Implicit `any`

Sources of implicit `any` (all caught by `strict: true`):

| Source | Example | Fix |
|---|---|---|
| Untyped function params | `function f(x) {}` | Add parameter type |
| Untyped `catch` clause | `catch (e)` | `useUnknownInCatchVariables` makes it `unknown` |
| Dynamic property access | `obj[key]` | `noPropertyAccessFromIndexSignature` |
| Array index | `arr[i]` | `noUncheckedIndexedAccess` returns `T \| undefined` |
| Untyped JSON | `JSON.parse(s)` | Parse as `unknown`, then validate |

### 14.3 Complex Conditional Types

✗ Conditional types beyond 2 levels of nesting. Unreadable, unmaintainable, slow compiler.

```typescript
// ✗ Over-engineered — nobody can read this
type DeepPartialExcept<T, K extends keyof T> = {
  [P in keyof T]: P extends K ? T[P] : T[P] extends object
    ? T[P] extends Array<infer U>
      ? Array<DeepPartialExcept<U, never>> | undefined
      : DeepPartialExcept<T[P], never> | undefined
    : T[P] | undefined;
};

// ✓ Use a library (ts-toolbelt) or simplify the type model
```

### 14.4 Other Anti-Patterns

| Anti-Pattern | Issue | Fix |
|---|---|---|
| `@ts-ignore` | Silences all errors on next line | `@ts-expect-error` with explanation — fails if error disappears |
| Default exports | Inconsistent naming across imports | Named exports only |
| `namespace` | Legacy TS construct, not ESM-compatible | Use modules |
| `declare global` pollution | Untracked globals | Minimize; use module scope |
| `Function` type | Accepts any callable | Specific signature: `(...args: unknown[]) => unknown` |
| `Object` / `{}` type | Accepts almost anything | `Record<string, unknown>` or specific shape |
| Mutable exports | `export let x = 5` | `export const` or function returning value |
| Class for pure data | Unnecessary complexity | Interface + plain object or `type` |
| Overusing `Partial<T>` | Hides required fields | Explicit optional fields per use case |

---

## 15. Checklist

### New TypeScript Project

- [ ] `strict: true` + `noUncheckedIndexedAccess` + `exactOptionalProperties` in tsconfig
- [ ] `verbatimModuleSyntax: true` enforcing `import type`
- [ ] ESM configured: `"type": "module"` in `package.json`
- [ ] `typescript-eslint` strict + stylistic configs enabled
- [ ] Prettier configured, no format rules in ESLint
- [ ] `@typescript-eslint/no-explicit-any: "error"`
- [ ] `@typescript-eslint/no-floating-promises: "error"`
- [ ] `import/no-cycle` enabled
- [ ] `import/no-default-export` enabled
- [ ] Runtime validation library installed (zod/valibot)
- [ ] Environment variables validated at startup
- [ ] Path alias `@/*` → `src/*` configured (if not library)
- [ ] Pre-commit hooks: `lint-staged` + `husky`/`lefthook`
- [ ] `src/` follows tier model: `types/`, `engine/`, `services/`, `adapters/`

### Per-File Review

- [ ] Zero `any` — `unknown` + narrowing used
- [ ] Zero `@ts-ignore` — `@ts-expect-error` with ticket reference if needed
- [ ] Zero unhandled promises — all `await`ed or explicit `void` with catch
- [ ] Zero non-null assertions outside tests (or with immediate guard)
- [ ] All public functions have explicit return types
- [ ] All discriminated unions have `kind` field
- [ ] All boundary data validated with schema (Tier 3)
- [ ] All imports use `type` keyword for type-only imports
- [ ] No barrel file contains logic
- [ ] No circular imports

### Error Handling Review

- [ ] Custom error classes extend base `AppError`
- [ ] Expected failures use `Result<T, E>` pattern
- [ ] `catch` clauses handle `unknown` — narrow before accessing
- [ ] `assertNever` used in exhaustive switches
- [ ] ✗ empty catch blocks — every catch handles, transforms, or propagates
