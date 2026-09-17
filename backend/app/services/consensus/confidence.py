"""
Bounded cross-model confidence fusion formulation.
Calculates final consensus confidence from ML probability confidence,
physics evidence strength, cross-model agreement, and evidence quality modifiers.
"""
from typing import List, Optional
from backend.app.schemas.consensus import ConsensusCategory, ConsensusFlag


# Prototype constants (Documented as transparent baseline assumptions)
ML_CONFIDENCE_WEIGHT = 0.60
PHYSICS_STRENGTH_WEIGHT = 0.40

AGREEMENT_MODIFIER_BASE = 0.50
AGREEMENT_MODIFIER_SLOPE = 0.50

QUALITY_MODIFIER_BASE = 0.40
QUALITY_MODIFIER_SLOPE = 0.60

TEMPORAL_MODIFIER_BASE = 0.70
TEMPORAL_MODIFIER_SLOPE = 0.30

MAX_INSUFFICIENT_CONFIDENCE = 0.25
MAX_LOW_QUALITY_CONFIDENCE = 0.35
MIN_CONFIDENCE_FLOOR = 0.05
MAX_CONFIDENCE_CEILING = 0.99


def calculate_consensus_confidence(
    ml_confidence: float,
    physics_evidence_strength: float,
    agreement_score: float,
    evidence_quality_score: float,
    temporal_persistence_score: float,
    consensus_class: ConsensusCategory,
    flags: Optional[List[str]] = None,
) -> float:
    """
    Computes bounded consensus confidence in [0.05, 0.99].

    MATHEMATICAL PRINCIPLE:
      - AGREEMENT -> increases confidence via agreement_modifier in [0.50, 1.00]
      - DISAGREEMENT -> reduces confidence via agreement_modifier and conflict penalties
      - LOW QUALITY -> suppresses confidence ceiling to <= 0.35
      - INSUFFICIENT EVIDENCE -> suppresses confidence ceiling to <= 0.25
      - Modifiers are strictly bounded to prevent catastrophic collapse to 0.0 for moderate signals.

    PROTOTYPE FORMULATION:
      base_conf = 0.60 * ml_conf + 0.40 * phys_strength
      agreement_mod = 0.50 + 0.50 * agreement_score
      quality_mod = 0.40 + 0.60 * quality_score
      temporal_mod = 0.70 + 0.30 * temporal_persistence_score
      fused = base_conf * agreement_mod * quality_mod * temporal_mod
    """
    flags = flags or []

    # 1. Base confidence combination
    base_conf = (
        ML_CONFIDENCE_WEIGHT * ml_confidence
        + PHYSICS_STRENGTH_WEIGHT * physics_evidence_strength
    )

    # 2. Bounded modifiers
    agreement_mod = AGREEMENT_MODIFIER_BASE + AGREEMENT_MODIFIER_SLOPE * agreement_score
    quality_mod = QUALITY_MODIFIER_BASE + QUALITY_MODIFIER_SLOPE * evidence_quality_score
    temporal_mod = TEMPORAL_MODIFIER_BASE + TEMPORAL_MODIFIER_SLOPE * temporal_persistence_score

    fused = base_conf * agreement_mod * quality_mod * temporal_mod

    # 3. Diagnostic conflict attenuations
    if ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value in flags:
        fused *= 0.70
    elif ConsensusFlag.MODEL_DISAGREEMENT.value in flags:
        fused *= 0.85

    if (
        ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in flags
        or ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value in flags
    ):
        fused *= 0.75

    # 4. Special class suppression caps
    if consensus_class == ConsensusCategory.INSUFFICIENT_EVIDENCE:
        fused = min(fused, MAX_INSUFFICIENT_CONFIDENCE)
    elif consensus_class == ConsensusCategory.LOW_QUALITY:
        fused = min(fused, MAX_LOW_QUALITY_CONFIDENCE)

    # 5. Clamping to valid bounds
    clamped = max(MIN_CONFIDENCE_FLOOR, min(MAX_CONFIDENCE_CEILING, fused))
    return round(float(clamped), 4)
