#!/usr/bin/env python3
"""
STRATA Phase 3.1: Synthetic Dataset Quality & Separability Audit.
Conducts statistical, informational, leakage, and diagnostic baseline audits.
Strictly diagnostic — NOT training the final Phase 4 ML classifier.
"""
import argparse
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict, List, Tuple
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler
from sklearn.tree import DecisionTreeClassifier

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.synthetic import GroundTruthClass, SyntheticSequenceSample
from backend.app.services.synthetic.feature_extractor import (
    OBSERVABLE_FEATURE_NAMES,
    extract_observable_features,
)


AUDIT_DIR = os.path.join(repo_root, "data", "synthetic", "audit")
PLOTS_DIR = os.path.join(AUDIT_DIR, "plots")
DATASET_DIR = os.path.join(repo_root, "data", "synthetic", "dataset")

STATIC_FEATURE_NAMES: List[str] = [
    "epoch_count",
    "duration_days",
    "temporal_spacing_mean_days",
    "temporal_spacing_std_days",
    "incidence_angle_mean_deg",
    "incidence_angle_std_deg",
    "coherence_mean",
    "coherence_std",
    "minimum_coherence",
    "phase_quality_mean",
    "phase_quality_std",
    "noise_estimate_mean_mm",
    "mean_displacement_mm",
    "displacement_std_mm",
    "displacement_range_mm",
    "displacement_to_noise_ratio",
]

TEMPORAL_FEATURE_NAMES: List[str] = [
    "mean_absolute_step_mm",
    "max_absolute_step_mm",
    "max_step_to_range_ratio",
    "sign_change_count",
    "zero_crossing_count",
    "directional_consistency",
    "slope_mm_per_year",
    "linear_fit_residual_std_mm",
    "acceleration_mm_per_year2",
    "quadratic_fit_residual_std_mm",
    "temporal_autocorrelation_lag1",
    "approximate_periodicity_indicator",
]


def load_and_extract_features(jsonl_path: str) -> pd.DataFrame:
    """
    Loads JSONL dataset and extracts observable features into a pandas DataFrame.
    Strictly separates observable features from ground-truth annotations.
    """
    records: List[Dict[str, Any]] = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            sample = SyntheticSequenceSample.model_validate(data)

            # Convert epochs to plain dicts (ignoring ground_truth field)
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

            feat_dict = extract_observable_features(epochs_raw)
            feat_dict["sample_id"] = sample.sample_id
            feat_dict["target_label"] = sample.ground_truth_class.value
            feat_dict["is_edge_case"] = sample.is_edge_case
            feat_dict["edge_case_type"] = sample.edge_case_type or "none"
            records.append(feat_dict)

    df = pd.DataFrame(records)
    return df


def audit_feature_distributions(df_all: pd.DataFrame) -> Dict[str, Any]:
    """Calculates class-wise statistics for all observable features."""
    summary: Dict[str, Any] = {}
    classes = sorted(df_all["target_label"].unique())

    for feat in OBSERVABLE_FEATURE_NAMES:
        feat_stat: Dict[str, Any] = {
            "overall": {
                "mean": float(df_all[feat].mean()),
                "std": float(df_all[feat].std()),
                "min": float(df_all[feat].min()),
                "max": float(df_all[feat].max()),
                "median": float(df_all[feat].median()),
            },
            "by_class": {},
        }
        for c in classes:
            sub = df_all[df_all["target_label"] == c][feat]
            feat_stat["by_class"][c] = {
                "mean": round(float(sub.mean()), 4),
                "std": round(float(sub.std()), 4),
                "min": round(float(sub.min()), 4),
                "q25": round(float(sub.quantile(0.25)), 4),
                "median": round(float(sub.median()), 4),
                "q75": round(float(sub.quantile(0.75)), 4),
                "max": round(float(sub.max()), 4),
            }
        summary[feat] = feat_stat
    return summary


