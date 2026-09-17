"""
Temporal persistence evaluation for STRATA Consensus.
Evaluates multi-epoch kinematic stability and persistence without confusing
persistence with structural failure.
"""
from typing import Any, Dict, Union
from backend.app.schemas.physics import PhysicsAssessmentRead, PhysicsEvidence
from backend.app.services.consensus.evidence import _extract_evidence_payload


def calculate_temporal_persistence_score(
    physics_evidence: Union[PhysicsEvidence, PhysicsAssessmentRead, Dict[str, Any]]
) -> float:
    """
    Computes bounded temporal_persistence_score in [0.0, 1.0].
    Measures the degree to which an observed deformation process is persistent and continuous
    over multiple observation epochs.

    CRITICAL SCIENTIFIC PRINCIPLE:
      - Temporal persistence does NOT automatically imply progressive structural deformation.
      - Periodic seasonal cycles and steady environmental fluctuations can be highly persistent.
      - This score serves strictly as an evidence-strength modifier across multi-epoch data,
        NOT as an independent classifier of structural failure.

    PROTOTYPE FORMULATION:
      persistence_score = (0.45 * persistence + 0.35 * directional_consistency + 0.20 * rate_consistency)
                          * (1.0 - 0.50 * abrupt_inconsistency_score)
    """
    payload = _extract_evidence_payload(physics_evidence)
    temporal_dict = payload.get("temporal_evidence", {})

    persistence = temporal_dict.get("persistence")
    p_val = float(persistence) if persistence is not None else 0.5

    dir_consistency = temporal_dict.get("directional_consistency")
    dir_val = float(dir_consistency) if dir_consistency is not None else 0.5

    rate_consistency = temporal_dict.get("rate_consistency")
    rate_val = float(rate_consistency) if rate_consistency is not None else 0.5

    abrupt_inconsistency = float(temporal_dict.get("abrupt_inconsistency_score", 0.0))

    base_score = 0.45 * p_val + 0.35 * dir_val + 0.20 * rate_val
    penalty_factor = max(0.0, 1.0 - 0.50 * abrupt_inconsistency)

    final_score = base_score * penalty_factor
    return round(float(max(0.0, min(1.0, final_score))), 4)
