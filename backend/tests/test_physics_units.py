from datetime import datetime, timedelta, timezone
import pytest
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import (
    GeometryStatus,
    ObservationSequence,
    PhysicsClassification,
    TemporalTrendPattern,
)
from backend.app.services.physics.atmospheric import evaluate_atmospheric_suspect
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.physics.geometry import evaluate_geometry
from backend.app.services.physics.kinematics import evaluate_kinematics
from backend.app.services.physics.quality import (
    COHERENCE_HIGH_THRESHOLD,
    COHERENCE_NOISE_FLOOR,
    evaluate_coherence,
    evaluate_measurement_quality,
    evaluate_phase_quality,
)
from backend.app.services.physics.temporal import evaluate_temporal_consistency
from backend.app.services.physics.environmental import evaluate_environmental_evidence


def make_obs(
    epoch_idx: int,
    disp: float,
    coh: float = 0.85,
    phase: float = 0.88,
    inc: float = 35.0,
    vel: float = -5.0,
    atm: str = "CLEAR",
) -> ObservationRead:
    return ObservationRead(
        id=f"obs_{epoch_idx}",
        infrastructure_id="infra_test",
        acquisition_timestamp=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc) + timedelta(days=epoch_idx * 12),
        deformation_mm=disp,
        los_displacement_mm=disp,
        velocity_mm_per_year=vel,
        coherence=coh,
        phase_quality=phase,
        incidence_angle=inc,
        atmospheric_indicator=atm,
        source="SYNTHETIC",
        created_at=datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
    )


def test_coherence_evaluation_boundaries():
    # High coherence
    score, suff, msg = evaluate_coherence(0.85)
    assert score == 0.85
    assert suff is True
    assert "High coherence" in msg

    # Moderate coherence
    score, suff, msg = evaluate_coherence(0.55)
    assert score == 0.55
    assert suff is True
    assert "Moderate coherence" in msg

    # Low coherence below noise floor
    score, suff, msg = evaluate_coherence(0.18)
    assert score == 0.18
    assert suff is False
    assert "Severely decorrelated" in msg

    # Missing coherence
    score, suff, msg = evaluate_coherence(None)
    assert score is None
    assert suff is False

    # Out of range coherence
    with pytest.raises(ValueError):
        evaluate_coherence(1.25)
    with pytest.raises(ValueError):
        evaluate_coherence(-0.05)


def test_phase_quality_evaluation():
    score, msg = evaluate_phase_quality(0.92)
    assert score == 0.92
    assert "High phase quality" in msg

    score, msg = evaluate_phase_quality(0.30)
    assert score == 0.30
    assert "Low phase quality" in msg

    score, msg = evaluate_phase_quality(None)
    assert score is None
    assert "omitted" in msg.lower()

    with pytest.raises(ValueError):
        evaluate_phase_quality(1.5)


def test_measurement_quality_aggregation():
    obs_list = [
        make_obs(0, -1.0, coh=0.88, phase=0.90),
        make_obs(1, -2.0, coh=0.82, phase=0.85),
        make_obs(2, -3.0, coh=0.80, phase=0.82),
    ]
    meas_ev = evaluate_measurement_quality(obs_list)
    assert meas_ev.has_sufficient_coherence is True
    assert meas_ev.quality_score > 0.70
    assert meas_ev.coherence_score == pytest.approx(0.833, abs=0.01)


def test_geometry_evaluation_and_vertical_projection():
    # Valid geometry: 35 degrees incidence
    obs_list = [make_obs(0, -2.86, inc=35.0)]
    geom_ev = evaluate_geometry(obs_list)
    assert geom_ev.status == GeometryStatus.VALID_GEOMETRY
    assert geom_ev.incidence_angle_deg == 35.0
    assert geom_ev.geometric_sensitivity_factor == pytest.approx(0.8192, abs=0.01)
    # Projected vertical: -2.86 / cos(35 deg) ~= -3.49 mm
    assert geom_ev.mean_projected_vertical_mm == pytest.approx(-3.491, abs=0.05)

    # Weak geometry: out of nominal range (e.g. 70 degrees)
    obs_weak = [make_obs(0, -2.0, inc=70.0)]
    geom_weak = evaluate_geometry(obs_weak)
    assert geom_weak.status == GeometryStatus.WEAK_GEOMETRY

    # Invalid geometry: 95 degrees
    obs_invalid = [make_obs(0, -2.0, inc=95.0)]
    geom_invalid = evaluate_geometry(obs_invalid)
    assert geom_invalid.status == GeometryStatus.INVALID_GEOMETRY


