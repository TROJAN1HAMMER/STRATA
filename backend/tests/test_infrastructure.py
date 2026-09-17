import pytest
from fastapi.testclient import TestClient


def test_create_infrastructure_success(client: TestClient):
    payload = {
        "name": "Golden Gate Test Sector",
        "structure_type": "BRIDGE",
        "latitude": 37.8199,
        "longitude": -122.4783,
        "description": "Synthetic suspension bridge reference point",
    }
    response = client.post("/api/v1/infrastructure", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["structure_type"] == "BRIDGE"
    assert data["latitude"] == pytest.approx(37.8199)
    assert data["longitude"] == pytest.approx(-122.4783)
    assert "id" in data
    assert "created_at" in data


@pytest.mark.parametrize(
    "invalid_payload,expected_error_field",
    [
        (
            {"name": "Invalid Lat", "structure_type": "DAM", "latitude": 95.0, "longitude": 10.0},
            "latitude",
        ),
        (
            {"name": "Invalid Lat Neg", "structure_type": "DAM", "latitude": -91.0, "longitude": 10.0},
            "latitude",
        ),
        (
            {"name": "Invalid Lon", "structure_type": "DAM", "latitude": 45.0, "longitude": 190.0},
            "longitude",
        ),
        (
            {"name": "", "structure_type": "DAM", "latitude": 45.0, "longitude": 10.0},
            "name",
        ),
    ],
)
def test_create_infrastructure_validation_error(client: TestClient, invalid_payload, expected_error_field):
    response = client.post("/api/v1/infrastructure", json=invalid_payload)
    assert response.status_code == 422
    errors = response.json().get("detail", [])
    assert any(expected_error_field in str(err) for err in errors)


def test_list_infrastructure_filtering(client: TestClient):
    client.post(
        "/api/v1/infrastructure",
        json={"name": "Dam Alpha", "structure_type": "DAM", "latitude": 10.0, "longitude": 20.0},
    )
    client.post(
        "/api/v1/infrastructure",
        json={"name": "Bridge Beta", "structure_type": "BRIDGE", "latitude": 12.0, "longitude": 22.0},
    )

    all_resp = client.get("/api/v1/infrastructure")
    assert all_resp.status_code == 200
    assert len(all_resp.json()) >= 2

    dam_resp = client.get("/api/v1/infrastructure?structure_type=DAM")
    assert dam_resp.status_code == 200
    dams = dam_resp.json()
    assert all(d["structure_type"] == "DAM" for d in dams)


def test_get_infrastructure_by_id(client: TestClient):
    create_resp = client.post(
        "/api/v1/infrastructure",
        json={"name": "Retaining Wall Test", "structure_type": "RETAINING_WALL", "latitude": 15.0, "longitude": 25.0},
    )
    infra_id = create_resp.json()["id"]

    get_resp = client.get(f"/api/v1/infrastructure/{infra_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == infra_id

    # Non-existent ID returns 404
    missing_resp = client.get("/api/v1/infrastructure/00000000-0000-0000-0000-000000000000")
    assert missing_resp.status_code == 404
