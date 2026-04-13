# Machine Learning Standards

Rules governing ML lifecycle from data collection through production monitoring.
Language-agnostic — applies to any ML framework or runtime.

Derived from: MLOps maturity models, Google ML best practices, Netflix Metaflow
patterns, Uber Michelangelo architecture, DVC/MLflow design principles, CRISP-DM,
model cards framework, and fairness-aware ML research.

Composable with: `data_pipeline/STANDARDS.md` · `testing/STANDARDS.md` ·
`observability/STANDARDS.md` · `architecture/STANDARDS.md`

---

## Table of Contents

1. [ML Lifecycle](#1-ml-lifecycle)
2. [Data Versioning](#2-data-versioning)
3. [Data Preparation](#3-data-preparation)
4. [Experiment Tracking](#4-experiment-tracking)
5. [Model Training](#5-model-training)
6. [Model Evaluation](#6-model-evaluation)
7. [Model Explainability](#7-model-explainability)
8. [Model Registry](#8-model-registry)
9. [Model Deployment](#9-model-deployment)
10. [Monitoring](#10-monitoring)
11. [Reproducibility](#11-reproducibility)
12. [Privacy & Ethics](#12-privacy--ethics)
13. [Scale Matrix](#13-scale-matrix)
14. [Checklist](#14-checklist)

---

## 1. ML Lifecycle

Every ML project follows six stages. Each stage has gate criteria before advancing.

| Stage | Input | Output | Gate Criteria |
|---|---|---|---|
| Data Collection | Problem definition | Raw dataset | Schema defined · source documented · volume sufficient |
| Data Preparation | Raw dataset | Feature matrix + splits | Leakage audit passed · distributions validated · splits reproducible |
| Training | Feature matrix | Trained model artifact | Converged · resource budget met · experiment logged |
| Evaluation | Model artifact + holdout | Metrics report | Beats baseline · holdout metrics within threshold · bias check passed |
| Deployment | Approved model | Serving endpoint/artifact | Serialization validated · latency budget met · rollback plan documented |
| Monitoring | Live predictions | Drift/performance reports | Drift thresholds defined · alerting configured · retraining trigger set |

### Stage Rules

- ✗ Skip stages. Every stage produces artifacts consumed by next stage.
- Gate criteria are pass/fail — partial passes ✗ qualify.
- Each stage records: who ran it · when · input hash · output hash · parameters.
- Failed gates → return to previous stage, not "proceed with caution."
- See `architecture/STANDARDS.md` §1 (principle 25): data flows one direction through pipeline.

---

## 2. Data Versioning

Datasets are immutable versioned artifacts. Treat data with same rigor as code.

### Version Rules

| Rule | Detail |
|---|---|
| Every dataset has unique version identifier | Content-hash based (SHA-256 of contents) or monotonic version number |
| Raw data is immutable | ✗ modify raw data in place — create new version |
| Transformations produce new versioned datasets | Input version + transform code version → output version |
| Schema changes increment major version | Additive column = minor; removed/renamed column = major |
| Storage tracks lineage | Each dataset version records: parent version(s) · transform applied · code commit |

### Lineage Requirements

- Every derived dataset traces back to raw source in ≤3 hops.
- Lineage graph stored as metadata alongside dataset, not in separate system.
- If source data is external, record: source URL/API · access timestamp · hash at retrieval.
- See `data_pipeline/STANDARDS.md` for ETL pipeline standards.

### Minimum Metadata Per Dataset Version

| Field | Required | Example |
|---|---|---|
| `version_id` | Yes | `v3` or content hash |
| `created_at` | Yes | ISO-8601 timestamp |
| `row_count` | Yes | 1,234,567 |
| `column_schema` | Yes | Column names + types |
| `parent_versions` | If derived | `[raw_v2, features_v1]` |
| `transform_commit` | If derived | Git SHA of transform code |
| `description` | Yes | What changed from prior version |
| `split_ratios` | If split | `train:0.8 / val:0.1 / test:0.1` |

---

## 3. Data Preparation

Feature engineering and split management. Primary risk: data leakage.

### Leakage Prevention Rules

| Leakage Type | Rule |
|---|---|
| Target leakage | ✗ Features derived from target variable or its proxies |
| Temporal leakage | Train set timestamp < validation timestamp < test timestamp ; ✗ random split on time-series |
| Group leakage | Same entity (user, session, patient) appears in only one split |
| Preprocessing leakage | Fit scalers/encoders on train split only → transform val/test with train-fitted parameters |
| Feature store leakage | Point-in-time joins only — ✗ join future data to past records |

### Split Strategy

| Data Type | Split Method | Minimum Test Size |
|---|---|---|
| Tabular i.i.d. | Stratified random | 20% or 10K rows (whichever larger) |
| Time-series | Temporal cutoff | Most recent 20% by time |
| Grouped (user/session) | Group-aware split | 20% of groups |
| Small dataset (<1K rows) | K-fold cross-validation (k≥5) | Full dataset via folds |
| Imbalanced classes | Stratified split preserving class ratios | 20% with ratio preserved |

### Feature Engineering Rules

- Every feature has documented definition: name · type · derivation logic · null handling.
- Feature computation is deterministic — same input → same output.
- ✗ Manual one-off feature transforms. All transforms in version-controlled pipeline code.
- Categorical encoding strategy declared per column, not ad-hoc.
- Missing value strategy declared per column: impute (median/mode/model) | drop | sentinel.
- Feature selection documented: method used (correlation, mutual info, model-based) · features removed · reason.

---

## 4. Experiment Tracking

Every training run = one experiment record. No untracked runs.

### Required Fields Per Experiment

| Category | Fields |
|---|---|
| Identity | Experiment ID · run ID · timestamp · author |
| Data | Dataset version · split ratios · feature set version |
| Parameters | All hyperparameters · model architecture name · framework version |
| Metrics | All evaluation metrics · training loss curve · validation loss curve |
| Artifacts | Model file path/hash · plots · confusion matrix · feature importance |
| Environment | Hardware (GPU/CPU) · OS · random seeds · dependency versions |
| Outcome | Status (success/failed/killed) · wall-clock time · peak memory |

### Experiment Rules

- Parameters logged before training starts, not after.
- Metrics logged at each checkpoint, not only at end.
- ✗ Overwrite previous experiment records. Append-only log.
- Failed runs logged with failure reason — ✗ delete failed experiments.
- Comparison queries supported: filter/sort by any metric or parameter.
- Experiment naming: `{project}_{model_type}_{YYYYMMDD}_{sequence}` or equivalent structured scheme.

### Experiment Comparison

- Minimum two comparisons per evaluation: (1) vs baseline model, (2) vs previous best.
- Comparison table includes: all metrics · parameter diff · data version diff · resource usage.
- Winner determined by primary metric; ties broken by secondary metric, then resource efficiency.

---

## 5. Model Training

### Hyperparameter Management

- All hyperparameters defined in configuration file, ✗ hardcoded in training script.
- Configuration file versioned alongside code.
- Search strategy declared explicitly: grid | random | Bayesian | manual.
- Search budget defined before starting: max trials · max wall-clock time · max compute cost.

| Search Strategy | When to Use | Budget Rule |
|---|---|---|
| Grid | ≤3 params, ≤5 values each | Exhaustive — budget = grid size |
| Random | >3 params or continuous ranges | Min 50 trials or 2× grid equivalent |
| Bayesian | Expensive-to-evaluate models | Min 20 trials; surrogate model logged |
| Manual | Expert tuning on top of automated search | Each manual trial logged as experiment |

### Training Discipline

- Early stopping required for iterative models: patience defined, metric monitored, best checkpoint saved.
- Learning rate schedule declared: constant | step decay | cosine | warmup+decay.
- Gradient clipping enabled for deep models — max norm documented.
- Batch size justified: memory-constrained → largest that fits; convergence-constrained → validated via ablation.
- Checkpoint saved at configurable interval (epoch/step count). Minimum: best + last.
- Training resumes from checkpoint without restarting from scratch.

### Resource Budgets

| Resource | Requirement |
|---|---|
| GPU memory | Peak usage logged; must not exceed 90% of available |
| Wall-clock time | Maximum training time defined before start |
| Disk | Checkpoint size budgeted; old checkpoints pruned (keep top-K by metric) |
| CPU/RAM | Peak usage logged; OOM = failed run, not silent degradation |

### Cross-Validation Rules

- K-fold (k≥5) required when dataset < 10K rows.
- Stratified folds for classification tasks.
- Group-aware folds when data has entity grouping.
- Report mean ± std of primary metric across folds.
- ✗ Select best single fold — report aggregate.

---

## 6. Model Evaluation

### Metrics by Task Type

| Task Type | Primary Metric | Required Secondary Metrics |
|---|---|---|
| Binary classification | F1 or AUC-ROC (domain-dependent) | Precision · Recall · AUC-PR · accuracy |
| Multi-class classification | Macro F1 | Per-class F1 · confusion matrix · weighted F1 |
| Regression | RMSE or MAE (domain-dependent) | R² · MAPE · residual distribution |
| Ranking | NDCG@K | MAP@K · MRR · precision@K |
| Clustering | Silhouette score | Calinski-Harabasz · Davies-Bouldin · cluster size distribution |
| Time-series forecasting | MASE or sMAPE | RMSE · directional accuracy · coverage (if probabilistic) |
| Anomaly detection | AUC-PR | Precision@K · recall@K · false positive rate |
| Generative / NLP | Task-specific (BLEU, ROUGE, etc.) | Human evaluation score · perplexity |

### Evaluation Rules

- Every model compared against at least one baseline:

| Baseline Type | Definition |
|---|---|
| Naive baseline | Predict mean (regression) · predict majority class (classification) · random (ranking) |
| Previous production model | Current deployed model, if exists |
| Simple model | Linear/logistic regression or decision tree on same features |

- Evaluation on holdout test set happens once per model candidate. ✗ Iterate on test set — use validation set for tuning.
- Metrics computed on full test set and per-segment (demographic, temporal, geographic slices).
- Performance thresholds defined before evaluation: "model passes if metric X ≥ Y."
- Confidence intervals or statistical significance tests required when comparing models with <5% metric difference.
- Evaluation artifacts stored: confusion matrix · ROC curve · calibration plot · residual plot (as applicable).

---

## 7. Model Explainability

### Explainability Requirements by Risk Level

| Risk Level | Examples | Required Explainability |
|---|---|---|
| Low | Recommendation, content ranking | Global feature importance |
| Medium | Pricing, fraud scoring | Global + local explanations for flagged cases |
| High | Credit decisions, medical diagnosis, hiring | Global + local + counterfactual + bias audit |

### Explanation Methods

| Method | Scope | Use When |
|---|---|---|
| Feature importance (built-in) | Global | Tree-based models; fast first-pass |
| Permutation importance | Global | Any model; model-agnostic validation |
| SHAP values | Global + Local | Default choice for detailed explanations |
| LIME | Local | When SHAP is too expensive; tabular/text |
| Partial dependence plots | Global | Understanding feature-target relationships |
| Counterfactual explanations | Local | High-risk decisions requiring "what-if" |

### Explainability Rules

- Global feature importance generated for every production model, regardless of risk level.
- Top-K features (K ≥ 10 or all if fewer) documented with importance scores.
- If top feature contributes >50% of total importance → investigate for leakage or proxy bias.
- Local explanations stored for every prediction on high-risk models.
- Explanations validated: perturb top features → prediction must change proportionally.
- ✗ Use explainability as post-hoc justification for a decision already made. Generate before decision.

---

## 8. Model Registry

Central catalog of all trained models. Single source of truth for what exists, what's deployed, what's retired.

### Registry Record Per Model

| Field | Required | Description |
|---|---|---|
| `model_id` | Yes | Unique identifier |
| `model_version` | Yes | Semantic version or auto-increment |
| `experiment_id` | Yes | Link to experiment that produced it |
| `dataset_version` | Yes | Training data version |
| `framework` | Yes | Framework + version (e.g., scikit-learn 1.4) |
| `artifact_path` | Yes | Location of serialized model |
| `artifact_hash` | Yes | SHA-256 of model file |
| `metrics` | Yes | Primary + secondary metrics on holdout |
| `stage` | Yes | `development` → `staging` → `production` → `retired` |
| `created_at` | Yes | Timestamp |
| `created_by` | Yes | Author or pipeline ID |
| `model_card` | Production only | See Privacy & Ethics §12 |
| `serving_config` | Staging+ | Input schema · output schema · latency SLA |

### Promotion Lifecycle

```
development → staging → production → retired
     ↑            |          |
     └── rejected ←── rolled back
```

| Transition | Gate |
|---|---|
| development → staging | Evaluation gate passed (§6) · explainability generated (§7) |
| staging → production | Integration tests pass · latency SLA met · A/B test results (if required) · bias audit passed |
| production → retired | Replacement model promoted · traffic fully drained · archival complete |
| Any → rejected | Gate failure at any stage; reason logged |
| production → rolled back | Performance degradation detected → revert to previous production version |

### Registry Rules

- ✗ Deploy model not in registry. Every serving model has registry entry.
- ✗ Delete registry entries. Retired models archived, not removed.
- One model version per (model_id, stage) pair. Promoting new version auto-retires previous.
- Registry queryable by: model_id · stage · metric thresholds · date range · dataset version.

---

## 9. Model Deployment

### Serialization Formats

| Format | Use Case | Interop |
|---|---|---|
| ONNX | Cross-framework serving, edge deployment | High — framework-agnostic |
| Framework-native (joblib, pickle, SavedModel, .pt) | Same-framework serving | Low — framework-locked |
| PMML | Legacy enterprise integration | Medium — limited model types |
| Custom export (coefficients, rules) | Simple models, embedded systems | High — no runtime dependency |

### Serialization Rules

- Model file + inference code versioned together. ✗ Serialize model without pinning inference code version.
- Deserialization validated before deployment: load artifact → run sample prediction → compare expected output.
- Input/output schema embedded in or alongside serialized artifact.
- ✗ Use pickle for untrusted models — security risk. Prefer ONNX or framework-safe formats for external models.

### Serving Patterns

| Pattern | Description | When to Use |
|---|---|---|
| Batch prediction | Scheduled pipeline writes predictions to storage | High volume · latency-tolerant · predictions cacheable |
| Real-time API | Model behind HTTP/gRPC endpoint | Low latency required · per-request prediction |
| Embedded model | Model loaded in application process | Edge/mobile · ultra-low latency · no network dependency |
| Streaming | Model consumes event stream, emits predictions | Continuous data · near-real-time required |

### Deployment Rules

- Every deployment has rollback plan: previous model version identified, switch mechanism tested.
- Canary/shadow deployment for production models: route small traffic % to new model first.
- Input validation at serving boundary: schema check → type check → range check → reject invalid.
- Prediction latency budget defined: p50 · p95 · p99 — measured, not estimated.
- Model warm-up: load model and run dummy prediction before accepting live traffic.
- See `architecture/STANDARDS.md` §1 (principle 26): graceful degradation — if model fails, fallback to previous model or rule-based default.

### A/B Testing

- Control = current production model. Treatment = candidate model.
- Minimum sample size calculated before launch (power analysis).
- Primary metric and success criterion defined before launch. ✗ Change success criterion mid-test.
- Test duration: minimum 1 week or 1 full business cycle (whichever longer).
- Statistical significance required (p < 0.05 or equivalent Bayesian threshold) before declaring winner.

---

## 10. Monitoring

Post-deployment surveillance. Detect problems before users report them.

### What to Monitor

| Category | Metrics | Alert Threshold |
|---|---|---|
| Data drift | Feature distribution shift (PSI, KS-test, Jensen-Shannon) | PSI > 0.2 per feature or >0.1 on ≥3 features simultaneously |
| Concept drift | Prediction distribution shift · actual-vs-predicted divergence | Prediction mean shifts >2σ from training baseline |
| Model performance | Primary metric on labeled feedback | Degrades >5% from deployment baseline |
| Serving health | Latency (p50/p95/p99) · error rate · throughput | p99 > 2× SLA · error rate > 1% |
| Input quality | Null rate · out-of-range rate · schema violations | Any metric >2× training-time baseline |
| Output quality | Prediction confidence distribution · extreme value rate | >10% predictions below confidence threshold |

### Monitoring Rules

- Drift detection runs on every prediction batch (batch serving) or every N minutes (real-time serving; N ≤ 60).
- Reference distribution = training data distribution, recalculated on each retraining.
- See `observability/STANDARDS.md` for structured logging and alerting patterns.
- Every alert has documented response runbook: who investigates · diagnostic steps · escalation path.

### Retraining Triggers

| Trigger | Action |
|---|---|
| Data drift exceeds threshold for >24 hours | Initiate retraining pipeline with fresh data |
| Performance metric degrades >5% on labeled data | Initiate retraining; if >15%, rollback to previous model immediately |
| Scheduled (calendar) | Retrain at defined cadence (weekly/monthly) regardless of drift |
| Data volume milestone | Retrain when new labeled data exceeds 20% of training set size |
| Feature store update | Evaluate impact; retrain if affected features are in top-K importance |

### Retraining Rules

- Retraining follows full lifecycle (§1) — ✗ skip evaluation or registry steps.
- Retrained model must pass same gates as original before promotion.
- Automated retraining pipelines require human approval gate before production promotion.
- Retraining frequency bounded: minimum interval between retrains to prevent thrashing.

---

## 11. Reproducibility

Every result must be reproducible from recorded metadata alone.

### Seed Management

| Component | Rule |
|---|---|
| Global random seed | Set once at pipeline entry point; logged in experiment record |
| Framework-specific seeds | Set explicitly for each framework (numpy, torch, tensorflow, etc.) |
| Data shuffling | Seed-controlled; same seed → same shuffle order |
| Model initialization | Seed-controlled; same seed → same initial weights |
| Hardware non-determinism | Document known sources (GPU atomics, cuDNN auto-tune); disable auto-tune for strict reproducibility |

### Deterministic Pipeline Rules

- Pipeline = code version + data version + config version + environment version → deterministic output.
- ✗ Download data at training time from mutable source. Snapshot first, version, then train.
- ✗ Depend on system clock, hostname, or process ID for any computation affecting model output.
- All random operations use seeded generators, ✗ default/unseeded random calls.
- If exact reproducibility impossible (GPU non-determinism), document tolerance: "metrics reproducible within ±0.2%."

### Environment Pinning

- Exact dependency versions locked (lock file, not version ranges).
- Runtime version pinned: language version + framework version + CUDA version (if GPU).
- Container image or environment hash recorded per experiment.
- ✗ "Works on my machine" — pipeline must reproduce in clean environment from recorded metadata.

---

## 12. Privacy & Ethics

### Data Anonymization

| Technique | Use When | Limitation |
|---|---|---|
| Pseudonymization | Need to re-link later (with key) | Reversible if key compromised |
| K-anonymity | Publishing aggregate data | Vulnerable to background knowledge attacks |
| Differential privacy | Training on sensitive data | Reduces model accuracy; privacy budget finite |
| Data masking | Display/logging of sensitive fields | ✗ Use for model training — destroys signal |
| Synthetic data | Cannot use real data at all | Must validate synthetic ≈ real distribution |

### Anonymization Rules

- PII removed or pseudonymized before data enters ML pipeline. ✗ PII in feature matrix.
- Anonymization applied at data collection/ingestion stage, ✗ at training time.
- Anonymization method + parameters logged as part of data version metadata.
- Re-identification risk assessed: if k-anonymity k < 5, insufficient.

### Bias Auditing

- Bias audit required before production promotion (staging → production gate in §8).
- Protected attributes identified per domain and jurisdiction (gender, race, age, disability, etc.).
- Audit method: evaluate model metrics per protected group independently.

| Fairness Metric | Definition | Threshold |
|---|---|---|
| Demographic parity | P(positive\|group A) ≈ P(positive\|group B) | Ratio within [0.8, 1.25] |
| Equal opportunity | TPR(group A) ≈ TPR(group B) | Ratio within [0.8, 1.25] |
| Predictive parity | Precision(group A) ≈ Precision(group B) | Ratio within [0.8, 1.25] |
| Calibration | Predicted probability ≈ observed rate per group | Max deviation < 0.05 |

- Fairness metric selection depends on domain — ✗ use single metric universally. Document which metric and why.
- If bias detected: (1) investigate root cause in data, (2) apply mitigation (resampling, reweighting, constraint), (3) re-audit.
- ✗ Ship model that fails bias audit without documented exception approved by accountable human.

### Model Card

Every production model has a model card documenting:

| Section | Contents |
|---|---|
| Model details | Type · version · framework · training date · owner |
| Intended use | Primary use case · known out-of-scope uses |
| Training data | Dataset version · size · collection methodology · limitations |
| Evaluation | Metrics on holdout · per-segment performance · comparison to baseline |
| Fairness | Protected groups evaluated · fairness metrics · known disparities |
| Limitations | Known failure modes · data gaps · performance ceilings |
| Recommendations | Deployment constraints · required monitoring · update cadence |

---

## 13. Scale Matrix

Apply ML rigor proportionally. See `architecture/STANDARDS.md` §12 for general scale guidance.

| Concern | PoC / Notebook | Small (Pipeline) | Production (Full MLOps) |
|---|---|---|---|
| Data versioning (§2) | Manual notes on data source | Hashed snapshots | Full lineage tracking + automated versioning |
| Data preparation (§3) | Notebook cells, manual splits | Script-based pipeline, reproducible splits | Automated pipeline with leakage tests |
| Experiment tracking (§4) | Notebook output cells | Local tracking tool (MLflow, etc.) | Centralized tracking with comparison UI |
| Hyperparameters (§5) | Manual tuning | Config file + grid/random search | Automated search with budget limits |
| Cross-validation (§5) | Single train/test split | K-fold if small data | K-fold + holdout + temporal validation |
| Evaluation (§6) | Primary metric only | Primary + secondary + baseline comparison | Full metric suite + per-segment + significance tests |
| Explainability (§7) | Feature importance plot | SHAP/LIME for key predictions | Full global + local + bias audit |
| Model registry (§8) | File system with naming convention | Local registry (MLflow, etc.) | Centralized registry with promotion gates |
| Deployment (§9) | Manual file copy / notebook | Batch script or simple API | Full CI/CD + canary + A/B + rollback |
| Monitoring (§10) | Manual checks | Scheduled drift reports | Real-time drift + performance + automated alerts |
| Reproducibility (§11) | Seeds set, manual notes | Locked deps + seeded pipeline | Full environment pinning + container |
| Privacy & Ethics (§12) | Awareness, no formal audit | PII removal + basic bias check | Full anonymization + bias audit + model card |

### Scale Transition Rules

- PoC → Small: triggered when model influences any business decision or user-facing output.
- Small → Production: triggered when model serves >100 users or >$10K decisions per month.
- Transition follows Strangler Fig pattern (see `architecture/STANDARDS.md` §11) — evolve, ✗ rewrite.

---

## 14. Checklist

### New ML Project

- [ ] Problem framed: task type · primary metric · success threshold · baseline defined
- [ ] Data sourced: collection method · access documented · initial quality assessment
- [ ] Data versioned: first snapshot created with schema + metadata (§2)
- [ ] Splits defined: strategy selected per data type · leakage audit performed (§3)
- [ ] Feature pipeline: transforms documented · deterministic · version-controlled (§3)
- [ ] Experiment tracking configured: all required fields capturable (§4)
- [ ] Training config: hyperparameters externalized · search strategy defined · resource budget set (§5)
- [ ] Evaluation plan: metrics selected by task type · baseline model trained · thresholds set (§6)
- [ ] Reproducibility: seeds set · dependencies locked · environment pinned (§11)

### Model Promotion to Staging

- [ ] Experiment logged with all required fields (§4)
- [ ] Beats baseline on primary metric (§6)
- [ ] Holdout evaluation complete — test set used exactly once (§6)
- [ ] Global feature importance generated (§7)
- [ ] Risk level assessed → explainability level determined (§7)
- [ ] Model registered with full metadata (§8)
- [ ] Serialization validated: load → predict → output matches expected (§9)
- [ ] Input/output schema documented (§9)

### Model Promotion to Production

- [ ] All staging checks passed
- [ ] Integration tests pass in staging environment (§9)
- [ ] Latency SLA met: p50 · p95 · p99 measured (§9)
- [ ] Bias audit passed per required fairness metrics (§12)
- [ ] Model card written (§12)
- [ ] Monitoring configured: drift detection · performance tracking · alerting (§10)
- [ ] Retraining triggers defined (§10)
- [ ] Rollback plan documented and tested (§9)
- [ ] Canary/shadow deployment completed successfully (§9)
- [ ] Human approval recorded

### Retraining Cycle

- [ ] Trigger documented (drift | schedule | data volume | performance degradation) (§10)
- [ ] New data version created (§2)
- [ ] Full lifecycle followed: preparation → training → evaluation → registry (§1)
- [ ] Comparison to current production model documented (§6)
- [ ] Promotion gates re-evaluated — ✗ skip any gate (§8)
- [ ] Previous model archived, not deleted (§8)
