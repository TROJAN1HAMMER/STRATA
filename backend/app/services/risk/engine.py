"""
Infrastructure-Specific Risk Characterization Engine for STRATA Phase 7.
Coordinates profile context ingestion, evidence normalization, 9-step decision hierarchy,
and structured explanation generation.

CRITICAL SCIENTIFIC PRINCIPLES:
- Characterizations are analytical inspection attention categories, NOT structural failure or collapse forecasts.
- Does not use one universal deformation threshold.
- Downstream criticality or critical zones cannot override upstream data quality suppression.
- Preserves full audit versioning across all analytical components.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.db.models import (
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    RiskCharacterizationState,
    StructureType,
)
from backend.app.schemas.risk import (
    CalibrationProfile,
    CriticalZone,
    EvidenceComponents,
    ExpectedDeformationBehavior,
    HistoricalBaseline,
    RiskCharacterizationRead,
)
from backend.app.schemas.temporal import TemporalEvidenceSummary
from backend.app.services.risk.decision_hierarchy import evaluate_decision_hierarchy
from backend.app.services.risk.explanation import generate_structured_explanation
from backend.app.services.risk.normalization import (
    _verify_risk_leakage,
    calculate_evidence_components,
)
from backend.app.services.temporal import TemporalEvidenceEngine

CHARACTERIZATION_VERSION = "strata_risk_v1_0_0"
DEFAULT_PROFILE_VERSION = "v1.0.0_prototype"


class InfrastructureRiskCharacterizationEngine:
    """
    Evaluates multi-epoch InSAR evidence in the context of an infrastructure asset's
    material, structure type, critical zones, baseline behavior, and criticality.
    """

    def __init__(self, temporal_engine: Optional[TemporalEvidenceEngine] = None):
        self.temporal_engine = temporal_engine or TemporalEvidenceEngine()

    def evaluate_infrastructure(
        self,
        infrastructure: Any,
        observations: List[Any],
        temporal_summary: Optional[TemporalEvidenceSummary] = None,
    ) -> RiskCharacterizationRead:
        """
        Executes end-to-end infrastructure risk characterization.
        """
        # 1. Enforce ground-truth leakage firewall
        if observations:
            _verify_risk_leakage(observations[0], path="observations[0]")
        if isinstance(infrastructure, dict):
            _verify_risk_leakage(infrastructure, path="infrastructure")
        elif hasattr(infrastructure, "__dict__"):
            _verify_risk_leakage(vars(infrastructure), path="infrastructure")

        infra_id = str(getattr(infrastructure, "id", None) or (infrastructure.get("id") if isinstance(infrastructure, dict) else "unknown"))

        struct_type = getattr(infrastructure, "structure_type", None)
        if struct_type is None and isinstance(infrastructure, dict):
            struct_type = infrastructure.get("structure_type")
        if isinstance(struct_type, str):
            try:
                struct_type = StructureType(struct_type)
            except ValueError:
                struct_type = StructureType.OTHER
        if struct_type is None:
            struct_type = StructureType.OTHER

        material = getattr(infrastructure, "material", None)
        if material is None and isinstance(infrastructure, dict):
            material = infrastructure.get("material")
        if isinstance(material, str):
            try:
                material = MaterialType(material)
            except ValueError:
                material = MaterialType.UNKNOWN
        if material is None:
            material = MaterialType.UNKNOWN

        criticality = getattr(infrastructure, "criticality", None)
        if criticality is None and isinstance(infrastructure, dict):
            criticality = infrastructure.get("criticality")
        if isinstance(criticality, str):
            try:
                criticality = CriticalityLevel(criticality)
            except ValueError:
                criticality = CriticalityLevel.UNKNOWN
        if criticality is None:
            criticality = CriticalityLevel.UNKNOWN

        # Critical Zones
        raw_cz = getattr(infrastructure, "critical_zones", None) or (
            infrastructure.get("critical_zones") if isinstance(infrastructure, dict) else None
        )
        critical_zones: List[CriticalZone] = []
        if raw_cz:
            for item in raw_cz:
                if isinstance(item, CriticalZone):
                    critical_zones.append(item)
                elif isinstance(item, dict):
                    critical_zones.append(CriticalZone(**item))

        # Historical Baseline
        raw_hb = getattr(infrastructure, "historical_baseline", None) or (
            infrastructure.get("historical_baseline") if isinstance(infrastructure, dict) else None
        )
        historical_baseline: Optional[HistoricalBaseline] = None
        if raw_hb:
            if isinstance(raw_hb, HistoricalBaseline):
                historical_baseline = raw_hb
            elif isinstance(raw_hb, dict):
                historical_baseline = HistoricalBaseline(**raw_hb)

        # Expected Behavior
        raw_eb = getattr(infrastructure, "expected_behavior", None) or (
            infrastructure.get("expected_behavior") if isinstance(infrastructure, dict) else None
        )
        expected_behavior: List[ExpectedDeformationBehavior] = []
        if raw_eb:
            for b in raw_eb:
                if isinstance(b, ExpectedDeformationBehavior):
                    expected_behavior.append(b)
                elif isinstance(b, str):
                    try:
                        expected_behavior.append(ExpectedDeformationBehavior(b))
                    except ValueError:
                        pass

        # Calibration Profile
        raw_cp = getattr(infrastructure, "calibration_profile", None) or (
            infrastructure.get("calibration_profile") if isinstance(infrastructure, dict) else None
        )
        calibration_profile: CalibrationProfile
        if raw_cp:
            if isinstance(raw_cp, CalibrationProfile):
                calibration_profile = raw_cp
            elif isinstance(raw_cp, dict):
                calibration_profile = CalibrationProfile(**raw_cp)
            else:
                calibration_profile = CalibrationProfile()
        else:
            calibration_profile = CalibrationProfile()

        profile_ver = str(getattr(infrastructure, "profile_version", None) or (
            infrastructure.get("profile_version") if isinstance(infrastructure, dict) else DEFAULT_PROFILE_VERSION
        ) or DEFAULT_PROFILE_VERSION)

        # 3. Obtain or evaluate Temporal Evidence Summary
        if temporal_summary is None:
            temporal_summary = self.temporal_engine.evaluate_summary(
                infrastructure_id=infra_id,
                observations=observations,
            )

        # 4. Normalize evidence components & baseline deviations
        evidence = calculate_evidence_components(
            temporal_summary=temporal_summary,
            calibration_profile=calibration_profile,
            historical_baseline=historical_baseline,
            critical_zones=critical_zones,
            expected_behavior=expected_behavior,
            recent_observations=observations,
        )

        # 5. Evaluate 9-step decision hierarchy
        state, conf, proto_index, sup_factors, suppr_factors, unc_factors = evaluate_decision_hierarchy(
            temporal_summary=temporal_summary,
            evidence=evidence,
            calibration_profile=calibration_profile,
            criticality=criticality,
            critical_zones=critical_zones,
            historical_baseline=historical_baseline,
            expected_behavior=expected_behavior,
        )

        # 6. Generate structured explanation
        explanation_str = generate_structured_explanation(
            state=state,
            evidence=evidence,
            supporting_factors=sup_factors,
            suppressing_factors=suppr_factors,
            uncertainty_factors=unc_factors,
            structure_type=struct_type.value if hasattr(struct_type, "value") else str(struct_type),
            material=material.value if hasattr(material, "value") else str(material),
            criticality=criticality,
        )

        # 7. Package complete audit versioning metadata
        version_meta = {
            "characterization_version": CHARACTERIZATION_VERSION,
            "profile_version": profile_ver,
            "temporal_version": "strata_temporal_v1_0_0",
            "consensus_version": "strata_consensus_v1_0_0",
            "physics_version": "strata_physics_v1_0_0",
            "ml_model_version": "strata_ml_v0_1_0",
            "configuration_version": "strata_config_v1_0_0",
        }

        # Observation window bounds
        window_start = temporal_summary.first_observation_time
        window_end = temporal_summary.last_observation_time

        return RiskCharacterizationRead(
            id=str(uuid.uuid4()),
            infrastructure_id=infra_id,
            observation_window_start=window_start,
            observation_window_end=window_end,
            epoch_count=temporal_summary.observation_count,
            characterization_state=state,
            confidence=round(conf, 4),
            prototype_risk_index=proto_index,
            evidence_components=evidence,
            supporting_factors=sup_factors,
            suppressing_factors=suppr_factors,
            uncertainty_factors=unc_factors,
            explanation=explanation_str,
            version_metadata=version_meta,
            created_at=datetime.now(timezone.utc),
        )
