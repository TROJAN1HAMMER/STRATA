"""
Observable Feature Extraction Engine for STRATA InSAR Multi-Epoch Sequences.
CRITICAL CONSTRAINT: Uses ONLY observable InSAR fields (timestamps, displacements,
coherence, phase quality, incidence angles, estimated noise).
Strictly NEVER accesses ground-truth component decomposition or generative parameters.
"""
from datetime import datetime
import math
from typing import Any, Dict, List, Tuple
import numpy as np


OBSERVABLE_FEATURE_NAMES: List[str] = [
    # Static & Geometry Summary
    "epoch_count",
    "duration_days",
    "temporal_spacing_mean_days",
    "temporal_spacing_std_days",
    "incidence_angle_mean_deg",
    "incidence_angle_std_deg",
    # Quality Summary
    "coherence_mean",
    "coherence_std",
    "minimum_coherence",
    "phase_quality_mean",
    "phase_quality_std",
    "noise_estimate_mean_mm",
    # Displacement Amplitude & Distribution
    "mean_displacement_mm",
    "displacement_std_mm",
    "displacement_range_mm",
    "displacement_to_noise_ratio",
    # Step & Transition Dynamics
    "mean_absolute_step_mm",
    "max_absolute_step_mm",
    "max_step_to_range_ratio",
    "sign_change_count",
    "zero_crossing_count",
    "directional_consistency",
    # Kinematic & Temporal Evolution
    "slope_mm_per_year",
    "linear_fit_residual_std_mm",
    "acceleration_mm_per_year2",
    "quadratic_fit_residual_std_mm",
    "temporal_autocorrelation_lag1",
    "approximate_periodicity_indicator",
]


