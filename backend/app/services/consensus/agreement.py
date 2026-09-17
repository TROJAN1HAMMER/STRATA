"""
Cross-model agreement and disagreement evaluation.
Calculates continuous category agreement from ML probability mass,
computes bounded disagreement penalties, and identifies diagnostic conflict flags.
"""
from typing import Dict, List
from backend.app.schemas.consensus import ConsensusCategory, ConsensusFlag


# Prototype thresholds (Documented as transparent engineering assumptions)
DISAGREEMENT_THRESHOLD_MODERATE = 0.30
DISAGREEMENT_THRESHOLD_STRONG = 0.15
AGREEMENT_THRESHOLD_MODERATE = 0.60
AGREEMENT_THRESHOLD_STRONG = 0.80
CONFLICT_STRUCTURAL_MASS_THRESHOLD = 0.40


def calculate_agreement_score(
    ml_category_masses: Dict[ConsensusCategory, float],
    physics_category: ConsensusCategory,
) -> float:
    """
    Calculates continuous cross-model agreement score in [0.0, 1.0].
    Defined as the total ML probability mass assigned to the semantic category
    identified by the deterministic physics engine.

    If Physics indicates INSUFFICIENT_EVIDENCE, returns 0.0 (no category agreement).
    """
    if physics_category == ConsensusCategory.INSUFFICIENT_EVIDENCE:
        return 0.0

    mass = ml_category_masses.get(physics_category, 0.0)
    return round(float(max(0.0, min(1.0, mass))), 4)


def calculate_disagreement_penalty(agreement_score: float) -> float:
    """
    Calculates the bounded disagreement penalty: penalty = 1.0 - agreement_score.
    Yields:
      - agreement 1.00 -> penalty 0.00
      - agreement 0.75 -> penalty 0.25
      - agreement 0.20 -> penalty 0.80
      - agreement 0.00 -> penalty 1.00

    PROTOTYPE FORMULATION: Transparent linear relationship. Not claimed to be theoretically optimal.
    """
    penalty = 1.0 - agreement_score
    return round(float(max(0.0, min(1.0, penalty))), 4)


def evaluate_agreement_flags(
    ml_category_masses: Dict[ConsensusCategory, float],
    physics_category: ConsensusCategory,
    agreement_score: float,
) -> List[str]:
    """
    Evaluates cross-model diagnostic flags indicating agreement, conflict, or quality alerts.
    """
    flags: List[str] = []

    # 1. Base agreement / disagreement levels
    if physics_category == ConsensusCategory.INSUFFICIENT_EVIDENCE:
        flags.append(ConsensusFlag.INSUFFICIENT_EVIDENCE_SUPPRESSION.value)
    else:
        if agreement_score < DISAGREEMENT_THRESHOLD_STRONG:
            flags.append(ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value)
            flags.append(ConsensusFlag.MODEL_DISAGREEMENT.value)
        elif agreement_score < DISAGREEMENT_THRESHOLD_MODERATE:
            flags.append(ConsensusFlag.MODEL_DISAGREEMENT.value)
        elif agreement_score >= AGREEMENT_THRESHOLD_STRONG:
            flags.append(ConsensusFlag.STRONG_MODEL_AGREEMENT.value)
            flags.append(ConsensusFlag.MODEL_AGREEMENT.value)
        elif agreement_score >= AGREEMENT_THRESHOLD_MODERATE:
            flags.append(ConsensusFlag.MODEL_AGREEMENT.value)

    # 2. Specific conflict detection
    structural_ml_mass = ml_category_masses.get(ConsensusCategory.STRUCTURAL, 0.0)

    if (
        physics_category == ConsensusCategory.SEASONAL
        and structural_ml_mass >= CONFLICT_STRUCTURAL_MASS_THRESHOLD
    ):
        flags.append(ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value)
        if ConsensusFlag.MODEL_DISAGREEMENT.value not in flags:
            flags.append(ConsensusFlag.MODEL_DISAGREEMENT.value)

    if (
        physics_category == ConsensusCategory.ATMOSPHERIC
        and structural_ml_mass >= CONFLICT_STRUCTURAL_MASS_THRESHOLD
    ):
        flags.append(ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value)
        if ConsensusFlag.MODEL_DISAGREEMENT.value not in flags:
            flags.append(ConsensusFlag.MODEL_DISAGREEMENT.value)

    # 3. Quality & data sufficiency flags
    low_quality_ml_mass = ml_category_masses.get(ConsensusCategory.LOW_QUALITY, 0.0)
    if (
        physics_category == ConsensusCategory.LOW_QUALITY
        or low_quality_ml_mass >= 0.50
    ):
        flags.append(ConsensusFlag.LOW_QUALITY_EVIDENCE.value)

    temp_inconsistent_ml_mass = ml_category_masses.get(ConsensusCategory.TEMPORALLY_INCONSISTENT, 0.0)
    if (
        physics_category == ConsensusCategory.TEMPORALLY_INCONSISTENT
        or temp_inconsistent_ml_mass >= 0.50
    ):
        flags.append(ConsensusFlag.TEMPORAL_INCONSISTENCY_FLAG.value)

    # Return unique sorted flags for determinism
    return sorted(list(set(flags)))
