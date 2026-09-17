"""
Kinematic trend and apparent acceleration calculations over irregular acquisition baselines.
Uses real elapsed observation timestamps (converted to years) rather than epoch indices.
Explicitly separates mathematically calculated acceleration from scientifically supported acceleration evidence.
"""
from typing import Any, List, Optional, Tuple
import numpy as np

from backend.app.services.temporal.ordering import _get_timestamp

DAYS_PER_YEAR = 365.25

# Basic mathematical calculation constraints
MIN_EPOCHS_FOR_RATE = 3
MIN_EPOCHS_FOR_ACCELERATION = 5
MIN_SPAN_DAYS_FOR_ACCELERATION = 30.0

# Scientific Support Criteria (Documented PROTOTYPE ASSUMPTIONS)
# These thresholds represent engineering prototype assumptions and are not claimed as validated external standards.
MIN_EPOCHS_FOR_SUPPORTED_ACCELERATION = 6  # PROTOTYPE_ASSUMPTION: ensures degrees of freedom (N-3 >= 3)
MIN_SPAN_DAYS_FOR_SUPPORTED_ACCELERATION = 90.0  # PROTOTYPE_ASSUMPTION: prevents (365.25/T)^2 noise explosion
MAX_INTERVAL_FRACTION_FOR_ACCELERATION = 0.70  # PROTOTYPE_ASSUMPTION: ensures observations are not endpoint-clustered
MIN_MEAN_COHERENCE_FOR_ACCELERATION = 0.65  # PROTOTYPE_ASSUMPTION: phase noise below 0.65 degrades 2nd derivatives
MIN_KINEMATIC_AMPLITUDE_MM = 2.0  # PROTOTYPE_ASSUMPTION: below 2.0 mm peak-to-peak is within InSAR noise floor
MAX_RESIDUAL_SCATTER_RATIO = 0.40  # PROTOTYPE_ASSUMPTION: RMSE of fit relative to signal amplitude must not exceed 40%


def _extract_displacement_mm(obs: Any) -> Optional[float]:
    """Extracts observed deformation displacement in mm."""
    val = getattr(obs, "deformation_mm", None)
    if val is None and isinstance(obs, dict):
        val = obs.get("deformation_mm", obs.get("observed_displacement_mm"))
    if val is not None and isinstance(val, (int, float)):
        return float(val)
    return None


def _extract_coherence(obs: Any) -> float:
    """Extracts interferometric coherence, defaulting to 0.80 if unspecified."""
    val = getattr(obs, "coherence", None)
    if val is None and isinstance(obs, dict):
        val = obs.get("coherence")
    if val is not None and isinstance(val, (int, float)):
        return float(val)
    return 0.80


