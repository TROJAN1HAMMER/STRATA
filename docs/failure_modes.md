# STRATA — Failure Modes, Boundary Conditions & Scientific Limitations

**Document Version**: 1.0.0  
**Status**: COMPLETE LIMITATIONS AUDIT  
**Analytical Pipeline Version**: `1.0.0`

In accordance with rigorous scientific practice, this document catalogs the known failure modes, observational ambiguities, and structural trade-offs identified during the design, testing, and evaluation of the STRATA prototype.

---

## 1. Failure Modes and Mitigations Matrix

| ID | Failure Mode Name | Underlying Root Cause | Architectural Mitigation | Residual Scientific Limitation |
| :--- | :--- | :--- | :--- | :--- |
| **F1** | **Stable Noise Mistaken for Periodicity** | Random sub-millimeter noise crossing zero combined with limited observation epochs can appear pseudo-sinusoidal. | Environmental correlation requires matching external thermal cycles ($R^2 \ge 0.60$); cross-model consensus penalizes unverified periodicity; temporal baseline guard. | Threshold sensitivity: In structures with noisy baselines, low-amplitude thermal breathing may still be classified as unverified or monitor state. |
| **F2** | **Partial Seasonal Cycle Resembles Monotonic Settlement** | Observing only a 3-to-6 month descending half of an annual thermal breathing cycle mimics linear settlement. | Environmental Recurrence Guard checks for annual cyclic history; temporal state machine flags unconfirmed trends on sequences under 180 days. | Requires sufficient longitudinal history: True structural settlement cannot be cleanly decoupled from seasonal contraction without at least one full annual cycle (12 months). |
| **F3** | **Slow Structural Deformation Hidden by Radar Noise** | Genuine creep or settlement ($< 2.0\text{ mm/yr}$) is of comparable magnitude to satellite InSAR phase noise ($1.5 - 3.0\text{ mm}$). | Multi-epoch longitudinal accumulation; linear trend fitting over extended temporal baselines ($> 1\text{ year}$) dampens Gaussian noise. | High latency: Detecting ultra-slow settlement requires 12 to 24 months of observation before statistical significance ($p < 0.05$) is achieved. |
| **F4** | **Accelerating Deformation on Short Baselines** | Fitting a 2nd-order polynomial to short sequences ($\le 60\text{ days}$) yields mathematically non-zero curvature from normal observation noise. | **Scientific Acceleration Guard**: Imposes a minimum 60-day baseline gate and baseline noise floor before asserting `acceleration_supported = True`. | Cannot detect rapid instantaneous acceleration events occurring within a single 12-day orbital repeat cycle without high-frequency sensors. |
| **F5** | **Frozen ML Domain Shift on External Data** | Statistical ML models trained on synthetic simulations drift when encountering real-world radar speckle, soil moisture, and geometry variations. | Dual-engine consensus: Disagreements between ML and deterministic physics penalize confidence and flag `CONFLICTED`, preventing false runaway alerts. | Standalone ML accuracy degrades on uncalibrated radar instruments; ML model requires future fine-tuning across diverse geographic radar domains. |
| **F6** | **Genuine Deformation Suppressed by Model Disagreement** | Rigid consensus penalizes analytical confidence whenever ML and Physics engines diverge. If one model fails to recognize an unusual kinematic mode, the alert is suppressed. | Symmetrical penalty lowers confidence but transitions the temporal state to `CONFLICTED` and risk to `MONITOR`, ensuring human inspection review rather than complete omission. | **Core Scientific Trade-Off**: Conservative consensus drastically reduces catastrophic false alarms, but can suppress or delay the escalation of genuine complex deformation. |
| **F7** | **External Data Provenance Boundary** | Current external case-study datasets are literature-calibrated parametric time series rather than raw, uncurated SLC radar scenes. | Phase 8.1 scientific audit formally reclassified all external benchmarks as `SYNTHETIC / CASE-STUDY PLACEHOLDER`, eliminating overclaims. | Genuine operational validation on uncurated multi-satellite SAR archives remains future research work. |

---

## 2. Deep-Dive: The Consensus Suppression Trade-Off (Failure Mode F6)

During the Phase 8.1 case-study evaluation of the severe subsidence scenario (`real_sentinel1_subsidence_tunnel_02`, $-18.92\text{ mm/yr}$), a fundamental engineering trade-off was exposed:

### The Phenomenon
1. The deterministic physics consistency engine correctly classified the rapid linear settlement as `STRUCTURALLY_CONSISTENT`.
2. The frozen ML classifier, facing an extended 52-epoch sequence with curvature variation, drifted into out-of-domain uncertainty and classified several epochs as `SEASONAL` or `CONFLICTED`.
3. The consensus engine, adhering to its core principle:
   $$\text{DISAGREEMENT} \implies \text{PENALIZED CONFIDENCE / ELEVATED UNCERTAINTY}$$
   reduced the fused confidence score and held the infrastructure characterization at `MONITOR` (Index: $35.0 / 100$) rather than escalating to `HIGH_ATTENTION`.

### The Engineering Rationale
This behavior is an intentional design consequence, not an accidental defect. In civil infrastructure monitoring:
- **Over-trusting a single model** leads to false alarms that close bridges and waste public resources.
- **Requiring consensus verification** ensures that critical alerts are backed by mutually supporting evidence.
- The trade-off is that **genuine deformation can be held at a cautionary `MONITOR` status** if one analytical model produces an ambiguous interpretation.

---

## 3. Observational and Operational Boundaries

1. **Single Line-of-Sight (LOS) Geometric Ambiguity**:
   A single satellite orbit (e.g., Sentinel-1 Descending Track 112) measures displacement only along the line connecting the ground target to the satellite radar antenna. It cannot mathematically separate horizontal shear from vertical settlement without combining ascending and descending geometry.
2. **Phase Unwrapping & Velocity Aliasing**:
   Displacements exceeding the InSAR phase unwrapping Nyquist limit ($\approx \lambda / 4 \approx 14\text{ mm}$ between successive passes for C-band) induce phase wrapping ambiguity that cannot be resolved without multi-baseline or multi-frequency radar data.
3. **Vegetation and Temporal Decorrelation**:
   Infrastructure assets obscured by dense seasonal vegetation or standing water exhibit low coherence ($|\gamma| < 0.35$), forcing the pipeline into `INSUFFICIENT_EVIDENCE` states.
4. **Research Prototype Boundary**:
   The STRATA characterization index ($0-100$) is an analytical ranking metric designed to assist structural engineers with inspection scheduling. It is **not** an automated safety certification, failure probability, or collapse warning system.
