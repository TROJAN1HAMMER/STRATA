"""
Comprehensive unit tests for STRATA Temporal Evidence Engine (Phase 6).
Validates canonical ordering, irregular interval kinematics, state machine transitions,
persistence scoring, environmental recurrence guards, and leakage firewall.
"""
from datetime import datetime, timezone
import pytest

from backend.app.schemas.consensus import (
    ConsensusAssessment,
    ConsensusCategory,
    ConsensusFlag,
)
from backend.app.schemas.temporal import TemporalStatus
from backend.app.services.temporal.engine import TemporalEvidenceEngine
from backend.app.services.temporal.kinematics import calculate_temporal_kinematics
from backend.app.services.temporal.ordering import canonicalize_and_order_observations
from backend.app.services.temporal.persistence import calculate_structural_persistence_score
from backend.app.services.temporal.state_machine import evaluate_temporal_state_machine


# ---------------------------------------------------------------------------
# HELPERS & MOCKS
# ---------------------------------------------------------------------------

def make_obs(obs_id: str, ts_str: str, disp_mm: float = 0.0, coh: float = 0.85):
    return {
        "id": obs_id,
        "acquisition_timestamp": ts_str,
        "deformation_mm": disp_mm,
        "coherence": coh,
        "phase_quality": 0.80,
    }


def make_assessment(
    cat: ConsensusCategory = ConsensusCategory.STRUCTURAL,
    conf: float = 0.80,
    agree: float = 0.80,
    qual: float = 0.85,
    flags: list = None,
) -> ConsensusAssessment:
    return ConsensusAssessment(
        consensus_class=cat,
        consensus_confidence=conf,
        agreement_score=agree,
        disagreement_penalty=round(1.0 - agree, 4),
        evidence_quality_score=qual,
        temporal_persistence_score=0.80,
        ml_contribution={"predicted_class": cat.value, "confidence": conf},
        physics_contribution={"classification": cat.value, "evidence_strength": conf},
        explanation="Test assessment.",
        flags=flags or [],
        model_versions={"ml": "1.0", "physics": "1.0", "consensus": "1.0"},
        consensus_engine_version="strata_consensus_v0.1.0",
    )


# ---------------------------------------------------------------------------
# 1. ORDERING, DEDUPLICATION, & INTERVALS
# ---------------------------------------------------------------------------

def test_canonical_ordering_and_intervals():
    obs_list = [
        make_obs("obs3", "2025-01-25T00:00:00Z", -3.0),
        make_obs("obs1", "2025-01-01T00:00:00Z", -1.0),
        make_obs("obs2", "2025-01-13T00:00:00Z", -2.0),
    ]

    ordered, intervals, missing, span = canonicalize_and_order_observations(obs_list)

    assert [o["id"] for o in ordered] == ["obs1", "obs2", "obs3"]
    assert len(intervals) == 2
    assert intervals[0] == pytest.approx(12.0, abs=1e-3)
    assert intervals[1] == pytest.approx(12.0, abs=1e-3)
    assert span == pytest.approx(24.0, abs=1e-3)
    assert missing == 0


def test_shuffled_input_determinism():
    obs_a = [
        make_obs("obs1", "2025-01-01T00:00:00Z", -1.0),
        make_obs("obs2", "2025-01-13T00:00:00Z", -2.0),
        make_obs("obs3", "2025-01-25T00:00:00Z", -3.0),
    ]
    obs_b = [obs_a[2], obs_a[0], obs_a[1]]

    ordered_a, _, _, _ = canonicalize_and_order_observations(obs_a)
    ordered_b, _, _, _ = canonicalize_and_order_observations(obs_b)

    assert [o["id"] for o in ordered_a] == [o["id"] for o in ordered_b]


def test_duplicate_observation_rejection():
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z"),
        make_obs("obs1", "2025-01-13T00:00:00Z"),
    ]
    with pytest.raises(ValueError, match="Duplicate observation ID detected"):
        canonicalize_and_order_observations(obs_list)


