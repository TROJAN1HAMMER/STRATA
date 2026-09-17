# STRATA — Core Invention Narrative & Analytical Methodology

**Document Version**: 1.0.0  
**Status**: TECHNICAL DISCLOSURE  
**Subject**: Multi-Source InSAR Analytical Evidence Fusion and Tamper-Evident Chronology Framework

---

## 1. The Core Inventive Contribution

STRATA is **not** defined as a generic technology aggregation of "AI + Physics + Blockchain". 

Rather, the fundamental technical contribution of STRATA lies in the **dynamic interaction between independent analytical evidence mechanisms**:

> **Core Inventive Principle**:  
> A multi-epoch infrastructure monitoring framework that combines a learned deformation classifier with an independent, deterministic InSAR physical-consistency model, explicitly modifies analytical confidence based on cross-model agreement or disagreement, incorporates temporal persistence and environmental recurrence safeguards, and maintains a tamper-evident chronology of analytical evidence.

---

## 2. The Technical Problem in Satellite SHM

Spaceborne Synthetic Aperture Radar interferometry provides millimetric ground deformation measurements from orbit across wide geographical regions. However, in civil structural health monitoring (SHM), raw InSAR measurements suffer from critical observational ambiguities:
1. **Atmospheric Turbulence**: Tropospheric water vapor delay creates localized phase gradients indistinguishable from acute structural deformation in single interferograms.
2. **Environmental & Thermal Modulation**: Bridges and concrete dams expand and contract cyclically by several millimeters annually due to temperature fluctuations. A simple displacement threshold inevitably misinterprets this benign breathing as progressive settlement.
3. **Interferometric Phase Noise & Decorrelation**: Low surface reflectivity, vegetation growth, and temporal decorrelation induce random phase noise that can masquerade as rapid kinematics.
4. **Temporal Baseline Artifacts**: Mathematically fitting a 2nd-order polynomial to a short observation sequence often yields high apparent acceleration ($\text{mm/yr}^2$) when the physical asset is entirely stable.

---

## 3. Existing Limitations of Prior Art

Conventional approaches rely on either:
- **A Single Machine Learning Model**: Deep learning or statistical classifiers trained on synthetic or localized datasets. When deployed on real-world structures, these models suffer from domain shift, high sensitivity to noise, and an inability to explain whether an inference violates physical radar constraints.
- **Single Deterministic Thresholds**: Static kinematic cutoffs (e.g., alert if velocity exceeds $10\text{ mm/yr}$). Such systems exhibit unacceptable false-alarm rates during seasonal extremes or miss genuine low-amplitude, persistent degradation.

A single model or single heuristic threshold is scientifically insufficient to certify or characterize structural risk from spaceborne radar.

---

## 4. The STRATA Multi-Stage Evidence Solution

STRATA resolves these ambiguities by decomposing observation interpretation into distinct, decoupled stages:

```text
Observable InSAR Sequence
           │
           ├──────────────────────────────┐
           ▼                              ▼
[Learned Model (ML Classifier)]    [Deterministic Physical Model]
• Feature space pattern recognition • Kinematic plausibility bounds
• Probabilistic classification      • Coherence & phase unwrapping limits
• Shannon entropy & confidence      • Thermal/environmental correlation
           │                              │
           └──────────────┬───────────────┘
                          ▼
             [Cross-Model Consensus Engine]
             • Agreement -> Amplifies analytical confidence
             • Disagreement -> Penalizes confidence & raises uncertainty
             • Environmental evidence -> Suppresses structural threat
                          │
                          ▼
             [Temporal Kinematics & Guards]
             • Multi-epoch trajectory persistence
             • Acceleration Guard: suppresses acceleration on baseline
                          │
                          ▼
             [Infrastructure Contextualization]
             • Modulates evidence against historical asset baseline
             • Evaluates critical structural zones & material types
                          │
                          ▼
             [Tamper-Evident Evidence Chronicle]
             • Cryptographic SHA-256 hash chaining of complete snapshots
             • Permanent auditability against post-hoc data tampering
```

### 4.1 Dual Independent Evaluation
Two fundamentally distinct analytical engines evaluate the *exact same* observable InSAR sequence:
1. **The Learned Engine**: Evaluates 28 statistical, spectral, and kinematic features without bias toward civil structural rules, outputting a calibrated probability distribution over physical deformation modes.
2. **The Deterministic Physical Engine**: Evaluates phase unwrapping limits, spatio-temporal coherence, and thermal correlation against known radar wave propagation physics.

### 4.2 Cross-Model Consensus Calculus
Instead of arbitrarily choosing the model with the higher nominal score, the consensus engine applies an explicit fusion calculus:
- **Concurrence**: When both engines independently detect monotonic structural deformation, confidence is elevated beyond either individual score.
- **Divergence**: When the ML model predicts accelerating settlement but the physics engine identifies atmospheric turbulence, the consensus engine penalizes confidence and flags a `CONFLICTED` state.
- **Environmental Suppression**: When physical evidence indicates strong thermal correlation, structural alarms are suppressed.

### 4.3 Longitudinal Temporal Safeguards
Single-epoch transient spikes cannot generate structural alerts. The temporal engine requires monotonic directional persistence across multiple satellite passes. Furthermore, the **Scientific Baseline Guard** prevents mathematical acceleration artifacts from generating false warnings when sequence displacements remain within the structure's established baseline noise floor.

### 4.4 Asset Context & Critical Zones
The same $5\text{ mm}$ displacement is interpreted contextually: on a high-criticality steel bridge pier, it warrants elevated monitoring; on a stable concrete embankment within historical baseline limits, it is characterized as nominal baseline behavior.

### 4.5 Immutable Evidence Chronology
Every analysis produces an immutable audit record chained via SHA-256 to its chronological predecessor. This ensures full forensic traceability for civil engineers, public infrastructure authorities, and regulatory bodies.
