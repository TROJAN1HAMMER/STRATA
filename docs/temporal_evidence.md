# STRATA — Temporal Evidence Layer (Phase 6)

## 1. Purpose & Core Scientific Principle

The STRATA Temporal Evidence Layer transforms individual epoch-level cross-model consensus assessments into an auditable, longitudinal evidence trajectory over time.

### Central Principle
STRATA evaluates satellite radar interferometry (InSAR) across multi-epoch baselines. The system adheres to a strict scientific boundary:

> **Temporal persistence is evidence accumulation, not proof of structural deformation or damage.**

The system does NOT claim that:
- Persistent deformation proves structural damage
- Deformation predicts collapse or structural failure
- The infrastructure is unsafe or safe
- The system provides an engineering safety certification
- ML classification alone establishes structural failure

Environmental processes (such as seasonal thermal expansion and hydrologic swelling) and atmospheric phase screen delays can also be persistent and temporally coherent. The temporal evidence layer maintains this distinction.

> [!IMPORTANT]
> **Prototype Status Disclaimer**:
> *"The Phase 6 temporal formulations, persistence coefficients, and kinematic thresholds are transparent prototype assumptions and have not yet been empirically validated on real-world civil infrastructure data. No final risk score or safety certification is asserted."*

---

## 2. Architecture & Evidence Pipeline

```
Observation Sequence (Multi-Epoch)
  │
  ├─► [ordering.py] Canonical ordering (oldest -> newest), deduplication, interval tracking (dt)
  │
  ├─► [consensus/engine.py] Progressive consensus history evaluation per prefix
  │
  ├─► [kinematics.py] Elapsed-time trend rate (mm/year) & apparent acceleration (mm/year²)
  │
  ├─► [persistence.py] Structural persistence scoring with Environmental Recurrence Guard
  │
  └─► [state_machine.py] Sequential 9-state temporal evolution and transition auditing
        │
        ▼
   TemporalEvidenceSummary (Physical units: mm, mm/year, mm/year², days)
```

---

## 3. Temporal Status Vocabulary & State Machine

The temporal layer defines 9 mutually exclusive analytical states (`TemporalStatus`):

| Temporal Status | Definition | Scientific Meaning |
| :--- | :--- | :--- |
| `INSUFFICIENT_HISTORY` | $< 3$ valid observation epochs | Baseline is too short to establish any longitudinal pattern. |
| `BASELINE` | Consistent nominal stability | Observations exhibit displacement near zero with stable radar coherence. |
| `EMERGING` | $\ge 2$ structural consensus candidates | Initial coherent deformation signal is beginning to emerge across recent epochs. |
| `PERSISTENT` | $\ge 4$ structural candidates with high persistence | Observed deformation evidence has persisted across multiple epochs with cross-model support. *(Does NOT mean structural damage).* |
| `REVERTED` | Previous `EMERGING` or `PERSISTENT` signal returning to stable | A previously identified deformation signal has attenuated or ceased. |
| `ENVIRONMENTAL_PATTERN` | Recurring seasonal / thermal cycles | Cyclical zero-crossings and periodic oscillations are present. Defends environmental baseline. |
| `ATMOSPHERIC_EVENT` | Isolated transient phase delay anomaly | Transient phase jump was detected and subsequently resolved back to nominal baseline. |
| `CONFLICTED` | Material conflict between analytical models | Analytical engines disagree on high-amplitude deformation or disagree across environmental vs structural interpretations. |
| `LOW_QUALITY` | Low coherence or severe noise across baseline | Interferometric measurements are degraded; confidence is capped ($\le 0.35$). |

### State Transitions (`TemporalStateTransition`)
Every transition between states is recorded chronologically with:
- `previous_state`
- `new_state`
- `observation_id`
- `timestamp`
- `reason` (causal justification)
- `confidence_before` and `confidence_after`

