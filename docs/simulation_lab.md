# STRATA Simulation Lab & Technical Explainability Guide

## 1. Overview & Purpose

The **STRATA Simulation Lab** is a dedicated scientific visualization, explainability, and patent figure environment within the STRATA frontend.

Its purpose is threefold:
1. **Academic & Reviewer Explainability**: Enable faculty, engineering reviewers, and patent examiners with no prior Synthetic Aperture Radar (SAR) or InSAR background to intuitively understand how satellite radar measures millimeter infrastructure motion.
2. **Mechanism Demonstration**: Visually expose the physical, environmental, and algorithmic mechanisms behind STRATA's metrics—specifically how the system separates reversible environmental cycles from true structural deterioration and why consensus disagreement suppresses overconfidence.
3. **Patent & Publication Assets**: Render high-contrast, uncluttered, publication-grade vector compositions suitable for academic papers, slide decks, and patent specifications.

---

## 2. Core Scientific Boundary: Conceptual vs. Analytical

STRATA maintains an immutable boundary between conceptual educational simulations and frozen analytical pipeline outputs:

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                            SCIENTIFIC SEPARATION                            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│        CONCEPTUAL SIMULATION         │       STRATA v1.0.0 ANALYTICAL       │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Educational visual representations │ • Authoritative frozen pipeline      │
│ • Illustrative response models       │ • 202/202 verified regression tests  │
│ • Interactive sliders & parameters   │ • Calibrated ML GBDT classifier      │
│ • Does NOT modify database state     │ • Deterministic kinematic laws       │
│ • Clearly badged in the UI           │ • SHA-256 tamper-evident ledger      │
└──────────────────────────────────────┴──────────────────────────────────────┘
```

> **Mandatory Notice:** Conceptual simulations are illustrative educational models. They do not calculate or alter frozen STRATA v1.0.0 analytical pipeline results, database records, or model weights.

---

## 3. Interactive Simulation Modules

### Module 01 — SAR / InSAR Fundamentals
* **Physical Phenomenon**: Active microwave pulses sent from satellite orbit (~693 km altitude) reflecting off civil infrastructure.
* **Key Mechanism**: Phase difference interferometry $\Delta\phi = \frac{4\pi}{\lambda} d_{\text{LOS}}$ and geometric projection into vertical displacement:
  $$d_{\text{vertical}} = \frac{d_{\text{LOS}}}{\cos\theta}$$
* **Interactive Controls**:
  - Radar Incidence Angle $\theta$ ($20^\circ$ to $55^\circ$).
  - Slant Range Line-of-Sight Displacement $d_{\text{LOS}}$ ($0$ to $-20\text{ mm}$).
* **Key Educational Takeaway**: Satellites look sideways at an incidence angle $\theta$, compressing vertical settlement along the line-of-sight slant path. STRATA trigonometrically reconstructs the true vertical motion.

---

### Module 02 — Environmental Water Response
* **Physical Phenomenon**: Rainstorms saturating subgrade soil beneath railway embankments and highway abutments.
* **Key Mechanism**: Soil pore-pressure modulation causing temporary, reversible heave and settlement.
* **Interactive Controls**:
  - Rainfall Intensity ($0 - 100\%$).
  - Soil Saturation / Pore Pressure ($0 - 100\%$).
  - Time of Year ($0 - 365\text{ days}$).
* **Key Educational Takeaway**: Because moisture drains and ground settles back toward the baseline, STRATA's **Environmental Recurrence Guard** detects reversibility and suppresses false structural alarm escalation.

---

### Module 03 — Seasonal Thermal Dynamics
* **Physical Phenomenon**: Annual ambient temperature cycling (summer heat vs. winter cold) causing steel and concrete thermal expansion and contraction.
* **Key Mechanism**: Multi-year sinusoidal deformation with $\ge 2$ zero crossings across 12-month calendar periods.
* **Interactive Controls**:
  - Thermal Expansion Amplitude ($\pm 2\text{ mm}$ to $\pm 15\text{ mm}$).
  - Noise Floor ($\pm 0.2\text{ mm}$ to $\pm 2.5\text{ mm}$).
  - Month Selection (January to December).
* **Key Educational Takeaway**: Coherent, large-amplitude movement does NOT automatically mean structural damage. Cyclic periodicity indicates healthy thermal breathing; STRATA classifies this as `ENVIRONMENTAL_PATTERN` and mutes monotonic failure alarms.

---

### Module 04 — Atmospheric Disturbance Illusion
* **Physical Phenomenon**: Localized tropospheric water vapor pockets slowing radar wave propagation.
* **Key Mechanism**: Atmospheric path delay producing a spurious $+14\text{ mm}$ displacement spike on a single observation epoch while the structure is 100% stationary ($0.0\text{ mm}$ true motion).
* **Interactive Controls**:
  - Tropospheric Delay Strength ($2 - 25\text{ mm}$).
  - Cloud Horizontal Position across radar path.
* **Key Educational Takeaway**: The concrete bridge does not move at all, yet the raw radar signal shows a huge motion spike. STRATA's spatial-temporal transient filter rejects single-epoch anomalies as `ATMOSPHERIC_EVENT`.

---

### Module 05 — Progressive Structural Deformation
* **Physical Phenomenon**: Foundation settlement, structural joint deterioration, or soil creep.
* **Key Mechanism**: Trajectory breaking out unidirectionally through the historical baseline noise envelope ($\pm 1\sigma$) across 8 consecutive observation epochs.
* **Interactive Modes**:
  - `Stable Infrastructure`: Oscillating within baseline noise floor.
  - `Monotonic Linear Settlement`: Constant velocity settlement exceeding noise band.
  - `Accelerating Subsidence`: Increasing velocity and curvature.
* **Engine Readouts**: Synchronized live gauges for ML probability, Physics consistency score, Consensus agreement, and the 0-100 Evidence Characterization Index.

---

### Module 06 — Cross-Model Consensus & Conflict
* **Core Invention Insight**: *Disagreement between independent analytical engines is itself mathematical evidence of uncertainty.*
* **Interactive Scenarios**:
  - **Symmetrical Agreement**: ML Classifier (Structural) + Physics Engine (Structural) $\to$ Confidence amplified by $+15\%$.
  - **Model Disagreement**: ML Classifier (Structural) vs. Physics Engine (Seasonal Cyclic) $\to$ Uncertainty penalty of $-30\%$ applied; alert downgraded to `MONITOR`.
  - **Quality Degradation**: Low coherence ($\gamma < 0.60$) $\to$ Quality gate overrides and mutes both engines.

---

## 4. Faculty Mode vs. Technical Mode

A persistent switch in the Simulation Lab header toggles terminology between standard InSAR scientific phrasing and faculty/reviewer plain English:

| Term | Technical Mode Phrasing | Faculty Mode Plain Phrasing |
| :--- | :--- | :--- |
| **LOS** | Line-Of-Sight range projection vector | Movement along the satellite's line of sight |
| **Coherence $\gamma$** | Interferometric coherence (0.0 to 1.0) | Radar reflection clarity and reliability |
| **Recurrence** | Multi-epoch cyclic periodic phase signature | A pattern that repeatedly returns over time |
| **Consensus Penalty** | Cross-model divergence confidence modulation | Confidence reduction due to model disagreement |
| **Atmospheric Delay** | Tropospheric water-vapor path retardation | Radar signal distortion caused by clouds/humidity |
| **Baseline Guard** | Historical $\pm 1\sigma$ geodetic envelope | Safety check ensuring noise is not mistaken for damage |
| **Evidence Index** | Composite Evidence Characterization Index | Priority inspection rating (0-100) |

---

## 5. Explain STRATA in 3 Minutes Walkthrough

A structured 10-step presenter walkthrough with exact speaker notes and timing:
- **00:00–00:20**: What is satellite radar? (All-weather active microwave imaging)
- **00:20–00:40**: Repeated observation & differential phase (Millimeter displacement tracking)
- **00:40–01:00**: The environmental confusion trap (Thermal expansion & soil moisture)
- **01:00–01:20**: Dual independent analytical engines (Learned pattern classification + deterministic kinematics)
- **01:20–01:40**: Consensus & the disagreement principle (Uncertainty penalty on divergence)
- **01:40–02:00**: Multi-epoch temporal evidence (Persistence beyond historical baseline)
- **02:00–02:20**: Infrastructure context (Material stiffness & critical zones)
- **02:20–02:40**: Evidence Characterization Index (0-100 inspection triage score)
- **02:40–03:00**: Tamper-evident chronology & mandatory non-safety disclaimers

---

## 6. Regulatory & Non-Safety Notice

> **Mandatory Notice:** STRATA is a research engineering prototype for satellite InSAR evidence characterization. It does not certify civil engineering safety, calculate collapse probabilities, forecast remaining structural fatigue life, or replace on-site physical engineering inspections.
