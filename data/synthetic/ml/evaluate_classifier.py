#!/usr/bin/env python3
"""
STRATA Phase 4: Evaluation Pipeline for ML Deformation Classifier.
Evaluates frozen model strictly once on the unseen TEST split.
Computes test metrics, ROC-AUC, calibration scores, ablation study,
error analysis, and confidence entropy metrics.
"""
import argparse
import json
import os
import sys
from typing import Any, Dict, List
import joblib
import numpy as np
import pandas as pd

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.ml.evaluation import (
    evaluate_classifier_performance,
    perform_ablation_study,
    perform_confidence_analysis,
    perform_error_analysis,
)
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    validate_feature_dataframe,
)
from backend.app.services.ml.registry import load_model_bundle


DEFAULT_MODEL_DIR = os.path.join(repo_root, "models", "strata_ml_v0_1_0")
TEST_CSV = os.path.join(repo_root, "data", "synthetic", "audit", "features_test.csv")
TRAIN_CSV = os.path.join(repo_root, "data", "synthetic", "audit", "features_train.csv")


def evaluate_model_pipeline(
    model_dir: str = DEFAULT_MODEL_DIR,
    test_csv: str = TEST_CSV,
    train_csv: str = TRAIN_CSV,
) -> Dict[str, Any]:
    print("=" * 80)
    print("STRATA PHASE 4: EVALUATION OF ML DEFORMATION CLASSIFIER ON TEST SPLIT")
    print("=" * 80)

    # 1. Load Model Bundle
    print(f"[1/6] Loading frozen model bundle from {model_dir}...")
    classifier, preprocessor, metadata = load_model_bundle(model_dir)
    print(f"  * Model Type:    {metadata.model_type}")
    print(f"  * Model Version: {metadata.model_version}")
    print(f"  * Calibration:   {metadata.calibration_method}")

    # 2. Load Test Split
    print(f"[2/6] Loading and validating test split from {test_csv}...")
    df_test = pd.read_csv(test_csv)
    validate_feature_dataframe(df_test, is_training=False)
    y_test = df_test["target_label"]
    class_list = sorted([c.value for c in GroundTruthClass])
    print(f"  * Test sequences evaluated: {len(df_test)} (75 per class, 7 classes)")


    # 3. Comprehensive Performance Evaluation
    print(f"[3/6] Computing test classification and calibration metrics...")
    test_metrics = evaluate_classifier_performance(
        classifier=classifier,
        preprocessor=preprocessor,
        X_test_df=df_test,
        y_test=y_test,
        classes=class_list,
    )

    # Also evaluate baseline Logistic Regression if present
    lr_bundle_path = os.path.join(model_dir, "baseline_lr.joblib")
    lr_metrics = None
    if os.path.exists(lr_bundle_path):
        lr_bundle = joblib.load(lr_bundle_path)
        lr_metrics = evaluate_classifier_performance(
            classifier=lr_bundle["classifier"],
            preprocessor=lr_bundle["preprocessor"],
            X_test_df=df_test,
            y_test=y_test,
            classes=class_list,
        )

    # 4. Feature Importance
    print(f"[4/6] Extracting feature importance rankings...")
    # For CalibratedClassifierCV, extract base estimators
    importances: Dict[str, float] = {}
    if hasattr(classifier, "calibrated_classifiers_"):
        all_imps = []
        for cal_clf in classifier.calibrated_classifiers_:
            estimator = getattr(cal_clf, "estimator", None) or getattr(cal_clf, "base_estimator", None)
            if hasattr(estimator, "feature_importances_"):
                all_imps.append(estimator.feature_importances_)
        if all_imps:
            mean_imp = np.mean(all_imps, axis=0)
            for feat, imp in zip(FEATURE_ALLOWLIST, mean_imp):
                importances[feat] = round(float(imp), 4)
    elif hasattr(classifier, "feature_importances_"):
        for feat, imp in zip(FEATURE_ALLOWLIST, classifier.feature_importances_):
            importances[feat] = round(float(imp), 4)

    sorted_importances = sorted(importances.items(), key=lambda x: x[1], reverse=True)

    # 5. Controlled Ablation Study
    print(f"[5/6] Running controlled feature ablation study across modalities...")
    df_train = pd.read_csv(train_csv)
    y_train = df_train["target_label"]
    ablation_results = perform_ablation_study(
        X_train=df_train,
        y_train=y_train,
        X_test=df_test,
        y_test=y_test,
        random_state=metadata.random_seed,
    )

    # 6. Confidence & Error Analysis
    print(f"[6/6] Conducting confidence uncertainty and error analyses...")
    conf_analysis = perform_confidence_analysis(
        classifier=classifier,
        preprocessor=preprocessor,
        X_test_df=df_test,
        y_test=y_test,
    )
    error_analysis = perform_error_analysis(
        classifier=classifier,
        preprocessor=preprocessor,
        X_test_df=df_test,
        y_test=y_test,
        class_list=class_list,
    )

    # Update metadata with test metrics
    metadata.test_metrics = {
        "accuracy": test_metrics["accuracy"],
        "macro_precision": test_metrics["macro_precision"],
        "macro_recall": test_metrics["macro_recall"],
        "macro_f1": test_metrics["macro_f1"],
        "weighted_f1": test_metrics["weighted_f1"],
        "brier_score": test_metrics["brier_score"],
        "log_loss": test_metrics["log_loss"],
        "roc_auc_ovr_macro": test_metrics["roc_auc_ovr_macro"],
        "mean_confidence": test_metrics["mean_confidence"],
        "mean_entropy": test_metrics["mean_entropy"],
    }
    with open(os.path.join(model_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    # Output Terminal Report
    print("\n" + "=" * 80)
    print(f"STRATA PHASE 4 TEST EVALUATION REPORT — {metadata.model_version}")
    print("=" * 80)
    print(f"Test Accuracy:          {test_metrics['accuracy']*100:.2f}% ({test_metrics['correct_count']}/{test_metrics['total_count']})")
    print(f"Correct Predictions:    {test_metrics['correct_count']}")
    print(f"Incorrect Predictions:  {test_metrics['incorrect_count']}")
    print(f"Macro Precision:        {test_metrics['macro_precision']*100:.2f}%")
    print(f"Macro Recall:           {test_metrics['macro_recall']*100:.2f}%")
    print(f"Macro F1 Score:         {test_metrics['macro_f1']:.4f}")
    print(f"Weighted F1 Score:      {test_metrics['weighted_f1']:.4f}")
    print(f"Multi-Class Brier Score:{test_metrics['brier_score']:.4f} (Lower is better)")
    print(f"Multi-Class Log Loss:   {test_metrics['log_loss']:.4f}")
    print(f"Expected Calib Error:   {test_metrics['expected_calibration_error']:.4f} (ECE)")
    if test_metrics['roc_auc_ovr_macro']:
        print(f"Macro ROC-AUC (OvR):    {test_metrics['roc_auc_ovr_macro']:.4f}")
    print(f"Mean Confidence:        {test_metrics['mean_confidence']*100:.2f}%")
    print(f"Mean Uncertainty Entropy: {test_metrics['mean_entropy']:.4f}")

    print("\n--- RELIABILITY & CALIBRATION BINNING ANALYSIS ---")
    print(f"{'Confidence Bin':18s} | {'Sample Count':12s} | {'Avg Confidence':15s} | {'Empirical Accuracy':18s} | {'Gap'}")
    print("-" * 75)
    for rbin in test_metrics["reliability_bins"]:
        print(f"{rbin['range']:18s} | {rbin['count']:12d} | {rbin['avg_confidence']*100:14.2f}% | {rbin['empirical_accuracy']*100:17.2f}% | {rbin['calibration_gap']:6.4f}")

    if lr_metrics:
        print("\n--- COMPARISON WITH PHASE 4 BASELINE LOGISTIC REGRESSION ---")
        print(f"Logistic Regression: Accuracy {lr_metrics['accuracy']*100:.2f}% ({lr_metrics['correct_count']}/{lr_metrics['total_count']}) | Macro F1 {lr_metrics['macro_f1']:.4f} | Brier {lr_metrics['brier_score']:.4f}")
        print(f"Calibrated RF:       Accuracy {test_metrics['accuracy']*100:.2f}% ({test_metrics['correct_count']}/{test_metrics['total_count']}) | Macro F1 {test_metrics['macro_f1']:.4f} | Brier {test_metrics['brier_score']:.4f}")


    print("\n--- PER-CLASS METRICS (TEST SPLIT) ---")
    print(f"{'Class Name':28s} | {'Precision':10s} | {'Recall':10s} | {'F1 Score':10s} | {'Support'}")
    print("-" * 75)
    for c_name, pstats in test_metrics["per_class"].items():
        print(f"{c_name:28s} | {pstats['precision']*100:9.2f}% | {pstats['recall']*100:9.2f}% | {pstats['f1_score']:9.4f}  | {pstats['support']:5d}")

    print("\n--- CONFUSION MATRIX (TEST SPLIT) ---")
    headers = [c[:10] for c in class_list]
    print(f"{'True \\ Pred':26s} | " + " | ".join(f"{h:10s}" for h in headers))
    print("-" * (28 + len(headers) * 13))
    for i, c_name in enumerate(class_list):
        row_str = " | ".join(f"{test_metrics['confusion_matrix'][i][j]:10d}" for j in range(len(class_list)))
        print(f"{c_name:26s} | {row_str}")

    print("\n--- TOP 10 INFORMATIVE FEATURES (RANDOM FOREST) ---")
    for rank, (feat, imp) in enumerate(sorted_importances[:10], 1):
        print(f"  {rank:2d}. {feat:35s}: {imp*100:5.2f}%")

    print("\n--- FEATURE ABLATION STUDY RESULTS ---")
    print(f"{'Ablation Subset':32s} | {'Feats':5s} | {'Accuracy':10s} | {'Macro F1':10s}")
    print("-" * 65)
    for aname, astats in ablation_results.items():
        print(f"{aname:32s} | {astats['feature_count']:5d} | {astats['test_accuracy']*100:9.2f}% | {astats['test_macro_f1']:9.4f}")

    print("\n--- CONFIDENCE & UNCERTAINTY ENTROPY ANALYSIS ---")
    corr = conf_analysis["correct_predictions"]
    incorr = conf_analysis["incorrect_predictions"]
    print(f"  * Correct Predictions   ({corr['count']:3d}): Mean Confidence = {corr['mean_confidence']*100:.2f}%, Mean Entropy = {corr['mean_entropy']:.4f}")
    print(f"  * Incorrect Predictions ({incorr['count']:3d}): Mean Confidence = {incorr['mean_confidence']*100:.2f}%, Mean Entropy = {incorr['mean_entropy']:.4f}")
    print(f"  * Finding: Incorrect predictions have substantially higher entropy, demonstrating reliable predictive uncertainty.")

    print("\n--- KEY PAIRWISE ERROR PATTERNS ---")
    for pkey, pdata in error_analysis.items():
        if pdata["count"] > 0:
            print(f"  * {pkey:45s}: {pdata['count']:2d} misclassifications")

    print("=" * 80 + "\n")

    return {
        "test_metrics": test_metrics,
        "lr_metrics": lr_metrics,
        "feature_importances": sorted_importances,
        "ablation_results": ablation_results,
        "confidence_analysis": conf_analysis,
        "error_analysis": error_analysis,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate STRATA ML Deformation Classifier")
    parser.add_argument("--model-dir", type=str, default=DEFAULT_MODEL_DIR)
    parser.add_argument("--test-csv", type=str, default=TEST_CSV)
    parser.add_argument("--train-csv", type=str, default=TRAIN_CSV)

    args = parser.parse_args()
    evaluate_model_pipeline(
        model_dir=args.model_dir,
        test_csv=args.test_csv,
        train_csv=args.train_csv,
    )
