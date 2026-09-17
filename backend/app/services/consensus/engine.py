"""
Cross-Model Consensus Engine for STRATA.
Synthesizes ML Deformation Classifier predictions and Physics InSAR Consistency Engine
evidence into a unified, traceable consensus interpretation.
"""
from typing import Any, Dict, List, Optional, Set, Union
from backend.app.schemas.consensus import (
    ConsensusAssessment,
    ConsensusCategory,
)
from backend.app.schemas.ml import MLClassificationResult
from backend.app.schemas.physics import (
    PhysicsAssessmentRead,
    PhysicsClassification,
    PhysicsEvidence,
)
from backend.app.services.consensus.agreement import (
    calculate_agreement_score,
    calculate_disagreement_penalty,
    evaluate_agreement_flags,
)
from backend.app.services.consensus.confidence import calculate_consensus_confidence
from backend.app.services.consensus.decision import determine_consensus_class
from backend.app.services.consensus.evidence import (
    _extract_evidence_payload,
    calculate_evidence_quality_score,
    calculate_physics_evidence_strength,
)
from backend.app.services.consensus.explanation import generate_consensus_explanation
from backend.app.services.consensus.mapping import (
    aggregate_ml_category_probabilities,
    map_ml_class_to_consensus,
    map_physics_class_to_consensus,
)

CONSENSUS_ENGINE_VERSION = "strata_consensus_v0.1.0"

# Strict leakage firewall: reject hidden synthetic generator parameters
FORBIDDEN_GROUND_TRUTH_KEYS: Set[str] = {
    "ground_truth_class",
    "true_structural_displacement_mm",
    "true_environmental_displacement_mm",
    "true_atmospheric_displacement_mm",
    "true_noise_mm",
    "seasonal_amplitude_mm",
    "seasonal_period_days",
    "linear_velocity_mm_yr",
    "acceleration_mm_yr2",
    "step_epoch_idx",
    "step_magnitude_mm",
    "noise_std_mm",
    "spatial_wavelength_m",
    "spike_magnitude_mm",
}


