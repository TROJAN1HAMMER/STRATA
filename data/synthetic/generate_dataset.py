#!/usr/bin/env python3
"""
STRATA Phase 3: Controlled Synthetic Multi-Epoch Dataset Generator.
Generates balanced, parameterized InSAR sequences with explicit ground-truth decomposition.
Saves partitioned train/validation/test splits as JSONL and emits dataset manifest metadata.json.
"""
import argparse
from datetime import datetime, timezone
import json
import os
import random
import sys
from typing import Any, Dict, List

# Ensure repository root is on sys.path
repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from backend.app.schemas.synthetic import (
    GroundTruthClass,
    SyntheticSequenceSample,
)
from backend.app.services.synthetic.builders import (
    generate_stable_sequence,
    generate_structural_monotonic_sequence,
    generate_structural_accelerating_sequence,
    generate_seasonal_sequence,
    generate_atmospheric_transient_sequence,
    generate_low_quality_sequence,
    generate_temporally_inconsistent_sequence,
)
from backend.app.services.synthetic.parameters import DatasetConfig, PROTOTYPE_ASSUMPTIONS


EDGE_CASE_TYPES = {
    GroundTruthClass.STABLE: ["short_sequence", "elevated_noise_stable"],
    GroundTruthClass.STRUCTURAL_MONOTONIC: [
        "weak_structural_near_noise",
        "low_coherence_structural",
        "structural_with_atmospheric_spike",
        "noise_reversal_edge",
        "short_sequence",
    ],
    GroundTruthClass.STRUCTURAL_ACCELERATING: [
        "accelerating_moderate_noise",
        "accelerating_subtle_onset",
        "short_sequence",
    ],
    GroundTruthClass.SEASONAL_ENVIRONMENTAL: [
        "strong_seasonal_amplitude",
        "seasonal_with_high_noise",
        "short_seasonal_sequence",
    ],
    GroundTruthClass.ATMOSPHERIC_TRANSIENT: ["high_coherence_atmospheric"],
    GroundTruthClass.LOW_QUALITY: [],
    GroundTruthClass.TEMPORALLY_INCONSISTENT: [],
}


BUILDERS = {
    GroundTruthClass.STABLE: generate_stable_sequence,
    GroundTruthClass.STRUCTURAL_MONOTONIC: generate_structural_monotonic_sequence,
    GroundTruthClass.STRUCTURAL_ACCELERATING: generate_structural_accelerating_sequence,
    GroundTruthClass.SEASONAL_ENVIRONMENTAL: generate_seasonal_sequence,
    GroundTruthClass.ATMOSPHERIC_TRANSIENT: generate_atmospheric_transient_sequence,
    GroundTruthClass.LOW_QUALITY: generate_low_quality_sequence,
    GroundTruthClass.TEMPORALLY_INCONSISTENT: generate_temporally_inconsistent_sequence,
}


def generate_class_samples(
    gt_class: GroundTruthClass,
    count: int,
    rng: random.Random,
    config: DatasetConfig,
    edge_case_ratio: float = 0.15,
) -> List[SyntheticSequenceSample]:
    builder = BUILDERS[gt_class]
    edge_types = EDGE_CASE_TYPES.get(gt_class, [])
    samples: List[SyntheticSequenceSample] = []

    for i in range(count):
        sample_id = f"STRATA_SYN_{gt_class.value}_{i+1:05d}"
        is_edge = bool(edge_types) and (rng.random() < edge_case_ratio)
        edge_type = rng.choice(edge_types) if is_edge else None

        sample = builder(
            sample_id=sample_id,
            rng=rng,
            config=config,
            is_edge_case=is_edge,
            edge_case_type=edge_type,
        )
        samples.append(sample)

    return samples


