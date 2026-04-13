# Performance Standards

Rules for measuring, budgeting, and optimizing system performance.
Measure first, optimize second. Every optimization traces to measured data.

Derived from: Mechanical Sympathy, Brendan Gregg's USE Method,
Google SRE performance practices, cache-aside/write-through patterns,
database query optimization, Linux kernel resource management,
and principle #29 from architecture/STANDARDS.md §1.

Composable with: Architecture Standards, Database Standards,
Observability Standards, API Standards, DevOps Standards.

---

## Table of Contents

1. [Performance Philosophy](#1-performance-philosophy)
2. [Performance Budgets](#2-performance-budgets)
3. [Profiling](#3-profiling)
4. [Caching Strategy](#4-caching-strategy)
5. [Lazy Loading](#5-lazy-loading)
6. [Memory Management](#6-memory-management)
7. [I/O Optimization](#7-io-optimization)
8. [Query Performance](#8-query-performance)
9. [Algorithm Selection](#9-algorithm-selection)
10. [Resource Budgets](#10-resource-budgets)
11. [Benchmarking](#11-benchmarking)
12. [Scale Matrix](#12-scale-matrix)
13. [Performance Checklist](#13-performance-checklist)

---

## 1. Performance Philosophy

### Core Rules

| # | Rule |
|---|---|
| 1 | ✗ optimize without measurement — profiling data required before any change |
| 2 | Correctness first, clarity second, performance third |
| 3 | Optimize the hot path; ignore the cold path until budgets break |
| 4 | One change per optimization cycle — isolate cause and effect |
| 5 | Every optimization carries a readability cost — cost must justify gain |
| 6 | Measure end-to-end latency, not just component time |
| 7 | Performance is a feature with regression tests, not an afterthought |
| 8 | ✗ speculative optimization — "it might be slow" is not evidence |

### Optimization Protocol

1. Define performance budget for the operation (§2)
2. Measure current performance against budget
3. If within budget → stop. ✗ optimize what is fast enough
4. Profile to identify bottleneck (§3)
5. Fix the single largest bottleneck
6. Measure again — verify improvement, check for regressions
7. Repeat from step 3 until budget met

### Amdahl's Law Awareness

Optimizing a component that accounts for 5% of total time yields
at most 5% improvement. Always identify the dominant time consumer
before optimizing. If 90% of time is I/O, optimizing CPU logic is waste.

---

## 2. Performance Budgets

### Response Time Tiers

| Operation class | P50 target | P99 target | Hard ceiling |
|---|---|---|---|
| In-memory lookup | < 1ms | < 5ms | 10ms |
| Local cache hit | < 5ms | < 20ms | 50ms |
| Database read (indexed) | < 10ms | < 50ms | 200ms |
| Database write | < 20ms | < 100ms | 500ms |
| External API call | < 100ms | < 500ms | 2s |
| Report/aggregation | < 500ms | < 2s | 10s |
| Batch job (per item) | < 50ms | < 200ms | 1s |
| Full page render | < 200ms | < 1s | 3s |

P99 is the accountability metric. P50 is the planning metric.
Hard ceiling = circuit-breaker trigger point.

### Startup Time Budgets

| System type | Cold start target | Hard ceiling |
|---|---|---|
| CLI tool | < 100ms | 500ms |
| Web server | < 2s | 10s |
| Background worker | < 5s | 30s |
| Desktop application | < 3s | 10s |

### Memory Budgets

| Component type | Baseline target | Hard ceiling |
|---|---|---|
| CLI tool | < 50MB | 200MB |
| Web request handler | < 100MB | 500MB |
| Background worker | < 256MB | 1GB |
| Data pipeline stage | < 512MB | 2GB |

### CPU Budgets

Idle CPU consumption for any service < 2%.
Sustained processing ceiling defined per deployment — default 80% of allocated.
CPU spike above 90% for > 30s triggers alert.
See observability/STANDARDS.md for alert configuration.

### Budget Enforcement

- Budgets defined at project start, recorded in project config
- CI pipeline checks performance budgets on every merge — see cicd/STANDARDS.md
- Budget violation = build warning; hard ceiling violation = build failure
- Budget changes require documented justification + team review

---

## 3. Profiling

### When to Profile

| Trigger | Action |
|---|---|
| Budget exceeded | Profile immediately — find bottleneck |
| New critical path | Baseline profile before shipping |
| Performance regression detected | Profile before/after comparison |
| Scaling to new tier (see §12) | Re-profile under projected load |
| ✗ "feels slow" without data | Get data first — instrument, then decide |

### What to Measure

| Dimension | Metric | Tool category |
|---|---|---|
| Wall time | End-to-end latency per operation | APM · distributed tracing |
| CPU time | User + system time per function | CPU profiler · flame graph |
| Memory | Peak allocation · allocation rate · live set | Heap profiler · allocation tracker |
| I/O | Read/write bytes · syscall count · wait time | I/O tracer · strace-class |
| Lock contention | Wait time on locks · lock hold duration | Concurrency profiler |
| GC pressure | GC pause time · frequency · promoted bytes | Runtime GC metrics |
| Cache | Hit rate · miss rate · eviction rate | Cache instrumentation |

### Bottleneck Identification — USE Method

For every resource (CPU, memory, disk, network, locks):

| Signal | Question |
|---|---|
| **U**tilization | What percentage of resource capacity is consumed? |
| **S**aturation | Is work queuing because the resource is full? |
| **E**rrors | Are errors occurring on this resource? |

High utilization + saturation = bottleneck.
High errors + low utilization = misconfiguration, not capacity.

### Profiling Rules

- Profile under realistic load — synthetic micro-tests hide real bottlenecks
- Profile in an environment matching production topology
- Capture both CPU-bound and I/O-bound profiles separately
- ✗ profile in debug/unoptimized builds — results not representative
- Store profile baselines alongside benchmarks (§11) for regression comparison
- Flame graphs = default visualization for CPU profiles

---

## 4. Caching Strategy

### Decision Framework — When to Cache

| Condition | Cache? |
|---|---|
| Read-heavy, write-rare data | Yes |
| Expensive computation, same inputs repeated | Yes |
| External API with rate limits | Yes — with TTL |
| Data changes every request | ✗ no |
| Data must be real-time consistent | ✗ no — use read-through only |
| Cache key space unbounded | ✗ no — bound first, then cache |

### Cache Layers

| Layer | Scope | TTL range | Eviction |
|---|---|---|---|
| L1 — In-process | Single instance, single request/session | Seconds–minutes | LRU · size-bounded |
| L2 — Shared local | Single host, all processes | Minutes–hours | LRU · TTL expiry |
| L3 — Distributed | All hosts in cluster | Minutes–days | TTL · explicit invalidation |
| L4 — CDN/edge | Geographically distributed | Hours–days | TTL · purge API |

Always start at L1. Add layers only when L1 miss rate exceeds budget.
Each layer adds complexity + consistency risk.

### Cache Invalidation Rules

| Pattern | Use when | Consistency |
|---|---|---|
| TTL expiry | Eventual consistency acceptable | Weak |
| Write-through | Write updates cache + store simultaneously | Strong |
| Write-behind | Write updates cache, async flush to store | Eventual |
| Cache-aside | Application manages cache explicitly | Application-controlled |
| Event-driven purge | Source emits change event → cache listener invalidates | Near-real-time |

### Cache Key Design

- Keys deterministic from input parameters — same input → same key always
- Include version/schema in key prefix — avoids stale data on schema changes
- ✗ user-specific data in shared cache keys without namespace isolation
- Key length bounded — hash long keys to fixed size

### Cache Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Unbounded cache | Memory leak — grows until OOM | Set max size + eviction policy |
| No TTL | Stale data served indefinitely | Always set TTL, even if long |
| Cache stampede | Many threads recompute on simultaneous expiry | Locking/coalescing on miss |
| Caching errors | Error responses cached, served repeatedly | ✗ cache error results |
| Cache as primary store | Data loss on eviction/restart | Cache is acceleration, not storage |

---

## 5. Lazy Loading

### Core Principle

Defer expensive work until the result is actually needed.
Pay initialization cost at first access, not at startup.

### Where to Apply

| Scenario | Lazy pattern |
|---|---|
| Module imports with heavy init | Lazy import — load on first use |
| Configuration from external source | Load on first read, cache result |
| Database connections | Pool initialized on first query |
| Large data structures | Build on demand, not at startup |
| Optional features | Load only if feature path is triggered |
| File/resource handles | Open on first I/O, not at construction |

### Lazy Initialization Rules

- Lazy init must be thread-safe — use language-idiomatic once/sync primitives
- Initialization failure on first access must propagate clearly — ✗ silent fallback to null
- Lazy-loaded resource must still respect startup time budgets (§2) for first-access latency
- ✗ lazy-load on the hot path if first-access penalty exceeds P99 budget — warm eagerly instead
- Document lazy behavior — callers must know first call may be slow

### Eager vs Lazy Decision

| Factor | Eager | Lazy |
|---|---|---|
| Used on every request | Eager — avoid per-request init check | |
| Used on < 20% of requests | | Lazy — avoid wasted init |
| Startup time is critical | | Lazy — defer to spread cost |
| First-request latency critical | Eager — no cold-start penalty | |
| Resource expensive to hold | | Lazy — hold only when needed |

---

## 6. Memory Management

### Allocation Awareness

- Minimize allocations in hot loops — pre-allocate, reuse buffers
- Prefer stack allocation over heap for short-lived data
- Size collections at creation when final size is known or estimable
- ✗ grow collections by appending one element at a time in tight loops

### Object Pooling

| Use pooling when | ✗ pool when |
|---|---|
| Object creation is expensive (DB connections, threads) | Object creation is cheap (primitives, small structs) |
| Objects are short-lived + high-frequency | Objects have long, variable lifetimes |
| Fixed upper bound on concurrent objects is known | Pool size cannot be reasonably bounded |

Pool rules:
- Every pool has explicit max size — see architecture/STANDARDS.md §9 resource budgets
- Idle objects reclaimed after timeout — ✗ hold unused resources indefinitely
- Borrowed objects returned to pool, never abandoned — use RAII/defer/finally patterns
- Pool exhaustion strategy explicit: block | reject | create-temporary (pick one, document)

### Buffer Reuse

- Allocate buffers once, clear and reuse across iterations
- Use ring buffers for streaming data with fixed window
- Size buffers to expected payload — ✗ default to MAX_SIZE "just in case"
- Return buffers to a pool when operation completes

### Leak Prevention

| Leak type | Prevention |
|---|---|
| Handle/connection leak | Deterministic cleanup — RAII, defer, finally, context managers |
| Event listener leak | Remove listeners when owner is destroyed |
| Closure/callback leak | ✗ capture references to long-lived objects in short-lived closures |
| Cache leak | Bounded size + TTL on every cache (§4) |
| Goroutine/task leak | Every spawned task has a cancellation path + timeout |

### Memory Profiling Triggers

- Resident set grows monotonically over time → investigate leak
- Allocation rate spikes during specific operations → profile those operations
- GC pause time exceeds 50ms → reduce allocation rate or tune GC
- Memory budget (§2) exceeded → profile peak allocation, optimize top consumers

---

## 7. I/O Optimization

### Batching

- Combine multiple small I/O operations into single batch call
- Database: batch inserts/updates instead of row-at-a-time — see database/STANDARDS.md
- Network: combine multiple API requests into batch endpoint when available
- File: buffer writes, flush at interval or threshold — ✗ flush per line/record

### Batching Thresholds

| I/O type | Min batch size | Max batch size | Flush interval |
|---|---|---|---|
| Database writes | 10 rows | 1000 rows | 5s |
| API calls | 5 requests | 100 requests | 2s |
| File writes | 4KB | 64KB | 1s |
| Log entries | 10 entries | 500 entries | 1s |

Adjust per workload — these are starting points, not absolutes.

### Streaming vs Load-All

| Choose streaming when | Choose load-all when |
|---|---|
| Data size exceeds available memory | Entire dataset fits comfortably in memory |
| Processing is sequential/single-pass | Multiple passes over data required |
| First result needed before all data arrives | All data needed before processing starts |
| Data source is continuous/unbounded | Data source is finite + small |

### Streaming Rules

- Process data as it arrives — ✗ accumulate entire stream then process
- Backpressure required — consumer controls pace, not producer
  (see architecture/STANDARDS.md §9 backpressure)
- Streaming pipeline has bounded memory regardless of input size
- Each stage in pipeline processes + forwards before reading next chunk

### Async I/O

- Default to async for network I/O — synchronous blocks thread on wait
- Use async for file I/O only when concurrent file operations needed
- ✗ mix sync and async I/O in the same code path — pick one model
- Every async operation has explicit timeout — see §10
- Async does not mean fire-and-forget — track completion, handle errors

### Connection Management

- Reuse connections — ✗ create new connection per request
- Connection pools for database, HTTP, gRPC — sized per workload
- Idle connection timeout: release unused connections after inactivity
- Connection health checks: validate before borrowing from pool
- Maximum connection lifetime: rotate connections to prevent stale state

---

## 8. Query Performance

Cross-reference: database/STANDARDS.md for schema design, migration, transaction rules.

### N+1 Prevention

N+1 = loading a list, then issuing one query per item in the list.

| Pattern | Mechanism |
|---|---|
| Eager join | Single query joins related data upfront |
| Batch loading | Collect IDs, load all related records in one query |
| DataLoader pattern | Automatic batching + caching within request scope |
| Denormalization | Store derived data alongside primary — avoids join entirely |

Rule: every list-then-lookup pattern flagged in code review.
Automated detection in CI when tooling supports it.

### Pagination

- ✗ unbounded result sets — every list query has a LIMIT
- Default page size: 20–100 items depending on payload weight
- Cursor-based pagination for large/changing datasets — ✗ OFFSET for deep pages
- OFFSET pagination acceptable for small, static datasets (< 10K rows)
- Include total count only when explicitly requested — count queries are expensive

### Index Strategy

| Query pattern | Index type |
|---|---|
| Exact match lookup | B-tree (default) |
| Range queries (dates, numbers) | B-tree |
| Full-text search | Full-text / inverted index |
| Geospatial queries | Spatial index |
| High-cardinality equality checks | Hash index (where supported) |

Index rules:
- Every WHERE clause column used in production queries has an index
- Composite indexes match query column order — leftmost prefix rule
- ✗ index every column — indexes cost write performance + storage
- Review query plans quarterly; drop unused indexes
- Covering indexes for read-heavy queries — avoid table lookups

### Query Plan Review

- Run EXPLAIN/ANALYZE on every query touching > 1K rows or joining > 2 tables
- Full table scans on tables > 10K rows = performance bug
- Nested loop joins on large tables = investigate alternatives (hash join, merge join)
- Query plan changes after schema migration → re-verify performance

---

## 9. Algorithm Selection

### Complexity Awareness

Every developer must know the time and space complexity of operations
they use. "It works" is not sufficient — "it works within budget at
expected scale" is the bar.

### Common Operation Complexity

| Operation | Acceptable | Investigate | ✗ Avoid |
|---|---|---|---|
| Collection lookup | O(1) hash · O(log n) tree | O(n) linear scan on large sets | O(n²) nested scans |
| Sorting | O(n log n) | O(n²) on small sets only | O(n²) on unbounded input |
| Search | O(log n) binary · O(1) hash | O(n) when set is small + unsorted | O(n) on large sorted sets |
| Graph traversal | O(V+E) BFS/DFS | | O(V²) adjacency matrix on sparse graphs |
| String matching | O(n+m) linear | O(nm) on short patterns | O(nm) on long text + pattern |

### Data Structure Selection

| Need | Use | ✗ Avoid |
|---|---|---|
| Fast key lookup | Hash map / hash set | Linear scan through list |
| Ordered iteration | Sorted tree / sorted array | Sort-on-every-access |
| Queue semantics | Ring buffer / deque | Array with shift-from-front |
| Priority ordering | Heap / priority queue | Sort-then-pop repeatedly |
| Membership test (approximate ok) | Bloom filter | Full set when false positives acceptable |
| Append-heavy log | Append-only list / linked list | Array with frequent resizing |

### Rules

- Choose data structure based on access pattern, not familiarity
- When in doubt, profile both options — theoretical complexity hides constant factors
- For collections < 100 elements, constant factors dominate — simpler structure often wins
- ✗ premature data structure optimization — start simple, switch when profiling demands
- Document non-obvious algorithm choices with complexity rationale in comments

---

## 10. Resource Budgets

Extends architecture/STANDARDS.md §1 principle #29 and §9 resource budgets.

### Budget Categories

| Resource | Budget defined as | Enforcement |
|---|---|---|
| Time | Max wall-clock per operation | Timeout — cancel after limit |
| Memory | Max bytes allocated per operation | Allocation tracking — reject above limit |
| Connections | Max concurrent connections per pool | Pool size cap — block or reject on exhaustion |
| File descriptors | Max open handles per process | OS-level ulimit + application tracking |
| Queue depth | Max items buffered per queue | Backpressure — block producer at limit |
| Worker count | Max concurrent workers per pool | Pool bounded — architecture/STANDARDS.md §9 |
| Disk space | Max storage per component | Rotation policy — archive or delete oldest |
| Network bandwidth | Max bytes/sec per operation class | Rate limiting at client or gateway |

### Timeout Strategy

| Operation class | Timeout | On timeout |
|---|---|---|
| Internal function call | 1–10s depending on complexity | Cancel + return error |
| Database query | 5–30s depending on query type | Cancel query + return error |
| External API call | 2–10s | Cancel + circuit breaker increment |
| Batch job (total) | Minutes–hours (defined per job) | Checkpoint + resume on restart |
| Health check | 1–3s | Mark unhealthy |

Rules:
- Every outbound call has an explicit timeout — ✗ rely on system defaults
- Timeout values derived from P99 measurements + safety margin (2–3x P99)
- Cascading timeouts: caller timeout > callee timeout — prevents orphan work
- Timeout at the outermost boundary catches all inner failures

### Rate Limiting

- Rate limits on all public API endpoints — see api/STANDARDS.md
- Internal service-to-service rate limiting when downstream has known capacity
- Rate limit responses include retry-after header/signal
- Client-side rate limiting: respect limits, implement exponential backoff

### Budget Monitoring

- All resource budgets exposed as metrics — see observability/STANDARDS.md
- Alerts at 80% utilization (warning) and 95% utilization (critical)
- Budget trending: track utilization over time to predict exhaustion
- Capacity planning uses budget metrics as input data
