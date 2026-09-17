"""
Unit Tests for STRATA Phase 4 Machine Learning Deformation Classifier.
Validates:
- Forbidden feature rejection / leakage firewall
- Feature allowlist ordering and purity
- Preprocessing fit-on-train isolation
- Calibrated probability output properties (sum ≈ 1.0, bounds in [0, 1])
- Model serialization, loading, and inference consistency
- Full 7-class representation
- Decoupled inference on raw InSAR observation sequences
"""
import math
import os
import tempfile
import numpy as np
import pandas as pd
import pytest

from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.ml.classifier import (
    DEFAULT_MODEL_DIR,
    MLDeformationClassifier,
    compute_normalized_entropy,
)
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FORBIDDEN_COLUMNS,
    extract_features_from_sequence,
    validate_feature_dataframe,
)
from backend.app.services.ml.preprocessing import MLPreprocessor
from backend.app.services.ml.registry import load_model_bundle, save_model_bundle
from backend.app.services.synthetic.builders import (
    generate_seasonal_sequence,
    generate_stable_sequence,
    generate_structural_monotonic_sequence,
)
import random


def test_forbidden_feature_rejection():
    """Verify validate_feature_dataframe raises ValueError when forbidden columns are present."""
    # Create synthetic DataFrame with valid features
    data = {feat: [1.0] for feat in FEATURE_ALLOWLIST}
    data["sample_id"] = ["TEST_001"]
    data["target_label"] = ["STABLE"]

    # Should pass initially
    df_valid = pd.DataFrame(data)
    validate_feature_dataframe(df_valid, is_training=True)

    # Inject forbidden column and ensure failure
    for forbidden_col in [
        "true_structural_displacement_mm",
        "true_environmental_displacement_mm",
        "true_atmospheric_displacement_mm",
        "true_noise_mm",
        "parameters",
        "scenario",
        "random_seed",
        "physics_classification",
        "physics_confidence",
    ]:
        df_invalid = df_valid.copy()
        df_invalid[forbidden_col] = [0.0]
        with pytest.raises(ValueError, match="CRITICAL DATA LEAKAGE"):
            validate_feature_dataframe(df_invalid, is_training=True)


def test_feature_allowlist_purity_and_ordering():
    """Verify FEATURE_ALLOWLIST contains 28 features, zero forbidden columns, and no duplicates."""
    assert len(FEATURE_ALLOWLIST) == 28
    assert len(FEATURE_ALLOWLIST) == len(set(FEATURE_ALLOWLIST))  # No duplicates

    leaked = FORBIDDEN_COLUMNS.intersection(set(FEATURE_ALLOWLIST))
    assert len(leaked) == 0, f"Leakage detected in allowlist: {leaked}"


def test_preprocessing_fit_isolation():
    """Verify preprocessor fits strictly on training data and transforms validation/test reproducibly."""
    # Synthetic train DataFrame
    train_data = {feat: [float(i)] for i, feat in enumerate(FEATURE_ALLOWLIST)}
    train_data["sample_id"] = ["TR_001"]
    train_data["target_label"] = ["STABLE"]
    df_train = pd.DataFrame(train_data)

    prep = MLPreprocessor(feature_names=FEATURE_ALLOWLIST, scale=True)
    assert not prep.is_fitted

    X_train_trans = prep.fit_transform(df_train)
    assert prep.is_fitted
    assert X_train_trans.shape == (1, 28)

    # Transform test row
    test_data = {feat: [float(i + 1)] for i, feat in enumerate(FEATURE_ALLOWLIST)}
    df_test = pd.DataFrame(test_data)
    X_test_trans = prep.transform(df_test)
    assert X_test_trans.shape == (1, 28)
    assert not np.isnan(X_test_trans).any()


def test_model_loading_and_inference_api():
    """Verify model can be loaded from default models directory and runs inference on a sequence."""
    if not os.path.exists(os.path.join(DEFAULT_MODEL_DIR, "model.joblib")):
        pytest.skip(f"Model bundle not found in {DEFAULT_MODEL_DIR}")

    clf = MLDeformationClassifier(model_dir=DEFAULT_MODEL_DIR)
    assert clf.is_loaded

    rng = random.Random(42)
    sample = generate_structural_monotonic_sequence("INFRA_TEST_001", rng)

    result = clf.predict(sample)

    assert isinstance(result.predicted_class, GroundTruthClass)
    assert len(result.probabilities) == 7
    for c_name in [c.value for c in GroundTruthClass]:
        assert c_name in result.probabilities
        assert 0.0 <= result.probabilities[c_name] <= 1.0

    # Probability sum must be approximately 1.0
    prob_sum = sum(result.probabilities.values())
    assert abs(prob_sum - 1.0) < 1e-3

    # Confidence must be the maximum probability
    max_p = max(result.probabilities.values())
    assert abs(result.confidence - max_p) < 1e-4

    # Entropy in [0.0, 1.0]
    assert 0.0 <= result.entropy <= 1.0
    assert result.model_version == "strata_ml_v0_1_0"


