# STRATA — Infrastructure-Specific Risk Characterization Layer (Phase 7)

## 1. Purpose & Core Scientific Principle

The STRATA Risk Characterization Layer converts multi-epoch satellite InSAR analytical evidence (from Physics, Machine Learning, Consensus, and Temporal Evidence layers) into an **infrastructure-aware, contextualized inspection characterization**.

### Fundamental Scientific Boundary
STRATA adheres to strict physical and legal boundaries:

> **The output is an analytical risk characterization for inspection prioritization, NOT an engineering structural certification or collapse forecast.**

The system does NOT claim:
- Structural failure probability or timeline
- Collapse prediction or guarantee of structural collapse
- Structural safety certification or regulatory engineering sign-off
- Guaranteed physical structural integrity

### Infrastructure Context Over Universal Thresholds
Satellite radar interferometry measures displacement along the radar line of sight ($d_{\text{LOS}}$). A measured deformation of $5\text{ mm}$ does not carry the same engineering significance across all structures:
- A $5\text{ mm}$ seasonal thermal expansion across a $500\text{ m}$ steel suspension bridge deck is nominal, expected behavior.
- A $5\text{ mm}$ progressive localized differential settlement at a dam crest or retaining wall foundation pier warrants elevated analytical attention.

STRATA evaluates InSAR evidence relative to:
1. **Structure Type** (e.g. `BRIDGE`, `DAM`, `TUNNEL`, `BUILDING`, `RETAINING_STRUCTURE`, `EMBANKMENT`, `PIPELINE`)
2. **Structural Material** (e.g. `CONCRETE`, `STEEL`, `MASONRY`, `EARTH`, `ROCK`, `COMPOSITE`)
3. **Critical Zones** (e.g. `PIER`, `ABUTMENT`, `FOUNDATION`, `CREST`, `DECK`, `JOINT`)
4. **Historical Baseline Behavior** ($\mu_{\text{base}}, \sigma_{\text{base}}$)
5. **Expected Deformation Behavior** (`MONOTONIC`, `SEASONAL`, `STABLE`, `CYCLIC`)
6. **Infrastructure Criticality** (`LOW`, `MODERATE`, `HIGH`, `CRITICAL`)

---

## 2. Evidence Architecture & Decoupled Pipeline

```
Satellite InSAR Observations (Multi-Epoch)
  │
  ├─► [Phase 2/2.1] Deterministic Physics / InSAR Consistency Engine
  │     └─► 7-component evidence vector (quality, geometry, kinematics, temporal, environmental, atmospheric)
  │
  ├─► [Phase 4] Independent ML Deformation Classifier
  │     └─► 7-class probabilities, confidence, Shannon entropy
  │
  ├─► [Phase 5] Cross-Model Consensus Engine
  │     └─► Unified consensus class, agreement score, evidence quality, conflict flags
  │
  ├─► [Phase 6/6.2] Temporal Evidence Layer & Tamper-Evident Chronology
  │     └─► Canonical ordering, apparent acceleration (supported vs unsupported), structural persistence
  │
  └─► [Phase 7] Infrastructure-Specific Risk Characterization (THIS LAYER)
        │
        ├─► Infrastructure Profile (Type, Material, Critical Zones, Baseline, Criticality)
        ├─► Evidence Normalization & Baseline Deviation (z-score)
        ├─► 9-Step Decision Hierarchy (Quality -> Environmental -> Baseline -> Conflict -> Context)
        ├─► Structured Explainability (Supporting, Suppressing, Uncertainty factors)
        └─► Immutable DB Record & Audit Versioning
```

---

## 3. Characterization Vocabulary

The system uses 6 mutually exclusive semantic analytical attention states (`RiskCharacterizationState`):

| Characterization State | Definition | Engineering Meaning |
| :--- | :--- | :--- |
| `INSUFFICIENT_EVIDENCE` | Data quality degraded or baseline too short | Interferometric coherence is low ($< 0.35$) or observations $< 3$ epochs. Capped at low confidence; precludes structural escalation. |
| `BASELINE` | Consistent with historical baseline | Observations remain within the nominal baseline stability envelope. No persistent deformation trend. |
| `ENVIRONMENTAL_PATTERN` | Dominated by seasonal/cyclical processes | Deformation is driven by recurring thermal/hydrological cycles. Structural persistence is actively suppressed. |
| `MONITOR` | Nascent persistence or model conflict | Deformation is emerging, volatile, or analytical models disagree. Continued observation is recommended. |
| `ELEVATED_ATTENTION` | Persistent multi-epoch deformation | Statistically significant trend deviating from nominal baseline with multi-epoch cross-model support. |
| `HIGH_ATTENTION` | Persistent deformation in critical context | Strong cross-model agreement, supported acceleration or high baseline deviation ($|z| \ge 2.5$), and critical zone overlap / high criticality. Prompts engineering investigation. |

---

## 4. Evidence Normalization & Formulations

All inputs are decomposed into transparent, bounded $[0.0, 1.0]$ components (`EvidenceComponents`):

### 1. Measurement Quality ($Q$)
$$Q = \left(0.6 \cdot \bar{\gamma} + 0.4 \cdot \bar{\phi}\right) \times \left(1.0 - \min(0.40, 0.05 \cdot N_{\text{missing}})\right)$$
- $\bar{\gamma}$: Mean interferometric coherence.
- $\bar{\phi}$: Mean phase stability index.
- $N_{\text{missing}}$: Missing acquisition epochs.

