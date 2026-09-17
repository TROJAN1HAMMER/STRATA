import math
from typing import List, Optional, Tuple
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import TemporalEvidence, TemporalTrendPattern

# Noise floor below which displacement is treated as stable/negligible
STABLE_DEFORMATION_THRESHOLD_MM: float = 1.0  # PROTOTYPE_ASSUMPTION
ABRUPT_JUMP_THRESHOLD_MM: float = 5.0  # PROTOTYPE_ASSUMPTION


def evaluate_temporal_consistency(observations: List[ObservationRead]) -> TemporalEvidence:
    """
    Evaluates observable multi-epoch temporal properties:
    - Persistence
    - Directional consistency
    - Rate consistency
    - Abrupt inconsistency
    - Data sufficiency
    - Qualitative trend pattern
    """
    epoch_count = len(observations)
    explanations: List[str] = []

    # Data sufficiency curve
    if epoch_count == 0:
        sufficiency = 0.0
    elif epoch_count == 1:
        sufficiency = 0.20
    elif epoch_count == 2:
        sufficiency = 0.40
    elif epoch_count == 3:
        sufficiency = 0.65
    elif epoch_count == 4:
        sufficiency = 0.85
    else:
        sufficiency = 1.0

    if epoch_count < 2:
        explanations.append(f"Sequence contains only {epoch_count} epoch(s); insufficient temporal history.")
        return TemporalEvidence(
            persistence=None,
            directional_consistency=None,
            rate_consistency=None,
            abrupt_inconsistency_score=0.0,
            data_sufficiency=sufficiency,
            trend_pattern=TemporalTrendPattern.INSUFFICIENT_DATA,
            epoch_count=epoch_count,
            explanation=explanations,
        )

    # Extract displacement sequence
    displacements: List[float] = []
    for obs in observations:
        d = obs.los_displacement_mm if obs.los_displacement_mm is not None else obs.deformation_mm
        if d is not None:
            displacements.append(d)

    if len(displacements) < 2:
        explanations.append("Fewer than 2 valid displacement values present in sequence.")
        return TemporalEvidence(
            persistence=None,
            directional_consistency=None,
            rate_consistency=None,
            abrupt_inconsistency_score=0.0,
            data_sufficiency=sufficiency,
            trend_pattern=TemporalTrendPattern.UNDETERMINED,
            epoch_count=epoch_count,
            explanation=explanations,
        )

    # 1. Evaluate Persistence:
    # Does deformation exceed the stable noise floor and persist across epochs?
    active_epochs = [d for d in displacements if abs(d) >= STABLE_DEFORMATION_THRESHOLD_MM]
    if not active_epochs:
        persistence = 0.0
        explanations.append(
            f"All observed displacements are within nominal stability margin (+/-{STABLE_DEFORMATION_THRESHOLD_MM} mm)."
        )
    else:
        persistence = round(len(active_epochs) / len(displacements), 3)
        explanations.append(
            f"Deformation observed in {len(active_epochs)}/{len(displacements)} epochs (persistence: {persistence:.2f})."
        )

    # 2. Directional Consistency:
    # Do active deformations share the same vector sign?
    if active_epochs:
        pos_count = sum(1 for d in active_epochs if d > 0)
        neg_count = sum(1 for d in active_epochs if d < 0)
        directional_consistency = round(max(pos_count, neg_count) / len(active_epochs), 3)
        direction_str = "subsidence/negative LOS" if neg_count >= pos_count else "uplift/positive LOS"
        explanations.append(
            f"Directional consistency: {directional_consistency:.2f} predominantly toward {direction_str}."
        )
    else:
        directional_consistency = 1.0  # Consistently zero/stable

    # 3. Incremental Steps, Rate Consistency, and Abrupt Inconsistency
    increments: List[float] = []
    reversals = 0
    for i in range(len(displacements) - 1):
        inc = displacements[i + 1] - displacements[i]
        increments.append(inc)

    for i in range(len(increments) - 1):
        inc1 = increments[i]
        inc2 = increments[i + 1]
        # Check for immediate sharp sign reversal
        if (inc1 * inc2 < -1e-4) and (abs(inc1) >= ABRUPT_JUMP_THRESHOLD_MM or abs(inc2) >= ABRUPT_JUMP_THRESHOLD_MM):
            reversals += 1

    abrupt_inconsistency_score = round(min(1.0, reversals * 0.5), 2)
    if reversals > 0:
        explanations.append(f"Detected {reversals} abrupt deformation jump-and-reversal event(s).")

    # Rate consistency: relative variance of increments
    if len(increments) >= 2:
        mean_inc = sum(increments) / len(increments)
        var_inc = sum((x - mean_inc) ** 2 for x in increments) / len(increments)
        std_inc = math.sqrt(var_inc)
        # Ratio of mean increment to spread
        spread_ratio = std_inc / (abs(mean_inc) + 1.0)
        rate_consistency = round(max(0.0, min(1.0, 1.0 / (1.0 + spread_ratio))), 3)
    else:
        rate_consistency = 1.0

    # 4. Trend Pattern Determination
    trend_pattern = determine_trend_pattern(displacements, increments, active_epochs, reversals)
    explanations.append(f"Identified qualitative trend pattern: {trend_pattern.value}.")

    total_disp = displacements[-1] - displacements[0]

    return TemporalEvidence(
        persistence=persistence,
        directional_consistency=directional_consistency,
        rate_consistency=rate_consistency,
        abrupt_inconsistency_score=abrupt_inconsistency_score,
        data_sufficiency=sufficiency,
        trend_pattern=trend_pattern,
        total_displacement_mm=round(total_disp, 3),
        epoch_count=epoch_count,
        explanation=explanations,
    )


