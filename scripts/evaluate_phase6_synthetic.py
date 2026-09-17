"""
Synthetic Evaluation script for STRATA Phase 6 Temporal Evidence & Chronology.
Tests representative multi-epoch sequences from data/synthetic/dataset/test.jsonl
across all 7 ground-truth classes to validate expected temporal behavior.
"""
import json
import os
from typing import Dict, List
from backend.app.schemas.synthetic import SyntheticSequenceSample
from backend.app.services.temporal.engine import TemporalEvidenceEngine

TEST_JSONL = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "dataset", "test.jsonl")
)

EXPECTED_BEHAVIOR = {
    "STABLE": "Nominal baseline stability across epochs (BASELINE)",
    "STRUCTURAL_MONOTONIC": "Persistent deformation candidate accumulating persistence (PERSISTENT / EMERGING)",
    "STRUCTURAL_ACCELERATING": "Persistent/accelerating deformation candidate with negative rate (PERSISTENT / EMERGING)",
    "SEASONAL_ENVIRONMENTAL": "Recurring cyclical environmental fluctuation without structural persistence (ENVIRONMENTAL_PATTERN)",
    "ATMOSPHERIC_TRANSIENT": "Transient phase delay anomaly resolving to baseline (ATMOSPHERIC_EVENT / BASELINE)",
    "LOW_QUALITY": "Severe interferometric degradation suppressing confidence (LOW_QUALITY)",
    "TEMPORALLY_INCONSISTENT": "High temporal volatility or conflict across epochs (CONFLICTED / LOW_QUALITY)",
}


def main():
    print("=" * 80)
    print("STRATA PHASE 6: SYNTHETIC DATASET TEMPORAL BEHAVIOR EVALUATION")
    print("=" * 80)

    engine = TemporalEvidenceEngine()

    # Load 1 representative sample per class
    samples_by_class: Dict[str, SyntheticSequenceSample] = {}
    with open(TEST_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            data = json.loads(line)
            gt = data.get("ground_truth_class")
            if gt not in samples_by_class:
                samples_by_class[gt] = SyntheticSequenceSample.model_validate(data)
                if len(samples_by_class) == 7:
                    break

    print(f"Loaded {len(samples_by_class)} representative multi-epoch sequences from test.jsonl\n")

    results = []
    for gt_class, sample in samples_by_class.items():
        obs_dicts = [
            {
                "id": f"{sample.sample_id}_ep_{ep.epoch_id}",
                "acquisition_timestamp": ep.acquisition_timestamp,
                "deformation_mm": ep.observed_displacement_mm,
                "coherence": ep.coherence,
                "phase_quality": ep.phase_quality,
                "incidence_angle": ep.incidence_angle_deg,
            }
            for ep in sample.epochs
        ]

        summary = engine.evaluate_summary(
            infrastructure_id=sample.sample_id,
            observations=obs_dicts,
        )

        expected = EXPECTED_BEHAVIOR.get(gt_class, "Unknown")
        observed = summary.temporal_status.value
        rate_str = f"{summary.trend_rate_mm_per_year:.2f} mm/yr" if summary.trend_rate_mm_per_year is not None else "N/A"
        accel_str = f"{summary.apparent_acceleration_mm_per_year2:.2f} mm/yr²" if summary.apparent_acceleration_mm_per_year2 is not None else "N/A"
        supp_str = "SUPPORTED" if summary.acceleration_supported else "UNSUPPORTED"

        print(f"Class:                     {gt_class}")
        print(f"Expected Temporal Status:  {expected}")
        print(f"Observed Temporal Status:  {observed}")
        print(f"Coverage / Epochs:         {summary.observation_count} epochs over {summary.coverage_duration_days:.1f} days")
        print(f"Mean Confidence:           {summary.mean_confidence * 100:.1f}%")
        print(f"Persistence Score:         {summary.persistence_score:.4f}")
        print(f"Trend Rate / Accel:        Rate={rate_str} | Accel={accel_str} ({supp_str})")
        if summary.apparent_acceleration_mm_per_year2 is not None:
            print(f"Accel Support Reason:      {summary.acceleration_support_reason}")
        print(f"State Transitions:         {[t.new_state.value for t in summary.state_transitions]}")
        print(f"Explanation:               {summary.explanation[:140]}...")
        print("-" * 80)

        results.append({
            "class": gt_class,
            "sample_id": sample.sample_id,
            "expected_status": expected,
            "observed_status": observed,
            "observation_count": summary.observation_count,
            "coverage_days": summary.coverage_duration_days,
            "mean_confidence": summary.mean_confidence,
            "persistence_score": summary.persistence_score,
            "trend_rate_mm_per_year": summary.trend_rate_mm_per_year,
            "apparent_acceleration_mm_per_year2": summary.apparent_acceleration_mm_per_year2,
            "trend_acceleration_mm_per_year2": summary.trend_acceleration_mm_per_year2,
            "acceleration_supported": summary.acceleration_supported,
            "acceleration_support_reason": summary.acceleration_support_reason,
            "state_transitions": [t.new_state.value for t in summary.state_transitions],
            "explanation": summary.explanation,
        })

    out_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "audit", "phase6_synthetic_evaluation.json"))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved evaluation matrix to {out_path}")


if __name__ == "__main__":
    main()
