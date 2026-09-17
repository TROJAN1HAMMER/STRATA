from typing import List, Optional
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import (
    EnvironmentalEvidence,
    TemporalEvidence,
    TemporalTrendPattern,
)

# Prototype thresholds for seasonal/environmental discrimination
SEASONAL_AMPLITUDE_MAX_MM: float = 25.0  # PROTOTYPE_ASSUMPTION: Typical thermal/reservoir deformation bound
SEASONAL_MIN_EPOCHS: int = 5  # PROTOTYPE_ASSUMPTION: Minimum epochs needed to identify a cycle
MIN_ZERO_CROSSINGS_FOR_CYCLE: int = 2  # PROTOTYPE_ASSUMPTION: At least two zero-crossings for periodic cycle


def evaluate_environmental_evidence(
    observations: List[ObservationRead],
    temporal_evidence: Optional[TemporalEvidence] = None,
) -> EnvironmentalEvidence:
    """
    Evaluates multi-epoch deformation trajectories to detect periodic environmental
    and seasonal thermal/reservoir loading signals.

    Distinguishes cyclic environmental oscillation from progressive structural deformation.
    """
    if len(observations) < SEASONAL_MIN_EPOCHS:
        return EnvironmentalEvidence(
            periodicity_detected=False,
            seasonal_pattern_strength=0.0,
            reversal_consistency=0.0,
            cycle_count=0,
            environmental_suspect_score=0.0,
            explanation=[
                f"Fewer than {SEASONAL_MIN_EPOCHS} epochs ({len(observations)}); "
                "insufficient time baseline to detect environmental periodicity."
            ],
        )

    displacements = [
        obs.los_displacement_mm if obs.los_displacement_mm is not None else obs.deformation_mm
        for obs in observations
    ]
    valid_disps = [d for d in displacements if d is not None]

    if len(valid_disps) < SEASONAL_MIN_EPOCHS:
        return EnvironmentalEvidence(
            periodicity_detected=False,
            seasonal_pattern_strength=0.0,
            reversal_consistency=0.0,
            cycle_count=0,
            environmental_suspect_score=0.0,
            explanation=["Insufficient valid displacement records for periodicity analysis."],
        )

    explanations: List[str] = []
    max_abs = max(abs(d) for d in valid_disps)

    # 1. Zero-Crossing and Sign Reversal Analysis
    signs = [1 if d > 0.5 else (-1 if d < -0.5 else 0) for d in valid_disps]
    non_zero_signs = [s for s in signs if s != 0]

    sign_changes = 0
    if len(non_zero_signs) >= 2:
        sign_changes = sum(
            1 for i in range(len(non_zero_signs) - 1) if non_zero_signs[i] != non_zero_signs[i + 1]
        )

    # 2. Reversal Regularity: Are there multiple epochs in positive and negative phases?
    pos_epochs = sum(1 for s in non_zero_signs if s > 0)
    neg_epochs = sum(1 for s in non_zero_signs if s < 0)
    balance_ratio = min(pos_epochs, neg_epochs) / max(pos_epochs, neg_epochs) if max(pos_epochs, neg_epochs) > 0 else 0.0

    # 3. Wave-like gradual continuity:
    # A genuine seasonal cycle has smooth steps rather than single-epoch impulse spikes
    step_increments = [abs(valid_disps[i + 1] - valid_disps[i]) for i in range(len(valid_disps) - 1)]
    max_step = max(step_increments) if step_increments else 0.0
    mean_step = sum(step_increments) / len(step_increments) if step_increments else 0.0

    # Smoothness factor: ratio of mean step to max step (higher means gradual continuous wave)
    smoothness = round(mean_step / max_step, 3) if max_step > 0 else 1.0

    # 4. Periodicity criteria
    # Must have bounded amplitude, at least 2 zero-crossings, and balanced positive/negative phases
    is_periodic = (
        sign_changes >= MIN_ZERO_CROSSINGS_FOR_CYCLE
        and max_abs <= SEASONAL_AMPLITUDE_MAX_MM
        and balance_ratio >= 0.30
        and (temporal_evidence is None or temporal_evidence.trend_pattern == TemporalTrendPattern.PERIODIC_SEASONAL)
    )

    if is_periodic:
        # High seasonal pattern strength
        strength = round(min(1.0, 0.50 + (sign_changes * 0.15) + (balance_ratio * 0.20)), 3)
        reversal_consistency = round(min(1.0, balance_ratio * smoothness * 1.2), 3)
        suspect_score = round(min(1.0, strength * 0.70 + reversal_consistency * 0.30), 3)

        explanations.append(
            f"Detected periodic zero-crossing oscillation ({sign_changes} sign changes across {len(valid_disps)} epochs)."
        )
        explanations.append(
            f"Displacement amplitude is bounded ({max_abs:.2f} mm <= {SEASONAL_AMPLITUDE_MAX_MM} mm); "
            f"seasonal pattern strength: {strength:.2f}."
        )
        explanations.append(
            "Trajectory aligns with annual cyclic environmental/thermal expansion rather than monotonic structural settlement."
        )
    else:
        strength = round(min(0.40, sign_changes * 0.10), 3)
        reversal_consistency = round(balance_ratio * 0.30, 3)
        suspect_score = round(strength * 0.50, 3)

        if sign_changes < MIN_ZERO_CROSSINGS_FOR_CYCLE:
            explanations.append(
                f"No recurring zero-crossing cycles detected ({sign_changes} sign change(s)); non-periodic signal."
            )
        elif max_abs > SEASONAL_AMPLITUDE_MAX_MM:
            explanations.append(
                f"Peak displacement ({max_abs:.2f} mm) exceeds typical seasonal bounds ({SEASONAL_AMPLITUDE_MAX_MM} mm)."
            )
        else:
            explanations.append("Signal does not exhibit characteristic cyclic environmental pattern.")

    return EnvironmentalEvidence(
        periodicity_detected=is_periodic,
        seasonal_pattern_strength=strength,
        reversal_consistency=reversal_consistency,
        cycle_count=sign_changes,
        environmental_suspect_score=suspect_score,
        explanation=explanations,
    )
