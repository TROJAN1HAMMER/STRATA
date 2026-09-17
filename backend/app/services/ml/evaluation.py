"""
Comprehensive Evaluation Suite for STRATA ML Deformation Classifier.
Implements test metrics, confusion matrix, ROC-AUC, Brier/LogLoss,
confidence entropy analysis, error tracking, and ablation studies.
"""
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import label_binarize

from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.ml.calibration import calculate_multiclass_brier_score
from backend.app.services.ml.classifier import compute_normalized_entropy
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FEATURE_GROUP_A_QUALITY,
    FEATURE_GROUP_B_DISPLACEMENT,
    FEATURE_GROUP_C_TEMPORAL_KINEMATIC,
    FEATURE_GROUP_D_PERIODICITY,
    FEATURE_GROUP_E_GEOMETRY,
)
from backend.app.services.ml.preprocessing import MLPreprocessor


def evaluate_classifier_performance(
    classifier: Any,
    preprocessor: MLPreprocessor,
    X_test_df: pd.DataFrame,
    y_test: pd.Series,
    classes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Evaluates classifier on the test split.
    Computes all standard classification and calibration metrics.
    """
    class_list = classes or [c.value for c in GroundTruthClass]
    X_test_trans = preprocessor.transform(X_test_df)

    y_pred = classifier.predict(X_test_trans)
    y_prob = classifier.predict_proba(X_test_trans)

    # 1. Overall Metrics
    acc = float(accuracy_score(y_test, y_pred))
    macro_p = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    macro_r = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    macro_f1 = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    weighted_f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    # 2. Confusion Matrix
    cm = confusion_matrix(y_test, y_pred, labels=class_list).tolist()

    # 3. Per-class metrics
    per_class_p = precision_score(y_test, y_pred, labels=class_list, average=None, zero_division=0)
    per_class_r = recall_score(y_test, y_pred, labels=class_list, average=None, zero_division=0)
    per_class_f1 = f1_score(y_test, y_pred, labels=class_list, average=None, zero_division=0)

    per_class_summary: Dict[str, Dict[str, float]] = {}
    for i, c_name in enumerate(class_list):
        per_class_summary[c_name] = {
            "precision": round(float(per_class_p[i]), 4),
            "recall": round(float(per_class_r[i]), 4),
            "f1_score": round(float(per_class_f1[i]), 4),
            "support": int(np.sum(y_test == c_name)),
        }

    # 4. Probabilistic calibration metrics (Brier, Log Loss, ROC-AUC)
    brier = calculate_multiclass_brier_score(y_test.to_numpy(), y_prob, class_list)
    try:
        loss = float(log_loss(y_test, y_prob, labels=class_list))
    except Exception:
        loss = float("nan")

    # One-vs-Rest ROC-AUC
    try:
        y_test_bin = label_binarize(y_test, classes=class_list)
        ovr_roc_auc = float(roc_auc_score(y_test_bin, y_prob, multi_class="ovr", average="macro"))
    except Exception:
        ovr_roc_auc = float("nan")

    # 5. Confidence & Entropy statistics
    confidences = np.max(y_prob, axis=1)
    entropies = np.array([compute_normalized_entropy(p) for p in y_prob])
    correct_count = int(np.sum(y_pred == y_test.to_numpy()))
    incorrect_count = int(np.sum(y_pred != y_test.to_numpy()))
    total_count = len(y_test)

    # 6. Reliability Binning & Expected Calibration Error (ECE)
    bins = [0.0, 0.4, 0.6, 0.8, 1.0]
    reliability_bins = []
    total_ece_weighted = 0.0
    for i in range(len(bins) - 1):
        low, high = bins[i], bins[i + 1]
        mask = (confidences >= low) & (confidences < high if i < len(bins) - 2 else confidences <= high)
        n_in_bin = int(np.sum(mask))
        if n_in_bin > 0:
            bin_acc = float(np.mean((y_pred[mask] == y_test.to_numpy()[mask]).astype(float)))
            bin_conf = float(np.mean(confidences[mask]))
            gap = abs(bin_conf - bin_acc)
            total_ece_weighted += (n_in_bin / total_count) * gap
            reliability_bins.append({
                "range": f"[{low:.1f}, {high:.1f}]",
                "count": n_in_bin,
                "avg_confidence": round(bin_conf, 4),
                "empirical_accuracy": round(bin_acc, 4),
                "calibration_gap": round(gap, 4),
            })
    ece = float(total_ece_weighted)

    return {
        "accuracy": round(acc, 4),
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "total_count": total_count,
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "brier_score": round(brier, 4),
        "log_loss": round(loss, 4),
        "expected_calibration_error": round(ece, 4),
        "reliability_bins": reliability_bins,
        "roc_auc_ovr_macro": round(ovr_roc_auc, 4) if not np.isnan(ovr_roc_auc) else None,
        "mean_confidence": round(float(np.mean(confidences)), 4),
        "median_confidence": round(float(np.median(confidences)), 4),
        "mean_entropy": round(float(np.mean(entropies)), 4),
        "per_class": per_class_summary,
        "confusion_matrix": cm,
        "classes": class_list,
    }



def perform_confidence_analysis(
    classifier: Any,
    preprocessor: MLPreprocessor,
    X_test_df: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """
    Compares confidence (max probability) and entropy between correct and incorrect predictions.
    """
    X_test_trans = preprocessor.transform(X_test_df)
    y_pred = classifier.predict(X_test_trans)
    y_prob = classifier.predict_proba(X_test_trans)

    confidences = np.max(y_prob, axis=1)
    entropies = np.array([compute_normalized_entropy(p) for p in y_prob])
    is_correct = (y_pred == y_test.to_numpy())

    correct_conf = confidences[is_correct]
    incorrect_conf = confidences[~is_correct]
    correct_ent = entropies[is_correct]
    incorrect_ent = entropies[~is_correct]

    return {
        "correct_predictions": {
            "count": int(np.sum(is_correct)),
            "mean_confidence": round(float(np.mean(correct_conf)), 4) if len(correct_conf) > 0 else 0.0,
            "mean_entropy": round(float(np.mean(correct_ent)), 4) if len(correct_ent) > 0 else 0.0,
        },
        "incorrect_predictions": {
            "count": int(np.sum(~is_correct)),
            "mean_confidence": round(float(np.mean(incorrect_conf)), 4) if len(incorrect_conf) > 0 else 0.0,
            "mean_entropy": round(float(np.mean(incorrect_ent)), 4) if len(incorrect_ent) > 0 else 0.0,
        },
        "interpretation": (
            "Higher entropy on incorrect predictions indicates well-calibrated epistemic uncertainty, "
            "allowing the Phase 5 consensus engine to detect when ML is uncertain."
        ),
    }


def perform_error_analysis(
    classifier: Any,
    preprocessor: MLPreprocessor,
    X_test_df: pd.DataFrame,
    y_test: pd.Series,
    class_list: List[str],
) -> Dict[str, Any]:
    """
    Identifies specific misclassifications across critical physical boundary pairs.
    """
    X_test_trans = preprocessor.transform(X_test_df)
    y_pred = classifier.predict(X_test_trans)
    y_prob = classifier.predict_proba(X_test_trans)

    critical_pairs = [
        ("STABLE", "SEASONAL_ENVIRONMENTAL"),
        ("STRUCTURAL_MONOTONIC", "SEASONAL_ENVIRONMENTAL"),
        ("STRUCTURAL_ACCELERATING", "STRUCTURAL_MONOTONIC"),
        ("STRUCTURAL_MONOTONIC", "TEMPORALLY_INCONSISTENT"),
        ("ATMOSPHERIC_TRANSIENT", "TEMPORALLY_INCONSISTENT"),
        ("LOW_QUALITY", "STABLE"),
    ]

    pair_errors: Dict[str, Any] = {}
    for c1, c2 in critical_pairs:
        # c1 predicted as c2
        mask = (y_test.to_numpy() == c1) & (y_pred == c2)
        indices = np.where(mask)[0]
        examples = []
        for idx in indices[:3]:
            row = X_test_df.iloc[idx]
            probs_dict = {class_list[k]: round(float(y_prob[idx, k]), 3) for k in range(len(class_list))}
            examples.append({
                "sample_id": row.get("sample_id", f"idx_{idx}"),
                "true_class": c1,
                "predicted_class": c2,
                "confidence": round(float(np.max(y_prob[idx])), 3),
                "probabilities": probs_dict,
                "key_features": {
                    "slope_mm_per_year": round(float(row.get("slope_mm_per_year", 0.0)), 3),
                    "displacement_range_mm": round(float(row.get("displacement_range_mm", 0.0)), 3),
                    "coherence_mean": round(float(row.get("coherence_mean", 0.0)), 3),
                    "directional_consistency": round(float(row.get("directional_consistency", 0.0)), 3),
                },
            })
        pair_errors[f"{c1}_confused_as_{c2}"] = {
            "count": int(len(indices)),
            "examples": examples,
        }

    return pair_errors


def perform_ablation_study(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    random_state: int = 42,
) -> Dict[str, Dict[str, Any]]:
    """
    Executes controlled feature group ablation study on the test split.
    """
    ablations = [
        ("A_Quality_Only", FEATURE_GROUP_A_QUALITY),
        ("B_Displacement_Only", FEATURE_GROUP_B_DISPLACEMENT),
        ("C_Temporal_Kinematic_Only", FEATURE_GROUP_C_TEMPORAL_KINEMATIC),
        ("D_Periodicity_Only", FEATURE_GROUP_D_PERIODICITY),
        ("E_Static_Plus_Temporal", FEATURE_GROUP_B_DISPLACEMENT + FEATURE_GROUP_C_TEMPORAL_KINEMATIC),
        ("F_All_Allowlisted_Features", FEATURE_ALLOWLIST),
    ]

    results: Dict[str, Dict[str, Any]] = {}
    for name, cols in ablations:
        prep = MLPreprocessor(feature_names=cols, scale=False)
        X_tr = prep.fit_transform(X_train)
        X_te = prep.transform(X_test)

        rf = RandomForestClassifier(
            n_estimators=100,
            max_depth=7,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=random_state,
        )
        rf.fit(X_tr, y_train)
        preds = rf.predict(X_te)

        results[name] = {
            "feature_count": len(cols),
            "test_accuracy": round(float(accuracy_score(y_test, preds)), 4),
            "test_macro_f1": round(float(f1_score(y_test, preds, average="macro", zero_division=0)), 4),
            "test_weighted_f1": round(float(f1_score(y_test, preds, average="weighted", zero_division=0)), 4),
        }

    return results
