# STRATA — Cross-Model Consensus & Evidence Fusion (Phase 5)

## 1. Purpose & Core Principles

The STRATA Consensus Engine synthesizes two independently generated analytical interpretations of multi-epoch InSAR (Interferometric Synthetic Aperture Radar) observation sequences:
1. **Machine Learning Deformation Classifier** (`MLDeformationClassifier`): A statistical model outputting calibrated class probabilities, confidence, and Shannon uncertainty entropy.
2. **Deterministic Physics InSAR Consistency Engine** (`PhysicsInSARConsistencyEngine`): A rules-based, physics-informed engine evaluating kinematic persistence, interferometric quality, and cyclic environmental/atmospheric signatures.

### Core Scientific Principle
Simple weighted averaging ($\frac{1}{2} \text{ML} + \frac{1}{2} \text{Physics}$) is strictly prohibited. The consensus engine operates under the foundational principle:

$$\text{AGREEMENT} \longrightarrow \text{increased analytical confidence}$$
$$\text{DISAGREEMENT} \longrightarrow \text{reduced confidence / increased uncertainty}$$

Both analytical engines remain completely decoupled and independently callable. Neither the ML classifier nor the physics consistency engine are modified or fused internally.

> [!IMPORTANT]
> **Mandatory Scientific Disclaimers**:
> 1. *"The Phase 5 consensus formulation is a transparent prototype and its coefficients and thresholds have not yet been empirically validated on real-world InSAR data."*
> 2. *"Consensus confidence represents confidence in the analytical interpretation of available evidence; it is not a probability of structural failure and does not constitute an engineering safety determination."*

---

## 2. Architecture & Evidence Flow

```
                      ┌─────────────────────────┐
                      │  ML Deformation Engine  │
                      └────────────┬────────────┘
                                   │ Calibrated Class
                                   │ Probabilities P_ml
InSAR Observation                  ▼
Sequence          ───► ┌─────────────────────────┐
(Multi-Epoch)          │    Consensus Engine     │ ──► ConsensusAssessment
                       │                         │     (Class, Confidence, Flags,
                       │  - Taxonomy Mapping     │      Quality, Persistence,
                       │  - Agreement Mass       │      Explanation, Provenance)
                       │  - Conflict Suppression │
                       │  - Bounded Fusion       │
                       └───────────▲─────────────┘
                                   │ Deterministic Kinematic
                                   │ & Environmental Evidence
                      ┌────────────┴────────────┐
                      │   Physics Consistency   │
                      │         Engine          │
                      └─────────────────────────┘
```

---

## 3. ML & Physics Taxonomy Mapping

Because the machine learning classifier and the deterministic physics consistency engine use distinct classification vocabularies, STRATA establishes an explicit semantic mapping layer into a unified consensus vocabulary (`backend/app/services/consensus/mapping.py`).

| Semantic Consensus Category (`ConsensusCategory`) | ML Classifier Class (`GroundTruthClass`) | Physics Engine Classification (`PhysicsClassification`) |
| :--- | :--- | :--- |
| `STABLE` | `STABLE` | `STABLE_NO_SIGNIFICANT_DEFORMATION` |
| `STRUCTURAL` | `STRUCTURAL_MONOTONIC`, `STRUCTURAL_ACCELERATING` | `STRUCTURALLY_CONSISTENT` |
| `SEASONAL` | `SEASONAL_ENVIRONMENTAL` | `SEASONALLY_SUSPECT` |
| `ATMOSPHERIC` | `ATMOSPHERIC_TRANSIENT` | `ATMOSPHERICALLY_SUSPECT` |
| `LOW_QUALITY` | `LOW_QUALITY` | `LOW_QUALITY` |
| `TEMPORALLY_INCONSISTENT` | `TEMPORALLY_INCONSISTENT` | `TEMPORALLY_INCONSISTENT` |
| `INSUFFICIENT_EVIDENCE` | *(N/A - ML does not predict missing data)* | `INSUFFICIENT_EVIDENCE` |

### Probability Mass Aggregation ($P_{ml}$)
For any consensus category $C \in \text{ConsensusCategory}$, the total ML probability mass is computed by summing the constituent ML class probabilities:

$$P_{ml}(C) = \sum_{m \in \text{MLClasses}, \text{map}(m) = C} P_{ml}(m)$$

*Example*: $P_{ml}(\text{STRUCTURAL}) = P(\text{STRUCTURAL\_MONOTONIC}) + P(\text{STRUCTURAL\_ACCELERATING})$.

---

## 4. Agreement Calculation & Disagreement Penalty

