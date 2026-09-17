"""
Semantic mapping layer between ML taxonomy, Physics consistency taxonomy,
and the unified STRATA Consensus vocabulary.
"""
from typing import Dict, Union
from backend.app.schemas.consensus import ConsensusCategory
from backend.app.schemas.physics import PhysicsClassification
from backend.app.schemas.synthetic import GroundTruthClass


ML_TO_CONSENSUS_MAP: Dict[GroundTruthClass, ConsensusCategory] = {
    GroundTruthClass.STABLE: ConsensusCategory.STABLE,
    GroundTruthClass.STRUCTURAL_MONOTONIC: ConsensusCategory.STRUCTURAL,
    GroundTruthClass.STRUCTURAL_ACCELERATING: ConsensusCategory.STRUCTURAL,
    GroundTruthClass.SEASONAL_ENVIRONMENTAL: ConsensusCategory.SEASONAL,
    GroundTruthClass.ATMOSPHERIC_TRANSIENT: ConsensusCategory.ATMOSPHERIC,
    GroundTruthClass.LOW_QUALITY: ConsensusCategory.LOW_QUALITY,
    GroundTruthClass.TEMPORALLY_INCONSISTENT: ConsensusCategory.TEMPORALLY_INCONSISTENT,
}

PHYSICS_TO_CONSENSUS_MAP: Dict[PhysicsClassification, ConsensusCategory] = {
    PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION: ConsensusCategory.STABLE,
    PhysicsClassification.STRUCTURALLY_CONSISTENT: ConsensusCategory.STRUCTURAL,
    PhysicsClassification.SEASONALLY_SUSPECT: ConsensusCategory.SEASONAL,
    PhysicsClassification.ATMOSPHERICALLY_SUSPECT: ConsensusCategory.ATMOSPHERIC,
    PhysicsClassification.LOW_QUALITY: ConsensusCategory.LOW_QUALITY,
    PhysicsClassification.TEMPORALLY_INCONSISTENT: ConsensusCategory.TEMPORALLY_INCONSISTENT,
    PhysicsClassification.INSUFFICIENT_EVIDENCE: ConsensusCategory.INSUFFICIENT_EVIDENCE,
}


def map_ml_class_to_consensus(ml_class: Union[GroundTruthClass, str]) -> ConsensusCategory:
    """
    Maps an individual ML ground-truth class to its consensus semantic category.
    """
    if isinstance(ml_class, str):
        ml_class = GroundTruthClass(ml_class)
    return ML_TO_CONSENSUS_MAP[ml_class]


def map_physics_class_to_consensus(
    physics_class: Union[PhysicsClassification, str]
) -> ConsensusCategory:
    """
    Maps an individual Physics consistency classification to its consensus semantic category.
    Explicitly preserves INSUFFICIENT_EVIDENCE without converting it to stable or structural.
    """
    if isinstance(physics_class, str):
        physics_class = PhysicsClassification(physics_class)
    return PHYSICS_TO_CONSENSUS_MAP[physics_class]


def aggregate_ml_category_probabilities(
    ml_probabilities: Dict[str, float]
) -> Dict[ConsensusCategory, float]:
    """
    Aggregates ML fine-grained class probabilities into unified consensus category masses.
    Example: P_ml(STRUCTURAL) = P(STRUCTURAL_MONOTONIC) + P(STRUCTURAL_ACCELERATING).

    Returns a normalized dictionary mapping ConsensusCategory to float in [0.0, 1.0].
    """
    category_masses: Dict[ConsensusCategory, float] = {cat: 0.0 for cat in ConsensusCategory}

    for class_str, prob in ml_probabilities.items():
        try:
            gt_class = GroundTruthClass(class_str)
            consensus_cat = ML_TO_CONSENSUS_MAP[gt_class]
            category_masses[consensus_cat] += float(prob)
        except (ValueError, KeyError):
            # Unknown class string in ML distribution is omitted from known mass
            continue

    # Round aggregated probabilities
    rounded_masses = {cat: round(mass, 4) for cat, mass in category_masses.items()}
    return rounded_masses
