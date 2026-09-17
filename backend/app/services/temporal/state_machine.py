"""
Temporal State Machine for STRATA multi-epoch evidence evolution.
Tracks deterministic transitions between 9 analytical states with full causal auditing.
Scientifically distinguishes between material cross-model conflicts and low-amplitude baseline sensitivity.
"""
from datetime import datetime
from typing import Any, List, Optional, Tuple
import numpy as np

from backend.app.schemas.consensus import ConsensusAssessment, ConsensusCategory, ConsensusFlag
from backend.app.schemas.temporal import TemporalStateTransition, TemporalStatus
from backend.app.services.temporal.kinematics import (
    DAYS_PER_YEAR,
    _extract_displacement_mm,
)
from backend.app.services.temporal.ordering import _get_id, _get_timestamp

MIN_HISTORY_EPOCHS = 3
PERSISTENT_STRUCTURAL_MIN_EPOCHS = 4
EMERGING_STRUCTURAL_MIN_EPOCHS = 2

# Baseline Stability Envelope Thresholds (Documented PROTOTYPE ASSUMPTIONS)
# For sequences without positive consensus deformation, signals within these bounds
# represent nominal interferometric phase noise rather than material structural conflict.
BASELINE_MAX_ABS_DISP_MM = 5.0  # PROTOTYPE_ASSUMPTION: single-look InSAR phase noise floor
BASELINE_MAX_PTP_DISP_MM = 8.0  # PROTOTYPE_ASSUMPTION: peak-to-peak noise margin
BASELINE_MAX_RATE_MM_YR = 5.0  # PROTOTYPE_ASSUMPTION: standard InSAR stability velocity threshold (5 mm/yr)
BASELINE_MIN_MEAN_COH = 0.60  # PROTOTYPE_ASSUMPTION: adequate coherence
BASELINE_MAX_APPARENT_ACCEL_MM_YR2 = 50.0  # PROTOTYPE_ASSUMPTION: rapid curvature exceeds baseline margin


