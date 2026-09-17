"""
Comprehensive unit and integration tests for STRATA Phase 6 Chronology Layer.
Validates SHA-256 hash chaining, tamper detection (payload edit, deletion, reordering,
duplicate sequence, previous-hash, timestamp inconsistency), replay reproducibility,
and Phase 6 REST API endpoints.
"""
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from backend.app.db.models import ChronologyRecord
from backend.app.main import app
from backend.app.schemas.consensus import ConsensusAssessment, ConsensusCategory
from backend.app.services.chronology.hasher import (
    canonical_json_bytes,
    compute_chained_record_hash,
    compute_payload_hash,
    compute_sha256_hash,
)
from backend.app.services.chronology.service import (
    EvidenceChronicleService,
    GENESIS_HASH,
)


def make_dummy_assessment(cat: ConsensusCategory = ConsensusCategory.STRUCTURAL, conf: float = 0.85):
    return ConsensusAssessment(
        consensus_class=cat,
        consensus_confidence=conf,
        agreement_score=0.85,
        disagreement_penalty=0.15,
        evidence_quality_score=0.90,
        temporal_persistence_score=0.85,
        ml_contribution={"predicted_class": "STRUCTURAL_MONOTONIC", "confidence": conf},
        physics_contribution={"classification": "STRUCTURALLY_CONSISTENT", "evidence_strength": conf},
        explanation="Controlled consensus assessment.",
        flags=["MODEL_AGREEMENT", "STRONG_MODEL_AGREEMENT"],
        model_versions={"ml": "strata_ml_v0_1_0", "physics": "strata_physics_v0.2.1", "consensus": "strata_consensus_v0.1.0"},
        consensus_engine_version="strata_consensus_v0.1.0",
    )


# ---------------------------------------------------------------------------
# 1. CHAIN INTEGRITY & DETERMINISM
# ---------------------------------------------------------------------------

def test_deterministic_hash_generation():
    p1 = {"record_index": 0, "b": "test", "a": 12.34}
    p2 = {"a": 12.34, "record_index": 0, "b": "test"}

    assert compute_payload_hash(p1) == compute_payload_hash(p2)
    h1 = compute_chained_record_hash(GENESIS_HASH, compute_payload_hash(p1))
    h2 = compute_chained_record_hash(GENESIS_HASH, compute_payload_hash(p2))
    assert h1 == h2


def test_intact_chain_verification():
    service = EvidenceChronicleService()
    records = []
    prev = GENESIS_HASH

    for i in range(4):
        payload = {
            "record_index": i,
            "observation_id": f"obs_{i}",
            "acquisition_timestamp": f"2025-01-{i+1:02d}T00:00:00Z",
            "consensus_category": "STRUCTURAL",
        }
        p_hash = compute_payload_hash(payload)
        c_hash = compute_chained_record_hash(prev, p_hash)
        rec = ChronologyRecord(
            id=f"r_{i}",
            observation_id=f"obs_{i}",
            analysis_result_id=f"res_{i}",
            record_index=i,
            payload=payload,
            payload_hash=p_hash,
            previous_hash=prev,
            current_hash=c_hash,
        )
        records.append(rec)
        prev = c_hash

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is True
    assert error is None


# ---------------------------------------------------------------------------
# 2. TAMPER DETECTION TESTS (A THROUGH F)
# ---------------------------------------------------------------------------

def _build_valid_chain(n: int = 4):
    records = []
    prev = GENESIS_HASH
    for i in range(n):
        payload = {
            "record_index": i,
            "observation_id": f"obs_{i}",
            "acquisition_timestamp": f"2025-01-{i+1:02d}T00:00:00Z",
            "consensus_category": "STRUCTURAL",
            "confidence": 0.85,
        }
        p_hash = compute_payload_hash(payload)
        c_hash = compute_chained_record_hash(prev, p_hash)
        rec = ChronologyRecord(
            id=f"r_{i}",
            observation_id=f"obs_{i}",
            analysis_result_id=f"res_{i}",
            record_index=i,
            payload=payload,
            payload_hash=p_hash,
            previous_hash=prev,
            current_hash=c_hash,
        )
        records.append(rec)
        prev = c_hash
    return records


def test_tamper_detection_a_modified_payload():
    service = EvidenceChronicleService()
    records = _build_valid_chain(4)

    # Tamper with record 2 payload content (e.g. change confidence)
    records[2].payload = {**records[2].payload, "confidence": 0.20}

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "payload tampering detected" in error.lower()


def test_tamper_detection_b_deleted_intermediate_record():
    service = EvidenceChronicleService()
    records = _build_valid_chain(4)

    # Delete record index 2
    del records[2]

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "broken sequence" in error.lower() or "mismatch" in error.lower()


def test_tamper_detection_c_reordered_records():
    service = EvidenceChronicleService()
    records = _build_valid_chain(4)

    # Swap records 1 and 2
    records[1], records[2] = records[2], records[1]

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False