def generate_full_dataset(
    samples_per_class: int = 500,
    seed: int = 42,
    output_dir: str = os.path.join(repo_root, "data", "synthetic", "dataset"),
    config: DatasetConfig = PROTOTYPE_ASSUMPTIONS,
) -> Dict[str, Any]:
    print(f"Initializing STRATA Synthetic Dataset Generation with seed={seed}...")
    rng = random.Random(seed)

    all_train: List[SyntheticSequenceSample] = []
    all_val: List[SyntheticSequenceSample] = []
    all_test: List[SyntheticSequenceSample] = []

    class_stats: Dict[str, Dict[str, int]] = {}

    for gt_class in GroundTruthClass:
        class_samples = generate_class_samples(
            gt_class=gt_class,
            count=samples_per_class,
            rng=rng,
            config=config,
        )
        # Deterministic shuffle within class
        rng.shuffle(class_samples)

        n_train = int(samples_per_class * config.train_ratio)
        n_val = int(samples_per_class * config.validation_ratio)
        n_test = samples_per_class - n_train - n_val

        train_slice = class_samples[:n_train]
        val_slice = class_samples[n_train : n_train + n_val]
        test_slice = class_samples[n_train + n_val :]

        for s in train_slice:
            s.split = "train"
        for s in val_slice:
            s.split = "validation"
        for s in test_slice:
            s.split = "test"

        all_train.extend(train_slice)
        all_val.extend(val_slice)
        all_test.extend(test_slice)

        class_stats[gt_class.value] = {
            "total": samples_per_class,
            "train": len(train_slice),
            "validation": len(val_slice),
            "test": len(test_slice),
        }
        print(f"  [+] {gt_class.value:25s}: {samples_per_class} samples (Train: {len(train_slice)}, Val: {len(val_slice)}, Test: {len(test_slice)})")

    # Shuffle splits to mix classes
    rng.shuffle(all_train)
    rng.shuffle(all_val)
    rng.shuffle(all_test)

    os.makedirs(output_dir, exist_ok=True)
    train_file = os.path.join(output_dir, "train.jsonl")
    val_file = os.path.join(output_dir, "validation.jsonl")
    test_file = os.path.join(output_dir, "test.jsonl")

    def _write_jsonl(path: str, samples: List[SyntheticSequenceSample]):
        with open(path, "w", encoding="utf-8") as f:
            for s in samples:
                f.write(s.model_dump_json() + "\n")

    print(f"Writing dataset files to {output_dir}...")
    _write_jsonl(train_file, all_train)
    _write_jsonl(val_file, all_val)
    _write_jsonl(test_file, all_test)

    total_samples = len(all_train) + len(all_val) + len(all_test)

    metadata = {
        "dataset_version": "1.0.0",
        "generator_version": "1.0.0",
        "generation_timestamp": datetime.now(timezone.utc).isoformat(),
        "random_seed": seed,
        "total_samples": total_samples,
        "samples_per_class": samples_per_class,
        "splits": {
            "train": len(all_train),
            "validation": len(all_val),
            "test": len(all_test),
        },
        "class_distribution": class_stats,
        "parameter_ranges": {
            "epoch_count": list(config.epoch_count_range),
            "temporal_spacing_days": list(config.temporal_spacing_days_range),
            "incidence_angle_deg": list(config.incidence_angle_deg_range),
            "nominal_coherence": list(config.nominal_coherence_range),
            "degraded_coherence": list(config.degraded_coherence_range),
            "measurement_noise_scale_mm": list(config.measurement_noise_scale_range),
            "monotonic_velocity_mm_yr": list(config.monotonic_velocity_mm_yr_range),
            "accelerating_initial_velocity_mm_yr": list(config.accelerating_initial_velocity_mm_yr_range),
            "acceleration_mm_yr2": list(config.acceleration_mm_yr2_range),
            "seasonal_amplitude_mm": list(config.seasonal_amplitude_mm_range),
            "seasonal_period_days": list(config.seasonal_period_days_range),
            "atmospheric_transient_magnitude_mm": list(config.atmospheric_transient_magnitude_mm_range),
        },
        "assumptions": config.prototype_assumptions,
    }

    metadata_path = os.path.abspath(os.path.join(output_dir, "..", "metadata.json"))
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"Metadata written to {metadata_path}")
    print(f"Generated {total_samples} total sequences successfully.")
    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate STRATA Synthetic InSAR Dataset")
    parser.add_argument("--samples-per-class", type=int, default=500, help="Number of samples per class (default: 500)")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic random seed (default: 42)")
    parser.add_argument("--output-dir", type=str, default=None, help="Target directory for JSONL dataset files")
    parser.add_argument("--validate", action="store_true", default=True, help="Run validation automatically after generation")

    args = parser.parse_args()
    target_dir = args.output_dir or os.path.join(repo_root, "data", "synthetic", "dataset")

    meta = generate_full_dataset(
        samples_per_class=args.samples_per_class,
        seed=args.seed,
        output_dir=target_dir,
    )

    if args.validate:
        print("\nInvoking validation pipeline...")
        from data.synthetic.validate_dataset import validate_synthetic_dataset
        success, issues = validate_synthetic_dataset(
            dataset_dir=target_dir,
            metadata_path=os.path.join(os.path.dirname(target_dir), "metadata.json"),
        )
        if not success:
            print("Validation FAILED with issues:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        else:
            print("Validation PASSED without any issues.")