### Stable Baseline vs Meaningful Conflict Distinction (Phase 6.1)
An essential scientific refinement introduced in Phase 6.1 prevents low-amplitude noise jitter around zero displacement from triggering an inappropriate `CONFLICTED` state:
- **Low-Amplitude Model Sensitivity around Baseline**: When displacements remain within the nominal InSAR stability envelope (maximum absolute displacement $\le 5.0\text{ mm}$, peak-to-peak variation $\le 8.0\text{ mm}$, linear rate $\le 5.0\text{ mm/year}$, adequate coherence $\ge 0.60$, absence of confirmed seasonal or atmospheric cycles), minor divergence in model class probabilities reflects near-zero baseline sensitivity. The temporal state machine classifies these sequences as `BASELINE`.
- **Meaningful Conflict**: When cross-model disagreement occurs alongside significant deformation exceeding the baseline stability envelope, or between incompatible deformation mechanisms (e.g., `ENVIRONMENTAL_STRUCTURAL_CONFLICT` or `ATMOSPHERIC_STRUCTURAL_CONFLICT`), the sequence evaluates to `CONFLICTED`.

---

## 4. Kinematics: Trend Rate, Apparent Acceleration, & Acceleration Support

### Irregular Acquisition Intervals
Satellite InSAR acquisitions do not arrive on a perfectly regular grid. STRATA strictly avoids calculating velocities as $\frac{\Delta d}{\Delta \text{epoch}}$. Instead, kinematics use real elapsed timestamps converted to years ($1 \text{ year} = 365.25 \text{ days}$):

$$t_i = \frac{T_i - T_0}{365.25 \times 86400} \quad [\text{years}]$$

### Linear Deformation Trend Rate ($\text{mm/year}$)
Calculated via ordinary least squares linear regression:

$$\text{trend\_rate} = \frac{\sum_{i=1}^N (t_i - \bar{t})(d_i - \bar{d})}{\sum_{i=1}^N (t_i - \bar{t})^2} \quad [\text{mm/year}]$$

- Requires $\ge 3$ valid observation epochs and total baseline $> 1.0$ day.
- Returns `None` if data is insufficient.

### Apparent Acceleration ($\text{mm/year}^2$)
Calculated by fitting a 2nd-order polynomial $d(t) = a t^2 + b t + c$:

$$\text{apparent\_acceleration} = 2a \quad [\text{mm/year}^2]$$

- Requires $\ge 5$ observation epochs and total coverage span $\ge 30.0$ days.
- Labeled neutrally as **"observed deformation-rate change"** or **"apparent acceleration in measured deformation trend"**.
- Never called "failure acceleration", "collapse rate", or "collapse prediction".

### Supported Acceleration Evidence vs Mathematical Fit (Phase 6.1 & Phase 6.2)
A mathematically computed 2nd derivative does not automatically constitute scientifically meaningful acceleration evidence. Annualized acceleration estimates over short baselines are subject to extreme $(365.25/T)^2$ noise magnification, where sub-millimeter errors can produce thousands of apparent $\text{mm/year}^2$. Furthermore, low-amplitude stable baseline sequences can exhibit subtle non-zero mathematical curvature from random phase noise.

STRATA enforces a strict three-tier scientific distinction:
$$\text{Mathematically Computed} \longrightarrow \text{Evidence-Supported} \longrightarrow \text{Structurally Interpretable}$$

1. `apparent_acceleration_mm_per_year2`: The numerical calculation is strictly preserved.
2. `acceleration_supported`: A boolean flag indicating whether the apparent acceleration satisfies explicit sufficiency criteria AND represents non-baseline deformation evidence.
3. `acceleration_support_reason`: Transparent physical justification for why acceleration is or is not supported.

#### Acceleration Support Criteria (Documented Prototype Assumptions)
All thresholds are explicitly documented as **prototype assumptions** and are not claimed as validated external standards:
0. **Baseline Stability Guard (Phase 6.2)**: Sequences remaining within the nominal baseline stability envelope and lacking independent structural deformation evidence evaluate to `acceleration_supported = False` with the explanation:
   > *"Apparent acceleration is mathematically detectable, but the sequence remains within the nominal baseline stability envelope and is not treated as supported deformation acceleration."*
