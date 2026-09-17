import json
import os
import pytest
from fastapi.testclient import TestClient
from backend.app.schemas.physics import (
    ObservationSequence,
    PhysicsClassification,
    TemporalTrendPattern,
)
from backend.app.schemas.observation import ObservationRead
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.synthetic.generator import generate_all_scenarios


@pytest.fixture(scope="module")
def all_scenarios():
    return generate_all_scenarios()


def test_scenario_a_stable(all_scenarios):
    sc_data = all_scenarios["SCENARIO_A_STABLE"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_a_{i}", infrastructure_id="infra_a", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_a", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION
    assert result.temporal_evidence.trend_pattern == TemporalTrendPattern.STABLE
    assert result.measurement_quality.quality_score > 0.80
    assert result.atmospheric_evidence.atmospheric_suspect_score < 0.20


def test_scenario_b_persistent_deformation(all_scenarios):
    sc_data = all_scenarios["SCENARIO_B_PERSISTENT"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_b_{i}", infrastructure_id="infra_b", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_b", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.STRUCTURALLY_CONSISTENT
    assert result.temporal_evidence.persistence == 1.0
    assert result.temporal_evidence.directional_consistency == 1.0
    assert result.temporal_evidence.trend_pattern == TemporalTrendPattern.MONOTONIC
    assert result.is_stub is False


def test_scenario_c_atmospheric_anomaly(all_scenarios):
    sc_data = all_scenarios["SCENARIO_C_ATMOSPHERIC"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_c_{i}", infrastructure_id="infra_c", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_c", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.ATMOSPHERICALLY_SUSPECT
    assert result.atmospheric_evidence.has_transient_spike is True
    assert result.atmospheric_evidence.atmospheric_suspect_score >= 0.55


def test_scenario_d_seasonal_pattern(all_scenarios):
    sc_data = all_scenarios["SCENARIO_D_SEASONAL"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_d_{i}", infrastructure_id="infra_d", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_d", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.SEASONALLY_SUSPECT
    assert result.environmental_evidence.periodicity_detected is True
    assert result.environmental_evidence.seasonal_pattern_strength >= 0.60
    assert result.environmental_evidence.environmental_suspect_score >= 0.50


def test_scenario_e_low_quality(all_scenarios):
    sc_data = all_scenarios["SCENARIO_E_LOW_QUALITY"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_e_{i}", infrastructure_id="infra_e", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_e", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.LOW_QUALITY
    assert result.measurement_quality.has_sufficient_coherence is False


def test_scenario_f_accelerating_deformation(all_scenarios):
    sc_data = all_scenarios["SCENARIO_F_ACCELERATING"]
    obs_list = [ObservationRead.model_validate(dict(obs, id=f"sc_f_{i}", infrastructure_id="infra_f", created_at=obs["acquisition_timestamp"])) for i, obs in enumerate(sc_data["observations"])]
    seq = ObservationSequence(infrastructure_id="infra_f", observations=obs_list, epoch_count=len(obs_list))

    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.STRUCTURALLY_CONSISTENT
    assert result.temporal_evidence.trend_pattern == TemporalTrendPattern.ACCELERATING
    assert result.temporal_evidence.persistence >= 0.80


def test_physics_api_pipeline_and_retrieval(client: TestClient, all_scenarios):
    # Ingest Scenario B into API
    sc_b = all_scenarios["SCENARIO_B_PERSISTENT"]
    infra_resp = client.post("/api/v1/infrastructure", json=sc_b["infrastructure"])
    assert infra_resp.status_code == 201
    infra_id = infra_resp.json()["id"]

    for obs in sc_b["observations"]:
        obs_payload = dict(obs, infrastructure_id=infra_id)
        obs_res = client.post("/api/v1/observations", json=obs_payload)
        assert obs_res.status_code == 201

    # Execute Physics Analysis Endpoint
    analysis_res = client.post(f"/api/v1/analysis/physics/{infra_id}")
    assert analysis_res.status_code == 200
    data = analysis_res.json()

    assert data["classification"] == "STRUCTURALLY_CONSISTENT"
    assert data["is_stub"] is False
    assert "measurement_quality" in data
    assert "geometry_evidence" in data
    assert "kinematic_evidence" in data
    assert "temporal_evidence" in data
    assert "atmospheric_evidence" in data
    assert "environmental_evidence" in data
    assert data["temporal_evidence"]["epoch_count"] == 5

    # Retrieve latest physics assessment
    get_res = client.get(f"/api/v1/infrastructure/{infra_id}/physics")
    assert get_res.status_code == 200
    retrieved = get_res.json()
    assert retrieved["infrastructure_id"] == infra_id
    assert retrieved["classification"] == "STRUCTURALLY_CONSISTENT"
    assert retrieved["epoch_count"] == 5

    # Verify 404 for missing infrastructure
    missing_res = client.post("/api/v1/analysis/physics/00000000-0000-0000-0000-000000000000")
    assert missing_res.status_code == 404
