"""
Transparent scientific explanation generator for STRATA Cross-Model Consensus.
Produces traceable justifications without ungrounded structural safety or collapse claims.
"""
from typing import Dict, List
from backend.app.schemas.consensus import ConsensusCategory, ConsensusFlag


def generate_consensus_explanation(
    consensus_class: ConsensusCategory,
    consensus_confidence: float,
    agreement_score: float,
    disagreement_penalty: float,
    evidence_quality_score: float,
    temporal_persistence_score: float,
    physics_category: ConsensusCategory,
    ml_category_masses: Dict[ConsensusCategory, float],
    flags: List[str],
) -> str:
    """
    Constructs a comprehensive, deterministic scientific explanation for the consensus result.

    BOUNDARY CONSTRAINT:
      Does NOT make unverified engineering determinations (e.g. 'structure is safe/unsafe',
      'collapse predicted'). Explains agreement/disagreement between the analytical models.
    """
    parts: List[str] = []

    # 1. Opening statement on models and agreement
    phys_str = physics_category.value
    ml_mass_phys = ml_category_masses.get(physics_category, 0.0) * 100.0

    if ConsensusFlag.STRONG_MODEL_AGREEMENT.value in flags:
        parts.append(
            f"Strong cross-model agreement observed. The deterministic physics engine classified the sequence as "
            f"'{phys_str}', which is strongly supported by the ML classifier allocating {ml_mass_phys:.1f}% "
            f"probability mass to this category (agreement score: {agreement_score:.2f})."
        )
    elif ConsensusFlag.MODEL_AGREEMENT.value in flags:
        parts.append(
            f"Cross-model agreement established. The deterministic physics engine classified the sequence as "
            f"'{phys_str}', with the ML classifier allocating {ml_mass_phys:.1f}% probability mass to this category "
            f"(agreement score: {agreement_score:.2f})."
        )
    elif ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value in flags:
        parts.append(
            f"Significant cross-model disagreement detected. The deterministic physics engine evaluated the sequence as "
            f"'{phys_str}', whereas the ML classifier assigned only {ml_mass_phys:.1f}% probability mass to this category "
            f"(disagreement penalty: {disagreement_penalty:.2f})."
        )
    elif ConsensusFlag.MODEL_DISAGREEMENT.value in flags:
        parts.append(
            f"Cross-model discrepancy identified. The deterministic physics engine classified the sequence as "
            f"'{phys_str}', while the ML model assigned {ml_mass_phys:.1f}% probability mass to this category."
        )
    elif physics_category == ConsensusCategory.INSUFFICIENT_EVIDENCE:
        parts.append(
            "Evaluation halted due to insufficient observational data. The physics engine marked the sequence as "
            "INSUFFICIENT_EVIDENCE; machine learning inference cannot substitute for an inadequate temporal baseline."
        )
    else:
        parts.append(
            f"Consensus evaluated between physics classification '{phys_str}' and ML probability distribution."
        )

    # 2. Specific conflict details
    if ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in flags:
        struct_mass = ml_category_masses.get(ConsensusCategory.STRUCTURAL, 0.0) * 100.0
        parts.append(
            f"Environmental conflict noted: ML assigned {struct_mass:.1f}% mass to progressive structural deformation, "
            f"but deterministic physical analysis identified cyclic zero-crossings indicative of seasonal environmental "
            f"fluctuation. Structural consensus was suppressed to prevent false alarms."
        )
    elif ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value in flags:
        struct_mass = ml_category_masses.get(ConsensusCategory.STRUCTURAL, 0.0) * 100.0
        parts.append(
            f"Atmospheric conflict noted: ML assigned {struct_mass:.1f}% mass to progressive structural deformation, "
            f"but physical analysis detected an isolated transient phase spike consistent with atmospheric artifact noise. "
            f"Structural consensus was suppressed to avoid misinterpreting localized atmospheric delays."
        )

    # 3. Evidence quality & temporal persistence context
    quality_pct = evidence_quality_score * 100.0
    persist_pct = temporal_persistence_score * 100.0
    parts.append(
        f"Observational evidence quality was evaluated at {quality_pct:.1f}% (interferometric coherence and geometric "
        f"stability). Multi-epoch temporal persistence was evaluated at {persist_pct:.1f}%."
    )

    # 4. Resulting consensus outcome and confidence
    conf_pct = consensus_confidence * 100.0
    parts.append(
        f"Consensus classification assigned as '{consensus_class.value}' with analytical confidence of {conf_pct:.1f}%."
    )

    # 5. Low quality / Insufficient data warning
    if ConsensusFlag.LOW_QUALITY_EVIDENCE.value in flags or consensus_class == ConsensusCategory.LOW_QUALITY:
        parts.append(
            "Caution: Interferometric measurement quality is degraded. Confidence ceiling has been restricted."
        )
    elif consensus_class == ConsensusCategory.INSUFFICIENT_EVIDENCE:
        parts.append(
            "Caution: Additional satellite observation epochs are required before a reliable classification can be determined."
        )

    return " ".join(parts)