def test_irregular_interval_and_missing_epoch_detection():
    # Regular 12-day cadence with a 48-day gap (3 missed epochs)
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z"),
        make_obs("obs2", "2025-01-13T00:00:00Z"),
        make_obs("obs3", "2025-01-25T00:00:00Z"),
        make_obs("obs4", "2025-03-14T00:00:00Z"),  # 48 days later
    ]
    _, intervals, missing, _ = canonicalize_and_order_observations(obs_list)
    assert missing >= 2


# ---------------------------------------------------------------------------
# 2. KINEMATICS: TREND RATE & APPARENT ACCELERATION
# ---------------------------------------------------------------------------

def test_kinematic_trend_rate_linear():
    # 5 epochs spanning ~120 days with -12 mm/year steady settlement
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0),
        make_obs("obs2", "2025-01-31T00:00:00Z", -1.0),
        make_obs("obs3", "2025-03-02T00:00:00Z", -2.0),
        make_obs("obs4", "2025-04-01T00:00:00Z", -3.0),
        make_obs("obs5", "2025-05-01T00:00:00Z", -4.0),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    assert rate is not None
    # Rate should be approximately -12 mm/year
    assert -13.0 <= rate <= -11.0
    # Acceleration for linear data should be approximately 0.0
    assert accel is not None
    assert abs(accel) < 2.0


def test_kinematic_apparent_acceleration():
    # Non-linear accelerating deformation: d(t) = -50 * t^2
    # Span 180 days (~0.5 years)
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0),
        make_obs("obs2", "2025-02-15T00:00:00Z", -0.8),
        make_obs("obs3", "2025-03-31T00:00:00Z", -3.2),
        make_obs("obs4", "2025-05-15T00:00:00Z", -7.2),
        make_obs("obs5", "2025-06-30T00:00:00Z", -12.5),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    assert rate is not None
    assert accel is not None
    # Apparent negative acceleration (downward acceleration)
    assert accel < -20.0


def test_insufficient_data_for_kinematics():
    # Fewer than 3 epochs returns None
    short_obs = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0),
        make_obs("obs2", "2025-01-12T00:00:00Z", -0.5),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(short_obs)
    assert rate is None
    assert accel is None
    assert supported is False


# ---------------------------------------------------------------------------
# 2.1 PHASE 6.1 ACCELERATION SUPPORT TESTS (CASES A, B, C, D)
# ---------------------------------------------------------------------------

def test_acceleration_case_a_adequate_temporal_coverage():
    """Case A: Adequate observations (>=6) and temporal coverage (>=90d) with consistent acceleration."""
    # 6 epochs spanning 180 days (~0.5 years) with quadratic acceleration d(t) = -50 * t^2
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("obs2", "2025-02-06T00:00:00Z", -0.49, coh=0.85),
        make_obs("obs3", "2025-03-14T00:00:00Z", -1.97, coh=0.85),
        make_obs("obs4", "2025-04-19T00:00:00Z", -4.43, coh=0.85),
        make_obs("obs5", "2025-05-25T00:00:00Z", -7.88, coh=0.85),
        make_obs("obs6", "2025-06-30T00:00:00Z", -12.30, coh=0.85),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    assert accel is not None
    assert accel < -50.0
    assert supported is True
    assert "supported across" in reason.lower()


def test_acceleration_case_b_short_baseline():
    """Case B: Short baseline (<90 days) with mathematically large apparent acceleration."""
    # 6 epochs spanning only 45 days (~0.123 years) with d(t) = -500 * t^2
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("obs2", "2025-01-10T00:00:00Z", -0.30, coh=0.85),
        make_obs("obs3", "2025-01-19T00:00:00Z", -1.22, coh=0.85),
        make_obs("obs4", "2025-01-28T00:00:00Z", -2.74, coh=0.85),
        make_obs("obs5", "2025-02-06T00:00:00Z", -4.88, coh=0.85),
        make_obs("obs6", "2025-02-15T00:00:00Z", -7.62, coh=0.85),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    # Mathematical apparent acceleration is calculated and preserved
    assert accel is not None
    assert accel < -500.0
    # But scientifically unsupported due to short temporal baseline
    assert supported is False
    assert "below prototype threshold" in reason.lower()
    assert "short baselines magnify" in reason.lower()


