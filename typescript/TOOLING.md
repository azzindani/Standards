# TypeScript Tooling Standards

> Compiler config, package manifest, source layout, lint, test, and runtime-validation rules for a TypeScript repository.

**ID** `typescript/tooling` · **Tier** Language · **Version** 1.0
**Owns** tsconfig · package manifest · project structure · lint · format · TS test framework · runtime validation at boundaries
**Defers to** type system · async · null · TS error mechanism → [typescript](STANDARDS.md) · test pyramid · coverage · mocking policy → [testing](../testing/STANDARDS.md) · lockfiles · version pinning · supply chain → [dependencies](../dependencies/STANDARDS.md) · pipeline stages · gates → [cicd](../cicd/STANDARDS.md) · validation boundary · secrets → [security](../security/STANDARDS.md) · tier model → [architecture](../architecture/STANDARDS.md)
**Load with** [typescript](STANDARDS.md) · [testing](../testing/STANDARDS.md) · [cicd](../cicd/STANDARDS.md) · [dependencies](../dependencies/STANDARDS.md)

---

## Table of Contents

1. [tsconfig](#1-tsconfig)
2. [Package Manifest](#2-package-manifest)
3. [Project Structure](#3-project-structure)
4. [Lint and Format](#4-lint-and-format)
5. [Testing](#5-testing)
6. [Runtime Validation](#6-runtime-validation)
7. [Checklist](#7-checklist)

---

## 1. tsconfig

### 1.1 Required Settings

```jsonc
{
  "compilerOptions": {
    // Type safety — all mandatory
    "strict": true,
    "noUncheckedIndexedAccess": true,        // arr[i] → T | undefined
    "exactOptionalPropertyTypes": true,      // ✗ assign undefined to an optional prop
    "noPropertyAccessFromIndexSignature": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitReturns": true,

    // Modules
    "module": "NodeNext",                    // "Preserve" when a bundler owns emit
    "moduleResolution": "NodeNext",          // "Bundler" when a bundler owns resolution
    "verbatimModuleSyntax": true,            // emit mirrors source; forces `import type`
    "isolatedModules": true,                 // required by esbuild · swc · bun · Vite
    "esModuleInterop": true,
    "resolveJsonModule": true,

    // Output
    "target": "ES2022",                      // floor — Node 18+ baseline
    "lib": ["ES2023"],
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true,
    "outDir": "dist",
    "rootDir": "src",

    // Ergonomics
    "skipLibCheck": true,                    // ✗ typecheck node_modules — not your bug
    "forceConsistentCasingInFileNames": true,
    "paths": { "@/*": ["./src/*"] }
  },
  "include": ["src"],
  "exclude": ["node_modules", "dist"]
}
```

`exactOptionalPropertyTypes` — spelled with `Types`. `exactOptionalProperties` is not a compiler flag and is silently ignored.

### 1.2 Environment Matrix

| Environment | `target` | `module` | `moduleResolution` |
|---|---|---|---|
| Node 18+ ESM | `ES2022` | `NodeNext` | `NodeNext` |
| Bundled app (Vite · esbuild) | `ES2022` | `Preserve` | `Bundler` |
| Browser library | `ES2022` | `ESNext` | `Bundler` |
| Published dual-format library | `ES2022` | `NodeNext` | `NodeNext` |

### 1.3 Path Aliases

One alias prefix per package: `@/*` → `./src/*`. ✗ multiple prefixes outside a monorepo.

`tsc` does NOT rewrite aliases in emitted JS. Runtime resolution requires `tsx`, a bundler, or Node's `imports` field. Published libraries: ✗ path aliases — relative imports only, or consumers break.

### 1.4 Monorepo

Project references + `"composite": true` per package. Root `tsconfig.json` lists `references`; build with `tsc --build`. ✗ a single tsconfig spanning packages — it destroys incremental builds and lets packages import each other's internals.

---

## 2. Package Manifest

### 2.1 Required Fields

```jsonc
{
  "name": "@scope/pkg",
  "version": "1.0.0",
  "type": "module",                 // ESM — non-negotiable
  "engines": { "node": ">=20" },
  "exports": {                      // ✗ "main" alone — `exports` is the modern gate
    ".": {
      "types": "./dist/index.d.ts", // `types` FIRST — resolution order is significant
      "default": "./dist/index.js"
    },
    "./package.json": "./package.json"
  },
  "files": ["dist"],
  "sideEffects": false              // enables tree-shaking; ✗ if the package mutates globals
}
```

`exports` seals the package: unlisted paths become unimportable. Deep imports into `dist/internal/*` are a bug, not a feature.

### 2.2 Scripts

Named exactly. CI invokes these, not raw tool paths → [cicd](../cicd/STANDARDS.md) owns the stages.

| Script | Command | Gate |
|---|---|---|
| `typecheck` | `tsc --noEmit` | Blocking |
| `lint` | `eslint .` | Blocking |
| `format:check` | `prettier --check .` | Blocking |
| `test` | `vitest run` | Blocking |
| `test:coverage` | `vitest run --coverage` | Blocking at threshold |
| `build` | `tsc --build` \| bundler | Blocking |

`tsc --noEmit` is a distinct gate from `build` — a bundler (esbuild, swc, Vite) strips types WITHOUT checking them. ✗ assume a green build means a green typecheck.

### 2.3 Package Manager

| Rule | Detail |
|---|---|
| Manager | `pnpm` default — content-addressed store, strict by default |
| Strictness | ✗ `hoist` / `shamefully-hoist` — undeclared deps must fail |
| Version pinning | `packageManager` field in `package.json` + Corepack |
| Lockfile | Committed. Policy → [dependencies](../dependencies/STANDARDS.md) |
| CI install | `pnpm install --frozen-lockfile` (`npm ci` for npm) — ✗ plain `install` in CI |

---

## 3. Project Structure

Directories map to the tier model → [architecture](../architecture/STANDARDS.md).

```text
src/
├── types/          # Tier 0 — shared types, brands, constants
├── engine/         # Tier 1 — pure domain logic; zero I/O
├── services/       # Tier 2 — orchestration, use cases
├── adapters/       # Tier 3 — I/O: http, db, fs, cli
│   ├── http/
│   └── db/
├── config.ts       # Tier 0 — validated config schema
├── main.ts         # entry point (applications)
└── index.ts        # public API barrel (libraries)
```

| Entity | Convention |
|---|---|
| Source file | `kebab-case.ts` — `user-service.ts` |
| Test file | `*.test.ts`, colocated with source |
| Declaration file | `*.d.ts` |
| Generated code | `src/generated/` — ✗ hand-edit; regenerate |

### 3.1 Declaration Files

| Scenario | Location |
|---|---|
| `process.env` augmentation | `src/env.d.ts` — prefer a validated config object (§6.3) |
| Untyped dependency | `src/types/<package>.d.ts` with `declare module` |
| Global augmentation | ✗ beyond the two rows above — globals are untrackable |

---

## 4. Lint and Format

### 4.1 Toolchain

| Tool | Role |
|---|---|
| `eslint` v9+ | Flat config (`eslint.config.mjs`) — ✗ `.eslintrc` |
| `typescript-eslint` | Type-aware rules — the entire point |
| `prettier` | Formatting. ✗ formatting rules in ESLint — one owner, no debates |
| `oxlint` \| `biome` | Optional fast pre-pass; ✗ replaces type-aware linting |

### 4.2 Minimum Rule Set

```javascript
// eslint.config.mjs
import eslint from "@eslint/js";
import tseslint from "typescript-eslint";

export default tseslint.config(
  eslint.configs.recommended,
  ...tseslint.configs.strictTypeChecked,      // ✗ downgrade to `recommended`
  ...tseslint.configs.stylisticTypeChecked,
  {
    languageOptions: {
      parserOptions: { projectService: true, tsconfigRootDir: import.meta.dirname },
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "error",
      "@typescript-eslint/no-floating-promises": "error",
      "@typescript-eslint/no-misused-promises": "error",
      "@typescript-eslint/switch-exhaustiveness-check": "error",
      "@typescript-eslint/consistent-type-imports": "error",
      "@typescript-eslint/no-non-null-assertion": "error",
      "import/no-cycle": ["error", { maxDepth: 5 }],
      "import/no-default-export": "error",
    },
  },
);
```

`projectService: true` — required for type-aware rules. Without it `strictTypeChecked` silently degrades to syntax-only linting.

### 4.3 Suppressions

| Directive | Verdict |
|---|---|
| `eslint-disable-next-line <rule>` + reason comment | ✓ narrowest scope |
| `eslint-disable` at file top | ✗ |
| `@ts-expect-error` + ticket reference | ✓ — fails once the underlying error disappears |
| `@ts-ignore` | ✗ never |

### 4.4 Pre-Commit

`lint-staged` + `husky` | `lefthook`. Staged `*.ts` → `eslint --fix` → `prettier --write`. Hooks are a fast local mirror of CI, ✗ a replacement for it.

---

## 5. Testing

Pyramid, coverage thresholds, and mocking policy → [testing](../testing/STANDARDS.md). This section owns the TypeScript toolchain only.

### 5.1 Framework

| Need | Tool |
|---|---|
| Runner | `vitest` — default. ESM- and TS-native, no transform config |
| Legacy runner | `jest` + `ts-jest` — existing repos only; ✗ new projects |
| Type-level assertions | `expectTypeOf` (built into vitest) |
| HTTP mocking | `msw` — intercepts at the network layer, ✗ monkey-patching `fetch` |
| Coverage | `vitest run --coverage` (v8 provider) |

Node's built-in `node:test` is acceptable for zero-dependency libraries; it lacks type-level assertions and watch ergonomics.

### 5.2 Type-Level Tests

Types are untested code. Assert the contract of exported generics, brands, and inferred schemas.

```typescript
import { expectTypeOf, test } from "vitest";

test("parseConfig contract", () => {
  expectTypeOf(parseConfig).returns.toEqualTypeOf<Result<Config, ParseError>>();
  expectTypeOf<User["id"]>().toEqualTypeOf<UserId>();
});
```

### 5.3 Mocks

```typescript
vi.mock("../adapters/db/user-repo.js", () => ({
  findById: vi.fn().mockResolvedValue({ id: "1", name: "Test" }),
}));
```

✗ `as any` to satisfy a mock's type · ✗ partial mocks missing required interface fields — both hide the drift the test exists to catch. Mock at the adapter boundary (Tier 3), never inside domain logic.

---

## 6. Runtime Validation

Types evaporate at runtime. Every value crossing an I/O boundary is `unknown` until parsed. The boundary rule itself → [security](../security/STANDARDS.md); this section owns the TypeScript mechanism.

### 6.1 Library

| Library | Use when |
|---|---|
| `zod` | Default — standard-schema compliant, broad ecosystem |
| `valibot` | Bundle-size critical (tree-shakeable, modular) |
| `arktype` | Very large schemas where parse throughput dominates |

One validation library per repo. ✗ mix.

### 6.2 Schema Is the Source of Truth

Declare the schema, infer the type. ✗ hand-write a type and a schema for the same shape — they drift.

```typescript
import { z } from "zod";

const UserSchema = z.object({
  id: z.uuid(),
  name: z.string().min(1).max(200),
  email: z.email(),
  role: z.enum(["admin", "editor", "viewer"]),
});

type User = z.infer<typeof UserSchema>;   // ✗ a separate `interface User`

function handleCreateUser(body: unknown): Result<User, ValidationError> {
  const parsed = UserSchema.safeParse(body);
  if (!parsed.success) return err(new ValidationError("Invalid user", parsed.error.issues));
  return ok(parsed.data);
}
```

`safeParse` at boundaries → returns a `Result`. `parse` (throwing) only at startup, where crashing is correct.

### 6.3 Where to Validate

| Boundary | Rule |
|---|---|
| HTTP body · params · query · headers | Always — typed `unknown` in, parsed out |
| Environment variables | At startup, once. Fail fast, exit non-zero |
| Config files (JSON · YAML · TOML) | At load |
| Third-party API responses | Always — an external contract can change without notice |
| Database rows | When the schema can drift ahead of generated types |
| Message queue payloads | Always — the producer may be an older deploy |
| Internal calls (Tier 0–2) | ✗ — types suffice; runtime checks there are noise |

### 6.4 Environment

```typescript
const EnvSchema = z.object({
  NODE_ENV: z.enum(["development", "production", "test"]),
  PORT: z.coerce.number().int().min(1).max(65_535),
  DATABASE_URL: z.url(),
});

export const env = EnvSchema.parse(process.env);   // throws at startup — correct
```

Export the parsed `env` object. ✗ read `process.env` anywhere else in the codebase.

---

## 7. Checklist

- [ ] `strict: true` plus `noUncheckedIndexedAccess` · `exactOptionalPropertyTypes` · `noImplicitOverride` · `noFallthroughCasesInSwitch`
- [ ] `verbatimModuleSyntax: true` and `isolatedModules: true` set
- [ ] `skipLibCheck: true` — dependency types are not typechecked
- [ ] `package.json` has `"type": "module"` and an `exports` map with `types` listed first
- [ ] `engines.node` declared; `packageManager` field pins the manager version
- [ ] Path aliases absent from published libraries
- [ ] Monorepo packages use project references with `composite: true`
- [ ] Scripts named `typecheck` · `lint` · `format:check` · `test` · `build`
- [ ] `tsc --noEmit` runs in CI as a gate separate from the bundler build
- [ ] CI installs with `--frozen-lockfile` (or `npm ci`), never a plain install
- [ ] `src/` mirrors the tier model: `types/` · `engine/` · `services/` · `adapters/`
- [ ] ESLint flat config with `typescript-eslint` `strictTypeChecked` enabled
- [ ] `projectService: true` set — type-aware rules actually active
- [ ] `no-floating-promises` · `no-misused-promises` · `switch-exhaustiveness-check` all `error`
- [ ] Prettier owns formatting; zero formatting rules in ESLint
- [ ] Zero file-level `eslint-disable`; zero `@ts-ignore`
- [ ] Pre-commit hook runs `eslint --fix` + `prettier --write` on staged files
- [ ] Vitest configured; coverage reported through `--coverage`
- [ ] Exported generics, brands, and inferred schemas covered by `expectTypeOf` tests
- [ ] Mocks are typed — zero `as any`, zero partial mocks of required fields
- [ ] One runtime-validation library across the repo
- [ ] Every schema-backed type is `z.infer`'d — no hand-written twin
- [ ] Every I/O boundary parses `unknown` with `safeParse` before use
- [ ] Environment parsed once at startup into an exported `env` object
- [ ] `process.env` is never read outside the env schema module
