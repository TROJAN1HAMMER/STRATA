"""
Evidence quality and physics evidence strength evaluation for STRATA Consensus.
Evaluates observation quality from observable InSAR metrics without ground-truth leakage.
"""
from typing import Any, Dict, Union
from backend.app.schemas.physics import GeometryStatus, PhysicsAssessmentRead, PhysicsEvidence


def _extract_evidence_payload(
    physics_evidence: Union[PhysicsEvidence, PhysicsAssessmentRead, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Helper to extract dictionary payload from PhysicsEvidence, PhysicsAssessmentRead, or dict.
    """
    if isinstance(physics_evidence, PhysicsEvidence):
        return physics_evidence.model_dump()
    elif isinstance(physics_evidence, PhysicsAssessmentRead):
        return physics_evidence.evidence_payload
    elif isinstance(physics_evidence, dict):
        if "evidence_payload" in physics_evidence and isinstance(physics_evidence["evidence_payload"], dict):
            return physics_evidence["evidence_payload"]
        return physics_evidence
    raise TypeError(f"Unsupported physics evidence type: {type(physics_evidence)}")


def calculate_evidence_quality_score(
    physics_evidence: Union[PhysicsEvidence, PhysicsAssessmentRead, Dict[str, Any]]
) -> float:
    """
    Computes bounded evidence_quality_score in [0.0, 1.0].
    Represents confidence in the AVAILABLE OBSERVATIONAL EVIDENCE (coherence, phase, sufficiency, geometry).

    CRITICAL SCIENTIFIC DISTINCTION:
      - This score represents the quality and reliability of the measurement data.
      - It does NOT represent the probability that the physical asset is safe or unsafe.

    PROTOTYPE FORMULATION:
      evidence_quality = 0.50 * Q_measurement + 0.30 * Q_sufficiency + 0.20 * Q_geometry
      penalized if high atmospheric artifact noise is detected.
    """
    payload = _extract_evidence_payload(physics_evidence)

    # 1. Measurement Quality (coherence, phase quality)
    meas_dict = payload.get("measurement_quality", {})
    q_meas = float(meas_dict.get("quality_score", 0.5))

    # 2. Temporal Data Sufficiency
    temporal_dict = payload.get("temporal_evidence", {})
    q_suff = float(temporal_dict.get("data_sufficiency", 0.5))

    # 3. Geometry Status
    geom_dict = payload.get("geometry_evidence", {})
    geom_status = geom_dict.get("status", GeometryStatus.VALID_GEOMETRY.value)
    if isinstance(geom_status, GeometryStatus):
        geom_status = geom_status.value

    if geom_status == GeometryStatus.VALID_GEOMETRY.value:
        q_geom = 1.0
    elif geom_status == GeometryStatus.WEAK_GEOMETRY.value:
        q_geom = 0.7
    else:
        q_geom = 0.3

    # Base linear combination
    raw_quality = 0.50 * q_meas + 0.30 * q_suff + 0.20 * q_geom

    # Atmospheric noise adjustment: high atmospheric suspicion attenuates clean deformation quality
    atmo_dict = payload.get("atmospheric_evidence", {})
    atmo_score = float(atmo_dict.get("atmospheric_suspect_score", 0.0))
    if atmo_score > 0.60:
        raw_quality *= 0.85

    return round(float(max(0.0, min(1.0, raw_quality))), 4)


def calculate_physics_evidence_strength(
    physics_evidence: Union[PhysicsEvidence, PhysicsAssessmentRead, Dict[str, Any]]
) -> float:
    """
    Calculates physics_evidence_strength in [0.0, 1.0].

    IMPORTANT DISTINCTION:
      The Physics Engine evaluates deterministic kinematic consistency.
      This value represents the strength of empirical consistency evidence,
      and is NOT a calibrated statistical probability.
    """
    payload = _extract_evidence_payload(physics_evidence)

    # Check if overall_confidence is explicitly provided
    overall_conf = payload.get("overall_confidence")
    if overall_conf is not None and isinstance(overall_conf, (int, float)):
        return round(float(max(0.0, min(1.0, overall_conf))), 4)

    # Derive evidence strength from measurement quality and temporal persistence
    meas_dict = payload.get("measurement_quality", {})
    q_meas = float(meas_dict.get("quality_score", 0.5))

    temporal_dict = payload.get("temporal_evidence", {})
    persistence = float(temporal_dict.get("persistence", 0.5) or 0.5)
    dir_consist = float(temporal_dict.get("directional_consistency", 0.5) or 0.5)

    strength = 0.40 * q_meas + 0.35 * persistence + 0.25 * dir_consist
    return round(float(max(0.0, min(1.0, strength))), 4)
