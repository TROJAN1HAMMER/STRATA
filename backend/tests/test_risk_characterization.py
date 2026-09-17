"""
STRATA — Phase 7: Infrastructure-Specific Risk Characterization Test Suite.
Comprehensive test suite covering all 35 required validation items:
- Infrastructure Profile (1-6)
- Evidence Normalization & Evaluation (7-16)
- Contextual Modulation (17-20)
- 9-Step Decision Hierarchy (21-25)
- Explainability & Safety Language (26-29)
- Audit Versioning & History (30-33)
- Programmatic Ground-Truth Leakage Firewall (34-35)
"""
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from pydantic import ValidationError

from backend.app.main import app
from backend.app.db.database import get_db
from backend.app.db.models import (
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    Observation,
    RiskCharacterization,
    RiskCharacterizationState,
    StructureType,
)
from backend.app.schemas.consensus import ConsensusAssessment, ConsensusCategory
from backend.app.schemas.risk import (
    CalibrationProfile,
    CriticalZone,
    CriticalZoneType,
    ExpectedDeformationBehavior,
    HistoricalBaseline,
    InfrastructureProfileUpdate,
)
from backend.app.schemas.temporal import (
    ConfidenceDataPoint,
    TemporalEvidenceSummary,
    TemporalStatus,
)
from backend.app.services.risk import (
    CHARACTERIZATION_VERSION,
    InfrastructureRiskCharacterizationEngine,
    calculate_evidence_components,
    evaluate_decision_hierarchy,
    _verify_risk_leakage,
)
from backend.app.services.risk.explanation import PROHIBITED_WORDS_REGEX


client = TestClient(app)


def _create_mock_obs(
    infrastructure_id: str,
    displacements: list,
    coherence: float = 0.85,
    interval_days: int = 14,
    start_date: datetime = None,
) -> list:
    """Helper to generate realistic Observation objects for testing."""
    if start_date is None:
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
    obs_list = []
    for idx, d in enumerate(displacements):
        t = start_date + timedelta(days=idx * interval_days)
        obs_list.append(
            Observation(
                id=f"obs_{infrastructure_id}_{idx}",
                infrastructure_id=infrastructure_id,
                acquisition_timestamp=t,
                deformation_mm=float(d),
                velocity_mm_per_year=0.0,
                coherence=coherence,
                phase_quality=0.85,
                incidence_angle=35.0,
                source="TEST_SYNTHETIC",
            )
        )
    return obs_list


def _create_mock_temporal_summary(
    infrastructure_id: str,
    status: TemporalStatus,
    persistence: float,
    trend_rate: float = 0.0,
    apparent_accel: float = 0.0,
    accel_supported: bool = False,
    obs_count: int = 10,
    coherence: float = 0.85,
    mean_conf: float = 0.80,
    struct_count: int = 5,
    env_count: int = 0,
) -> TemporalEvidenceSummary:
    """Helper to mock a comprehensive TemporalEvidenceSummary."""
    now = datetime.now(timezone.utc)
    traj = [
        ConfidenceDataPoint(
            observation_id=f"obs_{i}",
            timestamp=now - timedelta(days=(obs_count - i) * 14),
            consensus_category="STRUCTURAL" if i < struct_count else "STABLE",
            confidence=mean_conf,
            agreement_score=0.85,
            evidence_quality_score=0.85,
        )
        for i in range(obs_count)
    ]
    return TemporalEvidenceSummary(
        infrastructure_id=infrastructure_id,
        observation_count=obs_count,
        valid_observation_count=obs_count,
        first_observation_time=now - timedelta(days=obs_count * 14),
        last_observation_time=now,
        coverage_duration_days=obs_count * 14.0,
        temporal_status=status,
        confidence_trajectory=traj,
        mean_confidence=mean_conf,
        recent_confidence=mean_conf,
        consensus_category_history=[p.consensus_category for p in traj],
        agreement_history=[0.85] * obs_count,
        structural_candidate_count=struct_count,
        environmental_pattern_count=env_count,
        atmospheric_event_count=0,
        state_transitions=[],
        persistence_score=persistence,
        trend_rate_mm_per_year=trend_rate,
        apparent_acceleration_mm_per_year2=apparent_accel,
        trend_acceleration_mm_per_year2=apparent_accel,
        acceleration_supported=accel_supported,
        acceleration_support_reason="Supported" if accel_supported else "Insufficient",
        missing_epoch_count=0,
        max_interval_days=14.0,
        mean_interval_days=14.0,
        quality_summary={"mean_coherence": coherence, "mean_phase_quality": 0.85},
        explanation="Test explanation",
    )


