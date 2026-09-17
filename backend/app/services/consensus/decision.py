"""
Explicit consensus classification decision logic and hierarchy.
Enforces conservative safety rules, conflict resolution, and data quality constraints.
"""
from typing import Dict, List, Optional
from backend.app.schemas.consensus import ConsensusCategory, ConsensusFlag


# Prototype decision thresholds
STRUCTURAL_CONSENSUS_THRESHOLD = 0.50
SEASONAL_CONSENSUS_THRESHOLD = 0.35
ATMOSPHERIC_CONSENSUS_THRESHOLD = 0.35
STABLE_CONSENSUS_THRESHOLD = 0.40
MIN_EPOCHS_FOR_EVALUATION = 5
MIN_EVIDENCE_QUALITY_THRESHOLD = 0.35


def determine_consensus_class(
    physics_category: ConsensusCategory,
    ml_category_masses: Dict[ConsensusCategory, float],
    ml_predicted_category: ConsensusCategory,
    evidence_quality_score: float,
    epoch_count: int,
    flags: Optional[List[str]] = None,
) -> ConsensusCategory:
    """
    Executes explicit consensus decision hierarchy.

    DECISION HIERARCHY:
      1. INSUFFICIENT_EVIDENCE: Epochs < 5 or Physics classified as INSUFFICIENT_EVIDENCE.
         (Absence of data cannot be overridden by ML inference).
      2. LOW_QUALITY: Physics LOW_QUALITY, ML LOW_QUALITY >= 0.50, or quality < 0.35.
         (Inadequate interferometric quality suppresses all structural/environmental claims).
      3. TEMPORALLY_INCONSISTENT: Physics and ML both confirm temporal volatility.
      4. STRUCTURAL CONSENSUS: Requires BOTH ML structural mass >= 0.50 AND Physics STRUCTURAL.
      5. SEASONAL CONSENSUS: Physics SEASONAL and ML seasonal mass >= 0.35.
      6. ATMOSPHERIC CONSENSUS: Physics ATMOSPHERIC and ML atmospheric mass >= 0.35.
      7. STABLE CONSENSUS: Physics STABLE and ML stable mass >= 0.40.
      8. CONFLICT HANDLING:
         - Seasonal vs Structural conflict: Defers conservatively to SEASONAL (never structural).
         - Atmospheric vs Structural conflict: Defers conservatively to ATMOSPHERIC (never structural).
         - Unresolved conflict: Falls back to INSUFFICIENT_EVIDENCE.
    """
    flags = flags or []
    structural_ml_mass = ml_category_masses.get(ConsensusCategory.STRUCTURAL, 0.0)

    # 1. Insufficient data guard
    if (
        physics_category == ConsensusCategory.INSUFFICIENT_EVIDENCE
        or epoch_count < MIN_EPOCHS_FOR_EVALUATION
    ):
        return ConsensusCategory.INSUFFICIENT_EVIDENCE

    # 2. Low interferometric quality guard
    if (
        physics_category == ConsensusCategory.LOW_QUALITY
        or ml_category_masses.get(ConsensusCategory.LOW_QUALITY, 0.0) >= 0.50
        or evidence_quality_score < MIN_EVIDENCE_QUALITY_THRESHOLD
    ):
        return ConsensusCategory.LOW_QUALITY

    # 3. Temporal inconsistency guard
    if (
        physics_category == ConsensusCategory.TEMPORALLY_INCONSISTENT
        and ml_category_masses.get(ConsensusCategory.TEMPORALLY_INCONSISTENT, 0.0) >= 0.30
    ):
        return ConsensusCategory.TEMPORALLY_INCONSISTENT

    # 4. Environmental vs Structural conflict resolution
    if (
        physics_category == ConsensusCategory.SEASONAL
        and structural_ml_mass >= STRUCTURAL_CONSENSUS_THRESHOLD
    ):
        # Physics identified physical seasonal cycle; ML sees monotonic/accelerating trend.
        # DO NOT declare structural deformation! Defend environmental baseline.
        return ConsensusCategory.SEASONAL

    # 5. Atmospheric vs Structural conflict resolution
    if (
        physics_category == ConsensusCategory.ATMOSPHERIC
        and structural_ml_mass >= STRUCTURAL_CONSENSUS_THRESHOLD
    ):
        # Physics identified transient atmospheric spike; ML interpreted as step deformation.
        # DO NOT declare structural deformation! Defend atmospheric baseline.
        return ConsensusCategory.ATMOSPHERIC

    # 6. Structural Consensus (Bipartite Agreement Required)
    if (
        physics_category == ConsensusCategory.STRUCTURAL
        and structural_ml_mass >= STRUCTURAL_CONSENSUS_THRESHOLD
    ):
        return ConsensusCategory.STRUCTURAL

    # 7. Seasonal Consensus
    if (
        physics_category == ConsensusCategory.SEASONAL
        and ml_category_masses.get(ConsensusCategory.SEASONAL, 0.0) >= SEASONAL_CONSENSUS_THRESHOLD
    ):
        return ConsensusCategory.SEASONAL

    # 8. Atmospheric Consensus
    if (
        physics_category == ConsensusCategory.ATMOSPHERIC
        and ml_category_masses.get(ConsensusCategory.ATMOSPHERIC, 0.0) >= ATMOSPHERIC_CONSENSUS_THRESHOLD
    ):
        return ConsensusCategory.ATMOSPHERIC

    # 9. Stable Consensus
    if (
        physics_category == ConsensusCategory.STABLE
        and ml_category_masses.get(ConsensusCategory.STABLE, 0.0) >= STABLE_CONSENSUS_THRESHOLD
    ):
        return ConsensusCategory.STABLE

    # 10. Secondary match with physics category if moderate ML support exists
    if ml_category_masses.get(physics_category, 0.0) >= 0.30:
        return physics_category

    # 11. If Physics indicates stable but ML predicts structural without agreement
    if (
        physics_category == ConsensusCategory.STABLE
        and structural_ml_mass >= STRUCTURAL_CONSENSUS_THRESHOLD
    ):
        # Disagreement between stable physics and ML structural
        return ConsensusCategory.INSUFFICIENT_EVIDENCE

    # 12. Conservative Fallback for Unresolved Disagreements
    return ConsensusCategory.INSUFFICIENT_EVIDENCE
