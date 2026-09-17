"""
STRATA — Phase 9: System Hardening & End-to-End Integration Test Suite.

Validates:
1. End-to-end multi-engine execution pipeline (Input Validation -> Normalization -> ML ->
   Physics -> Consensus -> Temporal -> Risk Characterization -> Chronology).
2. Idempotency & replay safety (no duplicate chronology records or analysis records).
3. Transaction atomicity & rollback upon mid-pipeline failure.
4. Input validation & numerical sanity limits (NaN, Inf, coherence, angles, extreme bounds).
5. Incomplete infrastructure metadata resilience (missing baseline, materials, zones).
6. Missing satellite geometry resilience.
7. Scenarios A through G end-to-end behavior.
8. Chronology tamper detection (all 10 tamper vectors).
9. REST API endpoints (POST /pipeline/{id}, GET /pipeline/{id}, error codes).
10. Performance latency baseline.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.versions import (
    PIPELINE_VERSION,
    SYSTEM_VERSIONS,
)
from backend.app.db.models import (
    AnalysisResult,
    ChronologyRecord,
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    Observation,
    RiskCharacterization,
    RiskCharacterizationState,
    StructureType,
)
from backend.app.schemas.consensus import ConsensusCategory
from backend.app.schemas.risk import HistoricalBaseline
from backend.app.services.chronology.hasher import (
    compute_chained_record_hash,
    compute_payload_hash,
)
from backend.app.services.chronology.service import (
    EvidenceChronicleService,
    GENESIS_HASH,
)
from backend.app.services.pipeline import (
    ProcessingStatus,
    STRATAAnalysisPipeline,
    PipelineResult,
    PipelineExecutionError,
)


def _setup_test_infrastructure(
    db: Session,
    infra_id: str = "infra_hardening_1",
    name: str = "Metropolitan Suspension Bridge",
    structure_type: StructureType = StructureType.BRIDGE,
    material_type: MaterialType = MaterialType.STEEL,
    criticality: CriticalityLevel = CriticalityLevel.HIGH,
    baseline_trend: float = 0.0,
    baseline_noise: float = 1.0,
) -> Infrastructure:
    inf = db.query(Infrastructure).filter(Infrastructure.id == infra_id).first()
    if inf:
        return inf

    inf = Infrastructure(
        id=infra_id,
        name=name,
        structure_type=structure_type,
        material=material_type,
        criticality=criticality,
        latitude=40.7128,
        longitude=-74.0060,
        historical_baseline={
            "baseline_mean_mm": baseline_trend,
            "baseline_std_mm": baseline_noise,
            "baseline_period_days": 365.0,
        },
        critical_zones=[
            {
                "zone_id": "pier_north",
                "zone_name": "North Support Pier",
                "zone_type": "FOUNDATION",
                "importance_weight": 1.25,
            }
        ],
    )
    db.add(inf)
    db.commit()
    db.refresh(inf)
    return inf


def _seed_observation_sequence(
    db: Session,
    infra_id: str,
    displacements: list,
    interval_days: int = 14,
    start_date: datetime = None,
    coherence: float = 0.85,
    incidence_angle: float = 35.0,
) -> list:
    if start_date is None:
        start_date = datetime(2025, 1, 1, tzinfo=timezone.utc)

    observations = []
    for idx, disp in enumerate(displacements):
        t = start_date + timedelta(days=idx * interval_days)
        obs_id = f"obs_{infra_id}_{idx:03d}"
        existing = db.query(Observation).filter(Observation.id == obs_id).first()
        if existing:
            observations.append(existing)
            continue

        obs = Observation(
            id=obs_id,
            infrastructure_id=infra_id,
            acquisition_timestamp=t,
            deformation_mm=float(disp),
            los_displacement_mm=float(disp),
            velocity_mm_per_year=0.0,
            coherence=coherence,
            phase_quality=0.90,
            incidence_angle=incidence_angle,
            source="SENTINEL_1",
        )
        db.add(obs)
        observations.append(obs)

    db.commit()
    for o in observations:
        db.refresh(o)
    return observations


# ==============================================================================
# 1. END-TO-END PIPELINE EXECUTION
# ==============================================================================

def test_end_to_end_pipeline_success(db_session: Session):
    """Executes full multi-stage pipeline from observation to chronology append."""
    inf = _setup_test_infrastructure(db_session, "infra_e2e_1")
    displacements = [0.1, -0.2, 0.0, 0.2, -0.1, 0.0, 0.1, -0.1]
    observations = _seed_observation_sequence(db_session, inf.id, displacements)
    target_obs = observations[-1]

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, target_obs.id)

    # Verification: Result Structure
    assert isinstance(result, PipelineResult)
    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.observation_id == target_obs.id
    assert result.infrastructure_id == inf.id
    assert result.idempotent_replay is False

    # Timings
    assert result.stage_timings.total_ms > 0
    assert result.stage_timings.validation_ms >= 0
    assert result.stage_timings.ml_ms >= 0
    assert result.stage_timings.physics_ms >= 0
    assert result.stage_timings.consensus_ms >= 0
    assert result.stage_timings.temporal_ms >= 0
    assert result.stage_timings.characterization_ms >= 0
    assert result.stage_timings.chronology_ms >= 0

    # Intermediate Engine Artifacts Populated
    assert result.normalized_observation is not None
    assert result.normalized_observation.normalized_deformation_mm is not None
    assert result.ml_result is not None
    assert result.physics_evidence is not None
    assert result.consensus_assessment is not None
    assert result.temporal_summary is not None
    assert result.risk_characterization is not None
    assert result.chronology_record is not None

    # Version Audit Registry Recorded
    assert result.system_versions["pipeline_version"] == PIPELINE_VERSION
    assert result.system_versions["ml_model_version"] == SYSTEM_VERSIONS["ml_model_version"]

    # Database Records Persisted
    db_analysis = db_session.query(AnalysisResult).filter(AnalysisResult.observation_id == target_obs.id).first()
    assert db_analysis is not None
    assert db_analysis.execution_metadata["pipeline_version"] == PIPELINE_VERSION

    db_chronology = db_session.query(ChronologyRecord).filter(ChronologyRecord.observation_id == target_obs.id).first()
    assert db_chronology is not None
    assert len(db_chronology.current_hash) == 64


# ==============================================================================
# 2. IDEMPOTENCY & REPLAY REPRODUCIBILITY
# ==============================================================================

def test_pipeline_idempotency_and_no_duplicate_records(db_session: Session):
    """Re-executing pipeline on same observation must not duplicate DB records."""
    inf = _setup_test_infrastructure(db_session, "infra_idempotent_1")
    observations = _seed_observation_sequence(db_session, inf.id, [0.0, 0.5, 0.2, 0.4])
    target_obs = observations[-1]

    pipeline = STRATAAnalysisPipeline()

    # First Execution
    res1 = pipeline.execute_for_observation(db_session, target_obs.id, force_recompute=False)
    assert res1.idempotent_replay is False

    analysis_count_1 = db_session.query(AnalysisResult).filter(AnalysisResult.observation_id == target_obs.id).count()
    chronology_count_1 = db_session.query(ChronologyRecord).filter(ChronologyRecord.observation_id == target_obs.id).count()
    assert analysis_count_1 == 1
    assert chronology_count_1 == 1

    # Second Execution (idempotent replay)
    res2 = pipeline.execute_for_observation(db_session, target_obs.id, force_recompute=False)
    assert res2.idempotent_replay is True

    analysis_count_2 = db_session.query(AnalysisResult).filter(AnalysisResult.observation_id == target_obs.id).count()
    chronology_count_2 = db_session.query(ChronologyRecord).filter(ChronologyRecord.observation_id == target_obs.id).count()

    # Zero Duplication
    assert analysis_count_2 == 1
    assert chronology_count_2 == 1

    # Hash Match
    assert res1.chronology_record.current_hash == res2.chronology_record.current_hash

    # Third Execution with force_recompute=True
    res3 = pipeline.execute_for_observation(db_session, target_obs.id, force_recompute=True)
    assert res3.idempotent_replay is False
    assert res3.processing_status == ProcessingStatus.COMPLETED


# ==============================================================================
# 3. TRANSACTION ATOMICITY & ROLLBACK ON ERROR
# ==============================================================================

def test_pipeline_transaction_rollback_on_failure(db_session: Session):
    """If any analytical stage fails, no partial records are committed."""
    inf = _setup_test_infrastructure(db_session, "infra_rollback_1")
    observations = _seed_observation_sequence(db_session, inf.id, [0.0, 1.0, 2.0])
    target_obs_id = observations[-1].id

    pipeline = STRATAAnalysisPipeline()

    # Mock stage 8 (risk engine) to raise an unexpected exception
    with patch.object(
        pipeline.risk_engine,
        "evaluate_infrastructure",
        side_effect=RuntimeError("Simulated unhandled stage error"),
    ):
        with pytest.raises(PipelineExecutionError) as exc_info:
            pipeline.execute_for_observation(db_session, target_obs_id)

        assert exc_info.value.failed_stage in [
            ProcessingStatus.CHARACTERIZED,
            ProcessingStatus.TEMPORAL_ANALYZED,
        ]

    # Assert that rollback occurred: no analysis or chronology record committed
    analysis_in_db = db_session.query(AnalysisResult).filter(AnalysisResult.observation_id == target_obs_id).first()
    chronology_in_db = db_session.query(ChronologyRecord).filter(ChronologyRecord.observation_id == target_obs_id).first()

    assert analysis_in_db is None
    assert chronology_in_db is None


# ==============================================================================
# 4. INPUT VALIDATION & BOUNDS ENFORCEMENT
# ==============================================================================

def test_pipeline_rejects_nan_and_inf(db_session: Session):
    """Rejects NaN or Infinite displacement values."""
    inf = _setup_test_infrastructure(db_session, "infra_bounds_1")
    pipeline = STRATAAnalysisPipeline()

    # Direct validation test for in-memory NaN and Inf
    in_memory_nan = Observation(
        id="obs_mem_nan",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=float("nan"),
        coherence=0.8,
        incidence_angle=35.0,
    )
    with pytest.raises(PipelineExecutionError) as exc_mem_nan:
        pipeline._validate_numerical_integrity(in_memory_nan)
    assert exc_mem_nan.value.failed_stage == ProcessingStatus.VALIDATED
    assert "nan" in exc_mem_nan.value.message.lower()

    in_memory_inf = Observation(
        id="obs_mem_inf",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=float("inf"),
        coherence=0.8,
        incidence_angle=35.0,
    )
    with pytest.raises(PipelineExecutionError) as exc_mem_inf:
        pipeline._validate_numerical_integrity(in_memory_inf)
    assert exc_mem_inf.value.failed_stage == ProcessingStatus.VALIDATED
    assert "inf" in exc_mem_inf.value.message.lower()

    # Pipeline execution test: observation missing displacement entirely (or converted to NULL)
    obs_null = Observation(
        id="obs_null_001",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=None,
        los_displacement_mm=None,
        coherence=0.8,
        incidence_angle=35.0,
    )
    db_session.add(obs_null)
    db_session.commit()

    with pytest.raises(PipelineExecutionError) as exc_null:
        pipeline.execute_for_observation(db_session, obs_null.id)
    assert exc_null.value.failed_stage == ProcessingStatus.VALIDATED
    assert "missing displacement" in exc_null.value.message.lower()


def test_pipeline_rejects_impossible_coherence(db_session: Session):
    """Rejects coherence values outside [0.0, 1.0]."""
    inf = _setup_test_infrastructure(db_session, "infra_coherence_1")
    pipeline = STRATAAnalysisPipeline()

    obs_bad = Observation(
        id="obs_bad_coh",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=1.0,
        coherence=1.45,
        incidence_angle=35.0,
    )
    db_session.add(obs_bad)
    db_session.commit()

    with pytest.raises(PipelineExecutionError) as exc:
        pipeline.execute_for_observation(db_session, obs_bad.id)
    assert exc.value.failed_stage == ProcessingStatus.VALIDATED
    assert "coherence" in exc.value.message.lower()


def test_pipeline_rejects_impossible_incidence_angles(db_session: Session):
    """Rejects incidence angles outside (0, 90)."""
    inf = _setup_test_infrastructure(db_session, "infra_angle_1")
    pipeline = STRATAAnalysisPipeline()

    obs_bad = Observation(
        id="obs_bad_ang",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=1.0,
        coherence=0.8,
        incidence_angle=95.0,
    )
    db_session.add(obs_bad)
    db_session.commit()

    with pytest.raises(PipelineExecutionError) as exc:
        pipeline.execute_for_observation(db_session, obs_bad.id)
    assert exc.value.failed_stage == ProcessingStatus.VALIDATED
    assert "incidence angle" in exc.value.message.lower()


def test_pipeline_rejects_unphysical_displacement_ceiling(db_session: Session):
    """Rejects displacement beyond physical sanity limit (e.g. 100 meters)."""
    inf = _setup_test_infrastructure(db_session, "infra_extreme_1")
    pipeline = STRATAAnalysisPipeline()

    obs_bad = Observation(
        id="obs_bad_extreme",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=99999.0,
        coherence=0.8,
        incidence_angle=35.0,
    )
    db_session.add(obs_bad)
    db_session.commit()

    with pytest.raises(PipelineExecutionError) as exc:
        pipeline.execute_for_observation(db_session, obs_bad.id)
    assert exc.value.failed_stage == ProcessingStatus.VALIDATED
    assert "sanity ceiling" in exc.value.message.lower()


# ==============================================================================
# 5. INCOMPLETE INFRASTRUCTURE METADATA & MISSING GEOMETRY
# ==============================================================================

def test_pipeline_handles_incomplete_infrastructure_metadata(db_session: Session):
    """Pipeline operates safely when infrastructure lacks baseline, material, or critical zones."""
    inf = Infrastructure(
        id="infra_minimal",
        name="Uncharacterized Footbridge",
        structure_type=StructureType.BRIDGE,
        latitude=40.0,
        longitude=-74.0,
        historical_baseline=None,
        critical_zones=[],
        material=MaterialType.UNKNOWN,
        criticality=CriticalityLevel.UNKNOWN,
    )
    db_session.add(inf)
    db_session.commit()

    obs = Observation(
        id="obs_minimal_01",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=0.2,
        coherence=0.85,
        incidence_angle=35.0,
    )
    db_session.add(obs)
    db_session.commit()

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, obs.id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.risk_characterization is not None
    # Warnings or fallback states are generated safely
    assert result.risk_characterization.characterization_state is not None


def test_pipeline_handles_missing_satellite_geometry_safely(db_session: Session):
    """Pipeline falls back to nominal defaults without hallucinating satellite trajectory."""
    inf = _setup_test_infrastructure(db_session, "infra_missing_geom")
    obs = Observation(
        id="obs_no_geom_01",
        infrastructure_id=inf.id,
        acquisition_timestamp=datetime.now(timezone.utc),
        deformation_mm=-2.5,
        coherence=0.82,
        incidence_angle=None,
    )
    db_session.add(obs)
    db_session.commit()

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, obs.id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.normalized_observation.incidence_angle is None  # Does NOT invent satellite geometry


# ==============================================================================
# 6. SCENARIOS A THROUGH G END-TO-END VERIFICATION
# ==============================================================================

def test_scenario_a_stable_infrastructure_end_to_end(db_session: Session):
    """Scenario A: Low-amplitude noise around 0 mm -> BASELINE / NOMINAL."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_a")
    disps = [0.1, -0.2, 0.3, -0.1, 0.0, 0.2, -0.2, 0.1, 0.0, -0.1]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.risk_characterization.characterization_state == RiskCharacterizationState.BASELINE
    assert result.risk_characterization.prototype_risk_index <= 35.0