def test_acceleration_case_c_insufficient_observations():
    """Case C: Insufficient observations to calculate acceleration (<5 epochs)."""
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0),
        make_obs("obs2", "2025-02-01T00:00:00Z", -1.0),
        make_obs("obs3", "2025-03-01T00:00:00Z", -3.0),
        make_obs("obs4", "2025-04-01T00:00:00Z", -6.0),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    assert accel is None
    assert supported is False
    assert "insufficient" in reason.lower()


def test_acceleration_case_d_noisy_reversing_observations():
    """Case D: Large apparent acceleration produced by noisy oscillating measurements."""
    # 6 epochs spanning 180 days with erratic oscillations
    obs_list = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("obs2", "2025-02-06T00:00:00Z", 5.0, coh=0.85),
        make_obs("obs3", "2025-03-14T00:00:00Z", -5.0, coh=0.85),
        make_obs("obs4", "2025-04-19T00:00:00Z", 6.0, coh=0.85),
        make_obs("obs5", "2025-05-25T00:00:00Z", -4.0, coh=0.85),
        make_obs("obs6", "2025-06-30T00:00:00Z", 5.0, coh=0.85),
    ]
    rate, accel, supported, reason = calculate_temporal_kinematics(obs_list)
    assert accel is not None
    # Acceleration is NOT supported due to noisy reversals / scatter
    assert supported is False
    assert ("contradicts" in reason.lower() or "scatter" in reason.lower() or "noisy" in reason.lower())


# ---------------------------------------------------------------------------
# 3. EVIDENCE PERSISTENCE & ENVIRONMENTAL RECURRENCE
# ---------------------------------------------------------------------------

def test_structural_persistence_accumulation():
    # 5 consecutive high-agreement STRUCTURAL consensus assessments
    history = [make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85) for _ in range(5)]
    persistence = calculate_structural_persistence_score(history)
    assert persistence >= 0.70


def test_environmental_recurrence_suppresses_structural_persistence():
    # Recurring seasonal signal must NOT accumulate into structural persistence
    history = [
        make_assessment(ConsensusCategory.SEASONAL, conf=0.80),
        make_assessment(ConsensusCategory.SEASONAL, conf=0.85),
        make_assessment(ConsensusCategory.SEASONAL, conf=0.80),
        make_assessment(ConsensusCategory.STRUCTURAL, conf=0.70),  # 1 anomalous structural flag
    ]
    persistence = calculate_structural_persistence_score(history)
    assert persistence == 0.0


def test_atmospheric_transient_does_not_accumulate_persistence():
    history = [
        make_assessment(ConsensusCategory.ATMOSPHERIC, conf=0.75),
        make_assessment(ConsensusCategory.STABLE, conf=0.80),
        make_assessment(ConsensusCategory.ATMOSPHERIC, conf=0.75),
    ]
    persistence = calculate_structural_persistence_score(history)
    assert persistence == 0.0


# ---------------------------------------------------------------------------
# 4. TEMPORAL STATE MACHINE & TRANSITIONS
# ---------------------------------------------------------------------------

def test_state_machine_insufficient_history():
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z") for i in range(1, 3)]
    assessments = [make_assessment(ConsensusCategory.STABLE) for _ in range(2)]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.INSUFFICIENT_HISTORY
    assert len(transitions) == 1
    assert transitions[0].new_state == TemporalStatus.INSUFFICIENT_HISTORY


def test_state_machine_baseline_stability():
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z") for i in range(1, 5)]
    assessments = [make_assessment(ConsensusCategory.STABLE) for _ in range(4)]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.BASELINE
    # Transitioned from INSUFFICIENT_HISTORY -> BASELINE
    assert transitions[-1].new_state == TemporalStatus.BASELINE


def test_state_machine_emerging_to_persistent():
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z", disp_mm=-float(i * 3.0)) for i in range(1, 6)]
    assessments = [make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85) for _ in range(5)]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.PERSISTENT
    states = [t.new_state for t in transitions]
    assert TemporalStatus.EMERGING in states
    assert TemporalStatus.PERSISTENT in states