# =============================================================================
# PART 1: INFRASTRUCTURE PROFILE (Tests 1 - 6)
# =============================================================================

def test_01_create_infrastructure_profile():
    payload = {
        "name": "Phase7 Test Bridge 1",
        "structure_type": "BRIDGE",
        "material": "STEEL",
        "criticality": "HIGH",
        "latitude": 45.123,
        "longitude": 9.456,
        "description": "Strategic highway crossing",
        "expected_behavior": ["MONOTONIC"],
        "critical_zones": [
            {
                "zone_id": "z1",
                "zone_name": "Main Pier 3",
                "zone_type": "PIER",
                "importance_weight": 1.5,
            }
        ],
        "historical_baseline": {
            "baseline_mean_mm": 0.5,
            "baseline_std_mm": 1.2,
            "baseline_observation_count": 24,
        },
    }
    response = client.post("/api/v1/infrastructure", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Phase7 Test Bridge 1"
    assert data["structure_type"] == "BRIDGE"
    assert data["material"] == "STEEL"
    assert data["criticality"] == "HIGH"
    assert len(data["critical_zones"]) == 1
    assert data["critical_zones"][0]["zone_name"] == "Main Pier 3"


def test_02_update_infrastructure_profile():
    # Create base infrastructure
    create_resp = client.post(
        "/api/v1/infrastructure",
        json={"name": "Updatable Dam", "structure_type": "DAM", "latitude": 38.0, "longitude": -120.0},
    )
    infra_id = create_resp.json()["id"]

    # Update profile
    update_payload = {
        "material": "CONCRETE",
        "criticality": "CRITICAL",
        "expected_behavior": ["SEASONAL"],
        "critical_zones": [
            {"zone_id": "cz_crest", "zone_name": "Dam Crest", "zone_type": "CREST", "importance_weight": 1.8}
        ],
        "historical_baseline": {
            "baseline_mean_mm": -1.0,
            "baseline_std_mm": 0.8,
            "baseline_observation_count": 30,
        },
    }
    resp = client.post(f"/api/v1/infrastructure/{infra_id}/profile", json=update_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["material"] == "CONCRETE"
    assert data["criticality"] == "CRITICAL"
    assert data["expected_behavior"] == ["SEASONAL"]
    assert len(data["critical_zones"]) == 1
    assert data["critical_zones"][0]["zone_type"] == "CREST"


def test_03_profile_validation():
    # Invalid latitude
    resp = client.post(
        "/api/v1/infrastructure",
        json={"name": "Invalid Lat", "latitude": 95.0, "longitude": 0.0},
    )
    assert resp.status_code == 422


def test_04_invalid_critical_zone_data():
    # importance_weight must be <= 2.0
    with pytest.raises(ValidationError):
        CriticalZone(
            zone_id="z_bad",
            zone_name="Bad Zone",
            zone_type=CriticalZoneType.PIER,
            importance_weight=3.5,  # Exceeds le=2.0
        )


def test_05_missing_baseline_handling():
    summary = _create_mock_temporal_summary("infra_nobase", TemporalStatus.BASELINE, persistence=0.0)
    calib = CalibrationProfile()
    # Baseline is None
    components = calculate_evidence_components(
        temporal_summary=summary,
        calibration_profile=calib,
        historical_baseline=None,
    )
    assert components.baseline_deviation_mm is None
    assert components.baseline_z_score is None


def test_06_calibration_versioning():
    custom_profile = CalibrationProfile(
        profile_version="custom_v2_dam_profile",
        deformation_reference_range_mm=15.0,
        persistence_weight=0.40,
    )
    assert custom_profile.profile_version == "custom_v2_dam_profile"
    assert custom_profile.deformation_reference_range_mm == 15.0


# =============================================================================
# PART 2: EVIDENCE NORMALIZATION & EVALUATION (Tests 7 - 16)
# =============================================================================

def test_07_baseline_compatible_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_base", "structure_type": "BRIDGE", "material": "CONCRETE"}
    summary = _create_mock_temporal_summary(
        "inf_base",
        status=TemporalStatus.BASELINE,
        persistence=0.0,
        trend_rate=0.5,
        apparent_accel=-2.0,
        accel_supported=False,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.BASELINE
    assert res.prototype_risk_index is not None and res.prototype_risk_index < 20.0


def test_08_persistent_structural_candidate():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_persist", "structure_type": "BRIDGE", "criticality": "HIGH"}
    summary = _create_mock_temporal_summary(
        "inf_persist",
        status=TemporalStatus.PERSISTENT,
        persistence=0.75,
        trend_rate=-12.5,
        apparent_accel=-15.0,
        accel_supported=True,
        mean_conf=0.75,
        struct_count=8,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state in (
        RiskCharacterizationState.HIGH_ATTENTION,
        RiskCharacterizationState.ELEVATED_ATTENTION,
    )
    assert res.evidence_components.temporal_persistence == 0.75


def test_09_seasonal_environmental_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {
        "id": "inf_season",
        "structure_type": "DAM",
        "expected_behavior": ["SEASONAL"],
    }
    summary = _create_mock_temporal_summary(
        "inf_season",
        status=TemporalStatus.ENVIRONMENTAL_PATTERN,
        persistence=0.0,
        trend_rate=1.2,
        env_count=6,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.ENVIRONMENTAL_PATTERN
    assert res.evidence_components.environmental_suppression == 1.0


def test_10_atmospheric_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_atmo", "structure_type": "BUILDING"}
    summary = _create_mock_temporal_summary(
        "inf_atmo",
        status=TemporalStatus.ATMOSPHERIC_EVENT,
        persistence=0.0,
        trend_rate=0.0,
        struct_count=0,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    # Atmospheric event resolving back without persistence evaluates to MONITOR or BASELINE, never elevated attention
    assert res.characterization_state in (
        RiskCharacterizationState.MONITOR,
        RiskCharacterizationState.BASELINE,
    )


def test_11_low_quality_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_lq", "criticality": "CRITICAL"}
    summary = _create_mock_temporal_summary(
        "inf_lq",
        status=TemporalStatus.LOW_QUALITY,
        persistence=0.0,
        coherence=0.15,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE


def test_12_insufficient_temporal_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_short"}
    summary = _create_mock_temporal_summary(
        "inf_short",
        status=TemporalStatus.INSUFFICIENT_HISTORY,
        persistence=0.0,
        obs_count=2,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE


def test_13_model_disagreement():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_conflict"}
    summary = _create_mock_temporal_summary(
        "inf_conflict",
        status=TemporalStatus.CONFLICTED,
        persistence=0.0,
        mean_conf=0.20,
    )
    res = engine.evaluate_infrastructure(infrastructure=infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.MONITOR
    assert any("disagreement" in f.lower() or "conflict" in f.lower() for f in res.uncertainty_factors + res.suppressing_factors)


def test_14_acceleration_unsupported():
    summary = _create_mock_temporal_summary(
        "inf_acc_unsup",
        status=TemporalStatus.CONFLICTED,
        persistence=0.0,
        apparent_accel=1500.0,
        accel_supported=False,  # Short baseline rejection
    )
    comp = calculate_evidence_components(
        temporal_summary=summary,
        calibration_profile=CalibrationProfile(),
    )
    assert comp.acceleration_support == 0.0


def test_15_acceleration_supported():
    summary = _create_mock_temporal_summary(
        "inf_acc_sup",
        status=TemporalStatus.PERSISTENT,
        persistence=0.60,
        apparent_accel=-25.0,
        accel_supported=True,
    )
    comp = calculate_evidence_components(
        temporal_summary=summary,
        calibration_profile=CalibrationProfile(deformation_reference_range_mm=10.0),
    )
    assert comp.acceleration_support > 0.0


def test_16_baseline_deviation_calculation():
    hb = HistoricalBaseline(
        baseline_mean_mm=2.0,
        baseline_std_mm=1.0,
        baseline_observation_count=20,
    )
    summary = _create_mock_temporal_summary("inf_dev", TemporalStatus.PERSISTENT, persistence=0.5)
    # Recent displacement = 5.0 mm -> dev = +3.0 mm, z = +3.0
    mock_obs = [{"deformation_mm": 5.0}] * 3
    comp = calculate_evidence_components(
        temporal_summary=summary,
        calibration_profile=CalibrationProfile(),
        historical_baseline=hb,
        recent_observations=mock_obs,
    )
    assert comp.baseline_deviation_mm == 3.0
    assert comp.baseline_z_score == 3.0


# =============================================================================
# PART 3: CONTEXTUAL MODULATION (Tests 17 - 20)
# =============================================================================

def test_17_critical_zone_contextual_modulation():
    calib = CalibrationProfile()
    cz = [CriticalZone(zone_id="cz1", zone_name="Piers", zone_type=CriticalZoneType.PIER, importance_weight=1.8)]
    summary = _create_mock_temporal_summary("inf_cz", TemporalStatus.PERSISTENT, persistence=0.50)
    
    comp_without_cz = calculate_evidence_components(summary, calib, critical_zones=[])
    comp_with_cz = calculate_evidence_components(summary, calib, critical_zones=cz)
    
    assert comp_with_cz.critical_zone_context > comp_without_cz.critical_zone_context
    assert comp_with_cz.critical_zone_context >= 1.20


def test_18_infrastructure_criticality_contextual_modulation():
    engine = InfrastructureRiskCharacterizationEngine()
    summary = _create_mock_temporal_summary("inf_crit", TemporalStatus.PERSISTENT, persistence=0.60, mean_conf=0.70)
    
    infra_low = {"id": "inf_low", "criticality": CriticalityLevel.LOW}
    infra_high = {"id": "inf_high", "criticality": CriticalityLevel.CRITICAL}
    
    res_low = engine.evaluate_infrastructure(infra_low, observations=[], temporal_summary=summary)
    res_high = engine.evaluate_infrastructure(infra_high, observations=[], temporal_summary=summary)
    
    # Critical asset receives higher prototype attention index for the same deformation evidence
    assert res_high.prototype_risk_index > res_low.prototype_risk_index


def test_19_expected_seasonal_behavior():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {
        "id": "inf_exp_seasonal",
        "expected_behavior": [ExpectedDeformationBehavior.SEASONAL],
    }
    summary = _create_mock_temporal_summary(
        "inf_exp_seasonal",
        status=TemporalStatus.ENVIRONMENTAL_PATTERN,
        persistence=0.0,
        env_count=3,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.ENVIRONMENTAL_PATTERN
    assert any("expected seasonal deformation" in f.lower() for f in res.suppressing_factors)


def test_20_missing_infrastructure_metadata():
    engine = InfrastructureRiskCharacterizationEngine()
    # Missing type, material, criticality, critical_zones, baseline
    infra = {"id": "inf_bare_minimum"}
    summary = _create_mock_temporal_summary("inf_bare_minimum", TemporalStatus.BASELINE, persistence=0.0)
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.BASELINE


# =============================================================================
# PART 4: DECISION HIERARCHY (Tests 21 - 25)
# =============================================================================

def test_21_low_quality_overrides_criticality():
    # CRITICAL infrastructure with LOW_QUALITY data MUST NOT escalate to HIGH_ATTENTION
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_crit_lq", "criticality": CriticalityLevel.CRITICAL}
    summary = _create_mock_temporal_summary(
        "inf_crit_lq",
        status=TemporalStatus.LOW_QUALITY,
        persistence=0.0,
        coherence=0.10,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE
    assert res.characterization_state != RiskCharacterizationState.HIGH_ATTENTION


def test_22_environmental_suppression_prevents_structural_escalation():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_suppress", "criticality": CriticalityLevel.HIGH}
    summary = _create_mock_temporal_summary(
        "inf_suppress",
        status=TemporalStatus.ENVIRONMENTAL_PATTERN,
        persistence=0.0,
        trend_rate=15.0,  # High amplitude cyclical fluctuation
        env_count=6,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.ENVIRONMENTAL_PATTERN
    assert res.characterization_state != RiskCharacterizationState.HIGH_ATTENTION


def test_23_insufficient_evidence_prevents_high_characterization():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_few_epochs", "criticality": CriticalityLevel.CRITICAL}
    summary = _create_mock_temporal_summary(
        "inf_few_epochs",
        status=TemporalStatus.INSUFFICIENT_HISTORY,
        persistence=0.0,
        obs_count=2,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE


def test_24_disagreement_reduces_characterization():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_disagree"}
    summary = _create_mock_temporal_summary(
        "inf_disagree",
        status=TemporalStatus.CONFLICTED,
        persistence=0.0,
        mean_conf=0.18,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.characterization_state == RiskCharacterizationState.MONITOR


def test_25_persistence_increases_characterization_only_when_structural():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_persist_struct"}
    # Structural persistence 0.65 -> ELEVATED_ATTENTION
    summary_struct = _create_mock_temporal_summary(
        "inf_persist_struct",
        status=TemporalStatus.PERSISTENT,
        persistence=0.65,
        trend_rate=-10.0,
        mean_conf=0.70,
    )
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary_struct)
    assert res.characterization_state in (
        RiskCharacterizationState.ELEVATED_ATTENTION,
        RiskCharacterizationState.HIGH_ATTENTION,
    )


# =============================================================================
# PART 5: EXPLAINABILITY & SAFETY (Tests 26 - 29)
# =============================================================================

def test_26_supporting_factors_present():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_sup"}
    summary = _create_mock_temporal_summary("inf_sup", TemporalStatus.PERSISTENT, persistence=0.60, mean_conf=0.75)
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert len(res.supporting_factors) > 0


def test_27_suppressing_factors_present():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_supp"}
    summary = _create_mock_temporal_summary("inf_supp", TemporalStatus.ENVIRONMENTAL_PATTERN, persistence=0.0)
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert len(res.suppressing_factors) > 0


def test_28_explanation_matches_evidence():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_exp"}
    summary = _create_mock_temporal_summary("inf_exp", TemporalStatus.BASELINE, persistence=0.0)
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert "BASELINE" in res.explanation
    assert "Displacement" in res.explanation or "Multi-epoch" in res.explanation


def test_29_no_prohibited_safety_or_collapse_claims():
    engine = InfrastructureRiskCharacterizationEngine()
    for status in [
        TemporalStatus.BASELINE,
        TemporalStatus.PERSISTENT,
        TemporalStatus.ENVIRONMENTAL_PATTERN,
        TemporalStatus.LOW_QUALITY,
    ]:
        summary = _create_mock_temporal_summary("inf_safe", status, persistence=0.5 if status == TemporalStatus.PERSISTENT else 0.0)
        res = engine.evaluate_infrastructure({"id": "inf_safe"}, observations=[], temporal_summary=summary)
        # Verify prohibited keywords are strictly absent
        match = PROHIBITED_WORDS_REGEX.search(res.explanation)
        assert match is None, f"Prohibited word '{match.group(0)}' found in explanation for status {status.value}"


# =============================================================================
# PART 6: AUDIT VERSIONING & HISTORY (Tests 30 - 33)
# =============================================================================

def test_30_characterization_version_recorded():
    engine = InfrastructureRiskCharacterizationEngine()
    summary = _create_mock_temporal_summary("inf_ver", TemporalStatus.BASELINE, persistence=0.0)
    res = engine.evaluate_infrastructure({"id": "inf_ver"}, observations=[], temporal_summary=summary)
    assert res.version_metadata["characterization_version"] == CHARACTERIZATION_VERSION


def test_31_profile_version_recorded():
    engine = InfrastructureRiskCharacterizationEngine()
    infra = {"id": "inf_pver", "profile_version": "v1.4.2_custom"}
    summary = _create_mock_temporal_summary("inf_pver", TemporalStatus.BASELINE, persistence=0.0)
    res = engine.evaluate_infrastructure(infra, observations=[], temporal_summary=summary)
    assert res.version_metadata["profile_version"] == "v1.4.2_custom"


def test_32_model_versions_preserved():
    engine = InfrastructureRiskCharacterizationEngine()
    summary = _create_mock_temporal_summary("inf_all_ver", TemporalStatus.BASELINE, persistence=0.0)
    res = engine.evaluate_infrastructure({"id": "inf_all_ver"}, observations=[], temporal_summary=summary)
    for expected_key in ["consensus_version", "physics_version", "ml_model_version", "temporal_version"]:
        assert expected_key in res.version_metadata


def test_33_changed_profile_preserves_historical_characterizations():
    # Create infrastructure
    c_resp = client.post("/api/v1/infrastructure", json={"name": "History Asset", "latitude": 40.0, "longitude": -74.0})
    infra_id = c_resp.json()["id"]

    # Add observations
    obs_payload = [
        {
            "infrastructure_id": infra_id,
            "acquisition_timestamp": (datetime(2025, 1, 1, tzinfo=timezone.utc) + timedelta(days=i * 14)).isoformat(),
            "deformation_mm": float(i * -1.5),
            "coherence": 0.85,
            "phase_quality": 0.85,
        }
        for i in range(10)
    ]
    for op in obs_payload:
        client.post("/api/v1/observations", json=op)

    # Post initial risk characterization
    rc1_resp = client.post(f"/api/v1/infrastructure/{infra_id}/risk-characterization")
    assert rc1_resp.status_code == 201
    rc1_id = rc1_resp.json()["id"]

    # Update profile to a new version
    client.post(
        f"/api/v1/infrastructure/{infra_id}/profile",
        json={"calibration_profile": {"profile_version": "v2.0.0_experimental"}},
    )

    # Post second risk characterization
    rc2_resp = client.post(f"/api/v1/infrastructure/{infra_id}/risk-characterization")
    assert rc2_resp.status_code == 201
    rc2_id = rc2_resp.json()["id"]

    assert rc1_id != rc2_id

    # Retrieve history
    hist_resp = client.get(f"/api/v1/infrastructure/{infra_id}/risk-characterization?history=true")
    assert hist_resp.status_code == 200
    records = hist_resp.json()
    assert len(records) >= 2
    # Ensure original record's version is unchanged
    old_rec = next(r for r in records if r["id"] == rc1_id)
    assert old_rec["version_metadata"]["profile_version"] == "v1.0.0"


# =============================================================================
# PART 7: PROGRAMMATIC GROUND-TRUTH LEAKAGE FIREWALL (Tests 34 - 35)
# =============================================================================

def test_34_leakage_firewall_blocks_ground_truth_class():
    with pytest.raises(ValueError) as exc:
        _verify_risk_leakage({"ground_truth_class": "STRUCTURAL_ACCELERATING"})
    assert "Programmatic Leakage Firewall Violation" in str(exc.value)


def test_35_leakage_firewall_blocks_generator_parameters():
    for forbidden_param in [
        "true_structural_displacement_mm",
        "seasonal_amplitude_mm",
        "acceleration_mm_yr2",
        "step_magnitude_mm",
        "spike_magnitude_mm",
    ]:
        with pytest.raises(ValueError) as exc:
            _verify_risk_leakage({"payload": {forbidden_param: 5.0}})
        assert "Programmatic Leakage Firewall Violation" in str(exc.value)