def test_scenario_b_persistent_linear_deformation_end_to_end(db_session: Session):
    """Scenario B: Monotonically increasing settlement -> MONITOR or ELEVATED_ATTENTION."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_b")
    disps = [-1.0, -3.2, -5.5, -7.8, -10.1, -12.4, -14.6, -17.0]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.risk_characterization.characterization_state in [
        RiskCharacterizationState.MONITOR,
        RiskCharacterizationState.ELEVATED_ATTENTION,
    ]
    assert result.temporal_summary.temporal_status is not None


def test_scenario_c_seasonal_environmental_end_to_end(db_session: Session):
    """Scenario C: Sinusoidal oscillation -> ENVIRONMENTAL_PATTERN."""
    import math
    inf = _setup_test_infrastructure(db_session, "infra_scen_c")
    disps = [5.0 * math.sin(2 * math.pi * i / 8.0) for i in range(12)]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    # Should identify cyclical environmental modulation or baseline
    assert result.risk_characterization.characterization_state in [
        RiskCharacterizationState.ENVIRONMENTAL_PATTERN,
        RiskCharacterizationState.BASELINE,
    ]


def test_scenario_d_atmospheric_contamination_end_to_end(db_session: Session):
    """Scenario D: Isolated transient spike -> flagged, no false runaway risk."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_d")
    disps = [0.1, 0.0, 0.2, 14.5, 0.1, -0.1, 0.2]  # single spike at index 3
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    # Last observation is back to stable baseline
    assert result.risk_characterization.characterization_state in [
        RiskCharacterizationState.BASELINE,
        RiskCharacterizationState.MONITOR,
        RiskCharacterizationState.INSUFFICIENT_EVIDENCE,
    ]


