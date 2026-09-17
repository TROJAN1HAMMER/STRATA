import pytest
from fastapi.testclient import TestClient


def test_analyze_observation_pipeline(client: TestClient):
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Suspension Cable Bridge", "structure_type": "BRIDGE", "latitude": 40.5, "longitude": -74.0},
    ).json()

    obs = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-03-01T00:00:00Z",
            "deformation_mm": -5.1,
            "velocity_mm_per_year": -15.2,
            "coherence": 0.77,
            "phase_quality": 0.88,
            "incidence_angle": 35.0,
            "los_displacement_mm": -4.18,
            "source": "SENTINEL_1",
        },
    ).json()

    # Trigger analysis pipeline
    analysis_resp = client.post(f"/api/v1/analysis/{obs['id']}")
    assert analysis_resp.status_code == 201
    data = analysis_resp.json()

    # Scientific integrity assertions
    assert data["is_development_stub"] is True
    assert "scientific_integrity_notice" in data
    assert "stubbed" in data["scientific_integrity_notice"].lower()

    # Breakdown verification
    breakdown = data["component_breakdown"]
    assert breakdown["insar_normalization"]["is_implemented"] is True
    assert breakdown["insar_normalization"]["projected_vertical_displacement_mm"] is not None

    assert breakdown["ml_engine"]["is_stub"] is True
    assert breakdown["ml_engine"]["status"] == "PENDING_MODEL_INTEGRATION"

    assert breakdown["physics_engine"]["is_stub"] is True
    assert breakdown["physics_engine"]["status"] == "VALIDATION_STUB_ONLY"

    assert breakdown["consensus_engine"]["is_stub"] is True
    assert breakdown["consensus_engine"]["status"] == "PENDING_SCIENTIFIC_SPECIFICATION"

    # Verify Chronology Record generation
    chronicle = data["chronology_record"]
    assert chronicle is not None
    assert "current_hash" in chronicle
    assert len(chronicle["current_hash"]) == 64  # SHA-256 length


def test_analyze_nonexistent_observation(client: TestClient):
    resp = client.post("/api/v1/analysis/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()
