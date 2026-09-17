#!/usr/bin/env python3
"""
STRATA Phase 4: Training Pipeline for Machine Learning Deformation Classifier.
Strictly consumes observable InSAR features from the training split.
Calibrates probabilities on the validation split without test set contamination.
Saves versioned model bundle under models/strata_ml_v0_1_0/.
"""
import argparse
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.ml import ModelMetadata
from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.ml.calibration import (
    calibrate_classifier,
    evaluate_calibration_metrics,
)
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_COLUMNS,
    validate_feature_dataframe,
)
from backend.app.services.ml.preprocessing import MLPreprocessor
from backend.app.services.ml.registry import save_model_bundle


DEFAULT_MODEL_VERSION = "strata_ml_v0_1_0"
TRAIN_CSV = os.path.join(repo_root, "data", "synthetic", "audit", "features_train.csv")
VAL_CSV = os.path.join(repo_root, "data", "synthetic", "audit", "features_validation.csv")


def train_ml_pipeline(
    model_version: str = DEFAULT_MODEL_VERSION,
    train_csv: str = TRAIN_CSV,
    val_csv: str = VAL_CSV,
    random_seed: int = 42,
    output_base_dir: str = os.path.join(repo_root, "models"),
) -> str:
    print("=" * 80)
    print(f"STRATA PHASE 4: TRAINING ML DEFORMATION CLASSIFIER ({model_version})")
    print("=" * 80)

    # 1. Load Data
    print(f"[1/5] Loading training and validation feature sets...")
    if not os.path.exists(train_csv) or not os.path.exists(val_csv):
        raise FileNotFoundError(
            f"Feature CSVs not found. Please ensure Phase 3.1 features exist at:\n"
            f"  Train: {train_csv}\n  Validation: {val_csv}"
        )

    df_train = pd.read_csv(train_csv)
    df_val = pd.read_csv(val_csv)

    print(f"  * Loaded train split:      {df_train.shape[0]} sequences")
    print(f"  * Loaded validation split: {df_val.shape[0]} sequences")

    # 2. Strict Allowlist & Data-Leakage Audit
    print(f"[2/5] Auditing feature allowlist and enforcing strict leakage firewall...")
    validate_feature_dataframe(df_train, is_training=True)
    validate_feature_dataframe(df_val, is_training=False)
    print(f"  [+] Allowlist verified: {len(FEATURE_ALLOWLIST)} observable features approved.")
    print(f"  [+] Forbidden columns checked: {len(FORBIDDEN_COLUMNS)} forbidden fields blocked.")

    y_train = df_train["target_label"]
    y_val = df_val["target_label"]
    class_list = sorted([c.value for c in GroundTruthClass])


    # 3. Fit Preprocessing Pipeline on TRAIN Only
    print(f"[3/5] Fitting leakage-safe preprocessor strictly on TRAIN split...")
    preprocessor = MLPreprocessor(feature_names=FEATURE_ALLOWLIST, scale=False)
    X_train_trans = preprocessor.fit_transform(df_train)
    X_val_trans = preprocessor.transform(df_val)

    # 4. Train Conservative Random Forest Classifier
    hyperparameters = {
        "n_estimators": 200,
        "max_depth": 8,
        "min_samples_leaf": 3,
        "class_weight": "balanced",
        "random_state": random_seed,
        "n_jobs": -1,
    }
    print(f"[4/5] Training conservative Random Forest with hyperparameters:")
    for k, v in hyperparameters.items():
        print(f"  * {k:20s}: {v}")

    base_rf = RandomForestClassifier(**hyperparameters)
    base_rf.fit(X_train_trans, y_train)

    # Evaluate uncalibrated probabilities on validation set
    y_val_uncal_probs = base_rf.predict_proba(X_val_trans)
    uncal_metrics = evaluate_calibration_metrics(y_val.to_numpy(), y_val_uncal_probs, class_list)
    print(f"  * Validation (Uncalibrated) - Brier Score: {uncal_metrics['brier_score']:.4f} | Log Loss: {uncal_metrics['log_loss']:.4f}")

    # Probability Calibration using Validation Split (cv='prefit')
    print("  * Calibrating probabilities on validation split via CalibratedClassifierCV(method='sigmoid', cv='prefit')...")
    calibrated_rf = calibrate_classifier(base_rf, X_val_trans, y_val, method="sigmoid")
    y_val_cal_probs = calibrated_rf.predict_proba(X_val_trans)
    cal_metrics = evaluate_calibration_metrics(y_val.to_numpy(), y_val_cal_probs, class_list)
    print(f"  * Validation (Calibrated)   - Brier Score: {cal_metrics['brier_score']:.4f} | Log Loss: {cal_metrics['log_loss']:.4f}")

    # Also train baseline Logistic Regression on scaled data for comparison
    lr_prep = MLPreprocessor(feature_names=FEATURE_ALLOWLIST, scale=True)
    X_tr_lr = lr_prep.fit_transform(df_train)
    X_val_lr = lr_prep.transform(df_val)
    lr_model = LogisticRegression(max_iter=1000, C=1.0, random_state=random_seed)
    lr_model.fit(X_tr_lr, y_train)
    lr_cal = calibrate_classifier(lr_model, X_val_lr, y_val, method="sigmoid")

    # 5. Model Serialization into Registry
    target_model_dir = os.path.join(output_base_dir, model_version)
    print(f"[5/5] Registering model bundle into {target_model_dir}...")

    metadata = ModelMetadata(
        model_version=model_version,
        model_type="CalibratedRandomForestClassifier",
        training_dataset_version="1.0.0",
        feature_schema_version=FEATURE_SCHEMA_VERSION,
        training_timestamp=datetime.now(timezone.utc).isoformat(),
        random_seed=random_seed,
        hyperparameters=hyperparameters,
        feature_allowlist=FEATURE_ALLOWLIST,
        forbidden_features_checked=sorted(list(FORBIDDEN_COLUMNS)),
        calibration_method="sigmoid (Platt scaling, cv='prefit' on validation)",
        calibrated_brier_score=cal_metrics["brier_score"],
        calibrated_log_loss=cal_metrics["log_loss"],
        test_metrics=None,  # Will be populated strictly by evaluate_classifier.py
    )

    save_model_bundle(
        model_dir=target_model_dir,
        classifier=calibrated_rf,
        preprocessor=preprocessor,
        metadata=metadata,
    )

    # Also save LR baseline into model dir for evaluation comparison
    import joblib
    joblib.dump({"classifier": lr_cal, "preprocessor": lr_prep}, os.path.join(target_model_dir, "baseline_lr.joblib"))

    print(f"Model training and registration complete.")
    print(f"Artifacts saved to: {target_model_dir}")
    print("=" * 80)
    return target_model_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train STRATA ML Deformation Classifier")
    parser.add_argument("--model-version", type=str, default=DEFAULT_MODEL_VERSION, help="Target model version identifier")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--train-csv", type=str, default=TRAIN_CSV)
    parser.add_argument("--val-csv", type=str, default=VAL_CSV)

    args = parser.parse_args()
    train_ml_pipeline(
        model_version=args.model_version,
        train_csv=args.train_csv,
        val_csv=args.val_csv,
        random_seed=args.seed,
    )
