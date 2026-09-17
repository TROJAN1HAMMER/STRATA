"""
STRATA — Phase 8: Real-World InSAR Validation Test Suite.
Validates the complete real-data adapter, normalization, evidence hierarchy,
firewall isolation, and end-to-end behavior across all 14 mandatory areas:

1. Real-data adapter parsing
2. Unit conversion
3. Timestamp normalization
4. Missing observations handling
5. Irregular acquisition intervals
6. Missing geometry handling (no invented geometry)
7. Missing coherence / quality handling
8. LOS vs Vertical representation
9. Leakage prevention firewall
10. Deterministic replay
11. Threshold audit registry
12. End-to-end real-data pipeline execution
13. External reference isolation
14. Characterization with incomplete infrastructure metadata
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest

from backend.app.db.models import (
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    RiskCharacterizationState,
    StructureType,
)
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.risk import ExpectedDeformationBehavior
from backend.app.schemas.temporal import TemporalStatus
from backend.app.services.consensus import ConsensusEngine
from backend.app.services.ml.classifier import MLDeformationClassifier
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.real_data import (
    DisplacementType,
    ExternalDatasetMetadata,
    ExternalReference,
    FailureMode,
    ProvenanceStatus,
    RawObservationRecord,
    RealDataIngestionService,
    ReferenceStrength,
    ReferenceType,
    ThresholdAction,
    ThresholdOriginType,
    ThresholdRecord,
    convert_acceleration_to_mm_per_year2,
    convert_displacement_to_mm,
    convert_velocity_to_mm_per_year,
    get_formal_phase7_index_disclaimer,
    get_prototype_threshold_registry,
    get_provenance_registry,
    normalize_coherence,
    normalize_timestamp,
    project_los_to_vertical,
    verify_no_leakage,
)
from backend.app.services.risk import InfrastructureRiskCharacterizationEngine
from backend.app.services.temporal import TemporalEvidenceEngine

REAL_DATA_DIR = Path("data/real")


# ==============================================================================
# 1. Real-Data Adapter Parsing
# ==============================================================================
def test_real_data_adapter_parsing():
    """Verifies that the adapter loads and parses all 5 real datasets with complete metadata."""
    datasets = [
        "real_sentinel1_stable_bridge_01",
        "real_sentinel1_subsidence_tunnel_02",
        "real_terrasarx_thermal_dam_03",
        "real_sentinel1_tropospheric_noise_04",
        "real_sentinel1_vegetated_embankment_05",
    ]
    for ds_name in datasets:
        p = REAL_DATA_DIR / ds_name
        meta, obs = RealDataIngestionService.load_dataset(p)
        assert meta.dataset_id == ds_name
        assert meta.sensor in {"Sentinel-1A/B", "Sentinel-1A", "Sentinel-1B", "TerraSAR-X"}
        assert len(obs) >= 25
        assert all(isinstance(o, ObservationRead) for o in obs)
        assert meta.license is not None
        assert meta.source is not None


# ==============================================================================
# 2. Unit Conversion
# ==============================================================================
def test_unit_conversion():
    """Tests explicit unit conversions for displacement, velocity, and acceleration."""
    # Displacement
    assert convert_displacement_to_mm(5.0, "mm") == 5.0
    assert convert_displacement_to_mm(2.5, "cm") == 25.0
    assert convert_displacement_to_mm(0.012, "m") == 12.0
    with pytest.raises(ValueError, match="Unsupported displacement unit"):
        convert_displacement_to_mm(1.0, "inches")

    # Velocity
    assert convert_velocity_to_mm_per_year(10.0, "mm/yr") == 10.0
    assert convert_velocity_to_mm_per_year(1.5, "cm/year") == 15.0
    assert convert_velocity_to_mm_per_year(0.02, "m/a") == 20.0
    with pytest.raises(ValueError, match="Unsupported velocity unit"):
        convert_velocity_to_mm_per_year(1.0, "km/h")

    # Acceleration
    assert convert_acceleration_to_mm_per_year2(4.0, "mm/year2") == 4.0
    assert convert_acceleration_to_mm_per_year2(0.005, "m/yr^2") == 5.0
    with pytest.raises(ValueError, match="Unsupported acceleration unit"):
        convert_acceleration_to_mm_per_year2(1.0, "m/s2")


# ==============================================================================
# 3. Timestamp Normalization
# ==============================================================================
def test_timestamp_normalization():
    """Tests ISO string parsing, UTC retention, and naive datetime conversion."""
    # ISO string with Z
    dt1 = normalize_timestamp("2023-05-10T14:30:00Z")
    assert dt1.tzinfo == timezone.utc
    assert dt1.hour == 14

    # ISO string with offset
    dt2 = normalize_timestamp("2023-05-10T16:30:00+02:00")
    assert dt2.tzinfo == timezone.utc
    assert dt2.hour == 14

    # Naive datetime
    dt3 = normalize_timestamp(datetime(2023, 5, 10, 12, 0, 0))
    assert dt3.tzinfo == timezone.utc

    with pytest.raises(TypeError):
        normalize_timestamp(123456789)


# ==============================================================================
# 4. Missing Observations Handling
# ==============================================================================
def test_missing_observations_handling():
    """Verifies that sequences with missing epochs are handled without crashing."""
    p = REAL_DATA_DIR / "real_terrasarx_thermal_dam_03"
    meta, obs = RealDataIngestionService.load_dataset(p)

    # Sub-sample to simulate missing every second observation
    thinned_obs = obs[::2]
    temp_eng = TemporalEvidenceEngine()
    summary = temp_eng.evaluate_summary("test_thinned", thinned_obs)

    assert summary.observation_count == len(thinned_obs)
    assert summary.temporal_status != TemporalStatus.INSUFFICIENT_HISTORY
    assert summary.missing_epoch_count > 0


# ==============================================================================
# 5. Irregular Acquisition Intervals
# ==============================================================================
def test_irregular_acquisition_intervals():
    """Tests that real irregular acquisition spacing is preserved and handled properly."""
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)

    # Calculate intervals
    intervals = [
        (obs[i].acquisition_timestamp - obs[i - 1].acquisition_timestamp).total_seconds() / 86400.0
        for i in range(1, len(obs))
    ]
    # Verify irregular intervals exist (e.g. 12, 24, 36 days)
    unique_intervals = set(round(inv) for inv in intervals)
    assert len(unique_intervals) > 1

    temp_eng = TemporalEvidenceEngine()
    summary = temp_eng.evaluate_summary("test_irregular", obs)
    assert summary.coverage_duration_days > 365.0
    assert summary.trend_rate_mm_per_year is not None


# ==============================================================================
# 6. Missing Geometry Handling (No Invented Geometry)
# ==============================================================================
def test_missing_geometry_handling():
    """Verifies that missing incidence angle marks geometry UNAVAILABLE and does not invent angle."""
    vert, ok = project_los_to_vertical(10.0, None)
    assert vert is None
    assert ok is False

    vert_bad, ok_bad = project_los_to_vertical(10.0, 90.0)
    assert vert_bad is None
    assert ok_bad is False

    vert_zero, ok_zero = project_los_to_vertical(10.0, 0.0)
    assert vert_zero is None
    assert ok_zero is False

    # Ingestion test with missing geometry
    raw_rec = RawObservationRecord(
        timestamp="2023-01-01T00:00:00Z",
        displacement=5.0,
        displacement_unit="mm",
        displacement_type=DisplacementType.LOS,
        incidence_angle=None,
    )
    meta = ExternalDatasetMetadata(
        dataset_id="test_geom_missing",
        dataset_name="Test Missing Geometry",
        category="TEST",
        source="TEST",
        license="CC-0",
        geographic_region="TEST",
        sensor="Sentinel-1",
        acquisition_period={"start": "2023-01-01", "end": "2023-01-02"},
        spatial_resolution="10m",
        temporal_resolution="12d",
        processing_method="DInSAR",
        displacement_representation=DisplacementType.LOS,
        incidence_angle_deg=None,  # Missing
        independent_reference=ExternalReference(
            reference_type=ReferenceType.UNKNOWN,
            reference_source="None",
            reference_strength=ReferenceStrength.LOW,
            documented_behavior="None",
            expected_strata_behavior="None",
        ),
    )
    converted = RealDataIngestionService.convert_to_observations(meta, [raw_rec])
    assert converted[0].deformation_mm is None
    assert "GEOMETRY_UNAVAILABLE" in converted[0].metadata["flags"]


# ==============================================================================
# 7. Missing Coherence / Quality Handling
# ==============================================================================
def test_missing_coherence_handling():
    """Verifies that missing coherence is flagged without synthetic assumptions."""
    val, ok = normalize_coherence(None)
    assert val is None
    assert ok is False

    raw_rec = RawObservationRecord(
        timestamp="2023-01-01T00:00:00Z",
        displacement=5.0,
        displacement_unit="mm",
        displacement_type=DisplacementType.VERTICAL,
        coherence=None,
    )
    meta = ExternalDatasetMetadata(
        dataset_id="test_coherence_missing",
        dataset_name="Test Missing Coherence",
        category="TEST",
        source="TEST",
        license="CC-0",
        geographic_region="TEST",
        sensor="Sentinel-1",
        acquisition_period={"start": "2023-01-01", "end": "2023-01-02"},
        spatial_resolution="10m",
        temporal_resolution="12d",
        processing_method="DInSAR",
        displacement_representation=DisplacementType.VERTICAL,
        independent_reference=ExternalReference(
            reference_type=ReferenceType.UNKNOWN,
            reference_source="None",
            documented_behavior="None",
            expected_strata_behavior="None",
        ),
    )
    converted = RealDataIngestionService.convert_to_observations(meta, [raw_rec])
    assert converted[0].coherence is None
    assert "COHERENCE_UNAVAILABLE" in converted[0].metadata["flags"]


# ==============================================================================
# 8. LOS vs Vertical Representation
# ==============================================================================
def test_los_vs_vertical_representation():
    """Verifies projection for LOS and preservation without reprojecting for VERTICAL."""
    # 1. LOS: projected via d_los / cos(theta)
    vert, ok = project_los_to_vertical(10.0, 30.0)
    assert ok is True
    assert round(vert, 3) == round(10.0 / 0.8660254, 3)

    # 2. VERTICAL dataset: displacement directly ingested
    p = REAL_DATA_DIR / "real_sentinel1_subsidence_tunnel_02"
    meta, obs = RealDataIngestionService.load_dataset(p)
    assert meta.displacement_representation == DisplacementType.VERTICAL
    assert "EXTERNAL_VERTICAL_PROVIDED" in obs[0].metadata["flags"]
    assert obs[0].los_displacement_mm is None
    assert obs[0].deformation_mm == -0.43


# ==============================================================================
# 9. Leakage Prevention Firewall
# ==============================================================================
def test_leakage_prevention_firewall():
    """Verifies that external reference labels cannot leak into observation metadata or payloads."""
    # Test verify_no_leakage raises ValueError on forbidden keys
    with pytest.raises(ValueError, match="Programmatic Leakage Firewall Violation"):
        verify_no_leakage({"known_deformation": True, "value": 1.0})

    with pytest.raises(ValueError, match="Programmatic Leakage Firewall Violation"):
        verify_no_leakage({"reference_type": "INDEPENDENT_REFERENCE"})

    with pytest.raises(ValueError, match="Programmatic Leakage Firewall Violation"):
        verify_no_leakage({"metadata": {"ground_truth_class": "STRUCTURAL_MONOTONIC"}})

    # Verify that clean observation passes
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)
    verify_no_leakage(obs)


# ==============================================================================
# 10. Deterministic Replay
# ==============================================================================
def test_deterministic_replay():
    """Verifies that re-running the pipeline on real observations produces identical results."""
    p = REAL_DATA_DIR / "real_terrasarx_thermal_dam_03"
    meta, obs = RealDataIngestionService.load_dataset(p)

    inf = Infrastructure(
        id="inf_dam_replay",
        name=meta.dataset_name,
        structure_type=StructureType.DAM,
        material=MaterialType.CONCRETE,
        criticality=CriticalityLevel.CRITICAL,
    )

    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)

    # Run 1
    sum1 = temp_eng.evaluate_summary(inf.id, obs)
    char1 = risk_eng.evaluate_infrastructure(inf, obs, temporal_summary=sum1)

    # Run 2
    sum2 = temp_eng.evaluate_summary(inf.id, obs)
    char2 = risk_eng.evaluate_infrastructure(inf, obs, temporal_summary=sum2)

    assert sum1.temporal_status == sum2.temporal_status
    assert sum1.trend_rate_mm_per_year == sum2.trend_rate_mm_per_year
    assert sum1.persistence_score == sum2.persistence_score
    assert char1.characterization_state == char2.characterization_state
    assert char1.prototype_risk_index == char2.prototype_risk_index


# ==============================================================================
# 11. Threshold Audit Registry
# ==============================================================================
def test_threshold_audit_registry():
    """Verifies that all prototype thresholds are properly registered and documented."""
    registry = get_prototype_threshold_registry()
    assert len(registry) >= 10

    components = {t.component for t in registry}
    assert "Physics Engine" in components
    assert "Temporal Engine" in components
    assert "Consensus Engine" in components
    assert "Risk Characterization" in components

    actions = {t.recommended_action for t in registry}
    assert ThresholdAction.RETAIN_AS_PROTOTYPE in actions
    assert ThresholdAction.REQUIRES_REAL_WORLD_CALIBRATION in actions

    for t in registry:
        assert isinstance(t, ThresholdRecord)
        assert len(t.threshold_name) > 0
        assert len(t.rationale) > 0


# ==============================================================================
# 12. End-to-End Real-Data Pipeline
# ==============================================================================
def test_end_to_end_real_data_pipeline():
    """Executes the complete pipeline on real datasets and validates scientific behavior."""
    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)

    # Category C: Thermal Dam
    p_dam = REAL_DATA_DIR / "real_terrasarx_thermal_dam_03"
    meta_dam, obs_dam = RealDataIngestionService.load_dataset(p_dam)
    inf_dam = Infrastructure(
        id="test_dam",
        name=meta_dam.dataset_name,
        structure_type=StructureType.DAM,
        material=MaterialType.CONCRETE,
        criticality=CriticalityLevel.CRITICAL,
    )
    sum_dam = temp_eng.evaluate_summary(inf_dam.id, obs_dam)
    char_dam = risk_eng.evaluate_infrastructure(inf_dam, obs_dam, temporal_summary=sum_dam)

    # Must suppress seasonal cycle as environmental evidence
    assert sum_dam.temporal_status == TemporalStatus.ENVIRONMENTAL_PATTERN
    assert char_dam.characterization_state == RiskCharacterizationState.ENVIRONMENTAL_PATTERN

    # Category D: Tropospheric Viaduct
    p_viaduct = REAL_DATA_DIR / "real_sentinel1_tropospheric_noise_04"
    meta_viaduct, obs_viaduct = RealDataIngestionService.load_dataset(p_viaduct)
    inf_viaduct = Infrastructure(
        id="test_viaduct",
        name=meta_viaduct.dataset_name,
        structure_type=StructureType.BRIDGE,
        material=MaterialType.CONCRETE,
        criticality=CriticalityLevel.MODERATE,
    )
    sum_viaduct = temp_eng.evaluate_summary(inf_viaduct.id, obs_viaduct)
    char_viaduct = risk_eng.evaluate_infrastructure(inf_viaduct, obs_viaduct, temporal_summary=sum_viaduct)

    # Acute spike must not trigger structural alarm
    assert char_viaduct.characterization_state in {
        RiskCharacterizationState.BASELINE,
        RiskCharacterizationState.MONITOR,
    }
    assert (char_viaduct.prototype_risk_index or 0.0) < 30.0

    # Category E: Decorrelated Embankment
    p_emb = REAL_DATA_DIR / "real_sentinel1_vegetated_embankment_05"
    meta_emb, obs_emb = RealDataIngestionService.load_dataset(p_emb)
    inf_emb = Infrastructure(
        id="test_embankment",
        name=meta_emb.dataset_name,
        structure_type=StructureType.EMBANKMENT,
        material=MaterialType.EARTH,
        criticality=CriticalityLevel.LOW,
    )
    sum_emb = temp_eng.evaluate_summary(inf_emb.id, obs_emb)
    char_emb = risk_eng.evaluate_infrastructure(inf_emb, obs_emb, temporal_summary=sum_emb)

    # Low coherence must suppress risk to INSUFFICIENT_EVIDENCE
    assert sum_emb.temporal_status == TemporalStatus.LOW_QUALITY
    assert char_emb.characterization_state == RiskCharacterizationState.INSUFFICIENT_EVIDENCE


# ==============================================================================
# 13. External Reference Isolation
# ==============================================================================
def test_external_reference_isolation():
    """Verifies that ExternalReference exists in metadata and is strictly isolated from observations."""
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)

    ref = meta.independent_reference
    assert isinstance(ref, ExternalReference)
    assert ref.reference_type == ReferenceType.INDEPENDENT_REFERENCE
    assert ref.reference_strength == ReferenceStrength.HIGH

    # Observations must not contain any reference attributes
    for o in obs:
        obs_dump = o.model_dump()
        assert "reference_type" not in obs_dump
        assert "reference_source" not in obs_dump
        assert "documented_behavior" not in obs_dump
        if o.metadata:
            assert "reference_type" not in o.metadata
            assert "known_deformation" not in o.metadata


# ==============================================================================
# 14. Characterization with Incomplete Infrastructure Metadata
# ==============================================================================
def test_characterization_incomplete_metadata():
    """Tests Phase 7 Risk Characterization when infrastructure metadata is completely unknown/missing."""
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)

    # Infrastructure with minimal/unknown properties
    incomplete_inf = Infrastructure(
        id="inf_incomplete",
        name="Incomplete Infrastructure Asset",
        structure_type=StructureType.OTHER,
        material=MaterialType.UNKNOWN,
        criticality=CriticalityLevel.UNKNOWN,
        expected_behavior=None,
        critical_zones=None,
        historical_baseline=None,
    )

    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)

    summary = temp_eng.evaluate_summary(incomplete_inf.id, obs)
    char = risk_eng.evaluate_infrastructure(incomplete_inf, obs, temporal_summary=summary)

    # System must complete evaluation without crashing
    assert char.characterization_state is not None
    assert char.confidence is not None
    assert "uncertainty_factors" in char.model_dump()


# ==============================================================================
# 15. Provenance Registry & Classification (Phase 8.1 Section 1 & 3)
# ==============================================================================
def test_provenance_registry_and_classification():
    """Verifies that all 5 datasets are registered with explicit SYNTHETIC_CASE_STUDY status."""
    registry = get_provenance_registry()
    assert len(registry) == 5

    for rec in registry:
        # Must be explicitly marked as SYNTHETIC / CASE-STUDY PLACEHOLDER
        assert rec.provenance_status == ProvenanceStatus.SYNTHETIC_CASE_STUDY
        assert rec.reference_independent is True
        assert rec.sensor in {"Sentinel-1A/B (C-band)", "Sentinel-1A (C-band)", "Sentinel-1B (C-band)", "TerraSAR-X (X-band)"}
        assert len(rec.geographic_region) > 0
        assert len(rec.manual_entries_or_assumptions) > 0


# ==============================================================================
# 16. Threshold Audit Classification (Phase 8.1 Section 14)
# ==============================================================================
def test_threshold_audit_classification():
    """Verifies all thresholds are classified under the 4 formal origin types."""
    registry = get_prototype_threshold_registry()
    valid_origins = {
        ThresholdOriginType.LITERATURE_SUPPORTED,
        ThresholdOriginType.EXTERNALLY_DERIVED,
        ThresholdOriginType.EMPIRICAL_FROM_SYNTHETIC_DATA,
        ThresholdOriginType.PROTOTYPE_ASSUMPTION,
    }
    for t in registry:
        assert t.origin_type in valid_origins

    origin_counts = {orig: sum(1 for t in registry if t.origin_type == orig) for orig in valid_origins}
    assert origin_counts[ThresholdOriginType.LITERATURE_SUPPORTED] >= 4
    assert origin_counts[ThresholdOriginType.PROTOTYPE_ASSUMPTION] >= 2


# ==============================================================================
# 17. Prototype Index Wording & Disclaimer (Phase 8.1 Section 5 & 6)
# ==============================================================================
def test_prototype_index_wording_and_disclaimer():
    """Verifies that the formal Phase 7 disclaimer exists and disclaims safety/collapse claims."""
    disclaimer = get_formal_phase7_index_disclaimer()
    assert "experimental prototype index" in disclaimer.lower()
    assert "not a probability of failure" in disclaimer.lower()
    assert "not" in disclaimer.lower() and "safety rating" in disclaimer.lower()

    # Verify that Phase 7 explanations do not use unscientific (Safe) labels
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)
    inf = Infrastructure(
        id="inf_bridge_check",
        name=meta.dataset_name,
        structure_type=StructureType.BRIDGE,
        material=MaterialType.STEEL,
        criticality=CriticalityLevel.HIGH,
    )
    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)
    summary = temp_eng.evaluate_summary(inf.id, obs)
    char = risk_eng.evaluate_infrastructure(inf, obs, temporal_summary=summary)

    # Explanation and factors must not contain prohibited safety certification words
    char_str = str(char.model_dump())
    assert "(Safe)" not in char_str
    assert "collapse prediction" not in char_str.lower()
    assert "safety certification" not in char_str.lower()


# ==============================================================================
# 18. Case-Level Analysis: Stable Bridge Contained False Positive (Phase 8.1 Section 9)
# ==============================================================================
def test_case_level_stable_bridge_contained_false_positive():
    """
    Detailed audit of Category A: verifies that frozen ML domain shift is caught
    by consensus disagreement and temporal engine, preventing false structural escalation.
    """
    p = REAL_DATA_DIR / "real_sentinel1_stable_bridge_01"
    meta, obs = RealDataIngestionService.load_dataset(p)
    ml = MLDeformationClassifier()
    physics = PhysicsInSARConsistencyEngine()
    consensus = ConsensusEngine()
    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)

    ml_res = ml.predict(obs)
    # ML model exhibits out-of-domain shift due to sub-millimeter noise
    assert ml_res.confidence < 0.60

    seq_obj = ObservationSequence(infrastructure_id="bridge", epoch_count=len(obs), observations=obs)
    phys_res = physics.evaluate_sequence(seq_obj)
    cons_res = consensus.evaluate(ml_res, phys_res)

    # Consensus disagreement penalty is triggered
    assert cons_res.disagreement_penalty > 0.0

    summary = temp_eng.evaluate_summary("bridge", obs)
    # Temporal state reflects cross-model conflict
    assert summary.temporal_status == TemporalStatus.CONFLICTED
    assert abs(summary.trend_rate_mm_per_year or 0.0) < 1.0  # Near-zero secular drift

    char = risk_eng.evaluate_infrastructure(
        Infrastructure(id="bridge", name="Bridge", structure_type=StructureType.BRIDGE),
        obs,
        temporal_summary=summary,
    )
    # Final risk state remains MONITOR (non-structural alert), contained false positive
    assert char.characterization_state in {RiskCharacterizationState.MONITOR, RiskCharacterizationState.BASELINE}
    assert (char.prototype_risk_index or 0.0) < 30.0


# ==============================================================================
# 19. Case-Level Analysis: Subsidence Tunnel Conflict (Phase 8.1 Section 10)
# ==============================================================================
def test_case_level_subsidence_tunnel_conflict():
    """
    Detailed audit of Category B: verifies that strong subsidence (-18.9 mm/yr)
    is detected, and documents why long-sequence kinematic divergence produces CONFLICTED.
    """
    p = REAL_DATA_DIR / "real_sentinel1_subsidence_tunnel_02"
    meta, obs = RealDataIngestionService.load_dataset(p)
    temp_eng = TemporalEvidenceEngine()
    risk_eng = InfrastructureRiskCharacterizationEngine(temporal_engine=temp_eng)

    summary = temp_eng.evaluate_summary("tunnel", obs)
    # Trend rate clearly detects severe ground settlement
    assert summary.trend_rate_mm_per_year is not None
    assert summary.trend_rate_mm_per_year < -15.0

    # The 52-epoch sequence produces CONFLICTED temporal state due to cross-model kinematic conflict
    assert summary.temporal_status == TemporalStatus.CONFLICTED

    char = risk_eng.evaluate_infrastructure(
        Infrastructure(id="tunnel", name="Tunnel", structure_type=StructureType.TUNNEL, criticality=CriticalityLevel.CRITICAL),
        obs,
        temporal_summary=summary,
    )
    # Risk characterization assigns MONITOR (not high attention) due to consensus conflict
    assert char.characterization_state == RiskCharacterizationState.MONITOR
    assert 30.0 <= (char.prototype_risk_index or 0.0) <= 50.0


# ==============================================================================
# 20. Synthetic vs External Comparison & Shift (Phase 8.1 Section 13)
# ==============================================================================
def test_synthetic_vs_external_comparison():
    """Verifies that synthetic-to-external distribution shift metrics are computed."""
    audit_path = Path("data/real/audit/phase8_real_world_validation.json")
    assert audit_path.exists()

    import json
    with open(audit_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    shift = data.get("distribution_shift_analysis", {})
    assert "synthetic" in shift
    assert "real" in shift
    assert "key_observations" in shift

    # Real interval mean should be greater than synthetic 12.0d
    assert shift["real"]["interval_days"]["mean"] > 12.0
    # Real ML confidence mean should be lower than synthetic 0.88
    assert shift["real"]["ml_confidence"]["mean"] < 0.60


# ==============================================================================
# 21. Audit Files Existence & Schema Validity (Phase 8.1 Section 3, 14, 15)
# ==============================================================================
def test_audit_files_exist_and_valid():
    """Verifies that all Phase 8.1 audit artifacts exist and parse correctly."""
    import json
    audit_dir = Path("data/real/audit")
    prov_file = audit_dir / "provenance_registry.json"
    thresh_file = audit_dir / "threshold_audit.json"
    val_file = audit_dir / "phase8_real_world_validation.json"

    assert prov_file.exists(), f"Missing {prov_file}"
    assert thresh_file.exists(), f"Missing {thresh_file}"
    assert val_file.exists(), f"Missing {val_file}"

    with open(prov_file, "r", encoding="utf-8") as f:
        prov_data = json.load(f)
        assert len(prov_data) == 5

    with open(thresh_file, "r", encoding="utf-8") as f:
        thresh_data = json.load(f)
        assert len(thresh_data) >= 10

    with open(val_file, "r", encoding="utf-8") as f:
        val_data = json.load(f)
        assert val_data["scientific_status"] == "PHASE 8 — PRELIMINARY EXTERNAL VALIDATION ONLY"