def test_state_machine_signal_reversion():
    # 4 structural epochs (PERSISTENT), followed by 2 stable epochs (REVERTED)
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z") for i in range(1, 7)]
    assessments = [
        make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85),
        make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85),
        make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85),
        make_assessment(ConsensusCategory.STRUCTURAL, conf=0.85, agree=0.85),
        make_assessment(ConsensusCategory.STABLE, conf=0.80),
        make_assessment(ConsensusCategory.STABLE, conf=0.85),
    ]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.REVERTED


def test_state_machine_environmental_pattern():
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z") for i in range(1, 5)]
    assessments = [make_assessment(ConsensusCategory.SEASONAL, conf=0.82) for _ in range(4)]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.ENVIRONMENTAL_PATTERN


def test_state_machine_conflicted():
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z") for i in range(1, 4)]
    assessments = [
        make_assessment(ConsensusCategory.STABLE),
        make_assessment(ConsensusCategory.SEASONAL),
        make_assessment(
            ConsensusCategory.SEASONAL,
            flags=[ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value],
        ),
    ]

    status, _ = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.CONFLICTED


# ---------------------------------------------------------------------------
# 4.1 PHASE 6.1 STABLE BASELINE VS CONFLICT TESTS
# ---------------------------------------------------------------------------

def test_state_machine_stable_noise_retains_baseline():
    """Validates that low-amplitude model sensitivity near zero baseline remains BASELINE."""
    # 5 epochs with small displacement noise (+/- 1.5 mm)
    obs = [
        make_obs("o1", "2025-01-01T00:00:00Z", -1.2, coh=0.80),
        make_obs("o2", "2025-01-15T00:00:00Z", 0.8, coh=0.82),
        make_obs("o3", "2025-02-01T00:00:00Z", 1.4, coh=0.85),
        make_obs("o4", "2025-02-15T00:00:00Z", -0.5, coh=0.81),
        make_obs("o5", "2025-03-01T00:00:00Z", 0.3, coh=0.84),
    ]
    # Assessments flag model disagreement because of noise fluctuations, but no true conflict
    assessments = [
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
    ]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.BASELINE
    assert any("nominal stability margin" in t.reason.lower() for t in transitions)


def test_state_machine_material_conflict_with_large_displacement():
    """Validates that disagreement WITH significant displacement remains CONFLICTED."""
    # 5 epochs with large displacement (+/- 12.0 mm) outside the baseline stability envelope
    obs = [
        make_obs("o1", "2025-01-01T00:00:00Z", 0.0, coh=0.80),
        make_obs("o2", "2025-01-15T00:00:00Z", -4.0, coh=0.82),
        make_obs("o3", "2025-02-01T00:00:00Z", -8.0, coh=0.85),
        make_obs("o4", "2025-02-15T00:00:00Z", -12.0, coh=0.81),
        make_obs("o5", "2025-03-01T00:00:00Z", -15.0, coh=0.84),
    ]
    assessments = [
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
    ]

    status, transitions = evaluate_temporal_state_machine(obs, assessments)
    assert status == TemporalStatus.CONFLICTED
    assert any("exceeding the baseline stability margin" in t.reason.lower() for t in transitions)


def test_engine_summary_preserves_apparent_acceleration_and_sets_unsupported():
    """Validates TemporalEvidenceSummary preservation of apparent acceleration and support flags."""
    engine = TemporalEvidenceEngine()
    # 6 epochs spanning 45 days with rapid quadratic curving
    obs = [
        make_obs("o1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("o2", "2025-01-10T00:00:00Z", -0.3, coh=0.85),
        make_obs("o3", "2025-01-19T00:00:00Z", -1.2, coh=0.85),
        make_obs("o4", "2025-01-28T00:00:00Z", -2.7, coh=0.85),
        make_obs("o5", "2025-02-06T00:00:00Z", -4.9, coh=0.85),
        make_obs("o6", "2025-02-15T00:00:00Z", -7.6, coh=0.85),
    ]
    assessments = [make_assessment(ConsensusCategory.STRUCTURAL) for _ in range(6)]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_test_accel",
        observations=obs,
        consensus_history=assessments,
    )

    assert summary.apparent_acceleration_mm_per_year2 is not None
    assert summary.apparent_acceleration_mm_per_year2 < -400.0
    assert summary.trend_acceleration_mm_per_year2 == summary.apparent_acceleration_mm_per_year2
    assert summary.acceleration_supported is False
    assert summary.acceleration_support_reason is not None
    assert "short baselines magnify" in summary.acceleration_support_reason.lower()
    assert "a numerical acceleration was calculated" in summary.explanation.lower()
    assert "insufficient to treat it as supported acceleration evidence" in summary.explanation.lower()