### Continuous Agreement Score
Rather than comparing discrete hard labels, the consensus engine calculates agreement as the continuous ML probability mass allocated to the semantic category identified by the deterministic physics engine ($C_{phys}$):

$$\text{agreement\_score} = \begin{cases} 0.0 & \text{if } C_{phys} = \text{INSUFFICIENT\_EVIDENCE} \\ P_{ml}(C_{phys}) & \text{otherwise} \end{cases}$$

### Disagreement Penalty
The disagreement penalty provides an inverse, bounded linear measure:

$$\text{disagreement\_penalty} = 1.0 - \text{agreement\_score}$$

- $\text{agreement} = 1.00 \implies \text{penalty} = 0.00$
- $\text{agreement} = 0.75 \implies \text{penalty} = 0.25$
- $\text{agreement} = 0.20 \implies \text{penalty} = 0.80$
- $\text{agreement} = 0.00 \implies \text{penalty} = 1.00$

### Diagnostic Condition Flags

| Threshold Condition | Generated Diagnostic Flag |
| :--- | :--- |
| $\text{agreement\_score} \ge 0.80$ | `STRONG_MODEL_AGREEMENT`, `MODEL_AGREEMENT` |
| $0.60 \le \text{agreement\_score} < 0.80$ | `MODEL_AGREEMENT` |
| $0.15 \le \text{agreement\_score} < 0.30$ | `MODEL_DISAGREEMENT` |
| $\text{agreement\_score} < 0.15$ | `STRONG_MODEL_DISAGREEMENT`, `MODEL_DISAGREEMENT` |
| $C_{phys} = \text{SEASONAL} \land P_{ml}(\text{STRUCTURAL}) \ge 0.40$ | `ENVIRONMENTAL_STRUCTURAL_CONFLICT` |
| $C_{phys} = \text{ATMOSPHERIC} \land P_{ml}(\text{STRUCTURAL}) \ge 0.40$ | `ATMOSPHERIC_STRUCTURAL_CONFLICT` |
| $C_{phys} = \text{LOW\_QUALITY} \lor P_{ml}(\text{LOW\_QUALITY}) \ge 0.50$ | `LOW_QUALITY_EVIDENCE` |
| $C_{phys} = \text{INSUFFICIENT\_EVIDENCE}$ | `INSUFFICIENT_EVIDENCE_SUPPRESSION` |

---

## 5. Evidence Quality Score

The evidence quality score evaluates confidence in the **available observational data** (coherence, phase stability, epoch count, satellite radar geometry):

$$\text{evidence\_quality\_score} = 0.50 \cdot Q_{meas} + 0.30 \cdot Q_{suff} + 0.20 \cdot Q_{geom}$$

- $Q_{meas} \in [0.0, 1.0]$: Interferometric coherence and phase quality from measurement evidence.
- $Q_{suff} \in [0.0, 1.0]$: Temporal data sufficiency from epoch distribution.
- $Q_{geom} \in \{1.0 \text{ (valid)}, 0.7 \text{ (weak)}, 0.3 \text{ (invalid)}\}$: Geometry status.
- *Atmospheric Penalty*: If atmospheric suspect score $> 0.60$, raw quality is multiplied by $0.85$ to account for phase screen contamination.

> [!CAUTION]
> The evidence quality score measures data reliability. It does **not** indicate whether an infrastructure asset is safe, stable, or at risk of failure.

---

## 6. Temporal Persistence Score

STRATA evaluates multi-epoch InSAR sequences over time. The temporal persistence score measures kinematic continuity:

$$\text{persistence\_score} = \left(0.45 \cdot \text{persistence} + 0.35 \cdot \text{directional\_consistency} + 0.20 \cdot \text{rate\_consistency}\right) \times \left(1.0 - 0.50 \cdot \text{abrupt\_inconsistency}\right)$$

### Critical Scientific Principle: Persistence $\neq$ Structural Deformation
A cyclical seasonal oscillation can exhibit high temporal persistence across multi-year baselines while being entirely environmental. Therefore, **temporal persistence serves as an evidence-strength modifier**, not as an independent classifier of structural failure.

---

## 7. Bounded Confidence Formulation

Confidence fusion combines base predictions with bounded scaling factors to avoid catastrophic confidence collapse:

$$\text{base\_confidence} = 0.60 \cdot \text{ml\_confidence} + 0.40 \cdot \text{physics\_evidence\_strength}$$