def evaluate_temporal_state_machine(
    ordered_observations: List[Any],
    consensus_history: List[ConsensusAssessment],
) -> Tuple[TemporalStatus, List[TemporalStateTransition]]:
    """
    Executes sequential state machine over multi-epoch consensus history.
    Transitions are recorded incrementally at each epoch step.

    SCIENTIFIC INTEGRITY RULES:
      - Material conflict (e.g. seasonal vs structural, atmospheric vs structural, or
        high-amplitude disagreement) evaluates to CONFLICTED.
      - Disagreements occurring strictly within the nominal baseline noise envelope
        (<= 5.0 mm max disp, <= 5.0 mm/yr rate, <= 50 mm/yr² curvature) reflect model
        sensitivity near zero baseline, and preferentially remain BASELINE rather than CONFLICTED.
      - Unsupported acceleration does not imply stability: short volatile baselines with large
        curvature or recent conflict do NOT fall into BASELINE.
      - Environmental and atmospheric recurrence guards strictly prevent non-structural
        mechanisms from accumulating into structural persistence.

    Returns:
      (final_temporal_status, list_of_state_transitions)
    """
    if not ordered_observations or not consensus_history:
        return TemporalStatus.INSUFFICIENT_HISTORY, []

    transitions: List[TemporalStateTransition] = []
    current_state = TemporalStatus.INSUFFICIENT_HISTORY
    prev_conf = consensus_history[0].consensus_confidence

    for step_idx in range(len(consensus_history)):
        obs = ordered_observations[step_idx]
        obs_id = _get_id(obs)
        timestamp = _get_timestamp(obs)
        current_assessment = consensus_history[step_idx]
        current_conf = current_assessment.consensus_confidence

        history_window = consensus_history[: step_idx + 1]
        obs_window = ordered_observations[: step_idx + 1]
        n_epochs = len(history_window)

        # Determine target state at this temporal step
        target_state: TemporalStatus
        reason: str

        if n_epochs < MIN_HISTORY_EPOCHS:
            target_state = TemporalStatus.INSUFFICIENT_HISTORY
            reason = f"Baseline coverage is insufficient (< {MIN_HISTORY_EPOCHS} observation epochs)."

        else:
            # Tally categories in history window
            cats = [a.consensus_class for a in history_window]
            struct_count = cats.count(ConsensusCategory.STRUCTURAL)
            seasonal_count = cats.count(ConsensusCategory.SEASONAL)
            atmo_count = cats.count(ConsensusCategory.ATMOSPHERIC)
            low_qual_count = cats.count(ConsensusCategory.LOW_QUALITY)
            stable_count = cats.count(ConsensusCategory.STABLE)

            recent_3 = cats[-3:] if n_epochs >= 3 else cats
            latest_cat = cats[-1]
            latest_flags = current_assessment.flags

            # Kinematic and envelope metrics over current prefix
            disps = [
                _extract_displacement_mm(o)
                for o in obs_window
                if _extract_displacement_mm(o) is not None
            ]
            max_abs_disp = max(abs(d) for d in disps) if disps else 0.0
            ptp_disp = (max(disps) - min(disps)) if disps else 0.0

            coherences = [
                getattr(o, "coherence", None)
                or (o.get("coherence") if isinstance(o, dict) else None)
                or 0.80
                for o in obs_window
            ]
            coherences_float = [float(c) for c in coherences if isinstance(c, (int, float))]
            mean_coh = float(np.mean(coherences_float)) if coherences_float else 0.80

            # Compute preliminary trend rate and apparent acceleration if sufficient epochs
            rate_mm_yr = 0.0
            apparent_accel_mm_yr2 = 0.0
            span_days = 0.0
            if len(disps) >= 3:
                t0 = _get_timestamp(obs_window[0])
                times_yr = [
                    (_get_timestamp(o) - t0).total_seconds() / (86400.0 * DAYS_PER_YEAR)
                    for o in obs_window
                ]
                span_days = (times_yr[-1] - times_yr[0]) * DAYS_PER_YEAR
                t_arr = np.array(times_yr, dtype=np.float64)
                d_arr = np.array(disps, dtype=np.float64)
                denom = np.sum((t_arr - np.mean(t_arr)) ** 2)
                if denom > 1e-9:
                    rate_mm_yr = float(np.sum((t_arr - np.mean(t_arr)) * (d_arr - np.mean(d_arr))) / denom)
                if len(disps) >= 5:
                    try:
                        p_coeffs = np.polyfit(t_arr, d_arr, 2)
                        apparent_accel_mm_yr2 = float(2.0 * p_coeffs[0])
                    except (np.linalg.LinAlgError, ValueError):
                        apparent_accel_mm_yr2 = 0.0

            # Conflict history check: sequence must not have recent unresolved material conflicts
            has_recent_material_conflict = any(
                ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in a.flags
                or ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value in a.flags
                for a in history_window[-3:]
            )

            # Curvature check: rapid acceleration outside noise floor indicates non-baseline dynamics
            excessive_curvature = False
            if len(disps) >= 5:
                if span_days >= 90.0 and abs(apparent_accel_mm_yr2) > BASELINE_MAX_APPARENT_ACCEL_MM_YR2:
                    excessive_curvature = True
                elif span_days < 90.0 and ptp_disp > 4.0 and abs(apparent_accel_mm_yr2) > 500.0:
                    excessive_curvature = True

            # Determine if sequence is strictly within the nominal baseline noise envelope
            is_within_baseline_envelope = (
                max_abs_disp <= BASELINE_MAX_ABS_DISP_MM
                and ptp_disp <= BASELINE_MAX_PTP_DISP_MM
                and abs(rate_mm_yr) <= BASELINE_MAX_RATE_MM_YR
                and mean_coh >= BASELINE_MIN_MEAN_COH
                and (seasonal_count / n_epochs) < 0.40
                and struct_count <= 1
                and not excessive_curvature
                and not has_recent_material_conflict
            )

            # Rule 1: Low Quality dominance
            if (low_qual_count / n_epochs) >= 0.50 or latest_cat == ConsensusCategory.LOW_QUALITY:
                target_state = TemporalStatus.LOW_QUALITY
                reason = "Interferometric measurement quality is severely degraded across observation epochs."

            # Rule 2: Structural conflict / discrepancy
            elif (
                ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in latest_flags
                or ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value in latest_flags
            ):
                target_state = TemporalStatus.CONFLICTED
                reason = "Material cross-model conflict detected between structural and environmental/atmospheric evidence."

            elif ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value in latest_flags:
                if is_within_baseline_envelope:
                    target_state = TemporalStatus.BASELINE
                    reason = (
                        f"Displacements remain within nominal stability margin (max {max_abs_disp:.2f} mm <= {BASELINE_MAX_ABS_DISP_MM} mm); "
                        f"cross-model disagreement reflects low-amplitude sensitivity around the zero baseline rather than a material structural conflict."
                    )
                else:
                    target_state = TemporalStatus.CONFLICTED
                    reason = "Material cross-model disagreement observed with deformation or rate of change exceeding the baseline stability margin."

            # Rule 3: Recurring Environmental / Seasonal oscillation
            elif (seasonal_count / n_epochs) >= 0.40 or (seasonal_count >= 2 and latest_cat == ConsensusCategory.SEASONAL):
                target_state = TemporalStatus.ENVIRONMENTAL_PATTERN
                reason = "Recurring cyclical seasonal fluctuation detected. Signals are classified as environmental."

            # Rule 4: Atmospheric transient event
            elif atmo_count >= 1 and latest_cat in [ConsensusCategory.STABLE, ConsensusCategory.ATMOSPHERIC]:
                if latest_cat == ConsensusCategory.ATMOSPHERIC:
                    target_state = TemporalStatus.ATMOSPHERIC_EVENT
                    reason = "Transient phase delay anomaly detected, consistent with localized atmospheric disturbance."
                elif atmo_count >= 1 and stable_count >= 2 and current_state == TemporalStatus.ATMOSPHERIC_EVENT:
                    target_state = TemporalStatus.BASELINE
                    reason = "Atmospheric transient has cleared; observations have resumed nominal baseline stability."
                else:
                    target_state = TemporalStatus.BASELINE
                    reason = "Nominal stability observed across temporal sequence."

            # Rule 5: Signal Reversal (was EMERGING or PERSISTENT, now stable/zero displacement)
            elif (
                current_state in [TemporalStatus.EMERGING, TemporalStatus.PERSISTENT]
                and latest_cat == ConsensusCategory.STABLE
                and recent_3.count(ConsensusCategory.STABLE) >= 2
            ):
                target_state = TemporalStatus.REVERTED
                reason = "Previously identified deformation candidate signal has attenuated and returned to stable baseline."

            # Rule 6: Persistent Structural Candidate
            elif (
                struct_count >= PERSISTENT_STRUCTURAL_MIN_EPOCHS
                and (struct_count / n_epochs) >= 0.60
                and current_assessment.agreement_score >= 0.50
            ):
                target_state = TemporalStatus.PERSISTENT
                reason = (
                    f"Structural deformation candidate pattern has persisted across {struct_count} epochs "
                    f"with consistent cross-model agreement."
                )

            # Rule 7: Emerging Structural Candidate
            elif (
                struct_count >= EMERGING_STRUCTURAL_MIN_EPOCHS
                and latest_cat == ConsensusCategory.STRUCTURAL
            ):
                target_state = TemporalStatus.EMERGING
                reason = "Initial coherent structural deformation candidate pattern beginning to emerge across recent epochs."

            # Rule 8: Baseline Stability
            elif stable_count >= 2 and latest_cat == ConsensusCategory.STABLE:
                target_state = TemporalStatus.BASELINE
                reason = "Consistent nominal stability observed across multi-epoch observation sequence."

            else:
                # Default / Fallback
                if is_within_baseline_envelope:
                    target_state = TemporalStatus.BASELINE
                    reason = (
                        "Displacements fluctuate within the nominal noise floor without coherent deformation trend; "
                        "sequence represents baseline stability."
                    )
                elif latest_cat == ConsensusCategory.STRUCTURAL and struct_count == 1:
                    target_state = TemporalStatus.BASELINE
                    reason = "Isolated structural candidate insufficient to establish an emerging trend."
                else:
                    target_state = TemporalStatus.CONFLICTED
                    reason = "Heterogeneous multi-epoch interpretations without coherent temporal trend."

        # Record state transition if state changed
        if step_idx == 0 or target_state != current_state:
            transition = TemporalStateTransition(
                previous_state=current_state,
                new_state=target_state,
                observation_id=obs_id,
                timestamp=timestamp,
                reason=reason,
                confidence_before=round(prev_conf, 4),
                confidence_after=round(current_conf, 4),
            )
            transitions.append(transition)
            current_state = target_state

        prev_conf = current_conf

    return current_state, transitions
