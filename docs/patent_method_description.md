# STRATA — Patent-Style Method Description

**Document Version**: 1.0.0  
**Status**: TECHNICAL METHOD DISCLOSURE  
**Notice**: This document provides an engineering-level, step-by-step description of the STRATA method. It is prepared for review by patent counsel and does not constitute formal legal patent claims.

---

## Method for Multi-Source InSAR Analytical Evidence Fusion, Temporal Kinematics, and Evidence Chronology

A computer-implemented method for analyzing multi-epoch satellite Synthetic Aperture Radar (SAR) interferometry observations associated with civil infrastructure assets comprises the following steps:

---

### Step 1: Ingestion and Pre-Validation of SAR Observations
1. Ingest a satellite InSAR observation record associated with a monitored civil infrastructure asset.
2. Parse physical fields including Line-of-Sight (LOS) displacement ($\text{mm}$), interferometric coherence ($|\gamma|$), radar incidence angle ($\theta$), and acquisition timestamp ($t$).
3. Validate numerical finiteness by rejecting non-finite values ($\text{NaN}$, $\pm\infty$).
4. Enforce physical sanity bounds:
   - verify coherence satisfies $0.0 \le |\gamma| \le 1.0$;
   - verify incidence angle satisfies $0.0^\circ < \theta < 90.0^\circ$;
   - verify displacement magnitude does not exceed a physical sanity ceiling ($|d| \le 10,000\text{ mm}$).

---

### Step 2: Unit Normalization and Geometric Preservation
1. Preserve original LOS displacement, measurement units, and representation.
2. Project Line-of-Sight displacement to an equivalent vertical component:
   $$\Delta d_{\text{vert}} = \frac{\Delta d_{\text{los}}}{\cos\theta}$$
3. When satellite incidence angle or orbital trajectory metadata is absent, maintain missing fields as null without fabricating or hallucinating orbital geometry.
4. Normalize acquisition timestamps into a consistent UTC-aware time representation.

---

### Step 3: Learned Deformation Classification
1. Retrieve historical observations associated with the asset up to the current timestamp to form an observation sequence.
2. Extract statistical, kinematic, and spectral features across the sequence (e.g., velocity, acceleration curvature, autocorrelation, spectral energy).
3. Execute a trained, frozen statistical classifier (e.g., Random Forest) on the extracted feature vector.
4. Output a calibrated class probability distribution $P(C_k)$ across discrete physical deformation modes and compute the Shannon entropy $H = -\sum P(C_k) \log_2 P(C_k)$ and model confidence score.

---

### Step 4: Deterministic Physical InSAR Consistency Evaluation
1. In parallel and independently from the learned classification, process the observation sequence through a deterministic physical-consistency engine.
2. Evaluate interferometric phase unwrapping limits and verify whether average coherence satisfies a minimum reliability threshold ($\ge 0.40$).
3. Evaluate spatio-temporal phase variance to distinguish spatial smoothness from turbulent atmospheric artifacts.
4. Evaluate thermal correlation between displacement and environmental seasonal variations to identify cyclic elastic breathing.
5. Emit a physical consistency classification, evidence strength score, and kinematic factor breakdown.

---

### Step 5: Shared Evidence Taxonomy Mapping
1. Map heterogeneous outputs from the learned classifier and deterministic physical engine into a unified analytical evidence taxonomy:
   - `STRUCTURAL`: Monotonic settlement, shear, or supported acceleration.
   - `ENVIRONMENTAL`: Cyclic thermal expansion or seasonal hydrologic modulation.
   - `ATMOSPHERIC`: Uncorrelated transient phase noise or turbulent tropospheric delays.
   - `LOW_QUALITY`: Severe temporal or spatial phase decorrelation.
   - `CONFLICTED`: Divergence between analytical models.

---

### Step 6: Cross-Model Agreement and Disagreement Quantification
1. Compare the predicted evidence categories from the learned classifier and the physical consistency engine.
2. Quantify an agreement score $A \in [0.0, 1.0]$ based on categorical alignment and probability mass overlap.
3. Quantify a divergence factor $D = 1.0 - A$.

---

### Step 7: Dynamic Confidence Modification and Suppression
1. Calculate a fused consensus confidence score:
   - when models agree ($A \ge 0.70$), amplify confidence toward the consensus category:
     $$C_{\text{fused}} = \min\left(1.0, \, \frac{C_{\text{ml}} + C_{\text{phys}}}{2} \times (1.0 + 0.15 \times A)\right)$$
   - when models disagree, penalize confidence by subtracting a disagreement penalty proportional to $D$:
     $$C_{\text{fused}} = \max\left(0.10, \, \frac{C_{\text{ml}} + C_{\text{phys}}}{2} - 0.15 \times D\right)$$
2. If the physical engine identifies strong environmental or atmospheric contamination, suppress structural deformation flags regardless of nominal ML confidence.

---

### Step 8: Multi-Epoch Temporal Trajectory and Acceleration Safeguards
1. Assemble the longitudinal trajectory of fused consensus states across historical epochs.
2. Calculate the linear displacement trend rate ($\text{mm/yr}$) via robust regression.
3. Calculate apparent mathematical acceleration ($\text{mm/yr}^2$) by fitting a second-order polynomial.
4. Apply the **Scientific Baseline Guard**:
   - if the sequence temporal baseline is shorter than a minimum duration gate (e.g., 60 days), set `acceleration_supported = False`;
   - if sequence displacement remains within the structure's historical baseline noise floor, set `acceleration_supported = False`;
   - only assert `acceleration_supported = True` when persistent non-linear kinematic divergence is observed over sufficient temporal baseline.
5. Assign a temporal state (`BASELINE`, `PERSISTENT_LINEAR`, `ACCELERATING`, `ENVIRONMENTAL_PATTERN`, `ATMOSPHERIC_EVENT`, `CONFLICTED`).

---

### Step 9: Contextual Infrastructure Characterization
1. Retrieve an infrastructure engineering profile comprising structure type, primary construction material, operational criticality, historical baseline statistics ($z$-scores), and critical spatial zones.
2. Evaluate the evidence through a 9-step decision hierarchy firewalled against ground-truth leakage.
3. Compute a continuous prototype evidence index ($0.0 - 100.0$) combining measurement quality, consensus support, temporal persistence, and critical zone vulnerability weighting.
4. Generate a non-alarmist technical explanation detailing primary evidence, attenuation factors, and observational uncertainties, accompanied by a mandatory non-safety disclaimer.

---

### Step 10: Tamper-Evident Chronology Persistence
1. Package the complete analytical snapshot—including raw measurements, intermediate ML/Physics outputs, consensus assessment, temporal kinematics, characterization index, and version registry—into a canonical JSON payload.
2. Compute a SHA-256 payload hash of the canonical JSON bytes.
3. Retrieve the current hash of the immediately preceding record in the asset's evidence chain.
4. Compute the current chained SHA-256 hash:
   $$\text{Current Hash}_i = \text{SHA-256}(\text{Current Hash}_{i-1} \mathbin{\Vert} \text{Payload Hash}_i)$$
5. Persist the analytical result and chronology record within an atomic database transaction.
