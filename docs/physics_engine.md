# STRATA Physics-Based InSAR Consistency Engine (Phase 2 & 2.1)

## 1. Purpose & Core Scientific Principle

The **STRATA Physics-Based InSAR Consistency Engine** is a deterministic, explainable scientific component designed to evaluate whether multi-epoch satellite Interferometric Synthetic Aperture Radar (InSAR) deformation observations are consistent with a persistent structural deformation process versus periodic environmental/seasonal cycles, atmospheric artifacts, radar decorrelation, geometric limitations, or temporal volatility.

> **CORE SCIENTIFIC PRINCIPLE (PHASE 2.1 REFINEMENT)**  
> **Temporal persistence alone does not establish structural deformation.**  
> A cyclical or seasonal deformation process (such as thermal expansion of a bridge or reservoir level fluctuation on a dam) can exhibit high coherence, strong persistence, and regular repeatability without indicating progressive structural deterioration. The engine must explicitly distinguish monotonic/progressive deformation from periodic or environmentally correlated deformation.

> **CRITICAL SCIENTIFIC DISCLAIMER**  
> * `STRUCTURALLY_CONSISTENT` indicates that the observed multi-epoch interferometric signal satisfies mathematical and kinematic criteria consistent with a continuous structural deformation process (e.g. progressive subsidence or creep). **It does NOT indicate that the civil structure is unsafe, in danger of collapse, or structurally damaged.**  
> * `STABLE_NO_SIGNIFICANT_DEFORMATION` indicates that displacements remain within millimeter measurement noise margins. Absence of significant deformation is not classified as structural deformation.  
> * `SEASONALLY_SUSPECT` indicates that observed movements are cyclical and consistent with environmental thermal/loading oscillations.  
> * `ATMOSPHERICALLY_SUSPECT` indicates that the signature aligns with tropospheric phase screen delay patterns, not that atmospheric contamination is conclusively proven.

---

## 2. Distinguishing Evidence Types

To maintain scientific integrity, the engine maintains strict separation between four fundamentally different scientific phenomena:

```text
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                EVIDENCE TAXONOMY                                       │
├──────────────────────────┬─────────────────────────────────────────────────────────────┤
│ Evidence Type            │ Physical Meaning                                            │
├──────────────────────────┼─────────────────────────────────────────────────────────────┤
│ Measurement Quality      │ Reliability and phase noise level of the radar observations │
│ Atmospheric Suspicion    │ Tropospheric water-vapor phase delays (transient spikes)   │
│ Environmental Consistency│ Cyclic/seasonal reversible thermal or hydraulic expansion   │
│ Structural Consistency   │ Non-periodic, progressive, irreversible structural movement │
└──────────────────────────┴─────────────────────────────────────────────────────────────┘
```

---

## 3. Evidence Dimensions

Rather than collapsing all measurements into an opaque black-box score, the engine independently computes and retains six separate evidence dimensions:

```text
                                ObservationSequence
                                         │
        ┌───────────────┬───────────┬────┴────┬───────────┬───────────────┬───────────────┐
        ↓               ↓           ↓         ↓           ↓               ↓               ↓
   Measurement      Geometry    Kinematic  Temporal   Atmospheric   Environmental    Decision
     Quality        Evidence    Evidence   Evidence     Suspect       Evidence       Engine
```

### 1. Measurement Quality Evidence (`quality.py`)
* **Coherence ($\gamma$):**
  * $\gamma \ge 0.70$: High coherence, strong interferometric phase stability (literature standard).
  * $0.40 \le \gamma < 0.70$: Moderate coherence, acceptable measurement confidence.
  * $0.25 \le \gamma < 0.40$: Degraded coherence, elevated phase noise risk.
  * $\gamma < 0.25$: Severely decorrelated epoch, noise-dominated.
* **Phase Quality Metric:** Validates phase stability and flags unwrapping artifact risks.
* **Missing Value Penalty:** Deducts quality score when critical fields (incidence angle, displacement) are omitted.

