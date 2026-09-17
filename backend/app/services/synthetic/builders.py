"""
Parameterized scenario builders for generating synthetic InSAR multi-epoch sequences.
Every builder produces explicit ground truth decomposition matching:
    observed_displacement_mm = (
        true_structural_displacement_mm
        + true_environmental_displacement_mm
        + true_atmospheric_displacement_mm
        + true_noise_mm
    )
"""
import math
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.schemas.synthetic import (
    EpochGroundTruthDecomposition,
    GroundTruthClass,
    SyntheticEpoch,
    SyntheticSequenceSample,
)
from backend.app.services.synthetic.parameters import DatasetConfig, PROTOTYPE_ASSUMPTIONS


def _sample_range(rng: random.Random, r: Tuple[float, float]) -> float:
    return rng.uniform(r[0], r[1])


def _sample_int_range(rng: random.Random, r: Tuple[int, int]) -> int:
    return rng.randint(r[0], r[1])


def _build_timestamps(
    start_date: datetime,
    epoch_count: int,
    spacing_days: float,
    jitter_days: float = 0.5,
    rng: Optional[random.Random] = None,
) -> List[datetime]:
    timestamps: List[datetime] = []
    current_dt = start_date
    timestamps.append(current_dt)
    for i in range(1, epoch_count):
        jitter = rng.uniform(-jitter_days, jitter_days) if rng else 0.0
        delta_days = max(1.0, spacing_days + jitter)
        current_dt = current_dt + timedelta(days=delta_days)
        timestamps.append(current_dt)
    return timestamps


