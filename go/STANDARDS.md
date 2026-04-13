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
