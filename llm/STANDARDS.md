# LLM Application Standards

> Rules for software whose behavior depends on a language model — prompt artifacts, model pinning and migration, context assembly, output contracts, degradation, cost control, and call observability.

**ID** `llm` · **Tier** Domain · **Version** 1.0
**Owns** LLM application lifecycle · prompt as versioned artifact · prompt registry + rollback · model pinning + migration protocol · context assembly contract · retrieval grounding rules · structured-output contract · output validation boundary · degradation ladder (outage · refusal · truncation · rate limit) · token + cost budgets · non-determinism policy · LLM call observability
**Defers to** eval sets · graders · gate thresholds · regression detection → [llm/evaluation](EVALUATION.md) · prompt injection · untrusted content boundary · tool authorization · PII in prompts + logs → [llm/safety](SAFETY.md) · training · fine-tuning · dataset versioning · drift monitoring → [ml](../ml/STANDARDS.md) · SQL/command/XSS injection · secrets · authn/authz · PII policy → [security](../security/STANDARDS.md) · context-file structure · caveman density rules → [agent](../agent/STANDARDS.md) · test pyramid · coverage gate · mocking policy → [testing](../testing/STANDARDS.md) · quality rubric · peak comparator · failure taxonomy → [expectation](../expectation/STANDARDS.md) · log format · metric plumbing · SLOs · alert routing → [observability](../observability/STANDARDS.md) · feature flags · config cascade → [configuration](../configuration/STANDARDS.md) · latency budgets · caching mechanics → [performance](../performance/STANDARDS.md) · error taxonomy · boundaries · retry → [error_handling](../error_handling/STANDARDS.md) · endpoint contract · versioning → [api](../api/STANDARDS.md) · CI stages → [cicd](../cicd/STANDARDS.md)
**Load with** [llm/evaluation](EVALUATION.md) · [llm/safety](SAFETY.md) · [expectation](../expectation/STANDARDS.md) · [observability](../observability/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Lifecycle](#2-lifecycle)
3. [Prompts as Artifacts](#3-prompts-as-artifacts)
4. [Model Selection and Pinning](#4-model-selection-and-pinning)
5. [Context Assembly](#5-context-assembly)
6. [Retrieval Grounding](#6-retrieval-grounding)
7. [Structured Output](#7-structured-output)
8. [Output Validation](#8-output-validation)
9. [Degradation Ladder](#9-degradation-ladder)
10. [Token and Cost Budgets](#10-token-and-cost-budgets)
11. [Determinism](#11-determinism)
12. [Observability](#12-observability)
13. [Model Migration](#13-model-migration)
14. [Anti-Patterns](#14-anti-patterns)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| The prompt is source code | Versioned, reviewed, tested, released, rolled back — same discipline as any other deployed artifact |
| The model is a dependency | Pinned by exact version. A provider alias that silently re-points is an unpinned dependency |
| Output is untrusted input | Model output crossing into code, a query, a shell, a filesystem, or a browser is validated at that boundary like any external input |
| Evaluated, not eyeballed | A prompt change ships on a measured eval delta. "It looked better" is not a result |
| The model will be unavailable | Outage, rate limit, refusal, and truncation are normal operating states with defined behavior, ✗ exceptions |
| Non-determinism is bounded, ✗ eliminated | Same input may produce different output. Contracts constrain shape and invariants, ✗ exact bytes |
| Cost is a budget | Tokens are metered spend. An unbudgeted call path is an unbounded bill |

---

## 2. Lifecycle

Draft → eval baseline → change → eval delta → gate → canary → full rollout → monitor → retire.

| Phase | Gate to exit |
|---|---|
| Draft | Prompt has an ID, owner, and at least one eval case |
| Eval baseline | Scores recorded on the pinned model, committed with the prompt |
| Change | Diff is a prompt-registry diff, reviewed like code |
| Eval delta | Every gate metric ≥ baseline, or the regression is explicitly accepted in writing → [llm/evaluation §6](EVALUATION.md#6-gates) |
| Gate | Cost + latency budgets still met at the new prompt's token count |
| Canary | Percentage rollout behind a flag → [configuration](../configuration/STANDARDS.md) |
| Full rollout | Canary window clean on quality, cost, latency, refusal rate |
| Monitor | Live metrics tracked against eval expectations (§12) |
| Retire | Prompt version removed only when no traffic and no rollback target references it |

Rules:

- A prompt version reaching production without an eval baseline is a rollback with no destination.
- Canary compares against the previous prompt version on live traffic, ✗ against the eval set alone.
- Rollback is a config change to the previous prompt version — ✗ a code deploy, ✗ a re-edit of the prompt text.

---

## 3. Prompts as Artifacts

| Rule | Detail |
|---|---|
| Stored as files | Prompt text lives in the repository under version control, ✗ in a database row edited by hand, ✗ inline in a function body |
| Addressed by ID + version | Call sites reference `<prompt-id>@<version>`, never a file path or a literal |
| Immutable once released | A released version is never edited. A change produces a new version |
| One owner | Each prompt ID has a named owner responsible for its evals |
| Templated, ✗ concatenated | Variables are named slots filled by a renderer that escapes untrusted values → [llm/safety §3](SAFETY.md#3-untrusted-content-boundary) |
| Reviewed as code | Prompt diffs go through [code_review](../code_review/STANDARDS.md). A reviewer who cannot see the rendered prompt cannot approve it |
| Pinned per environment | dev · staging · production may run different prompt versions. The version in use is readable at runtime |

Prompt registry entry — required fields:

| Field | Content |
|---|---|
| `id` | Stable slug. Never reused after retirement |
| `version` | Monotonic. Bump on any text, variable, or model-parameter change |
| `model` | Exact model version this text was evaluated against (§4) |
| `parameters` | Temperature, max output tokens, stop sequences, tool set |
| `variables` | Declared slot names with types and whether each carries untrusted content |
| `output_contract` | Schema ID the output must satisfy (§7) |
| `eval_set` | Eval set ID and the baseline scores → [llm/evaluation](EVALUATION.md) |
| `token_estimate` | Rendered input tokens at the p95 variable size, and max output tokens |

A registry entry missing `eval_set` or `output_contract` is incomplete — ✗ deployable.

---

## 4. Model Selection and Pinning

| Rule | Detail |
|---|---|
| Pin the exact version | Configure the fully-qualified model version string. A floating alias re-points under you without a deploy |
| Pin per prompt | The model is part of the prompt's contract, ✗ a global |
| Record the served model | Providers fall back under load. Log the model that actually served each call, which can differ from the requested one (§12) |
| Select on measured fit | Model choice follows eval scores, cost per task, and p95 latency — ✗ benchmark leaderboards, ✗ parameter count |
| Cheapest model that passes | Route each task to the smallest model whose eval scores clear the gate. Escalate on failure, ✗ by default |
| One escalation hop | A cheap-model failure escalates to one stronger model, then falls through to the degradation ladder (§9) — ✗ unbounded chains |
| Provider abstraction is thin | Wrap the provider SDK behind a narrow interface → [dependencies §3](../dependencies/STANDARDS.md#3-wrapper-pattern). The wrapper normalizes errors, retries, token accounting, and streaming — ✗ hides parameters the caller must set |

Capability floor — a prompt declares what it requires; a model lacking any declared capability is ineligible regardless of score:

| Capability | Declared when |
|---|---|
| Context window | Rendered input at p99 variable size exceeds a smaller model's window |
| Structured output | Output contract is enforced by the provider, ✗ by post-parse (§7) |
| Tool calling | Prompt grants tools → [llm/safety §5](SAFETY.md#5-tool-authorization) |
| Multimodal input | Any variable carries image, audio, or document bytes |
| Extended reasoning | Eval shows a measured delta on the task, ✗ assumed |

---

## 5. Context Assembly

Context is assembled by explicit code with a token budget, ✗ by appending until the call succeeds.

| Rule | Detail |
|---|---|
| Budget before assembly | Each context segment has a token allocation set before any content is fetched |
| Ordered by eviction priority | System instruction · output contract · task input are never evicted. History and retrieved documents are evicted first |
| Truncate at segment boundaries | Drop whole documents or whole turns. ✗ cut a document mid-sentence and pass the fragment as if complete |
| Truncation is visible | When a segment is dropped or trimmed, the prompt states it and the call record logs it. Silent truncation produces confident answers from missing data |
| Deterministic assembly | Same inputs and same budget produce the same rendered prompt, byte for byte |
| Rendered prompt is inspectable | The exact text sent is retrievable for any call within the log retention window → [observability](../observability/STANDARDS.md) |
| Stable prefix | Invariant content sits at the front so provider prefix caching applies. Reordering a stable prefix per call forfeits the discount |
| Conversation history is bounded | A hard turn or token cap with a defined eviction or summarization policy. ✗ unbounded growth |

Summarization of evicted history is itself an LLM call: it has a prompt ID, an output contract, and evals. ✗ an untracked inline call.

---

## 6. Retrieval Grounding

| Rule | Detail |
|---|---|
| Retrieved content is untrusted | It reaches the model as data inside a delimited block, never as instruction → [llm/safety §3](SAFETY.md#3-untrusted-content-boundary) |
| Every chunk carries provenance | Source ID, version, and retrieval timestamp travel with the chunk into the prompt |
| Citations are verified | A citation the output produces is checked against the chunks actually supplied. An unresolvable citation fails validation (§8) |
| Retrieval quality is evaluated separately | Recall and precision of the retriever are measured independently of generation quality → [llm/evaluation §4](EVALUATION.md#4-component-evals) |
| Empty retrieval is a defined state | Zero relevant chunks → the prompt is told so and the contract permits "insufficient information". ✗ let the model fill the gap |
| Freshness is declared | Index build time is exposed to the caller. A stale index answering time-sensitive questions is a correctness failure, ✗ a latency one |
| Index rebuild is versioned | Embedding model, chunker, and index are versioned together. Changing any one invalidates the eval baseline |

---

## 7. Structured Output

| Rule | Detail |
|---|---|
| Schema-first | Any output a program consumes has a declared schema before the prompt is written |
| Provider enforcement preferred | Use constrained decoding or a native structured-output mode when available. Post-hoc parsing is the fallback, ✗ the default |
| Schema is the contract | The schema is versioned with the prompt and changes under [api §5](../api/STANDARDS.md#5-versioning--deprecation) rules — additive fields are compatible; removed or retyped fields are breaking |
| Closed enumerations | Every categorical field is a closed enum with an explicit "other" or "unknown" member. An open string field invites drift |
| No prose in data fields | Freeform explanation lives in its own declared field, never mixed into an identifier, number, or enum |
| Refusal is in the schema | The contract has a representable refusal or abstention state. A model with no way to say "I cannot" fabricates instead (§9) |
| Confidence is not a probability | A self-reported confidence field is a ranking signal at best. ✗ gate on it as if calibrated |
| Streaming yields partial, never invalid | A streamed structured response is validated on completion. Partial output is never committed to durable state |

---

## 8. Output Validation

Validation happens at the boundary where output leaves the LLM layer, before any consumer sees it.

| Layer | Check |
|---|---|
| Syntactic | Parses as the declared format. Malformed → retry once with the parse error, then fail (§9) |
| Schema | Validates against the versioned schema. Unknown fields rejected, required fields present |
| Semantic | Field-level invariants: ranges, referential integrity against inputs, cross-field consistency |
| Grounding | Every claimed citation resolves to a supplied chunk (§6) |
| Safety | Output-side checks → [llm/safety §6](SAFETY.md#6-output-side-controls) |
| Sink encoding | Encoded for its destination — SQL parameters, shell argv arrays, HTML escaping → [security](../security/STANDARDS.md) |

Rules:

- Validation failure is a typed error → [error_handling](../error_handling/STANDARDS.md), ✗ a silent default, ✗ a coerced best guess.
- A repair retry sends the validation error back to the model. One repair attempt, then fail. ✗ loop until valid.
- ✗ regex-scrape a value out of a response that failed schema validation.
- Model output is never interpolated into code, a query, a command line, a path, or markup without the sink's encoding applied.
- An action the output requests that exceeds the caller's own authority is refused at this boundary → [llm/safety §5](SAFETY.md#5-tool-authorization).

---

## 9. Degradation Ladder

Every LLM-dependent path declares its behavior for each state. An undeclared state degrades into a 500.

| State | Detection | Required behavior |
|---|---|---|
| Provider outage | Connection failure, 5xx | Fail over to the declared secondary model or serve the declared fallback. ✗ retry into a queue that grows unbounded |
| Rate limited | 429, quota error | Respect the retry-after header, shed load per [performance](../performance/STANDARDS.md). ✗ retry immediately |
| Timeout | Wall-clock budget exceeded | Cancel the call and release the connection. A cancelled call still costs tokens — record them (§10) |
| Refusal | Model declines the task | Surface as a distinct outcome, ✗ an error, ✗ an empty success. Track refusal rate as a quality metric |
| Truncation | Output hit the token limit | Never treated as complete. Detect via the finish reason, ✗ by inspecting whether the text "looks done" |
| Content filter | Provider blocked input or output | Distinct outcome from refusal. ✗ retry verbatim |
| Validation failure | §8 | One repair retry, then the declared fallback |
| Degraded quality | Live metrics breach eval expectations (§12) | Alert; roll back to the previous prompt version |

Rules:

- Retries are bounded, jittered, and idempotency-keyed → [error_handling](../error_handling/STANDARDS.md). ✗ retry a non-idempotent tool-calling turn blindly.
- A fallback that silently returns a lower-quality answer is labeled as degraded in the response, ✗ passed off as normal.
- The deterministic non-LLM path is the last rung where one exists — a template, a cached answer, or an honest "unavailable".

---

## 10. Token and Cost Budgets

| Rule | Detail |
|---|---|
| Every call path has a budget | Max input tokens, max output tokens, max calls per request. Declared at the call site, enforced in the wrapper |
| Enforced before the call | The rendered prompt is measured and rejected over budget. ✗ discover the overage on the bill |
| Recorded after the call | Input, output, cached, and reasoning tokens are recorded per call, per prompt ID, per model (§12) |
| Cost attributed | Every call is attributed to a tenant, feature, and prompt version. Unattributed spend is unmanageable |
| Cache deliberately | Prompt prefix caching is a design decision reflected in assembly order (§5), ✗ an accident |
| Loops are capped | Any agentic or retry loop has a hard step cap and a cumulative token cap. Hitting either is a defined terminal state (§9) |
| Budget regression is a gate | A prompt change raising p95 tokens beyond the declared budget fails the gate as surely as a quality regression |
| Batch when latency allows | Offline and scheduled work uses the provider's batch path where cost differs materially |

Token accounting reports the provider's reported usage, ✗ a local tokenizer estimate. Estimates are for pre-call budget checks only.

---

## 11. Determinism

| Rule | Detail |
|---|---|
| ✗ assume reproducibility | Identical input, temperature 0, and a pinned version still permit different output. Provider-side changes are invisible to you |
| Test invariants, ✗ strings | Assertions check schema conformance, ranges, required entities, and forbidden content — ✗ exact text equality → [testing](../testing/STANDARDS.md) |
| Temperature is declared | Set explicitly per prompt and recorded in the registry. ✗ rely on a provider default |
| Seed is recorded, ✗ trusted | Where a provider offers a seed, record it for debugging. ✗ build correctness on it |
| Unit tests do not call providers | Tests at unit tier use recorded fixtures. A live call is an integration test, tier-classified accordingly → [testing](../testing/STANDARDS.md) |
| Fixtures are refreshed on pin change | Recorded responses are re-captured when the pinned model version changes (§13), ✗ carried forward silently |
| Flaky eval ≠ flaky test | An eval case whose score varies across runs is reported with its variance and run count → [llm/evaluation §5](EVALUATION.md#5-scoring) |

---

## 12. Observability

Every LLM call emits one structured record → [observability](../observability/STANDARDS.md) owns the format.

| Field | Content |
|---|---|
| `prompt_id` · `prompt_version` | The registry entry that produced the call |
| `model_requested` · `model_served` | Both. A divergence is a provider fallback and explains a quality shift (§4) |
| `tokens` | Input · output · cached · reasoning, as reported by the provider |
| `cost` | Computed from tokens and the rate card for `model_served` |
| `latency_ms` | Total, and time to first token for streamed calls |
| `finish_reason` | Normalized: complete · truncated · refusal · filtered · error · timeout |
| `outcome` | Post-validation: ok · repaired · failed · degraded |
| `trace_id` | Links the call to the request and to any sibling calls in a loop |
| `variables_digest` | Hash of the rendered prompt, ✗ its content, where variables carry sensitive data → [llm/safety §7](SAFETY.md#7-privacy-in-prompts-and-logs) |

Metrics tracked against eval expectations:

| Metric | Alert when |
|---|---|
| Validation failure rate | Exceeds the rate observed on the eval set |
| Refusal rate | Steps beyond its canary-window band |
| Truncation rate | Any sustained rise — the prompt or the output cap is mis-sized |
| Provider fallback rate | `model_served` diverges from `model_requested` on a sustained fraction of calls |
| p95 input tokens | Approaches the context window or the declared budget (§10) |
| Cost per successful task | Rises without a corresponding prompt or model change |

Live metrics are compared to eval-set expectations continuously. An eval set whose scores no longer predict live behavior is stale → [llm/evaluation §7](EVALUATION.md#7-eval-set-maintenance).

---

## 13. Model Migration

A pinned model is deprecated by its provider on a schedule outside your control. Migration is a planned project, ✗ an emergency.

Deprecation notice → inventory → eval on candidate → diff analysis → prompt adaptation → canary → cutover → retire pin.

| Step | Rule |
|---|---|
| Inventory | Every prompt pinned to the retiring version is listed with its owner and traffic share. The registry makes this a query, ✗ a code search |
| Candidate eval | The candidate model runs the full eval set for every affected prompt, unchanged, before any prompt is edited |
| Diff analysis | Per-case score deltas, ✗ only the aggregate. An aggregate that holds while individual cases invert is a masked regression |
| Prompt adaptation | Only prompts whose eval regresses are edited. Each edit is a new prompt version with its own baseline (§3) |
| Budget recheck | Token counts, latency, and cost per task are re-measured on the candidate. A cheaper score at triple the cost is not a pass |
| Canary | Percentage rollout with the old pin still deployable. Rollback is a config change |
| Cutover | Fixtures re-recorded (§11), rate card updated, dashboards re-baselined |
| Retire | The old pin is removed only after the canary window closes clean |

Rules:

- Migration begins on notice, ✗ at the shutoff date. A provider's stated end-of-life is the deadline, ✗ the start.
- ✗ migrate and change the prompt in one step — the eval delta becomes unattributable.
- A prompt with no eval set cannot be migrated safely. It is evaluated first, or retired.
- Cross-provider migration re-checks every capability in §4's floor, ✗ only the scores.

---

## 14. Anti-Patterns

| Anti-pattern | Why it fails | Instead |
|---|---|---|
| Prompt inlined in a function | Unversioned, unreviewable, unrollbackable | Registry entry with an ID (§3) |
| Floating model alias | Silent re-point changes behavior with no deploy | Pin the exact version (§4) |
| Shipping on a vibe check | Undetected regressions on unseen cases | Eval gate → [llm/evaluation](EVALUATION.md) |
| Parsing with regex | Breaks on the first phrasing shift | Schema + provider enforcement (§7) |
| Retry until valid | Unbounded cost, masks a broken prompt | One repair retry, then fail (§8) |
| Treating refusal as an error | Loses a real signal and triggers retry storms | Distinct outcome (§9) |
| Appending until the window fits | Silent truncation of load-bearing context | Budgeted assembly (§5) |
| Exact-string test assertions | Permanently flaky | Invariant assertions (§11) |
| Concatenating retrieved text as instruction | Injection surface | Delimited untrusted block → [llm/safety §3](SAFETY.md#3-untrusted-content-boundary) |
| Self-reported confidence as a gate | Uncalibrated, correlates with fluency ✗ accuracy | Measured eval scores (§7) |
| Model output straight into a sink | Injection at the sink | Encode per destination (§8) |
| Unattributed token spend | Cost cannot be traced to a feature | Attributed call records (§10, §12) |
| Migrating at the shutoff date | No room for regressions | Migrate on notice (§13) |

---

## 15. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Prompt storage | File in repo, versioned | Registry with IDs, versions, per-environment pins | Registry with traffic-share and owner queries |
| Eval set | 10+ cases, run by hand | Gate in CI, baseline committed | Tiered sets — smoke per commit, full per release |
| Model pin | Exact version in config | Per-prompt pin, served model logged | Per-prompt routing with a cost/quality policy |
| Output contract | Schema validated post-parse | Provider-enforced structured output | Contract versioning with consumer compatibility checks |
| Degradation | Fail with a clear error | Full ladder declared (§9) | Secondary provider, cached answers, deterministic fallback |
| Cost control | Max tokens set | Per-path budgets, attributed spend | Per-tenant quotas, batch routing, cache hit-rate targets |
| Observability | Calls logged | Full call record (§12) with alerts | Live-vs-eval drift detection, per-prompt dashboards |
| Migration | Re-run evals by hand | Documented protocol (§13) | Inventory query, automated candidate eval sweep |

---

## 16. Checklist

- [ ] Every prompt is a registry entry with an ID, version, owner, and eval set
- [ ] No prompt text is inlined at a call site
- [ ] Every prompt pins an exact model version — no floating aliases
- [ ] Model choice is justified by eval scores, cost per task, and p95 latency
- [ ] Context assembly is budgeted and deterministic; truncation is visible to the model and the log
- [ ] Retrieved content carries provenance and enters as delimited data, never as instruction
- [ ] Every program-consumed output has a versioned schema with a representable refusal state
- [ ] Output is validated syntactically, schematically, semantically, and at its sink before any consumer sees it
- [ ] At most one repair retry per call; no retry-until-valid loops
- [ ] Every state in the degradation ladder has declared behavior: outage · rate limit · timeout · refusal · truncation · filter · validation failure
- [ ] Every call path declares token, output, and call-count budgets, enforced before the call
- [ ] Token usage and cost are recorded per call and attributed to tenant, feature, and prompt version
- [ ] Tests assert invariants, not exact strings; unit-tier tests use recorded fixtures
- [ ] Every call emits a record carrying prompt version, requested and served model, tokens, finish reason, and outcome
- [ ] Live metrics are compared against eval-set expectations, with alerts on drift
- [ ] Every pinned model has a named migration owner, and migration starts on deprecation notice
- [ ] Rollback to the previous prompt version is a config change, not a deploy
