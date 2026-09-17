"""
Configurable prototype parameter distributions for synthetic multi-epoch InSAR generation.
All ranges here represent explicitly parameterized PROTOTYPE_ASSUMPTIONS for algorithm development.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class ParameterRange:
    min_val: float
    max_val: float

    def clamp(self, val: float) -> float:
        return max(self.min_val, min(self.max_val, val))


@dataclass
class DatasetConfig:
    """
    Centralized configuration structure for synthetic InSAR sequence parameters.
    No magic numbers scattered across generator modules.
    """
    # Temporal sampling
    epoch_count_range: Tuple[int, int] = (6, 20)
    temporal_spacing_days_range: Tuple[float, float] = (6.0, 24.0)

    # Radar Geometry & Measurement Quality
    incidence_angle_deg_range: Tuple[float, float] = (25.0, 45.0)
    nominal_coherence_range: Tuple[float, float] = (0.65, 0.95)
    degraded_coherence_range: Tuple[float, float] = (0.10, 0.24)
    nominal_phase_quality_range: Tuple[float, float] = (0.70, 0.95)
    degraded_phase_quality_range: Tuple[float, float] = (0.10, 0.25)
    measurement_noise_scale_range: Tuple[float, float] = (0.5, 3.0)  # standard deviation in mm

    # Structural Monotonic Deformation
    monotonic_velocity_mm_yr_range: Tuple[float, float] = (0.8, 12.0)

    # Structural Accelerating Deformation
    accelerating_initial_velocity_mm_yr_range: Tuple[float, float] = (0.5, 5.0)
    acceleration_mm_yr2_range: Tuple[float, float] = (0.8, 8.0)

    # Seasonal / Environmental Cycle
    seasonal_amplitude_mm_range: Tuple[float, float] = (2.0, 10.0)
    seasonal_period_days_range: Tuple[float, float] = (180.0, 365.25)

    # Atmospheric Phase Screen (APS) / Tropospheric Turbulence
    atmospheric_transient_magnitude_mm_range: Tuple[float, float] = (3.0, 15.0)
    atmospheric_transient_duration_epochs: int = 1  # 1-2 consecutive epochs

    # Split allocations
    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15

    # Documentation of prototype assumptions
    prototype_assumptions: List[str] = field(default_factory=lambda: [
        "Synthetic displacements follow linear superposition: observed = physical + atmospheric + noise.",
        "Monotonic structural deformation rate is modeled as constant velocity: d(t) = v * t.",
        "Accelerating deformation follows quadratic kinematic model: d(t) = v0 * t + 0.5 * a * t^2.",
        "Seasonal deformation is modeled as single-harmonic sinusoidal thermal response: d(t) = A * sin(2*pi*t / T + phi).",
        "Atmospheric transients represent isolated non-persistent tropospheric turbulence spikes.",
        "Temporal spacing approximates Sentinel-1 constellation orbits (6 to 24-day repeat baselines).",
        "Incidence angles represent typical C-band satellite configurations (25° to 45°).",
        "Parameter distributions are experimental prototype assumptions and NOT calibrated against specific ground truth sites."
    ])


PROTOTYPE_ASSUMPTIONS = DatasetConfig()
