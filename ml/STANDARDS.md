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