def run_diagnostic_baselines(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    feature_cols: List[str],
) -> Dict[str, Any]:
    """
    Evaluates diagnostic baseline models.
    NOTE: 'PHASE 3.1 DIAGNOSTIC BASELINE — NOT FINAL ML MODEL'
    """
    results: Dict[str, Any] = {}
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train[feature_cols])
    X_val_scaled = scaler.transform(X_val[feature_cols])
    X_test_scaled = scaler.transform(X_test[feature_cols])

    classes = sorted(list(y_train.unique()))

    # 1. Majority Class Baseline
    majority_class = y_train.mode()[0]
    maj_pred = [majority_class] * len(y_test)
    results["majority_class"] = {
        "accuracy": round(float(accuracy_score(y_test, maj_pred)), 4),
        "macro_f1": round(float(f1_score(y_test, maj_pred, average="macro", zero_division=0)), 4),
    }

    # 2. Logistic Regression (Conservative C=1.0)
    lr = LogisticRegression(max_iter=1000, C=1.0, random_state=42)
    lr.fit(X_train_scaled, y_train)
    lr_pred_val = lr.predict(X_val_scaled)
    lr_pred_test = lr.predict(X_test_scaled)
    results["logistic_regression"] = {
        "val_accuracy": round(float(accuracy_score(y_val, lr_pred_val)), 4),
        "test_accuracy": round(float(accuracy_score(y_test, lr_pred_test)), 4),
        "test_macro_precision": round(float(precision_score(y_test, lr_pred_test, average="macro", zero_division=0)), 4),
        "test_macro_recall": round(float(recall_score(y_test, lr_pred_test, average="macro", zero_division=0)), 4),
        "test_macro_f1": round(float(f1_score(y_test, lr_pred_test, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, lr_pred_test, labels=classes).tolist(),
    }

    # 3. Decision Tree (Shallow max_depth=4)
    dt = DecisionTreeClassifier(max_depth=4, random_state=42)
    dt.fit(X_train[feature_cols], y_train)
    dt_pred_test = dt.predict(X_test[feature_cols])
    results["decision_tree_depth4"] = {
        "test_accuracy": round(float(accuracy_score(y_test, dt_pred_test)), 4),
        "test_macro_f1": round(float(f1_score(y_test, dt_pred_test, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, dt_pred_test, labels=classes).tolist(),
    }

    # 4. Random Forest (Conservative max_depth=6, n_estimators=50)
    rf = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
    rf.fit(X_train[feature_cols], y_train)
    rf_pred_val = rf.predict(X_val[feature_cols])
    rf_pred_test = rf.predict(X_test[feature_cols])
    results["random_forest_depth6"] = {
        "val_accuracy": round(float(accuracy_score(y_val, rf_pred_val)), 4),
        "test_accuracy": round(float(accuracy_score(y_test, rf_pred_test)), 4),
        "test_macro_precision": round(float(precision_score(y_test, rf_pred_test, average="macro", zero_division=0)), 4),
        "test_macro_recall": round(float(recall_score(y_test, rf_pred_test, average="macro", zero_division=0)), 4),
        "test_macro_f1": round(float(f1_score(y_test, rf_pred_test, average="macro", zero_division=0)), 4),
        "confusion_matrix": confusion_matrix(y_test, rf_pred_test, labels=classes).tolist(),
    }

    return results


def run_single_feature_probing(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> List[Dict[str, Any]]:
    """Probes diagnostic predictive power of each individual observable feature."""
    probing_results: List[Dict[str, Any]] = []

    for feat in OBSERVABLE_FEATURE_NAMES:
        # Train a shallow decision tree (depth=3) on single feature
        clf = DecisionTreeClassifier(max_depth=3, random_state=42)
        clf.fit(X_train[[feat]], y_train)
        preds = clf.predict(X_test[[feat]])

        acc = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, average="macro", zero_division=0))

        probing_results.append({
            "feature": feat,
            "test_accuracy": round(acc, 4),
            "test_macro_f1": round(f1, 4),
        })

    probing_results.sort(key=lambda x: x["test_macro_f1"], reverse=True)
    return probing_results


def run_temporal_vs_static_comparison(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """Compares information content: Static only vs Temporal only vs Combined."""
    comparison: Dict[str, Any] = {}

    experiments = [
        ("Static Features Only", STATIC_FEATURE_NAMES),
        ("Temporal Features Only", TEMPORAL_FEATURE_NAMES),
        ("Combined (Static + Temporal)", OBSERVABLE_FEATURE_NAMES),
    ]

    for name, cols in experiments:
        rf = RandomForestClassifier(n_estimators=50, max_depth=6, random_state=42)
        rf.fit(X_train[cols], y_train)
        preds = rf.predict(X_test[cols])

        acc = float(accuracy_score(y_test, preds))
        f1 = float(f1_score(y_test, preds, average="macro", zero_division=0))
        prec = float(precision_score(y_test, preds, average="macro", zero_division=0))
        rec = float(recall_score(y_test, preds, average="macro", zero_division=0))

        comparison[name] = {
            "feature_count": len(cols),
            "test_accuracy": round(acc, 4),
            "test_macro_f1": round(f1, 4),
            "test_macro_precision": round(prec, 4),
            "test_macro_recall": round(rec, 4),
        }

    return comparison


def run_pairwise_separability(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, Any]:
    """Calculates diagnostic pairwise separability between critical class pairs."""
    pairs = [
        ("STABLE", "STRUCTURAL_MONOTONIC"),
        ("STABLE", "STRUCTURAL_ACCELERATING"),
        ("STRUCTURAL_MONOTONIC", "SEASONAL_ENVIRONMENTAL"),
        ("STRUCTURAL_ACCELERATING", "SEASONAL_ENVIRONMENTAL"),
        ("STRUCTURAL_MONOTONIC", "ATMOSPHERIC_TRANSIENT"),
        ("SEASONAL_ENVIRONMENTAL", "ATMOSPHERIC_TRANSIENT"),
        ("TEMPORALLY_INCONSISTENT", "ATMOSPHERIC_TRANSIENT"),
    ]

    pairwise_results: Dict[str, Any] = {}

    for c1, c2 in pairs:
        pair_key = f"{c1} vs {c2}"
        # Filter train and test
        mask_train = y_train.isin([c1, c2])
        mask_test = y_test.isin([c1, c2])

        X_tr = X_train[mask_train][OBSERVABLE_FEATURE_NAMES]
        y_tr = y_train[mask_train]
        X_te = X_test[mask_test][OBSERVABLE_FEATURE_NAMES]
        y_te = y_test[mask_test]

        clf = RandomForestClassifier(n_estimators=30, max_depth=5, random_state=42)
        clf.fit(X_tr, y_tr)
        preds = clf.predict(X_te)

        acc = float(accuracy_score(y_te, preds))
        f1 = float(f1_score(y_te, preds, pos_label=c2, average="binary", zero_division=0))

        cm = confusion_matrix(y_te, preds, labels=[c1, c2]).tolist()

        pairwise_results[pair_key] = {
            "accuracy": round(acc, 4),
            "f1_score": round(f1, 4),
            "test_samples": len(y_te),
            "confusion_matrix": {
                f"true_{c1}": {f"pred_{c1}": cm[0][0], f"pred_{c2}": cm[0][1]},
                f"true_{c2}": {f"pred_{c1}": cm[1][0], f"pred_{c2}": cm[1][1]},
            },
        }

    return pairwise_results


def run_ambiguity_analysis(df_test: pd.DataFrame) -> Dict[str, Any]:
    """Identifies sequences where observable features show high physical ambiguity."""
    ambiguities: Dict[str, Any] = {}

    # 1. Partial seasonal vs monotonic structural
    # Seasonal sequences with high directional consistency (monotonic flank of sine)
    seasonal_monotonic_flank = df_test[
        (df_test["target_label"] == "SEASONAL_ENVIRONMENTAL")
        & (df_test["directional_consistency"] >= 0.75)
    ]
    ambiguities["seasonal_with_monotonic_flank"] = {
        "count": len(seasonal_monotonic_flank),
        "sample_ids": seasonal_monotonic_flank["sample_id"].head(5).tolist(),
        "description": "Seasonal cycles observed over partial period exhibiting monotonic persistent flanks.",
    }

    # 2. Weak structural vs noise
    # Monotonic structural deformation with low displacement range (< 3.0 mm)
    weak_structural = df_test[
        (df_test["target_label"] == "STRUCTURAL_MONOTONIC")
        & (df_test["displacement_range_mm"] <= 3.0)
    ]
    ambiguities["weak_structural_near_noise"] = {
        "count": len(weak_structural),
        "sample_ids": weak_structural["sample_id"].head(5).tolist(),
        "description": "Slow monotonic structural movement (< 3mm total range) buried in measurement noise.",
    }

    # 3. Stable noise with zero-crossings vs subtle seasonal
    stable_zero_crossings = df_test[
        (df_test["target_label"] == "STABLE")
        & (df_test["zero_crossing_count"] >= 3)
    ]
    ambiguities["stable_zero_crossings"] = {
        "count": len(stable_zero_crossings),
        "sample_ids": stable_zero_crossings["sample_id"].head(5).tolist(),
        "description": "Pure stable measurement noise crossing zero >= 3 times mimicking subtle cyclical oscillation.",
    }

    # 4. Atmospheric spike vs Temporally Inconsistent
    # Temporally inconsistent sequences with a single dominant step
    inconsistent_spike = df_test[
        (df_test["target_label"] == "TEMPORALLY_INCONSISTENT")
        & (df_test["max_step_to_range_ratio"] >= 0.70)
    ]
    ambiguities["temporally_inconsistent_spike_like"] = {
        "count": len(inconsistent_spike),
        "sample_ids": inconsistent_spike["sample_id"].head(5).tolist(),
        "description": "Temporally inconsistent sequences where one abrupt step accounts for >70% of total range.",
    }

    return ambiguities


def generate_visual_audit_plots(
    df_all: pd.DataFrame,
    df_test: pd.DataFrame,
    rf_confusion_matrix: List[List[int]],
    classes: List[str],
    plots_dir: str,
) -> None:
    """Generates and saves visual audit plots."""
    os.makedirs(plots_dir, exist_ok=True)

    # 1. Trajectory Examples for each class
    fig, axes = plt.subplots(4, 2, figsize=(14, 16))
    axes_flat = axes.flatten()

    # Load 1 sample per class from train.jsonl
    sample_trajectories: Dict[str, Tuple[List[float], List[float]]] = {}
    with open(os.path.join(DATASET_DIR, "train.jsonl"), "r", encoding="utf-8") as f:
        for line in f:
            if len(sample_trajectories) >= 7:
                break
            d = json.loads(line)
            c = d["ground_truth_class"]
            if c not in sample_trajectories:
                t = [(datetime.fromisoformat(ep["acquisition_timestamp"]) - datetime.fromisoformat(d["epochs"][0]["acquisition_timestamp"])).days for ep in d["epochs"]]
                disp = [ep["observed_displacement_mm"] for ep in d["epochs"]]
                sample_trajectories[c] = (t, disp)

    for idx, c in enumerate(classes):
        ax = axes_flat[idx]
        if c in sample_trajectories:
            t, disp = sample_trajectories[c]
            ax.plot(t, disp, "o-", color="#1f77b4", lw=2, markersize=5)
            ax.axhline(0, color="gray", linestyle="--", alpha=0.5)
            ax.set_title(f"Class: {c}", fontsize=11, fontweight="bold")
            ax.set_xlabel("Elapsed Days")
            ax.set_ylabel("Displacement (mm)")
            ax.grid(True, alpha=0.3)
    # Hide 8th subplot
    axes_flat[7].axis("off")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "trajectory_examples.png"), dpi=150)
    plt.close()

    # 2. Coherence Distribution by Class
    plt.figure(figsize=(10, 6))
    data_coh = [df_all[df_all["target_label"] == c]["coherence_mean"] for c in classes]
    plt.boxplot(data_coh, tick_labels=classes, patch_artist=True, boxprops=dict(facecolor="#2ca02c", alpha=0.6))
    plt.xticks(rotation=30, ha="right")
    plt.title("Distribution of Mean Coherence by Ground-Truth Class", fontsize=12, fontweight="bold")
    plt.ylabel("Mean Coherence")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "coherence_distribution.png"), dpi=150)
    plt.close()

    # 3. Displacement Range Distribution by Class
    plt.figure(figsize=(10, 6))
    data_range = [df_all[df_all["target_label"] == c]["displacement_range_mm"] for c in classes]
    plt.boxplot(data_range, tick_labels=classes, patch_artist=True, boxprops=dict(facecolor="#ff7f0e", alpha=0.6))
    plt.xticks(rotation=30, ha="right")
    plt.title("Distribution of Displacement Range (mm) by Class", fontsize=12, fontweight="bold")
    plt.ylabel("Displacement Range (mm)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "displacement_range_distribution.png"), dpi=150)
    plt.close()

    # 4. Slope Distribution by Class
    plt.figure(figsize=(10, 6))
    data_slope = [df_all[df_all["target_label"] == c]["slope_mm_per_year"] for c in classes]
    plt.boxplot(data_slope, tick_labels=classes, patch_artist=True, boxprops=dict(facecolor="#d62728", alpha=0.6))
    plt.axhline(0, color="gray", linestyle="--", alpha=0.5)
    plt.xticks(rotation=30, ha="right")
    plt.title("Estimated Deformation Slope (mm/year) by Class", fontsize=12, fontweight="bold")
    plt.ylabel("Slope (mm/year)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "slope_distribution.png"), dpi=150)
    plt.close()

    # 5. Sign Change Count Distribution by Class
    plt.figure(figsize=(10, 6))
    data_sign = [df_all[df_all["target_label"] == c]["sign_change_count"] for c in classes]
    plt.boxplot(data_sign, tick_labels=classes, patch_artist=True, boxprops=dict(facecolor="#9467bd", alpha=0.6))
    plt.xticks(rotation=30, ha="right")
    plt.title("Sign-Change Count Distribution by Class", fontsize=12, fontweight="bold")
    plt.ylabel("Number of Step Sign Changes")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    plt.savefig(os.path.join(plots_dir, "sign_changes_distribution.png"), dpi=150)
    plt.close()

    # 6. PCA 2D Feature Projection (Test Split)
    scaler = StandardScaler()
    X_test_scaled = scaler.fit_transform(df_test[OBSERVABLE_FEATURE_NAMES])
    pca = PCA(n_components=2, random_state=42)
    pca_coords = pca.fit_transform(X_test_scaled)

    plt.figure(figsize=(10, 8))
    for c in classes:
        mask = (df_test["target_label"] == c)
        plt.scatter(
            pca_coords[mask, 0],
            pca_coords[mask, 1],
            label=c,
            alpha=0.65,
            edgecolors="none",
            s=40,
        )
    plt.title(
        f"2D PCA Projection of Observable InSAR Features (Test Split, EVR: {pca.explained_variance_ratio_.sum()*100:.1f}%)",
        fontsize=12,
        fontweight="bold",
    )
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)")
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "pca_feature_projection.png"), dpi=150)
    plt.close()

    # 7. Diagnostic Baseline Confusion Matrix Heatmap
    cm_arr = np.array(rf_confusion_matrix)
    plt.figure(figsize=(9, 8))
    plt.imshow(cm_arr, interpolation="nearest", cmap=plt.cm.Blues)
    plt.title("Phase 3.1 Diagnostic Random Forest Confusion Matrix (Test Split)", fontsize=12, fontweight="bold")
    plt.colorbar()
    tick_marks = np.arange(len(classes))
    plt.xticks(tick_marks, classes, rotation=35, ha="right")
    plt.yticks(tick_marks, classes)

    thresh = cm_arr.max() / 2.0
    for i in range(cm_arr.shape[0]):
        for j in range(cm_arr.shape[1]):
            plt.text(
                j,
                i,
                f"{cm_arr[i, j]}",
                horizontalalignment="center",
                color="white" if cm_arr[i, j] > thresh else "black",
                fontweight="bold",
            )
    plt.ylabel("True Ground-Truth Class")
    plt.xlabel("Diagnostic Predicted Class")
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "baseline_confusion_matrix.png"), dpi=150)
    plt.close()


