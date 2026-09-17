import json
import math
import os
import random
import tempfile
from datetime import datetime
import pytest

from backend.app.schemas.synthetic import (
    EpochGroundTruthDecomposition,
    GroundTruthClass,
    SyntheticEpoch,
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
from data.synthetic.generate_dataset import generate_full_dataset
from data.synthetic.validate_dataset import validate_synthetic_dataset


ALL_BUILDERS = [
    (GroundTruthClass.STABLE, generate_stable_sequence),
    (GroundTruthClass.STRUCTURAL_MONOTONIC, generate_structural_monotonic_sequence),
    (GroundTruthClass.STRUCTURAL_ACCELERATING, generate_structural_accelerating_sequence),
    (GroundTruthClass.SEASONAL_ENVIRONMENTAL, generate_seasonal_sequence),
    (GroundTruthClass.ATMOSPHERIC_TRANSIENT, generate_atmospheric_transient_sequence),
    (GroundTruthClass.LOW_QUALITY, generate_low_quality_sequence),
    (GroundTruthClass.TEMPORALLY_INCONSISTENT, generate_temporally_inconsistent_sequence),
]


def test_all_scenario_generators_correct_class():
    """Verify each builder generates sequences with matching GroundTruthClass."""
    rng = random.Random(42)
    config = PROTOTYPE_ASSUMPTIONS

    for expected_gt, builder in ALL_BUILDERS:
        sample = builder(
            sample_id=f"TEST_{expected_gt.value}",
            rng=rng,
            config=config,
            is_edge_case=False,
        )
        assert sample.ground_truth_class == expected_gt
        assert len(sample.epochs) >= 2
        assert sample.epoch_count == len(sample.epochs)


def test_builders_decomposition_mathematical_identity():
    """Verify observed_displacement == structural + environmental + atmospheric + noise."""
    rng = random.Random(101)
    config = PROTOTYPE_ASSUMPTIONS

    for _, builder in ALL_BUILDERS:
        sample = builder(
            sample_id="DECOMP_TEST",
            rng=rng,
            config=config,
            is_edge_case=False,
        )
        for ep in sample.epochs:
            gt = ep.ground_truth
            reconstructed = (
                gt.true_structural_displacement_mm
                + gt.true_environmental_displacement_mm
                + gt.true_atmospheric_displacement_mm
                + gt.true_noise_mm
            )
            assert abs(ep.observed_displacement_mm - reconstructed) < 1e-4
            assert abs(ep.observed_displacement_mm - gt.total_reconstructed_displacement_mm) < 1e-4


def test_reproducibility_with_fixed_seed():
    """Verify deterministic reproducibility when given the same random seed."""
    config = PROTOTYPE_ASSUMPTIONS

    rng1 = random.Random(9999)
    sample1 = generate_structural_monotonic_sequence("REPRO_1", rng1, config)

    rng2 = random.Random(9999)
    sample2 = generate_structural_monotonic_sequence("REPRO_1", rng2, config)

    assert sample1.epoch_count == sample2.epoch_count
    assert sample1.parameters == sample2.parameters
    for ep1, ep2 in zip(sample1.epochs, sample2.epochs):
        assert ep1.observed_displacement_mm == ep2.observed_displacement_mm
        assert ep1.coherence == ep2.coherence
        assert ep1.ground_truth.true_structural_displacement_mm == ep2.ground_truth.true_structural_displacement_mm
        assert ep1.ground_truth.true_noise_mm == ep2.ground_truth.true_noise_mm


def test_chronological_ordering():
    """Verify all epochs have strictly monotonically increasing acquisition timestamps."""
    rng = random.Random(2025)
    config = PROTOTYPE_ASSUMPTIONS

    for _, builder in ALL_BUILDERS:
        sample = builder("CHRONO_TEST", rng, config)
        prev_dt = None
        for ep in sample.epochs:
            dt = datetime.fromisoformat(ep.acquisition_timestamp)
            if prev_dt:
                assert dt > prev_dt, f"Epoch {ep.epoch_id} timestamp {dt} is not after {prev_dt}"
            prev_dt = dt


def test_valid_physical_ranges():
    """Verify physical ranges: coherence in [0, 1], incidence angles valid, no NaN/Inf."""
    rng = random.Random(777)
    config = PROTOTYPE_ASSUMPTIONS

    for _, builder in ALL_BUILDERS:
        sample = builder("RANGE_TEST", rng, config)
        for ep in sample.epochs:
            assert 0.0 <= ep.coherence <= 1.0
            assert 0.0 <= ep.phase_quality <= 1.0
            assert 15.0 <= ep.incidence_angle_deg <= 60.0
            assert not math.isnan(ep.observed_displacement_mm)
            assert not math.isinf(ep.observed_displacement_mm)
            assert not math.isnan(ep.los_displacement_mm)


def test_edge_case_generation():
    """Verify edge-case samples are flagged and have valid components."""
    rng = random.Random(888)
    config = PROTOTYPE_ASSUMPTIONS

    sample = generate_structural_monotonic_sequence(
        sample_id="EDGE_MONOTONIC",
        rng=rng,
        config=config,
        is_edge_case=True,
        edge_case_type="weak_structural_near_noise",
    )
    assert sample.is_edge_case is True
    assert sample.edge_case_type == "weak_structural_near_noise"

    # Verify decomposition still holds on edge case
    for ep in sample.epochs:
        gt = ep.ground_truth
        reconstructed = gt.total_reconstructed_displacement_mm
        assert abs(ep.observed_displacement_mm - reconstructed) < 1e-4


def test_public_observation_conversion_safety():
    """Verify to_public_observation_dict removes ground_truth container to prevent leakage."""
    rng = random.Random(42)
    sample = generate_seasonal_sequence("SAFETY_TEST", rng)
    ep = sample.epochs[0]

    public_dict = ep.to_public_observation_dict("INFRA_123")
    assert "ground_truth" not in public_dict
    assert "true_structural_displacement_mm" not in public_dict
    assert "true_noise_mm" not in public_dict
    assert public_dict["infrastructure_id"] == "INFRA_123"
    assert public_dict["source"] == "SYNTHETIC"
    assert "deformation_mm" in public_dict


def test_full_dataset_generation_and_validation():
    """Test full dataset generation CLI function and automated validation tool on a small partition."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dataset_dir = os.path.join(tmpdir, "dataset")
        metadata = generate_full_dataset(
            samples_per_class=20,  # Small test size: 20 * 7 = 140
            seed=123,
            output_dir=dataset_dir,
        )

        assert metadata["total_samples"] == 140
        assert metadata["splits"]["train"] == 14 * 7  # 14 * 7 = 98
        assert metadata["splits"]["validation"] == 3 * 7  # 3 * 7 = 21
        assert metadata["splits"]["test"] == 3 * 7  # 3 * 7 = 21

        metadata_path = os.path.join(tmpdir, "metadata.json")
        assert os.path.exists(metadata_path)

        # Run validation tool
        is_valid, issues = validate_synthetic_dataset(
            dataset_dir=dataset_dir,
            metadata_path=metadata_path,
        )
        assert is_valid, f"Validation issues: {issues}"
        assert len(issues) == 0
