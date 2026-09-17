from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient


def test_submit_observation_success(client: TestClient):
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Viaduct 7", "structure_type": "BRIDGE", "latitude": 44.1, "longitude": 6.8},
    ).json()

    obs_payload = {
        "infrastructure_id": infra["id"],
        "acquisition_timestamp": "2026-03-01T10:00:00Z",
        "deformation_mm": -3.2,
        "velocity_mm_per_year": -8.5,
        "coherence": 0.81,
        "phase_quality": 0.92,
        "incidence_angle": 39.4,
        "los_displacement_mm": -2.47,
        "atmospheric_indicator": "STABLE",
        "source": "SENTINEL_1",
        "metadata": {"polarization": "VV", "orbit": 112},
    }

    response = client.post("/api/v1/observations", json=obs_payload)
    assert response.status_code == 201
    data = response.json()
    assert data["infrastructure_id"] == infra["id"]
    assert data["coherence"] == pytest.approx(0.81)
    assert data["incidence_angle"] == pytest.approx(39.4)
    assert "id" in data


def test_submit_observation_invalid_coherence(client: TestClient):
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Dam Test", "structure_type": "DAM", "latitude": 30.0, "longitude": 40.0},
    ).json()

    # Coherence > 1.0 is physically impossible
    response_high = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-03-01T10:00:00Z",
            "coherence": 1.45,
        },
    )
    assert response_high.status_code == 422

    # Coherence < 0.0 is physically impossible
    response_neg = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-03-01T10:00:00Z",
            "coherence": -0.1,
        },
    )
    assert response_neg.status_code == 422


def test_submit_observation_invalid_incidence_angle(client: TestClient):
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Dam Test Angle", "structure_type": "DAM", "latitude": 30.0, "longitude": 40.0},
    ).json()

    # Incidence angle > 90°
    response = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-03-01T10:00:00Z",
            "incidence_angle": 95.0,
        },
    )
    assert response.status_code == 422


def test_submit_observation_nonexistent_infrastructure(client: TestClient):
    response = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": "00000000-0000-0000-0000-000000000000",
            "acquisition_timestamp": "2026-03-01T10:00:00Z",
            "coherence": 0.8,
        },
    )
    assert response.status_code == 404
    assert "not exist" in response.json()["detail"]


def test_observation_chronological_ordering(client: TestClient):
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Chronology Check Dam", "structure_type": "DAM", "latitude": 25.0, "longitude": 35.0},
    ).json()

    # Ingest timestamps in arbitrary (shuffled) order
    timestamps = [
        "2026-03-15T00:00:00Z",
        "2026-01-05T00:00:00Z",
        "2026-02-20T00:00:00Z",
        "2026-01-25T00:00:00Z",
    ]

    for ts in timestamps:
        client.post(
            "/api/v1/observations",
            json={
                "infrastructure_id": infra["id"],
                "acquisition_timestamp": ts,
                "deformation_mm": -1.0,
                "coherence": 0.8,
            },
        )

    # Retrieve history
    history_resp = client.get(f"/api/v1/infrastructure/{infra['id']}/observations")
    assert history_resp.status_code == 200
    items = history_resp.json()
    assert len(items) == 4

    # Verify chronological ascending order
    retrieved_timestamps = [item["acquisition_timestamp"] for item in items]
    expected_sorted = sorted(retrieved_timestamps)
    assert retrieved_timestamps == expected_sorted


def test_synthetic_benchmark_fixture_ingestion(client: TestClient, synthetic_benchmark_data: dict):
    # Ingest synthetic benchmark dataset
    infra_data = synthetic_benchmark_data["infrastructure"]
    infra = client.post("/api/v1/infrastructure", json=infra_data).json()

    for obs in synthetic_benchmark_data["observations"]:
        obs_payload = dict(obs)
        obs_payload["infrastructure_id"] = infra["id"]
        res = client.post("/api/v1/observations", json=obs_payload)
        assert res.status_code == 201

    history = client.get(f"/api/v1/infrastructure/{infra['id']}/observations").json()
    assert len(history) == len(synthetic_benchmark_data["observations"])
