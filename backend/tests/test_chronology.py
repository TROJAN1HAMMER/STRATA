import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from backend.app.services.chronology.hasher import (
    canonical_json_bytes,
    compute_sha256_hash,
    compute_payload_hash,
    compute_chained_record_hash,
)
from backend.app.services.chronology.service import (
    EvidenceChronicleService,
    GENESIS_HASH,
)
from backend.app.db.models import ChronologyRecord


def test_canonical_json_determinism():
    dict1 = {"b": 2, "a": 1, "c": {"y": "hello", "x": 10}}
    dict2 = {"a": 1, "c": {"x": 10, "y": "hello"}, "b": 2}

    bytes1 = canonical_json_bytes(dict1)
    bytes2 = canonical_json_bytes(dict2)

    assert bytes1 == bytes2
    assert compute_payload_hash(dict1) == compute_payload_hash(dict2)
    assert len(compute_payload_hash(dict1)) == 64


def test_hash_chain_creation_and_verification():
    service = EvidenceChronicleService()

    # Construct mock records to simulate chain
    records = []
    prev_hash = GENESIS_HASH

    for i in range(3):
        payload = {
            "record_index": i,
            "observation_id": f"obs_{i}",
            "analysis_result_id": f"res_{i}",
            "timestamp": "2026-01-01T00:00:00Z",
            "data": f"epoch_{i}",
        }
        p_hash = compute_payload_hash(payload)
        c_hash = compute_chained_record_hash(prev_hash, p_hash)

        rec = ChronologyRecord(
            id=f"rec_{i}",
            observation_id=f"obs_{i}",
            analysis_result_id=f"res_{i}",
            record_index=i,
            timestamp=datetime.now(timezone.utc),
            payload=payload,
            payload_hash=p_hash,
            previous_hash=prev_hash,
            current_hash=c_hash,
        )
        records.append(rec)
        prev_hash = c_hash

    # Valid chain should verify
    is_valid, reason = service.verify_chain(records)
    assert is_valid is True
    assert reason is None

    # Tampering test 1: Modify payload content
    records[1].payload = {**records[1].payload, "data": "TAMPERED_CONTENT"}
    is_valid_tampered, reason_tampered = service.verify_chain(records)
    assert is_valid_tampered is False
    assert "tampering detected" in reason_tampered.lower()

    # Restore payload, Tampering test 2: Break hash link
    records[1].payload["data"] = "epoch_1"
    records[2].previous_hash = "f" * 64
    is_valid_broken, reason_broken = service.verify_chain(records)
    assert is_valid_broken is False
    assert "mismatch" in reason_broken.lower()


def test_chronicle_api_verification_endpoint(client: TestClient):
    # Ingest infrastructure & observation
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Chronicle River Bridge", "structure_type": "BRIDGE", "latitude": 42.0, "longitude": 12.0},
    ).json()

    obs1 = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-01-01T00:00:00Z",
            "deformation_mm": -1.0,
            "coherence": 0.85,
        },
    ).json()

    obs2 = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-01-12T00:00:00Z",
            "deformation_mm": -1.5,
            "coherence": 0.82,
        },
    ).json()

    # Analyze both observations to build chronicle chain
    client.post(f"/api/v1/analysis/{obs1['id']}")
    client.post(f"/api/v1/analysis/{obs2['id']}")

    # Call verification endpoint
    verify_resp = client.get("/api/v1/analysis/chronicle/verify")
    assert verify_resp.status_code == 200
    data = verify_resp.json()
    assert data["is_intact"] is True
    assert data["verification_status"] == "VALID"
    assert data["chain_length"] >= 2