def _verify_no_ground_truth_leakage(data: Any, path: str = "input") -> None:
    """
    Recursively inspects data dictionaries and objects to ensure no hidden
    ground-truth generator parameters leak into the consensus layer.
    """
    if isinstance(data, dict):
        for k, v in data.items():
            if k in FORBIDDEN_GROUND_TRUTH_KEYS:
                raise ValueError(
                    f"Ground-truth leakage firewall violation at '{path}.{k}': "
                    f"Consensus engine strictly rejects hidden synthetic parameters."
                )
            if isinstance(v, (dict, list)):
                _verify_no_ground_truth_leakage(v, f"{path}.{k}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                _verify_no_ground_truth_leakage(item, f"{path}[{idx}]")


class ConsensusEngine:
    """
    STRATA Cross-Model Consensus & Evidence Fusion Engine.
    Combines independent ML and Physics evidence without simple averaging.
    Enforces the central principle:
      AGREEMENT -> increased confidence
      DISAGREEMENT -> reduced confidence / increased uncertainty
    """

    def __init__(self, version: str = CONSENSUS_ENGINE_VERSION):
        self.version = version

    def evaluate(
        self,
        ml_result: MLClassificationResult,
        physics_evidence: Union[PhysicsEvidence, PhysicsAssessmentRead, Dict[str, Any]],
        epoch_count: Optional[int] = None,
        **extra_inputs: Any,
    ) -> ConsensusAssessment:
        """
        Executes cross-model consensus evaluation.

        Parameters:
          ml_result: Inference output from MLDeformationClassifier
          physics_evidence: Output from PhysicsInSARConsistencyEngine
          epoch_count: Number of observation epochs in sequence (optional, inferred if None)
        """
        # 1. Enforce ground-truth leakage firewall
        if extra_inputs:
            _verify_no_ground_truth_leakage(extra_inputs, path="extra_inputs")
        _verify_no_ground_truth_leakage(ml_result.model_dump(), path="ml_result")
        payload = _extract_evidence_payload(physics_evidence)
        _verify_no_ground_truth_leakage(payload, path="physics_evidence")

        # 2. Extract physics classification and epoch count
        raw_phys_class = payload.get("classification")
        if isinstance(raw_phys_class, PhysicsClassification):
            physics_class_enum = raw_phys_class
        elif isinstance(raw_phys_class, str):
            physics_class_enum = PhysicsClassification(raw_phys_class)
        else:
            raise ValueError(f"Invalid physics classification: {raw_phys_class}")

        if epoch_count is None:
            temporal_dict = payload.get("temporal_evidence", {})
            epoch_count = int(temporal_dict.get("epoch_count", payload.get("epoch_count", 0)))

        # 3. Semantic Taxonomy Mapping & ML Probability Mass Aggregation
        physics_category = map_physics_class_to_consensus(physics_class_enum)
        ml_predicted_category = map_ml_class_to_consensus(ml_result.predicted_class)
        ml_category_masses = aggregate_ml_category_probabilities(ml_result.probabilities)

        # 4. Cross-Model Agreement & Disagreement Penalty
        agreement_score = calculate_agreement_score(ml_category_masses, physics_category)
        disagreement_penalty = calculate_disagreement_penalty(agreement_score)

        # 5. Diagnostic Agreement & Conflict Flags
        flags = evaluate_agreement_flags(ml_category_masses, physics_category, agreement_score)

        # 6. Observational Evidence Quality & Temporal Persistence
        from backend.app.services.consensus.temporal import calculate_temporal_persistence_score

        evidence_quality_score = calculate_evidence_quality_score(physics_evidence)
        temporal_persistence_score = calculate_temporal_persistence_score(physics_evidence)
        physics_evidence_strength = calculate_physics_evidence_strength(physics_evidence)

        # 7. Consensus Classification via Decision Hierarchy
        consensus_class = determine_consensus_class(
            physics_category=physics_category,
            ml_category_masses=ml_category_masses,
            ml_predicted_category=ml_predicted_category,
            evidence_quality_score=evidence_quality_score,
            epoch_count=epoch_count,
            flags=flags,
        )

        # 8. Bounded Confidence Fusion
        consensus_confidence = calculate_consensus_confidence(
            ml_confidence=ml_result.confidence,
            physics_evidence_strength=physics_evidence_strength,
            agreement_score=agreement_score,
            evidence_quality_score=evidence_quality_score,
            temporal_persistence_score=temporal_persistence_score,
            consensus_class=consensus_class,
            flags=flags,
        )

        # 9. Transparent Justification Explanation
        explanation = generate_consensus_explanation(
            consensus_class=consensus_class,
            consensus_confidence=consensus_confidence,
            agreement_score=agreement_score,
            disagreement_penalty=disagreement_penalty,
            evidence_quality_score=evidence_quality_score,
            temporal_persistence_score=temporal_persistence_score,
            physics_category=physics_category,
            ml_category_masses=ml_category_masses,
            flags=flags,
        )

        # 10. Assemble preserved contributions & provenance metadata
        provenance = payload.get("provenance", {})
        physics_version = str(provenance.get("engine_version", "strata_physics_v0.2.1"))

        ml_contrib: Dict[str, Any] = {
            "predicted_class": ml_result.predicted_class.value,
            "predicted_category": ml_predicted_category.value,
            "confidence": ml_result.confidence,
            "entropy": ml_result.entropy,
            "probabilities": ml_result.probabilities,
            "category_masses": {cat.value: mass for cat, mass in ml_category_masses.items()},
            "model_version": ml_result.model_version,
        }

        phys_contrib: Dict[str, Any] = {
            "classification": physics_class_enum.value,
            "category": physics_category.value,
            "evidence_strength": physics_evidence_strength,
            "overall_confidence": payload.get("overall_confidence"),
            "measurement_quality_score": payload.get("measurement_quality", {}).get("quality_score"),
            "data_sufficiency": payload.get("temporal_evidence", {}).get("data_sufficiency"),
            "epoch_count": epoch_count,
            "engine_version": physics_version,
        }

        model_versions: Dict[str, str] = {
            "consensus_engine": self.version,
            "ml_model": ml_result.model_version,
            "physics_engine": physics_version,
        }

        return ConsensusAssessment(
            consensus_class=consensus_class,
            consensus_confidence=consensus_confidence,
            agreement_score=agreement_score,
            disagreement_penalty=disagreement_penalty,
            evidence_quality_score=evidence_quality_score,
            temporal_persistence_score=temporal_persistence_score,
            ml_contribution=ml_contrib,
            physics_contribution=phys_contrib,
            explanation=explanation,
            flags=flags,
            model_versions=model_versions,
            consensus_engine_version=self.version,
        )
