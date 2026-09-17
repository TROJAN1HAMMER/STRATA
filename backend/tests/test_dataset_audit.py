import math
import os
import numpy as np
import pandas as pd
import pytest


from backend.app.schemas.synthetic import (
    GroundTruthClass,
    SyntheticSequenceSample,
)
from backend.app.services.synthetic.builders import (
    generate_stable_sequence,
    generate_structural_monotonic_sequence,
)
from backend.app.services.synthetic.feature_extractor import (
    OBSERVABLE_FEATURE_NAMES,
    extract_observable_features,
)
import random

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
AUDIT_DIR = os.path.join(repo_root, "data", "synthetic", "audit")


def test_feature_extraction_observable_keys():
    """Verify feature extractor produces all expected observable keys and no ground truth keys."""
    rng = random.Random(42)
    sample = generate_structural_monotonic_sequence("TEST_FEAT", rng)

    epochs_raw = [
        {
            "epoch_id": ep.epoch_id,
            "acquisition_timestamp": ep.acquisition_timestamp,
            "observed_displacement_mm": ep.observed_displacement_mm,
            "coherence": ep.coherence,
            "incidence_angle_deg": ep.incidence_angle_deg,
            "noise_estimate_mm": ep.noise_estimate_mm,
            "phase_quality": ep.phase_quality,
            # Deliberately include ground_truth to verify it is ignored
            "ground_truth": ep.ground_truth.model_dump(),
        }
        for ep in sample.epochs
    ]

    features = extract_observable_features(epochs_raw)

    # Check all expected features present
    for fname in OBSERVABLE_FEATURE_NAMES:
        assert fname in features, f"Missing feature {fname}"
        val = features[fname]
        assert not math.isnan(val), f"Feature {fname} is NaN"
        assert not math.isinf(val), f"Feature {fname} is Inf"

    # Strict check: No ground-truth fields allowed in extracted features
    forbidden_keys = [
        "true_structural_displacement_mm",
        "true_environmental_displacement_mm",
        "true_atmospheric_displacement_mm",
        "true_noise_mm",
        "ground_truth",
        "ground_truth_class",
        "parameters",
    ]
    for fkey in forbidden_keys:
        assert fkey not in features, f"Forbidden ground truth key leaked: {fkey}"


def test_feature_extraction_determinism():
    """Verify feature extraction is strictly deterministic given the same inputs."""
    rng = random.Random(101)
    sample = generate_stable_sequence("TEST_DET", rng)
    epochs_raw = [
        {
            "epoch_id": ep.epoch_id,
            "acquisition_timestamp": ep.acquisition_timestamp,
            "observed_displacement_mm": ep.observed_displacement_mm,
            "coherence": ep.coherence,
            "incidence_angle_deg": ep.incidence_angle_deg,
            "noise_estimate_mm": ep.noise_estimate_mm,
            "phase_quality": ep.phase_quality,
        }
        for ep in sample.epochs
    ]

    feats1 = extract_observable_features(epochs_raw)
    feats2 = extract_observable_features(epochs_raw)

    assert feats1 == feats2


def test_audit_feature_tables_integrity():
    """Verify generated audit feature tables exist and contain clean finite values without ground truth leakage."""
    for split in ["train", "validation", "test"]:
        csv_path = os.path.join(AUDIT_DIR, f"features_{split}.csv")
        assert os.path.exists(csv_path), f"Missing feature table: {csv_path}"

        df = pd.read_csv(csv_path)
        assert len(df) > 0

        # Check sample_id and target_label
        assert "sample_id" in df.columns
        assert "target_label" in df.columns

        # Verify no NaN values in features
        for feat in OBSERVABLE_FEATURE_NAMES:
            assert feat in df.columns, f"Feature {feat} missing in {split} CSV"
            assert not df[feat].isna().any(), f"NaN found in feature {feat} in {split} CSV"
            assert not np.isinf(df[feat]).any(), f"Inf found in feature {feat} in {split} CSV"

        # Verify ground truth components are NOT columns
        forbidden = [
            "true_structural_displacement_mm",
            "true_environmental_displacement_mm",
            "true_atmospheric_displacement_mm",
            "true_noise_mm",
        ]
        for fcol in forbidden:
            assert fcol not in df.columns, f"Ground truth component {fcol} found in feature table!"


def test_audit_split_alignment_and_no_leakage():
    """Verify train, validation, and test sample IDs are completely disjoint."""
    df_train = pd.read_csv(os.path.join(AUDIT_DIR, "features_train.csv"))
    df_val = pd.read_csv(os.path.join(AUDIT_DIR, "features_validation.csv"))
    df_test = pd.read_csv(os.path.join(AUDIT_DIR, "features_test.csv"))

    train_ids = set(df_train["sample_id"])
    val_ids = set(df_val["sample_id"])
    test_ids = set(df_test["sample_id"])

    assert len(train_ids.intersection(val_ids)) == 0, "Leakage between train and validation!"
    assert len(train_ids.intersection(test_ids)) == 0, "Leakage between train and test!"
    assert len(val_ids.intersection(test_ids)) == 0, "Leakage between validation and test!"


def test_audit_metadata_manifest_exists():
    """Verify audit metadata json is created and contains all diagnostic sections."""
    meta_path = os.path.join(AUDIT_DIR, "audit_metadata.json")
    assert os.path.exists(meta_path)

    import json
    with open(meta_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "diagnostic_baselines" in data
    assert "top_single_feature_predictors" in data
    assert "temporal_vs_static_comparison" in data
    assert "pairwise_separability" in data
    assert "ambiguity_analysis" in data
    assert "synthetic_shortcuts" in data