# ---------------------------------------------------------------------------
# 4.2 PHASE 6.2 ACCELERATION SEMANTICS & BASELINE GUARD TESTS
# ---------------------------------------------------------------------------

def test_phase6_2_test_a_stable_mathematical_acceleration():
    """Test A: Stable sequence with mathematical apparent acceleration must NOT report supported acceleration."""
    engine = TemporalEvidenceEngine()
    # 10 epochs spanning 180 days with low-amplitude noise within +/- 1.2 mm
    obs = [
        make_obs(f"o{i}", f"2025-0{1 + (i // 2):01d}-{(i % 2) * 14 + 1:02d}T00:00:00Z", disp_mm=(-1.0 if i % 2 == 0 else 0.8), coh=0.85)
        for i in range(10)
    ]
    assessments = [make_assessment(ConsensusCategory.STABLE) for _ in range(10)]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_stable_accel",
        observations=obs,
        consensus_history=assessments,
    )

    assert summary.temporal_status == TemporalStatus.BASELINE
    assert summary.apparent_acceleration_mm_per_year2 is not None
    # Scientific integrity: mathematical acceleration in stable baseline is NOT supported deformation acceleration
    assert summary.acceleration_supported is False
    assert summary.acceleration_support_reason is not None
    assert "nominal baseline stability envelope" in summary.acceleration_support_reason.lower()
    assert "not treated as supported deformation acceleration" in summary.acceleration_support_reason.lower()
    assert "apparent acceleration is mathematically detectable" in summary.explanation.lower()


def test_phase6_2_test_b_short_baseline_accelerating_sequence():
    """Test B: Short baseline (<90d) with large apparent acceleration and disagreement must NOT become BASELINE."""
    engine = TemporalEvidenceEngine()
    # 6 epochs spanning 45 days with rapid curving and large mathematical acceleration
    obs = [
        make_obs("o1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("o2", "2025-01-10T00:00:00Z", -0.5, coh=0.85),
        make_obs("o3", "2025-01-19T00:00:00Z", -1.8, coh=0.85),
        make_obs("o4", "2025-01-28T00:00:00Z", -3.5, coh=0.85),
        make_obs("o5", "2025-02-06T00:00:00Z", -6.0, coh=0.85),
        make_obs("o6", "2025-02-15T00:00:00Z", -9.5, coh=0.85),
    ]
    # Assessments with cross-model disagreement
    assessments = [
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.25, agree=0.10, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
        make_assessment(ConsensusCategory.SEASONAL, conf=0.30, agree=0.15, flags=[ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value]),
        make_assessment(ConsensusCategory.SEASONAL, conf=0.30, agree=0.15, flags=[ConsensusFlag.ENVIRONMENTAL_STRUCTURAL_CONFLICT.value]),
        make_assessment(ConsensusCategory.INSUFFICIENT_EVIDENCE, conf=0.20, agree=0.08, flags=[ConsensusFlag.STRONG_MODEL_DISAGREEMENT.value]),
    ]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_short_accel",
        observations=obs,
        consensus_history=assessments,
    )

    # Acceleration is unsupported due to short baseline
    assert summary.acceleration_supported is False
    # CRITICAL: Unsupported acceleration does NOT imply baseline stability!
    assert summary.temporal_status != TemporalStatus.BASELINE
    assert summary.temporal_status == TemporalStatus.CONFLICTED


