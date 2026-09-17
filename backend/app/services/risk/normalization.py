"""
Evidence normalization and baseline deviation calculations for Phase 7 Risk Characterization.
Strictly enforces the programmatic ground-truth leakage firewall.
Decomposes raw multi-epoch observations and temporal evidence into transparent,
bounded [0.0, 1.0] components.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from backend.app.schemas.risk import (
    CalibrationProfile,
    CriticalZone,
    EvidenceComponents,
    ExpectedDeformationBehavior,
    HistoricalBaseline,
)
from backend.app.schemas.temporal import TemporalEvidenceSummary, TemporalStatus

# Programmatic Leakage Firewall Keywords
FORBIDDEN_GROUND_TRUTH_KEYS = {
    "ground_truth_class",
    "true_structural_displacement_mm",
    "true_environmental_displacement_mm",
    "true_atmospheric_displacement_mm",
    "true_noise_mm",
    "seasonal_amplitude_mm",
    "seasonal_period_days",
    "linear_velocity_mm_yr",
    "acceleration_mm_yr2",
    "step_epoch_idx",
    "step_magnitude_mm",
    "noise_std_mm",
    "spatial_wavelength_m",
    "spike_magnitude_mm",
}


import enum

def _verify_risk_leakage(obj: Any, path: str = "root") -> None:
    """Recursively validates that synthetic generator attributes do not leak into risk evaluation."""
    if obj is None or isinstance(obj, (str, int, float, bool, bytes, enum.Enum)):
        return

    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k) in FORBIDDEN_GROUND_TRUTH_KEYS:
                raise ValueError(
                    f"Programmatic Leakage Firewall Violation: Forbidden synthetic ground truth key '{k}' "
                    f"detected at path '{path}.{k}' during risk characterization."
                )
            _verify_risk_leakage(v, path=f"{path}.{k}")
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _verify_risk_leakage(item, path=f"{path}[{idx}]")
    elif hasattr(obj, "__dict__"):
        for k, v in vars(obj).items():
            if k.startswith("_"):
                continue
            if k in FORBIDDEN_GROUND_TRUTH_KEYS:
                raise ValueError(
                    f"Programmatic Leakage Firewall Violation: Forbidden synthetic ground truth key '{k}' "
                    f"detected at path '{path}.{k}' during risk characterization."
                )
            if isinstance(v, (dict, list)):
                _verify_risk_leakage(v, path=f"{path}.{k}")



def calculate_evidence_components(
    temporal_summary: TemporalEvidenceSummary,
    calibration_profile: CalibrationProfile,
    historical_baseline: Optional[HistoricalBaseline] = None,
    critical_zones: Optional[List[CriticalZone]] = None,
    expected_behavior: Optional[List[ExpectedDeformationBehavior]] = None,
    recent_observations: Optional[List[Any]] = None,
) -> EvidenceComponents:
    """
    Normalizes multi-epoch InSAR consensus and temporal metrics into interpretable components.
    
    CRITICAL PRINCIPLE:
    - If acceleration_supported is False, acceleration_support is strictly 0.0.
    - If environmental pattern is detected, environmental_suppression is fully active.
    - Critical zone context modulates importance only when evidence exists, never manufacturing risk.
    """
    # 1. Measurement Quality [0.0 - 1.0]
    qs = temporal_summary.quality_summary or {}
    mean_coh = float(qs.get("mean_coherence", 0.80))
    mean_phase_q = float(qs.get("mean_phase_quality", 0.80))
    missing_ep = temporal_summary.missing_epoch_count
    quality_penalty = min(0.40, 0.05 * missing_ep)
    quality_score = float(np.clip((0.6 * mean_coh + 0.4 * mean_phase_q) * (1.0 - quality_penalty), 0.0, 1.0))

    # 2. Consensus Support [0.0 - 1.0]
    agree_hist = temporal_summary.agreement_history or []
    conf_traj = [p.confidence for p in temporal_summary.confidence_trajectory] if temporal_summary.confidence_trajectory else []
    mean_agr = float(np.mean(agree_hist)) if agree_hist else 0.5
    mean_cnf = float(np.mean(conf_traj)) if conf_traj else temporal_summary.mean_confidence
    consensus_score = float(np.clip(0.6 * mean_agr + 0.4 * mean_cnf, 0.0, 1.0))

    # 3. Temporal Persistence [0.0 - 1.0]
    persistence_score = float(np.clip(temporal_summary.persistence_score, 0.0, 1.0))

    # 4. Trend Significance [0.0 - 1.0]
    ref_range = max(1.0, calibration_profile.deformation_reference_range_mm)
    if temporal_summary.trend_rate_mm_per_year is not None:
        raw_trend = abs(temporal_summary.trend_rate_mm_per_year)
        trend_score = float(np.clip(raw_trend / ref_range, 0.0, 1.0))
    else:
        trend_score = 0.0

    # 5. Acceleration Support [0.0 - 1.0]
    # STRICT SCIENTIFIC RULE: Unsupported acceleration is NEVER treated as supported acceleration evidence
    if temporal_summary.acceleration_supported and temporal_summary.apparent_acceleration_mm_per_year2 is not None:
        raw_accel = abs(temporal_summary.apparent_acceleration_mm_per_year2)
        # Scaled relative to prototype reference curvature limit (5 * reference displacement range)
        accel_ref = max(5.0, 5.0 * ref_range)
        accel_score = float(np.clip(raw_accel / accel_ref, 0.0, 1.0))
    else:
        accel_score = 0.0

    # 6. Environmental Suppression [0.0 - 1.0]
    if temporal_summary.temporal_status == TemporalStatus.ENVIRONMENTAL_PATTERN:
        env_suppression = 1.0
    elif temporal_summary.environmental_pattern_count >= 2 and temporal_summary.temporal_status != TemporalStatus.CONFLICTED:
        env_suppression = float(np.clip(0.35 * temporal_summary.environmental_pattern_count, 0.0, 1.0))
    elif expected_behavior and ExpectedDeformationBehavior.SEASONAL in expected_behavior:
        # Known seasonal asset suppresses structural escalation for cyclical movements
        env_suppression = 0.50 if temporal_summary.environmental_pattern_count >= 1 else 0.0
    else:
        env_suppression = 0.0

    # 7. Critical Zone Context [1.0 - 2.0]
    cz_context = 1.0
    if critical_zones:
        max_zone_weight = max((z.importance_weight for z in critical_zones), default=1.0)
        # Contextual boost applies only if structural persistence or trend significance exists
        if persistence_score > 0.20 or trend_score > 0.20:
            cz_context = float(np.clip(1.0 + 0.25 * (max_zone_weight - 1.0) + 0.15, 1.0, 1.5))

    # 8. Baseline Deviation & Standardized Z-Score
    base_dev_mm: Optional[float] = None
    base_z: Optional[float] = None

    recent_disp: Optional[float] = None
    if recent_observations:
        disps = []
        for o in recent_observations:
            d = getattr(o, "deformation_mm", None)
            if d is None and isinstance(o, dict):
                d = o.get("deformation_mm", o.get("observed_displacement_mm"))
            if d is not None:
                disps.append(float(d))
        if disps:
            # Use median of the most recent window (up to 3 epochs) to resist single-epoch noise
            recent_disp = float(np.median(disps[-3:]))

    if historical_baseline is not None and recent_disp is not None:
        base_dev_mm = float(round(recent_disp - historical_baseline.baseline_mean_mm, 3))
        # Z-score requires adequate baseline standard deviation and observation count (>= 5)
        obs_count = historical_baseline.baseline_observation_count or 0
        if historical_baseline.baseline_std_mm > 0.05 and obs_count >= 5:
            base_z = float(round(base_dev_mm / historical_baseline.baseline_std_mm, 2))

    return EvidenceComponents(
        measurement_quality=round(quality_score, 4),
        consensus_support=round(consensus_score, 4),
        temporal_persistence=round(persistence_score, 4),
        trend_significance=round(trend_score, 4),
        acceleration_support=round(accel_score, 4),
        environmental_suppression=round(env_suppression, 4),
        critical_zone_context=round(cz_context, 4),
        baseline_deviation_mm=base_dev_mm,
        baseline_z_score=base_z,
    )