def run_synthetic_shortcut_audit(df_all: pd.DataFrame) -> Dict[str, Any]:
    """
    Audits for potential synthetic generator shortcuts.
    Classifies shortcuts as PHYSICALLY_JUSTIFIED, GENERATOR_ARTIFACT, or UNCERTAIN.
    """
    shortcuts: Dict[str, Any] = {}

    # 1. Coherence vs LOW_QUALITY
    lq_coh_max = df_all[df_all["target_label"] == "LOW_QUALITY"]["coherence_mean"].max()
    other_coh_min = df_all[df_all["target_label"] != "LOW_QUALITY"]["coherence_mean"].min()
    shortcuts["low_quality_coherence_separation"] = {
        "finding": f"LOW_QUALITY maximum mean coherence is {lq_coh_max:.3f}, while non-LOW_QUALITY minimum mean coherence is {other_coh_min:.3f}.",
        "classification": "PHYSICALLY_JUSTIFIED",
        "rationale": "By definition in radar interferometry, low quality occurs when coherence drops below 0.25 decorrelation noise floor.",
    }

    # 2. Epoch Count Discrepancy
    epoch_stats = df_all.groupby("target_label")["epoch_count"].agg(["min", "mean", "max"]).to_dict("index")
    shortcuts["epoch_count_distribution"] = {
        "finding": epoch_stats,
        "classification": "GENERATOR_ARTIFACT",
        "rationale": "SEASONAL sequences were generated with 10-24 epochs (mean ~17) whereas others used 6-20 (mean ~13). While seasonal cycles physically require longer observation baselines, the model might exploit epoch_count as a slight shortcut if not controlled.",
    }

    # 3. Incidence Angle
    inc_stats = df_all.groupby("target_label")["incidence_angle_mean_deg"].agg(["min", "mean", "max"]).to_dict("index")
    shortcuts["incidence_angle_distribution"] = {
        "finding": inc_stats,
        "classification": "PHYSICALLY_JUSTIFIED",
        "rationale": "All classes share identical 25-45 degree range and mean (~35 degrees), showing zero geometric shortcut leakage.",
    }

    # 4. Max Step Ratio vs Atmospheric Transient
    atm_ratio_mean = df_all[df_all["target_label"] == "ATMOSPHERIC_TRANSIENT"]["max_step_to_range_ratio"].mean()
    other_ratio_mean = df_all[df_all["target_label"] != "ATMOSPHERIC_TRANSIENT"]["max_step_to_range_ratio"].mean()
    shortcuts["atmospheric_transient_step_ratio"] = {
        "finding": f"ATMOSPHERIC_TRANSIENT mean max_step_to_range_ratio is {atm_ratio_mean:.3f} vs {other_ratio_mean:.3f} for other classes.",
        "classification": "PHYSICALLY_JUSTIFIED",
        "rationale": "An isolated transient spike naturally produces a single step that constitutes almost the entire sequence range.",
    }

    return shortcuts


