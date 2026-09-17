# STRATA — Live Demonstration Presenter Script (2–3 Minutes)

**Target Audience**: Research stakeholders, engineering evaluation committees, technical judges, and patent examiners.  
**Demonstration Mode**: Use STRATA UI Demo Mode (10-Scene Sequential Walkthrough).

---

## Scene 1 — System & Portfolio Overview [0:00 – 0:20]

> **Presenter**:  
> "Civil infrastructure monitoring faces a fundamental challenge with satellite radar interferometry (InSAR): raw millimeter-scale deformation observations are frequently contaminated by atmospheric water vapor turbulence, seasonal thermal expansion, and noise. In practice, isolated machine learning models often trigger catastrophic false alarms or suffer from uncalibrated domain shift.
>
> STRATA—Structural Temporal Analysis & Threat Assessment—is an analytical research platform designed to characterize multi-epoch InSAR deformation evidence with high scientific integrity and verifiable auditability."

---

## Scene 2 — Asset Identification [0:20 – 0:35]

> **Presenter**:  
> "Here, we select a representative monitored asset—such as this suspension bridge or tunnel structure. STRATA maintains an asset profile specifying structure classification, construction material, criticality tier, designated critical zones, and an empirical historical baseline noise floor. Crucially, raw ground-truth coordinates are decoupled to prevent geographic fabrication."

---

## Scene 3 — Multi-Epoch Trajectory [0:35 – 0:50]

> **Presenter**:  
> "Across successive satellite acquisition epochs, STRATA tracks cumulative vertical and line-of-sight displacements alongside interferometric coherence ($\gamma$). Rather than reacting to an isolated displacement spike, STRATA observes how evidence evolves over time within the calibrated historical baseline envelope."

---

## Scene 4 — Dual Independent Evidence Engines [0:50 – 1:10]

> **Presenter**:  
> "At each epoch, STRATA invokes two completely independent, decoupled evidence branches:
> 1. A **gradient-boosted ML classifier** trained on spatiotemporal feature vectors to discern deformation patterns.
> 2. A **deterministic kinematic physics consistency engine** that evaluates velocity admissibility and baseline noise limits without ML hallucination risk."

---

## Scene 5 — Cross-Model Consensus Convergence [1:10 – 1:30]

> **Presenter**:  
> "Here is the core architectural innovation: the **Cross-Model Consensus Engine**.
> When ML and physics agree—for example, confirming that movement is physical and persistent—analytical confidence is strengthened.
> Conversely, when models disagree—such as an ML model claiming structural damage during an acute non-physical transient—STRATA applies a conservative disagreement penalty, lowers analytical confidence, and flags the epoch as conflicted."

---

## Scene 6 — Temporal Evidence & Scientific Baseline Guard [1:30 – 1:50]

> **Presenter**:  
> "Evidence accumulates longitudinally. A single anomaly is treated as emerging or suspect. Only sustained, multi-epoch deformation transitions into a persistent evidence state.
> Furthermore, STRATA's **Scientific Baseline Guard** guarantees that if an asset oscillates strictly within its nominal historical noise floor, apparent acceleration is suppressed, preventing false alarms on stable civil structures."

---

## Scene 7 — Infrastructure Context & Baseline Sensitivity [1:50 – 2:05]

> **Presenter**:  
> "Contextual sensitivity modulates the evidence: high-criticality assets with brittle materials and critical zones receive appropriate inspection weighting, while baseline deviation is expressed as a normalized standard deviation score ($z$-score), strictly avoiding medical survival analogies or safety certifications."

---

## Scene 8 — Evidence Characterization Index [2:05 – 2:20]

> **Presenter**:  
> "The final analytical output is the **Evidence Characterization Index (0–100)** paired with its **Analytical Confidence**. This provides engineering managers with an objective, reproducible metric to prioritize physical field inspection crews."

---

## Scene 9 — Tamper-Evident Evidence Chronology [2:20 – 2:40]

> **Presenter**:  
> "To guarantee analytical provenance across research epochs, every pipeline calculation produces an immutable SHA-256 fingerprint cryptographically chained to previous observations. Any retrospective tampering with past observations or algorithm versions is mathematically detectable."

---

## Scene 10 — Scientific Transparency & Closing Disclaimer [2:40 – 3:00]

> **Presenter**:  
> "Finally, STRATA upholds strict scientific transparency:
> STRATA is a research prototype for analytical evidence characterization and inspection prioritization. It does not replace physical structural inspection or provide structural safety certification.
>
> All 202 backend tests pass with zero regressions, and the analytical engine remains frozen at version 1.0.0. Thank you."
