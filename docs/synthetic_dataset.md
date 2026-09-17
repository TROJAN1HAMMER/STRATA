# STRATA Synthetic Multi-Epoch InSAR Dataset & Ground-Truth Framework (Phase 3)

> **MANDATORY SCIENTIFIC DISCLAIMER**  
> *This dataset is synthetic and intended for controlled algorithm development and validation. Its parameter distributions are prototype assumptions and are not a substitute for validation against real Sentinel-1/InSAR observations.*

---

## 1. Purpose of the Synthetic Dataset

The STRATA Phase 3 Synthetic Dataset framework establishes a scientifically controlled, parameterized generation environment with explicit ground-truth decomposition. 

Prior to Phase 3, STRATA relied on six fixed benchmark scenarios (A through F). While sufficient for initial unit and regression tests, six scenarios cannot provide:
1. Statistical confidence across diverse noise levels, sampling frequencies, and velocities.
2. Boundary stress testing (weak signals near the noise floor, high-coherence atmospheric spikes).
3. Leakage-free training, validation, and test partitions for future machine learning classifiers.
4. Independent validation of the deterministic physics engine against genuine ground truth.

---

## 2. Ground-Truth Taxonomy vs. Physics Output vs. Future ML Output

STRATA maintains strict separation between three distinct operational concepts:

| Concept | Definition | Origin |
|---|---|---|
| **Ground Truth** | The exact physical generative process that synthesized the observation timeline. | Assigned at generation time from known physical parameters. |
| **Physics Output** | Deterministic inference produced by the rule-based physics engine (`PhysicsInSARConsistencyEngine`). | Evaluated at runtime using InSAR observations without knowledge of ground truth. |
| **Future ML Output** | Statistical inferences from learned models (Phase 4). | Inferred from features extracted from observations alone. |

### Ground-Truth Classes

1. **`STABLE`**: Physical deformation is identically zero; observed measurements represent zero-mean instrument and thermal noise.
2. **`STRUCTURAL_MONOTONIC`**: Progressive linear structural settlement or uplift ($d(t) = v \cdot t$).
3. **`STRUCTURAL_ACCELERATING`**: Expanding structural deformation following quadratic kinematics ($d(t) = v_0 t + 0.5 a t^2$).
4. **`SEASONAL_ENVIRONMENTAL`**: Periodic, bounded cyclic movement driven by thermal or hydrologic loading ($d(t) = A \sin(2\pi t / T + \phi)$) with zero net structural degradation.
5. **`ATMOSPHERIC_TRANSIENT`**: Zero physical deformation, but contaminated on isolated epochs by tropospheric water-vapor delays / phase screens that immediately revert to baseline.
6. **`LOW_QUALITY`**: Severe radar decorrelation ($\gamma < 0.25$) and phase noise where physical signal cannot be reliably resolved.
7. **`TEMPORALLY_INCONSISTENT`**: Erratic, unphysical displacement jumps and high-frequency reversals incompatible with smooth structural, seasonal, or atmospheric signatures.

---

## 3. Synthetic Physical Model & Component Decomposition

Every generated epoch satisfies the linear superposition identity:

$$\text{observed\_displacement}(t) = d_{\text{struct}}(t) + d_{\text{env}}(t) + d_{\text{atm}}(t) + \epsilon_{\text{noise}}(t)$$

Within the dataset, this decomposition is preserved per-epoch in the isolated container `ground_truth`:
* `true_structural_displacement_mm`: Actual physical structural movement.
* `true_environmental_displacement_mm`: Periodic thermal/environmental movement.
* `true_atmospheric_displacement_mm`: Tropospheric delay spike.
* `true_noise_mm`: Zero-mean Gaussian measurement noise.

Mathematical reconstruction identity:
$$|\text{observed\_displacement\_mm} - (\text{true\_structural} + \text{true\_environmental} + \text{true\_atmospheric} + \text{true\_noise})| < 10^{-4}\text{ mm}$$