### 2. Geometry Evidence (`geometry.py`)
* **Radar Incidence Angle ($\theta$):**
  * Nominal spaceborne SAR range: $15.0^\circ \le \theta \le 60.0^\circ$ (`VALID_GEOMETRY`).
  * Outside nominal range: `WEAK_GEOMETRY` (reduced sensitivity or steep shadow/layover).
  * $\theta \le 0^\circ$ or $\theta \ge 90^\circ$: `INVALID_GEOMETRY`.
* **LOS to Vertical Projection:**
  $$d_{\text{vert}} = \frac{d_{\text{los}}}{\cos(\theta)}$$
  Vertical sensitivity factor is $\cos(\theta)$. Both quantities are reported separately.

### 3. Kinematic Evidence (`kinematics.py`)
* Evaluates consistency between discrete epoch displacements and reported instantaneous velocities:
  $$\Delta t = \frac{t_{i+1} - t_i}{365.25 \times 86400} \quad (\text{years})$$
  $$v_{\text{empirical}} = \frac{d_{i+1} - d_i}{\Delta t}$$
  $$\text{Residual} = |v_{\text{empirical}} - v_{\text{reported}}|$$
  $$\text{Kinematic Consistency} = \frac{1.0}{1.0 + \frac{\text{Mean Residual}}{\text{Scale}}}$$

### 4. Multi-Epoch Temporal Evidence (`temporal.py`)
* **Persistence:** Proportion of epochs where $|d| \ge 1.0\text{ mm}$ (stable threshold).
* **Directional Consistency:** Proportion of active epochs sharing the dominant displacement sign (uplift vs subsidence).
* **Rate Consistency:** Inverse normalized spread of incremental epoch-to-epoch velocities.
* **Abrupt Inconsistency:** Detects isolated jump-and-reversal events ($\Delta d_1 \cdot \Delta d_2 < 0$ with $|\Delta d| \ge 5.0\text{ mm}$).
* **Trend Pattern:** Categorized into `STABLE`, `MONOTONIC`, `ACCELERATING`, `TRANSIENT`, `PERIODIC_SEASONAL`, `INSUFFICIENT_DATA`, or `VOLATILE`.

### 5. Atmospheric-Suspect Evidence (`atmospheric.py`)
* **Transient Spikes:** Detects sharp excursions at epoch $t$ ($|d_t - d_{t-1}| \ge 6.0\text{ mm}$ and $|d_t - d_{t+1}| \ge 6.0\text{ mm}$) where baseline immediately recovers ($|d_{t+1} - d_{t-1}| \le 3.0\text{ mm}$).
* **Explicit Indicators:** Evaluates tropospheric turbulence flags (e.g. `HIGH_TROPOSPHERIC_TURBULENCE`).
* Reports `ATMOSPHERIC_DATA_UNAVAILABLE` when atmospheric data is not provided rather than assuming zero atmospheric contamination.

### 6. Environmental Evidence (`environmental.py`)
* **Zero-Crossing Frequency:** Detects repeated transitions across baseline ($> 2$ sign changes across $\ge 5$ epochs).
* **Reversal Consistency:** Measures symmetry between positive and negative excursion durations.
* **Bounded Amplitude:** Verifies that cyclic deformation remains within typical seasonal civil bounds ($\le 25\text{ mm}$).
* **Smoothness:** Distinguishes smooth sinusoidal curves from abrupt 1-epoch tropospheric spikes.

---

## 4. Conservative Classification Hierarchy

The engine executes a deterministic decision tree designed to prevent overconfident claims:

```text
1. Low Measurement Quality / Decorrelation (< 0.35)
   └──> LOW_QUALITY

2. Insufficient Observations (< 3 epochs or data sufficiency < 0.50)
   └──> INSUFFICIENT_EVIDENCE

3. Strong Atmospheric / Transient Evidence (score >= 0.55 or spike detected)
   └──> ATMOSPHERICALLY_SUSPECT

4. Periodic / Seasonal Evidence (periodicity detected or seasonal strength >= 0.60)
   └──> SEASONALLY_SUSPECT

5. Stable Signal Without Significant Deformation (displacements within noise margin)
   └──> STABLE_NO_SIGNIFICANT_DEFORMATION

6. Temporal Inconsistency (abrupt jumps / volatile trajectory)
   └──> TEMPORALLY_INCONSISTENT

7. Persistent Non-Periodic Deformation (monotonic or accelerating, persistence >= 0.50)
   └──> STRUCTURALLY_CONSISTENT
```