### 2. Consensus Support ($S$)
$$S = 0.6 \cdot \bar{A} + 0.4 \cdot \bar{C}$$
- $\bar{A}$: Mean cross-model agreement score from Phase 5.
- $\bar{C}$: Mean consensus confidence.

### 3. Temporal Persistence ($P$)
Multi-epoch structural persistence score from Phase 6. Subject to the Environmental Recurrence Guard ($P \equiv 0.0$ if seasonal cycles recur).

### 4. Trend Significance ($T_{\text{sig}}$)
$$T_{\text{sig}} = \min\left(1.0, \frac{|\text{trend\_rate}|}{v_{\text{ref}}}\right)$$
- $v_{\text{ref}}$: Infrastructure reference range (prototype default $10.0\text{ mm/year}$).

### 5. Supported Acceleration Score ($A_{\text{supp}}$)
$$\text{If } \text{acceleration\_supported} = \text{False}: \quad A_{\text{supp}} \equiv 0.0$$
$$\text{If } \text{acceleration\_supported} = \text{True}: \quad A_{\text{supp}} = \min\left(1.0, \frac{|\text{apparent\_accel}|}{5 \cdot v_{\text{ref}}}\right)$$
*Strict Phase 6.2 adherence: Unsupported mathematical acceleration is never treated as supported deformation acceleration.*

### 6. Environmental Suppression ($E_{\text{supp}}$)
$$E_{\text{supp}} = 1.0 \quad \text{if } \text{temporal\_status} == \text{ENVIRONMENTAL\_PATTERN}$$

### 7. Critical Zone Context ($C_{\text{zone}}$)
$$C_{\text{zone}} = \min\left(1.50, 1.0 + 0.25 \cdot (w_{\text{max}} - 1.0) + 0.15\right) \quad \text{if } P > 0.20 \text{ or } T_{\text{sig}} > 0.20$$
Modulates attention only when structural deformation evidence exists; cannot manufacture risk.

### 8. Standardized Baseline Deviation ($z$)
$$z = \frac{d_{\text{recent}} - \mu_{\text{base}}}{\sigma_{\text{base}}} \quad \text{when } \sigma_{\text{base}} > 0.05\text{ mm and } N_{\text{base}} \ge 5$$

---

## 5. The 9-Step Decision Hierarchy

1. **Step 1 (Quality Guard)**: If `temporal_status == LOW_QUALITY` or $Q < 0.35$ or $N < 3 \longrightarrow \text{INSUFFICIENT\_EVIDENCE}$. Downstream criticality CANNOT override this.
2. **Step 2 (Environmental Suppression)**: If `temporal_status == ENVIRONMENTAL_PATTERN` or $E_{\text{supp}} \ge 0.80 \longrightarrow \text{ENVIRONMENTAL\_PATTERN}$.
3. **Step 3 (Baseline Stability)**: If `temporal_status == BASELINE` and displacement remains within baseline envelope $\longrightarrow \text{BASELINE}$.
4. **Step 4 (Model Conflict)**: If `temporal_status == CONFLICTED` or $S < 0.35 \longrightarrow \text{MONITOR}$.
5. **Step 5 (Insufficient Persistence)**: If structural observations $< 2$ or $P < 0.20 \longrightarrow \text{MONITOR}$.
6. **Step 6 (Persistent Structural Evidence)**: Evaluates persistence $P \ge 0.20$ and consensus $S \ge 0.35$.
7. **Step 7 (Baseline Deviation & Acceleration)**: Checks whether $|z| \ge 2.5$ and whether acceleration is supported.
8. **Step 8 (Critical Zone & Criticality Modulation)**:
   - $P \ge 0.55$, $S \ge 0.55$, and (Critical Zone match or Criticality in {HIGH, CRITICAL} or $A_{\text{supp}} > 0.25$ or $|z| \ge 3.0$) $\longrightarrow \text{HIGH\_ATTENTION}$.
   - $P \ge 0.35$ and $S \ge 0.45 \longrightarrow \text{ELEVATED\_ATTENTION}$.
   - Otherwise $\longrightarrow \text{MONITOR}$.
9. **Step 9 (Synthesis & Bound Calculation)**: Computes bounded prototype characterization index decomposed across factors.

---

## 6. API Endpoints

- `POST /api/v1/infrastructure/{infrastructure_id}/profile`: Update structural material, criticality, critical zones, baseline, and expected behavior.
- `GET /api/v1/infrastructure/{infrastructure_id}/profile`: Retrieve current engineering profile.
- `POST /api/v1/infrastructure/{infrastructure_id}/risk-characterization`: Run and persist immutable characterization.
- `GET /api/v1/infrastructure/{infrastructure_id}/risk-characterization`: Retrieve latest characterization or full history (`?history=true`).

---

## 7. Scientific Limitations

1. **InSAR Measures Kinematics, Not Stress**: InSAR observes displacement of reflecting surfaces. Internal stress, structural fatigue, and internal crack propagation cannot be directly measured by satellite radar.
2. **Resolution Limits**: Sentinel-1 spatial resolution ($\approx 5\text{ m} \times 20\text{ m}$) may average across multiple structural components. High-resolution SAR (e.g. TerraSAR-X) is needed for sub-element zone resolution.
3. **Prototype Assumptions**: Reference deformation ranges and weighting parameters are prototype assumptions and require empirical calibration with real civil structural instrumentation.
4. **No Autonomous Intervention**: STRATA provides analytical decision-support for human structural engineers; it never initiates automated structural actions or evacuations.