### API Safety & Leakage Prevention
The isolated `ground_truth` sub-container is stripped when transforming epochs to public InSAR payloads (`to_public_observation_dict()`). Ground-truth fields never enter production API contracts or feature extractors.

---

## 4. Parameter Ranges & Prototype Assumptions

All parameters are centrally defined in `backend/app/services/synthetic/parameters.py`:

| Parameter | Prototype Range | Unit | Note |
|---|---|:---:|---|
| Epoch Count | $6 - 20$ | epochs | Variable sequence lengths |
| Temporal Spacing | $6.0 - 24.0$ | days | Mimics Sentinel-1 constellation revisit baselines |
| Radar Incidence Angle | $25.0 - 45.0$ | degrees | Typical C-band orbital geometry |
| Nominal Coherence ($\gamma$) | $0.65 - 0.95$ | unitless | Coherent civil infrastructure |
| Degraded Coherence ($\gamma$) | $0.10 - 0.24$ | unitless | Decorrelated noise floor |
| Measurement Noise ($\sigma$) | $0.5 - 3.0$ | mm | Zero-mean Gaussian phase error |
| Monotonic Velocity ($v$) | $0.8 - 12.0$ | mm/year | Realistic settlement / heave |
| Initial Velocity ($v_0$) | $0.5 - 5.0$ | mm/year | Base rate before acceleration |
| Acceleration ($a$) | $0.8 - 8.0$ | mm/year$^2$ | Progressive creep acceleration |
| Seasonal Amplitude ($A$) | $2.0 - 10.0$ | mm | Peak cyclic amplitude |
| Seasonal Period ($T$) | $180.0 - 365.25$ | days | Annual / semi-annual cycles |
| Atmospheric Spike Magnitude | $3.0 - 15.0$ | mm | Transient tropospheric anomalies |

---

## 5. Train / Validation / Test Partitioning

Dataset partitioning guarantees:
1. **Zero Sequence Leakage**: Every sequence belongs to exactly one split. Epochs from the same sequence are never split across train, validation, and test.
2. **Disjoint Sample IDs**: `train`, `validation`, and `test` sample IDs have null intersection.
3. **Deterministic Partitioning**: Using seed `42`, 500 samples per class are partitioned into:
   * **Train (70%)**: 2,450 sequences (350 per class)
   * **Validation (15%)**: 525 sequences (75 per class)
   * **Test (15%)**: 525 sequences (75 per class)
   * **Total**: 3,500 sequences

---

## 6. Difficult Edge Cases

The generator includes controlled challenging scenarios:
* **Weak structural deformation near the noise floor**: Velocity $\sim 0.5 - 1.0$ mm/yr with noise $\sim 1.5$ mm.
* **Seasonal deformation with high noise**: Noise creates false non-monotonic fluctuations.
* **Atmospheric spike superimposed on structural trend**: Transient tropospheric anomaly on top of true structural displacement.
* **High-coherence atmospheric anomaly**: Spikes occurring on stable targets with high spatial coherence.
* **Low-coherence structural deformation**: True settlement occurring under partially decorrelated radar returns.
* **Short sequences**: Sequences with only 6 epochs where trend persistence is difficult to establish.

---

## 7. Physics Engine Benchmark Findings (Test Split)

Running `PhysicsInSARConsistencyEngine` on the test split (525 sequences) yielded the following empirical baseline:

### Summary Metrics
* **Total Evaluated**: 525 sequences
* **Overall Physics Accuracy**: **40.95%** (215 / 525)
* **False Structural Classifications**: 15 sequences
* **Missed Structural Classifications**: 123 sequences