---

## 5. Distinction: Literature Standard vs Prototype Assumptions

| Parameter / Threshold | Classification | Rationale |
|---|---|---|
| Coherence $\ge 0.70$ (High) | Literature Standard | Standard in spaceborne interferometry for reliable phase unwrapping. |
| Coherence $< 0.25$ (Noise floor) | Literature Standard | Decorrelation noise dominates above phase variance threshold. |
| Incidence Angle $[15^\circ, 60^\circ]$ | Literature Standard | Nominal geometric operating envelope for Sentinel-1 / TerraSAR-X. |
| $d_{\text{vert}} = d_{\text{los}} / \cos(\theta)$ | Literature Standard | Direct geometric decomposition for 1D single-orbit Line-of-Sight. |
| Stable noise margin ($1.0\text{ mm}$) | PROTOTYPE_ASSUMPTION | Typical empirical standard error for multi-temporal PSI over hard targets. |
| Abrupt jump threshold ($5.0\text{ mm}$) | PROTOTYPE_ASSUMPTION | Empirical threshold for single 12-day epoch step to flag phase turbulence. |
| Transient spike threshold ($6.0\text{ mm}$) | PROTOTYPE_ASSUMPTION | Empirical spike detection threshold for atmospheric phase delay. |
| Seasonal amplitude bound ($25.0\text{ mm}$) | PROTOTYPE_ASSUMPTION | Literature-derived bound for non-destructive thermal civil expansion. |

---

## 6. Synthetic Benchmark Scenarios & Evaluation

All benchmark datasets are located in `data/synthetic/scenarios.json`:

| Scenario ID | Description | Epochs | Output Classification | Key Distinguishing Feature |
|---|---|:---:|---|---|
| **Scenario A** | Stable Structure | 5 | `STABLE_NO_SIGNIFICANT_DEFORMATION` | Displacements within noise margin ($\pm 0.3\text{ mm}$); no structural movement. |
| **Scenario B** | Persistent Structural | 5 | `STRUCTURALLY_CONSISTENT` | Monotonic negative displacement ($-2.0 \to -12.4\text{ mm}$), directional consistency $1.0$. |
| **Scenario C** | Atmospheric Anomaly | 5 | `ATMOSPHERICALLY_SUSPECT` | Sharp transient spikes ($-8.5\text{ mm}, +7.2\text{ mm}$) reverting to baseline; turbulence flag. |
| **Scenario D** | Seasonal Pattern | 10 | `SEASONALLY_SUSPECT` | Sinusoidal cycle crossing baseline; recognized as environmental, non-structural. |
| **Scenario E** | Low Quality | 5 | `LOW_QUALITY` | Coherence $< 0.22$, phase quality $0.22$, noise-dominated. |
| **Scenario F** | Accelerating Creep | 6 | `STRUCTURALLY_CONSISTENT` | Expanding step size ($-1.0 \to -24.0\text{ mm}$), accelerating trend reported transparently. |

---

## 7. Phase 3 Controlled Synthetic Dataset & Statistical Benchmark

In addition to the six individual scenarios above, Phase 3 introduced a 3,500-sequence controlled synthetic dataset partitioned into train, validation, and test splits with explicit ground-truth decomposition.

The test split evaluation benchmarked the physics engine across 525 unseen sequences across 7 physical classes. See [docs/synthetic_dataset.md](file:///Users/23MIS0012/Desktop/PROJECTS/STRATA/docs/synthetic_dataset.md) for full benchmark methodology, confusion matrix, edge cases, and discovered failure modes.

