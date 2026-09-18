# STRATA Patent Figure Guide & Disclosure Visual Mapping

## 1. Overview

This document provides formal technical descriptions, figure element callouts, and prospective patent claim alignments for the eight specification figures implemented in the **STRATA Patent Visualization Mode**.

These vector figures are designed for direct inclusion in patent disclosure documents, academic publications, and technical grant presentations.

---

## 2. Master Patent Figure Mapping

| Figure Number | View Title | Subsystem Focus | Prospective Disclosure Alignment |
| :--- | :--- | :--- | :--- |
| **FIG. 1** | Overall STRATA Interaction Architecture | System-level interaction | Claim 1: Multi-engine evidence characterization architecture with consensus confidence modulation. |
| **FIG. 2** | Multi-Epoch InSAR Differential Geometry | InSAR physics & projection | Claim 2: Deterministic trigonometric projection of slant Line-of-Sight range into vertical geodetic displacement. |
| **FIG. 3** | Environmental Recurrence Safeguard | Environmental discrimination | Claim 3: Zero-crossing periodic analysis separating cyclic thermal/hydrological motion from structural settlement. |
| **FIG. 4** | Cross-Model Consensus & Confidence Modulation | Consensus engine | Claim 4: Symmetrical cross-model consensus engine treating analytical disagreement as mathematical uncertainty. |
| **FIG. 5** | Multi-Epoch Temporal State Machine | Temporal evidence engine | Claim 5: 9-state kinematic state machine evaluating multi-epoch persistence against historical baseline envelopes. |
| **FIG. 6** | Infrastructure Context & Characterization Index | Risk characterization engine | Claim 6: Hierarchical evidence characterization where physical measurement quality gates asset criticality weighting. |
| **FIG. 7** | Canonical SHA-256 Tamper-Evident Chronology | Integrity & audit engine | Claim 7: Cryptographic hash chain linking consecutive analysis records for tamper-evident provenance verification. |
| **FIG. 8** | Complete Nine-Stage Analytical Pipeline | Pipeline orchestration | Claim 8: Transactional, idempotent 9-stage analysis pipeline with atomic state rollback. |

---

## 3. Detailed Figure Descriptions & Element Callouts

### FIG. 1 — Overall System Architecture
* **Element 100**: Multi-epoch satellite InSAR observation stream (Sentinel-1 C-band, line-of-sight displacement $d_{\text{LOS}}$, coherence $\gamma$, temporal baseline $\Delta t$).
* **Element 200**: Machine Learning Deformation Engine (calibrated GBDT classifier evaluated across 28 observable features).
* **Element 300**: Deterministic Physics Consistency Engine (evaluating kinematic velocity bounds, noise floors, and environmental periodicities).
* **Element 400**: Cross-Model Consensus Engine (calculating agreement mass, applying $+15\%$ agreement boost or $-30\%$ divergence uncertainty penalty).
* **Element 500**: Infrastructure-Specific Evidence Characterization Engine (fusing consensus evidence with asset type, material stiffness, critical zones, and baseline $z$-score).
* **Element 600**: Cryptographic Chronology Engine (canonical JSON SHA-256 ledger).

---

### FIG. 2 — Differential InSAR Geometry & Vertical Projection
* **Element 201**: Radar satellite antenna platform orbiting at altitude ~$693\text{ km}$.
* **Element 202**: Slant range Line-of-Sight (LOS) propagation vector.
* **Element 203**: Radar incidence angle $\theta$ measured relative to local nadir vector.
* **Element 204**: Target infrastructure deck exhibiting vertical deformation $d_{\text{vertical}}$.
* **Governing Relationship**:
  $$d_{\text{vertical}} = \frac{d_{\text{LOS}}}{\cos\theta}$$

---

### FIG. 3 — Environmental Recurrence Discrimination Safeguard
* **Element 301**: Sinusoidal deformation profile reflecting annual thermal expansion/contraction or rainfall pore-pressure cycles.
* **Element 302**: Historical baseline noise envelope ($\pm 1\sigma$).
* **Element 303**: Reversible zero-crossing points ($\ge 2$ zero crossings across 12-month periods).
* **Governing Rule**: Detection of cyclic zero-crossing behavior classifies trajectory as `ENVIRONMENTAL_PATTERN`, suppressing monotonic failure alarm contributions.

---

### FIG. 4 — Cross-Model Consensus & Confidence Modulation
* **Case A (Symmetrical Agreement)**:
  - Condition: ML and Physics engines both classify observation as structural.
  - Confidence Formula: $\text{Confidence}_{\text{fused}} = \min(1.0, \, \text{Confidence}_{\text{base}} \times 1.15)$.
* **Case B (Model Divergence)**:
  - Condition: ML engine predicts structural deformation while Physics engine detects seasonal cyclicity.
  - Confidence Formula: $\text{Confidence}_{\text{fused}} = \text{Confidence}_{\text{base}} \times 0.70$.
  - Result: State set to `CONFLICTED`; alarm downgraded to `MONITOR`.

---

### FIG. 5 — Multi-Epoch Temporal State Machine
* **Nine Operational States**:
  1. `INSUFFICIENT_HISTORY`: Sequence contains $< 3$ valid epochs.
  2. `BASELINE`: Trajectory remains within $\pm 1\sigma$ historical envelope.
  3. `EMERGING`: Single departure from baseline without confirmed persistence.
  4. `PERSISTENT`: Unidirectional monotonic departure sustained over consecutive revisits.
  5. `ACCELERATING`: Monotonic departure with mathematically and physically supported acceleration.
  6. `REVERTED`: Previous departure returns back into baseline envelope.
  7. `ENVIRONMENTAL_PATTERN`: Reversible cyclic oscillation detected.
  8. `ATMOSPHERIC_EVENT`: Transient single-epoch phase delay spike.
  9. `CONFLICTED`: Divergent interpretations between independent analytical engines.

---

### FIG. 6 — Infrastructure Context & Characterization Index
* **Context Dimensions**: Structure type, construction material, criticality tier, critical zone weighting, geodetic baseline mean/std.
* **Dominance Rule**: *Measurement quality dominates infrastructure context.* High asset criticality cannot override degraded interferometric coherence ($\gamma < 0.60$).
* **Output Rating**: Calibrated 0–100 Evidence Characterization Index.

---

### FIG. 7 — Canonical SHA-256 Tamper-Evident Chronology
* **Record Structure**: Sequential audit block containing record ID, observation ID, canonical payload hash, previous record hash pointer, and current record hash.
* **Chaining Algorithm**:
  $$h_i = \operatorname{SHA-256}(h_{i-1} \parallel \operatorname{SHA-256}(\text{payload}_i))$$
* **Verification**: Tested against 10 adversarial tamper vectors (retroactive displacement modification, record deletion, block insertion, timestamp alteration) with 100% detection rate.

---

### FIG. 8 — Complete Nine-Stage Analytical Pipeline
* **Linear Execution Sequence**:
  1. Input Validation & Physical Sanity
  2. Observation Normalization
  3. Historical Sequence Assembly
  4. Frozen ML Inference (GBDT)
  5. Deterministic Physics Consistency
  6. Cross-Model Consensus
  7. Multi-Epoch Temporal Evidence
  8. Infrastructure Risk Characterization
  9. Cryptographic Chronology & Persistence

---

## 4. Legal & Regulatory Notice

> **Mandatory Notice:** This patent figure guide provides descriptive mappings for research, educational, and patent disclosure review. It does not constitute a legal opinion on patentability or novelty. STRATA is an experimental decision-support prototype and does not provide certified civil engineering safety ratings, structural life forecasts, or replacement for certified physical inspections.
