# STRATA — System Hardening & End-to-End Integration (Phase 9)

**Document Version**: 1.0.0  
**Status**: ARCHITECTURALLY VERIFIED & LOCKED  
**Date**: September 2026  
**Analytical Pipeline Version**: `1.0.0`

---

## 1. Executive Summary & Architecture Overview

The STRATA platform (**Structural Temporal Analysis & Threat Assessment**) provides non-invasive, longitudinal Structural Health Monitoring (SHM) for civil infrastructure (bridges, dams, tunnels, retaining walls) using multi-epoch satellite Interferometric Synthetic Aperture Radar (InSAR) observations.

Phase 9 transforms the phase-separated prototype components (Phases 1 through 8.1) into an integrated, hardened, reproducible, end-to-end analytical pipeline (`STRATAAnalysisPipeline`).

### 1.1 Architectural Flowchart

```text
Raw InSAR Observation Ingestion
   │
   ▼
[Stage 1: Validation & Bounds Checking]
   │── Finiteness: NaN / Inf rejections
   │── Physical Sanity Bounds (coherence [0,1], incidence (0,90), |disp| <= 10,000 mm)
   │── Idempotency Filter (return cached result if previously analyzed)
   ▼
[Stage 2: InSAR Normalization & Preservation]
   │── LOS to Vertical projection preservation
   │── Zero hallucination of missing geometry
   ▼
[Stage 3: Historical Sequence Assembly]
   │── Monotonic chronological query for infrastructure asset
   │── Timezone normalization (strictly UTC-aware)
   ▼
[Stage 4: Frozen ML Deformation Classifier] ─── (Decoupled Engine)
   │── Statistical & spectral feature extraction
   │── 7-class deformation probabilities (Entropy, Softmax confidence)
   ▼
[Stage 5: Deterministic Physics Consistency Engine] ─── (Decoupled Engine)
   │── Kinematic plausibility & spatio-temporal coherence
   │── Thermal & environmental correlation analysis
   ▼
[Stage 6: Cross-Model Consensus Fusion] ─── (Decoupled Engine)
   │── Agreement scoring (Increased confidence on concurrence)
   │── Disagreement penalization (Uncertainty on divergence)
   ▼
[Stage 7: Multi-Epoch Temporal Kinematics & Guard] ─── (Decoupled Engine)
   │── Velocity slope, trajectory continuity, apparent acceleration
   │── Scientific baseline guard (acceleration suppressed on stable baseline)
   ▼
[Stage 8: Infrastructure-Specific Risk Characterization] ─── (Decoupled Engine)
   │── 9-step decision hierarchy (Firewalled against ground-truth leakage)
   │── Non-alarmist civil engineering explanation & disclaimer
   ▼
[Stage 9: Atomic DB Persistence & Tamper-Evident Chronology]
   │── AnalysisResult record creation
   │── Canonical JSON hashing: SHA-256(previous_hash || payload_hash)
   │── Commit Transaction (Rollback on any stage failure)
   ▼
Completed Pipeline Result (HTTP 200/201 Response)
```

### 1.2 Independence Boundaries

1. **ML Classifier Independence**: The Random Forest classifier functions as a pure mathematical pattern recognizer trained on observable features. It does not inspect civil structural thresholds, historical maintenance records, or physics consistency rules.
2. **Physics Engine Independence**: The physics consistency engine evaluates kinematic plausibility against physical InSAR constraints. It has zero knowledge of ML internal weights, class probabilities, or latent features.
3. **Consensus Engine Independence**: Evaluates convergence or divergence between ML and Physics outputs. It never re-runs ML or Physics models and applies symmetrical penalty on divergence.
4. **Temporal Evidence Independence**: Evaluates sequence kinematics without access to infrastructure asset criticality or material types.
5. **Risk Characterization Independence**: Modulates analytical findings contextually against infrastructure baseline and critical zones, strictly protected by the Ground-Truth Leakage Firewall.
6. **Chronology Independence**: The SHA-256 evidence chain records complete analytical snapshots immutably, independent of how scores were computed.

---

## 2. Component Directory

