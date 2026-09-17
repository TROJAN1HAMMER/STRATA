"""
Comprehensive unit tests for STRATA Cross-Model Consensus & Evidence Fusion (Phase 5).
Validates taxonomy mapping, agreement/disagreement metrics, evidence quality,
temporal persistence, confidence fusion, decision hierarchy, monotonicity,
ground-truth leakage firewall, and Scenarios A through H.
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.schemas.consensus import (
    ConsensusAssessment,
    ConsensusCategory,
    ConsensusFlag,
)
from backend.app.schemas.ml import MLClassificationResult
from backend.app.schemas.physics import (
    AtmosphericEvidence,
    EnvironmentalEvidence,
    GeometryEvidence,
    GeometryStatus,
    KinematicEvidence,
    MeasurementQualityEvidence,
    PhysicsAssessmentRead,
    PhysicsClassification,
    PhysicsEvidence,
    TemporalEvidence,
    TemporalTrendPattern,
)
from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.consensus.agreement import (
    calculate_agreement_score,
    calculate_disagreement_penalty,
    evaluate_agreement_flags,
)
from backend.app.services.consensus.confidence import calculate_consensus_confidence
from backend.app.services.consensus.decision import determine_consensus_class
from backend.app.services.consensus.engine import ConsensusEngine
from backend.app.services.consensus.evidence import (
    calculate_evidence_quality_score,
    calculate_physics_evidence_strength,
)
from backend.app.services.consensus.mapping import (
    aggregate_ml_category_probabilities,
    map_ml_class_to_consensus,
    map_physics_class_to_consensus,
)
from backend.app.services.consensus.temporal import calculate_temporal_persistence_score


# ---------------------------------------------------------------------------
# FIXTURE GENERATORS
# ---------------------------------------------------------------------------

def make_dummy_physics_evidence(
    classification: PhysicsClassification = PhysicsClassification.STRUCTURALLY_CONSISTENT,
    quality_score: float = 0.85,
    coherence: float = 0.80,
    data_sufficiency: float = 0.90,
    persistence: float = 0.85,
    directional_consistency: float = 0.90,
    rate_consistency: float = 0.80,
    abrupt_inconsistency: float = 0.05,
    atmospheric_suspect_score: float = 0.10,
    seasonal_pattern_strength: float = 0.05,
    overall_confidence: float = 0.85,
    epoch_count: int = 15,
) -> PhysicsEvidence:
    """Creates a controlled PhysicsEvidence instance for consensus testing."""
    return PhysicsEvidence(
        classification=classification,
        measurement_quality=MeasurementQualityEvidence(
            quality_score=quality_score,
            coherence_score=coherence,
            phase_quality_score=0.85,
            has_sufficient_coherence=True,
            explanation=["High interferometric coherence."],
        ),
        geometry_evidence=GeometryEvidence(
            status=GeometryStatus.VALID_GEOMETRY,
            incidence_angle_deg=35.0,
            explanation=["Valid satellite radar geometry."],
        ),
        kinematic_evidence=KinematicEvidence(
            kinematic_consistency=0.85,
            mean_kinematic_residual_mm_yr=1.2,
            explanation=["Consistent kinematic velocity."],
        ),
        temporal_evidence=TemporalEvidence(
            persistence=persistence,
            directional_consistency=directional_consistency,
            rate_consistency=rate_consistency,
            abrupt_inconsistency_score=abrupt_inconsistency,
            data_sufficiency=data_sufficiency,
            trend_pattern=TemporalTrendPattern.MONOTONIC,
            epoch_count=epoch_count,
            explanation=["Continuous multi-epoch signal."],
        ),
        atmospheric_evidence=AtmosphericEvidence(
            atmospheric_suspect_score=atmospheric_suspect_score,
            has_transient_spike=False,
            atmospheric_data_status="AVAILABLE",
            explanation=["Atmospheric disturbance low."],
        ),
        environmental_evidence=EnvironmentalEvidence(
            periodicity_detected=seasonal_pattern_strength > 0.40,
            seasonal_pattern_strength=seasonal_pattern_strength,
            environmental_suspect_score=seasonal_pattern_strength,
            explanation=["Environmental evaluation completed."],
        ),
        overall_confidence=overall_confidence,
        explanation=["Physics analysis completed."],
        is_stub=False,
        provenance={"engine_name": "STRATA Deterministic Physics Engine", "engine_version": "strata_physics_v0.2.1"},
    )


def make_dummy_ml_result(
    pred_class: GroundTruthClass = GroundTruthClass.STRUCTURAL_MONOTONIC,
    confidence: float = 0.85,
    entropy: float = 0.25,
    prob_dist: dict = None,
) -> MLClassificationResult:
    """Creates a controlled MLClassificationResult instance for consensus testing."""
    if prob_dist is None:
        prob_dist = {
            GroundTruthClass.STABLE.value: 0.02,
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.70,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.15,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.05,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.04,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.02,
        }
    return MLClassificationResult(
        predicted_class=pred_class,
        probabilities=prob_dist,
        confidence=confidence,
        entropy=entropy,
        model_version="strata_ml_v0_1_0",
        feature_version="strata_features_v0_1_0",
    )


# ---------------------------------------------------------------------------
# 1. TAXONOMY MAPPING & AGGREGATION TESTS
# ---------------------------------------------------------------------------

def test_ml_to_consensus_mapping():
    assert map_ml_class_to_consensus(GroundTruthClass.STABLE) == ConsensusCategory.STABLE
    assert map_ml_class_to_consensus(GroundTruthClass.STRUCTURAL_MONOTONIC) == ConsensusCategory.STRUCTURAL
    assert map_ml_class_to_consensus(GroundTruthClass.STRUCTURAL_ACCELERATING) == ConsensusCategory.STRUCTURAL
    assert map_ml_class_to_consensus(GroundTruthClass.SEASONAL_ENVIRONMENTAL) == ConsensusCategory.SEASONAL
    assert map_ml_class_to_consensus(GroundTruthClass.ATMOSPHERIC_TRANSIENT) == ConsensusCategory.ATMOSPHERIC
    assert map_ml_class_to_consensus(GroundTruthClass.LOW_QUALITY) == ConsensusCategory.LOW_QUALITY
    assert map_ml_class_to_consensus(GroundTruthClass.TEMPORALLY_INCONSISTENT) == ConsensusCategory.TEMPORALLY_INCONSISTENT


def test_physics_to_consensus_mapping():
    assert map_physics_class_to_consensus(PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION) == ConsensusCategory.STABLE
    assert map_physics_class_to_consensus(PhysicsClassification.STRUCTURALLY_CONSISTENT) == ConsensusCategory.STRUCTURAL
    assert map_physics_class_to_consensus(PhysicsClassification.SEASONALLY_SUSPECT) == ConsensusCategory.SEASONAL
    assert map_physics_class_to_consensus(PhysicsClassification.ATMOSPHERICALLY_SUSPECT) == ConsensusCategory.ATMOSPHERIC
    assert map_physics_class_to_consensus(PhysicsClassification.LOW_QUALITY) == ConsensusCategory.LOW_QUALITY
    assert map_physics_class_to_consensus(PhysicsClassification.TEMPORALLY_INCONSISTENT) == ConsensusCategory.TEMPORALLY_INCONSISTENT
    assert map_physics_class_to_consensus(PhysicsClassification.INSUFFICIENT_EVIDENCE) == ConsensusCategory.INSUFFICIENT_EVIDENCE


def test_ml_probability_mass_aggregation():
    dist = {
        GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.55,
        GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.20,
        GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.10,
        GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.05,
        GroundTruthClass.STABLE.value: 0.05,
        GroundTruthClass.LOW_QUALITY.value: 0.03,
        GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.02,
    }
    masses = aggregate_ml_category_probabilities(dist)
    # Structural mass should combine monotonic (0.55) + accelerating (0.20) = 0.75
    assert masses[ConsensusCategory.STRUCTURAL] == pytest.approx(0.75, abs=1e-4)
    assert masses[ConsensusCategory.SEASONAL] == pytest.approx(0.10, abs=1e-4)
    assert masses[ConsensusCategory.ATMOSPHERIC] == pytest.approx(0.05, abs=1e-4)
    assert masses[ConsensusCategory.STABLE] == pytest.approx(0.05, abs=1e-4)
    assert masses[ConsensusCategory.LOW_QUALITY] == pytest.approx(0.03, abs=1e-4)
    assert masses[ConsensusCategory.TEMPORALLY_INCONSISTENT] == pytest.approx(0.02, abs=1e-4)
    assert masses[ConsensusCategory.INSUFFICIENT_EVIDENCE] == 0.0


# ---------------------------------------------------------------------------
# 2. AGREEMENT & DISAGREEMENT METRICS
# ---------------------------------------------------------------------------

def test_agreement_score_and_penalty():
    masses = {
        ConsensusCategory.STRUCTURAL: 0.75,
        ConsensusCategory.SEASONAL: 0.15,
        ConsensusCategory.STABLE: 0.10,
    }

    # High agreement
    score = calculate_agreement_score(masses, ConsensusCategory.STRUCTURAL)
    assert score == pytest.approx(0.75, abs=1e-4)
    penalty = calculate_disagreement_penalty(score)
    assert penalty == pytest.approx(0.25, abs=1e-4)

    # Low agreement
    score_low = calculate_agreement_score(masses, ConsensusCategory.SEASONAL)
    assert score_low == pytest.approx(0.15, abs=1e-4)
    penalty_high = calculate_disagreement_penalty(score_low)
    assert penalty_high == pytest.approx(0.85, abs=1e-4)

    # Insufficient evidence produces zero agreement
    score_insuff = calculate_agreement_score(masses, ConsensusCategory.INSUFFICIENT_EVIDENCE)
    assert score_insuff == 0.0
    penalty_insuff = calculate_disagreement_penalty(score_insuff)
    assert penalty_insuff == 1.0


def test_agreement_flags_generation():
    # Strong agreement
    flags_strong = evaluate_agreement_flags(
        {ConsensusCategory.STRUCTURAL: 0.85},
        ConsensusCategory.STRUCTURAL,
        0.85,
    )
    assert ConsensusFlag.STRONG_MODEL_AGREEMENT.value in flags_strong
    assert ConsensusFlag.MODEL_AGREEMENT.value in flags_strong

    # Strong disagreement
    flags_disagree = evaluate_agreement_flags(
        {ConsensusCategory.STRUCTURAL: 0.10, ConsensusCategory.SEASONAL: 0.85},
        ConsensusCategory.STRUCTURAL,
        0.10,
    )
    assert ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value in flags_disagree
    assert ConsensusFlag.MODEL_DISAGREEMENT.value in flags_disagree

    # Environmental conflict
    flags_env_conflict = evaluate_agreement_flags(
        {ConsensusCategory.STRUCTURAL: 0.65, ConsensusCategory.SEASONAL: 0.20},
        ConsensusCategory.SEASONAL,
        0.20,
    )
    assert ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in flags_env_conflict


# ---------------------------------------------------------------------------
# 3. MATHEMATICAL SANITY & MONOTONICITY TESTS
# ---------------------------------------------------------------------------

def test_agreement_monotonicity():
    """Increasing ML probability for physics category must not decrease agreement score."""
    p_values = [0.10, 0.25, 0.50, 0.75, 0.90]
    scores = []
    penalties = []
    for p in p_values:
        masses = {ConsensusCategory.STRUCTURAL: p}
        s = calculate_agreement_score(masses, ConsensusCategory.STRUCTURAL)
        pen = calculate_disagreement_penalty(s)
        scores.append(s)
        penalties.append(pen)

    # Scores must be strictly increasing
    for i in range(len(scores) - 1):
        assert scores[i] <= scores[i + 1]
    # Penalties must be strictly decreasing
    for i in range(len(penalties) - 1):
        assert penalties[i] >= penalties[i + 1]


def test_confidence_monotonicity_wrt_agreement():
    """Increasing agreement score must not reduce consensus confidence (all else equal)."""
    agreement_levels = [0.10, 0.30, 0.50, 0.70, 0.90]
    confidences = []
    for ag in agreement_levels:
        c = calculate_consensus_confidence(
            ml_confidence=0.80,
            physics_evidence_strength=0.80,
            agreement_score=ag,
            evidence_quality_score=0.85,
            temporal_persistence_score=0.80,
            consensus_class=ConsensusCategory.STRUCTURAL,
            flags=[],
        )
        confidences.append(c)

    for i in range(len(confidences) - 1):
        assert confidences[i] <= confidences[i + 1]


def test_confidence_monotonicity_wrt_evidence_quality():
    """Increasing evidence quality must not reduce consensus confidence (all else equal)."""
    quality_levels = [0.40, 0.55, 0.70, 0.85, 1.00]
    confidences = []
    for q in quality_levels:
        c = calculate_consensus_confidence(
            ml_confidence=0.80,
            physics_evidence_strength=0.80,
            agreement_score=0.80,
            evidence_quality_score=q,
            temporal_persistence_score=0.80,
            consensus_class=ConsensusCategory.STRUCTURAL,
            flags=[],
        )
        confidences.append(c)

    for i in range(len(confidences) - 1):
        assert confidences[i] <= confidences[i + 1]


def test_agreement_vs_disagreement_confidence_comparison():
    """Under identical evidence, strong agreement produces higher confidence than strong disagreement."""
    conf_agree = calculate_consensus_confidence(
        ml_confidence=0.80,
        physics_evidence_strength=0.80,
        agreement_score=0.85,
        evidence_quality_score=0.80,
        temporal_persistence_score=0.80,
        consensus_class=ConsensusCategory.STRUCTURAL,
        flags=[ConsensusFlag.STRONG_MODEL_AGREEMENT.value],
    )
    conf_disagree = calculate_consensus_confidence(
        ml_confidence=0.80,
        physics_evidence_strength=0.80,
        agreement_score=0.10,
        evidence_quality_score=0.80,
        temporal_persistence_score=0.80,
        consensus_class=ConsensusCategory.STRUCTURAL,
        flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value],
    )
    assert conf_agree > conf_disagree
    # Gap must be substantial (> 0.15)
    assert (conf_agree - conf_disagree) > 0.15


# ---------------------------------------------------------------------------
# 4. SCENARIO TESTS A THROUGH H
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return ConsensusEngine()


def test_scenario_a_strong_structural_agreement(engine):
    """Scenario A: ML structural high + Physics STRUCTURALLY_CONSISTENT -> STRUCTURAL consensus."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.STRUCTURALLY_CONSISTENT,
        quality_score=0.90,
        overall_confidence=0.88,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        confidence=0.85,
        prob_dist={
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.65,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.20,
            GroundTruthClass.STABLE.value: 0.05,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.04,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.03,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class == ConsensusCategory.STRUCTURAL
    assert assessment.agreement_score >= 0.80
    assert assessment.disagreement_penalty <= 0.20
    assert assessment.consensus_confidence >= 0.65
    assert ConsensusFlag.STRONG_MODEL_AGREEMENT.value in assessment.flags


def test_scenario_b_strong_seasonal_agreement(engine):
    """Scenario B: ML seasonal high + Physics SEASONALLY_SUSPECT -> SEASONAL consensus."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.SEASONALLY_SUSPECT,
        seasonal_pattern_strength=0.85,
        overall_confidence=0.80,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.SEASONAL_ENVIRONMENTAL,
        confidence=0.82,
        prob_dist={
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.82,
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.05,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.03,
            GroundTruthClass.STABLE.value: 0.05,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.02,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class == ConsensusCategory.SEASONAL
    assert assessment.agreement_score >= 0.80
    assert assessment.consensus_confidence >= 0.60
    assert ConsensusFlag.STRONG_MODEL_AGREEMENT.value in assessment.flags


def test_scenario_c_strong_atmospheric_agreement(engine):
    """Scenario C: ML atmospheric high + Physics ATMOSPHERICALLY_SUSPECT -> ATMOSPHERIC consensus."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.ATMOSPHERICALLY_SUSPECT,
        atmospheric_suspect_score=0.85,
        overall_confidence=0.75,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.ATMOSPHERIC_TRANSIENT,
        confidence=0.80,
        prob_dist={
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.80,
            GroundTruthClass.STABLE.value: 0.10,
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.03,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.02,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.02,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class == ConsensusCategory.ATMOSPHERIC
    assert assessment.agreement_score >= 0.75
    assert ConsensusFlag.MODEL_AGREEMENT.value in assessment.flags


def test_scenario_d_structural_vs_seasonal_conflict(engine):
    """
    Scenario D: ML strongly predicts structural, but Physics says SEASONALLY_SUSPECT.
    Consensus MUST NOT declare structural; it must flag conflict and reduce confidence.
    """
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.SEASONALLY_SUSPECT,
        seasonal_pattern_strength=0.80,
        overall_confidence=0.80,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        confidence=0.85,
        prob_dist={
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.70,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.15,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.05,
            GroundTruthClass.STABLE.value: 0.05,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.02,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    # Structural consensus MUST NOT be declared!
    assert assessment.consensus_class != ConsensusCategory.STRUCTURAL
    assert assessment.consensus_class == ConsensusCategory.SEASONAL
    # Must identify environmental structural conflict and disagreement
    assert ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value in assessment.flags
    assert ConsensusFlag.MODEL_DISAGREEMENT.value in assessment.flags
    # Agreement score with Physics (Seasonal) is low (0.05)
    assert assessment.agreement_score <= 0.10
    assert assessment.disagreement_penalty >= 0.90


def test_scenario_e_structural_vs_atmospheric_conflict(engine):
    """
    Scenario E: ML strongly predicts structural, but Physics says ATMOSPHERICALLY_SUSPECT.
    Consensus MUST NOT declare structural; it must flag conflict and reduce confidence.
    """
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.ATMOSPHERICALLY_SUSPECT,
        atmospheric_suspect_score=0.85,
        overall_confidence=0.75,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        confidence=0.85,
        prob_dist={
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.80,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.05,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.05,
            GroundTruthClass.STABLE.value: 0.05,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.02,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class != ConsensusCategory.STRUCTURAL
    assert assessment.consensus_class == ConsensusCategory.ATMOSPHERIC
    assert ConsensusFlag.ATMOSPHERIC_STRUCTURAL_CONFLICT.value in assessment.flags
    assert ConsensusFlag.MODEL_DISAGREEMENT.value in assessment.flags


def test_scenario_f_low_quality_evidence(engine):
    """Scenario F: Low quality evidence suppresses confidence regardless of ML structural confidence."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.LOW_QUALITY,
        quality_score=0.20,
        coherence=0.20,
        overall_confidence=0.25,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        confidence=0.90,  # ML is confident, but data is bad
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class == ConsensusCategory.LOW_QUALITY
    assert ConsensusFlag.LOW_QUALITY_EVIDENCE.value in assessment.flags
    # Confidence must be strictly suppressed
    assert assessment.consensus_confidence <= 0.35


def test_scenario_g_insufficient_evidence(engine):
    """Scenario G: Physics INSUFFICIENT_EVIDENCE -> consensus remains INSUFFICIENT_EVIDENCE with capped confidence."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.INSUFFICIENT_EVIDENCE,
        epoch_count=3,
        overall_confidence=0.15,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        confidence=0.80,
    )
    assessment = engine.evaluate(ml, phys, epoch_count=3)
    assert assessment.consensus_class == ConsensusCategory.INSUFFICIENT_EVIDENCE
    assert ConsensusFlag.INSUFFICIENT_EVIDENCE_SUPPRESSION.value in assessment.flags
    assert assessment.consensus_confidence <= 0.25


def test_scenario_h_stable_agreement(engine):
    """Scenario H: Both ML and Physics indicate stable signal."""
    phys = make_dummy_physics_evidence(
        classification=PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION,
        quality_score=0.90,
        overall_confidence=0.85,
    )
    ml = make_dummy_ml_result(
        pred_class=GroundTruthClass.STABLE,
        confidence=0.85,
        prob_dist={
            GroundTruthClass.STABLE.value: 0.85,
            GroundTruthClass.STRUCTURAL_MONOTONIC.value: 0.04,
            GroundTruthClass.STRUCTURAL_ACCELERATING.value: 0.02,
            GroundTruthClass.SEASONAL_ENVIRONMENTAL.value: 0.04,
            GroundTruthClass.ATMOSPHERIC_TRANSIENT.value: 0.02,
            GroundTruthClass.LOW_QUALITY.value: 0.02,
            GroundTruthClass.TEMPORALLY_INCONSISTENT.value: 0.01,
        },
    )
    assessment = engine.evaluate(ml, phys)
    assert assessment.consensus_class == ConsensusCategory.STABLE
    assert assessment.agreement_score >= 0.80
    assert assessment.consensus_confidence >= 0.65
    assert ConsensusFlag.STRONG_MODEL_AGREEMENT.value in assessment.flags


# ---------------------------------------------------------------------------
# 5. GROUND-TRUTH LEAKAGE FIREWALL TESTS
# ---------------------------------------------------------------------------

def test_ground_truth_leakage_rejection(engine):
    """Consensus engine must reject any input containing hidden synthetic generator parameters."""
    phys = make_dummy_physics_evidence()
    ml = make_dummy_ml_result()

    # Leaking generator parameter via extra kwargs
    with pytest.raises(ValueError, match="Ground-truth leakage firewall violation"):
        engine.evaluate(ml, phys, true_structural_displacement_mm=5.2)

    with pytest.raises(ValueError, match="Ground-truth leakage firewall violation"):
        engine.evaluate(ml, phys, ground_truth_class="STRUCTURAL_MONOTONIC")

    with pytest.raises(ValueError, match="Ground-truth leakage firewall violation"):
        engine.evaluate(ml, phys, seasonal_amplitude_mm=3.0)


# ---------------------------------------------------------------------------
# 6. EXPLANATION INTEGRITY & BOUNDS TESTS
# ---------------------------------------------------------------------------

def test_explanation_safety_and_integrity(engine):
    """Explanation must provide transparent metrics and omit ungrounded structural safety claims."""
    phys = make_dummy_physics_evidence()
    ml = make_dummy_ml_result()
    assessment = engine.evaluate(ml, phys)

    explanation = assessment.explanation
    assert len(explanation) > 50
    assert "agreement" in explanation.lower() or "physics" in explanation.lower()
    assert "confidence" in explanation.lower()

    # Critical safety checks: must NOT make safety certifications or failure predictions
    forbidden_terms = [
        "structure will collapse",
        "collapse predicted",
        "structure is unsafe",
        "structure is safe",
        "catastrophic failure",
    ]
    for term in forbidden_terms:
        assert term not in explanation.lower()


# ---------------------------------------------------------------------------
# 7. VERSIONING & PROVENANCE METADATA TESTS
# ---------------------------------------------------------------------------

def test_consensus_versioning(engine):
    phys = make_dummy_physics_evidence()
    ml = make_dummy_ml_result()
    assessment = engine.evaluate(ml, phys)

    assert assessment.consensus_engine_version == "strata_consensus_v0.1.0"
    assert "consensus_engine" in assessment.model_versions
    assert "ml_model" in assessment.model_versions
    assert "physics_engine" in assessment.model_versions
    assert assessment.ml_contribution["model_version"] == "strata_ml_v0_1_0"
    assert assessment.physics_contribution["engine_version"] == "strata_physics_v0.2.1"


# ---------------------------------------------------------------------------
# 8. API INTEGRATION TEST
# ---------------------------------------------------------------------------

def test_api_consensus_endpoint():
    """Validates the POST /api/v1/analysis/consensus/{observation_id} endpoint."""
    client = TestClient(app)

    # 1. Create infrastructure
    infra_resp = client.post(
        "/api/v1/infrastructure/",
        json={
            "name": "Consensus Test Viaduct",
            "asset_type": "BRIDGE",
            "latitude": 45.4642,
            "longitude": 9.1900,
            "criticality": "HIGH",
        },
    )
    assert infra_resp.status_code == 201
    infra_id = infra_resp.json()["id"]

    # 2. Submit multi-epoch observations
    last_obs_id = None
    for i in range(1, 10):
        obs_resp = client.post(
            "/api/v1/observations/",
            json={
                "infrastructure_id": infra_id,
                "acquisition_timestamp": f"2025-01-{i:02d}T10:00:00Z",
                "deformation_mm": float(i * -2.5),
                "coherence": 0.88,
                "phase_quality": 0.85,
                "incidence_angle": 35.2,
                "satellite_orbit": "ASCENDING",
                "observation_metadata": {"noise_estimate_mm": 0.8},
            },
        )
        assert obs_resp.status_code == 201
        last_obs_id = obs_resp.json()["id"]

    # 3. Call consensus endpoint
    consensus_resp = client.post(f"/api/v1/analysis/consensus/{last_obs_id}")
    assert consensus_resp.status_code == 200
    data = consensus_resp.json()

    # Validate output schema fields
    assert "consensus_class" in data
    assert "consensus_confidence" in data
    assert "agreement_score" in data
    assert "disagreement_penalty" in data
    assert "evidence_quality_score" in data
    assert "temporal_persistence_score" in data
    assert "ml_contribution" in data
    assert "physics_contribution" in data
    assert "explanation" in data
    assert "flags" in data
    assert "model_versions" in data
    assert data["consensus_engine_version"] == "strata_consensus_v0.1.0"