1. **Observation Count Sufficiency**: $N \ge 6$ observation epochs (ensures $N - 3 \ge 3$ statistical degrees of freedom). *(Prototype assumption)*
2. **Temporal Baseline Sufficiency**: Total temporal coverage $\ge 90.0$ days ($\approx 3$ months) to prevent short-baseline annualization noise magnification. *(Prototype assumption)*
3. **Temporal Spacing**: Maximum interval gap between consecutive observations must not exceed $70\%$ of the total baseline (avoids endpoint clustering). *(Prototype assumption)*
4. **Interferometric Coherence**: Mean coherence $\ge 0.65$ across the sequence (prevents phase decorrelation noise from corrupting derivatives). *(Prototype assumption)*
5. **Kinematic Signal Amplitude**: Peak-to-peak displacement $\ge 2.0\text{ mm}$ (ensures signal exceeds the nominal satellite phase noise floor). *(Prototype assumption)*
6. **Multi-Interval Rate Consistency**: Independent linear rates fitted across split halves of the observation sequence must show velocity progression agreeing in sign with the 2nd derivative. *(Prototype assumption)*
7. **Residual Scatter Ratio**: Root Mean Square Error (RMSE) of the quadratic fit relative to displacement amplitude must not exceed $0.40$. *(Prototype assumption)*

#### Baseline Envelope Guard: Unsupported Acceleration $\neq$ Baseline Stability (Phase 6.2)
A critical scientific principle is that **insufficient temporal evidence $\neq$ evidence of baseline stability**.
When an observation sequence has temporal coverage below the acceleration-support threshold ($< 90$ days) or high curvature/conflict, but displays non-negligible deformation or active cross-model conflict (e.g. `STRUCTURAL_ACCELERATING` with high apparent acceleration), the state machine does **NOT** force the sequence into `BASELINE`. Instead, it conservatively maintains `CONFLICTED` or `INSUFFICIENT_HISTORY`. Nominal `BASELINE` is reserved solely for sequences whose evidence genuinely supports baseline stability.

When temporal coverage or evidence consistency is insufficient, the system reports:
> *"A numerical acceleration was calculated ($X\text{ mm/year}^2$), but the available temporal coverage is insufficient to treat it as supported acceleration evidence."*

## 5. Structural Persistence & Environmental Recurrence Guard

### Formulation
$$\text{persistence\_score} = \left(0.45 \cdot f_{struct} + 0.25 \cdot \bar{A} + 0.20 \cdot \bar{C} + 0.10 \cdot \bar{Q}\right) \times (1.0 - \text{penalty}_{gap})$$

- $f_{struct}$: Proportion of structurally interpreted observations.
- $\bar{A}$: Mean cross-model agreement score.
- $\bar{C}$: Mean consensus confidence.
- $\bar{Q}$: Mean observation quality score.
- $\text{penalty}_{gap} = \min(0.50, 0.08 \times \text{missing\_epochs})$.

### Environmental Recurrence Guard
If cyclical seasonal signals recur ($f_{seasonal} \ge 0.40$ or $f_{seasonal} > f_{struct}$ with $\ge 2$ seasonal epochs):
$$\text{persistence\_score} \equiv 0.0$$
This guarantees that **recurring seasonal/environmental fluctuations cannot accumulate into false-positive structural persistence**.

---

## 6. Programmatic Leakage Firewall

The temporal engine enforces a recursive firewall (`_verify_temporal_leakage`). Any input dictionary or object containing hidden synthetic generator parameters is immediately blocked:
- `true_structural_displacement_mm`, `true_environmental_displacement_mm`, `true_atmospheric_displacement_mm`, `true_noise_mm`
- `ground_truth_class`, `seasonal_amplitude_mm`, `seasonal_period_days`, `linear_velocity_mm_yr`, `acceleration_mm_yr2`
- `step_epoch_idx`, `step_magnitude_mm`, `noise_std_mm`, `spatial_wavelength_m`, `spike_magnitude_mm`

---

## 7. Scientific Limitations

1. **Persistence is Not Damage**: Coherent persistent movement can arise from non-damaging geotechnical settlement, groundwater variations, or thermal effects.
2. **Seasonal Recurrence**: Long temporal baselines ($> 1$ year) are needed to separate annual seasonal cycles from slow progressive monotonic creep.
3. **Atmospheric Artifacts**: Large localized turbulent atmospheric phase screens can mimic abrupt step displacements.
4. **Irregular Sampling**: Extended gaps in satellite acquisitions reduce confidence in continuous persistence claims.
5. **No Safety Certification**: STRATA outputs indicate analytical evidence strength; they do not certify structural integrity.
