# Rust Standards

Idiomatic Rust rules for ownership, error handling, crate design, traits,
concurrency, unsafe, and tooling. Language-specific companion to the general
standards library.

Composable with: architecture/STANDARDS.md, error_handling/STANDARDS.md,
testing/STANDARDS.md, performance/STANDARDS.md, code_writing/STANDARDS.md.

---

## Table of Contents

1. [Ownership & Borrowing](#1-ownership--borrowing)
2. [Error Handling](#2-error-handling)
3. [Crate Structure](#3-crate-structure)
4. [Type System](#4-type-system)
5. [Trait Design](#5-trait-design)
6. [Pattern Matching](#6-pattern-matching)
7. [Unsafe Rules](#7-unsafe-rules)
8. [Concurrency](#8-concurrency)
9. [Memory](#9-memory)
10. [Cargo & Dependencies](#10-cargo--dependencies)
11. [Testing](#11-testing)
12. [Clippy & Formatting](#12-clippy--formatting)
13. [Performance](#13-performance)
14. [Idiomatic Patterns](#14-idiomatic-patterns)
15. [Checklist](#15-checklist)

---

## 1. Ownership & Borrowing

See architecture/STANDARDS.md §1 — principle #14 (every resource has exactly one owner).

### Borrow by Default

| Situation | Use | Why |
|---|---|---|
| Reading data | `&T` | Zero-cost, no ownership transfer |
| Mutating caller's data | `&mut T` | Single-writer guarantee |
| Transferring ownership | `T` (move) | Caller done with value |
| Shared read across threads | `Arc<T>` | Thread-safe ref counting |
| Need owned copy, source still needed | `.clone()` | Explicit cost |

**Rule:** prefer `&T` → `&mut T` → `T` (move) → `.clone()`. Clone is last resort, never default.

### When to Clone

```rust
// ✓ clone when storing data that outlives the borrow
fn register_name(registry: &mut Vec<String>, name: &str) {
    registry.push(name.to_owned());
}

// ✗ clone to avoid fighting the borrow checker
fn bad(data: &Vec<String>) -> Vec<String> {
    data.clone() // restructure logic instead
}
```

### Lifetime Annotations

| Rule | Example |
|---|---|
| Elision covers most cases — ✗ annotate when compiler infers correctly | `fn first(s: &str) -> &str` |
| Annotate when multiple input lifetimes → ambiguous output | `fn longest<'a>(a: &'a str, b: &'a str) -> &'a str` |
| ✗ `'static` unless data truly lives for entire program | String literals, leaked boxes only |
| Struct holding references → explicit lifetime | `struct Cursor<'a> { data: &'a [u8] }` |
| ✗ lifetime annotations on owned types | `struct Config { name: String }` — no lifetime needed |

### Ownership Transfer Patterns

```rust
// Builder takes ownership — caller can't reuse partial state
let config = ConfigBuilder::new()
    .port(8080)
    .host("localhost".into())
    .build();

// Accept Into<T> for ergonomic ownership transfer
fn connect(addr: impl Into<SocketAddr>) -> Connection { /* ... */ }
```

### Common Anti-Patterns

| Anti-pattern | Fix |
|---|---|
| `&String` in function params | Use `&str` — accepts both `String` and `&str` |
| `&Vec<T>` in function params | Use `&[T]` — accepts arrays, slices, Vec |
| `&Box<T>` in function params | Use `&T` — Box is transparent |
| Cloning inside loops to satisfy borrow checker | Restructure: collect refs first, process second |
| Returning references to local variables | Return owned data or use lifetime-bound structs |

---

## 2. Error Handling

See architecture/STANDARDS.md §7 — error architecture.
See architecture/STANDARDS.md §1 — principle #15 (represent absence explicitly, never null → `Option<T>`).

### Result vs Option

| Type | Use for |
|---|---|
| `Result<T, E>` | Operations that can fail — caller needs to know why |
| `Option<T>` | Value presence/absence — no error context needed |
| ✗ `panic!()` | Only in tests, prototypes, or truly unrecoverable invariant violations |
| ✗ `.unwrap()` in production | Use `.expect("context")` at minimum; prefer `?` or match |

### The `?` Operator

```rust
// ✓ propagate errors with ? — clean, composable
fn load_config(path: &Path) -> Result<Config, AppError> {
    let contents = fs::read_to_string(path)?;
    let config: Config = toml::from_str(&contents)?;
    Ok(config)
}

// ✗ manual match chains for simple propagation
fn load_config_bad(path: &Path) -> Result<Config, AppError> {
    let contents = match fs::read_to_string(path) {
        Ok(c) => c,
        Err(e) => return Err(e.into()),
    };
    // ... tedious
}
```

### Error Type Selection

| Crate type | Error strategy | Crate |
|---|---|---|
| Library | Custom enum implementing `std::error::Error` | `thiserror` |
| Application binary | Opaque error with context chain | `anyhow` |
| Mixed (lib + bin) | `thiserror` in lib, `anyhow` in `main.rs` | Both |

### Custom Error Types with `thiserror`

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum StorageError {
    #[error("file not found: {path}")]
    NotFound { path: PathBuf },

    #[error("permission denied: {path}")]
    PermissionDenied { path: PathBuf },

    #[error("corrupt data at offset {offset}")]
    Corrupt { offset: u64 },

    #[error(transparent)]
    Io(#[from] std::io::Error),
}
```

### Error Rules

| Rule |
|---|
| ✗ string errors (`Result<T, String>`) — unstructured, unmatchable |
| ✗ `Box<dyn Error>` in library public API — callers can't match variants |
| Every error variant carries enough context to diagnose without a debugger |
| Implement `From<SourceError>` for automatic `?` conversion |
| Log errors at the boundary where they're handled, not where created |
| ✗ discard errors silently — `let _ = fallible()` requires `// intentional` comment |

---

## 3. Crate Structure

### Workspace Layout

```
my-project/
├── Cargo.toml          ← workspace root, [workspace] members
├── crates/
│   ├── core/           ← domain logic, zero I/O (Tier 0–1)
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   ├── storage/        ← I/O adapters (Tier 3)
│   │   ├── Cargo.toml
│   │   └── src/lib.rs
│   └── api/            ← HTTP/gRPC surface (Tier 3)
│       ├── Cargo.toml
│       └── src/lib.rs
├── src/
│   └── main.rs         ← binary entry point, wiring only
└── tests/
    └── integration.rs  ← cross-crate integration tests
```

### lib.rs vs main.rs

| File | Purpose | Contains |
|---|---|---|
| `lib.rs` | Reusable library logic | Types, traits, impls, public API |
| `main.rs` | Binary entry point | CLI parsing, wiring, startup only |
| ✗ `main.rs` with logic | Move logic to `lib.rs` — enables testing without binary |

**Rule:** binary crates with >50 lines of logic → extract `lib.rs`.

### Module Organization

```rust
// src/lib.rs — re-export public API, hide internal modules
mod parser;
mod validator;
mod engine;

pub use parser::Parser;
pub use validator::{Validator, ValidationError};
pub use engine::Engine;
```

| Rule |
|---|
| One module per concept — ✗ multi-thousand-line `lib.rs` |
| `mod.rs` acceptable but prefer `module_name.rs` + `module_name/` directory |
| Private by default — `pub` only for items callers need |
| `pub(crate)` for internal cross-module access |
| ✗ `pub` on struct fields unless struct is a plain data carrier |
| Re-export public API from `lib.rs` root — callers use `crate::Type`, not `crate::deep::nested::Type` |

### Visibility Ladder

```rust
fn private()              // module-only (default)
pub(crate) fn internal()  // crate-wide
pub(super) fn parent()    // parent module
pub fn public()           // external API
```

**Rule:** start private, widen only when needed. Every `pub` item = API contract you must maintain.

---

## 4. Type System

### Newtype Pattern

Wrap primitive types to prevent mixing semantically different values.

```rust
// ✗ type aliases — compiler treats them as identical
type UserId = u64;
type OrderId = u64;
fn process(user: UserId, order: OrderId) {} // can swap args — no compiler error

// ✓ newtypes — compiler enforces distinction
struct UserId(u64);
struct OrderId(u64);
fn process(user: UserId, order: OrderId) {} // swapped args → compile error
```

| When to newtype |
|---|
| IDs, indices, keys — any semantically distinct integer/string |
| Units: `Meters(f64)`, `Seconds(u64)`, `Bytes(usize)` |
| Validated strings: `Email(String)`, `Hostname(String)` — validate in constructor |
| Foreign types needing local trait impls (orphan rule workaround) |

### Enums as State Machines

```rust
// Each variant carries only the data valid for that state
enum Connection {
    Disconnected,
    Connecting { attempt: u32 },
    Connected { stream: TcpStream, since: Instant },
    Failed { error: io::Error, retries: u32 },
}

// Transitions are explicit — ✗ invalid states
impl Connection {
    fn connect(self) -> Connection {
        match self {
            Connection::Disconnected => Connection::Connecting { attempt: 1 },
            Connection::Failed { retries, .. } => Connection::Connecting { attempt: retries + 1 },
            other => other, // already connecting/connected
        }
    }
}
```

See architecture/STANDARDS.md §6 — state architecture (states as types, transitions as functions).

### Type System Rules

| Rule |
|---|
| Make illegal states unrepresentable — if a combination is invalid, the type system prevents it |
| ✗ boolean parameters — use enums: `enum Mode { Read, Write }` not `fn open(writable: bool)` |
| ✗ stringly-typed APIs — `fn set_level(level: &str)` → `fn set_level(level: Level)` |
| Zero-sized types (ZST) for type-level markers: `struct Validated;` `struct Unvalidated;` |
| `PhantomData<T>` when type parameter needed without storing T |

---

## 5. Trait Design

### When to Define Traits

| Scenario | Trait? | Alternative |
|---|---|---|
| Multiple concrete implementations needed now | Yes | — |
| Mocking for tests | Yes, or use `cfg(test)` module swap | Function pointers |
| Single implementation, future flexibility | ✗ No | Concrete type; add trait when second impl appears |
| Shared behavior across unrelated types | Yes | — |
| Marker for type-level constraints | Yes (empty trait) | — |

**Rule:** ✗ trait-per-struct. Traits are abstractions — don't create them for a single impl unless testing demands it.

### Trait Bound Rules

```rust
// ✓ impl Trait for simple single-use bounds
fn serialize(item: &impl Serialize) -> Vec<u8> { /* ... */ }

// ✓ where clause for complex bounds
fn merge<T>(a: T, b: T) -> T
where
    T: Clone + Ord + Debug,
{ /* ... */ }

// ✓ trait objects for heterogeneous collections
fn handlers() -> Vec<Box<dyn Handler>> { /* ... */ }
```

| Rule |
|---|
| `impl Trait` in arg position → monomorphized, zero-cost dispatch |
| `dyn Trait` → dynamic dispatch, heap allocation — use when types vary at runtime |
| ✗ `dyn Trait` in hot paths without measuring — vtable call overhead |
| Bound only on traits actually used — ✗ `T: Clone + Debug + Send + Sync` if only `Clone` is called |
| Supertraits (`trait A: B`) only when every implementor of A must also implement B |

### Blanket Implementations

```rust
// ✓ blanket impl when behavior is universally derivable
impl<T: Display> Loggable for T {
    fn log(&self) { println!("{}", self); }
}
```

✗ blanket impls that conflict with user-defined impls. Test with concrete types before publishing.

### Extension Traits

```rust
// Add methods to foreign types without newtypes
trait StrExt {
    fn is_blank(&self) -> bool;
}

impl StrExt for str {
    fn is_blank(&self) -> bool {
        self.trim().is_empty()
    }
}
```

Convention: suffix `Ext` for extension traits on foreign types.

---

## 6. Pattern Matching

### Exhaustive Matching

```rust
// ✓ handle every variant — compiler enforces
match event {
    Event::Start { id } => begin(id),
    Event::Data { payload } => process(payload),
    Event::End => finish(),
}

// ✗ wildcard catch-all hiding new variants
match event {
    Event::Start { id } => begin(id),
    _ => (), // new Event::Error variant silently ignored
}
```

| Rule |
|---|
| ✗ `_ =>` on enums you control — add explicit arms for each variant |
| `_ =>` acceptable for foreign enums marked `#[non_exhaustive]` |
| `_ =>` acceptable for large integer/string ranges |
| Compiler error on missed variant = free correctness — don't silence it |

### Destructuring

```rust
// ✓ destructure in match arms — access fields directly
match result {
    Ok(Config { port, host, .. }) => connect(host, port),
    Err(e) => handle_error(e),
}

// ✓ if-let for single-variant interest
if let Some(user) = find_user(id) {
    greet(user);
}

// ✓ let-else for early exit (Rust 1.65+)
let Some(config) = load_config() else {
    return Err(AppError::NoConfig);
};
```

### Match Guards

```rust
match value {
    n @ 1..=100 if n % 2 == 0 => even(n),
    n @ 1..=100 => odd(n),
    _ => out_of_range(),
}
```

✗ complex logic in guards — extract to named function if guard exceeds one condition.

---

## 7. Unsafe Rules

### When Unsafe is Justified

| Justified | Not Justified |
|---|---|
| FFI calls to C libraries | Bypassing borrow checker "because it's hard" |
| SIMD intrinsics | Performance optimization without benchmarks proving need |
| Implementing `Send`/`Sync` for types with manual invariants | Convenience — "safe version is verbose" |
| Lock-free data structures with proven algorithms | "I know this pointer is valid" without proof |
| Platform-specific syscalls | ✗ ever in application code if safe alternative exists |

### Unsafe Block Rules

```rust
// ✓ minimal unsafe scope — only the operation that requires it
let value = unsafe {
    // SAFETY: pointer is non-null and aligned, validated by caller contract.
    // Lifetime tied to parent struct which holds the allocation.
    ptr.read()
};

// ✗ large unsafe block covering safe operations
unsafe {
    let x = compute(); // safe — should be outside
    ptr.write(x);      // actually unsafe
    log(x);            // safe — should be outside
}
```

| Rule |
|---|
| Every `unsafe` block requires a `// SAFETY:` comment explaining why invariants hold |
| Minimize unsafe scope — one operation per block when possible |
| Encapsulate unsafe behind safe public API — callers never write `unsafe` |
| ✗ `unsafe impl` without formal reasoning about invariants |
| Unsafe code requires dedicated review — tag in PR description |
| Run Miri (`cargo +nightly miri test`) on all unsafe code in CI |
| Fuzz unsafe boundary functions with `cargo-fuzz` or `proptest` |

### Encapsulation Pattern

```rust
pub struct AlignedBuffer {
    ptr: *mut u8,
    len: usize,
}

impl AlignedBuffer {
    /// Creates a new buffer with guaranteed 64-byte alignment.
    pub fn new(size: usize) -> Self {
        let layout = Layout::from_size_align(size, 64).unwrap();
        // SAFETY: layout is non-zero (checked above), alloc returns aligned ptr
        let ptr = unsafe { alloc::alloc(layout) };
        Self { ptr, len: size }
    }

    pub fn as_slice(&self) -> &[u8] {
        // SAFETY: ptr valid for len bytes, lifetime tied to &self
        unsafe { std::slice::from_raw_parts(self.ptr, self.len) }
    }
}
```

**Rule:** safe public API + unsafe private internals = safe abstraction. Callers get safety guarantees without `unsafe` in their code.

---

## 8. Concurrency

See architecture/STANDARDS.md §9 — concurrency architecture.

### Send and Sync

| Trait | Meaning | Auto-derived when |
|---|---|---|
| `Send` | Safe to transfer to another thread | All fields are `Send` |
| `Sync` | Safe to share `&T` across threads | All fields are `Sync` |
| `!Send` | ✗ move between threads | Contains `Rc`, raw pointers, etc. |
| `!Sync` | ✗ shared references across threads | Contains `Cell`, `RefCell`, etc. |

**Rule:** ✗ implement `Send`/`Sync` manually unless building a sync primitive. Compiler auto-derives correctly for safe types.

### Concurrency Primitive Selection

| Need | Primitive | When |
|---|---|---|
| Shared read-only data | `Arc<T>` | Immutable data across tasks/threads |
| Shared mutable data (low contention) | `Arc<Mutex<T>>` | Short critical sections, infrequent writes |
| Shared mutable data (read-heavy) | `Arc<RwLock<T>>` | Many readers, few writers |
| One-shot value passing | `oneshot` channel | Single result from spawned task |
| Stream of values | `mpsc` channel | Producer-consumer pipelines |
| Many producers, many consumers | `crossbeam::channel` | Fan-in or work distribution |
| Lock-free counters | `AtomicU64`, `AtomicBool` | Metrics, flags, reference counts |

### Async Rust (Tokio)

```rust
// ✓ tokio for I/O-bound concurrent work
#[tokio::main]
async fn main() -> Result<()> {
    let listener = TcpListener::bind("0.0.0.0:8080").await?;
    loop {
        let (stream, _) = listener.accept().await?;
        tokio::spawn(handle_connection(stream));
    }
}
```

| Rule |
|---|
| Tokio for I/O-bound work (network, file, DB) |
| `std::thread` for CPU-bound work — ✗ block tokio runtime with CPU tasks |
| `tokio::task::spawn_blocking` to bridge CPU work into async context |
| ✗ hold `Mutex` guard across `.await` — use `tokio::sync::Mutex` if unavoidable |
| ✗ `async` on functions that don't `.await` — just make them sync |
| Prefer structured concurrency: `tokio::select!`, `JoinSet` over unbounded `spawn` |
| ✗ `tokio::sync::Mutex` when `std::sync::Mutex` suffices (no await while locked) |
| Cancel safety: every `.await` point is a potential cancellation — hold no invariants across awaits |
