from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List
import json
import os


def generate_all_scenarios(base_date: datetime = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)) -> Dict[str, Any]:
    """
    Generates deterministic benchmark observation scenarios (A through F)
    for STRATA InSAR Physics Consistency Engine evaluation.
    All data explicitly marked source='SYNTHETIC'.
    """
    scenarios: Dict[str, Any] = {}

    # Scenario A: Stable Structure
    scenarios["SCENARIO_A_STABLE"] = {
        "scenario_id": "SCENARIO_A_STABLE",
        "description": "Stable civil structure with high interferometric coherence and displacements within noise floor",
        "expected_classification": "STABLE_NO_SIGNIFICANT_DEFORMATION",
        "infrastructure": {
            "name": "Benchmark Dam Alpha (Stable)",
            "structure_type": "DAM",
            "latitude": 37.7749,
            "longitude": -122.4194,
            "description": "Synthetic benchmark for stable infrastructure baseline",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=12 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": -0.5,
                "coherence": 0.88,
                "phase_quality": 0.90,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "CLEAR_NOMINAL",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "A", "epoch_idx": i, "is_simulated": True},
            }
            for i, disp in enumerate([-0.2, 0.1, -0.3, 0.2, -0.1])
        ],
    }

    # Scenario B: Persistent Structural Deformation
    scenarios["SCENARIO_B_PERSISTENT"] = {
        "scenario_id": "SCENARIO_B_PERSISTENT",
        "description": "Monotonic structural settlement with high coherence and persistent negative displacement",
        "expected_classification": "STRUCTURALLY_CONSISTENT",
        "infrastructure": {
            "name": "Benchmark Bridge Beta (Persistent Settlement)",
            "structure_type": "BRIDGE",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "Synthetic benchmark for continuous structural settlement",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=12 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": -7.5,
                "coherence": 0.82,
                "phase_quality": 0.85,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "CLEAR_STABLE",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "B", "epoch_idx": i, "is_simulated": True},
            }
            for i, disp in enumerate([-2.0, -4.5, -7.1, -9.8, -12.4])
        ],
    }

    # Scenario C: Atmospheric-Like Anomaly
    scenarios["SCENARIO_C_ATMOSPHERIC"] = {
        "scenario_id": "SCENARIO_C_ATMOSPHERIC",
        "description": "Isolated sharp transient spikes that immediately revert to baseline, typical of tropospheric turbulence",
        "expected_classification": "ATMOSPHERICALLY_SUSPECT",
        "infrastructure": {
            "name": "Benchmark Retaining Wall Gamma (Atmospheric Anomaly)",
            "structure_type": "RETAINING_WALL",
            "latitude": 34.0522,
            "longitude": -118.2437,
            "description": "Synthetic benchmark for atmospheric turbulence contamination",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=12 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": 0.0,
                "coherence": 0.78,
                "phase_quality": 0.75,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "HIGH_TROPOSPHERIC_TURBULENCE" if i in [1, 3] else "CLEAR_NOMINAL",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "C", "epoch_idx": i, "is_simulated": True},
            }
            for i, disp in enumerate([-0.2, -8.5, -0.6, 7.2, 0.1])
        ],
    }

    # Scenario D: Seasonal Pattern
    scenarios["SCENARIO_D_SEASONAL"] = {
        "scenario_id": "SCENARIO_D_SEASONAL",
        "description": "Periodic thermal / reservoir loading cycle with zero net structural deterioration",
        "expected_classification": "SEASONALLY_SUSPECT",
        "infrastructure": {
            "name": "Benchmark Arch Dam Delta (Seasonal Cycle)",
            "structure_type": "DAM",
            "latitude": 46.8182,
            "longitude": 8.2275,
            "description": "Synthetic benchmark for cyclic environmental / seasonal response",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=24 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": 0.0,
                "coherence": 0.85,
                "phase_quality": 0.88,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "CLEAR_NOMINAL",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "D", "epoch_idx": i, "is_simulated": True},
            }
            for i, disp in enumerate([3.5, 6.5, 8.0, 4.5, 0.0, -4.5, -7.5, -6.0, -2.0, 2.5])
        ],
    }

    # Scenario E: Low Quality
    scenarios["SCENARIO_E_LOW_QUALITY"] = {
        "scenario_id": "SCENARIO_E_LOW_QUALITY",
        "description": "Radar decorrelation noise floor with coherence below 0.25 and degraded phase quality",
        "expected_classification": "LOW_QUALITY",
        "infrastructure": {
            "name": "Benchmark Bridge Epsilon (Decorrelated)",
            "structure_type": "BRIDGE",
            "latitude": 51.5074,
            "longitude": -0.1278,
            "description": "Synthetic benchmark for noise-dominated decorrelated radar signal",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=12 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": -2.0,
                "coherence": coh,
                "phase_quality": 0.22,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "APS_DATA_UNAVAILABLE",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "E", "epoch_idx": i, "is_simulated": True},
            }
            for i, (disp, coh) in enumerate([
                (-1.5, 0.18),
                (-3.2, 0.21),
                (-2.0, 0.15),
                (-4.5, 0.22),
                (-3.0, 0.19),
            ])
        ],
    }

    # Scenario F: Accelerating Deformation
    scenarios["SCENARIO_F_ACCELERATING"] = {
        "scenario_id": "SCENARIO_F_ACCELERATING",
        "description": "Persistent deformation where epoch-to-epoch step size expands continuously",
        "expected_classification": "STRUCTURALLY_CONSISTENT",
        "infrastructure": {
            "name": "Benchmark Retaining Wall Zeta (Accelerating Creep)",
            "structure_type": "RETAINING_WALL",
            "latitude": 45.4642,
            "longitude": 9.1900,
            "description": "Synthetic benchmark for accelerating deformation trend",
        },
        "observations": [
            {
                "acquisition_timestamp": (base_date + timedelta(days=12 * i)).isoformat(),
                "deformation_mm": disp,
                "los_displacement_mm": round(disp * 0.82, 3),
                "velocity_mm_per_year": -15.0,
                "coherence": 0.81,
                "phase_quality": 0.84,
                "incidence_angle": 35.0,
                "atmospheric_indicator": "CLEAR_STABLE",
                "source": "SYNTHETIC",
                "metadata": {"scenario": "F", "epoch_idx": i, "is_simulated": True},
            }
            for i, disp in enumerate([-1.0, -2.5, -5.0, -9.0, -15.0, -24.0])
        ],
    }

    return scenarios


def save_scenarios_to_file(output_path: str) -> None:
    data = generate_all_scenarios()
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "..", "data", "synthetic", "scenarios.json"))
    save_scenarios_to_file(target_path)
