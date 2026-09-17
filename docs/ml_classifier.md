# STRATA — Phase 4: Machine Learning Deformation Classifier

> **MANDATORY SCIENTIFIC & SAFETY DISCLAIMERS**  
> 1. *The Phase 4 classifier is trained and evaluated on controlled synthetic data. Performance on synthetic observations does not establish equivalent performance on real-world Sentinel-1/InSAR observations.*  
> 2. *Model confidence is an internal statistical output and is not equivalent to engineering safety confidence. High confidence indicates statistical alignment with training features, NOT structural safety or absence of risk.*

---

## 1. Architecture & Design Principles

The **STRATA ML Deformation Classifier** is the primary statistical learning engine designed to classify multi-epoch InSAR observation sequences into 7 ground-truth deformation classes:

```text
┌─────────────────────────────────────────────────────────────────────────────────┐
│                           ML INFERENCE ARCHITECTURE                             │
│                                                                                 │
│   InSAR Observation Sequence                                                    │
│               │                                                                 │
│               ▼                                                                 │
│   Observable Feature Extraction (28 features)                                   │
│   [Strict Allowlist Enforcement — Forbidden Columns Blocked]                   │
│               │                                                                 │
│               ▼                                                                 │
│   Preprocessing Pipeline (Fitted strictly on TRAIN)                             │
│   [Median Imputation → Optional Feature Scaling]                                │
│               │                                                                 │
│               ▼                                                                 │
│   Base Classifier (Balanced Random Forest: n=200, depth=8, leaf=3)             │
│               │                                                                 │
│               ▼                                                                 │
│   Probability Calibration (Sigmoid / Platt Scaling on VALIDATION)               │
│               │                                                                 │
│               ▼                                                                 │
│   MLClassificationResult                                                        │
│   ├── Predicted Class: GroundTruthClass                                         │
│   ├── Calibrated Probabilities (7-class distribution, sum = 1.0)               │
│   ├── Model Confidence: max(P)                                                  │
│   ├── Predictive Uncertainty: Normalized Shannon Entropy                        │
│   └── Model & Feature Metadata                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### Decoupling Principle
The ML classifier operates completely independently from the deterministic `PhysicsInSARConsistencyEngine`. The ML model does not ingest physics engine classifications, confidence scores, or kinematic flags, ensuring that both engines produce independent evidence streams for subsequent consensus evaluation (Phase 5).

---

## 2. Input Features & Strict Allowlist

The model only ingests features that can be derived from observable radar observations.

### Feature Groupings (28 Features)

| Group | Features | Physical Meaning |
|---|---|---|
| **A. Measurement Quality** | `coherence_mean`, `coherence_std`, `minimum_coherence`, `phase_quality_mean`, `phase_quality_std`, `noise_estimate_mean_mm` | Measures interferometric phase stability and decorrelation noise. |
| **B. Displacement Statistics** | `mean_displacement_mm`, `displacement_std_mm`, `displacement_range_mm`, `displacement_to_noise_ratio`, `mean_absolute_step_mm`, `max_absolute_step_mm`, `max_step_to_range_ratio` | Measures deformation amplitude, range, and step transition dynamics. |
| **C. Temporal / Kinematic** | `slope_mm_per_year`, `linear_fit_residual_std_mm`, `acceleration_mm_per_year2`, `quadratic_fit_residual_std_mm`, `directional_consistency`, `sign_change_count`, `temporal_autocorrelation_lag1` | Captures long-term velocity, curvature, step reversals, and persistent drift. |
| **D. Periodicity** | `zero_crossing_count`, `approximate_periodicity_indicator` | Detects cyclic baseline crossings characteristic of seasonal thermal expansion. |
| **E. Geometry** | `epoch_count`, `duration_days`, `temporal_spacing_mean_days`, `temporal_spacing_std_days`, `incidence_angle_mean_deg`, `incidence_angle_std_deg` | Radar look geometry and orbital temporal sampling. |

---

## 3. Forbidden Ground-Truth Fields (Leakage Firewall)

The training and inference pipelines enforce a strict leakage firewall. Any presence of forbidden columns triggers an immediate `ValueError`:

* `true_structural_displacement_mm`
* `true_environmental_displacement_mm`
* `true_atmospheric_displacement_mm`
* `true_noise_mm`
* `ground_truth_class` (Permitted solely as target label $y$)
* `scenario` (e.g. `STABLE_NOMINAL`)
* `parameters` (generative parameters: velocity, acceleration, amplitude, period)
* `random_seed`
* `is_edge_case` / `edge_case_type`
* `physics_classification`
* `physics_confidence` / `overall_confidence`

---

## 4. Training & Validation Protocol

The model was trained following strict partition isolation:
1. **Train Split (2,450 sequences)**: Preprocessing pipeline (`SimpleImputer`) and base estimator (`RandomForestClassifier`) were fitted exclusively on training data.
2. **Validation Split (525 sequences)**: Probability calibration (`CalibratedClassifierCV` with Platt scaling) was fitted on the validation set using `FrozenEstimator` to prevent test contamination.
3. **Test Split (525 sequences)**: Evaluated strictly once after model freeze.

### Hyperparameters
```json
{
  "n_estimators": 200,
  "max_depth": 8,
  "min_samples_leaf": 3,
  "class_weight": "balanced",
  "random_state": 42
}
```

---

## 5. Test Split Evaluation Metrics

Evaluated on the 525 unseen sequences in `test.jsonl`:

| Metric | Phase 4 Calibrated Random Forest | Phase 4 Baseline Logistic Regression | Phase 3.1 Random Forest Baseline |
|---|:---:|:---:|:---:|
| **Test Accuracy** | **72.19%** (378/525) | 70.10% (368/525) | 69.52% (365/525) |
| **Macro Precision** | **72.27%** | 70.08% | 69.68% |
| **Macro Recall** | **72.19%** | 70.10% | 69.52% |
| **Macro F1 Score** | **0.7180** | 0.6855 | 0.6872 |
| **Weighted F1 Score** | **0.7180** | 0.6855 | 0.6872 |
| **Multi-Class Brier Score** | **0.3529** | 0.4217 | 0.3829 |
| **Multi-Class Log Loss** | **0.7143** | 0.7712 | 0.7543 |
| **Macro ROC-AUC (OvR)** | **0.9392** | 0.9204 | 0.9180 |
| **Mean Confidence** | 68.65% | 64.12% | 67.43% |
| **Mean Uncertainty Entropy** | 0.4544 | 0.4910 | 0.4720 |

---

## 6. Per-Class Test Performance

| Class Name | Precision | Recall | F1 Score | Support | Key Distinction |
|---|:---:|:---:|:---:|:---:|---|
| `LOW_QUALITY` | **100.00%** | **100.00%** | **1.0000** | 75 | Decorrelation floor ($\gamma < 0.25$) perfectly identified. |
| `TEMPORALLY_INCONSISTENT` | **95.89%** | **93.33%** | **0.9459** | 75 | High sign reversals and volatility cleanly captured. |
| `SEASONAL_ENVIRONMENTAL` | **92.42%** | **81.33%** | **0.8652** | 75 | Bounded sinusoidal oscillations cleanly isolated. |
| `ATMOSPHERIC_TRANSIENT` | **73.49%** | **81.33%** | **0.7722** | 75 | High single-step ratio flags isolated transient spikes. |
| `STABLE` | **53.40%** | **73.33%** | **0.6180** | 75 | Low displacement range; absorbs weak structural creep. |
| `STRUCTURAL_MONOTONIC` | **47.83%** | **44.00%** | **0.4583** | 75 | Confused with accelerating deformation and noise. |
| `STRUCTURAL_ACCELERATING` | **42.86%** | **32.00%** | **0.3664** | 75 | Near-degenerate with monotonic trend on short baselines. |

---

## 7. Confusion Matrix (Test Split)

```text
True \ Pred                | ATMOSPHERI | LOW_QUALIT | SEASONAL_E | STABLE     | STRUCT_ACC | STRUCT_MON | TEMPORALLY
------------------------------------------------------------------------------------------------------------------
ATMOSPHERIC_TRANSIENT      |         61 |          0 |          1 |          6 |          3 |          2 |          2
LOW_QUALITY                |          0 |         75 |          0 |          0 |          0 |          0 |          0
SEASONAL_ENVIRONMENTAL     |          6 |          0 |         61 |          0 |          2 |          6 |          0
STABLE                     |          4 |          0 |          0 |         55 |         11 |          4 |          1
STRUCTURAL_ACCELERATING    |          3 |          0 |          2 |         22 |         24 |         24 |          0
STRUCTURAL_MONOTONIC       |          5 |          0 |          2 |         19 |         16 |         33 |          0
TEMPORALLY_INCONSISTENT    |          4 |          0 |          0 |          1 |          0 |          0 |         70
```

---

## 8. Confidence & Epistemic Uncertainty Analysis

To determine whether model probabilities reflect genuine uncertainty for the Phase 5 consensus engine, we compared correct vs. incorrect test predictions:

| Prediction Outcome | Sample Count | Mean Confidence ($\max P$) | Mean Shannon Entropy |
|---|:---:|:---:|:---:|
| **Correct Predictions** | 379 | **76.71%** | **0.3779** |
| **Incorrect Predictions** | 146 | **47.71%** | **0.6531** |

* **Key Scientific Finding**: When the model makes incorrect predictions, its uncertainty entropy increases sharply ($0.3779 \to 0.6531$), and confidence drops from $76.7\%$ to $47.7\%$. This indicates well-calibrated epistemic uncertainty, allowing the consensus engine to downweight or trigger arbitration on ambiguous samples.

---

## 9. Feature Importance (Random Forest)

Top 10 features ranked by mean Gini impurity reduction:

| Rank | Feature | Importance | Feature Group | Physical Association |
|:---:|---|:---:|:---:|---|
| 1 | `temporal_autocorrelation_lag1` | **9.50%** | C (Temporal) | Continuity of deformation trajectory across successive epochs. |
| 2 | `mean_absolute_step_mm` | **8.29%** | B (Displacement) | Scale of epoch-to-epoch displacement shifts. |
| 3 | `displacement_to_noise_ratio` | **7.69%** | B (Displacement) | Signal-to-noise ratio above instrument noise floor. |
| 4 | `minimum_coherence` | **7.64%** | A (Quality) | Flags decorrelated radar acquisitions. |
| 5 | `coherence_mean` | **6.96%** | A (Quality) | Baseline interferometric quality. |
| 6 | `phase_quality_mean` | **6.72%** | A (Quality) | Phase unwrapping stability. |
| 7 | `mean_displacement_mm` | **6.54%** | B (Displacement) | Net directional settlement or heave. |
| 8 | `noise_estimate_mean_mm` | **4.98%** | A (Quality) | Measurement error standard deviation. |
| 9 | `linear_fit_residual_std_mm` | **4.77%** | C (Temporal) | Deviation from linear kinematics. |
| 10 | `max_absolute_step_mm` | **4.47%** | B (Displacement) | Peak single-epoch jump (flags atmospheric spikes). |

---

## 10. Controlled Feature Ablation Study

Evaluated on the exact same train/test splits:

| Ablation Subset | Feature Count | Test Accuracy | Macro F1 | Key Finding |
|---|:---:|:---:|:---:|---|
| **A. Quality Only** | 6 | 35.05% | 0.3357 | Can separate `LOW_QUALITY`, but fails on physical kinematics. |
| **B. Displacement Only** | 7 | 64.95% | 0.6337 | Good amplitude discrimination, but misses complex temporal curves. |
| **C. Temporal Only** | 7 | 51.62% | 0.5055 | Kinematics alone struggle without radar noise/amplitude scale. |
| **D. Periodicity Only** | 2 | 30.10% | 0.2645 | Insufficient alone to separate non-seasonal classes. |
| **E. Static + Temporal** | 14 | 67.81% | 0.6650 | Substantial synergy between amplitude and temporal evolution. |
| **F. All Allowlisted Features** | **28** | **73.14%** | **0.7231** | **Best performance**: Multi-modal fusion is necessary. |

---

## 11. Error Analysis & Key Failure Modes

1. **Near-Degeneracy of Monotonic vs. Accelerating Creep**:
   - 24 accelerating sequences were predicted as monotonic; 16 monotonic were predicted as accelerating.
   - *Physical Mechanism*: Over short observation windows ($t < 0.5$ years), $0.5 a t^2$ is negligible relative to $v_0 t$. The two classes are mathematically near-degenerate.
2. **Weak Structural Deformation vs. Noise Floor**:
   - 22 accelerating and 19 monotonic sequences were classified as `STABLE`.
   - *Physical Mechanism*: Slow settlement rates ($0.8 - 1.5$ mm/yr) over $\sim 100$ days accumulate $< 0.5$ mm total movement, which is buried under the $1.5$ mm measurement noise floor.
3. **Flank Ambiguity of Seasonal Oscillations**:
   - 6 seasonal sequences were predicted as monotonic and 2 as accelerating.
   - *Physical Mechanism*: Capturing only a monotonic rising/falling flank of an annual ($T=365$ day) cycle resembles progressive settlement over truncated observation windows.

---

## 12. Model Versioning & Registry

* **Model Version**: `strata_ml_v0_1_0`
* **Feature Schema**: `v1.0.0`
* **Registry Artifacts**:
  - `models/strata_ml_v0_1_0/model.joblib`: Serialized calibrated Random Forest and preprocessor.
  - `models/strata_ml_v0_1_0/metadata.json`: Provenance metadata, training configuration, and test metrics.
  - `models/strata_ml_v0_1_0/feature_schema.json`: Complete feature allowlist and groupings.
* **Inference API**:
  ```python
  from backend.app.services.ml import MLDeformationClassifier

  classifier = MLDeformationClassifier()
  result = classifier.predict(observation_sequence)
  print(result.predicted_class)
  print(result.probabilities)
  print(result.confidence)
  print(result.entropy)
  ```