def test_scenario_e_low_quality_decorrelation_end_to_end(db_session: Session):
    """Scenario E: Very low coherence -> INSUFFICIENT_EVIDENCE / decorrelation flags."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_e")
    disps = [1.0, 3.0, 2.0, 4.0]
    observations = _seed_observation_sequence(db_session, inf.id, disps, coherence=0.15)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.risk_characterization.characterization_state in [
        RiskCharacterizationState.INSUFFICIENT_EVIDENCE,
        RiskCharacterizationState.MONITOR,
    ]


def test_scenario_f_cross_model_conflict_end_to_end(db_session: Session):
    """Scenario F: Models disagree -> CONFLICTED state handled without crashing."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_f")
    disps = [0.0, 1.5, 0.2, 1.8, 0.1]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.consensus_assessment is not None
    assert result.consensus_assessment.agreement_score >= 0.0


def test_scenario_g_ground_subsidence_end_to_end(db_session: Session):
    """Scenario G: Regional gradual settlement -> characterizes appropriately."""
    inf = _setup_test_infrastructure(db_session, "infra_scen_g")
    disps = [-2.0, -4.0, -6.0, -8.0, -10.0, -12.0]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.risk_characterization.prototype_risk_index > 0.3


# ==============================================================================
# 7. CHRONOLOGY TAMPER DETECTION (ALL 10 SCENARIOS)
# ==============================================================================