def generate_stable_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a STABLE infrastructure sequence where physical deformation is zero.
    Observations consist solely of zero-mean instrument measurement noise.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    # Edge cases: short sequence or elevated noise
    if is_edge_case and edge_case_type == "short_sequence":
        n_epochs = 6
    elif is_edge_case and edge_case_type == "elevated_noise_stable":
        noise_std = config.measurement_noise_scale_range[1]

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        noise = round(rng.gauss(0.0, noise_std), 4)
        struct = 0.0
        env = 0.0
        atm = 0.0
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, config.nominal_coherence_range), 4)
        phase_q = round(_sample_range(rng, config.nominal_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator="CLEAR_NOMINAL",
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="STABLE_NOMINAL",
        ground_truth_class=GroundTruthClass.STABLE,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_structural_monotonic_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a STRUCTURAL_MONOTONIC sequence.
    Deformation follows linear kinematics: d_struct(t) = v * t.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    # Direction: 75% settlement (subsidence), 25% uplift
    direction = -1.0 if rng.random() < 0.75 else 1.0
    velocity = _sample_range(rng, config.monotonic_velocity_mm_yr_range) * direction

    coh_range = config.nominal_coherence_range
    phase_q_range = config.nominal_phase_quality_range
    atm_spike_epoch = -1
    atm_spike_mag = 0.0

    if is_edge_case:
        if edge_case_type == "weak_structural_near_noise":
            # Very slow deformation near noise floor (~0.5 - 1.0 mm/yr)
            velocity = direction * rng.uniform(0.5, 1.0)
            noise_std = rng.uniform(1.0, 2.0)
        elif edge_case_type == "low_coherence_structural":
            coh_range = (0.28, 0.45)
            phase_q_range = (0.30, 0.50)
        elif edge_case_type == "structural_with_atmospheric_spike":
            atm_spike_epoch = rng.randint(1, n_epochs - 2)
            atm_spike_mag = round(rng.choice([-1.0, 1.0]) * _sample_range(rng, config.atmospheric_transient_magnitude_mm_range), 4)
        elif edge_case_type == "noise_reversal_edge":
            # Moderate deformation where a noisy epoch temporarily reverses apparent direction
            velocity = direction * rng.uniform(1.2, 2.5)
            noise_std = rng.uniform(1.5, 2.5)
        elif edge_case_type == "short_sequence":
            n_epochs = 6

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        days_from_start = (dt - start_date).total_seconds() / 86400.0
        t_years = days_from_start / 365.25

        struct = round(velocity * t_years, 4)
        env = 0.0
        atm = atm_spike_mag if idx == atm_spike_epoch else 0.0
        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, coh_range), 4)
        phase_q = round(_sample_range(rng, phase_q_range), 4)
        indicator = "HIGH_TROPOSPHERIC_TURBULENCE" if idx == atm_spike_epoch else "CLEAR_STABLE"

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator=indicator,
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="STRUCTURAL_MONOTONIC",
        ground_truth_class=GroundTruthClass.STRUCTURAL_MONOTONIC,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "velocity_mm_yr": round(velocity, 3),
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_structural_accelerating_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a STRUCTURAL_ACCELERATING sequence.
    Deformation follows quadratic kinematics: d_struct(t) = v0 * t + 0.5 * a * t^2.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    direction = -1.0 if rng.random() < 0.80 else 1.0
    v0 = _sample_range(rng, config.accelerating_initial_velocity_mm_yr_range) * direction
    accel = _sample_range(rng, config.acceleration_mm_yr2_range) * direction

    if is_edge_case:
        if edge_case_type == "accelerating_moderate_noise":
            noise_std = rng.uniform(2.0, 3.2)
        elif edge_case_type == "accelerating_subtle_onset":
            v0 = 0.2 * direction
            accel = rng.uniform(1.0, 2.5) * direction
        elif edge_case_type == "short_sequence":
            n_epochs = 6

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        days_from_start = (dt - start_date).total_seconds() / 86400.0
        t_years = days_from_start / 365.25

        struct = round(v0 * t_years + 0.5 * accel * (t_years ** 2), 4)
        env = 0.0
        atm = 0.0
        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, config.nominal_coherence_range), 4)
        phase_q = round(_sample_range(rng, config.nominal_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator="CLEAR_STABLE",
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="STRUCTURAL_ACCELERATING",
        ground_truth_class=GroundTruthClass.STRUCTURAL_ACCELERATING,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "initial_velocity_mm_yr": round(v0, 3),
            "acceleration_mm_yr2": round(accel, 3),
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_seasonal_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a SEASONAL_ENVIRONMENTAL sequence.
    Physical deformation is purely cyclic: d_env(t) = A * sin(2*pi*t / T + phi).
    Zero net structural damage.
    """
    # Seasonal patterns benefit from longer observations (10-24 epochs)
    n_epochs = epoch_count or rng.randint(10, max(12, config.epoch_count_range[1] + 4))
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    amplitude = _sample_range(rng, config.seasonal_amplitude_mm_range)
    period_days = _sample_range(rng, config.seasonal_period_days_range)
    phase = rng.uniform(0.0, 2.0 * math.pi)

    if is_edge_case:
        if edge_case_type == "strong_seasonal_amplitude":
            amplitude = rng.uniform(9.0, 15.0)
        elif edge_case_type == "seasonal_with_high_noise":
            noise_std = rng.uniform(2.5, 3.5)
        elif edge_case_type == "short_seasonal_sequence":
            n_epochs = 8

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        days_from_start = (dt - start_date).total_seconds() / 86400.0
        env = round(amplitude * math.sin((2.0 * math.pi * days_from_start / period_days) + phase), 4)
        struct = 0.0
        atm = 0.0
        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, config.nominal_coherence_range), 4)
        phase_q = round(_sample_range(rng, config.nominal_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator="CLEAR_NOMINAL",
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="SEASONAL_ENVIRONMENTAL",
        ground_truth_class=GroundTruthClass.SEASONAL_ENVIRONMENTAL,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "amplitude_mm": round(amplitude, 3),
            "period_days": round(period_days, 1),
            "phase_rad": round(phase, 3),
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_atmospheric_transient_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates an ATMOSPHERIC_TRANSIENT sequence.
    Physical deformation is zero; one or two isolated epochs suffer severe
    tropospheric delay / phase screen spikes that immediately revert to baseline.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    # 1 or 2 isolated spikes
    spike_count = 1 if rng.random() < 0.65 else 2
    spike_candidates = list(range(1, n_epochs - 1))
    spike_epochs = set(rng.sample(spike_candidates, min(spike_count, len(spike_candidates))))

    coh_range = config.nominal_coherence_range
    if is_edge_case and edge_case_type == "high_coherence_atmospheric":
        # High coherence can fool naive filters into thinking spike is structural
        coh_range = (0.88, 0.98)

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        struct = 0.0
        env = 0.0
        if idx in spike_epochs:
            sign = rng.choice([-1.0, 1.0])
            mag = _sample_range(rng, config.atmospheric_transient_magnitude_mm_range)
            atm = round(sign * mag, 4)
            indicator = "HIGH_TROPOSPHERIC_TURBULENCE"
        else:
            atm = 0.0
            indicator = "CLEAR_NOMINAL"

        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, coh_range), 4)
        phase_q = round(_sample_range(rng, config.nominal_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator=indicator,
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="ATMOSPHERIC_TRANSIENT",
        ground_truth_class=GroundTruthClass.ATMOSPHERIC_TRANSIENT,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "spike_epochs": sorted(list(spike_epochs)),
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_low_quality_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a LOW_QUALITY sequence.
    Dominated by temporal radar decorrelation, coherence < 0.25, and elevated phase noise.
    No reliable physical signal can be inferred.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = rng.uniform(2.5, 5.0)

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    for idx, dt in enumerate(timestamps):
        struct = 0.0
        env = 0.0
        atm = 0.0
        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, config.degraded_coherence_range), 4)
        phase_q = round(_sample_range(rng, config.degraded_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator="APS_DATA_UNAVAILABLE",
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="LOW_QUALITY_DECORRELATED",
        ground_truth_class=GroundTruthClass.LOW_QUALITY,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )


def generate_temporally_inconsistent_sequence(
    sample_id: str,
    rng: random.Random,
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
    is_edge_case: bool = False,
    edge_case_type: Optional[str] = None,
    epoch_count: Optional[int] = None,
) -> SyntheticSequenceSample:
    """
    Generates a TEMPORALLY_INCONSISTENT sequence.
    Contains irregular abrupt displacement jumps and alternating reversals
    that cannot be modeled by monotonic, accelerating, or cyclic physical mechanisms.
    """
    n_epochs = epoch_count or _sample_int_range(rng, config.epoch_count_range)
    spacing_days = _sample_range(rng, config.temporal_spacing_days_range)
    inc_angle = _sample_range(rng, config.incidence_angle_deg_range)
    noise_std = _sample_range(rng, config.measurement_noise_scale_range)

    start_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    timestamps = _build_timestamps(start_date, n_epochs, spacing_days, rng=rng)

    epochs: List[SyntheticEpoch] = []
    cos_inc = math.cos(math.radians(inc_angle))

    # Generate erratic jumps: alternating large positive and negative step shifts
    current_displacement = 0.0
    for idx, dt in enumerate(timestamps):
        if idx > 0:
            # Abrupt jump between -6 and +6 mm with high probability of sign inversion
            step = rng.uniform(3.0, 7.5) * (1.0 if (idx % 2 == 1) else -1.0)
            current_displacement += step

        # Model the erratic jump in the structural trajectory
        struct = round(current_displacement, 4)
        env = 0.0
        atm = 0.0
        noise = round(rng.gauss(0.0, noise_std), 4)
        observed = round(struct + env + atm + noise, 4)
        los = round(observed * cos_inc, 4)
        coh = round(_sample_range(rng, config.nominal_coherence_range), 4)
        phase_q = round(_sample_range(rng, config.nominal_phase_quality_range), 4)

        epochs.append(
            SyntheticEpoch(
                epoch_id=idx,
                acquisition_timestamp=dt.isoformat(),
                observed_displacement_mm=observed,
                los_displacement_mm=los,
                coherence=coh,
                incidence_angle_deg=round(inc_angle, 2),
                noise_estimate_mm=round(noise_std, 3),
                phase_quality=phase_q,
                atmospheric_indicator="CLEAR_NOMINAL",
                ground_truth=EpochGroundTruthDecomposition(
                    true_structural_displacement_mm=struct,
                    true_environmental_displacement_mm=env,
                    true_atmospheric_displacement_mm=atm,
                    true_noise_mm=noise,
                ),
            )
        )

    return SyntheticSequenceSample(
        sample_id=sample_id,
        scenario="TEMPORALLY_INCONSISTENT",
        ground_truth_class=GroundTruthClass.TEMPORALLY_INCONSISTENT,
        random_seed=rng.randint(0, 1000000),
        epoch_count=n_epochs,
        start_date=start_date.isoformat(),
        temporal_spacing_days=round(spacing_days, 2),
        parameters={
            "noise_std_mm": round(noise_std, 3),
            "incidence_angle_deg": round(inc_angle, 2),
        },
        is_edge_case=is_edge_case,
        edge_case_type=edge_case_type,
        epochs=epochs,
    )
