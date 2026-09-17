"""
Multi-epoch evidence persistence evaluation and environmental recurrence safeguards.
Quantifies evidence continuity without treating persistence as proof of structural failure.
"""
from typing import List, Tuple
from backend.app.schemas.consensus import ConsensusAssessment, ConsensusCategory


def calculate_structural_persistence_score(
    consensus_history: List[ConsensusAssessment],
    missing_epoch_count: int = 0,
) -> float:
    """
    Calculates the bounded structural evidence persistence score in [0.0, 1.0].

    CRITICAL SCIENTIFIC PRINCIPLES:
      1. Persistence is evidence accumulation, NOT proof of structural failure or damage.
      2. Environmental & Seasonal Recurrence Guard:
         Recurring seasonal patterns (e.g. SEASONAL consensus or periodic physics cycles)
         must NOT accumulate into structural evidence. If seasonal signals recur,
         structural persistence is suppressed.
      3. Atmospheric Transients Guard:
         Isolated or recurring atmospheric transients do NOT indicate progressive deformation.
      4. Penalized by large gaps of missing observational epochs.

    PROTOTYPE ASSUMPTIONS (Coefficients are transparent baseline assumptions):
      - Structural fraction weight: 0.45
      - Mean agreement weight: 0.25
      - Mean confidence weight: 0.20
      - Quality weight: 0.10
    """
    if not consensus_history:
        return 0.0

    total_epochs = len(consensus_history)
    if total_epochs < 3:
        # Insufficient baseline for longitudinal persistence
        return 0.0

    structural_count = 0
    seasonal_count = 0
    atmospheric_count = 0
    total_agreement = 0.0
    total_confidence = 0.0
    total_quality = 0.0

    for assessment in consensus_history:
        cat = assessment.consensus_class
        if cat == ConsensusCategory.STRUCTURAL:
            structural_count += 1
        elif cat == ConsensusCategory.SEASONAL:
            seasonal_count += 1
        elif cat == ConsensusCategory.ATMOSPHERIC:
            atmospheric_count += 1

        total_agreement += assessment.agreement_score
        total_confidence += assessment.consensus_confidence
        total_quality += assessment.evidence_quality_score

    f_struct = structural_count / total_epochs
    f_seasonal = seasonal_count / total_epochs
    f_atmo = atmospheric_count / total_epochs

    # ENVIRONMENTAL RECURRENCE SAFEGUARD:
    # If seasonal environmental fluctuations are dominant, structural persistence is actively suppressed.
    if f_seasonal >= 0.40 or (f_seasonal > f_struct and seasonal_count >= 2):
        return 0.0

    # ATMOSPHERIC TRANSIENT SAFEGUARD:
    if f_atmo >= 0.50:
        return 0.0

    mean_agree = total_agreement / total_epochs
    mean_conf = total_confidence / total_epochs
    mean_qual = total_quality / total_epochs

    # Base linear persistence combination
    raw_persistence = (
        0.45 * f_struct
        + 0.25 * mean_agree
        + 0.20 * mean_conf
        + 0.10 * mean_qual
    )

    # Missing epochs continuity penalty: gaps in temporal coverage weaken continuous persistence claims
    if missing_epoch_count > 0:
        gap_penalty = min(0.50, 0.08 * missing_epoch_count)
        raw_persistence *= (1.0 - gap_penalty)

    # If structural evidence was never detected, persistence is zero
    if structural_count == 0:
        raw_persistence = 0.0

    return round(float(max(0.0, min(1.0, raw_persistence))), 4)