def evaluate_acceleration_support(
    times_years: List[float],
    displacements: List[float],
    coherences: List[float],
    apparent_accel_mm_yr2: Optional[float],
    poly_coeffs: Optional[np.ndarray],
    is_baseline_stability: bool = False,
) -> Tuple[bool, Optional[str]]:
    """
    Evaluates explicit scientific criteria to determine whether a mathematically computed
    apparent acceleration is temporally and physically supported as deformation evidence.

    CRITERIA EVALUATED (All thresholds are PROTOTYPE ASSUMPTIONS):
      0. Baseline Guard: Sequences within nominal baseline stability do not assert supported deformation acceleration.
      1. Observation Count: N >= 6 epochs.
      2. Temporal Coverage: Total baseline >= 90.0 days (~3 months).
      3. Temporal Spacing: Maximum interval gap does not exceed 70% of total span.
      4. Measurement Quality: Mean interferometric coherence >= 0.65.
      5. Kinematic Amplitude: Peak-to-peak displacement >= 2.0 mm (exceeds noise floor).
      6. Trend Consistency: Velocity progression across split halves agrees with acceleration sign.
      7. Residual Scatter: RMSE of quadratic fit relative to displacement amplitude <= 0.40.
    """
    if apparent_accel_mm_yr2 is None or len(times_years) < MIN_EPOCHS_FOR_ACCELERATION:
        return False, "Insufficient observation history to estimate numerical acceleration."

    # 0. Baseline Stability Guard (Phase 6.2)
    if is_baseline_stability:
        return (
            False,
            "Apparent acceleration is mathematically detectable, but the sequence remains within the nominal baseline stability envelope and is not treated as supported deformation acceleration.",
        )

    n_obs = len(times_years)
    total_span_days = (times_years[-1] - times_years[0]) * DAYS_PER_YEAR

    # 1. Observation Count Sufficiency
    if n_obs < MIN_EPOCHS_FOR_SUPPORTED_ACCELERATION:
        return (
            False,
            f"Observation count ({n_obs}) is below prototype threshold "
            f"(>= {MIN_EPOCHS_FOR_SUPPORTED_ACCELERATION} epochs) for supported acceleration evidence.",
        )

    # 2. Temporal Baseline Sufficiency
    if total_span_days < MIN_SPAN_DAYS_FOR_SUPPORTED_ACCELERATION:
        return (
            False,
            f"Temporal baseline ({total_span_days:.1f} days) is below prototype threshold "
            f"(>= {MIN_SPAN_DAYS_FOR_SUPPORTED_ACCELERATION:.1f} days); short baselines magnify annualization error.",
        )

    # 3. Temporal Spacing / Clustering Check
    intervals = [times_years[i + 1] - times_years[i] for i in range(n_obs - 1)]
    max_int_days = max(intervals) * DAYS_PER_YEAR
    if max_int_days > MAX_INTERVAL_FRACTION_FOR_ACCELERATION * total_span_days:
        return (
            False,
            f"Observation spacing is clustered; maximum gap of {max_int_days:.1f} days "
            f"exceeds {MAX_INTERVAL_FRACTION_FOR_ACCELERATION * 100:.0f}% of total baseline.",
        )

    # 4. Measurement Quality (Interferometric Coherence)
    mean_coh = float(np.mean(coherences)) if coherences else 0.80
    if mean_coh < MIN_MEAN_COHERENCE_FOR_ACCELERATION:
        return (
            False,
            f"Mean interferometric coherence ({mean_coh:.2f}) is below prototype quality threshold "
            f"(>= {MIN_MEAN_COHERENCE_FOR_ACCELERATION:.2f}).",
        )

    # 5. Kinematic Amplitude Check
    ptp_disp = float(np.ptp(displacements))
    if ptp_disp < MIN_KINEMATIC_AMPLITUDE_MM:
        return (
            False,
            f"Observed displacement amplitude ({ptp_disp:.2f} mm) is within the nominal noise floor "
            f"(< {MIN_KINEMATIC_AMPLITUDE_MM:.1f} mm).",
        )

    # 6. Trend Consistency / Multi-Rate Progression Check
    mid_idx = n_obs // 2
    t_first, d_first = times_years[: mid_idx + 1], displacements[: mid_idx + 1]
    t_second, d_second = times_years[mid_idx:], displacements[mid_idx:]

    try:
        rate_1 = float(np.polyfit(t_first, d_first, 1)[0])
        rate_2 = float(np.polyfit(t_second, d_second, 1)[0])
        delta_rate = rate_2 - rate_1

        # If rate change sign directly contradicts 2nd-derivative sign and magnitude is non-negligible
        if (delta_rate * apparent_accel_mm_yr2) < 0 and abs(delta_rate) > 1.0:
            return (
                False,
                "Independent interval rate progression contradicts apparent acceleration sign (noisy oscillation).",
            )
    except (np.linalg.LinAlgError, ValueError):
        pass

    # 7. Residual Scatter Check
    if poly_coeffs is not None:
        fitted = np.polyval(poly_coeffs, times_years)
        rmse = float(np.sqrt(np.mean((np.array(displacements) - fitted) ** 2)))
        if ptp_disp > 0 and (rmse / ptp_disp) > MAX_RESIDUAL_SCATTER_RATIO:
            return (
                False,
                f"Residual scatter (RMSE {rmse:.2f} mm) relative to signal amplitude ({ptp_disp:.2f} mm) "
                f"exceeds prototype threshold ({MAX_RESIDUAL_SCATTER_RATIO:.2f}).",
            )

    return (
        True,
        f"Acceleration evidence is supported across {total_span_days:.1f} days "
        f"({n_obs} epochs, mean coherence {mean_coh:.2f}) with consistent deformation-rate change.",
    )