def test_phase6_2_test_c_genuine_stable_sequence():
    """Test C: Genuine stable sequence has status BASELINE, persistence 0, and acceleration_supported FALSE."""
    engine = TemporalEvidenceEngine()
    # 8 epochs spanning 140 days with tiny displacements (+/- 0.3 mm)
    obs = [
        make_obs("o1", "2025-01-01T00:00:00Z", 0.1, coh=0.88),
        make_obs("o2", "2025-01-20T00:00:00Z", -0.2, coh=0.87),
        make_obs("o3", "2025-02-10T00:00:00Z", 0.0, coh=0.89),
        make_obs("o4", "2025-03-02T00:00:00Z", 0.2, coh=0.86),
        make_obs("o5", "2025-03-22T00:00:00Z", -0.1, coh=0.88),
        make_obs("o6", "2025-04-11T00:00:00Z", 0.3, coh=0.87),
        make_obs("o7", "2025-05-01T00:00:00Z", -0.2, coh=0.89),
        make_obs("o8", "2025-05-21T00:00:00Z", 0.1, coh=0.88),
    ]
    assessments = [make_assessment(ConsensusCategory.STABLE, conf=0.85) for _ in range(8)]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_genuine_stable",
        observations=obs,
        consensus_history=assessments,
    )

    assert summary.temporal_status == TemporalStatus.BASELINE
    assert summary.persistence_score == 0.0
    assert summary.acceleration_supported is False


def test_phase6_2_test_d_existing_supported_acceleration():
    """Test D: Genuine supported acceleration (satisfies 7 criteria, non-baseline) reports acceleration_supported TRUE."""
    engine = TemporalEvidenceEngine()
    # 6 epochs spanning 180 days with consistent progressive quadratic acceleration reaching -15 mm
    obs = [
        make_obs("obs1", "2025-01-01T00:00:00Z", 0.0, coh=0.85),
        make_obs("obs2", "2025-02-06T00:00:00Z", -0.6, coh=0.85),
        make_obs("obs3", "2025-03-14T00:00:00Z", -2.4, coh=0.85),
        make_obs("obs4", "2025-04-19T00:00:00Z", -5.4, coh=0.85),
        make_obs("obs5", "2025-05-25T00:00:00Z", -9.6, coh=0.85),
        make_obs("obs6", "2025-06-30T00:00:00Z", -15.0, coh=0.85),
    ]
    assessments = [make_assessment(ConsensusCategory.STRUCTURAL, conf=0.88, agree=0.90) for _ in range(6)]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_supported_accel",
        observations=obs,
        consensus_history=assessments,
    )

    assert summary.temporal_status in [TemporalStatus.PERSISTENT, TemporalStatus.EMERGING]
    assert summary.apparent_acceleration_mm_per_year2 is not None
    assert summary.apparent_acceleration_mm_per_year2 < -40.0
    assert summary.acceleration_supported is True
    assert "supported across" in summary.acceleration_support_reason.lower()
    assert "supported by the temporal baseline" in summary.explanation.lower()


# ---------------------------------------------------------------------------
# 5. LEAKAGE FIREWALL & EXPLANATION SAFETY
# ---------------------------------------------------------------------------

def test_temporal_leakage_firewall():
    engine = TemporalEvidenceEngine()
    obs_clean = [make_obs("o1", "2025-01-01T00:00:00Z")]

    with pytest.raises(ValueError, match="Ground-truth leakage firewall violation"):
        engine.evaluate_summary(
            infrastructure_id="infra_1",
            observations=obs_clean,
            true_structural_displacement_mm=4.5,
        )

    with pytest.raises(ValueError, match="Ground-truth leakage firewall violation"):
        engine.evaluate_summary(
            infrastructure_id="infra_1",
            observations=obs_clean,
            ground_truth_class="STRUCTURAL_MONOTONIC",
        )


def test_temporal_explanation_safety():
    engine = TemporalEvidenceEngine()
    obs = [make_obs(f"o{i}", f"2025-01-{i:02d}T00:00:00Z", disp_mm=-float(i)) for i in range(1, 6)]
    assessments = [make_assessment(ConsensusCategory.STRUCTURAL) for _ in range(5)]

    summary = engine.evaluate_summary(
        infrastructure_id="infra_test",
        observations=obs,
        consensus_history=assessments,
    )

    explanation = summary.explanation.lower()
    assert len(explanation) > 50

    forbidden_terms = [
        "structure will collapse",
        "collapse predicted",
        "structure is unsafe",
        "structure is safe",
        "failure confirmed",
        "certified safe",
    ]
    for term in forbidden_terms:
        assert term not in explanation
