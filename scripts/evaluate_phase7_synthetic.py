"""
Synthetic Evaluation script for STRATA Phase 7 Infrastructure-Specific Risk Characterization.
Evaluates representative multi-epoch sequences from data/synthetic/dataset/test.jsonl
across all 7 ground-truth classes within contextual infrastructure profiles.
"""
import json
import os
from typing import Dict, List
from backend.app.db.models import (
    CriticalityLevel,
    MaterialType,
    StructureType,
)
from backend.app.schemas.risk import (
    CalibrationProfile,
    CriticalZone,
    CriticalZoneType,
    ExpectedDeformationBehavior,
    HistoricalBaseline,
)
from backend.app.schemas.synthetic import SyntheticSequenceSample
from backend.app.services.risk import InfrastructureRiskCharacterizationEngine

TEST_JSONL = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "dataset", "test.jsonl")
)

# Realistic infrastructure profiles for the 7 synthetic classes
CLASS_PROFILES = {
    "STABLE": {
        "structure_type": StructureType.BRIDGE,
        "material": MaterialType.CONCRETE,
        "criticality": CriticalityLevel.MODERATE,
        "historical_baseline": HistoricalBaseline(
            baseline_mean_mm=0.0,
            baseline_std_mm=1.5,
            baseline_observation_count=25,
        ),
    },
    "SEASONAL_ENVIRONMENTAL": {
        "structure_type": StructureType.DAM,
        "material": MaterialType.CONCRETE,
        "criticality": CriticalityLevel.HIGH,
        "expected_behavior": [ExpectedDeformationBehavior.SEASONAL],
        "historical_baseline": HistoricalBaseline(
            baseline_mean_mm=0.0,
            baseline_std_mm=3.0,
            baseline_observation_count=30,
        ),
    },
    "STRUCTURAL_MONOTONIC": {
        "structure_type": StructureType.BRIDGE,
        "material": MaterialType.STEEL,
        "criticality": CriticalityLevel.HIGH,
        "critical_zones": [
            CriticalZone(
                zone_id="cz_pier_2",
                zone_name="South Abutment / Pier 2",
                zone_type=CriticalZoneType.PIER,
                importance_weight=1.6,
            )
        ],
        "historical_baseline": HistoricalBaseline(
            baseline_mean_mm=0.0,
            baseline_std_mm=1.0,
            baseline_observation_count=20,
        ),
    },
    "STRUCTURAL_ACCELERATING": {
        "structure_type": StructureType.RETAINING_STRUCTURE,
        "material": MaterialType.CONCRETE,
        "criticality": CriticalityLevel.HIGH,
        "critical_zones": [
            CriticalZone(
                zone_id="cz_toe",
                zone_name="Wall Toe Foundation",
                zone_type=CriticalZoneType.FOUNDATION,
                importance_weight=1.5,
            )
        ],
    },
    "TEMPORALLY_INCONSISTENT": {
        "structure_type": StructureType.TUNNEL,
        "material": MaterialType.CONCRETE,
        "criticality": CriticalityLevel.MODERATE,
    },
    "ATMOSPHERIC_TRANSIENT": {
        "structure_type": StructureType.BUILDING,
        "material": MaterialType.MASONRY,
        "criticality": CriticalityLevel.LOW,
    },
    "LOW_QUALITY": {
        "structure_type": StructureType.EMBANKMENT,
        "material": MaterialType.EARTH,
        "criticality": CriticalityLevel.CRITICAL,
    },
}


def main():
    print("=" * 80)
    print("STRATA PHASE 7: SYNTHETIC DATASET RISK CHARACTERIZATION EVALUATION")
    print("=" * 80)

    engine = InfrastructureRiskCharacterizationEngine()

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
                "source": "SYNTHETIC",
            }
            for ep in sample.epochs
        ]

        prof_kwargs = CLASS_PROFILES.get(gt_class, {})
        infra_dict = {
            "id": sample.sample_id,
            "name": f"Asset {sample.sample_id}",
            **prof_kwargs,
        }

        characterization = engine.evaluate_infrastructure(
            infrastructure=infra_dict,
            observations=obs_dicts,
        )

        state_str = characterization.characterization_state.value
        idx_str = f"{characterization.prototype_risk_index:.1f}/100" if characterization.prototype_risk_index is not None else "N/A"
        comp = characterization.evidence_components

        print(f"Class:                   {gt_class}")
        print(f"Asset Context:           {infra_dict.get('structure_type', 'OTHER')} | {infra_dict.get('material', 'UNKNOWN')} | Criticality: {infra_dict.get('criticality', 'UNKNOWN')}")
        print(f"Characterization State:  {state_str}")
        print(f"Prototype Index:         {idx_str} (Confidence: {characterization.confidence * 100:.1f}%)")
        print(f"Components:              Qual={comp.measurement_quality:.2f} | Agree={comp.consensus_support:.2f} | Persist={comp.temporal_persistence:.2f} | RateSig={comp.trend_significance:.2f} | Accel={comp.acceleration_support:.2f} | EnvSupp={comp.environmental_suppression:.2f}")
        if comp.baseline_deviation_mm is not None:
            print(f"Baseline Deviation:      {comp.baseline_deviation_mm:+.2f} mm (z = {comp.baseline_z_score})")
        print(f"Supporting Factors:      {characterization.supporting_factors[:2]}")
        print(f"Suppressing Factors:     {characterization.suppressing_factors[:2]}")
        print(f"Uncertainty Factors:     {characterization.uncertainty_factors[:2]}")
        print("-" * 80)

        results.append({
            "class": gt_class,
            "sample_id": sample.sample_id,
            "structure_type": str(infra_dict.get("structure_type", "OTHER")),
            "criticality": str(infra_dict.get("criticality", "UNKNOWN")),
            "characterization_state": state_str,
            "confidence": characterization.confidence,
            "prototype_risk_index": characterization.prototype_risk_index,
            "evidence_components": comp.model_dump(),
            "supporting_factors": characterization.supporting_factors,
            "suppressing_factors": characterization.suppressing_factors,
            "uncertainty_factors": characterization.uncertainty_factors,
            "explanation": characterization.explanation,
        })

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "data", "synthetic", "audit", "phase7_synthetic_evaluation.json")
    )
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nSaved Phase 7 evaluation matrix to {out_path}")


if __name__ == "__main__":
    main()
