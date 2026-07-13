# Machine Learning Standards

> Rules for the ML lifecycle — data versioning, experiment tracking, training, evaluation, registry, deployment, drift monitoring, and reproducibility.

**ID** `ml` · **Tier** Domain · **Version** 1.0
**Owns** ML lifecycle gates · dataset versioning + lineage · leakage prevention · split strategy · experiment tracking · training discipline · evaluation + baselines · explainability · model registry + promotion · serving + rollout · drift monitoring + retraining triggers · reproducibility · fairness audit + model cards
**Defers to** ingestion · ETL · batch orchestration · pipeline schema enforcement · dead-letter queues · backfill → [data_pipeline](../data_pipeline/STANDARDS.md) · test pyramid · coverage → [testing](../testing/STANDARDS.md) · error taxonomy · boundaries · retry → [error_handling](../error_handling/STANDARDS.md) · log format · metric plumbing · traces · alert routing → [observability](../observability/STANDARDS.md) · table schema · migrations → [database](../database/STANDARDS.md) · CI stages → [cicd](../cicd/STANDARDS.md) · secrets · access control · PII policy → [security](../security/STANDARDS.md) · endpoint contract · versioning → [api](../api/STANDARDS.md) · profiling · latency budgets → [performance](../performance/STANDARDS.md)
**Load with** [data_pipeline](../data_pipeline/STANDARDS.md) · [testing](../testing/STANDARDS.md) · [observability](../observability/STANDARDS.md)

---

## Table of Contents