$$\text{agreement\_modifier} = 0.50 + 0.50 \cdot \text{agreement\_score} \quad \in [0.50, 1.00]$$
$$\text{quality\_modifier} = 0.40 + 0.60 \cdot \text{evidence\_quality\_score} \quad \in [0.40, 1.00]$$
$$\text{temporal\_modifier} = 0.70 + 0.30 \cdot \text{temporal\_persistence\_score} \quad \in [0.70, 1.00]$$

$$\text{fused\_confidence} = \text{base\_confidence} \times \text{agreement\_modifier} \times \text{quality\_modifier} \times \text{temporal\_modifier}$$

### Conflict and Quality Caps
- `STRONG_MODEL_DISAGREEMENT`: $\text{fused} \leftarrow \text{fused} \times 0.70$
- `ENVIRONMENTAL_STRUCTURAL_CONFLICT` or `ATMOSPHERIC_STRUCTURAL_CONFLICT`: $\text{fused} \leftarrow \text{fused} \times 0.75$
- `LOW_QUALITY` ceiling: $\min(\text{fused}, 0.35)$
- `INSUFFICIENT_EVIDENCE` ceiling: $\min(\text{fused}, 0.25)$
- Clamping range: $[0.05, 0.99]$.

---

## 8. Decision Hierarchy & Conflict Resolution

The consensus decision is governed by an explicit priority hierarchy (`backend/app/services/consensus/decision.py`):

1. **INSUFFICIENT_EVIDENCE**: If observation epochs $< 5$ or physics indicates insufficient data, consensus must remain `INSUFFICIENT_EVIDENCE`. Absence of evidence cannot be substituted by ML.
2. **LOW_QUALITY**: If physics indicates `LOW_QUALITY`, ML low-quality mass $\ge 0.50$, or evidence quality $< 0.35$, consensus is `LOW_QUALITY`. Degraded radar data cannot support structural or environmental conclusions.
3. **TEMPORALLY_INCONSISTENT**: If physics and ML both confirm temporal volatility, consensus is `TEMPORALLY_INCONSISTENT`.
4. **ENVIRONMENTAL vs. STRUCTURAL CONFLICT**: If physics identifies physical cyclic reversals (`SEASONAL`) but ML predicts structural deformation, **consensus defends the environmental baseline (`SEASONAL`)**; structural consensus is suppressed and conflict flags are attached.
5. **ATMOSPHERIC vs. STRUCTURAL CONFLICT**: If physics identifies an isolated phase delay spike (`ATMOSPHERIC`) while ML predicts step displacement, **consensus suppresses structural claims** and classifies as `ATMOSPHERIC`.
6. **STRUCTURAL CONSENSUS**: Requires **bipartite agreement**:
   $$P_{ml}(\text{STRUCTURAL}) \ge 0.50 \quad \text{AND} \quad C_{phys} = \text{STRUCTURAL}$$
7. **SEASONAL CONSENSUS**: $C_{phys} = \text{SEASONAL} \land P_{ml}(\text{SEASONAL}) \ge 0.35$.
8. **ATMOSPHERIC CONSENSUS**: $C_{phys} = \text{ATMOSPHERIC} \land P_{ml}(\text{ATMOSPHERIC}) \ge 0.35$.
9. **STABLE CONSENSUS**: $C_{phys} = \text{STABLE} \land P_{ml}(\text{STABLE}) \ge 0.40$.
10. **UNRESOLVED CONFLICT FALLBACK**: Defaults conservatively to `INSUFFICIENT_EVIDENCE` with reduced confidence and diagnostic disagreement flags.

---

## 9. Ground-Truth Leakage Firewall

The consensus engine incorporates strict programmatic protection against synthetic ground-truth leakage (`_verify_no_ground_truth_leakage`). Any input dictionary, extra keyword argument, or nested object containing hidden generator parameters is immediately rejected:
- `true_structural_displacement_mm`, `true_environmental_displacement_mm`, `true_atmospheric_displacement_mm`, `true_noise_mm`
- `ground_truth_class`, `seasonal_amplitude_mm`, `seasonal_period_days`, `linear_velocity_mm_yr`, `acceleration_mm_yr2`
- `step_epoch_idx`, `step_magnitude_mm`, `noise_std_mm`, `spatial_wavelength_m`, `spike_magnitude_mm`

---

## 10. API Specification

### Endpoint: `POST /api/v1/analysis/consensus/{observation_id}`
Executes stateless cross-model consensus evaluation on the historical multi-epoch sequence terminating at `observation_id`.