def calculate_temporal_kinematics(
    ordered_observations: List[Any],
    is_baseline_stability: bool = False,
) -> Tuple[Optional[float], Optional[float], bool, Optional[str]]:
    """
    Calculates:
      1. trend_rate_mm_per_year: Linear regression slope over actual elapsed years.
      2. apparent_acceleration_mm_per_year2: 2nd derivative of quadratic fit (2 * a) in mm/year².
      3. acceleration_supported: Whether apparent acceleration satisfies scientific sufficiency criteria.
      4. acceleration_support_reason: Clear scientific justification for support status.

    CRITICAL SCIENTIFIC PRINCIPLES:
      - Uses actual time differences (dt) in years, NOT epoch index differences.
      - Preserves numerical apparent acceleration even if temporal coverage is insufficient.
      - Explicitly flags when short baselines (< 90 days) magnify annualization error.
      - Explicitly flags when sequence is within nominal baseline stability (not deformation acceleration).
      - Values represent observed kinematic trend rates; they do NOT predict collapse
        or assert structural failure probability.
    """
    if len(ordered_observations) < MIN_EPOCHS_FOR_RATE:
        return None, None, False, "Insufficient observations for kinematic rate estimation."

    t0 = _get_timestamp(ordered_observations[0])
    times_years: List[float] = []
    displacements: List[float] = []
    coherences: List[float] = []

    for obs in ordered_observations:
        disp = _extract_displacement_mm(obs)
        if disp is not None:
            t = _get_timestamp(obs)
            delta_years = (t - t0).total_seconds() / (86400.0 * DAYS_PER_YEAR)
            times_years.append(delta_years)
            displacements.append(disp)
            coherences.append(_extract_coherence(obs))

    if len(times_years) < MIN_EPOCHS_FOR_RATE:
        return None, None, False, "Fewer than 3 valid displacement epochs present."

    total_span_days = (times_years[-1] - times_years[0]) * DAYS_PER_YEAR
    if total_span_days <= 1.0:
        return None, None, False, "Time baseline too short (<= 1 day) for meaningful annual rate estimation."

    t_arr = np.array(times_years, dtype=np.float64)
    d_arr = np.array(displacements, dtype=np.float64)

    # 1. Linear rate fit (mm/year)
    t_mean = np.mean(t_arr)
    d_mean = np.mean(d_arr)
    denom = np.sum((t_arr - t_mean) ** 2)
    if denom <= 1e-9:
        rate_mm_yr = 0.0
    else:
        rate_mm_yr = float(np.sum((t_arr - t_mean) * (d_arr - d_mean)) / denom)

    # 2. Apparent acceleration fit (mm/year^2)
    accel_mm_yr2: Optional[float] = None
    poly_coeffs: Optional[np.ndarray] = None
    if (
        len(t_arr) >= MIN_EPOCHS_FOR_ACCELERATION
        and total_span_days >= MIN_SPAN_DAYS_FOR_ACCELERATION
    ):
        try:
            poly_coeffs = np.polyfit(t_arr, d_arr, 2)
            a = poly_coeffs[0]
            accel_mm_yr2 = float(round(2.0 * a, 4))
        except (np.linalg.LinAlgError, ValueError):
            accel_mm_yr2 = None
            poly_coeffs = None

    # 3. Acceleration Support Evaluation
    accel_supported, accel_reason = evaluate_acceleration_support(
        times_years=times_years,
        displacements=displacements,
        coherences=coherences,
        apparent_accel_mm_yr2=accel_mm_yr2,
        poly_coeffs=poly_coeffs,
        is_baseline_stability=is_baseline_stability,
    )

    return round(rate_mm_yr, 4), accel_mm_yr2, accel_supported, accel_reason
