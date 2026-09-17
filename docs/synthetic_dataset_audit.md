# STRATA — Phase 3.1: Synthetic Dataset Quality & Separability Audit

> **MANDATORY AUDIT DISCLAIMER**  
> *This document represents an objective statistical and informational audit of the STRATA Phase 3 synthetic InSAR dataset. It does NOT train or tune the final Phase 4 machine learning classifier, does NOT alter physics engine thresholds, and does NOT regenerate synthetic samples to optimize classification scores.*

---

## 1. Objective

The primary objective of Phase 3.1 is to conduct an empirical audit of the 3,500-sequence synthetic InSAR dataset generated in Phase 3. Specifically, this audit evaluates:
1. **Physical Coherence**: Whether generated multi-epoch sequences adhere to radar geometry and kinematics.
2. **Statistical Separability**: How distinguishable ground-truth deformation classes are using purely observable InSAR features.
3. **Absence of Synthetic Shortcuts**: Whether generator artifacts or parameter shortcuts artificially separate classes.
4. **Information Modality**: The relative predictive contribution of static radar summary statistics versus dynamic temporal sequence features.
5. **Legitimate Physical Ambiguity**: Documenting cases where physical processes naturally overlap within realistic observation windows.

---

## 2. Dataset Integrity & Partitions

The audited dataset consists of 3,500 multi-epoch InSAR sequences partitioned deterministically (seed `42`) with zero sample overlap:

| Split | Sequence Count | Samples per Class | Status |
|---|:---:|:---:|---|
| **Train** | 2,450 | 350 | Verified, 0 missing values, 0 NaNs |
| **Validation** | 525 | 75 | Verified, 0 missing values, 0 NaNs |
| **Test** | 525 | 75 | Verified, 0 missing values, 0 NaNs |
| **Total** | **3,500** | **500** | **Verified, 0 split leakage** |

* **Observed Fact**: All 3,500 sequence timelines have strictly increasing UTC timestamps ($t_{i+1} > t_i$).
* **Observed Fact**: Component reconstruction identity $|\text{observed} - (\text{structural} + \text{environmental} + \text{atmospheric} + \text{noise})| < 10^{-4}$ mm holds identically across all 43,842 synthesized epochs.

---

## 3. Observable vs. Ground-Truth Features

