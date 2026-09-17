# Technical Invention Summary: STRATA

**Title**: System and Method for Multi-Source InSAR Analytical Evidence Fusion, Temporal Kinematics, and Tamper-Evident Chronology for Civil Infrastructure Monitoring  
**Technical Field**: Civil Structural Health Monitoring (SHM), Spaceborne Radar Remote Sensing, Interferometric Synthetic Aperture Radar (InSAR), Distributed Evidence Fusion.

---

## 1. Background & Problem Description

Civil infrastructure assets—such as suspension bridges, viaducts, arch dams, and retaining structures—undergo slow, progressive physical deformation prior to failure. Satellite InSAR provides millimeter-scale displacement tracking across broad geographic areas without requiring physical access to the asset.

However, raw InSAR observations frequently suffer from false alarms due to atmospheric phase delay, seasonal thermal expansion, and temporal decorrelation. Conventional systems either deploy single-threshold alert rules (which trigger false alerts on cyclic thermal movements) or rely on single machine learning models (which are prone to out-of-domain failures and lack physical interpretability).

---

## 2. System Overview & Architecture

STRATA provides a decoupled, multi-engine analytical architecture that processes multi-epoch satellite InSAR observations through a deterministic pipeline:

```text
InSAR Observations ──► [Input Validation & Normalization]
                                │
                 ┌──────────────┴──────────────┐
                 ▼                             ▼
        [ML Classifier]            [Physics Consistency]
                 │                             │
                 └──────────────┬──────────────┘
                                ▼
                    [Cross-Model Consensus]
                                ▼
                       [Temporal Engine]
                                ▼
               [Infrastructure Characterization]
                                ▼
                  [Tamper-Evident Chronology]
```

---

## 3. Core Technical Method

The STRATA method operates in sequential, decoupled stages:
1. **Observation Validation & Bounds Checking**: Filters non-finite values (NaN, Inf), verifies physical coherence bounds $[0, 1]$, validates incidence angle geometry, and enforces physical displacement ceilings ($|d| \le 10,000$ mm).
2. **InSAR Normalization**: Transforms raw Line-of-Sight (LOS) phase displacements into projected vertical displacements while strictly preserving original geometric angles and flags without fabrication.
3. **Independent Dual Inference**:
   - The **Machine Learning Deformation Classifier** extracts 28 statistical and spectral features to output a 7-class probability distribution and Shannon entropy score.
   - The **Deterministic Physics InSAR Consistency Engine** verifies kinematic plausibility, spatial unwrapping coherence floors, and thermal/environmental correlation.
4. **Cross-Model Consensus Fusion**:
   - Converts heterogeneous engine outputs into a shared evidence taxonomy (`STRUCTURAL`, `ENVIRONMENTAL`, `ATMOSPHERIC`, `LOW_QUALITY`, `CONFLICTED`).
   - Symmetrically modulates analytical confidence: agreement elevates confidence; disagreement reduces confidence and applies an explicit disagreement penalty.
5. **Multi-Epoch Temporal Reasoning**:
   - Traces the longitudinal trajectory across historical observations.
   - Enforces the **Scientific Baseline Guard**: mathematically apparent acceleration ($\text{mm/yr}^2$) is flagged as unsupported unless observed over a minimum baseline duration ($\ge 60$ days) and outside the asset's established baseline noise floor.
6. **Infrastructure Contextualization**:
   - Evaluates evidence within a 9-step decision hierarchy firewalled against ground-truth leakage.
   - Contextualizes evidence against asset material (concrete, steel), operational criticality, historical baseline $z$-scores, and monitored critical zones.
   - Computes a continuous prototype evidence index ($0-100$) and generates non-alarmist engineering explanations.
7. **Tamper-Evident Chronology Persistence**:
   - Serializes the complete analytical snapshot into canonical JSON.
   - Appends a cryptographically linked SHA-256 record ($\text{SHA-256}(\text{previous\_hash} \mathbin{\Vert} \text{payload\_hash})$).
   - Commits all outputs atomically within a database transaction.

---

## 4. Example Execution Walkthrough

Consider a high-criticality steel viaduct pier subject to an 8-epoch InSAR sequence over 84 days with progressive negative displacement ($-0.5\text{ mm}$ to $-12.4\text{ mm}$):
- **Normalization**: Projected to $-12.40\text{ mm}$ vertical (incidence angle $36.5^\circ$, coherence $0.86$).
- **ML Classifier**: Predicts deformation pattern with probability distribution and confidence.
- **Physics Engine**: Confirms spatial coherence satisfies radar limits and classifies kinematics as structurally consistent.
- **Consensus Engine**: Compares findings; upon alignment, boosts fused confidence; upon divergence, penalizes confidence.
- **Temporal Engine**: Computes trend velocity ($-15.2\text{ mm/yr}$) and evaluates acceleration support.
- **Risk Characterization Engine**: Applies steel pier contextual weighting, flags critical foundation zone, assigns `MONITOR` state (Index: $35.0 / 100$), and emits explanatory narrative.
- **Chronology Service**: Computes SHA-256 current hash linked to previous hash and commits records atomically in $\approx 125\text{ ms}$.

---

## 5. Technical Advantages

1. **False-Positive Mitigation**: Disagreement between ML and physics models prevents transient noise from triggering unverified structural alerts.
2. **Environmental Artifact Suppression**: Bennign seasonal thermal breathing is identified and prevented from escalating into structural alarms.
3. **Forensic Immutability**: The SHA-256 chained chronicle provides tamper-evident auditability for public infrastructure authorities.
4. **Mathematical Acceleration Guarding**: Eliminates short-baseline mathematical artifacts from being reported as accelerating deformation.
5. **Decoupled Architecture**: Engines can be audited, updated, or verified independently without cross-component contamination.

---

## 6. Technical Limitations

1. **Domain Sensitivity**: Frozen statistical ML models may experience domain drift when applied to uncalibrated radar instruments.
2. **Consensus Suppression Trade-Off**: Rigid consensus can suppress genuine physical deformation if one model fails to recognize an unusual kinematic mode (as observed in Phase 8 Case B).
3. **No 3D Vector Decomposition**: Single-geometry LOS cannot separate horizontal shear from vertical settlement without combining ascending and descending satellite orbits.
4. **Research Prototype Identity**: The prototype characterization index ($0-100$) is an analytical ranking metric for inspection prioritization, not a physical probability of structural failure or engineering safety certification.