| Component | File Path | Class / Entry Function | Input Schema | Output Schema | Semantic Version |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Pipeline Coordinator** | `backend/app/services/pipeline/service.py` | `STRATAAnalysisPipeline` | Observation ID, DB Session | `PipelineResult` | `1.0.0` |
| **InSAR Normalization** | `backend/app/services/insar/normalization.py` | `InSARNormalizationService` | `Observation` DB model | `InSARNormalizedFeatures` | `0.1.0` |
| **Feature Extraction** | `backend/app/services/ml/features.py` | `extract_features_from_sequence` | `List[ObservationRead]` | `ExtractedFeatureVector` | `0.1.0` |
| **ML Classifier** | `backend/app/services/ml/classifier.py` | `MLDeformationClassifier` | `ObservationSequence` | `MLClassificationResult` | `0.1.0` |
| **Physics Consistency** | `backend/app/services/physics/engine.py` | `PhysicsInSARConsistencyEngine` | `ObservationSequence` | `PhysicsConsistencyEvidence` | `0.2.1` |
| **Consensus Fusion** | `backend/app/services/consensus/engine.py` | `ConsensusEngine` | `MLResult`, `PhysicsEvidence` | `ConsensusAssessment` | `strata_consensus_v0.1.0` |
| **Temporal Kinematics** | `backend/app/services/temporal/engine.py` | `TemporalEvidenceEngine` | Sequence observations | `TemporalEvidenceSummary` | `strata_temporal_v1_0_0` |
| **Risk Characterization**| `backend/app/services/risk/engine.py` | `InfrastructureRiskCharacterizationEngine`| Asset, Sequence, Summary | `RiskCharacterizationRead` | `strata_risk_v1_0_0` |
| **Evidence Chronicle** | `backend/app/services/chronology/service.py` | `EvidenceChronicleService` | DB, Assessment, Snapshot | `ChronologyRecord` | `1.0.0` |

---

## 3. Centralized Versioning Registry

Semantic versioning (`MAJOR.MINOR.PATCH`) is centrally maintained in `backend/app/core/versions.py`:

```python
PIPELINE_VERSION = "1.0.0"
ML_MODEL_VERSION = "0.1.0"
FEATURE_SCHEMA_VERSION = "0.1.0"
PHYSICS_ENGINE_VERSION = "0.2.1"
CONSENSUS_ENGINE_VERSION = "strata_consensus_v0.1.0"
TEMPORAL_ENGINE_VERSION = "strata_temporal_v1_0_0"
RISK_CHARACTERIZATION_VERSION = "strata_risk_v1_0_0"
CHRONOLOGY_ENGINE_VERSION = "1.0.0"
THRESHOLD_REGISTRY_VERSION = "1.0.0"
```

### Version Audit Rules
- Every analytical execution permanently binds `system_versions` into the `AnalysisResult.execution_metadata` column and the `ChronologyRecord.payload`.
- Any modification to model weights, feature extractors, or decision thresholds mandates a semantic version bump.

---

## 4. Analytical Threshold Registry

All heuristic and physical cutoffs across STRATA engines are documented below:

| Engine | Parameter / Threshold | Value | Rationale & Physical Justification |
| :--- | :--- | :--- | :--- |
| **Validation** | Max Displacement Ceil | `10,000.0 mm` | Displacements exceeding 10 meters represent physical catastrophic failure or measurement artifacts. |
| **Validation** | Coherence Bounds | `[0.0, 1.0]` | Interferometric coherence $|\gamma|$ is strictly bounded in $[0, 1]$ by definition. |
| **Validation** | Incidence Angle Bounds | `(0.0, 90.0)` | Radar LOS geometry cannot be parallel or nadir-orthogonal to surface. |
| **Physics** | Minimum Coherence Floor | `0.40` | Coherence below 0.40 exhibits severe phase noise and unresolvable phase ambiguity. |
| **Physics** | Maximum Linear Rate | `150.0 mm/yr` | Deformation exceeding 150 mm/yr exceeds phase unwrapping Nyquist limit without multi-baseline SAR. |
| **Consensus**| Disagreement Penalty | `0.15` | Multiplied by divergence factor to reduce confidence when ML and Physics conflict. |
| **Temporal** | Minimum Baseline Window | `60.0 days` | Acceleration calculations over < 60 days reflect short-term noise rather than physical kinematic drift. |
| **Temporal** | Acceleration Noise Floor | `3.0 mm/yr²` | Kinematic noise below 3.0 mm/yr² cannot be reliably distinguished from atmospheric turbulence. |
| **Risk** | Baseline Z-Score Floor | `2.5` | Deviations under 2.5 standard deviations from historical baseline remain in `BASELINE` state. |
| **Risk** | Index Scale | `0.0 – 100.0` | Continuous index: 0–25 (BASELINE), 20–50 (MONITOR), 50–75 (ELEVATED), 75–100 (HIGH). |

---

## 5. Error Handling & Transaction Atomicity

### 5.1 Processing Status Lifecycle

```text
RECEIVED ──► VALIDATED ──► NORMALIZED ──► ML_ANALYZED ──► PHYSICS_ANALYZED ──►
CONSENSUS_ANALYZED ──► TEMPORAL_ANALYZED ──► CHARACTERIZED ──► CHRONICLED ──► COMPLETED
                                              │
                                              └──► FAILED (Rollback DB Transaction)
```

### 5.2 Transaction Rollback Guarantee
If an unhandled exception or analytical validation failure occurs at any stage:
1. `db.rollback()` is immediately triggered.
2. No orphaned `AnalysisResult` or `ChronologyRecord` can exist in the database.
3. A structured `PipelineExecutionError` is raised, capturing the `failed_stage`, root error message, and diagnostic execution context.

---

## 6. Idempotency & Replay Reproducibility