def determine_trend_pattern(
    displacements: List[float],
    increments: List[float],
    active_epochs: List[float],
    reversals: int,
) -> TemporalTrendPattern:
    """Classifies qualitative temporal trend pattern from displacement trajectory."""
    max_abs = max(abs(d) for d in displacements)
    if max_abs < STABLE_DEFORMATION_THRESHOLD_MM:
        return TemporalTrendPattern.STABLE

    if reversals >= 2:
        return TemporalTrendPattern.VOLATILE

    # Check for monotonic progression
    is_strictly_decreasing = all(displacements[i] >= displacements[i + 1] - 0.2 for i in range(len(displacements) - 1))
    is_strictly_increasing = all(displacements[i] <= displacements[i + 1] + 0.2 for i in range(len(displacements) - 1))

    if is_strictly_decreasing or is_strictly_increasing:
        # Check if rate is accelerating: |inc_{i+1}| > |inc_i| consistently
        abs_incs = [abs(inc) for inc in increments]
        if len(abs_incs) >= 3 and all(abs_incs[i] <= abs_incs[i + 1] + 0.1 for i in range(len(abs_incs) - 1)) and (abs_incs[-1] > abs_incs[0] * 1.5):
            return TemporalTrendPattern.ACCELERATING
        return TemporalTrendPattern.MONOTONIC

    # Check for periodic / seasonal oscillation (crosses baseline with bounded amplitude)
    signs = [1 if d > 0.5 else (-1 if d < -0.5 else 0) for d in displacements]
    non_zero_signs = [s for s in signs if s != 0]
    sign_changes = sum(1 for i in range(len(non_zero_signs) - 1) if non_zero_signs[i] != non_zero_signs[i + 1])
    if sign_changes >= 2 and max_abs < 15.0:
        return TemporalTrendPattern.PERIODIC_SEASONAL

    # Check for transient spike: an isolated large step followed immediately by a return
    if len(displacements) >= 3:
        for i in range(1, len(displacements) - 1):
            jump_1 = displacements[i] - displacements[i - 1]
            jump_2 = displacements[i] - displacements[i + 1]
            if abs(jump_1) >= 5.0 and abs(jump_2) >= 5.0 and (jump_1 * jump_2 > 0):
                return TemporalTrendPattern.TRANSIENT

    if reversals > 0:
        return TemporalTrendPattern.VOLATILE

    return TemporalTrendPattern.UNDETERMINED
