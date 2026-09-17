"""
Explicit 9-step decision hierarchy for STRATA Phase 7 Risk Characterization.
Translates multi-epoch InSAR consensus evidence and infrastructure profile context
into interpretable analytical attention states.

STRICT SCIENTIFIC PRINCIPLES:
- Downstream contextual metadata (criticality / critical zone) NEVER overrides upstream quality suppression.
- Low quality + high criticality remains INSUFFICIENT_EVIDENCE.
- Environmental patterns remain suppressed as ENVIRONMENTAL_PATTERN.
- Characterization states are attention/inspection categories, NOT failure predictions.
"""
from typing import List, Optional, Tuple

from backend.app.db.models import CriticalityLevel, RiskCharacterizationState
from backend.app.schemas.risk import (
    CalibrationProfile,
    CriticalZone,
    EvidenceComponents,
    ExpectedDeformationBehavior,
    HistoricalBaseline,
)
from backend.app.schemas.temporal import TemporalEvidenceSummary, TemporalStatus


def evaluate_decision_hierarchy(
    temporal_summary: TemporalEvidenceSummary,
    evidence: EvidenceComponents,
    calibration_profile: CalibrationProfile,
    criticality: CriticalityLevel = CriticalityLevel.UNKNOWN,
    critical_zones: Optional[List[CriticalZone]] = None,
    historical_baseline: Optional[HistoricalBaseline] = None,
    expected_behavior: Optional[List[ExpectedDeformationBehavior]] = None,
) -> Tuple[RiskCharacterizationState, float, Optional[float], List[str], List[str], List[str]]:
    """
    Executes the 9-step decision hierarchy in order.
    
    Returns:
      (characterization_state, confidence, prototype_risk_index, supporting_factors, suppressing_factors, uncertainty_factors)
    """
    supporting_factors: List[str] = []
    suppressing_factors: List[str] = []
    uncertainty_factors: List[str] = []

    # -------------------------------------------------------------------------
    # STEP 1: Quality / Data Sufficiency Guard
    # Downstream contextual weighting CANNOT override upstream quality suppression.
    # -------------------------------------------------------------------------
    if temporal_summary.temporal_status == TemporalStatus.LOW_QUALITY:
        suppressing_factors.append("Interferometric coherence degradation suppresses structural characterization.")
        uncertainty_factors.append("Low radar phase coherence across observation baseline.")
        conf = float(min(0.35, round(evidence.measurement_quality, 4)))
        return (
            RiskCharacterizationState.INSUFFICIENT_EVIDENCE,
            conf,
            round(10.0 * evidence.measurement_quality, 1),
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    if temporal_summary.observation_count < 3 or temporal_summary.temporal_status == TemporalStatus.INSUFFICIENT_HISTORY:
        uncertainty_factors.append("Temporal baseline has fewer than 3 observation epochs.")
        return (
            RiskCharacterizationState.INSUFFICIENT_EVIDENCE,
            0.15,
            5.0,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    if evidence.measurement_quality < 0.35:
        suppressing_factors.append("Severe measurement quality degradation restricts reliable inference.")
        uncertainty_factors.append("Measurement quality score is below prototype reliability threshold (0.35).")
        return (
            RiskCharacterizationState.INSUFFICIENT_EVIDENCE,
            round(evidence.measurement_quality, 4),
            12.0,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # STEP 2: Strong Environmental / Atmospheric Suppression
    # Recurring seasonal oscillations or atmospheric phase delays must remain non-structural.
    # -------------------------------------------------------------------------
    if temporal_summary.temporal_status != TemporalStatus.CONFLICTED and (
        temporal_summary.temporal_status == TemporalStatus.ENVIRONMENTAL_PATTERN
        or evidence.environmental_suppression >= 0.80
        or (expected_behavior and ExpectedDeformationBehavior.SEASONAL in expected_behavior and temporal_summary.environmental_pattern_count >= 1)
    ):
        suppressing_factors.append(
            "Cyclical seasonal recurrence confirmed across multi-epoch baseline; temporal persistence is suppressed."
        )
        if expected_behavior and ExpectedDeformationBehavior.SEASONAL in expected_behavior:
            suppressing_factors.append("Infrastructure profile specifies expected seasonal deformation behavior.")
        
        conf = float(round(max(0.40, evidence.consensus_support), 4))
        # Bounded prototype index for environmental fluctuation
        proto_index = float(round(15.0 + 10.0 * evidence.trend_significance, 1))
        return (
            RiskCharacterizationState.ENVIRONMENTAL_PATTERN,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # STEP 3: Established Baseline Behavior
    # Sequence remains within the nominal baseline stability envelope.
    # -------------------------------------------------------------------------
    if temporal_summary.temporal_status == TemporalStatus.BASELINE:
        supporting_factors.append("Observed deformation remains within the nominal baseline stability envelope.")
        if evidence.acceleration_support == 0.0 and temporal_summary.apparent_acceleration_mm_per_year2 is not None:
            suppressing_factors.append(
                "Apparent acceleration is mathematically detectable but sequence remains within nominal baseline stability."
            )
        conf = float(round(max(0.20, evidence.measurement_quality), 4))
        proto_index = float(round(5.0 + 5.0 * evidence.trend_significance, 1))
        return (
            RiskCharacterizationState.BASELINE,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # STEP 4: Material Model Conflict / Disagreement
    # Analytical models disagree or temporal volatility exists.
    # -------------------------------------------------------------------------
    if temporal_summary.temporal_status == TemporalStatus.CONFLICTED or evidence.consensus_support < 0.35:
        uncertainty_factors.append("Cross-model disagreement between ML and physical consistency models.")
        uncertainty_factors.append("Temporal status indicates active conflict or volatility across epochs.")
        suppressing_factors.append("Model disagreement reduces analytical confidence in current interpretation.")
        conf = float(round(min(0.35, evidence.consensus_support), 4))
        proto_index = float(round(25.0 + 10.0 * evidence.trend_significance, 1))
        return (
            RiskCharacterizationState.MONITOR,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # STEP 5: Insufficient Temporal Persistence
    # Initial or single-epoch structural indications cannot escalate to attention.
    # -------------------------------------------------------------------------
    if temporal_summary.structural_candidate_count < 2 or evidence.temporal_persistence < 0.20:
        uncertainty_factors.append("Deformation persistence score (< 0.20) is insufficient to establish a structural pattern.")
        if temporal_summary.structural_candidate_count == 1:
            supporting_factors.append("Single isolated structural observation detected; ongoing monitoring required.")
        conf = float(round(evidence.consensus_support * 0.8, 4))
        proto_index = float(round(20.0 + 15.0 * evidence.trend_significance, 1))
        return (
            RiskCharacterizationState.MONITOR,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    # -------------------------------------------------------------------------
    # STEP 6: Persistent Non-Baseline Evidence
    # -------------------------------------------------------------------------
    supporting_factors.append(
        f"Multi-epoch structural persistence confirmed (persistence score: {evidence.temporal_persistence:.2f})."
    )
    if evidence.trend_significance > 0.30:
        supporting_factors.append(
            f"Observed linear trend rate ({temporal_summary.trend_rate_mm_per_year:.2f} mm/year) is significant."
        )

    # -------------------------------------------------------------------------
    # STEP 7: Cross-Model Support & Historical Baseline Deviation
    # -------------------------------------------------------------------------
    if evidence.consensus_support >= 0.50:
        supporting_factors.append(
            f"Strong cross-model consensus agreement (score: {evidence.consensus_support:.2f})."
        )
    else:
        uncertainty_factors.append("Moderate cross-model consensus agreement.")

    if evidence.baseline_deviation_mm is not None:
        supporting_factors.append(
            f"Deformation deviates by {evidence.baseline_deviation_mm:+.2f} mm from historical baseline."
        )
        if evidence.baseline_z_score is not None and abs(evidence.baseline_z_score) >= 2.5:
            supporting_factors.append(
                f"Standardized baseline deviation (|z| = {abs(evidence.baseline_z_score):.1f}) is statistically significant."
            )
    else:
        uncertainty_factors.append("No historical baseline available for asset-specific deviation benchmarking.")

    # Check supported acceleration (Phase 6.2 requirement)
    if evidence.acceleration_support > 0.0:
        supporting_factors.append(
            f"Apparent acceleration ({temporal_summary.apparent_acceleration_mm_per_year2:.2f} mm/year²) "
            f"satisfies scientific temporal support criteria."
        )
    elif temporal_summary.apparent_acceleration_mm_per_year2 is not None:
        suppressing_factors.append(
            "Apparent acceleration lacks sufficient temporal support and is excluded from structural escalation."
        )

    # -------------------------------------------------------------------------
    # STEP 8: Critical Zone & Criticality Contextual Modulation
    # -------------------------------------------------------------------------
    has_critical_zone_overlap = evidence.critical_zone_context > 1.10
    if has_critical_zone_overlap:
        supporting_factors.append(
            f"Observed deformation context overlaps configured critical zones (weight modifier: {evidence.critical_zone_context:.2f}x)."
        )

    is_high_criticality = criticality in (CriticalityLevel.HIGH, CriticalityLevel.CRITICAL)
    if is_high_criticality:
        supporting_factors.append(
            f"Infrastructure criticality is designated as {criticality.value}; contextual inspection priority elevated."
        )

    # -------------------------------------------------------------------------
    # STEP 9: Characterization State Synthesis & Decomposed Prototype Index
    # -------------------------------------------------------------------------
    # Base prototype index calculation from normalized components:
    # 0.35 * persistence + 0.25 * trend_sig + 0.20 * consensus + 0.10 * accel + 0.10 * quality
    raw_score = (
        calibration_profile.persistence_weight * evidence.temporal_persistence
        + 0.25 * evidence.trend_significance
        + calibration_profile.consensus_weight * evidence.consensus_support
        + calibration_profile.acceleration_weight * evidence.acceleration_support
        + calibration_profile.quality_weight * evidence.measurement_quality
    )
    # Context multiplier
    context_mult = 1.0
    if has_critical_zone_overlap:
        context_mult += 0.15
    if is_high_criticality:
        context_mult += 0.10 if criticality == CriticalityLevel.HIGH else 0.20

    proto_index = float(round(min(100.0, raw_score * 100.0 * context_mult), 1))
    conf = float(round(min(1.0, 0.5 * evidence.consensus_support + 0.3 * evidence.temporal_persistence + 0.2 * evidence.measurement_quality), 4))

    # Attention State Assignment
    if (
        evidence.temporal_persistence >= 0.55
        and evidence.consensus_support >= 0.55
        and (has_critical_zone_overlap or is_high_criticality or evidence.acceleration_support > 0.25 or (evidence.baseline_z_score and abs(evidence.baseline_z_score) >= 3.0))
    ):
        return (
            RiskCharacterizationState.HIGH_ATTENTION,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    if evidence.temporal_persistence >= 0.35 and evidence.consensus_support >= 0.45:
        return (
            RiskCharacterizationState.ELEVATED_ATTENTION,
            conf,
            proto_index,
            supporting_factors,
            suppressing_factors,
            uncertainty_factors,
        )

    return (
        RiskCharacterizationState.MONITOR,
        conf,
        proto_index,
        supporting_factors,
        suppressing_factors,
        uncertainty_factors,
    )