### 6.1 Idempotency Filter
When an observation is analyzed via `POST /api/v1/analysis/pipeline/{observation_id}` with `force_recompute=False`:
1. The pipeline checks for an existing `AnalysisResult` for `observation_id` with matching `pipeline_version`.
2. If found, it fetches the associated `ChronologyRecord` and returns the cached `PipelineResult` with `idempotent_replay: true`.
3. **No duplicate chronology record** is appended to the SHA-256 hash chain.
4. If `force_recompute=True` is provided, a fresh analytical cycle executes cleanly.

---

## 7. InSAR & Infrastructure Data Contracts

### 7.1 InSAR Observation Schema
- `deformation_mm` / `los_displacement_mm`: Float (mm), negative indicates settlement or movement away from satellite sensor.
- `coherence`: Float $[0.0, 1.0]$. Values $< 0.35$ trigger decorrelation warnings.
- `incidence_angle`: Float $(0.0, 90.0)$, default $35.0^\circ$ when missing. No orbital trajectories are fabricated.

### 7.2 Infrastructure Profile Schema
- Required: `name`, `structure_type`, `latitude`, `longitude`.
- Optional: `material`, `criticality`, `historical_baseline`, `critical_zones`.
- Safe Degradation: If baseline is omitted, the pipeline defaults to uncharacterized baseline with generic noise floor ($1.5$ mm) rather than crashing.

---

## 8. Tamper-Evident Chronology & SHA-256 Audit Chain

### 8.1 Hash Chaining Formula
Every analytical result produces an immutable, chained record:
$$\text{Payload Hash}_i = \text{SHA-256}(\text{CanonicalJSON}(\text{Payload}_i))$$
$$\text{Current Hash}_i = \text{SHA-256}(\text{Current Hash}_{i-1} \mathbin{\Vert} \text{Payload Hash}_i)$$
where $\text{Current Hash}_0$ chains to the 64-zero `GENESIS_HASH`.

### 8.2 Tamper Vectors Verified (10/10 Detected)
1. **Payload Tampering**: Modifying displacement or metrics inside `payload`.
2. **Current Hash Mismatch**: Altering `current_hash`.
3. **Previous Hash Mismatch**: Breaking pointer to predecessor.
4. **Record Deletion**: Sequence gaps ($0, 1, 3$).
5. **Record Reordering**: Swapping adjacent records.
6. **Duplicate Sequence Numbers**: Duplicate `record_index`.
7. **Non-Monotonic Timestamps**: Negative time progression.
8. **Inserted Fake Record**: Injecting unauthorized records into the chain.
9. **Modified Model Version**: Retroactively altering model versions in audit logs.
10. **Modified Classification**: Tampering with consensus category or risk index.

---

## 9. REST API Specification

### `POST /api/v1/analysis/pipeline/{observation_id}`
Executes the unified multi-engine pipeline.

**Query Parameters:**
- `force_recompute` (bool, default `false`): Force re-execution even if already analyzed.

**Responses:**
- `201 Created`: Analysis successfully performed or replayed.
- `404 Not Found`: Observation or associated infrastructure not found.
- `422 Unprocessable Entity`: Input failed validation (NaN, Inf, coherence out of bounds).
- `500 Internal Server Error`: Pipeline execution failure.

### `GET /api/v1/analysis/pipeline/{observation_id}`
Retrieves existing analytical result via idempotent execution replay.

---

## 10. Verification & Test Suite Summary

### 10.1 Test Coverage by Phase
- **Phase 1 (Foundation & Normalization)**: 15 tests
- **Phase 2 & 2.1 (Physics Consistency & Discrimination)**: 18 tests
- **Phase 3 & 3.1 (Controlled Dataset & Audit)**: 13 tests
- **Phase 4 (ML Deformation Classifier)**: 8 tests
- **Phase 5 (Cross-Model Consensus)**: 21 tests
- **Phase 6, 6.1, 6.2 (Temporal Kinematics & Chronology)**: 42 tests
- **Phase 7 (Infrastructure Risk Characterization)**: 35 tests
- **Phase 8 & 8.1 (Case-Study Benchmark Validation & Audit)**: 21 tests
- **Phase 9 (System Hardening & End-to-End Integration)**: 29 tests
- **Total Suite**: **202 / 202 Tests Passing (100% Pass Rate, 0 Regressions)**

### 10.2 Performance Latency Baseline
Measured on local hardware (macOS, Python 3.14.6):
- Input Validation: $0.3 - 1.0$ ms
- InSAR Normalization: $< 0.05$ ms
- Frozen ML Classifier: $15 - 25$ ms
- Physics Consistency: $0.1 - 0.2$ ms
- Consensus Fusion: $0.1 - 0.3$ ms
- Multi-Epoch Temporal Kinematics: $30 - 100$ ms
- Risk Characterization: $0.1 - 0.2$ ms
- Chronology Hash Chaining: $1.5 - 3.0$ ms
- **Total Pipeline Execution Latency**: **$\approx 125$ ms** (Well below the $1500$ ms interactive budget).
