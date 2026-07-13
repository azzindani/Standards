# Rust Standards

> Idiomatic Rust: ownership, the Result/panic error mechanism, crate structure, traits, unsafe, async, and the cargo toolchain.

**ID** `rust` · **Tier** Language · **Version** 1.0
**Owns** ownership + borrowing idioms · `Result`/`Option`/`?` mechanism · thiserror/anyhow selection · crate + module layout · trait design · type-state + newtype patterns · unsafe rules · tokio async idioms · cargo + workspace config · clippy + rustfmt invocation
**Defers to** test strategy + coverage thresholds + mocking policy → [testing](../testing/STANDARDS.md) · error taxonomy + boundaries + recovery → [error_handling](../error_handling/STANDARDS.md) · lockfile + pinning + supply-chain policy → [dependencies](../dependencies/STANDARDS.md) · layering + dependency direction → [architecture](../architecture/STANDARDS.md) · file + directory naming → [directory](../directory/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md) · budgets + profiling method → [performance](../performance/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [testing](../testing/STANDARDS.md) · [dependencies](../dependencies/STANDARDS.md)

---

## Table of Contents

1. [Baseline & Toolchain](#1-baseline--toolchain)
2. [Ownership & Borrowing](#2-ownership--borrowing)
3. [Error Handling](#3-error-handling)
4. [Crate & Module Structure](#4-crate--module-structure)
5. [Type System](#5-type-system)
6. [Trait Design](#6-trait-design)
7. [Pattern Matching](#7-pattern-matching)
8. [Unsafe](#8-unsafe)
9. [Concurrency & Async](#9-concurrency--async)
10. [Memory](#10-memory)
11. [Cargo & Workspaces](#11-cargo--workspaces)
12. [Testing Tools](#12-testing-tools)
13. [Clippy & rustfmt](#13-clippy--rustfmt)
14. [Performance Idioms](#14-performance-idioms)
15. [Checklist](#15-checklist)

---

## 1. Baseline & Toolchain

| Item | Value |
|---|---|
| Edition | **2024** for new crates. 2021 permitted only for crates with an MSRV below 1.85 |
| MSRV | Declared in `Cargo.toml` as `rust-version`, tested in CI |
| Toolchain pin | `rust-toolchain.toml` — stable channel, same version everywhere |
| Format | `rustfmt` |
| Lint | `clippy` |
| Errors — library | `thiserror` |
| Errors — binary | `anyhow` |
| Async runtime | `tokio` |
| Serialization | `serde` |
| Supply chain | `cargo deny` (licenses + advisories) |

`Cargo.lock` committed for binaries **and** libraries — it pins the CI build, and consumers ignore it. Pinning policy → [dependencies](../dependencies/STANDARDS.md).

---

## 2. Ownership & Borrowing

Preference order: `&T` → `&mut T` → `T` (move) → `.clone()`. Clone is the last resort, never the default.

| Situation | Take |
|---|---|
| Read the value | `&T` |
| Mutate the caller's value | `&mut T` |
| Consume / store the value | `T` |
| Share reads across threads | `Arc<T>` |
| Caller still needs it and no borrow works | `.clone()` — justify at the call site |

### Parameter Types

| ✗ | → | Why |
|---|---|---|
| `&String` | `&str` | Accepts `String`, `&str`, literals |
| `&Vec<T>` | `&[T]` | Accepts arrays, slices, `Vec` |
| `&Box<T>` | `&T` | `Box` derefs transparently |
| `&PathBuf` | `&Path` | Same relationship |
| `String` when only read | `&str` | ✗ force the caller to allocate |

### Lifetimes

| Rule | Detail |
|---|---|
| ✗ annotate what elision infers | `fn first(s: &str) -> &str` needs nothing |
| Annotate when multiple inputs make the output ambiguous | `fn longest<'a>(a: &'a str, b: &'a str) -> &'a str` |
| ✗ `'static` unless the data truly lives for the whole program | Literals, leaked boxes only |
| Struct holding a reference declares a lifetime | `struct Cursor<'a> { data: &'a [u8] }` |
| ✗ lifetimes on owned types | `struct Config { name: String }` |
| ✗ clone inside a loop to appease the borrow checker | Restructure: collect references first, mutate second |

---

## 3. Error Handling

Error taxonomy, boundary placement, and recovery policy → [error_handling](../error_handling/STANDARDS.md). Rust mechanism below.

| Type | For |
|---|---|
| `Result<T, E>` | Fallible operation — the caller needs to know why |
| `Option<T>` | Presence/absence — no failure reason exists |
| `panic!` | Unrecoverable invariant violation only. ✗ in library code |

| Rule | Detail |
|---|---|
| ✗ `.unwrap()` outside tests | `?` \| `match` \| `.expect("invariant: ...")` stating the invariant |
| ✗ `Result<T, String>` | Unstructured, unmatchable |
| ✗ `Box<dyn Error>` in a library's public API | Callers cannot match variants |
| Library errors | Enum implementing `std::error::Error` via `thiserror` |
| Binary errors | `anyhow::Result` + `.context("...")` at each layer |
| Every variant carries diagnostic context | Path, offset, id — enough to debug without a debugger |
| `#[from]` for automatic `?` conversion | ✗ hand-written `From` boilerplate |
| ✗ silent discard | `let _ = fallible();` requires a `// intentional:` comment |
| `#[non_exhaustive]` on public error enums | Adding a variant stays non-breaking |

```rust
#[derive(Debug, Error)]
#[non_exhaustive]
pub enum StorageError {
    #[error("file not found: {path}")]
    NotFound { path: PathBuf },
    #[error("corrupt record at offset {offset}")]
    Corrupt { offset: u64 },
    #[error(transparent)]
    Io(#[from] std::io::Error),
}

fn load_config(path: &Path) -> Result<Config, StorageError> {
    let text = fs::read_to_string(path)?;      // ✓ ? + From — ✗ manual match chain
    Ok(toml::from_str(&text)?)
}
```

---

## 4. Crate & Module Structure

```text
my-project/
├── Cargo.toml            ← [workspace] root, [workspace.dependencies]
├── crates/
│   ├── core/             ← domain logic, zero I/O
│   ├── storage/          ← I/O adapters
│   └── api/              ← HTTP/gRPC surface
└── src/main.rs           ← binary: parse args, wire, run
```

| Rule | Detail |
|---|---|
| `main.rs` holds wiring only | >50 lines of logic in a binary → extract `lib.rs`. Logic in `lib.rs` is testable without running the binary |
| `lib.rs` re-exports the public API | Callers write `crate::Engine`, ✗ `crate::deep::nested::Engine` |
| Private by default | `pub` only for what callers need. Ladder: private → `pub(crate)` → `pub(super)` → `pub` |
| ✗ `pub` struct fields | Except plain data carriers — public fields are a permanent contract |
| One concept per module | ✗ a multi-thousand-line `lib.rs` |
| `module.rs` + `module/` directory | Preferred over `mod.rs` |

Layering and dependency direction → [architecture](../architecture/STANDARDS.md).

---

## 5. Type System

Make illegal states unrepresentable. If a combination of values is invalid, the type must not be able to express it.

### Newtypes

```rust
type UserId = u64;                                   // ✗ alias — u64 and UserId interchangeable
struct UserId(u64);                                  // ✓ newtype — swapping args is a compile error
struct Email(String);                                // ✓ validate in the constructor, parse once
```

Newtype every semantically distinct primitive: IDs · indices · units (`Meters(f64)`, `Bytes(usize)`) · validated strings.

### Enums as State Machines

```rust
enum Connection {
    Disconnected,
    Connecting { attempt: u32 },
    Connected { stream: TcpStream },
    Failed { error: io::Error, retries: u32 },
}
```

Each variant carries only the data valid in that state; transitions consume `self` and return the next state. An invalid state has no constructor.

| Rule | Detail |
|---|---|
| ✗ boolean parameters | `fn open(writable: bool)` → `fn open(mode: Mode)` — a bare `true` at the call site is unreadable |
| ✗ stringly-typed APIs | `fn set_level(level: &str)` → `fn set_level(level: Level)` |
| Zero-sized markers for type-state | `struct Validated;` · `struct Unvalidated;` |
| `PhantomData<T>` | Type parameter needed without storing a `T` |
| `#[must_use]` on constructors + builders | An ignored return value is a bug |

---

## 6. Trait Design

| Scenario | Trait? |
|---|---|
| Two or more real implementations exist now | Yes |
| Test doubles required | Yes — or swap the module under `cfg(test)` |
| Shared behavior across unrelated types | Yes |
| One implementation, "future flexibility" | ✗ No — use the concrete type; add the trait when the second impl appears |

✗ trait-per-struct. A trait with one implementor is indirection with no abstraction.

| Rule | Detail |
|---|---|
| `impl Trait` in argument position | Monomorphized, static dispatch, zero cost |
| `dyn Trait` | Dynamic dispatch + heap. Use when the concrete type varies at runtime; ✗ in a hot path without measuring |
| `where` clause for complex bounds | Keeps the signature readable |
| Bound only on what is called | ✗ `T: Clone + Debug + Send + Sync` when only `Clone` is used |
| Supertrait | Only when every implementor genuinely must implement the parent |
| Extension traits carry the `Ext` suffix | `trait StrExt { fn is_blank(&self) -> bool; }` |
| Sealed trait for public traits not meant to be implemented downstream | Private supertrait — keeps adding methods non-breaking |

---

## 7. Pattern Matching

| Rule | Detail |
|---|---|
| ✗ `_ =>` on an enum you own | Add an arm per variant — a compiler error on a new variant is free correctness. ✗ silence it |
| `_ =>` permitted | `#[non_exhaustive]` foreign enums · integer and string ranges |
| `if let` | Single variant of interest |
| `let ... else` | Early exit without nesting |
| Destructure in the arm | `Ok(Config { port, .. })` |
| ✗ complex guards | More than one condition → extract a named predicate |

```rust
let Some(config) = load_config() else {
    return Err(AppError::NoConfig);
};
```

---

## 8. Unsafe

| Justified | Not justified |
|---|---|
| FFI to C libraries | "The borrow checker was in the way" |
| SIMD intrinsics | Optimization with no benchmark proving the need |
| Manual `Send`/`Sync` on types with hand-proved invariants | "The safe version is verbose" |
| Lock-free structures implementing a published algorithm | "I know this pointer is valid" |
| Platform syscalls with no safe wrapper | Anything with a safe alternative |

| Rule | Detail |
|---|---|
| `unsafe_code = "forbid"` in `[lints.rust]` | Default for every crate that does not need unsafe |
| Every `unsafe` block carries a `// SAFETY:` comment | States which invariant holds and who guarantees it |
| Minimal scope | One operation per block. ✗ safe code inside an unsafe block |
| Safe public API over unsafe internals | Callers never write `unsafe` |
| ✗ `unsafe impl` without written reasoning | Send/Sync claims are proofs, not preferences |
| Miri in CI | `cargo +nightly miri test` over all unsafe paths |
| Fuzz the unsafe boundary | `cargo-fuzz` \| `proptest` |
| Unsafe code gets a dedicated review | Flag it in the PR description |

```rust
let value = unsafe {
    // SAFETY: ptr is non-null and aligned; the caller contract guarantees it
    // points to an initialized T that outlives this borrow.
    ptr.read()
};
```

---

## 9. Concurrency & Async

Compiler-derived `Send`/`Sync` is correct for every safe type. ✗ implement either manually unless building a synchronization primitive.

| Need | Use |
|---|---|
| Shared immutable data | `Arc<T>` |
| Shared mutable, low contention | `Arc<Mutex<T>>` |
| Shared mutable, read-heavy | `Arc<RwLock<T>>` |
| Single result from a task | `oneshot` channel |
| Producer → consumer stream | `mpsc` channel (bounded — an unbounded queue is an OOM waiting to happen) |
| Many producers, many consumers | `crossbeam::channel` |
| Counters and flags | `AtomicU64` · `AtomicBool` |

### Async (Tokio)

| Rule | Detail |
|---|---|
| Tokio for I/O-bound work | Network · file · DB |
| CPU-bound work off the runtime | `tokio::task::spawn_blocking` \| a `rayon` pool — a blocking task starves every other task on the worker |
| ✗ hold a `std::sync::Mutex` guard across `.await` | Not `Send` → compile error, or a deadlock with a re-entrant lock. Restructure, or use `tokio::sync::Mutex` |
| ✗ `tokio::sync::Mutex` when nothing awaits under the lock | `std::sync::Mutex` is faster |
| ✗ `async fn` that never awaits | Make it sync |
| Structured concurrency | `JoinSet` · `tokio::select!` — ✗ unbounded detached `spawn` |
| Cancel safety | Every `.await` is a cancellation point — hold no broken invariant across one |
| ✗ blocking I/O (`std::fs`, `std::net`) in a coroutine | `tokio::fs` · `tokio::net` |

---

## 10. Memory

Default to the stack. Heap only when the size is unknown at compile time, ownership is shared, or the data must outlive the frame.

| Pointer | Ownership | Thread-safe | Use |
|---|---|---|---|
| `Box<T>` | Single | Follows `T` | Trait objects · recursive types · large values |
| `Rc<T>` | Shared, counted | ✗ No | Single-threaded graphs and trees |
| `Arc<T>` | Shared, counted | Yes | Cross-thread sharing |
| `Cow<'a, T>` | Borrowed or owned | Follows `T` | Usually borrowed, occasionally must own |

| ✗ | → |
|---|---|
| `Vec::new()` allocated fresh each loop iteration | Allocate before the loop, `.clear()` and reuse |
| `format!()` to produce a constant string | `&str` literal |
| `.to_string()` on a literal at every call site | Take `&str`; let the caller own if needed |
| `collect::<Vec<_>>()` then immediately iterate | Chain the iterators — skip the allocation |
| `Box<dyn Trait>` for 2–3 known variants | Enum dispatch — stack-allocated, no vtable |
| `Rc<RefCell<T>>` as a default | Restructure ownership; runtime borrow panics are not a design |

---

## 11. Cargo & Workspaces

```toml
[package]
name = "my-crate"
edition = "2024"
rust-version = "1.85"

[lints.rust]
unsafe_code = "forbid"

[lints.clippy]
all = "deny"
pedantic = "warn"
unwrap_used = "deny"
```

All shared dependency versions live in the workspace root's `[workspace.dependencies]`; member crates inherit with `serde = { workspace = true }`. ✗ the same dependency versioned twice in one workspace.

| Rule | Detail |
|---|---|
| Default features = minimal working set | ✗ kitchen-sink defaults — every consumer pays for them |
| Feature names kebab-case | `json-output` · `tls-native` |
| ✗ features that change the shape of the public API | Combinatorial testing burden |
| Features are additive | Enabling one must never break another |
| `cargo tree` before adding a dependency | ✗ 100 transitive crates for one function |
| `cargo deny check` in CI | Licenses + RUSTSEC advisories |
| `cargo build --timings` | Compile-time cost of a heavy dependency needs justification |

---

## 12. Testing Tools

Pyramid, coverage thresholds, and mocking policy → [testing](../testing/STANDARDS.md). Rust tooling below.

| Kind | Location | Command |
|---|---|---|
| Unit | `#[cfg(test)] mod tests` in the same file | `cargo test` |
| Integration | `tests/*.rs` at the crate root | `cargo test` |
| Doc test | `///` example blocks | `cargo test --doc` |
| Property | `proptest` \| `quickcheck` | `cargo test` |
| Benchmark | `benches/*.rs` with `criterion` | `cargo bench` |
| Fuzz | `fuzz/fuzz_targets/*.rs` | `cargo fuzz run <target>` |

| Rule | Detail |
|---|---|
| Test name = `{unit}_{scenario}_{expected}` | `parse_empty_input_returns_error` |
| `assert_eq!` over `assert!(a == b)` | Failure prints both values |
| `assert!(matches!(x, Err(E::Empty)))` | Variant assertions |
| One behavior per test | ✗ a mega-test asserting ten things |
| ✗ `#[ignore]` without a tracker link | In a comment on the attribute |
| Test helpers live under `#[cfg(test)]` | ✗ test utilities compiled into the shipped binary |
| Every public item has a doc test | It is both the example and a compile-checked regression test |

```rust
/// Parses a duration string into seconds.
///
/// ```
/// assert_eq!(my_crate::parse_duration("5m").unwrap(), 300);
/// ```
pub fn parse_duration(s: &str) -> Result<u64, ParseError> { /* ... */ }

proptest! {
    #[test]
    fn roundtrip(input in any::<Config>()) {
        prop_assert_eq!(deserialize(&serialize(&input)?)?, input);
    }
}
```

---

## 13. Clippy & rustfmt

`rustfmt.toml`: `edition = "2024"` · `max_width = 100` · `use_field_init_shorthand = true` · `use_try_shorthand = true`. ✗ further per-team overrides.

| Lint | Level | Reason |
|---|---|---|
| `clippy::unwrap_used` | deny | Forces explicit handling |
| `clippy::expect_used` | warn | Allowed with a message naming the invariant |
| `clippy::panic` | deny in libraries | Libraries return errors |
| `clippy::todo` · `clippy::unimplemented` | deny | ✗ merge incomplete code |
| `clippy::dbg_macro` · `clippy::print_stdout` | deny in libraries | Libraries log, ✗ print |
| `clippy::large_enum_variant` | warn | `Box` the outlier — the enum is as large as its biggest variant |
| `clippy::needless_pass_by_value` | warn | Take `&T` when ownership is not needed |

Gate — every command exits 0 before merge:

```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-features
cargo doc --no-deps
cargo deny check
```

Pipeline stages and caching → [cicd](../cicd/STANDARDS.md).

---

## 14. Performance Idioms

Budgets and profiling methodology → [performance](../performance/STANDARDS.md). Rust specifics:

| Abstraction | Runtime cost |
|---|---|
| Generics (monomorphized) · `impl Trait` | Zero |
| Chained iterators | Zero — fused into one loop |
| Enum dispatch | A branch, no vtable |
| `dyn Trait` | Vtable indirection — measure before using in a hot path |
| `Box<dyn Fn>` closure | Heap + vtable — ✗ in a hot path |

| Rule | Detail |
|---|---|
| Benchmark before optimizing | `criterion` for statistics, ✗ wall-clock `Instant` timing |
| `black_box()` in benchmarks | Prevents the optimizer deleting the code under test |
| `Vec::with_capacity(n)` when `n` is known | ✗ repeated reallocation |
| `BufReader` / `BufWriter` on all file and socket I/O | Unbuffered syscall-per-byte is the default trap |
| Return `impl Iterator` over `Vec` | Lazy, no intermediate allocation |
| Extract a non-generic inner function | Cuts monomorphization bloat from a generic wrapper |
| Profile with `cargo flamegraph` / `perf` | Algorithm first, micro-optimization last |
| Build release with `lto = "thin"` + `codegen-units = 1` | For shipped binaries |

### Conversions and Derives

- Implement `From<A> for B`, never `Into` directly — `Into` comes free. `From` must be infallible; use `TryFrom` when it can fail. ✗ `From` for lossy conversions — give them a named method.
- Every public type derives `Debug`. Derive order: `Debug, Clone, Copy, PartialEq, Eq, Hash, Default, Serialize, Deserialize`.
- `Display` for anything a user sees; it is required by `std::error::Error` and must stay concise. `Debug` may be verbose.
- Builders consume `self` (`fn port(mut self, p: u16) -> Self`) and validate in `build() -> Result<T, E>`.

---

## 15. Checklist

- [ ] `edition = "2024"` and `rust-version` (MSRV) set in `Cargo.toml`
- [ ] `Cargo.lock` committed
- [ ] `[lints.rust] unsafe_code = "forbid"` unless the crate genuinely needs unsafe
- [ ] `[lints.clippy]` sets `all = "deny"`, `pedantic = "warn"`, `unwrap_used = "deny"`
- [ ] Shared dependency versions declared once in `[workspace.dependencies]`
- [ ] Parameters take `&str` / `&[T]` / `&Path`, ✗ `&String` / `&Vec<T>` / `&PathBuf`
- [ ] Every `.clone()` justified — borrow was tried first
- [ ] ✗ `.unwrap()` outside tests; `.expect()` messages name the invariant
- [ ] Library errors are a `thiserror` enum; binaries use `anyhow` with `.context()`
- [ ] ✗ `Result<T, String>` and ✗ `Box<dyn Error>` in a public library API
- [ ] Public error enums are `#[non_exhaustive]`
- [ ] Newtypes used for IDs, units, and validated strings — ✗ bare `u64` / `String`
- [ ] ✗ boolean parameters — enums instead
- [ ] `match` on owned enums is exhaustive — ✗ wildcard arm
- [ ] Every `unsafe` block has a `// SAFETY:` comment; Miri runs over unsafe paths in CI
- [ ] ✗ mutex guard held across an `.await`
- [ ] Channels are bounded; every spawned task is tracked (`JoinSet`), ✗ detached
- [ ] Blocking work runs on `spawn_blocking`, not on the async runtime
- [ ] Every public item has a doc comment; every public function has a doc test
- [ ] `cargo fmt --check` exits 0
- [ ] `cargo clippy --all-targets -- -D warnings` exits 0
- [ ] `cargo test` and `cargo doc --no-deps` exit 0
- [ ] `cargo deny check` passes — licenses and advisories
- [ ] ✗ `todo!()` / `unimplemented!()` / `dbg!()` in committed code