def _build_valid_chronology_chain(n: int = 5):
    records = []
    prev = GENESIS_HASH
    for i in range(n):
        payload = {
            "record_index": i,
            "observation_id": f"obs_{i:03d}",
            "acquisition_timestamp": f"2025-01-{i+1:02d}T00:00:00Z",
            "displacement_mm": round(i * 1.5, 2),
            "consensus_category": "STRUCTURAL",
            "model_version": "strata_pipeline_v1.0.0",
        }
        p_hash = compute_payload_hash(payload)
        c_hash = compute_chained_record_hash(prev, p_hash)
        rec = ChronologyRecord(
            id=f"rec_{i:03d}",
            observation_id=f"obs_{i:03d}",
            analysis_result_id=f"res_{i:03d}",
            record_index=i,
            payload=payload,
            payload_hash=p_hash,
            previous_hash=prev,
            current_hash=c_hash,
        )
        records.append(rec)
        prev = c_hash
    return records


def test_tamper_scenario_1_payload_tampering():
    """Scenario 1: Modified displacement value inside payload is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    records[2].payload = {**records[2].payload, "displacement_mm": 999.0}

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "payload tampering" in error.lower()


def test_tamper_scenario_2_current_hash_mismatch():
    """Scenario 2: Tampered current_hash is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    records[3].current_hash = "deadbeef" * 8

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "hash link mismatch" in error.lower() or "current hash" in error.lower()


