from backend.app.services.synthetic.generator import generate_all_scenarios
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine

def run_benchmarks():
    scenarios = generate_all_scenarios()
    engine = PhysicsInSARConsistencyEngine()

    print(f"{'Scenario':<28} | {'Classification':<35} | {'Structural (P/D)':<20} | {'Environmental':<15} | {'Atmospheric':<12}")
    print("-" * 118)

    for key, sc in scenarios.items():
        obs_list = [
            ObservationRead.model_validate(dict(obs, id=f"{key}_{i}", infrastructure_id=f"infra_{key}", created_at=obs["acquisition_timestamp"]))
            for i, obs in enumerate(sc["observations"])
        ]
        seq = ObservationSequence(infrastructure_id=f"infra_{key}", observations=obs_list, epoch_count=len(obs_list))
        res = engine.evaluate_sequence(seq)

        p = res.temporal_evidence.persistence
        d = res.temporal_evidence.directional_consistency
        struct_str = f"P={p:.2f}, D={d:.2f}" if p is not None and d is not None else "N/A"
        env_str = f"Score={res.environmental_evidence.environmental_suspect_score:.2f}"
        atm_str = f"Score={res.atmospheric_evidence.atmospheric_suspect_score:.2f}"

        print(f"{key:<28} | {res.classification.value:<35} | {struct_str:<20} | {env_str:<15} | {atm_str:<12}")

if __name__ == "__main__":
    run_benchmarks()
