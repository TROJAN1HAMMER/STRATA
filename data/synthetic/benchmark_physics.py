#!/usr/bin/env python3
"""
STRATA Phase 3: Physics Engine Benchmark on Synthetic Test Split.
Evaluates PhysicsInSARConsistencyEngine against ground truth without altering physics thresholds.
Produces confusion matrix, overall accuracy, false structural, and missed structural analyses.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence, PhysicsClassification
from backend.app.schemas.synthetic import GroundTruthClass, SyntheticSequenceSample
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine


import logging

# Explicit Ground Truth to Expected Physics Classification Mapping
EXPECTED_PHYSICS_MAPPING: Dict[GroundTruthClass, PhysicsClassification] = {
    GroundTruthClass.STABLE: PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION,
    GroundTruthClass.STRUCTURAL_MONOTONIC: PhysicsClassification.STRUCTURALLY_CONSISTENT,
    GroundTruthClass.STRUCTURAL_ACCELERATING: PhysicsClassification.STRUCTURALLY_CONSISTENT,
    GroundTruthClass.SEASONAL_ENVIRONMENTAL: PhysicsClassification.SEASONALLY_SUSPECT,
    GroundTruthClass.ATMOSPHERIC_TRANSIENT: PhysicsClassification.ATMOSPHERICALLY_SUSPECT,
    GroundTruthClass.LOW_QUALITY: PhysicsClassification.LOW_QUALITY,
    GroundTruthClass.TEMPORALLY_INCONSISTENT: PhysicsClassification.TEMPORALLY_INCONSISTENT,
}

STRUCTURAL_GROUND_TRUTH_CLASSES = {
    GroundTruthClass.STRUCTURAL_MONOTONIC,
    GroundTruthClass.STRUCTURAL_ACCELERATING,
}


def run_physics_benchmark(
    test_jsonl_path: str = os.path.join(repo_root, "data", "synthetic", "dataset", "test.jsonl"),
) -> Dict[str, Any]:
    logging.getLogger("strata").setLevel(logging.WARNING)
    if not os.path.exists(test_jsonl_path):

        raise FileNotFoundError(f"Test split not found at: {test_jsonl_path}")

    engine = PhysicsInSARConsistencyEngine()

    total_samples = 0
    correct_classifications = 0

    # Confusion matrix: ground_truth -> physics_prediction -> count
    confusion_matrix: Dict[str, Dict[str, int]] = {
        gt.value: defaultdict(int) for gt in GroundTruthClass
    }

    false_structural_samples: List[Dict[str, Any]] = []
    missed_structural_samples: List[Dict[str, Any]] = []
    edge_case_performance: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "correct": 0})

    with open(test_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            sample_dict = json.loads(line)
            sample = SyntheticSequenceSample.model_validate(sample_dict)
            total_samples += 1

            # Convert epochs to ObservationRead objects for the physics engine
            obs_list: List[ObservationRead] = []
            for ep in sample.epochs:
                obs_dict = ep.to_public_observation_dict(infrastructure_id=sample.sample_id)
                obs_list.append(
                    ObservationRead(
                        id=f"OBS_{sample.sample_id}_{ep.epoch_id}",
                        infrastructure_id=sample.sample_id,
                        acquisition_timestamp=datetime.fromisoformat(obs_dict["acquisition_timestamp"]),
                        deformation_mm=obs_dict["deformation_mm"],
                        los_displacement_mm=obs_dict["los_displacement_mm"],
                        velocity_mm_per_year=sample.parameters.get("velocity_mm_yr") or sample.parameters.get("initial_velocity_mm_yr"),
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
                infrastructure_id=sample.sample_id,
                observations=obs_list,
                start_time=obs_list[0].acquisition_timestamp if obs_list else None,
                end_time=obs_list[-1].acquisition_timestamp if obs_list else None,
                epoch_count=len(obs_list),
            )


            evidence = engine.evaluate_sequence(seq)
            pred_class = evidence.classification
            gt_class = sample.ground_truth_class

            confusion_matrix[gt_class.value][pred_class.value] += 1

            expected_pred = EXPECTED_PHYSICS_MAPPING[gt_class]
            is_correct = (pred_class == expected_pred)

            if is_correct:
                correct_classifications += 1

            # Track edge cases
            if sample.is_edge_case:
                etype = sample.edge_case_type or "unspecified_edge"
                edge_case_performance[etype]["total"] += 1
                if is_correct:
                    edge_case_performance[etype]["correct"] += 1

            # False Structural Classification: GT is NOT structural, but physics said STRUCTURALLY_CONSISTENT
            if gt_class not in STRUCTURAL_GROUND_TRUTH_CLASSES and pred_class == PhysicsClassification.STRUCTURALLY_CONSISTENT:
                false_structural_samples.append({
                    "sample_id": sample.sample_id,
                    "ground_truth": gt_class.value,
                    "predicted": pred_class.value,
                    "edge_case": sample.edge_case_type,
                    "explanations": evidence.explanation[:2],
                })

            # Missed Structural Classification: GT IS structural, but physics did NOT say STRUCTURALLY_CONSISTENT
            if gt_class in STRUCTURAL_GROUND_TRUTH_CLASSES and pred_class != PhysicsClassification.STRUCTURALLY_CONSISTENT:
                missed_structural_samples.append({
                    "sample_id": sample.sample_id,
                    "ground_truth": gt_class.value,
                    "predicted": pred_class.value,
                    "edge_case": sample.edge_case_type,
                    "explanations": evidence.explanation[:2],
                })

    overall_accuracy = (correct_classifications / total_samples) if total_samples > 0 else 0.0

    # Format confusion matrix
    all_pred_classes = [c.value for c in PhysicsClassification]
    matrix_table = {}
    for gt in GroundTruthClass:
        matrix_table[gt.value] = {pred: confusion_matrix[gt.value][pred] for pred in all_pred_classes}

    per_class_summary = {}
    for gt in GroundTruthClass:
        expected = EXPECTED_PHYSICS_MAPPING[gt].value
        total_gt = sum(confusion_matrix[gt.value].values())
        correct_gt = confusion_matrix[gt.value][expected]
        acc = (correct_gt / total_gt) if total_gt > 0 else 0.0
        per_class_summary[gt.value] = {
            "total": total_gt,
            "correct": correct_gt,
            "accuracy": round(acc, 4),
            "expected_physics_label": expected,
        }

    results = {
        "benchmark_timestamp": datetime.now(timezone.utc).isoformat(),
        "total_test_samples": total_samples,
        "correct_classifications": correct_classifications,
        "overall_accuracy": round(overall_accuracy, 4),
        "false_structural_count": len(false_structural_samples),
        "missed_structural_count": len(missed_structural_samples),
        "per_class_summary": per_class_summary,
        "confusion_matrix": matrix_table,
        "edge_case_performance": dict(edge_case_performance),
        "false_structural_examples": false_structural_samples[:5],
        "missed_structural_examples": missed_structural_samples[:5],
    }

    return results


def print_benchmark_report(results: Dict[str, Any]) -> None:
    print("\n" + "=" * 80)
    print("STRATA PHASE 3: PHYSICS ENGINE BENCHMARK ON SYNTHETIC TEST SPLIT")
    print("=" * 80)
    print(f"Total Test Sequences Evaluated: {results['total_test_samples']}")
    print(f"Overall Classification Accuracy: {results['overall_accuracy'] * 100:.2f}% ({results['correct_classifications']}/{results['total_test_samples']})")
    print(f"False Structural Classifications: {results['false_structural_count']}")
    print(f"Missed Structural Classifications: {results['missed_structural_count']}")
    print("\n--- PER-CLASS PERFORMANCE ---")
    print(f"{'Ground Truth Class':30s} | {'Total':6s} | {'Correct':8s} | {'Accuracy':9s} | {'Expected Physics Label'}")
    print("-" * 88)
    for gt_name, stats in results["per_class_summary"].items():
        print(f"{gt_name:30s} | {stats['total']:6d} | {stats['correct']:8d} | {stats['accuracy']*100:8.2f}% | {stats['expected_physics_label']}")

    print("\n--- CONFUSION MATRIX ---")
    pred_headers = [c.value[:14] for c in PhysicsClassification]
    header_str = " | ".join(f"{h:14s}" for h in pred_headers)
    print(f"{'Ground Truth':26s} | {header_str}")
    print("-" * (28 + len(pred_headers) * 17))
    for gt in GroundTruthClass:
        row_vals = [f"{results['confusion_matrix'][gt.value][c.value]:14d}" for c in PhysicsClassification]
        print(f"{gt.value:26s} | {' | '.join(row_vals)}")

    if results["edge_case_performance"]:
        print("\n--- EDGE CASE PERFORMANCE ---")
        for etype, stats in results["edge_case_performance"].items():
            acc = (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
            print(f"  * {etype:35s}: {stats['correct']:2d}/{stats['total']:2d} ({acc:5.1f}%)")

    if results["missed_structural_examples"]:
        print("\n--- NOTABLE MISSED STRUCTURAL DETECTIONS (EXPOSING BOUNDARY LIMITS) ---")
        for ex in results["missed_structural_examples"]:
            print(f"  [!] Sample {ex['sample_id']} (GT: {ex['ground_truth']}, Edge: {ex['edge_case']}) -> Physics: {ex['predicted']}")
            for exp in ex["explanations"]:
                print(f"      Reason: {exp}")

    if results["false_structural_examples"]:
        print("\n--- NOTABLE FALSE STRUCTURAL DETECTIONS ---")
        for ex in results["false_structural_examples"]:
            print(f"  [!] Sample {ex['sample_id']} (GT: {ex['ground_truth']}, Edge: {ex['edge_case']}) -> Physics: {ex['predicted']}")
            for exp in ex["explanations"]:
                print(f"      Reason: {exp}")

    print("=" * 80 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Benchmark Physics Engine on STRATA Synthetic Test Split")
    parser.add_argument("--test-split", type=str, default=os.path.join(repo_root, "data", "synthetic", "dataset", "test.jsonl"))
    parser.add_argument("--json-out", type=str, default=None, help="Optional output path to save JSON results")

    args = parser.parse_args()
    benchmark_results = run_physics_benchmark(args.test_split)
    print_benchmark_report(benchmark_results)

    if args.json_out:
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(benchmark_results, f, indent=2)
        print(f"Benchmark results saved to {args.json_out}")