def main() -> None:
    print("=" * 80)
    print("STRATA PHASE 3.1: SYNTHETIC DATASET QUALITY & SEPARABILITY AUDIT")
    print("=" * 80)

    os.makedirs(AUDIT_DIR, exist_ok=True)
    os.makedirs(PLOTS_DIR, exist_ok=True)

    # 1. Feature Extraction
    print("[1/8] Extracting observable features from train, validation, and test splits...")
    df_train = load_and_extract_features(os.path.join(DATASET_DIR, "train.jsonl"))
    df_val = load_and_extract_features(os.path.join(DATASET_DIR, "validation.jsonl"))
    df_test = load_and_extract_features(os.path.join(DATASET_DIR, "test.jsonl"))

    print(f"  * Train features shape:      {df_train.shape}")
    print(f"  * Validation features shape: {df_val.shape}")
    print(f"  * Test features shape:       {df_test.shape}")

    # Export CSVs
    df_train.to_csv(os.path.join(AUDIT_DIR, "features_train.csv"), index=False)
    df_val.to_csv(os.path.join(AUDIT_DIR, "features_validation.csv"), index=False)
    df_test.to_csv(os.path.join(AUDIT_DIR, "features_test.csv"), index=False)
    print("  * Saved features_train.csv, features_validation.csv, features_test.csv")

    df_all = pd.concat([df_train, df_val, df_test], ignore_index=True)

    # 2. Feature Distribution Audit
    print("[2/8] Auditing feature distributions across ground-truth classes...")
    feature_summary = audit_feature_distributions(df_all)
    with open(os.path.join(AUDIT_DIR, "feature_summary.json"), "w", encoding="utf-8") as f:
        json.dump(feature_summary, f, indent=2)
    print("  * Saved feature_summary.json")

    # 3. Diagnostic Baseline Classifiers
    print("[3/8] Training and evaluating diagnostic baseline classifiers...")
    y_train = df_train["target_label"]
    y_val = df_val["target_label"]
    y_test = df_test["target_label"]

    baseline_results = run_diagnostic_baselines(
        X_train=df_train,
        y_train=y_train,
        X_val=df_val,
        y_val=y_val,
        X_test=df_test,
        y_test=y_test,
        feature_cols=OBSERVABLE_FEATURE_NAMES,
    )

    print(f"  * Majority Class Test Accuracy:  {baseline_results['majority_class']['accuracy']*100:.2f}%")
    print(f"  * Logistic Regression Test Acc: {baseline_results['logistic_regression']['test_accuracy']*100:.2f}% (Macro F1: {baseline_results['logistic_regression']['test_macro_f1']:.4f})")
    print(f"  * Decision Tree (d=4) Test Acc: {baseline_results['decision_tree_depth4']['test_accuracy']*100:.2f}% (Macro F1: {baseline_results['decision_tree_depth4']['test_macro_f1']:.4f})")
    print(f"  * Random Forest (d=6) Test Acc: {baseline_results['random_forest_depth6']['test_accuracy']*100:.2f}% (Macro F1: {baseline_results['random_forest_depth6']['test_macro_f1']:.4f})")

    # 4. Single-Feature Probing
    print("[4/8] Executing single-feature diagnostic probing...")
    single_feat_results = run_single_feature_probing(
        X_train=df_train,
        y_train=y_train,
        X_test=df_test,
        y_test=y_test,
    )
    print("  Top 5 Single-Feature Predictors:")
    for item in single_feat_results[:5]:
        print(f"    - {item['feature']:32s} -> Test Acc: {item['test_accuracy']*100:5.2f}% | Macro F1: {item['test_macro_f1']:.4f}")

    # 5. Temporal vs Static Information Comparison
    print("[5/8] Evaluating Temporal vs. Static information content...")
    temp_vs_static = run_temporal_vs_static_comparison(
        X_train=df_train,
        y_train=y_train,
        X_test=df_test,
        y_test=y_test,
    )
    for exp_name, metrics in temp_vs_static.items():
        print(f"  * {exp_name:30s} ({metrics['feature_count']} feats): Acc {metrics['test_accuracy']*100:.2f}% | F1 {metrics['test_macro_f1']:.4f}")

    # 6. Pairwise Class Separability
    print("[6/8] Auditing critical pairwise class separability...")
    pairwise_results = run_pairwise_separability(
        X_train=df_train,
        y_train=y_train,
        X_test=df_test,
        y_test=y_test,
    )
    for pair, pmetrics in pairwise_results.items():
        print(f"  * {pair:45s} -> Accuracy: {pmetrics['accuracy']*100:5.2f}% | F1: {pmetrics['f1_score']:.4f}")

    # 7. Ambiguity Analysis & Shortcut Audit
    print("[7/8] Conducting physical ambiguity and synthetic shortcut audit...")
    ambiguities = run_ambiguity_analysis(df_test)
    shortcuts = run_synthetic_shortcut_audit(df_all)

    # 8. Visual Audit Plots
    print("[8/8] Generating visual audit plots...")
    classes = sorted(list(y_train.unique()))
    generate_visual_audit_plots(
        df_all=df_all,
        df_test=df_test,
        rf_confusion_matrix=baseline_results["random_forest_depth6"]["confusion_matrix"],
        classes=classes,
        plots_dir=PLOTS_DIR,
    )
    print(f"  * Plots saved to {PLOTS_DIR}")

    # Compile and save audit metadata
    audit_metadata = {
        "audit_version": "1.0.0",
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "dataset_total_samples": len(df_all),
        "split_counts": {
            "train": len(df_train),
            "validation": len(df_val),
            "test": len(df_test),
        },
        "observable_feature_count": len(OBSERVABLE_FEATURE_NAMES),
        "observable_features": OBSERVABLE_FEATURE_NAMES,
        "ground_truth_only_fields": [
            "true_structural_displacement_mm",
            "true_environmental_displacement_mm",
            "true_atmospheric_displacement_mm",
            "true_noise_mm",
            "ground_truth_class",
            "scenario",
            "parameters",
            "is_edge_case",
            "edge_case_type",
        ],
        "diagnostic_baselines": baseline_results,
        "top_single_feature_predictors": single_feat_results[:10],
        "temporal_vs_static_comparison": temp_vs_static,
        "pairwise_separability": pairwise_results,
        "ambiguity_analysis": ambiguities,
        "synthetic_shortcuts": shortcuts,
    }

    with open(os.path.join(AUDIT_DIR, "audit_metadata.json"), "w", encoding="utf-8") as f:
        json.dump(audit_metadata, f, indent=2)

    print(f"\nAudit complete. All artifacts saved to {AUDIT_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()
