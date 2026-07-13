# Go Standards

> Idiomatic Go: package design, interfaces, the error-value mechanism, concurrency, context, and the go toolchain.

**ID** `go` · **Tier** Language · **Version** 1.0
**Owns** package design · interface design · identifier naming · error values + `%w` wrapping · struct + constructor patterns · goroutine and channel idioms · `context.Context` rules · module layout · go toolchain invocation · Go anti-patterns
**Defers to** test strategy + coverage thresholds + mocking policy → [testing](../testing/STANDARDS.md) · error taxonomy + boundaries + recovery → [error_handling](../error_handling/STANDARDS.md) · lockfile + pinning + supply-chain policy → [dependencies](../dependencies/STANDARDS.md) · layering + dependency direction → [architecture](../architecture/STANDARDS.md) · file + directory naming → [directory](../directory/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md) · budgets + profiling method → [performance](../performance/STANDARDS.md) · log levels + structured fields → [observability](../observability/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [code_writing](../code_writing/STANDARDS.md) · [error_handling](../error_handling/STANDARDS.md) · [testing](../testing/STANDARDS.md) · [dependencies](../dependencies/STANDARDS.md)

---

## Table of Contents

1. [Baseline & Toolchain](#1-baseline--toolchain)
2. [Package Design](#2-package-design)
3. [Interfaces](#3-interfaces)
4. [Naming](#4-naming)
5. [Errors](#5-errors)
6. [Structs & Constructors](#6-structs--constructors)
7. [Concurrency](#7-concurrency)
8. [Context](#8-context)
9. [Modules](#9-modules)
10. [Project Layout](#10-project-layout)
11. [Testing Tools](#11-testing-tools)
12. [Lint & Vet](#12-lint--vet)
13. [Performance Idioms](#13-performance-idioms)
14. [Anti-Patterns](#14-anti-patterns)
15. [Checklist](#15-checklist)

---

## 1. Baseline & Toolchain

Baseline **Go 1.24**, declared in `go.mod`. Generics are available (1.18+); loop variables are per-iteration (1.22+) — the classic closure-capture bug is gone, but ✗ rely on it in code that must build under an older toolchain.

| Job | Tool | Note |
|---|---|---|
| Format | `gofmt` (`gofumpt` optional) | Non-negotiable — zero formatting debate |
| Static analysis | `go vet` | CI gate |
| Meta-lint | `golangci-lint` | CI gate |
| Vulnerabilities | `govulncheck ./...` | CI gate + scheduled |
| Test | `go test -race -count=1 ./...` | `-race` always in CI |
| Structured logging | `log/slog` | ✗ `log` · ✗ third-party loggers in new code |
| Collections | `slices` · `maps` · `cmp` | ✗ hand-rolled sort/contains helpers |
| Randomness | `math/rand/v2` | ✗ `math/rand` · ✗ `rand.Seed` |
| Dev tooling | `tool` directive in `go.mod` (1.24+) | ✗ `tools.go` with blank imports |

---

## 2. Package Design

A package is the unit of compilation, encapsulation, and distribution.

| Rule | Example | ✗ |
|---|---|---|
| Short, lowercase, one word | `auth` · `http` · `userstore` | `authUtils` · `user_store` · `userStore` |
| ✗ underscores, hyphens, mixedCaps | `userstore` | `user_store` |
| ✗ catch-all names | `auth` · `billing` | `util` · `common` · `helpers` · `misc` · `base` |
| ✗ stutter | `auth.Client` | `auth.AuthClient` |
| Package name = last path segment | `internal/auth` → `auth.New()` | — |

Package by **feature**, not by layer: `internal/auth/`, `internal/billing/` — ✗ `models/`, `controllers/`, `services/`, which spread one change across every directory.

`internal/` is a compiler-enforced boundary — nothing outside the module can import it. Domain code starts in `internal/` and is promoted to `pkg/` only when an external consumer actually exists.

---

## 3. Interfaces

Interfaces are satisfied implicitly. Declare them where they are **consumed**, not where they are implemented.

| Rule | Detail |
|---|---|
| 1–3 methods | >3 → the interface is doing too much; split it |
| Defined at the consumer | The caller states what it needs; the provider does not guess |
| Accept interfaces, return concrete structs | The caller chooses the abstraction level |
| ✗ preemptive interfaces | Extract only when a second implementation exists or a test demands a double |
| One method → `-er` name | `Reader` · `Closer` · `Stringer` |
| Two or three → descriptive noun | `Store` · `Cache` · `ReadCloser` |
| ✗ `I`-prefix | `IReader` is not Go |

```go
type UserStore interface {                                  // ✓ declared by the consumer
    GetUser(ctx context.Context, id string) (*User, error)
}

func NewPostgresStore(db *sql.DB) *PostgresStore { ... }    // ✓ returns the concrete type
func NewPostgresStore(db *sql.DB) UserStore      { ... }    // ✗ hides the type from callers
```

---

## 4. Naming

Exported = `PascalCase`. Unexported = `camelCase`. Go names are short — length scales with scope, not with importance.

| Category | Convention | ✗ |
|---|---|---|
| Acronyms | All one case — `HTTPClient` · `ID` · `URL` | `HttpClient` · `Id` · `Url` |
| Local variable | Short and contextual — `r`, `w`, `ctx`, `err` | `requestObject` |
| Loop variable | `i`, `k`, `v` in a short body | `index`, `element` |
| Receiver | 1–2 letters from the type — `func (s *Server)` | `self` · `this` · `me` |
| Constructor | `NewX` → `*X` or `(*X, error)` | `CreateNewServerInstance` |
| Getter | The field name — `s.Name()` | `s.GetName()` |
| Setter | `SetX` | — |
| Boolean query | `IsX` · `HasX` · `CanX` | — |
| Conversion | `String()` · `ToJSON()` | — |
| Sentinel error | `ErrX` | `NotFoundError` as a value |
| Error type | `XError` | — |

---

## 5. Errors

Errors are values, returned as the last result and handled explicitly. Taxonomy and boundary placement → [error_handling](../error_handling/STANDARDS.md).

| Rule | Detail |
|---|---|
| Every returned error is checked | ✗ `_ = f()` when `f` returns an error — `errcheck` enforces |
| Wrap with context at each boundary | `fmt.Errorf("fetch user %s: %w", id, err)` — `%w` preserves the chain, `%v` destroys it |
| Message states the operation, lowercase, no punctuation | `"open config: %w"` — ✗ `"Error: Failed to open config!"` |
| Handle **or** return — never both | Log-and-return duplicates the same failure at every frame |
| `errors.Is` for sentinels · `errors.As` for types | ✗ `err == ErrX` · ✗ `err.(*T)` — both break through wrapping |
| `panic` only for programmer bugs | Impossible state, nil deref, index out of range. ✗ for expected failure |
| Recover at goroutine and process boundaries only | Convert to an error and return it |
| Sentinels for expected conditions | `ErrNotFound` · `ErrConflict` |
| Typed errors when the caller needs fields | `*ValidationError{Field, Message}` |

```go
user, err := store.GetUser(ctx, id)
if err != nil {
    return fmt.Errorf("resolve billing for user %s: %w", id, err)   // ✓ context + chain
}

if err != nil { return err }                        // ✗ no context — a bare chain of nothing
if err != nil { log.Error(err); return err }        // ✗ logged twice, three frames up as well
```

```go
var ErrNotFound = errors.New("not found")

if errors.Is(err, ErrNotFound) { return http.StatusNotFound }

var ve *ValidationError
if errors.As(err, &ve) { return http.StatusBadRequest }
```

Join independent failures with `errors.Join(err1, err2)` — ✗ concatenate error strings.

---

## 6. Structs & Constructors

```go
type Server struct {
    addr    string          // configuration
    timeout time.Duration

    store  Store            // dependencies
    logger *slog.Logger

    mu      sync.Mutex      // state — guarded fields directly below the mutex
    started bool
}
```

| Rule | Detail |
|---|---|
| Group fields: config → dependencies → state | Guarded fields sit directly under the mutex that protects them |
| Order by size within a group | Minimizes padding |
| `mu sync.Mutex` as a named field | ✗ embed it — embedding exports `Lock`/`Unlock` onto the type's API |
| Embed for behavior, not for data reuse | Embedding means "is-a" |
| ✗ embed an exported type in an exported struct | Its methods silently join your public API |
| Constructor validates and returns `(*T, error)` | ✗ a half-constructed struct escaping to the caller |
| Zero value usable, or construction mandatory | Pick one and document it |
| Functional options for optional config | ✗ a constructor with six positional parameters |

```go
type Option func(*Server)

func WithTimeout(d time.Duration) Option { return func(s *Server) { s.timeout = d } }

func NewServer(addr string, opts ...Option) (*Server, error) {
    if addr == "" {
        return nil, errors.New("addr required")
    }
    s := &Server{addr: addr, logger: slog.Default()}
    for _, opt := range opts {
        opt(s)
    }
    return s, nil
}
```

---

## 7. Concurrency

| Rule | Detail |
|---|---|
| ! ✗ start a goroutine without knowing how it stops | Every goroutine has an owner and a shutdown path |
| The starter owns the lifecycle | The function that spawns it provides the stop mechanism |
| Share by communicating | Prefer channels; use a mutex to protect state inside one type |
| ✗ goroutine leaks | A send with no receiver, or a receive with no sender, blocks forever |
| Every long-running loop selects on `ctx.Done()` | Otherwise cancellation is ignored |
| `errgroup.Group` when errors matter | Over `sync.WaitGroup`, which discards them |
| Bounded worker pools | ✗ one goroutine per request item without a limit |

| Primitive | Use | ✗ Misuse |
|---|---|---|
| `sync.Mutex` | Protect fields inside one struct | Cross-goroutine coordination → use a channel |
| `sync.RWMutex` | Read-heavy, write-rare | Write-heavy — the read lock's bookkeeping costs more than it saves |
| `sync.Once` | One-time init that cannot fail | Lazy init that can fail — no error return |
| `sync.WaitGroup` | Wait for N goroutines | When any of them can fail → `errgroup` |
| `sync.Map` | High-contention, stable key set | A general map replacement — it is slower for the common case |
| `atomic.*` | Counters, flags | Multi-word invariants |

`defer mu.Unlock()` on the line after `mu.Lock()`. ✗ hold a lock across I/O or across a call into code you do not control.

```go
func (s *Server) Run(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)
    g.Go(func() error { return s.listenHTTP(ctx) })
    g.Go(func() error { return s.processQueue(ctx) })
    return g.Wait()                        // ✓ blocks until all exit; first error cancels the rest
}

for {
    select {
    case <-ctx.Done():
        return ctx.Err()                   // ✓ cancellable — ✗ a bare `for range jobs` cannot stop
    case job := <-jobs:
        if err := process(job); err != nil {
            return fmt.Errorf("process job %s: %w", job.ID, err)
        }
    }
}
```

---

## 8. Context

`context.Context` carries cancellation, deadline, and request-scoped metadata. Nothing else.

| Rule | Detail |
|---|---|
| First parameter, named `ctx` | `func Do(ctx context.Context, ...)` |
| ✗ store a context in a struct field | Pass it per call — a stored context outlives its request |
| ✗ pass `nil` | `context.TODO()` when genuinely undecided |
| Propagate to every downstream call | DB · HTTP · gRPC · file I/O |
| Set the timeout at the entry point | HTTP handler · CLI command · cron job — and `defer cancel()` immediately |
| ✗ ignore the `cancel` func | Not calling it leaks the timer and the parent's child list |
| Values = request-scoped metadata only | Trace ID · request ID · auth claims. ✗ dependencies, config, or business data |
| Key is an unexported struct type | `type ctxKey struct{}` — ✗ a string key (cross-package collision) |

```go
ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
defer cancel()
user, err := h.store.GetUser(ctx, id)
```

---

## 9. Modules

| Rule | Detail |
|---|---|
| Module path = repository path | `module github.com/org/project` |
| `go` directive = minimum supported version | Not "whatever is installed" |
| `go.sum` always committed | Integrity verification — ✗ hand-edit it |
| `go mod tidy` before every commit | Adds missing, removes unused |
| ✗ `replace` directives in a library | Permitted only in a final binary |
| ✗ commit `vendor/` | Unless the build must be hermetic and offline |
| Checksum mismatch → investigate | ✗ delete `go.sum` and re-tidy to "fix" it |

`go get pkg@version` to add · `go get -u ./... && go mod tidy` to update · `go mod verify` to check · `govulncheck ./...` to scan. Version-selection and supply-chain policy → [dependencies](../dependencies/STANDARDS.md).

---

## 10. Project Layout

```text
project/
├── cmd/server/main.go     ← entry point: parse flags, wire, run
├── internal/
│   ├── auth/              ← domain package (auth.go · token.go · auth_test.go)
│   ├── billing/
│   └── platform/          ← shared types, config, errors
├── pkg/client/            ← public API — only when an external consumer exists
├── go.mod · go.sum
└── Makefile
```

| Directory | Contains | Importable |
|---|---|---|
| `cmd/` | One `main.go` per binary. Wiring only, ✗ logic | — |
| `internal/` | Domain packages. Compiler-enforced privacy | ✗ outside the module |
| `pkg/` | Public library code. Use sparingly | By anyone — permanent contract |

| Rule | Detail |
|---|---|
| One primary type per file, file named after it | `server.go` holds `type Server` |
| `doc.go` for package docs | `// Package auth provides ...` |
| Files ≤ 500 lines | Split by sub-concern beyond that |
| `x_test.go` beside `x.go` | Same package = white box; `x_test` package = black box |

Layering and dependency direction → [architecture](../architecture/STANDARDS.md); directory naming → [directory](../directory/STANDARDS.md).

---

## 11. Testing Tools

Pyramid, coverage thresholds, and mocking policy → [testing](../testing/STANDARDS.md). Go tooling below.

| Rule | Detail |
|---|---|
| Table-driven by default | Named cases, one body |
| `t.Run(tt.name, ...)` subtests | Failures name the case; `-run` targets one |
| `t.Helper()` in every helper | Failure reports the caller's line |
| `t.Cleanup()` for teardown | ✗ manual `defer` chains inside the test body |
| `httptest` for HTTP | ✗ bind a real port |
| `testing/synctest` for concurrent code (1.25+) | Deterministic virtual clock — ✗ `time.Sleep` to "wait" |
| Build tags separate slow tests | `//go:build integration` · `//go:build e2e` |
| `-race` in CI, always | A data race that never fires locally will fire in production |
| ✗ assert on unexported internals | Test behavior through the exported API |

```go
func TestParseSize(t *testing.T) {
    tests := []struct {
        name    string
        input   string
        want    int64
        wantErr bool
    }{
        {name: "bytes", input: "1024", want: 1024},
        {name: "kilobytes", input: "1KB", want: 1024},
        {name: "invalid", input: "abc", wantErr: true},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            got, err := ParseSize(tt.input)
            if tt.wantErr {
                require.Error(t, err)
                return
            }
            require.NoError(t, err)
            assert.Equal(t, tt.want, got)
        })
    }
}

func BenchmarkParse(b *testing.B) {
    input := loadTestData(b)
    for b.Loop() {            // ✓ Go 1.24+ — setup outside the loop is not timed
        _ = Parse(input)
    }
}
```

---

## 12. Lint & Vet

| Gate | Command |
|---|---|
| Format | `gofmt -l .` — output must be empty |
| Vet | `go vet ./...` |
| Lint | `golangci-lint run ./...` |
| Test | `go test -race -count=1 ./...` |
| Vulnerabilities | `govulncheck ./...` |
| Tidy | `go mod tidy && go mod verify` — ✗ diff after running |

Minimum enabled linters: `errcheck` · `govet` · `staticcheck` · `unused` · `ineffassign` · `gocritic` · `revive` · `errorlint` · `errname` · `prealloc` · `bodyclose` · `contextcheck` · `nilerr`.

Every gate is a Makefile target and runs identically in CI. ✗ a lint suppression without a comment naming the reason. Pipeline stages → [cicd](../cicd/STANDARDS.md).

---

## 13. Performance Idioms

Budgets and profiling methodology → [performance](../performance/STANDARDS.md). Go specifics:

| Rule | Detail |
|---|---|
| ✗ optimize without a benchmark | Write `BenchmarkX`, measure, then change. Compare with `benchstat` |
| `b.ReportAllocs()` · `-benchmem` | Allocations per op is the number that matters |
| `make([]T, 0, n)` when `n` is known | ✗ grow a slice by repeated append |
| `strings.Builder` for concatenation | ✗ `+=` in a loop — O(n²) copies |
| ✗ `fmt.Sprintf` in a hot path | `strconv.Itoa` · `strconv.FormatInt` |
| Large structs by pointer | ✗ copy a 200-byte struct per call |
| `sync.Pool` for short-lived reusable buffers | Reset on `Put`; ✗ pool anything holding a reference to request data |
| ✗ `any` / `interface{}` in a hot path | Type assertion + boxing allocation |
| ✗ `reflect` in a hot path | 10–100x slower |
| Profile with pprof | CPU · heap · block · mutex · trace |

```go
var bufPool = sync.Pool{New: func() any { return new(bytes.Buffer) }}

buf := bufPool.Get().(*bytes.Buffer)
defer func() { buf.Reset(); bufPool.Put(buf) }()
```

Beware slice aliasing: `append` may mutate a shared backing array. Copy before handing a sub-slice to code that will retain or modify it.

---

## 14. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| Fire-and-forget `go f()` | Leaks; the error vanishes; shutdown never completes | `errgroup` + `context` |
| `select {}` without `ctx.Done()` | Blocks forever on cancellation | Always add `case <-ctx.Done():` |
| `time.Sleep` for synchronization | Flaky and slow | Channels · `sync.WaitGroup` · `testing/synctest` |
| Unclosed resources | Leaked file descriptors and connections | `defer f.Close()` at open; check `Close()` error on writers |
| Ignoring `Close()` on a writer | Buffered data silently lost | Capture it into the named return |
| `init()` doing real work | Hidden ordering, untestable, unfailable | Explicit init in `main()` or a constructor |
| Package-level mutable state | Data races, test pollution | Pass dependencies explicitly |
| Interface pollution | Abstraction with one implementor | Extract when the consumer needs it |
| `panic` as control flow | Crashes production | Return an error |
| `%v` instead of `%w` when wrapping | `errors.Is`/`As` stop working | `%w` |
| Naked returns in a long function | The reader cannot tell what is returned | Named returns only when the function is ≤10 lines |
| String-keyed context values | Cross-package key collision | Unexported struct key type |
| Nil map write | Panic — a nil map reads fine but cannot be written | `make(map[K]V)` before writing |

```go
func write(path string) (err error) {
    f, err := os.Create(path)
    if err != nil {
        return fmt.Errorf("create %s: %w", path, err)
    }
    defer func() {
        if cerr := f.Close(); cerr != nil && err == nil {
            err = fmt.Errorf("close %s: %w", path, cerr)   // ✓ close error not lost
        }
    }()
    ...
}
```

---

## 15. Checklist

- [ ] `go.mod` declares the minimum supported Go version; `go.sum` committed
- [ ] `go mod tidy` produces no diff
- [ ] ✗ `replace` directives in a library module
- [ ] Package names short, lowercase, single word — ✗ `util` / `common` / `helpers`
- [ ] ✗ stutter — `auth.Client`, not `auth.AuthClient`
- [ ] Domain code lives in `internal/`; `pkg/` only where an external consumer exists
- [ ] Interfaces ≤3 methods, declared at the consumer
- [ ] Functions accept interfaces and return concrete types
- [ ] Every returned error is checked
- [ ] Errors wrapped with `%w` and an operation-naming message
- [ ] Errors compared with `errors.Is` / `errors.As` — ✗ `==` or a type assertion
- [ ] ✗ log-and-return the same error
- [ ] ✗ `panic` for an expected failure
- [ ] `ctx context.Context` is the first parameter; ✗ stored in a struct
- [ ] Every `context.WithTimeout`/`WithCancel` has a matching `defer cancel()`
- [ ] Every goroutine has a known shutdown path; `errgroup` used when errors matter
- [ ] Every long-running loop selects on `ctx.Done()`
- [ ] Mutex scope minimal — ✗ a lock held across I/O
- [ ] Structured logging via `log/slog`
- [ ] Tests are table-driven with named subtests; helpers call `t.Helper()`
- [ ] `gofmt -l .` is empty; `go vet ./...` and `golangci-lint run ./...` pass
- [ ] `go test -race -count=1 ./...` passes
- [ ] `govulncheck ./...` reports no known vulnerabilities
- [ ] ✗ package-level mutable state; ✗ `init()` doing real work
