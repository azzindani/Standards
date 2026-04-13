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
