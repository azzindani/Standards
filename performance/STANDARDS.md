# Performance Standards

> How systems are budgeted, measured, profiled, cached, and kept fast under load.

**ID** `performance` · **Tier** Core · **Version** 1.0
**Owns** performance budgets · percentile measurement · profiling method · caching strategy · memory + I/O optimization · algorithmic discipline · timeouts + load shedding · benchmark regression gates
**Defers to** pagination + N+1 remediation → [database](../database/STANDARDS.md) · browser metrics (LCP · INP · CLS) → [web](../web/STANDARDS.md) · load · soak · spike · chaos execution → [testing/PRESSURE.md](../testing/PRESSURE.md) · coverage + pyramid → [testing](../testing/STANDARDS.md) · alert thresholds + SLO burn-rate → [observability](../observability/STANDARDS.md) · pipeline stages → [cicd](../cicd/STANDARDS.md) · layer model + backpressure architecture → [architecture](../architecture/STANDARDS.md) · infra cost + capacity spend → [devops](../devops/STANDARDS.md)
**Load with** [architecture](../architecture/STANDARDS.md) · [observability](../observability/STANDARDS.md) · [database](../database/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Measurement](#2-measurement)
3. [Performance Budgets](#3-performance-budgets)
4. [Profiling](#4-profiling)
5. [Caching Strategy](#5-caching-strategy)
6. [Memory and Allocation](#6-memory-and-allocation)
7. [I/O and Concurrency](#7-io-and-concurrency)
8. [Query Performance Detection](#8-query-performance-detection)
9. [Algorithmic Discipline](#9-algorithmic-discipline)
10. [Resource Budgets and Load Shedding](#10-resource-budgets-and-load-shedding)
11. [Benchmarking](#11-benchmarking)
12. [Anti-Patterns](#12-anti-patterns)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. Principles

| # | Rule |
|---|---|
| 1 | Measure, ✗ guess — profiling data required before any optimization lands |
| 2 | Correctness first · clarity second · performance third |
| 3 | Optimize the hot path; leave the cold path alone until a budget breaks |
| 4 | One change per optimization cycle — isolate cause from effect |
| 5 | Every optimization costs readability — the measured gain must justify it |
| 6 | Measure end-to-end latency, ✗ component time alone |
| 7 | Performance is a feature with regression gates, ✗ an afterthought |
| 8 | ✗ speculative optimization — "it might be slow" is not evidence. Fast-and-wrong is still wrong |

### Optimization Protocol

1. Define budget for the operation (§3).
2. Measure current performance against budget.
3. Within budget → stop. ✗ optimize what is fast enough.
4. Profile to locate the bottleneck (§4).
5. Fix the single largest bottleneck.
6. Re-measure — confirm gain, check for regressions elsewhere.
7. Repeat from step 3 until budget met.

**Amdahl's Law** — optimizing a component consuming 5% of total time yields ≤ 5% improvement. Identify the dominant consumer before touching code. 90% of time in I/O → CPU micro-optimization is waste.

---

## 2. Measurement

### Percentiles, Never Averages

| Rule | Detail |
|---|---|
| ✗ average latency | Mean hides the tail; a bimodal distribution has no meaningful mean |
| Report p50 · p95 · p99 always | Three numbers minimum for every latency metric |
| p99 is the accountability metric | It is the experience of your worst-served 1% — real users, not outliers |
| p50 is the planning metric | Capacity and cost models key off median |
| p99.9 for high-fan-out systems | A request touching 100 services hits someone's p99 nearly always |
| ✗ average percentiles together | Aggregate raw distributions/histograms, ✗ per-instance p99s |
| Max is a signal, ✗ a target | Investigate max; ✗ budget against it |

### Latency vs Throughput

Latency = time for one operation. Throughput = operations/sec at saturation. They trade against each other: batching + deep queues buy throughput and pay in tail latency.

- Declare per operation class which one is primary — ✗ optimize both blindly. Interactive → latency. Batch/pipeline → throughput.
- Latency degrades non-linearly near saturation — throughput gained above ~70% utilization is paid for in the tail.
- Queue depth is latency debt: wait time = queue depth ÷ service rate.
- Measure at the boundary the user experiences, ✗ only inside the component. Durations from a monotonic clock — ✗ wall clock.
- Measurement overhead is itself budgeted — sampling profilers over exhaustive tracing on hot paths.

---

## 3. Performance Budgets

Budget = a number an operation is not allowed to exceed. Undefined budget → performance is unmanaged.

### Response Time Budgets

| Operation class | p50 | p99 | Hard ceiling |
|---|---|---|---|
| In-memory lookup | < 1 ms | < 5 ms | 10 ms |
| Local cache hit | < 5 ms | < 20 ms | 50 ms |
| Database read (indexed) | < 10 ms | < 50 ms | 200 ms |
| Database write | < 20 ms | < 100 ms | 500 ms |
| External API call | < 100 ms | < 500 ms | 2 s |
| Report / aggregation | < 500 ms | < 2 s | 10 s |
| Batch job (per item) | < 50 ms | < 200 ms | 1 s |
| Full page render | < 200 ms | < 1 s | 3 s |

Hard ceiling = timeout + circuit-breaker trip point, ✗ a target.
Browser-perceived metrics (LCP · INP · CLS) are owned by [web](../web/STANDARDS.md) — ✗ restate them here.

### Startup and Memory Budgets

| Component | Cold start | Start ceiling | Memory baseline | Memory ceiling |
|---|---|---|---|---|
| CLI tool | < 100 ms | 500 ms | < 50 MB | 200 MB |
| Web server / request handler | < 2 s | 10 s | < 100 MB | 500 MB |
| Background worker | < 5 s | 30 s | < 256 MB | 1 GB |
| Desktop application | < 3 s | 10 s | — | — |
| Data pipeline stage | — | — | < 512 MB | 2 GB |

### CPU Budget

Idle CPU per service < 2%. Sustained processing ceiling: 80% of allocated by default. Resource **alert** thresholds → [observability](../observability/STANDARDS.md); ✗ restate here.

### Enforcement in CI

| Rule | Detail |
|---|---|
| Budgets declared at project start | Recorded in repo, versioned with code — ✗ tribal knowledge |
| CI checks budgets on every merge | Budget exceeded → warning · hard ceiling exceeded → build failure. Stage placement → [cicd](../cicd/STANDARDS.md) |
| Relaxing a budget requires written justification + review | ✗ silently raise the number to make CI green |

---

## 4. Profiling

### When to Profile

| Trigger | Action |
|---|---|
| Budget exceeded | Profile immediately — find the bottleneck |
| New critical path | Baseline profile before shipping |
| Regression detected | Before/after profile comparison |
| Scale tier change (§13) | Re-profile under projected load |
| "Feels slow", no data | ✗ act — instrument first, decide second |

### What to Measure

| Dimension | Metric | Tool class |
|---|---|---|
| Wall time | End-to-end latency per operation | APM · distributed tracing |
| CPU time | User + system time per function | CPU profiler · flame graph |
| Memory | Peak allocation · allocation rate · live set | Heap profiler · allocation tracker |
| I/O | Bytes read/written · syscall count · wait time | I/O tracer |
| Lock contention | Wait time on locks · hold duration | Concurrency profiler |
| GC pressure | Pause time · frequency · promoted bytes | Runtime GC metrics |
| Cache | Hit rate · miss rate · eviction rate | Cache instrumentation |

### USE Method — per resource (CPU · memory · disk · network · locks)

| Signal | Question |
|---|---|
| **U**tilization | What percentage of capacity is consumed? |
| **S**aturation | Is work queuing because the resource is full? |
| **E**rrors | Are errors occurring on this resource? |

High utilization + saturation → bottleneck. High errors + low utilization → misconfiguration, not capacity.

### Profiling Rules

- Profile under realistic load in an environment matching production topology — synthetic micro-tests hide real bottlenecks.
- Capture CPU-bound and I/O-bound profiles separately — one masks the other.
- ✗ profile debug/unoptimized builds — results are not representative.
- Flame graphs = default visualization for CPU profiles. Store baselines with benchmarks (§11).

---

## 5. Caching Strategy

Cache = acceleration, ✗ storage. Data that exists only in cache is data already lost.

### When to Cache

| Condition | Cache? |
|---|---|
| Read-heavy, write-rare data · expensive computation with repeated inputs | Yes |
| External API with rate limits | Yes — with TTL |
| Data changes every request · strict real-time consistency required | ✗ no — read through to source |
| Key space unbounded | ✗ no — bound the key space first |

### Cache Layers

| Layer | Scope | TTL range | Eviction |
|---|---|---|---|
| L1 — in-process | One instance, one request/session | Seconds–minutes | LRU · size-bounded |
| L2 — shared local | One host, all processes | Minutes–hours | LRU · TTL |
| L3 — distributed | All hosts in cluster | Minutes–days | TTL · explicit invalidation |
| L4 — CDN / edge | Geographic | Hours–days | TTL · purge API |

Start at L1. Add a layer only when the miss rate of the layer below breaks a budget — each layer adds a consistency failure mode. HTTP cache headers · CDN rules · browser cache → [web](../web/STANDARDS.md).

### Write and Invalidation Patterns

| Pattern | Mechanism | Consistency |
|---|---|---|
| Cache-aside | Application reads cache, loads + populates on miss | Application-controlled — default choice |
| Write-through | Write updates cache + store synchronously | Strong; slower writes |
| Write-behind | Write hits cache, async flush to store | Eventual; data loss window on crash |
| TTL expiry | Entry dies on a clock | Weak — staleness bounded by TTL |
| Event-driven purge | Source emits change event → cache invalidates | Near-real-time; requires event bus |

Rules:

- Every cache entry has a TTL — ✗ unbounded lifetime, even for "immutable" data.
- Every cache has a max size + eviction policy — ✗ unbounded cache (it is a memory leak).
- ✗ cache error responses — a transient 500 must not be served for a TTL.
- Invalidation is the hard part: prefer short TTL over clever invalidation when correctness allows.

### Stampede Protection — mandatory on any cache fronting an expensive origin

| Mechanism | Effect |
|---|---|
| Single-flight / request coalescing | Concurrent misses on one key → one origin call, all callers share the result |
| Lock-on-miss | First miss takes a lock; others wait or serve stale |
| Early / probabilistic refresh | Refresh before expiry with jittered probability — entry never expires under load |
| TTL jitter | Randomize TTL ±10% — ✗ synchronized mass expiry |
| Stale-while-revalidate | Serve stale entry, refresh in background |
| Negative caching | Cache "not found" with a short TTL — bounds miss floods for absent keys |

### Cache Keys and Metrics

- Keys deterministic from inputs — same input → same key, always.
- Version/schema prefix in every key — a schema change must not read stale-shaped data.
- ✗ user-scoped data under a shared key without a namespace — cross-tenant leak.
- Bound key length — hash long keys to a fixed size.
- Track hit rate · miss rate · eviction rate · origin load **per layer**. Hit rate below budget → the cache is decoration; fix it or delete it.

---

## 6. Memory and Allocation

### Allocation Rules

- Minimize allocation in hot loops — pre-allocate, reuse buffers. Prefer stack allocation for short-lived data where the language offers the choice.
- Size collections at creation when the final size is known or estimable. ✗ grow a collection one element at a time inside a tight loop.
- Size buffers to the expected payload — ✗ default to MAX_SIZE "just in case".

### Object Pooling

| Pool when | ✗ Pool when |
|---|---|
| Creation is expensive (DB connections, threads, TLS sessions) | Creation is cheap (primitives, small structs) |
| Objects are short-lived + high-frequency | Lifetimes are long and variable |
| Concurrent count has a known upper bound | Pool size cannot be bounded |

Pool rules:

- Every pool has an explicit max size — see [architecture](../architecture/STANDARDS.md). Idle objects reclaimed after a timeout; ✗ hold unused resources indefinitely.
- Borrowed objects always returned — RAII · defer · finally · context manager.
- Exhaustion strategy declared explicitly: block | reject | create-temporary. Pick one, document it.

### Eager vs Lazy Initialization

| Factor | Choose |
|---|---|
| Used on every request | Eager — ✗ pay a per-request init check |
| Used on < 20% of requests · expensive to hold idle | Lazy — ✗ waste init cost |
| Startup budget is the binding constraint | Lazy — spread the cost |
| First-request latency is the binding constraint | Eager — ✗ put a cold-start penalty on a user |

- Lazy init must be thread-safe — language-idiomatic once/sync primitive. First-access failure propagates loudly; ✗ silent fallback to null/default.
- ✗ lazy-load on the hot path when first-access cost exceeds the p99 budget — warm eagerly instead.

### Leak Prevention

| Leak | Prevention |
|---|---|
| Handle / connection | Deterministic cleanup — RAII · defer · finally · context manager |
| Event listener | Remove listener when the owner is destroyed |
| Closure capture | ✗ capture long-lived references in short-lived closures |
| Cache | Bounded size + TTL on every cache (§5) |
| Task / thread | Every spawned task has a cancellation path + timeout |

Triggers: resident set grows monotonically → leak hunt · GC pause > 50 ms → cut allocation rate · memory budget (§3) exceeded → profile peak allocation.

---

## 7. I/O and Concurrency

### Batching Thresholds

| I/O type | Min batch | Max batch | Flush interval |
|---|---|---|---|
| Database writes | 10 rows | 1000 rows | 5 s |
| API calls | 5 requests | 100 requests | 2 s |
| File writes | 4 KB | 64 KB | 1 s |
| Log entries | 10 entries | 500 entries | 1 s |

Starting points, tuned per workload. ✗ flush per line/record. Batch flushes on size **or** interval, whichever hits first — an unflushed batch is unbounded latency.

### Streaming vs Load-All

| Stream when | Load-all when |
|---|---|
| Data exceeds available memory | Dataset fits comfortably in memory |
| Processing is single-pass | Multiple passes required |
| First result needed before all data arrives | All data needed before processing |
| Source is unbounded/continuous | Source is finite + small |

- Process as data arrives — ✗ accumulate the whole stream then process. Streaming pipeline has bounded memory regardless of input size.
- Backpressure required: the consumer sets the pace, ✗ the producer. Architecture → [architecture](../architecture/STANDARDS.md).

### Async and Connections

- Async by default for network I/O — a synchronous call blocks a thread for the whole wait. ✗ mix sync and async I/O in one code path.
- Every async operation has an explicit timeout (§10). Async ✗ fire-and-forget — track completion, handle errors.
- Reuse connections — ✗ new connection per request. Pool database · HTTP · gRPC, with health-check before borrow · idle timeout · max lifetime (rotate to shed stale state).

---

## 8. Query Performance Detection

Pagination strategy and N+1 remediation are owned by [database](../database/STANDARDS.md). This section covers **detection and profiling only** — ✗ restate keyset-vs-OFFSET rules here.

### N+1 Detection

N+1 = load a list, then issue one query per item.

| Detection method | Mechanism |
|---|---|
| Query count per request as a metric | Instrument the data layer; alert when count scales with result-set size |
| Query-count assertion in tests | Assert a fixed query count for a fixed fixture — count grows → test fails |
| Slow-query log correlation | Many identical queries differing only in a bound parameter |
| ORM/data-layer log in dev | Log every query with its calling site in development builds |
| Code review trigger | Any list-then-lookup pattern is flagged |

Query count per request has a budget like any other resource. Remediation → [database](../database/STANDARDS.md).

### Query Profiling

- Run EXPLAIN/ANALYZE on every query touching > 1K rows or joining > 2 tables. Re-verify plans after every schema migration — plans shift under new statistics.
- Full table scan on a table > 10K rows = performance bug. Unbounded result set = performance bug; every list query has a LIMIT.
- Track slow queries as a metric, ✗ an anecdote — see [observability](../observability/STANDARDS.md).

---

## 9. Algorithmic Discipline

Know the time and space complexity of what you call. "It works" is not the bar — "it works within budget at expected scale" is.

| Operation | Acceptable | Investigate | ✗ Avoid |
|---|---|---|---|
| Collection lookup | O(1) hash · O(log n) tree | O(n) scan on small sets | O(n²) nested scans |
| Sorting | O(n log n) | O(n²) on small sets only | O(n²) on unbounded input |
| Search | O(log n) binary · O(1) hash | O(n) on small unsorted sets | O(n) on large sorted sets |
| Graph traversal | O(V+E) BFS/DFS | — | O(V²) adjacency matrix on sparse graphs |
| String matching | O(n+m) | O(nm) on short patterns | O(nm) on long text + pattern |

| Need | Use | ✗ Avoid |
|---|---|---|
| Fast key lookup | Hash map / set | Linear scan of a list |
| Ordered iteration | Sorted tree / sorted array | Sort on every access |
| Queue semantics | Ring buffer / deque | Array with shift-from-front |
| Priority ordering | Heap | Sort-then-pop repeatedly |
| Membership, false positives ok | Bloom filter | Full set in memory |

Rules:

- Choose by access pattern, ✗ by familiarity. Below ~100 elements constant factors dominate — the simpler structure usually wins.
- ✗ premature data-structure optimization. Start simple; switch when profiling demands it, and profile both options.
- Document non-obvious algorithm choices with the complexity rationale.

---

## 10. Resource Budgets and Load Shedding

### Budget Categories

| Resource | Budget | Enforcement |
|---|---|---|
| Time | Max wall-clock per operation | Timeout — cancel at limit |
| Memory | Max bytes per operation | Allocation tracking — reject above limit |
| Connections | Max concurrent per pool | Pool cap — block or reject on exhaustion |
| File descriptors | Max open handles per process | OS ulimit + application tracking |
| Queue depth | Max items buffered | Backpressure — block producer at limit |
| Concurrency | Max in-flight operations | Bounded worker pool / semaphore |
| Disk | Max storage per component | Rotation — archive or delete oldest |
| Bandwidth | Max bytes/sec per operation class | Rate limit at client or gateway |

### Timeouts

| Operation class | Timeout | On expiry |
|---|---|---|
| Internal call | 1–10 s by complexity | Cancel + return error |
| Database query | 5–30 s by query type | Cancel query + return error |
| External API call | 2–10 s | Cancel + increment circuit breaker |
| Batch job (total) | Defined per job | Checkpoint + resume on restart |
| Health check | 1–3 s | Mark unhealthy |

- Every outbound call has an explicit timeout — ✗ rely on library or system defaults (often infinite). Values derive from measured p99 × 2–3, ✗ from intuition.
- Cascading rule: caller timeout > callee timeout — otherwise the callee orphans work the caller already abandoned.
- Propagate a deadline through the call chain; ✗ start downstream work for a request that has already blown its deadline.

### Backpressure and Load Shedding

| Mechanism | Rule |
|---|---|
| Bounded queues | Every queue has a max depth — an unbounded queue converts overload into OOM |
| Backpressure | At depth limit, block or reject the producer — ✗ buffer without limit |
| Load shedding | Above capacity, reject early with a retryable error — ✗ accept work you cannot finish |
| Shed by priority | Drop low-value traffic first (background, retries, non-paying tiers); protect the critical path |
| Fail fast at the edge | Reject at admission, ✗ after doing the expensive work |
| Circuit breaker | Consecutive failures/timeouts on a dependency → open the circuit, fail immediately, probe periodically |
| Rate limits | On all public endpoints — see [api](../api/STANDARDS.md). Responses carry a retry-after signal; clients respect it with exponential backoff + jitter. ✗ retry storms |

A degraded response served in time beats a perfect response served after the client gave up.

---

## 11. Benchmarking

### Reproducibility

- Dedicated, isolated environment — ✗ a shared CI runner with variable neighbors. Record hardware · OS · runtime version · configuration.
- Warm-up iterations excluded — steady state only. ≥ 30 iterations; report median, p99, standard deviation.
- Deterministic input data — same data every run, or results are not comparable.
- Results committed with the code — history enables regression detection.

### Regression Gates

| Method | Frequency | Threshold |
|---|---|---|
| CI benchmark suite | Every merge to main | > 10% regression → warn · > 20% → fail |
| Nightly extended suite | Daily | > 5% sustained over 3 days → alert |
| Pre-release comparison | Before release | Throughput drop > 10% vs baseline → block release |

### Design Rules

- Benchmark real operations, ✗ micro-operations in isolation. Data size matches production scale, or a documented fraction of it.
- Include setup/teardown only when production pays that cost too.
- ✗ benchmark debug builds. ✗ benchmark only the best case — include the worst case.
- Baseline updated after each shipped optimization — the new floor for regression detection.
- Load · soak · spike · chaos execution → [testing/PRESSURE.md](../testing/PRESSURE.md).

---

## 12. Anti-Patterns

| Anti-pattern | Problem | Fix |
|---|---|---|
| Optimizing without profiling | Effort spent on the 5% path | Profile first (§4) |
| Averaging latency | Tail invisible; users feel the tail | p50 · p95 · p99 (§2) |
| Unbounded cache | Memory leak with extra steps | Max size + eviction + TTL (§5) |
| Unbounded queue | Overload becomes OOM | Bounded queue + backpressure (§10) |
| No timeout | One slow dependency hangs the system | Explicit timeout everywhere (§10) |
| Cache as source of truth | Data lost on eviction or restart | Cache accelerates; the store persists |
| Retry without backoff | Retry storm turns a blip into an outage | Backoff + jitter + circuit breaker (§10) |
| Premature micro-optimization | Unreadable code, no measured gain | Budget → measure → optimize (§1) |
| Budget raised to make CI green | Regression laundered into policy | Justification + review (§3) |

---

## 13. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Budgets (§3) | Informal | Defined for critical paths · CI-warned | Full budget set · CI-enforced ceilings |
| Measurement (§2) | Ad-hoc timing | p50 · p99 on critical paths | p50 · p95 · p99 · p99.9, all endpoints |
| Profiling (§4) | On demand when slow | Baseline per critical path | Continuous/always-on profiling |
| Caching (§5) | In-process only if needed | L1 + L2 where measured need exists | Multi-layer · stampede protection · hit-rate SLOs |
| Memory (§6) | Language defaults | Pool connections | Full pooling · buffer reuse · leak monitoring |
| I/O (§7) | Direct I/O acceptable | Batch writes · connection reuse | Batching · streaming · async · backpressure |
| Timeouts (§10) | On external calls | All outbound calls | Deadline propagation across the chain |
| Load shedding (§10) | ✗ not needed | Circuit breakers on dependencies | Priority shedding · admission control |
| Benchmarks (§11) | Manual timing | CI benchmarks on critical paths | Full suite · regression gates · pre-release comparison |

Transition triggers: single operation over budget → profile it · traffic > 100 req/s → add caching + load tests · memory grows over time → leak hunt · multi-service topology → distributed tracing + deadline propagation.

---

## 14. Checklist

- [ ] Performance budgets defined for every critical path and committed to the repo
- [ ] Latency reported as p50 · p95 · p99 — no average-latency metric anywhere
- [ ] CI checks budgets on every merge; hard-ceiling breach fails the build
- [ ] No budget was relaxed without written justification and review
- [ ] Every optimization traces to a profile — none justified by intuition
- [ ] Profiles captured under realistic load, in optimized builds only
- [ ] USE method applied when hunting a bottleneck (utilization · saturation · errors)
- [ ] Every cache has a max size, an eviction policy, and a TTL
- [ ] Stampede protection on every cache fronting an expensive origin
- [ ] Cache keys deterministic, schema-versioned, namespaced per tenant/user
- [ ] Cache hit rate monitored per layer; error responses never cached
- [ ] No unbounded collection, queue, or buffer anywhere
- [ ] Every spawned task has a cancellation path and a timeout
- [ ] Pools have an explicit max size and a declared exhaustion policy
- [ ] I/O batched with both a size trigger and an interval trigger
- [ ] Every outbound call has an explicit timeout derived from measured p99
- [ ] Caller timeout exceeds callee timeout across the whole chain
- [ ] Backpressure at every queue; load shedding rejects early when over capacity
- [ ] Circuit breaker on every external dependency
- [ ] Query count per request measured and budgeted; N+1 caught by a test
- [ ] Every list query has a LIMIT
- [ ] Algorithm complexity appropriate for production data size
- [ ] Benchmarks reproducible: isolated environment, ≥ 30 iterations, deterministic data
- [ ] Benchmark regression gate in CI (> 10% warn · > 20% fail)