1. [Principles](#1-principles)
2. [Lifecycle](#2-lifecycle)
3. [Data Versioning](#3-data-versioning)
4. [Data Preparation](#4-data-preparation)
5. [Experiment Tracking](#5-experiment-tracking)
6. [Training](#6-training)
7. [Evaluation](#7-evaluation)
8. [Explainability](#8-explainability)
9. [Model Registry](#9-model-registry)
10. [Deployment](#10-deployment)
11. [Monitoring and Retraining](#11-monitoring-and-retraining)
12. [Reproducibility](#12-reproducibility)
13. [Privacy and Fairness](#13-privacy-and-fairness)
14. [Anti-Patterns](#14-anti-patterns)
15. [Scale Matrix](#15-scale-matrix)
16. [Checklist](#16-checklist)

---

## 1. Principles

| Principle | Rule |
|---|---|
| Data is code | Datasets are immutable, versioned, hashed artifacts. A model without a data version is unreproducible |
| Every run is tracked | An untracked training run did not happen — its result may not be used |
| The test set is spent once | Every look at holdout leaks information into model selection |
| Reproducible from metadata alone | Code version + data version + config + environment → the same model, on another machine |
| Leakage is the default failure | Assume leakage until an audit proves otherwise (§4) |
| A model is a liability until monitored | Deployment without drift detection ships a silently decaying system |
| Gates are binary | A gate passes or fails. "Proceed with caution" is a failed gate |

Boundary with [data_pipeline](../data_pipeline/STANDARDS.md): pipelines own ingestion, batch orchestration, schema enforcement, and dead-letter handling. ML owns dataset versioning, experiments, registry, and drift. A feature pipeline is a pipeline — it follows that standard, and its output is a versioned dataset under §3.

---

## 2. Lifecycle

Six stages. Each produces an artifact the next consumes. ✗ skip a stage.

| Stage | Output | Gate before advancing |
|---|---|---|
| Data collection | Raw dataset | Schema declared · source documented · volume sufficient |
| Data preparation | Feature matrix + splits | Leakage audit passed · distributions validated · splits reproducible |
| Training | Model artifact | Converged · resource budget met · experiment logged |
| Evaluation | Metrics report | Beats baseline · holdout metrics ≥ threshold · fairness check passed |
| Deployment | Serving endpoint or artifact | Serialization validated · latency budget met · rollback tested |
| Monitoring | Drift + performance reports | Drift thresholds set · alerts routed · retraining trigger defined |

Every stage records who ran it · when · input hash · output hash · parameters. A failed gate returns to the previous stage — ✗ proceed with a caveat.

---

## 3. Data Versioning

Datasets are immutable versioned artifacts, tracked with a data-versioning system (DVC · lakeFS · Delta/Iceberg tables · equivalent) — ✗ a shared folder of dated files.

| Rule | Detail |
|---|---|
| Unique version id | Content hash (SHA-256) of the data, or a monotonic version bound to a content hash |
| Raw data immutable | ✗ modify raw data in place — every change creates a new version |
| Derived = input + transform | Input version + transform code commit → deterministic output version |
| Schema change bumps major | Added column = minor; removed or renamed column = major |
| Lineage stored with the data | Parent version(s) · transform applied · code commit — ✗ in a separate system that can drift |
| ≤ 3 hops to raw | Every derived dataset traces back to a raw source within three hops |
| External sources snapshotted | Record source URI · retrieval timestamp · hash at retrieval. ✗ train against a live remote source |

Minimum metadata per version: `version_id` · `created_at` · `row_count` · `column_schema` · `description of the change` · parent versions (if derived) · transform commit (if derived) · split ratios (if split).

---

## 4. Data Preparation

! Leakage is the highest-frequency, highest-cost ML defect. It is invisible in offline metrics and fatal in production.

| Leakage type | Rule |
|---|---|
| Target leakage | ✗ features derived from the target or any proxy of it |
| Temporal leakage | train timestamps < validation timestamps < test timestamps. ✗ random split on time-dependent data |
| Group leakage | An entity (user · session · patient · device) appears in exactly one split |
| Preprocessing leakage | Fit scalers, encoders, and imputers on **train only**; transform val/test with train-fitted parameters |
| Feature-store leakage | Point-in-time joins only — ✗ join a value that did not exist at the row's timestamp |
| Duplicate leakage | Deduplicate **before** splitting — a duplicate straddling splits inflates every metric |

### Splits

| Data type | Method | Minimum test size |
|---|---|---|
| Tabular i.i.d. | Stratified random | 20% or 10K rows, whichever is larger |
| Time-series | Temporal cutoff | Most recent 20% by time |
| Grouped | Group-aware split | 20% of groups |
| Imbalanced classes | Stratified, class ratios preserved | 20% with the ratio preserved |
| Small (< 1K rows) | K-fold cross-validation, k ≥ 5 | Full dataset via folds |

Splits are reproducible from a seed + the dataset version. ✗ re-split on every run.

### Features

- Every feature documents name · type · derivation · null strategy (impute median/mode/model · drop · sentinel) · encoding strategy.
- Feature computation is deterministic and version-controlled. ✗ one-off notebook transforms feeding a production model.
- Feature selection records the method used, the features removed, and why.
- Training-time and serving-time feature computation come from **one** implementation. Two implementations = training/serving skew.

---

## 5. Experiment Tracking

Every training run is one tracked experiment record, in a tracking system (MLflow · Weights & Biases · equivalent). ✗ untracked runs. ✗ results from a notebook cell that was not logged.

| Category | Required fields |
|---|---|
| Identity | Experiment id · run id · timestamp · author |
| Data | Dataset version + hash · split ratios · feature set version |
| Parameters | Every hyperparameter · architecture · framework version |
| Metrics | All evaluation metrics · training and validation curves per checkpoint |
| Artifacts | Model file path + hash · plots · confusion matrix · feature importance |
| Environment | Hardware · OS · seeds · dependency lock hash · container/image id |
| Outcome | Status (success · failed · killed) · wall-clock · peak memory |

| Rule | Detail |
|---|---|
| Log before, not after | Parameters logged at run start — a crashed run must still show what it tried |
| Append-only | ✗ overwrite or delete an experiment record, including failed runs |
| Failures are records | A failed run is logged with its failure reason — it is evidence |
| Comparable | Every run queryable and sortable by any metric or parameter |
| Two comparisons minimum | Each candidate is compared against (1) the baseline and (2) the current best |

---

## 6. Training

### Hyperparameters

- All hyperparameters live in a versioned config file. ✗ hardcoded in the training script.
- Search strategy declared: grid · random · Bayesian · manual.
- Search budget declared **before** the search starts: max trials · max wall-clock · max compute cost.

| Strategy | Use when | Budget |
|---|---|---|
| Grid | ≤ 3 params, ≤ 5 values each | Exhaustive — budget = grid size |
| Random | > 3 params or continuous ranges | ≥ 50 trials, or 2× the grid equivalent |
| Bayesian | Expensive-to-evaluate models | ≥ 20 trials; the surrogate is logged |
| Manual | Expert tuning atop an automated search | Each trial logged as an experiment |

### Discipline

| Rule | Detail |
|---|---|
| Early stopping | Required for iterative models: metric · patience · best checkpoint restored |
| LR schedule | Declared: constant · step · cosine · warmup+decay |
| Gradient clipping | Enabled for deep models; max norm recorded |
| Batch size | Justified — memory-bound → largest that fits; convergence-bound → validated by ablation |
| Checkpoints | At a configured interval; keep at minimum best + last; prune the rest by metric |
| Resumable | Training resumes from a checkpoint, ✗ restarts from scratch |
| Resource budgets | Peak GPU memory ≤ 90% of available · max wall-clock declared before start · peak RAM logged. OOM = failed run, ✗ silent degradation |

### Cross-validation

K-fold with k ≥ 5 when the dataset is < 10K rows · stratified folds for classification · group-aware folds when entities repeat · report mean ± std across folds. ✗ report the best single fold.

---

## 7. Evaluation

### Metrics by task

| Task | Primary | Required secondary |
|---|---|---|
| Binary classification | F1 or AUC-ROC (domain-chosen) | Precision · recall · AUC-PR · accuracy |
| Multi-class | Macro F1 | Per-class F1 · confusion matrix · weighted F1 |
| Regression | RMSE or MAE (domain-chosen) | R² · MAPE · residual distribution |
| Ranking | NDCG@K | MAP@K · MRR · precision@K |
| Clustering | Silhouette | Calinski-Harabasz · Davies-Bouldin · cluster size distribution |
| Forecasting | MASE or sMAPE | RMSE · directional accuracy · interval coverage if probabilistic |
| Anomaly detection | AUC-PR | Precision@K · recall@K · false-positive rate |
| Generative / NLP | Task metric (BLEU · ROUGE · pass@k) | Human evaluation score · held-out eval-set score |

Primary metric and its pass threshold are declared **before** evaluation. ✗ pick the metric that made the model look good.

### Baselines and rigor

| Rule | Detail |
|---|---|
| Baseline required | Every model beats at least one: naive (mean · majority class · random) · the current production model · a simple model (linear/tree on the same features) |
| ! Holdout used once | Test set is evaluated **once** per candidate. Tuning happens on validation. Repeated test evaluation = selection on the test set |
| Eval set held out | The evaluation set is versioned, frozen, and never trained on — including for generative systems and prompt/judge tuning |
| Per-segment metrics | Metrics computed on the full test set **and** per segment: demographic · temporal · geographic · volume tier |
| Significance | Metric differences < 5% require a confidence interval or a significance test before declaring a winner |
| Artifacts stored | Confusion matrix · ROC/PR curve · calibration plot · residual plot, as applicable |

---

## 8. Explainability

| Risk level | Examples | Required |
|---|---|---|
| Low | Recommendation · content ranking | Global feature importance |
| Medium | Pricing · fraud scoring | Global + local explanations for flagged cases |
| High | Credit · medical · hiring · housing | Global + local + counterfactual + fairness audit (§13) |

| Method | Scope | Use when |
|---|---|---|
| Built-in importance | Global | Tree models; fast first pass |
| Permutation importance | Global | Any model; model-agnostic cross-check |
| SHAP | Global + local | Default for detailed explanation |
| LIME | Local | SHAP too expensive |
| Partial dependence | Global | Feature–target relationship shape |
| Counterfactual | Local | High-risk decisions requiring "what would change this" |

| Rule | Detail |
|---|---|
| Always global | Global feature importance is generated for every production model, at every risk level |
| Top-K documented | Top 10 features (or all, if fewer) with importance scores |
| ! Dominance check | One feature contributing > 50% of total importance → investigate for leakage or a protected-attribute proxy before promotion |
| High-risk local storage | Local explanations stored per prediction for high-risk models |
| Validated | Perturbing a top feature must change the prediction in the expected direction |
| ✗ post-hoc justification | Explanations are generated before the decision is acted on, ✗ assembled afterward to defend it |

---

## 9. Model Registry

Central catalog: what exists · what is deployed · what is retired. ✗ deploy a model that is not in the registry.

| Field | Required | Content |
|---|---|---|
| `model_id` · `model_version` | Yes | Unique id + version |
| `experiment_id` | Yes | Link to the run that produced it |
| `dataset_version` | Yes | Training data version + hash |
| `framework` | Yes | Framework + version |
| `artifact_path` · `artifact_hash` | Yes | Location + SHA-256 of the serialized model |
| `metrics` | Yes | Primary + secondary metrics on holdout |
| `stage` | Yes | development · staging · production · retired |
| `created_at` · `created_by` | Yes | Timestamp + author or pipeline id |
| `code_commit` | Yes | Commit of training **and** inference code |
| `serving_config` | Staging+ | Input schema · output schema · latency SLA |
| `model_card` | Production | See §13 |

Promotion path: `development → staging → production → retired`. Off-ramps: any stage → `rejected` (gate failure, reason logged); `production → rolled back` (degradation detected → previous version restored).

| Transition | Gate |
|---|---|
| development → staging | Evaluation gate passed (§7) · explainability generated (§8) |
| staging → production | Integration tests pass · latency SLA met · A/B or shadow result (if required) · fairness audit passed (§13) · human approval recorded |
| production → retired | Replacement promoted · traffic drained · artifact archived |

| Rule | Detail |
|---|---|
| ✗ delete entries | Retired models are archived, never removed — audits reach back years |
| One per stage | One model version per (model_id, stage); promoting a new version auto-retires the previous |
| Queryable | By model_id · stage · metric threshold · date range · dataset version |

---

## 10. Deployment

### Serialization

| Format | Use | Interop |
|---|---|---|
| ONNX | Cross-framework serving · edge | High |
| Framework-native | Same-framework serving | Low — framework-locked |
| Custom export (coefficients, rules) | Simple models · embedded systems | High — no runtime dependency |

| Rule | Detail |
|---|---|
| Code pinned with the artifact | Model file + inference code version travel together. A model without its inference code is not deployable |
| Load-test before promoting | Deserialize → run a sample prediction → compare against the expected output recorded at training |
| Schema embedded | Input and output schema stored with the artifact |
| ! ✗ pickle for untrusted models | Deserializing an untrusted pickle executes arbitrary code → ONNX or a safe format. See [security](../security/STANDARDS.md) |

### Serving and rollout

| Pattern | Use when |
|---|---|
| Batch prediction | High volume · latency-tolerant · predictions cacheable |
| Real-time endpoint | Per-request prediction · low latency |
| Embedded | Edge/mobile · ultra-low latency · no network |
| Streaming | Continuous events · near-real-time |

| Rule | Detail |
|---|---|
| Rollback ready | Previous version identified and the switch **tested**, before the new version takes traffic |
| Progressive | Shadow or canary first; a small traffic percentage, then ramp |
| Validate at the boundary | Schema → type → range check on every request; reject invalid input, ✗ impute silently |
| Latency budget | p50 · p95 · p99 declared and **measured**, ✗ estimated |
| Warm-up | Model loaded and a dummy prediction run before the instance accepts traffic |
| Degrade gracefully | Model failure → previous model or a rule-based default, ✗ a 500 to the user |

A/B test: control = current production model. Sample size from a power analysis **before** launch. Primary metric and success criterion fixed before launch — ✗ change them mid-test. Minimum duration: one week or one full business cycle, whichever is longer. Significance required before declaring a winner.

---

## 11. Monitoring and Retraining

Log format, metric plumbing, tracing, and alert routing → [observability](../observability/STANDARDS.md). This section names the **model-specific signals** that must exist.

| Signal | Measure | Alert threshold |
|---|---|---|
| Data drift | Feature distribution shift (PSI · KS · Jensen-Shannon) vs the training distribution | PSI > 0.2 on any feature, or > 0.1 on ≥ 3 features simultaneously |
| Concept drift | Prediction distribution shift · actual-vs-predicted divergence | Prediction mean shifts > 2σ from the training baseline |
| Model performance | Primary metric on labeled feedback | Degrades > 5% from the deployment baseline |
| Input quality | Null rate · out-of-range rate · schema violations | Any metric > 2× the training-time baseline |
| Output quality | Confidence distribution · extreme-value rate | > 10% of predictions below the confidence threshold |
| Serving health | Latency p50/p95/p99 · error rate · throughput | p99 > 2× SLA · error rate > 1% |
| Prediction log | Input hash · prediction · model version · timestamp | Missing = the incident is undiagnosable |

| Rule | Detail |
|---|---|
| Cadence | Drift computed per batch (batch serving) or every N minutes (real-time), N ≤ 60 |
| Reference distribution | The training distribution, recomputed at every retrain |
| Every prediction attributable | Prediction logs carry the model version that produced them |
| Runbook per alert | Who investigates · diagnostic steps · escalation path |

### Retraining triggers

| Trigger | Action |
|---|---|
| Drift above threshold for > 24 h | Start the retraining pipeline on fresh data |
| Performance degrades > 5% on labeled data | Retrain. Degrades > 15% → ! roll back immediately, then retrain |
| Scheduled cadence | Retrain on the declared calendar regardless of drift |
| New labeled data > 20% of the training set | Retrain |
| Upstream feature change | Assess impact; retrain if an affected feature is in the top-K importance |

Retraining runs the **full** lifecycle (§2) and re-passes every gate — ✗ hot-swap a retrained model. Automated retraining still requires a human approval gate before production. A minimum interval between retrains prevents thrashing.

---

## 12. Reproducibility

Every result is reproducible from recorded metadata alone.

| Component | Rule |
|---|---|
| Global seed | Set once at the pipeline entry point; recorded in the experiment |
| Framework seeds | Set explicitly per framework — a global seed does not reach every RNG |
| Shuffling · initialization · augmentation | Seed-controlled, ✗ unseeded default random calls |
| Data | Referenced by version + content hash. ✗ download from a mutable source at training time — snapshot, version, then train |
| Environment | Dependency lock file (✗ version ranges) · pinned language, framework, and accelerator runtime versions · container image or environment hash recorded per run |
| Config | Versioned alongside code; the exact config recorded in the run |
| Non-determinism | Hardware sources (GPU atomics, autotuning kernels) documented; autotuning disabled when strict reproducibility is required |
| Tolerance | If bit-exactness is impossible, the tolerance is stated: "metrics reproducible within ±0.2%" |

✗ any dependence on wall-clock, hostname, or process id in a computation affecting model output.
✗ "works on my machine" — the run must reproduce in a clean environment from the recorded metadata.

---

## 13. Privacy and Fairness

### PII and anonymization

| Technique | Use when | Limitation |
|---|---|---|
| Pseudonymization | Re-linking needed later | Reversible if the key leaks |
| K-anonymity | Publishing aggregates | Vulnerable to background-knowledge attacks |
| Differential privacy | Training on sensitive data | Costs accuracy; the privacy budget is finite and spends down |
| Synthetic data | Real data unusable | Must be validated as distributionally close to real |
| Masking | Display and logging only | ✗ for training — destroys signal |

| Rule | Detail |
|---|---|
| PII out before the pipeline | Removed or pseudonymized at ingestion, ✗ at training time. ✗ PII in the feature matrix |
| Method recorded | Anonymization technique + parameters stored in the dataset version metadata |
| Re-identification risk | k < 5 under k-anonymity is insufficient |
| Prediction logs | Subject to the same PII policy as training data → [security](../security/STANDARDS.md) |

### Fairness audit

Required before every staging → production promotion (§9). Protected attributes identified per domain and jurisdiction. Method: evaluate model metrics per protected group independently.

| Metric | Test | Threshold |
|---|---|---|
| Demographic parity | Positive rate across groups | Ratio within [0.8, 1.25] |
| Equal opportunity | True-positive rate across groups | Ratio within [0.8, 1.25] |
| Predictive parity | Precision across groups | Ratio within [0.8, 1.25] |
| Calibration | Predicted probability vs observed rate per group | Max deviation < 0.05 |

Metric choice is domain-dependent and documented — ✗ apply one fairness metric universally; they are mutually incompatible in general. Bias found → investigate the data root cause → mitigate (resample · reweight · constrain) → re-audit. ! ✗ ship a model that fails its fairness audit without a documented exception approved by an accountable human.

### Model card

Every production model has one, versioned with the model: model details (type · version · framework · date · owner) · intended use and out-of-scope uses · training data (version · size · collection method · known limitations) · evaluation (holdout metrics · per-segment performance · baseline comparison) · fairness (groups evaluated · metrics · known disparities) · limitations (failure modes · data gaps) · recommendations (deployment constraints · required monitoring · update cadence).

---

## 14. Anti-Patterns

| Anti-pattern | Failure | Fix |
|---|---|---|
| Random split on time-series | Metrics look excellent; production collapses | Temporal cutoff (§4) |
| Scaler fit on the full dataset | Test statistics leak into training | Fit on train only (§4) |
| Repeated evaluation on the test set | The test set becomes a validation set; reported metrics are fiction | Use it once per candidate (§7) |
| Notebook result promoted | Unreproducible, untracked, unattributable | Tracked experiment (§5) |
| Data pulled live at training time | The dataset changes under the model | Snapshot → version → train (§3, §12) |
| Random UUID as a record id | Dedup and lineage impossible | Content hash / business key (§3) |
| Two feature implementations | Training/serving skew; offline metrics do not hold | One implementation (§4) |
| Model deployed without a registry entry | Nobody can say what is running | Registry-gated deploy (§9) |
| Unpickling a third-party model | Arbitrary code execution | ONNX or a safe format (§10) |
| No prediction log | Incidents undiagnosable after the fact | Log input hash · prediction · model version (§11) |
| Drift monitoring deferred to "later" | Silent decay found by a customer | Configure before promotion (§2, §11) |
| Retrained model hot-swapped | Untested model in production | Full lifecycle, all gates (§11) |
| One fairness metric for all domains | False assurance | Domain-chosen and documented (§13) |

---

## 15. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Data versioning | Hashed snapshot + notes | Data-versioning tool + full lineage | Lineage + automated dataset promotion |
| Experiment tracking | Local tracking server | Central tracking, comparison UI, retention policy | Central tracking + lineage from run to serving |
| Splits | Reproducible seeded split | Leakage tests in CI | Leakage tests + temporal + group validation in CI |
| Evaluation | Primary metric + baseline | Full suite + per-segment + significance | Automated eval gates blocking promotion |
| Registry | Registry with stages | Registry with promotion gates + approval | Multi-model governance + audit trail |
| Deployment | Manual promotion | CI/CD + canary + tested rollback | Automated canary analysis + auto-rollback |
| Monitoring | Scheduled drift report | Real-time drift + performance + alerts | Automated retraining pipeline with human gate |
| Fairness | Documented awareness | Full audit before production | Audit + continuous per-segment monitoring |

Prototype → Production is triggered when the model influences any business decision or user-facing output — ✗ by team preference.

---

## 16. Checklist

- [ ] Every lifecycle stage produced its artifact; no stage skipped
- [ ] Dataset versioned with a content hash and lineage back to raw in ≤ 3 hops
- [ ] Raw data never modified in place; external sources snapshotted with retrieval hash
- [ ] Leakage audit passed: target · temporal · group · preprocessing · feature-store · duplicate
- [ ] Preprocessing fitted on train only, applied to val/test with train parameters
- [ ] Splits reproducible from seed + dataset version
- [ ] Training-time and serving-time features come from one implementation
- [ ] Every training run tracked with data version, params, metrics, environment, and seeds
- [ ] Failed runs logged, never deleted; records append-only
- [ ] Hyperparameters in a versioned config; search strategy and budget declared up front
- [ ] Early stopping, checkpointing, and resume configured; resource budgets enforced
- [ ] Primary metric and pass threshold declared before evaluation
- [ ] Model beats a documented baseline
- [ ] Holdout evaluated exactly once per candidate; eval set frozen and never trained on
- [ ] Per-segment metrics computed; sub-5% differences backed by a significance test
- [ ] Global feature importance generated; single-feature dominance > 50% investigated
- [ ] Explainability level matches the risk level
- [ ] Model in the registry with artifact hash, dataset version, code commit, and metrics
- [ ] Serialization validated by load → predict → compare
- [ ] Latency p50/p95/p99 measured against the declared budget
- [ ] Rollback path identified and tested before traffic shifts
- [ ] Canary or shadow completed before full rollout
- [ ] Input validated at the serving boundary; failure degrades gracefully
- [ ] Drift, performance, input-quality, and prediction logs configured before promotion
- [ ] Retraining triggers defined; retraining re-passes every gate with human approval
- [ ] Seeds set globally and per framework; dependencies locked; environment hash recorded
- [ ] Run reproduces in a clean environment from recorded metadata alone
- [ ] PII removed or pseudonymized before the pipeline; never in the feature matrix
- [ ] Fairness audit passed with a domain-justified metric before production
- [ ] Model card written and versioned with the model