def test_tamper_detection_d_modified_previous_hash():
    service = EvidenceChronicleService()
    records = _build_valid_chain(4)

    # Tamper with previous_hash of record 3
    records[3].previous_hash = "a" * 64

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "hash link mismatch" in error.lower()


def test_tamper_detection_e_duplicate_sequence_number():
    service = EvidenceChronicleService()
    records = _build_valid_chain(4)

    # Assign duplicate record_index to record 2
    records[2].record_index = 1

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "duplicate sequence number" in error.lower()


def test_tamper_detection_f_timestamp_inconsistency():
    service = EvidenceChronicleService()
    # Build chain where record 2 has an earlier timestamp than record 1
    records = []
    prev = GENESIS_HASH
    timestamps = [
        "2025-01-01T00:00:00Z",
        "2025-01-15T00:00:00Z",
        "2025-01-05T00:00:00Z",  # Backwards in time!
    ]
    for i, ts in enumerate(timestamps):
        payload = {
            "record_index": i,
            "observation_id": f"obs_{i}",
            "acquisition_timestamp": ts,
        }
        p_hash = compute_payload_hash(payload)
        c_hash = compute_chained_record_hash(prev, p_hash)
        rec = ChronologyRecord(
            id=f"r_{i}",
            observation_id=f"obs_{i}",
            analysis_result_id=f"res_{i}",
            record_index=i,
            payload=payload,
            payload_hash=p_hash,
            previous_hash=prev,
            current_hash=c_hash,
        )
        records.append(rec)
        prev = c_hash

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "timestamp inconsistency" in error.lower()


# ---------------------------------------------------------------------------
# 3. REPLAY & REPRODUCIBILITY TESTS
# ---------------------------------------------------------------------------

def test_replay_analytical_reproducibility():
    """Validates that repeating analysis on the same observation inputs yields identical hashes."""
    assessment_1 = make_dummy_assessment()
    assessment_2 = make_dummy_assessment()

    p1 = {
        "record_index": 0,
        "observation_id": "obs_1",
        "consensus_category": assessment_1.consensus_class.value,
        "consensus_confidence": assessment_1.consensus_confidence,
        "model_versions": assessment_1.model_versions,
    }
    p2 = {
        "record_index": 0,
        "observation_id": "obs_1",
        "consensus_category": assessment_2.consensus_class.value,
        "consensus_confidence": assessment_2.consensus_confidence,
        "model_versions": assessment_2.model_versions,
    }

    h1 = compute_chained_record_hash(GENESIS_HASH, compute_payload_hash(p1))
    h2 = compute_chained_record_hash(GENESIS_HASH, compute_payload_hash(p2))

    assert h1 == h2


# ---------------------------------------------------------------------------
# 4. REST API INTEGRATION TESTS
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    return TestClient(app)


def test_api_chronology_and_temporal_summary_endpoints(client):
    # 1. Create infrastructure
    infra_resp = client.post(
        "/api/v1/infrastructure",
        json={
            "name": "Phase 6 Viaduct",
            "structure_type": "BRIDGE",
            "latitude": 45.123,
            "longitude": 9.456,
        },
    )
    assert infra_resp.status_code == 201
    infra_id = infra_resp.json()["id"]

    # 2. Add 4 multi-epoch observations
    obs_ids = []
    for i in range(1, 5):
        obs_resp = client.post(
            "/api/v1/observations",
            json={
                "infrastructure_id": infra_id,
                "acquisition_timestamp": f"2025-01-{i*6:02d}T00:00:00Z",
                "deformation_mm": float(i * -1.5),
                "coherence": 0.88,
                "phase_quality": 0.82,
                "incidence_angle": 35.0,
            },
        )
        assert obs_resp.status_code == 201
        obs_ids.append(obs_resp.json()["id"])

    # 3. Call POST /api/v1/analysis/chronology/{observation_id} for the observations
    for obs_id in obs_ids:
        chrono_post = client.post(f"/api/v1/analysis/chronology/{obs_id}")
        assert chrono_post.status_code == 201
        assert "current_hash" in chrono_post.json()

    # 4. Call GET /api/v1/infrastructure/{id}/chronology
    chrono_get = client.get(f"/api/v1/infrastructure/{infra_id}/chronology")
    assert chrono_get.status_code == 200
    records = chrono_get.json()
    assert len(records) == 4

    # 5. Call GET /api/v1/infrastructure/{id}/chronology/verify
    verify_resp = client.get(f"/api/v1/infrastructure/{infra_id}/chronology/verify")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["is_intact"] is True
    assert v_data["verification_status"] == "VALID"
    assert v_data["chain_length"] == 4

    # 6. Call GET /api/v1/infrastructure/{id}/temporal-summary
    summary_resp = client.get(f"/api/v1/infrastructure/{infra_id}/temporal-summary")
    assert summary_resp.status_code == 200
    summary = summary_resp.json()
    assert summary["infrastructure_id"] == infra_id
    assert summary["observation_count"] == 4
    assert "temporal_status" in summary
    assert "confidence_trajectory" in summary
    assert "persistence_score" in summary
    assert "explanation" in summary