def test_tamper_scenario_3_previous_hash_mismatch():
    """Scenario 3: Tampered previous_hash link is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    records[3].previous_hash = "00000000" * 8

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "hash link mismatch" in error.lower()


def test_tamper_scenario_4_record_deletion():
    """Scenario 4: Deleted intermediate record causing sequence gap is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    del records[2]

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "broken sequence" in error.lower() or "mismatch" in error.lower()


def test_tamper_scenario_5_record_reordering():
    """Scenario 5: Swapped adjacent records are detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    records[1], records[2] = records[2], records[1]

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False


def test_tamper_scenario_6_duplicate_sequence_numbers():
    """Scenario 6: Duplicate record_index is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(5)
    records[3].record_index = 2

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "duplicate sequence number" in error.lower()


def test_tamper_scenario_7_non_monotonic_timestamps():
    """Scenario 7: Inverted time sequence is detected."""
    service = EvidenceChronicleService()
    records = []
    prev = GENESIS_HASH
    timestamps = [
        "2025-01-01T00:00:00Z",
        "2025-01-10T00:00:00Z",
        "2025-01-05T00:00:00Z",  # Backwards
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


def test_tamper_scenario_8_inserted_fake_record():
    """Scenario 8: Foreign record inserted without updating hash links is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(4)

    fake_payload = {"record_index": 2, "observation_id": "fake_obs", "acquisition_timestamp": "2025-01-02T12:00:00Z"}
    p_hash = compute_payload_hash(fake_payload)
    c_hash = compute_chained_record_hash(records[1].current_hash, p_hash)
    fake_rec = ChronologyRecord(
        id="fake_rec",
        observation_id="fake_obs",
        analysis_result_id="fake_res",
        record_index=2,
        payload=fake_payload,
        payload_hash=p_hash,
        previous_hash=records[1].current_hash,
        current_hash=c_hash,
    )
    records.insert(2, fake_rec)

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False


def test_tamper_scenario_9_modified_model_version_in_payload():
    """Scenario 9: Retroactively changed model version in payload is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(4)
    records[1].payload = {**records[1].payload, "model_version": "strata_ml_v9.9.9"}

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "payload tampering" in error.lower()


def test_tamper_scenario_10_modified_analysis_result_in_payload():
    """Scenario 10: Retroactively changed consensus classification in payload is detected."""
    service = EvidenceChronicleService()
    records = _build_valid_chronology_chain(4)
    records[1].payload = {**records[1].payload, "consensus_category": "STABLE"}

    is_valid, error = service.verify_chain_enhanced(records)
    assert is_valid is False
    assert "payload tampering" in error.lower()


# ==============================================================================
# 8. REST API INTEGRATION TESTS
# ==============================================================================

def test_api_pipeline_execution_and_retrieval(client: TestClient):
    """Tests POST /api/v1/analysis/pipeline/{id} and GET /api/v1/analysis/pipeline/{id}."""
    infra = client.post(
        "/api/v1/infrastructure",
        json={"name": "Harbor Crane Base", "structure_type": "BRIDGE", "latitude": 40.5, "longitude": -74.0},
    ).json()

    obs = client.post(
        "/api/v1/observations",
        json={
            "infrastructure_id": infra["id"],
            "acquisition_timestamp": "2026-04-01T00:00:00Z",
            "deformation_mm": -3.5,
            "velocity_mm_per_year": -12.0,
            "coherence": 0.85,
            "phase_quality": 0.90,
            "incidence_angle": 35.0,
            "los_displacement_mm": -3.5,
            "source": "SENTINEL_1",
        },
    ).json()

    # 1. Execute Pipeline
    post_resp = client.post(f"/api/v1/analysis/pipeline/{obs['id']}")
    assert post_resp.status_code == 201
    post_data = post_resp.json()
    assert post_data["processing_status"] == "COMPLETED"
    assert post_data["idempotent_replay"] is False
    assert "stage_timings" in post_data

    # 2. Re-Execute Pipeline (Idempotent)
    post_re_resp = client.post(f"/api/v1/analysis/pipeline/{obs['id']}")
    assert post_re_resp.status_code == 201
    assert post_re_resp.json()["idempotent_replay"] is True

    # 3. Retrieve Pipeline Result
    get_resp = client.get(f"/api/v1/analysis/pipeline/{obs['id']}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["observation_id"] == obs["id"]
    assert get_data["chronology_record"]["current_hash"] == post_data["chronology_record"]["current_hash"]


def test_api_pipeline_nonexistent_observation(client: TestClient):
    """POST /api/v1/analysis/pipeline/{invalid_id} returns 404."""
    resp = client.post("/api/v1/analysis/pipeline/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ==============================================================================
# 9. PERFORMANCE LATENCY BASELINE CHECK
# ==============================================================================

def test_pipeline_execution_latency_baseline(db_session: Session):
    """Single observation pipeline execution completes well under 1500 ms."""
    inf = _setup_test_infrastructure(db_session, "infra_perf_1")
    disps = [0.1, -0.2, 0.3, -0.1, 0.0]
    observations = _seed_observation_sequence(db_session, inf.id, disps)

    pipeline = STRATAAnalysisPipeline()
    result = pipeline.execute_for_observation(db_session, observations[-1].id)

    assert result.processing_status == ProcessingStatus.COMPLETED
    assert result.stage_timings.total_ms < 1500.0, f"Total execution took {result.stage_timings.total_ms} ms, expected < 1500 ms"