def test_inference_on_raw_observation_sequence():
    """Verify inference works on a standard STRATA ObservationSequence object without ground truth."""
    if not os.path.exists(os.path.join(DEFAULT_MODEL_DIR, "model.joblib")):
        pytest.skip(f"Model bundle not found in {DEFAULT_MODEL_DIR}")

    clf = MLDeformationClassifier(model_dir=DEFAULT_MODEL_DIR)

    # Generate synthetic observations and strip ground truth completely
    rng = random.Random(101)
    sample = generate_seasonal_sequence("SEASONAL_INFRA", rng)
    obs_list = []
    for ep in sample.epochs:
        obs_dict = ep.to_public_observation_dict("SEASONAL_INFRA")
        from datetime import datetime, timezone
        obs_list.append(
            ObservationRead(
                id=f"OBS_{ep.epoch_id}",
                infrastructure_id="SEASONAL_INFRA",
                acquisition_timestamp=datetime.fromisoformat(obs_dict["acquisition_timestamp"]),
                deformation_mm=obs_dict["deformation_mm"],
                los_displacement_mm=obs_dict["los_displacement_mm"],
                velocity_mm_per_year=0.0,
                coherence=obs_dict["coherence"],
                phase_quality=obs_dict["phase_quality"],
                incidence_angle=obs_dict["incidence_angle"],
                atmospheric_indicator=obs_dict["atmospheric_indicator"],
                source="SYNTHETIC",
                observation_metadata=obs_dict["metadata"],
                created_at=datetime.now(timezone.utc),
            )
        )

    seq = ObservationSequence(
        infrastructure_id="SEASONAL_INFRA",
        observations=obs_list,
        epoch_count=len(obs_list),
    )

    result = clf.predict(seq)
    assert result.predicted_class in list(GroundTruthClass)
    assert abs(sum(result.probabilities.values()) - 1.0) < 1e-3


def test_model_serialization_and_deserialization():
    """Verify model can be serialized and reloaded cleanly via joblib in a temporary directory."""
    if not os.path.exists(os.path.join(DEFAULT_MODEL_DIR, "model.joblib")):
        pytest.skip(f"Model bundle not found in {DEFAULT_MODEL_DIR}")

    orig_clf, orig_prep, orig_meta = load_model_bundle(DEFAULT_MODEL_DIR)

    with tempfile.TemporaryDirectory() as tmpdir:
        target_dir = os.path.join(tmpdir, "test_model_v1")
        save_model_bundle(
            model_dir=target_dir,
            classifier=orig_clf,
            preprocessor=orig_prep,
            metadata=orig_meta,
        )

        assert os.path.exists(os.path.join(target_dir, "model.joblib"))
        assert os.path.exists(os.path.join(target_dir, "metadata.json"))
        assert os.path.exists(os.path.join(target_dir, "feature_schema.json"))

        reloaded_clf, reloaded_prep, reloaded_meta = load_model_bundle(target_dir)
        assert reloaded_meta.model_version == orig_meta.model_version
        assert reloaded_meta.model_type == orig_meta.model_type


def test_entropy_uncertainty_bounds():
    """Verify compute_normalized_entropy behaves properly at boundary extremes."""
    # Completely certain distribution
    certain_p = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
    ent_certain = compute_normalized_entropy(certain_p)
    assert ent_certain == 0.0

    # Completely uncertain uniform distribution (1/7 for each)
    uniform_p = np.array([1.0 / 7.0] * 7)
    ent_uniform = compute_normalized_entropy(uniform_p)
    assert abs(ent_uniform - 1.0) < 1e-3


def test_training_reproducibility():
    """Verify training with the same random seed produces identical predictions."""
    from sklearn.ensemble import RandomForestClassifier

    rng = np.random.RandomState(42)
    X = rng.randn(100, 28)
    y = rng.choice(["STABLE", "STRUCTURAL_MONOTONIC"], 100)

    rf1 = RandomForestClassifier(n_estimators=20, max_depth=4, random_state=42)
    rf1.fit(X, y)
    p1 = rf1.predict_proba(X)

    rf2 = RandomForestClassifier(n_estimators=20, max_depth=4, random_state=42)
    rf2.fit(X, y)
    p2 = rf2.predict_proba(X)

    np.testing.assert_allclose(p1, p2, atol=1e-7)