STRATA enforces strict architectural separation between features available to inference models and internal ground-truth components.

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         FEATURE SEPARATION FRAMEWORK                             │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ GROUP A: OBSERVABLE MODEL INPUTS       │ GROUP B: ISOLATED GROUND-TRUTH ONLY     │
│ (Permitted for ML feature tables)       │ (Strictly forbidden for ML inputs)      │
├────────────────────────────────────────┼─────────────────────────────────────────┤
│ • epoch_count                          │ • true_structural_displacement_mm       │
│ • duration_days                        │ • true_environmental_displacement_mm    │
│ • temporal_spacing_mean/std_days       │ • true_atmospheric_displacement_mm      │
│ • incidence_angle_mean/std_deg         │ • true_noise_mm                         │
│ • coherence_mean/std/minimum           │ • ground_truth_class (Target label only)│
│ • phase_quality_mean/std               │ • scenario (e.g. STABLE_NOMINAL)        │
│ • noise_estimate_mean_mm               │ • generative parameters (v, a, A, T)    │
│ • mean/std/range displacement          │ • is_edge_case                          │
│ • displacement_to_noise_ratio          │ • edge_case_type                        │
│ • mean/max absolute step               │                                         │
│ • max_step_to_range_ratio              │                                         │
│ • sign_change_count                    │                                         │
│ • zero_crossing_count                  │                                         │
│ • directional_consistency              │                                         │
│ • slope_mm_per_year                    │                                         │
│ • linear_fit_residual_std_mm           │                                         │
│ • acceleration_mm_per_year2            │                                         │
│ • quadratic_fit_residual_std_mm        │                                         │
│ • temporal_autocorrelation_lag1        │                                         │
│ • approximate_periodicity_indicator    │                                         │
└────────────────────────────────────────┴─────────────────────────────────────────┘
```

The feature extraction engine (`backend/app/services/synthetic/feature_extractor.py`) extracts 28 continuous observable features and completely strips any ground-truth components before generating CSV tables (`features_train.csv`, `features_validation.csv`, `features_test.csv`).

---

## 4. Feature Distribution Analysis

Statistical summaries across all 3,500 samples (from `feature_summary.json`):

| Feature | Overall Mean | Min | Median | Max | Class Distribution Highlights |
|---|:---:|:---:|:---:|:---:|---|
| `coherence_mean` | 0.729 | 0.126 | 0.817 | 0.948 | `LOW_QUALITY` is concentrated in $[0.13, 0.23]$; all other classes span $[0.65, 0.95]$. |
| `displacement_range_mm` | 8.84 | 1.13 | 7.21 | 54.72 | `STABLE` median range is $3.78$ mm; `STRUCTURAL_ACCEL` median range is $15.82$ mm. |
| `slope_mm_per_year` | -2.18 | -42.85 | -0.62 | 26.54 | Monotonic and accelerating structures have strong negative/positive slopes; stable and seasonal center around $0.0$ mm/yr. |
| `sign_change_count` | 4.82 | 0.0 | 5.0 | 18.0 | `TEMPORALLY_INCONSISTENT` exhibits high sign changes (median 9.0); `STRUCTURAL` exhibits low sign changes (median 2.0). |
| `directional_consistency`| 0.635 | 0.250 | 0.625 | 1.000 | Structural trends average $0.78 - 0.84$; stable and inconsistent average $0.50 - 0.58$. |
| `incidence_angle_mean_deg`| 35.03 | 25.04 | 35.05 | 44.97 | Identical uniform distribution across all 7 classes (mean $\approx 35.0^\circ$, std $\approx 5.7^\circ$). |

* **Observed Fact**: No features contain NaN, Inf, or constant null variance.

---

## 5. Shortcut & Leakage Analysis

The audit examined whether any observable feature trivially identifies a ground-truth class:

1. **Low-Quality Coherence Separation**:
   - *Finding*: `LOW_QUALITY` maximum mean coherence is $0.229$; non-`LOW_QUALITY` minimum mean coherence is $0.651$.
   - *Audit Verdict*: **PHYSICALLY JUSTIFIED**.
   - *Rationale*: In SAR interferometry, decorrelation noise dominates when $\gamma < 0.25$. This separation reflects the real-world definition of unusable interferograms.
2. **Epoch Count Distribution**:
   - *Finding*: `SEASONAL_ENVIRONMENTAL` sequences have mean epoch count $16.7$ (range 10–24) compared to mean $13.0$ (range 6–20) for other classes.
   - *Audit Verdict*: **GENERATOR ARTIFACT**.
   - *Rationale*: To capture multi-epoch seasonal cycles, the generator used longer durations. While physically understandable, an ML classifier could use sequence length as a weak proxy for seasonality. In Phase 4, models should be tested with sequence-length normalization.
3. **Radar Incidence Angle**:
   - *Finding*: Class means are strictly identical ($35.0^\circ \pm 0.2^\circ$).
   - *Audit Verdict*: **NO LEAKAGE** (Physically coherent common radar envelope).
4. **Single-Feature Probing Test (Decision Tree Depth=3)**:
   - Evaluated whether any single feature could classify the 7 classes:
     - `displacement_to_noise_ratio`: **28.19%** test accuracy (Macro F1: 0.2680)
     - `temporal_autocorrelation_lag1`: **32.19%** test accuracy (Macro F1: 0.2546)
     - `linear_fit_residual_std_mm`: **30.67%** test accuracy (Macro F1: 0.2506)
     - `mean_absolute_step_mm`: **28.38%** test accuracy (Macro F1: 0.2449)
     - `coherence_mean`: **24.57%** test accuracy (Macro F1: 0.2012)
   - *Audit Verdict*: **NO TRIVIAL SHORTCUTS DETECTED**. The highest single-feature accuracy is 32.19% (compared to 14.29% random guessing). No single feature acts as a cheat code for the dataset.

---

## 6. Diagnostic Baseline Results

> **PHASE 3.1 DIAGNOSTIC BASELINE — NOT FINAL ML MODEL**  
> Evaluated on the unseen test split (525 sequences):

| Diagnostic Model | Test Accuracy | Macro Precision | Macro Recall | Macro F1 |
|---|:---:|:---:|:---:|:---:|
| **Majority-Class Baseline** | 14.29% | 2.04% | 14.29% | 0.0357 |
| **Logistic Regression (C=1.0)** | 68.95% | 68.28% | 68.95% | 0.6835 |
| **Shallow Decision Tree (d=4)** | 60.00% | 60.42% | 60.00% | 0.5675 |
| **Conservative Random Forest (d=6)** | **69.52%** | **69.68%** | **69.52%** | **0.6872** |

### Diagnostic Random Forest Confusion Matrix (Test Split)
```text
True Ground-Truth Class  | ATMOSP | LOW_Q | SEASON | STABLE | ACCEL | MONOTON | INCONS
---------------------------------------------------------------------------------------
ATMOSPHERIC_TRANSIENT    |     58 |     0 |      1 |      6 |     3 |       2 |      5
LOW_QUALITY              |      0 |    75 |      0 |      0 |     0 |       0 |      0
SEASONAL_ENVIRONMENTAL   |      7 |     0 |     60 |      1 |     4 |       3 |      0
STABLE                   |      6 |     0 |      0 |     55 |    12 |       0 |      2
STRUCTURAL_ACCELERATING  |      4 |     0 |      4 |     25 |    26 |      16 |      0
STRUCTURAL_MONOTONIC     |      8 |     0 |      3 |     24 |    17 |      23 |      0
TEMPORALLY_INCONSISTENT  |      4 |     0 |      0 |      2 |     1 |       0 |     68
```

---

## 7. Static vs. Temporal Information Comparison

To assess whether the classification signal is static or temporal, a controlled experiment was run using the diagnostic Random Forest model:

| Information Subset | Feature Count | Test Accuracy | Test Macro F1 |
|---|:---:|:---:|:---:|
| **Experiment A: Static Features Only** | 16 | 63.81% | 0.6296 |
| **Experiment B: Temporal Features Only** | 12 | 56.00% | 0.5521 |
| **Experiment C: Combined (Static + Temporal)**| **28** | **69.52%** | **0.6872** |

### Interpretation
* **Observed Fact**: Neither static summary features alone (63.81%) nor temporal step features alone (56.00%) achieve the performance of the combined feature set (69.52%).
* **Scientific Interpretation**: Structural deformation classification requires cross-referencing kinematic evolution (slope, curvature, step consistency) against radar quality and noise floors (coherence, noise standard deviation).

---

## 8. Pairwise Class Separability

Pairwise binary classification diagnostics on critical class boundaries:

| Class Pair | Binary Test Accuracy | Binary F1 | Key Distinguishing Factors |
|---|:---:|:---:|---|
| **SEASONAL vs ATMOSPHERIC** | **94.00%** | 0.9412 | Reversible oscillation vs single isolated impulse spike. |
| **INCONSISTENT vs ATMOSPHERIC** | **94.00%** | 0.9396 | Alternating direction jumps vs single baseline return. |
| **ACCELERATING vs SEASONAL** | **90.00%** | 0.8980 | Non-zero second derivative with monotonic trend vs zero net displacement. |
| **MONOTONIC vs SEASONAL** | **89.33%** | 0.8904 | Monotonic slope and high directional consistency vs periodic zero crossings. |
| **MONOTONIC vs ATMOSPHERIC** | **88.00%** | 0.8784 | Continuous velocity vs single-epoch impulse. |
| **STABLE vs MONOTONIC** | **76.67%** | 0.7368 | Separability depends on velocity SNR ($v / \sigma_{\text{noise}}$). |
| **STABLE vs ACCELERATING** | **69.33%** | 0.6806 | Early-stage quadratic curvature is subtle in short observation sequences. |

---

## 9. Legitimate Physical Ambiguities Discovered

The audit uncovered several intrinsically ambiguous boundary conditions in the dataset:

1. **Slow Structural Deformation vs. Measurement Noise**:
   * *Observation*: 24 out of 75 `STRUCTURAL_MONOTONIC` and 25 out of 75 `STRUCTURAL_ACCELERATING` test sequences were classified by the baseline model as `STABLE`.
   * *Physical Mechanism*: When $v \in [0.8, 2.0]$ mm/yr and the observation timeline is only 6–10 epochs ($\approx 100$ days), total physical deformation is $< 0.6$ mm, well below the $1.5$ mm measurement noise floor.
   * *Interpretation*: This is a legitimate physical boundary condition. An SHM system must acknowledge that deformation below the sensor noise floor is undetectable without longer temporal baselines.
2. **Accelerating vs. Monotonic Structural Deformation**:
   * *Observation*: 16 accelerating sequences were predicted as monotonic, and 17 monotonic sequences were predicted as accelerating.
   * *Physical Mechanism*: On short observation baselines ($t < 0.5$ years), the quadratic term $0.5 a t^2$ is negligible compared to the linear term $v_0 t$. The two classes are mathematically near-degenerate on short baselines.
3. **Partial Seasonal Cycles**:
   * *Observation*: 14 `SEASONAL_ENVIRONMENTAL` sequences in the test set exhibited directional consistency $\ge 0.75$.
   * *Physical Mechanism*: An observation sequence spanning 120 days of an annual ($T=365$ day) thermal cycle captures only one flank of the sinusoidal curve, creating apparent monotonic movement.

---

## 10. Audit Findings Summary

1. **No Catastrophic Leakage**: Ground-truth components are strictly decoupled from observable InSAR features.
2. **No Single-Feature Shortcut**: The best single feature achieves only 28–32% test accuracy.
3. **Multi-Feature Coherence**: Combined static and temporal features outperform isolated subsets, proving multi-modal necessity.
4. **Clean Baseline Ceiling**: The conservative baseline models score between 60% and 70% accuracy, providing a healthy, non-trivial headroom for the Phase 4 ML classifier.
5. **High Confidence Quality Detection**: Low coherence and severe decorrelation are 100% cleanly separable.

---

## 11. Scientific Limitations

* **Prototype Distributions**: Generative parameter ranges are experimental prototype assumptions, not calibrated against specific geotechnical field sites.
* **Single-Orbit Line-of-Sight**: Displacements are modeled along a single 1D Line-of-Sight (LOS) angle; 3D decomposition from ascending and descending passes is not included.
* **Linear Phase Screening**: Tropospheric delays are modeled as localized temporal impulse spikes rather than spatial 2D turbulence phase screens (APS).

---

## 12. Recommendations for Phase 4 (ML Classifier)

1. **Sequence Length Invariance**: Normalize features (e.g. step rates, slope residuals) by total duration to prevent models from exploiting the slight epoch count disparity in seasonal samples.
2. **Hierarchical or Multiclass Structuring**: Consider grouping `STRUCTURAL_MONOTONIC` and `STRUCTURAL_ACCELERATING` into a broader `STRUCTURAL` meta-class for early-stage screening, since they are near-degenerate over short time baselines.
3. **Calibrated Probabilistic Uncertainty**: In Phase 4, the ML model should output class probabilities rather than hard decisions. Samples near the noise floor should yield high entropy (uncertainty) to trigger consensus evaluation in Phase 5.

---
*Phase 3.1 Audit Complete. All feature CSVs, diagnostic summaries, and visual plots generated under `data/synthetic/audit/`.*