### Per-Class Results
| Ground Truth Class | Test Count | Correct | Accuracy | Expected Physics Classification |
|---|:---:|:---:|:---:|---|
| `LOW_QUALITY` | 75 | 75 | **100.00%** | `LOW_QUALITY` |
| `ATMOSPHERIC_TRANSIENT` | 75 | 56 | **74.67%** | `ATMOSPHERICALLY_SUSPECT` |
| `TEMPORALLY_INCONSISTENT` | 75 | 33 | **44.00%** | `TEMPORALLY_INCONSISTENT` |
| `SEASONAL_ENVIRONMENTAL` | 75 | 23 | **30.67%** | `SEASONALLY_SUSPECT` |
| `STRUCTURAL_MONOTONIC` | 75 | 15 | **20.00%** | `STRUCTURALLY_CONSISTENT` |
| `STRUCTURAL_ACCELERATING`| 75 | 12 | **16.00%** | `STRUCTURALLY_CONSISTENT` |
| `STABLE` | 75 | 1 | **1.33%** | `STABLE_NO_SIGNIFICANT_DEFORMATION` |

### Confusion Matrix
```text
Ground Truth               | STABLE | STRUCT | ATMOSP | SEASON | INCONS | LOW_Q | INSUFF
---------------------------------------------------------------------------------------
STABLE                     |      1 |      3 |      3 |     47 |     21 |     0 |      0
STRUCTURAL_MONOTONIC       |      2 |     15 |      1 |     32 |     24 |     1 |      0
STRUCTURAL_ACCELERATING    |      3 |     12 |      1 |     36 |     23 |     0 |      0
SEASONAL_ENVIRONMENTAL     |      0 |     11 |      5 |     23 |     36 |     0 |      0
ATMOSPHERIC_TRANSIENT      |      0 |      0 |     56 |     18 |      1 |     0 |      0
LOW_QUALITY                |      0 |      0 |      0 |      0 |      0 |    75 |      0
TEMPORALLY_INCONSISTENT    |      0 |      1 |     37 |      4 |     33 |     0 |      0
```

---

## 8. Scientific Limitations & Key Failure Modes Discovered

The benchmark achieved its exact scientific objective: exposing the deterministic engine's boundary conditions and failure modes rather than creating a false illusion of perfection.

### Discovered Limitations:
1. **Zero-Crossing Heuristic vs. Stable Measurement Noise**:
   * *Observed*: 47 out of 75 `STABLE` sequences were misclassified as `SEASONALLY_SUSPECT`.
   * *Mechanism*: Independent Gaussian noise ($\sigma \sim 1.0 - 2.0$ mm) around a 0.0 mm baseline naturally crosses zero several times over 10–20 epochs. The Phase 2.1 zero-crossing detector interpreted these random zero-crossings with bounded amplitude as a low-amplitude seasonal oscillation.
2. **Partial-Period Observation Window on Seasonal Cycles**:
   * *Observed*: 11 `SEASONAL_ENVIRONMENTAL` sequences were classified as `STRUCTURALLY_CONSISTENT`.
   * *Mechanism*: When an observation window (e.g., 8–10 epochs spanning 120 days) captures only the rising or falling flank of an annual cycle (period $T = 365$ days), the observed displacement appears strictly monotonic and persistent. Without observing the seasonal reversal, no physical model can distinguish it from genuine structural movement.
3. **Signal-to-Noise Ratio (SNR) in Weak Structural Deformation**:
   * *Observed*: Slow monotonic settlement ($0.8 - 2.0$ mm/yr) over 6–12 epochs resulted in total true displacements ($\sim 0.5 - 1.0$ mm) below the measurement noise standard deviation ($\sigma \sim 1.5 - 2.5$ mm).
   * *Mechanism*: Noise-induced direction reversals caused the physics engine to flag the sequence as `TEMPORALLY_INCONSISTENT` or `SEASONALLY_SUSPECT`.

These findings confirm the STRATA architecture thesis: **a deterministic rule-based physics engine alone cannot solve satellite SHM across all noise regimes.** Combining physics-based heuristics with machine learning classification and multi-engine consensus is indispensable.
