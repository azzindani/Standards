# Go Standards

Go-specific rules for package design, error handling, concurrency, testing,
and tooling. Implements general principles from `architecture/STANDARDS.md`
and `error_handling/STANDARDS.md` in idiomatic Go.

Composable with: Architecture Standards, Code Writing Standards, Error Handling Standards, Testing Standards.

---

## Table of Contents

1. [Package Design](#1-package-design)
2. [Interface Design](#2-interface-design)
3. [Error Handling](#3-error-handling)
4. [Error Types](#4-error-types)
5. [Naming](#5-naming)
6. [Struct Design](#6-struct-design)
7. [Concurrency](#7-concurrency)
8. [Context](#8-context)
9. [Module Structure](#9-module-structure)
10. [Code Organization](#10-code-organization)
11. [Testing](#11-testing)
12. [Tooling](#12-tooling)
13. [Performance](#13-performance)
14. [Go-Specific Anti-Patterns](#14-go-specific-anti-patterns)
15. [Checklist](#15-checklist)

---

## 1. Package Design

Package = unit of compilation, distribution, and encapsulation. See `architecture/STANDARDS.md §5` for module boundary rules.

### Naming Rules

| Rule | Example | Violation |
|---|---|---|
| Short, lowercase, single word | `http`, `json`, `auth` | `httpUtils`, `json_parser` |
| ✗ underscores, hyphens, mixedCaps | `userstore` | `user_store`, `userStore` |
| ✗ generic names | `auth`, `metric` | `util`, `common`, `helpers`, `misc` |
| Package name = last path segment | `import "app/internal/auth"` → `auth.` | — |
| ✗ stutter: type repeats package name | `auth.Client` | `auth.AuthClient` |

### Package Granularity

```go
// ✓ Package by feature — each feature = self-contained package
internal/
  auth/        // authentication + authorization
  billing/     // payment, invoicing
  notify/      // email, push, SMS

// ✗ Package by layer — splits related code across packages
models/
  user.go
  billing.go
controllers/
  user.go
  billing.go
```

### internal/ Packages

- `internal/` prevents external imports — compiler-enforced boundary
- Place domain logic in `internal/` by default; promote to public only when reuse is proven
- Each `internal/` sub-package follows same naming rules

---

## 2. Interface Design

Go interfaces enable implicit satisfaction — define consumers, not providers. See `architecture/STANDARDS.md §9` (contract-first).

### Core Rules

| Rule | Rationale |
|---|---|
| Small interfaces: 1–3 methods | Composable, easy to implement + mock |
| Define interface at consumer, not provider | Consumer knows what it needs |
| Accept interfaces, return concrete structs | Caller decides abstraction level |
| ✗ preemptive interfaces | Only extract when ≥2 implementations exist or testing demands it |

### Interface Naming

| Method Count | Convention | Example |
|---|---|---|
| 1 method | `-er` suffix from method name | `Reader`, `Stringer`, `Closer` |
| 2–3 methods | Descriptive noun | `ReadCloser`, `Store`, `Cache` |
| >3 methods | Likely too large — split | — |

### Pattern: Accept Interface, Return Struct

```go
// ✓ Consumer defines what it needs
type UserStore interface {
    GetUser(ctx context.Context, id string) (*User, error)
}

// ✓ Provider returns concrete type
func NewPostgresStore(db *sql.DB) *PostgresStore {
    return &PostgresStore{db: db}
}

// ✗ Provider returns interface — hides concrete type, prevents extension
func NewPostgresStore(db *sql.DB) UserStore {
    return &PostgresStore{db: db}
}
```

---

## 3. Error Handling

Go errors are values — handle them explicitly. Implements `architecture/STANDARDS.md §7` (error architecture) + `error_handling/STANDARDS.md` in Go idiom.

### Fundamental Rules

| Rule | Detail |
|---|---|
| Always check returned errors | ✗ `_ = f()` when `f` returns error |
| Return `error` as last return value | Convention: `(result, error)` |
| ✗ `panic` for expected failures | `panic` = programmer bug only (index OOB, nil deref, impossible state) |
| Wrap errors with context at each boundary | `fmt.Errorf("fetch user %s: %w", id, err)` |
| ✗ wrap with redundant context | Don't repeat what caller already knows |
| Handle error OR return it — ✗ both | Log-and-return = duplicate noise |

### Wrapping Pattern

```go
// ✓ Add context, preserve chain
user, err := store.GetUser(ctx, id)
if err != nil {
    return fmt.Errorf("resolve billing for user %s: %w", id, err)
}

// ✗ Bare return — no context for debugging
if err != nil {
    return err
}

// ✗ Log AND return — caller will also log
if err != nil {
    log.Error("failed", "err", err)
    return err
}
```

### Error Decision Matrix

| Situation | Action |
|---|---|
| Caller can retry/recover | Return error with context |
| Error is expected (not found, conflict) | Return typed/sentinel error |
| Programmer bug (impossible state) | `panic` with explanation |
| Goroutine boundary | Recover at top, convert to error, send via channel/errgroup |
| HTTP/gRPC boundary | Map to status code, log once at boundary |

---

## 4. Error Types

### Sentinel Errors

```go
// Package-level, exported, ErrX naming
var (
    ErrNotFound     = errors.New("not found")
    ErrUnauthorized = errors.New("unauthorized")
    ErrConflict     = errors.New("conflict")
)
```

### Custom Error Types

```go
// Implement error interface — carry structured context
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation: %s — %s", e.Field, e.Message)
}
```

### Checking Errors

```go
// errors.Is — check sentinel (value equality through chain)
if errors.Is(err, ErrNotFound) {
    return http.StatusNotFound
}

// errors.As — check type (extracts typed error through chain)
var ve *ValidationError
if errors.As(err, &ve) {
    return http.StatusBadRequest
}
```

| Function | Use Case | Checks Through Wrapping |
|---|---|---|
| `errors.Is(err, target)` | Sentinel comparison | Yes |
| `errors.As(err, &target)` | Type extraction | Yes |
| `err == ErrX` | ✗ Breaks on wrapping | No |
| `_, ok := err.(*T)` | ✗ Breaks on wrapping | No |

---

## 5. Naming

Go naming is intentionally terse. Exported = `PascalCase`. Unexported = `camelCase`. See `code_writing/STANDARDS.md` for general naming principles.

### Identifier Rules

| Category | Convention | Example | Violation |
|---|---|---|---|
| Exported type/func/var | `PascalCase` | `HTTPClient`, `NewServer` | `Http_Client` |
| Unexported type/func/var | `camelCase` | `parseHeader`, `connPool` | `parse_header` |
| Acronyms | All caps when exported | `HTTPClient`, `ID`, `URL` | `HttpClient`, `Id` |
| Local variables | Short, contextual | `r`, `w`, `ctx`, `err` | `requestObject` |
| Loop variables | Single letter when body small | `i`, `k`, `v` | `index`, `element` |
| Receiver | 1–2 letter abbreviation of type | `func (s *Server)` | `func (self *Server)`, `func (this *Server)` |
| Test helpers | `testX` or `newTestX` | `newTestServer()` | `createHelperServerForTesting()` |

### Function Naming

| Pattern | Convention | Example |
|---|---|---|
| Constructor | `NewX` returns `*X` | `NewServer(cfg Config) *Server` |
| Constructor with error | `NewX` returns `(*X, error)` | `NewClient(addr string) (*Client, error)` |
| Getter | Field name, ✗ `Get` prefix | `s.Name()` not `s.GetName()` |
| Setter | `SetX` | `s.SetName(n string)` |
| Boolean query | `IsX`, `HasX`, `CanX` | `IsValid()`, `HasChildren()` |
| Conversion | `ToX`, `String`, `Bytes` | `String() string`, `ToJSON() []byte` |

### Interface Naming

```go
// Single-method → -er suffix
type Reader interface { Read(p []byte) (n int, err error) }
type Stringer interface { String() string }
type Handler interface { Handle(ctx context.Context, req Request) error }

// ✗ I-prefix (Java style)
type IReader interface{}  // wrong
```

---

## 6. Struct Design

### Field Ordering

Order fields by alignment to minimize padding. Group logically.

```go
// ✓ Grouped by purpose, larger types first
type Server struct {
    // Configuration
    addr    string
    timeout time.Duration

    // Dependencies
    store  Store
    logger *slog.Logger

    // State
    mu      sync.Mutex
    started bool
}
```

### Embedding Rules

| Rule | Detail |
|---|---|
| Embed for behavior, ✗ for data reuse | Embedding = "is-a", not "has-a" |
| ✗ embed exported type in exported struct | Leaks methods to public API unintentionally |
| Embed `sync.Mutex` as unexported | `mu sync.Mutex` field preferred over embedding |
| Embed interfaces for partial implementation | Useful in test doubles |

```go
// ✓ Embedding for behavior
type CountingWriter struct {
    io.Writer
    count int64
}

// ✗ Embedding for data — use field instead
type Server struct {
    Config  // leaks all Config methods to Server
}
```

### Constructor Functions

```go
// NewX pattern — always validate, return ready-to-use struct
func NewServer(addr string, opts ...Option) (*Server, error) {
    if addr == "" {
        return nil, errors.New("addr required")
    }
    s := &Server{addr: addr}
    for _, opt := range opts {
        opt(s)
    }
    return s, nil
}
```

### Functional Options Pattern

```go
type Option func(*Server)

func WithTimeout(d time.Duration) Option {
    return func(s *Server) { s.timeout = d }
}

func WithLogger(l *slog.Logger) Option {
    return func(s *Server) { s.logger = l }
}
```

---

## 7. Concurrency

Go concurrency = goroutines + channels + sync primitives. See `architecture/STANDARDS.md §9` for concurrency architecture principles.

### Core Rules

| Rule | Detail |
|---|---|
| ✗ start goroutine without knowing how it stops | Every goroutine must have clear shutdown path |
| Caller owns goroutine lifecycle | Function that starts goroutine provides stop mechanism |
| Share by communicating, ✗ communicate by sharing | Prefer channels over shared memory + mutex |
| ✗ goroutine leaks | Unbuffered channel + no reader = permanent leak |
| Always pass `context.Context` for cancellation | Goroutines respect context done signal |

### Goroutine Lifecycle Pattern

```go
func (s *Server) Start(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)

    g.Go(func() error {
        return s.listenHTTP(ctx)
    })
    g.Go(func() error {
        return s.processQueue(ctx)
    })

    return g.Wait()  // blocks until all goroutines exit
}
```

### Channel Patterns

| Pattern | When | Example |
|---|---|---|
| Unbuffered `chan` | Synchronization, handoff | `done := make(chan struct{})` |
| Buffered `chan` | Decouple producer/consumer | `jobs := make(chan Job, 100)` |
| `chan struct{}` | Signal-only, no data | `quit := make(chan struct{})` |
| `select` with `ctx.Done()` | Cancelable operations | See below |

```go
// ✓ Cancelable loop with select
for {
    select {
    case <-ctx.Done():
        return ctx.Err()
    case job := <-jobs:
        if err := process(job); err != nil {
            return fmt.Errorf("process job %s: %w", job.ID, err)
        }
    }
}
```

### Sync Primitives

| Primitive | Use Case | ✗ Misuse |
|---|---|---|
| `sync.Mutex` | Protect shared state in struct | Protecting cross-goroutine coordination (use channel) |
| `sync.RWMutex` | Read-heavy, write-rare | Write-heavy workloads (contention) |
| `sync.Once` | One-time initialization | Lazy init that can fail (no error return) |
| `sync.WaitGroup` | Wait for N goroutines | Prefer `errgroup.Group` when errors matter |
| `sync.Map` | High-contention, key-stable maps | General-purpose map replacement |

### Mutex Discipline

```go
type Cache struct {
    mu    sync.RWMutex
    items map[string]Item
}

// ✓ Lock scope = minimal
func (c *Cache) Get(key string) (Item, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, ok := c.items[key]
    return item, ok
}

// ✗ Lock held across I/O or long operation
func (c *Cache) GetFromDB(ctx context.Context, key string) (Item, error) {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.db.Query(ctx, key)  // holding lock during I/O!
}
```

---

## 8. Context

`context.Context` = cancellation + deadline + request-scoped values. First parameter of every function that does I/O or takes time.

### Rules

| Rule | Detail |
|---|---|
| First parameter, named `ctx` | `func Do(ctx context.Context, ...)` |
| ✗ store context in struct | Pass explicitly per-call |
| ✗ pass `nil` context | Use `context.TODO()` if unsure |
| Propagate to all downstream calls | DB, HTTP, gRPC, file I/O |
| Set timeouts at entry points | HTTP handler, CLI command, cron job |
| Check `ctx.Err()` in long loops | Early exit on cancellation |

### Timeout Propagation

```go
// ✓ Set timeout at entry, propagates through entire call chain
func (h *Handler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
    defer cancel()

    user, err := h.store.GetUser(ctx, r.URL.Query().Get("id"))
    // ...
}
```

### Context Values — Minimal Use

```go
// ✓ Request-scoped metadata only: trace ID, request ID, auth claims
type ctxKey struct{}

func WithTraceID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, ctxKey{}, id)
}

// ✗ Passing dependencies, config, or business data through context
ctx = context.WithValue(ctx, "db", database)  // wrong
```

---

## 9. Module Structure

### go.mod Rules

| Rule | Detail |
|---|---|
| Module path = repository path | `module github.com/org/project` |
| Pin Go version to minimum required | `go 1.22` |
| ✗ commit vendor/ unless required for hermetic builds | Use module proxy |
| Run `go mod tidy` before every commit | Removes unused, adds missing |
| ✗ replace directives in libraries | Only permitted in final binaries |

### Version Management

| Action | Command |
|---|---|
| Add dependency | `go get pkg@version` |
| Update specific | `go get pkg@latest` |
| Update all | `go get -u ./...` then `go mod tidy` |
| Check for vulnerabilities | `govulncheck ./...` |
| Verify checksums | `go mod verify` |

### go.sum

- Always commit `go.sum` — provides integrity verification
- ✗ manually edit `go.sum`
- If checksum mismatch occurs, investigate before running `go mod tidy`

---

## 10. Code Organization

Maps to `architecture/STANDARDS.md §2` tier model. See `directory/STANDARDS.md` for general layout rules.

### Standard Project Layout

```
project/
├── cmd/
│   └── server/
│       └── main.go          // Tier 3: entry point, wiring
├── internal/
│   ├── auth/                 // Tier 1–2: domain packages
│   │   ├── auth.go
│   │   ├── token.go
│   │   └── auth_test.go
│   ├── billing/
│   └── platform/             // Tier 0: shared types, utilities
│       ├── errors.go
│       └── config.go
├── pkg/                      // Public API (use sparingly)
│   └── client/
├── go.mod
├── go.sum
└── Makefile
```

### Directory Rules

| Directory | Purpose | Visibility |
|---|---|---|
| `cmd/` | Binary entry points. One `main.go` per binary | — |
| `internal/` | Private packages. Compiler-enforced | ✗ importable outside module |
| `pkg/` | Public library code. Use only when external consumers exist | Importable by anyone |
| Root `.go` files | Only if module is single-package library | — |

### File Organization Within Package

| Rule | Detail |
|---|---|
| One primary type per file | `server.go` contains `type Server struct` |
| File name = primary type, lowercase | `server.go`, `client.go`, `handler.go` |
| `doc.go` for package documentation | `// Package auth provides...` |
| `_test.go` suffix for tests | Same package or `_test` package |
| Keep files under 500 lines | Split by sub-concern if larger |

### Tier Mapping to Go Packages

| Tier | Go Location | Contains |
|---|---|---|
| 0 (Kernel) | `internal/platform/` or `internal/types/` | Types, constants, pure utilities |
| 1 (Engine) | `internal/{domain}/` | Business logic, validation, transforms |
| 2 (Service) | `internal/{domain}/service.go` or `internal/service/` | Orchestration, workflows |
| 3 (Interface) | `cmd/`, `internal/api/`, `internal/handler/` | HTTP, gRPC, CLI, DB adapters |

---

## 11. Testing

### Core Rules

| Rule | Detail |
|---|---|
| Table-driven tests by default | Reduces boilerplate, covers edge cases |
| Test file = `x_test.go` next to `x.go` | Same package for white-box, `_test` package for black-box |
| Test function = `TestXxx` | `TestServer_Start`, `TestParseConfig_InvalidYAML` |
| ✗ test against implementation details | Test behavior through public API |
| Test helpers return values, ✗ `*testing.T` assertions | Except `t.Helper()` marked functions |

### Table-Driven Tests

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
        {name: "megabytes", input: "1MB", want: 1048576},
        {name: "invalid", input: "abc", wantErr: true},
        {name: "empty", input: "", wantErr: true},
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
```

### Test Helpers

```go
// t.Helper() marks function — failures report caller's line, not helper's
func newTestServer(t *testing.T) *Server {
    t.Helper()
    s, err := NewServer("localhost:0", WithLogger(slog.Default()))
    require.NoError(t, err)
    t.Cleanup(func() { s.Close() })
    return s
}
```

### HTTP Testing

```go
func TestHealthEndpoint(t *testing.T) {
    srv := newTestServer(t)
    
    req := httptest.NewRequest(http.MethodGet, "/health", nil)
    rec := httptest.NewRecorder()
    
    srv.ServeHTTP(rec, req)
    
    assert.Equal(t, http.StatusOK, rec.Code)
    assert.JSONEq(t, `{"status":"ok"}`, rec.Body.String())
}
```

### Benchmark Tests

```go
func BenchmarkParse(b *testing.B) {
    input := loadTestData(b)
    b.ResetTimer()
    for b.Loop() {
        _ = Parse(input)
    }
}
```

### Test Categories

| Tag | Command | Use |
|---|---|---|
| No tag | `go test ./...` | Unit tests — fast, no I/O |
| `//go:build integration` | `go test -tags=integration ./...` | DB, network, file system |
| `//go:build e2e` | `go test -tags=e2e ./...` | Full system tests |
| `-short` flag | `go test -short ./...` | Skip slow tests via `testing.Short()` |

---

## 12. Tooling

### Required Tools

| Tool | Purpose | Enforcement |
|---|---|---|
| `gofmt` | Format code | ✗ commit unformatted code. CI rejects |
| `go vet` | Static analysis (compiler-adjacent) | CI gate |
| `golangci-lint` | Meta-linter (aggregates 50+ linters) | CI gate |
| `staticcheck` | Advanced static analysis | Included in golangci-lint |
| `govulncheck` | Vulnerability scanning | CI gate, weekly |

### golangci-lint Configuration

```yaml
# .golangci.yml — minimal enforced set
linters:
  enable:
    - errcheck       # unchecked errors
    - govet          # suspicious constructs
    - staticcheck    # advanced checks
    - unused         # unused code
    - gosimple       # simplifications
    - ineffassign    # ineffectual assignments
    - typecheck      # type errors
    - gocritic       # opinionated style
    - revive         # replacement for golint
    - errname        # error naming convention
    - errorlint      # error wrapping checks
    - prealloc       # slice preallocation
```

### Makefile Targets

```makefile
.PHONY: lint test build

lint:
	golangci-lint run ./...

test:
	go test -race -count=1 ./...

build:
	go build -o bin/ ./cmd/...

vet:
	go vet ./...

tidy:
	go mod tidy
	go mod verify
```

---

## 13. Performance

See `performance/STANDARDS.md` for general profiling strategy. Go-specific optimizations below.

### Allocation Reduction

| Technique | Example |
|---|---|
| Pre-allocate slices when size known | `make([]T, 0, expectedLen)` |
| Reuse buffers with `sync.Pool` | See below |
| Avoid `fmt.Sprintf` in hot paths | Use `strconv` or string concatenation |
| Pass large structs by pointer | `func process(s *LargeStruct)` not `func process(s LargeStruct)` |
| Use `strings.Builder` for concatenation | ✗ `+=` in loops |
| Return slices, ✗ append to parameter | Caller controls allocation |

### sync.Pool

```go
var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer)
    },
}

func process(data []byte) string {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()
    // use buf...
    return buf.String()
}
```

### Profiling

```go
// CPU profile
import _ "net/http/pprof"
go func() { http.ListenAndServe("localhost:6060", nil) }()
// Then: go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

// Memory profile
// go tool pprof http://localhost:6060/debug/pprof/heap

// Trace
// go tool trace http://localhost:6060/debug/pprof/trace?seconds=5
```

### Benchmark-Driven Optimization

| Rule | Detail |
|---|---|
| ✗ optimize without benchmark proof | Write `BenchmarkX` first, measure, then optimize |
| Use `b.ReportAllocs()` | Track allocations per operation |
| Compare with `benchstat` | `benchstat old.txt new.txt` for statistical comparison |
| `-benchmem` flag | `go test -bench=. -benchmem` |

### Hot Path Rules

| Rule | Detail |
|---|---|
| ✗ `interface{}` / `any` in hot paths | Type assertions have cost |
| ✗ reflection in hot paths | `reflect` = 10–100x slower |
| Minimize allocations per request | Target zero-alloc for critical paths |
| Use `[]byte` over `string` when mutating | Avoid copy on conversion |

---

## 14. Go-Specific Anti-Patterns

| Anti-Pattern | Problem | Fix |
|---|---|---|
| Nil pointer without check | Panic at runtime | Check `if x == nil` before dereference |
| Unclosed resources | Leak: file descriptors, connections, goroutines | `defer f.Close()` immediately after open; check close error on writes |
| `init()` overuse | Hidden execution order, hard to test | Explicit initialization in `main()` or constructors |
| Goroutine fire-and-forget | Leak, lost errors, no shutdown | Use `errgroup`, track lifecycle, pass `context.Context` |
| Naked return in long functions | Unreadable — unclear what's returned | Named returns only when function ≤ 10 lines |
| Interface pollution | Premature abstraction, unused interfaces | Extract interface only when needed by consumer |
| `panic` for control flow | Crashes production, unrecoverable | Return `error` — `panic` only for programmer bugs |
| Empty error wrapping | Lost context — debugging nightmare | Always wrap: `fmt.Errorf("context: %w", err)` |
| Package-level mutable state | Race conditions, test pollution | Pass dependencies explicitly, ✗ global `var` |
| `select{}` without `ctx.Done()` | Goroutine blocks forever if context canceled | Always include `case <-ctx.Done():` |
| String keyed context values | Collision risk across packages | Use unexported struct type as key |
| Ignoring `Close()` errors | Data loss on buffered writers | `if err := w.Close(); err != nil { ... }` |
| Slice append without understanding | Shared backing array mutation | Copy slice before modifying if shared |
| `time.Sleep` for synchronization | Flaky, slow | Use channels, `sync.WaitGroup`, or `sync.Cond` |

### Resource Cleanup Pattern

```go
f, err := os.Create(path)
if err != nil {
    return fmt.Errorf("create %s: %w", path, err)
}
defer func() {
    if cerr := f.Close(); cerr != nil && err == nil {
        err = fmt.Errorf("close %s: %w", path, cerr)
    }
}()
```

---

## 15. Checklist

### Package & Module

- [ ] Package names: short, lowercase, no underscores
- [ ] ✗ stutter (`auth.AuthClient` → `auth.Client`)
- [ ] Domain logic in `internal/`
- [ ] `go mod tidy` run, `go.sum` committed
- [ ] ✗ `replace` directives in library modules

### Interfaces

- [ ] Interfaces ≤ 3 methods
- [ ] Defined at consumer, not provider
- [ ] Functions accept interfaces, return concrete structs

### Errors

- [ ] All returned errors checked
- [ ] Errors wrapped with context at boundaries: `fmt.Errorf("...: %w", err)`
- [ ] Sentinel errors use `ErrX` naming, checked with `errors.Is`
- [ ] Custom error types checked with `errors.As`
- [ ] ✗ `panic` for expected failures
- [ ] ✗ log-and-return (choose one)

### Naming

- [ ] Exported = `PascalCase`, unexported = `camelCase`
- [ ] Acronyms all-caps (`HTTP`, `ID`, `URL`)
- [ ] Receivers = 1–2 letter abbreviation
- [ ] Constructors = `NewX` pattern
- [ ] Getters = field name, ✗ `Get` prefix

### Structs

- [ ] Fields ordered by alignment, grouped by purpose
- [ ] ✗ exported type embedded in exported struct
- [ ] Constructors validate inputs, return `(*T, error)`
- [ ] Functional options for complex configuration

### Concurrency

- [ ] Every goroutine has known shutdown path
- [ ] `context.Context` passed and respected
- [ ] Mutex scope minimized — ✗ lock held during I/O
- [ ] `errgroup` used when goroutine errors matter
- [ ] ✗ goroutine leaks (unbuffered chan with no reader)

### Context

- [ ] First parameter, named `ctx`
- [ ] ✗ stored in struct fields
- [ ] Timeouts set at entry points
- [ ] `ctx.Err()` checked in long loops
- [ ] Context values = request-scoped metadata only

### Testing

- [ ] Table-driven tests with named cases
- [ ] `t.Helper()` on test helper functions
- [ ] `t.Cleanup()` for resource teardown
- [ ] `httptest` for HTTP testing
- [ ] Build tags separate integration/e2e tests
- [ ] Benchmarks use `b.ReportAllocs()`

### Tooling

- [ ] `gofmt` applied (zero tolerance)
- [ ] `go vet` passes
- [ ] `golangci-lint` configured and passing
- [ ] `govulncheck` run periodically
- [ ] `-race` flag in test CI

### Performance

- [ ] Slices pre-allocated when size known
- [ ] `sync.Pool` for frequently allocated buffers
- [ ] ✗ reflection/`any` in hot paths
- [ ] ✗ optimization without benchmark proof
- [ ] `strings.Builder` for string concatenation

### Anti-Patterns Avoided

- [ ] ✗ nil pointer dereference without check
- [ ] ✗ unclosed resources
- [ ] ✗ `init()` for complex initialization
- [ ] ✗ fire-and-forget goroutines
- [ ] ✗ package-level mutable state
- [ ] ✗ `time.Sleep` for synchronization
