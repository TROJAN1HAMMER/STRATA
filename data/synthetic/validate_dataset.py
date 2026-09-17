#!/usr/bin/env python3
"""
STRATA Phase 3: Synthetic Dataset Validation Script.
Verifies integrity, mathematical reconstruction, no split leakage,
monotonic timestamp ordering, and adherence to physical bounds.
"""
import argparse
from datetime import datetime
import json
import math
import os
import sys
from typing import Dict, List, Set, Tuple

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.synthetic import (
    GroundTruthClass,
    SyntheticSequenceSample,
)


def validate_synthetic_dataset(
    dataset_dir: str = os.path.join(repo_root, "data", "synthetic", "dataset"),
    metadata_path: str = os.path.join(repo_root, "data", "synthetic", "metadata.json"),
    tolerance: float = 1e-4,
) -> Tuple[bool, List[str]]:
    """
    Validates synthetic dataset splits and metadata.
    Returns (is_valid, list_of_issues).
    """
    issues: List[str] = []
    split_files = {
        "train": os.path.join(dataset_dir, "train.jsonl"),
        "validation": os.path.join(dataset_dir, "validation.jsonl"),
        "test": os.path.join(dataset_dir, "test.jsonl"),
    }

    # 1. Check file existence
    for split_name, path in split_files.items():
        if not os.path.exists(path):
            issues.append(f"Split file missing: {path}")

    if not os.path.exists(metadata_path):
        issues.append(f"Metadata file missing: {metadata_path}")

    if issues:
        return False, issues

    # Load metadata
    with open(metadata_path, "r", encoding="utf-8") as f:
        try:
            metadata = json.load(f)
        except Exception as e:
            issues.append(f"Failed to parse metadata.json: {e}")
            return False, issues

    split_sample_ids: Dict[str, Set[str]] = {"train": set(), "validation": set(), "test": set()}
    all_sample_ids: Set[str] = set()
    class_counts_by_split: Dict[str, Dict[str, int]] = {
        "train": {},
        "validation": {},
        "test": {},
    }

    # 2. Iterate through each split file
    for split_name, path in split_files.items():
        line_num = 0
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line_num += 1
                line = line.strip()
                if not line:
                    continue

                try:
                    data = json.loads(line)
                    sample = SyntheticSequenceSample.model_validate(data)
                except Exception as e:
                    issues.append(f"[{split_name}:{line_num}] Schema validation failed: {e}")
                    continue

                sample_id = sample.sample_id

                # Unique sample_id
                if sample_id in all_sample_ids:
                    issues.append(f"Duplicate sample_id found across dataset: {sample_id}")
                all_sample_ids.add(sample_id)
                split_sample_ids[split_name].add(sample_id)

                # Ground truth class validation
                if not isinstance(sample.ground_truth_class, GroundTruthClass):
                    issues.append(f"[{sample_id}] Invalid ground truth class: {sample.ground_truth_class}")

                gt_name = sample.ground_truth_class.value
                class_counts_by_split[split_name][gt_name] = class_counts_by_split[split_name].get(gt_name, 0) + 1

                # Epoch count
                if len(sample.epochs) < 2:
                    issues.append(f"[{sample_id}] Sequence has fewer than 2 epochs: {len(sample.epochs)}")
                if len(sample.epochs) != sample.epoch_count:
                    issues.append(f"[{sample_id}] Stated epoch_count ({sample.epoch_count}) != actual ({len(sample.epochs)})")

                # Epoch checks
                prev_dt: datetime = None
                for ep in sample.epochs:
                    # Check timestamp ordering
                    try:
                        dt = datetime.fromisoformat(ep.acquisition_timestamp)
                        if prev_dt and dt <= prev_dt:
                            issues.append(f"[{sample_id}:epoch {ep.epoch_id}] Non-monotonic timestamp: {ep.acquisition_timestamp} <= {prev_dt.isoformat()}")
                        prev_dt = dt
                    except Exception as e:
                        issues.append(f"[{sample_id}:epoch {ep.epoch_id}] Invalid ISO timestamp: {ep.acquisition_timestamp}")

                    # Check physical boundaries
                    if not (0.0 <= ep.coherence <= 1.0) or math.isnan(ep.coherence) or math.isinf(ep.coherence):
                        issues.append(f"[{sample_id}:epoch {ep.epoch_id}] Invalid coherence: {ep.coherence}")

                    if not (15.0 <= ep.incidence_angle_deg <= 60.0) or math.isnan(ep.incidence_angle_deg) or math.isinf(ep.incidence_angle_deg):
                        issues.append(f"[{sample_id}:epoch {ep.epoch_id}] Out-of-bounds incidence angle: {ep.incidence_angle_deg}")

                    if math.isnan(ep.observed_displacement_mm) or math.isinf(ep.observed_displacement_mm):
                        issues.append(f"[{sample_id}:epoch {ep.epoch_id}] NaN/Inf in observed displacement")

                    # Check mathematical identity
                    gt = ep.ground_truth
                    reconstructed = (
                        gt.true_structural_displacement_mm
                        + gt.true_environmental_displacement_mm
                        + gt.true_atmospheric_displacement_mm
                        + gt.true_noise_mm
                    )
                    diff = abs(ep.observed_displacement_mm - reconstructed)
                    if diff > tolerance:
                        issues.append(
                            f"[{sample_id}:epoch {ep.epoch_id}] Mathematical reconstruction mismatch: "
                            f"observed={ep.observed_displacement_mm}, reconstructed={reconstructed:.6f}, diff={diff:.6f} > {tolerance}"
                        )

    # 3. Check for split leakage (disjoint sets)
    train_val_overlap = split_sample_ids["train"].intersection(split_sample_ids["validation"])
    train_test_overlap = split_sample_ids["train"].intersection(split_sample_ids["test"])
    val_test_overlap = split_sample_ids["validation"].intersection(split_sample_ids["test"])

    if train_val_overlap:
        issues.append(f"Split leakage: {len(train_val_overlap)} samples overlap between train and validation!")
    if train_test_overlap:
        issues.append(f"Split leakage: {len(train_test_overlap)} samples overlap between train and test!")
    if val_test_overlap:
        issues.append(f"Split leakage: {len(val_test_overlap)} samples overlap between validation and test!")

    # 4. Check metadata consistency
    meta_splits = metadata.get("splits", {})
    for split_name in ["train", "validation", "test"]:
        actual_count = len(split_sample_ids[split_name])
        expected_count = meta_splits.get(split_name, 0)
        if actual_count != expected_count:
            issues.append(f"Split size mismatch for '{split_name}': actual={actual_count}, metadata={expected_count}")

    is_valid = len(issues) == 0
    return is_valid, issues


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate STRATA Synthetic InSAR Dataset")
    parser.add_argument("--dataset-dir", type=str, default=os.path.join(repo_root, "data", "synthetic", "dataset"))
    parser.add_argument("--metadata", type=str, default=os.path.join(repo_root, "data", "synthetic", "metadata.json"))

    args = parser.parse_args()
    valid, issues_list = validate_synthetic_dataset(args.dataset_dir, args.metadata)

    if valid:
        print("SUCCESS: All synthetic dataset validation checks passed!")
        sys.exit(0)
    else:
        print(f"FAILED: Found {len(issues_list)} validation issues:")
        for idx, issue in enumerate(issues_list[:25], 1):
            print(f"  {idx}. {issue}")
        if len(issues_list) > 25:
            print(f"  ... and {len(issues_list) - 25} more issues.")
        sys.exit(1)