**Response Schema (`ConsensusAssessment`)**:
```json
{
  "consensus_class": "STRUCTURAL",
  "consensus_confidence": 0.7412,
  "agreement_score": 0.8500,
  "disagreement_penalty": 0.1500,
  "evidence_quality_score": 0.8850,
  "temporal_persistence_score": 0.8650,
  "ml_contribution": {
    "predicted_class": "STRUCTURAL_MONOTONIC",
    "predicted_category": "STRUCTURAL",
    "confidence": 0.8500,
    "entropy": 0.2500,
    "probabilities": { ... },
    "category_masses": { ... },
    "model_version": "strata_ml_v0_1_0"
  },
  "physics_contribution": {
    "classification": "STRUCTURALLY_CONSISTENT",
    "category": "STRUCTURAL",
    "evidence_strength": 0.8500,
    "overall_confidence": 0.8500,
    "measurement_quality_score": 0.9000,
    "data_sufficiency": 0.9000,
    "epoch_count": 15,
    "engine_version": "strata_physics_v0.2.1"
  },
  "explanation": "Strong cross-model agreement observed...",
  "flags": [
    "MODEL_AGREEMENT",
    "STRONG_MODEL_AGREEMENT"
  ],
  "model_versions": {
    "consensus_engine": "strata_consensus_v0.1.0",
    "ml_model": "strata_ml_v0_1_0",
    "physics_engine": "strata_physics_v0.2.1"
  },
  "consensus_engine_version": "strata_consensus_v0.1.0",
  "scientific_disclaimer": "STRATA Cross-Model Consensus combines independent machine-learning predictions..."
}
```

---

## 11. Validation Scenarios & Verification Matrix

The consensus engine was verified across 21 dedicated unit tests in `backend/tests/test_consensus.py`:

| Scenario | ML Behavior | Physics Classification | Expected Consensus Class | Expected Flags / Behavior | Test Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **A. Structural Agreement** | Structural $P_{ml} = 0.85$ | `STRUCTURALLY_CONSISTENT` | `STRUCTURAL` | `STRONG_MODEL_AGREEMENT`, high confidence | **PASSED** |
| **B. Seasonal Agreement** | Seasonal $P_{ml} = 0.82$ | `SEASONALLY_SUSPECT` | `SEASONAL` | `STRONG_MODEL_AGREEMENT`, high confidence | **PASSED** |
| **C. Atmospheric Agreement** | Atmospheric $P_{ml} = 0.80$ | `ATMOSPHERICALLY_SUSPECT` | `ATMOSPHERIC` | `MODEL_AGREEMENT` | **PASSED** |
| **D. Structural vs. Seasonal** | Structural $P_{ml} = 0.85$ | `SEASONALLY_SUSPECT` | `SEASONAL` *(not structural!)* | `ENVIRONMENTAL_STRUCTURAL_CONFLICT`, confidence penalty | **PASSED** |
| **E. Structural vs. Atmospheric** | Structural $P_{ml} = 0.85$ | `ATMOSPHERICALLY_SUSPECT` | `ATMOSPHERIC` *(not structural!)* | `ATMOSPHERIC_STRUCTURAL_CONFLICT`, confidence penalty | **PASSED** |
| **F. Low Quality Evidence** | Structural $P_{ml} = 0.90$ | `LOW_QUALITY` | `LOW_QUALITY` | `LOW_QUALITY_EVIDENCE`, confidence $\le 0.35$ | **PASSED** |
| **G. Insufficient Evidence** | Structural $P_{ml} = 0.80$ | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE` | `INSUFFICIENT_EVIDENCE_SUPPRESSION`, confidence $\le 0.25$ | **PASSED** |
| **H. Stable Agreement** | Stable $P_{ml} = 0.85$ | `STABLE_NO_SIGNIFICANT_DEFORMATION` | `STABLE` | `STRONG_MODEL_AGREEMENT` | **PASSED** |
| **Monotonicity (Agreement)** | Varying $P_{ml}$ | Fixed | Strictly monotonic | Agreement increases with probability mass | **PASSED** |
| **Monotonicity (Quality)** | Fixed | Varying Quality | Strictly monotonic | Confidence increases with evidence quality | **PASSED** |
| **Agreement vs Disagreement** | High Agreement vs Disagree | Identical Evidence | $\Delta_{\text{conf}} > 0.15$ | Agreement yields substantially higher confidence | **PASSED** |
| **Firewall Leakage** | Forbidden attributes passed | - | `ValueError` raised | Blocks hidden generator parameters | **PASSED** |
| **Explanation Safety** | Output generated | - | Clean explanation | Omits "collapse predicted", "structure unsafe" | **PASSED** |
| **API Endpoint** | Full observation sequence | Independent engines | 200 OK | End-to-end consensus response | **PASSED** |