def test_kinematic_consistency():
    # 12 days between epochs: dt ~= 0.03285 years
    # Reported velocity: -30.44 mm/year
    # dt * -30.44 = -1.0 mm displacement step
    obs_list = [
        make_obs(0, 0.0, vel=-30.44),
        make_obs(1, -1.0, vel=-30.44),
    ]
    kin_ev = evaluate_kinematics(obs_list)
    assert kin_ev.kinematic_consistency is not None
    assert kin_ev.kinematic_consistency > 0.85
    assert kin_ev.mean_kinematic_residual_mm_yr < 2.0


def test_temporal_persistence_and_directional_consistency():
    # Monotonic persistent settlement
    obs_list = [
        make_obs(0, -1.5),
        make_obs(1, -3.0),
        make_obs(2, -4.8),
        make_obs(3, -6.5),
        make_obs(4, -8.0),
    ]
    temp_ev = evaluate_temporal_consistency(obs_list)
    assert temp_ev.persistence == 1.0  # 100% of epochs exceed stable noise floor
    assert temp_ev.directional_consistency == 1.0  # All negative
    assert temp_ev.abrupt_inconsistency_score == 0.0
    assert temp_ev.trend_pattern == TemporalTrendPattern.MONOTONIC


def test_atmospheric_transient_spike_detection():
    # Baseline near zero, epoch 1 spikes to -9.0 mm, epoch 2 returns to baseline (-0.5 mm)
    obs_list = [
        make_obs(0, -0.2, atm="CLEAR"),
        make_obs(1, -9.0, atm="HIGH_TROPOSPHERIC_TURBULENCE"),
        make_obs(2, -0.5, atm="CLEAR"),
        make_obs(3, -0.3, atm="CLEAR"),
    ]
    temp_ev = evaluate_temporal_consistency(obs_list)
    atm_ev = evaluate_atmospheric_suspect(obs_list, temp_ev)

    assert atm_ev.has_transient_spike is True
    assert atm_ev.atmospheric_suspect_score > 0.60
    assert "Transient spike" in str(atm_ev.explanation)


def test_insufficient_evidence_behavior():
    engine = PhysicsInSARConsistencyEngine()
    # Sequence with only 1 epoch
    seq = ObservationSequence(
        infrastructure_id="infra_single",
        observations=[make_obs(0, -2.5)],
        epoch_count=1,
    )
    result = engine.evaluate_sequence(seq)
    assert result.classification == PhysicsClassification.INSUFFICIENT_EVIDENCE
    assert any("Fewer than 3" in exp for exp in result.explanation)


def test_environmental_evidence_periodic_cycle():
    # 8 epochs oscillating between positive and negative displacement with bounded amplitude
    obs_list = [
        make_obs(0, 4.0),
        make_obs(1, 7.5),
        make_obs(2, 5.0),
        make_obs(3, 0.0),
        make_obs(4, -4.5),
        make_obs(5, -7.0),
        make_obs(6, -3.5),
        make_obs(7, 1.0),
    ]
    temp_ev = evaluate_temporal_consistency(obs_list)
    env_ev = evaluate_environmental_evidence(obs_list, temp_ev)

    assert env_ev.periodicity_detected is True
    assert env_ev.seasonal_pattern_strength >= 0.60
    assert env_ev.environmental_suspect_score >= 0.50
    assert env_ev.cycle_count >= 2


def test_environmental_evidence_monotonic_rejection():
    # Monotonic progression must NOT trigger periodicity
    obs_list = [
        make_obs(0, -1.0),
        make_obs(1, -3.0),
        make_obs(2, -5.5),
        make_obs(3, -8.0),
        make_obs(4, -11.0),
    ]
    temp_ev = evaluate_temporal_consistency(obs_list)
    env_ev = evaluate_environmental_evidence(obs_list, temp_ev)

    assert env_ev.periodicity_detected is False
    assert env_ev.seasonal_pattern_strength < 0.40
    assert env_ev.cycle_count == 0


def test_stable_classification_decision():
    # Subtle variations within noise margins (+/- 0.3 mm)
    obs_list = [
        make_obs(0, -0.2),
        make_obs(1, 0.1),
        make_obs(2, -0.3),
        make_obs(3, 0.2),
        make_obs(4, -0.1),
    ]
    seq = ObservationSequence(
        infrastructure_id="infra_stable",
        observations=obs_list,
        epoch_count=len(obs_list),
    )
    engine = PhysicsInSARConsistencyEngine()
    result = engine.evaluate_sequence(seq)

    assert result.classification == PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION
    assert result.temporal_evidence.trend_pattern == TemporalTrendPattern.STABLE

