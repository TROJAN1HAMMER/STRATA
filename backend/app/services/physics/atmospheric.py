from typing import List, Optional
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import AtmosphericEvidence, TemporalEvidence


def evaluate_atmospheric_suspect(
    observations: List[ObservationRead],
    temporal_evidence: Optional[TemporalEvidence] = None,
) -> AtmosphericEvidence:
    """
    Evaluates evidence of atmospheric contamination or environmental phase screen (APS) artifacts.
    Identifies transient spikes, rapid reversals, and explicitly logged atmospheric conditions.
    """
    if not observations:
        return AtmosphericEvidence(
            atmospheric_suspect_score=0.0,
            has_transient_spike=False,
            atmospheric_indicator_reported=None,
            atmospheric_data_status="ATMOSPHERIC_DATA_UNAVAILABLE",
            explanation=["No observations available for atmospheric assessment."],
        )

    indicators = [obs.atmospheric_indicator for obs in observations if obs.atmospheric_indicator is not None]
    explanations: List[str] = []

    # Check atmospheric indicator status
    if not indicators:
        atm_status = "ATMOSPHERIC_DATA_UNAVAILABLE"
        explanations.append("Atmospheric screen indicators omitted; atmospheric noise cannot be ruled out.")
        indicator_reported = None
        indicator_score = 0.0
    else:
        atm_status = "AVAILABLE"
        indicator_reported = "; ".join(set(indicators))
        # Check if known turbulent keywords appear
        turbulent_keywords = ["TURBULENCE", "TURBULENT", "APS", "STORM", "WATER_VAPOR", "ANOMALOUS", "HIGH_APS"]
        has_turbulent_flag = any(any(kw in ind.upper() for kw in turbulent_keywords) for ind in indicators)
        if has_turbulent_flag:
            indicator_score = 0.85
            explanations.append(f"Observation metadata explicitly flags atmospheric turbulence ({indicator_reported}).")
        else:
            indicator_score = 0.10
            explanations.append(f"Observation atmospheric metadata reports nominal conditions ({indicator_reported}).")

    # Check for transient spike: a sharp excursion that quickly returns to baseline
    displacements = [
        obs.los_displacement_mm if obs.los_displacement_mm is not None else obs.deformation_mm
        for obs in observations
    ]
    valid_disps = [d for d in displacements if d is not None]

    has_transient_spike = False
    if len(valid_disps) >= 3:
        for i in range(1, len(valid_disps) - 1):
            prev_d = valid_disps[i - 1]
            curr_d = valid_disps[i]
            next_d = valid_disps[i + 1]

            # Spike condition: current is significantly different from both neighbors, but neighbors are close to each other
            jump_1 = curr_d - prev_d
            jump_2 = curr_d - next_d
            baseline_diff = abs(next_d - prev_d)

            if abs(jump_1) >= 6.0 and abs(jump_2) >= 6.0 and (jump_1 * jump_2 > 0) and (baseline_diff <= 3.0):
                has_transient_spike = True
                explanations.append(
                    f"Transient spike detected at epoch index {i}: jumped to {curr_d:.1f} mm from {prev_d:.1f} mm "
                    f"and returned to {next_d:.1f} mm (typical turbulent atmospheric phase delay signature)."
                )
                break

    # Also factor in temporal abrupt inconsistency score if provided
    abrupt_score = temporal_evidence.abrupt_inconsistency_score if temporal_evidence else 0.0

    # Composite atmospheric suspect score [0.0, 1.0]
    spike_component = 0.60 if has_transient_spike else 0.0
    abrupt_component = abrupt_score * 0.30
    indicator_component = indicator_score * 0.40

    suspect_score = min(1.0, spike_component + abrupt_component + indicator_component)

    if suspect_score >= 0.60:
        explanations.append(
            f"Atmospheric suspect score is elevated ({suspect_score:.2f}); observed anomalies align with tropospheric phase screen behavior."
        )
    elif suspect_score < 0.25:
        explanations.append(
            f"Atmospheric suspect score is low ({suspect_score:.2f}); no characteristic transient APS signatures detected."
        )

    return AtmosphericEvidence(
        atmospheric_suspect_score=round(suspect_score, 3),
        has_transient_spike=has_transient_spike,
        atmospheric_indicator_reported=indicator_reported,
        atmospheric_data_status=atm_status,
        explanation=explanations,
    )
