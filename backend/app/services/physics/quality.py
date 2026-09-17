from typing import List, Optional, Tuple
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import MeasurementQualityEvidence

# Explicit Scientific & Prototype Assumptions
# Coherence above 0.70 indicates high interferometric phase stability (literature standard).
# Coherence below 0.25 indicates dominant decorrelation noise.
COHERENCE_HIGH_THRESHOLD: float = 0.70
COHERENCE_MODERATE_THRESHOLD: float = 0.40
COHERENCE_NOISE_FLOOR: float = 0.25  # PROTOTYPE_ASSUMPTION

PHASE_QUALITY_HIGH_THRESHOLD: float = 0.70  # PROTOTYPE_ASSUMPTION
PHASE_QUALITY_MODERATE_THRESHOLD: float = 0.40  # PROTOTYPE_ASSUMPTION


def evaluate_coherence(coherence: Optional[float]) -> Tuple[Optional[float], bool, str]:
    """
    Evaluates individual epoch coherence against named interferometric thresholds.
    Returns (normalized_score, is_sufficient, explanation).
    """
    if coherence is None:
        return None, False, "Coherence measurement missing; interferometric reliability cannot be confirmed."

    if not (0.0 <= coherence <= 1.0):
        raise ValueError(f"Coherence {coherence} is outside physical domain [0.0, 1.0].")

    if coherence >= COHERENCE_HIGH_THRESHOLD:
        return (
            coherence,
            True,
            f"High coherence ({coherence:.2f} >= {COHERENCE_HIGH_THRESHOLD}); strong interferometric phase stability.",
        )
    elif coherence >= COHERENCE_MODERATE_THRESHOLD:
        return (
            coherence,
            True,
            f"Moderate coherence ({coherence:.2f} in [{COHERENCE_MODERATE_THRESHOLD}, {COHERENCE_HIGH_THRESHOLD}]); acceptable measurement confidence.",
        )
    elif coherence >= COHERENCE_NOISE_FLOOR:
        return (
            coherence,
            False,
            f"Degraded coherence ({coherence:.2f} < {COHERENCE_MODERATE_THRESHOLD}); increased phase noise risk.",
        )
    else:
        return (
            coherence,
            False,
            f"Severely decorrelated epoch ({coherence:.2f} < {COHERENCE_NOISE_FLOOR}); noise dominated.",
        )


def evaluate_phase_quality(phase_quality: Optional[float]) -> Tuple[Optional[float], str]:
    """
    Evaluates interferometric phase quality metric [0.0, 1.0].
    Returns (normalized_score, explanation).
    """
    if phase_quality is None:
        return None, "Phase quality metric omitted from observation metadata."

    if not (0.0 <= phase_quality <= 1.0):
        raise ValueError(f"Phase quality {phase_quality} is outside physical domain [0.0, 1.0].")

    if phase_quality >= PHASE_QUALITY_HIGH_THRESHOLD:
        return phase_quality, f"High phase quality ({phase_quality:.2f} >= {PHASE_QUALITY_HIGH_THRESHOLD})."
    elif phase_quality >= PHASE_QUALITY_MODERATE_THRESHOLD:
        return phase_quality, f"Moderate phase quality ({phase_quality:.2f})."
    else:
        return phase_quality, f"Low phase quality ({phase_quality:.2f} < {PHASE_QUALITY_MODERATE_THRESHOLD}); phase unwrapping artifact risk."


def evaluate_measurement_quality(observations: List[ObservationRead]) -> MeasurementQualityEvidence:
    """
    Aggregates multi-epoch measurement quality evidence.
    Does NOT collapse into an arbitrary black-box score; preserves explanations.
    """
    if not observations:
        return MeasurementQualityEvidence(
            quality_score=0.0,
            coherence_score=None,
            phase_quality_score=None,
            missing_fields_count=0,
            has_sufficient_coherence=False,
            explanation=["No observations available for measurement quality evaluation."],
        )

    coherence_vals = [obs.coherence for obs in observations if obs.coherence is not None]
    phase_vals = [obs.phase_quality for obs in observations if obs.phase_quality is not None]

    missing_fields = 0
    for obs in observations:
        if obs.coherence is None:
            missing_fields += 1
        if obs.phase_quality is None:
            missing_fields += 1
        if obs.incidence_angle is None:
            missing_fields += 1
        if obs.los_displacement_mm is None and obs.deformation_mm is None:
            missing_fields += 1

    explanations: List[str] = []

    mean_coherence: Optional[float] = None
    has_sufficient_coherence = True
    if coherence_vals:
        mean_coherence = sum(coherence_vals) / len(coherence_vals)
        _, has_sufficient_coherence, coh_expl = evaluate_coherence(mean_coherence)
        explanations.append(f"Mean coherence across {len(coherence_vals)} epochs: {mean_coherence:.3f}. {coh_expl}")
    else:
        has_sufficient_coherence = False
        explanations.append("No valid coherence values present across observation sequence.")

    mean_phase_quality: Optional[float] = None
    if phase_vals:
        mean_phase_quality = sum(phase_vals) / len(phase_vals)
        _, phase_expl = evaluate_phase_quality(mean_phase_quality)
        explanations.append(f"Mean phase quality across {len(phase_vals)} epochs: {mean_phase_quality:.3f}. {phase_expl}")

    # Deterministic calculation of measurement quality score [0.0, 1.0]
    # Primary weight on mean coherence (60%) and phase quality (40%), penalized for missing data.
    quality_components: List[float] = []
    if mean_coherence is not None:
        quality_components.append(mean_coherence * 0.6)
    if mean_phase_quality is not None:
        quality_components.append(mean_phase_quality * 0.4)

    if not quality_components:
        overall_score = 0.0
    else:
        base_score = sum(quality_components) / (0.6 if mean_phase_quality is None else 1.0)
        penalty = min(0.3, missing_fields * 0.05)
        overall_score = max(0.0, min(1.0, base_score - penalty))

    return MeasurementQualityEvidence(
        quality_score=round(overall_score, 3),
        coherence_score=round(mean_coherence, 3) if mean_coherence is not None else None,
        phase_quality_score=round(mean_phase_quality, 3) if mean_phase_quality is not None else None,
        missing_fields_count=missing_fields,
        has_sufficient_coherence=has_sufficient_coherence,
        explanation=explanations,
    )