def extract_observable_features(epochs_data: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Extracts purely observable features from an InSAR epoch list.
    Accepts either SyntheticEpoch dicts or standard InSAR observation dicts.
    Ignores any 'ground_truth' key if present.
    """
    if len(epochs_data) < 2:
        raise ValueError(f"Feature extraction requires at least 2 epochs, got {len(epochs_data)}")

    # Extract raw observable timelines
    timestamps: List[datetime] = []
    displacements: List[float] = []
    coherences: List[float] = []
    phase_qualities: List[float] = []
    inc_angles: List[float] = []
    noise_estimates: List[float] = []

    for ep in epochs_data:
        # Timestamp
        ts_val = ep.get("acquisition_timestamp")
        if isinstance(ts_val, str):
            dt = datetime.fromisoformat(ts_val)
        elif isinstance(ts_val, datetime):
            dt = ts_val
        else:
            raise ValueError(f"Invalid timestamp format: {ts_val}")
        timestamps.append(dt)

        # Displacement (observable deformation or los_displacement)
        disp = ep.get("observed_displacement_mm")
        if disp is None:
            disp = ep.get("deformation_mm", 0.0)
        displacements.append(float(disp))

        # Coherence
        coh = ep.get("coherence", 0.5)
        coherences.append(float(coh))

        # Phase quality
        pq = ep.get("phase_quality", 0.5)
        phase_qualities.append(float(pq))

        # Incidence angle
        inc = ep.get("incidence_angle_deg")
        if inc is None:
            inc = ep.get("incidence_angle", 35.0)
        inc_angles.append(float(inc))

        # Noise estimate
        noise = ep.get("noise_estimate_mm")
        if noise is None:
            meta = ep.get("metadata") or ep.get("observation_metadata") or {}
            noise = meta.get("noise_estimate_mm", 1.0)
        noise_estimates.append(float(noise))

    n_epochs = len(timestamps)
    t0 = timestamps[0]
    time_days = np.array([(t - t0).total_seconds() / 86400.0 for t in timestamps], dtype=np.float64)
    time_years = time_days / 365.25
    disp_arr = np.array(displacements, dtype=np.float64)
    coh_arr = np.array(coherences, dtype=np.float64)
    pq_arr = np.array(phase_qualities, dtype=np.float64)
    inc_arr = np.array(inc_angles, dtype=np.float64)
    noise_arr = np.array(noise_estimates, dtype=np.float64)

    # 1. Temporal spacing & duration
    deltas_days = np.diff(time_days)
    total_duration = float(time_days[-1] - time_days[0])
    mean_spacing = float(np.mean(deltas_days)) if len(deltas_days) > 0 else 0.0
    std_spacing = float(np.std(deltas_days)) if len(deltas_days) > 0 else 0.0

    # 2. Geometry & Quality statistics
    inc_mean = float(np.mean(inc_arr))
    inc_std = float(np.std(inc_arr))
    coh_mean = float(np.mean(coh_arr))
    coh_std = float(np.std(coh_arr))
    coh_min = float(np.min(coh_arr))
    pq_mean = float(np.mean(pq_arr))
    pq_std = float(np.std(pq_arr))
    noise_mean = float(np.mean(noise_arr)) if len(noise_arr) > 0 else 1.0

    # 3. Displacement statistics
    disp_mean = float(np.mean(disp_arr))
    disp_std = float(np.std(disp_arr))
    disp_range = float(np.ptp(disp_arr))
    snr_ratio = float(disp_range / (noise_mean if noise_mean > 1e-6 else 1.0))

    # 4. Step dynamics
    disp_steps = np.diff(disp_arr)
    abs_steps = np.abs(disp_steps)
    mean_abs_step = float(np.mean(abs_steps)) if len(abs_steps) > 0 else 0.0
    max_abs_step = float(np.max(abs_steps)) if len(abs_steps) > 0 else 0.0
    max_step_ratio = float(max_abs_step / (disp_range if disp_range > 1e-6 else 1.0))

    # Directional consistency
    if len(disp_steps) > 0:
        pos_steps = np.sum(disp_steps > 0.1)
        neg_steps = np.sum(disp_steps < -0.1)
        dir_consistency = float(max(pos_steps, neg_steps) / len(disp_steps))
    else:
        dir_consistency = 0.0

    # Sign changes of steps
    sign_changes = 0
    for i in range(len(disp_steps) - 1):
        if (disp_steps[i] > 0.05 and disp_steps[i + 1] < -0.05) or (disp_steps[i] < -0.05 and disp_steps[i + 1] > 0.05):
            sign_changes += 1

    # Zero crossings of displacement
    zero_crossings = 0
    for i in range(len(disp_arr) - 1):
        if (disp_arr[i] > 0.0 and disp_arr[i + 1] < 0.0) or (disp_arr[i] < 0.0 and disp_arr[i + 1] > 0.0):
            zero_crossings += 1

    # 5. Kinematic regressions
    # Linear fit: disp = slope * time_years + c
    if total_duration > 0.0 and n_epochs >= 2:
        poly1 = np.polyfit(time_years, disp_arr, 1)
        slope = float(poly1[0])
        pred1 = np.polyval(poly1, time_years)
        res1_std = float(np.std(disp_arr - pred1))
    else:
        slope = 0.0
        res1_std = 0.0

    # Quadratic fit: disp = 0.5 * accel * t^2 + v0 * t + c
    if n_epochs >= 3 and total_duration > 0.0:
        poly2 = np.polyfit(time_years, disp_arr, 2)
        # poly2 = [p0*t^2, p1*t, p2], so 0.5 * accel = poly2[0] => accel = 2.0 * poly2[0]
        accel = float(2.0 * poly2[0])
        pred2 = np.polyval(poly2, time_years)
        res2_std = float(np.std(disp_arr - pred2))
    else:
        accel = 0.0
        res2_std = res1_std

    # 6. Autocorrelation lag-1
    if n_epochs >= 3 and disp_std > 1e-6:
        norm_disp = disp_arr - disp_mean
        auto_cov = np.correlate(norm_disp, norm_disp, mode="full")
        mid = len(norm_disp) - 1
        var = auto_cov[mid]
        lag1 = float(auto_cov[mid + 1] / var) if var > 1e-8 else 0.0
        lag1 = max(-1.0, min(1.0, lag1))
    else:
        lag1 = 0.0

    # 7. Approximate Periodicity Indicator
    # Ratio of residual improvement between linear fit and sinusoidal or zero-crossing frequency
    # We measure cyclicality: combination of regular zero-crossings and bounded linear residual
    if zero_crossings >= 2 and disp_range > 1.0:
        # Bounded amplitude and frequent reversals indicate cyclic/periodic behavior
        cyclic_score = min(1.0, (zero_crossings / (n_epochs / 3.0))) * (1.0 - min(1.0, abs(disp_arr[-1] - disp_arr[0]) / (disp_range + 1e-4)))
        periodicity_indicator = float(max(0.0, min(1.0, cyclic_score)))
    else:
        periodicity_indicator = 0.0

    return {
        "epoch_count": float(n_epochs),
        "duration_days": round(total_duration, 2),
        "temporal_spacing_mean_days": round(mean_spacing, 2),
        "temporal_spacing_std_days": round(std_spacing, 2),
        "incidence_angle_mean_deg": round(inc_mean, 2),
        "incidence_angle_std_deg": round(inc_std, 2),
        "coherence_mean": round(coh_mean, 4),
        "coherence_std": round(coh_std, 4),
        "minimum_coherence": round(coh_min, 4),
        "phase_quality_mean": round(pq_mean, 4),
        "phase_quality_std": round(pq_std, 4),
        "noise_estimate_mean_mm": round(noise_mean, 3),
        "mean_displacement_mm": round(disp_mean, 4),
        "displacement_std_mm": round(disp_std, 4),
        "displacement_range_mm": round(disp_range, 4),
        "displacement_to_noise_ratio": round(snr_ratio, 3),
        "mean_absolute_step_mm": round(mean_abs_step, 4),
        "max_absolute_step_mm": round(max_abs_step, 4),
        "max_step_to_range_ratio": round(max_step_ratio, 4),
        "sign_change_count": float(sign_changes),
        "zero_crossing_count": float(zero_crossings),
        "directional_consistency": round(dir_consistency, 4),
        "slope_mm_per_year": round(slope, 4),
        "linear_fit_residual_std_mm": round(res1_std, 4),
        "acceleration_mm_per_year2": round(accel, 4),
        "quadratic_fit_residual_std_mm": round(res2_std, 4),
        "temporal_autocorrelation_lag1": round(lag1, 4),
        "approximate_periodicity_indicator": round(periodicity_indicator, 4),
    }
