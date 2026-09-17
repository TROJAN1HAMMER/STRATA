"""
Unified Feature Pipeline and Allowlist Enforcement for STRATA ML Deformation Classifier.
Guarantees strict separation between observable InSAR fields and forbidden ground-truth fields.
"""
from typing import Any, Dict, List, Set, Union
import numpy as np
import pandas as pd

from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.synthetic import SyntheticSequenceSample
from backend.app.services.synthetic.feature_extractor import extract_observable_features


FEATURE_SCHEMA_VERSION = "v1.0.0"

# Explicit Feature Groupings
FEATURE_GROUP_A_QUALITY: List[str] = [
    "coherence_mean",
    "coherence_std",
    "minimum_coherence",
    "phase_quality_mean",
    "phase_quality_std",
    "noise_estimate_mean_mm",
]

FEATURE_GROUP_B_DISPLACEMENT: List[str] = [
    "mean_displacement_mm",
    "displacement_std_mm",
    "displacement_range_mm",
    "displacement_to_noise_ratio",
    "mean_absolute_step_mm",
    "max_absolute_step_mm",
    "max_step_to_range_ratio",
]

FEATURE_GROUP_C_TEMPORAL_KINEMATIC: List[str] = [
    "slope_mm_per_year",
    "linear_fit_residual_std_mm",
    "acceleration_mm_per_year2",
    "quadratic_fit_residual_std_mm",
    "directional_consistency",
    "sign_change_count",
    "temporal_autocorrelation_lag1",
]

FEATURE_GROUP_D_PERIODICITY: List[str] = [
    "zero_crossing_count",
    "approximate_periodicity_indicator",
]

FEATURE_GROUP_E_GEOMETRY: List[str] = [
    "epoch_count",
    "duration_days",
    "temporal_spacing_mean_days",
    "temporal_spacing_std_days",
    "incidence_angle_mean_deg",
    "incidence_angle_std_deg",
]

# Complete Approved Allowlist (ordered deterministically)
FEATURE_ALLOWLIST: List[str] = (
    FEATURE_GROUP_A_QUALITY
    + FEATURE_GROUP_B_DISPLACEMENT
    + FEATURE_GROUP_C_TEMPORAL_KINEMATIC
    + FEATURE_GROUP_D_PERIODICITY
    + FEATURE_GROUP_E_GEOMETRY
)

# Strict Forbidden Columns (ground-truth, generative parameters, physics engine outputs)
FORBIDDEN_COLUMNS: Set[str] = {
    "true_structural_displacement_mm",
    "true_environmental_displacement_mm",
    "true_atmospheric_displacement_mm",
    "true_noise_mm",
    "ground_truth_class",
    "ground_truth",
    "scenario",
    "parameters",
    "random_seed",
    "is_edge_case",
    "edge_case_type",
    "physics_classification",
    "physics_confidence",
    "overall_confidence",
}


def validate_feature_dataframe(df: pd.DataFrame, is_training: bool = True) -> None:
    """
    Strictly audits a feature DataFrame before ingestion into training or inference.
    Fails loudly with ValueError if:
    - Any forbidden ground truth or parameter column is present among feature columns.
    - Any required allowlisted feature is missing.
    - Any NaN or Inf values are detected.
    """
    # Verify allowlist itself is strictly pure
    allowlist_leak = FORBIDDEN_COLUMNS.intersection(set(FEATURE_ALLOWLIST))
    if allowlist_leak:
        raise ValueError(f"CRITICAL LEAKAGE: FEATURE_ALLOWLIST contains forbidden columns: {allowlist_leak}")

    # Exclude non-feature row metadata that may legitimately accompany rows (sample_id, target_label, audit tags)
    exempt_cols = {"sample_id", "target_label", "is_edge_case", "edge_case_type"}
    feature_cols = [c for c in df.columns if c not in exempt_cols]

    # Check for forbidden columns in feature columns
    leaked_cols = FORBIDDEN_COLUMNS.intersection(set(feature_cols))
    if leaked_cols:
        raise ValueError(
            f"CRITICAL DATA LEAKAGE: Forbidden ground-truth columns detected in feature matrix: {sorted(list(leaked_cols))}"
        )


    # Check allowlist coverage
    missing_features = [f for f in FEATURE_ALLOWLIST if f not in df.columns]
    if missing_features:
        raise ValueError(f"Missing required allowlisted features: {missing_features}")

    # Check for NaN / Inf
    sub_df = df[FEATURE_ALLOWLIST]
    if sub_df.isna().any().any():
        nan_cols = sub_df.columns[sub_df.isna().any()].tolist()
        raise ValueError(f"NaN values detected in features: {nan_cols}")

    if np.isinf(sub_df.to_numpy()).any():
        raise ValueError("Infinite values detected in features")


def extract_features_from_sequence(
    sequence: Union[ObservationSequence, SyntheticSequenceSample, List[ObservationRead], List[Dict[str, Any]]]
) -> Dict[str, float]:
    """
    Transforms any raw InSAR sequence into the approved observable feature dictionary.
    Guarantees strict exclusion of all ground-truth fields.
    """
    if isinstance(sequence, ObservationSequence):
        epochs_data = []
        for idx, obs in enumerate(sequence.observations):
            meta = getattr(obs, "metadata", None) or getattr(obs, "observation_metadata", None) or {}
            epochs_data.append({
                "epoch_id": idx,
                "acquisition_timestamp": obs.acquisition_timestamp.isoformat(),
                "observed_displacement_mm": obs.deformation_mm if obs.deformation_mm is not None else 0.0,
                "coherence": obs.coherence if obs.coherence is not None else 0.5,
                "phase_quality": obs.phase_quality if obs.phase_quality is not None else 0.5,
                "incidence_angle_deg": obs.incidence_angle if obs.incidence_angle is not None else 35.0,
                "noise_estimate_mm": meta.get("noise_estimate_mm", 1.0),
            })
    elif isinstance(sequence, SyntheticSequenceSample):
        epochs_data = [
            {
                "epoch_id": ep.epoch_id,
                "acquisition_timestamp": ep.acquisition_timestamp,
                "observed_displacement_mm": ep.observed_displacement_mm,
                "coherence": ep.coherence,
                "phase_quality": ep.phase_quality,
                "incidence_angle_deg": ep.incidence_angle_deg,
                "noise_estimate_mm": ep.noise_estimate_mm,
            }
            for ep in sequence.epochs
        ]
    elif isinstance(sequence, list) and sequence and isinstance(sequence[0], ObservationRead):
        epochs_data = []
        for idx, obs in enumerate(sequence):
            meta = getattr(obs, "metadata", None) or getattr(obs, "observation_metadata", None) or {}
            epochs_data.append({
                "epoch_id": idx,
                "acquisition_timestamp": obs.acquisition_timestamp.isoformat(),
                "observed_displacement_mm": obs.deformation_mm if obs.deformation_mm is not None else 0.0,
                "coherence": obs.coherence if obs.coherence is not None else 0.5,
                "phase_quality": obs.phase_quality if obs.phase_quality is not None else 0.5,
                "incidence_angle_deg": obs.incidence_angle if obs.incidence_angle is not None else 35.0,
                "noise_estimate_mm": meta.get("noise_estimate_mm", 1.0),
            })

    elif isinstance(sequence, list) and sequence and isinstance(sequence[0], dict):
        epochs_data = sequence
    else:
        raise ValueError(f"Unsupported sequence type for feature extraction: {type(sequence)}")

    extracted = extract_observable_features(epochs_data)

    # Return strictly allowlisted features in consistent deterministic order
    return {k: extracted[k] for k in FEATURE_ALLOWLIST}
