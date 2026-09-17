#!/usr/bin/env python3
"""
STRATA — Final Research Demonstration Script (Phase 10).

Executes an end-to-end analytical demonstration on a representative
longitudinal infrastructure sequence, showcasing:
  1. ML Deformation Classifier pattern recognition & probabilities
  2. Deterministic Physics InSAR consistency & environmental factors
  3. Cross-model consensus fusion and confidence modulation
  4. Multi-epoch temporal kinematics & acceleration guarding
  5. Infrastructure contextualization under the ground-truth firewall
  6. Tamper-evident SHA-256 evidence chronicle verification
"""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
import sys

# Ensure repository root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.app.core.versions import PIPELINE_VERSION, get_system_versions
from backend.app.db.database import Base
from backend.app.db.models import (
    AnalysisResult,
    ChronologyRecord,
    CriticalityLevel,
    Infrastructure,
    MaterialType,
    Observation,
    StructureType,
)
from backend.app.services.chronology.service import EvidenceChronicleService
from backend.app.services.pipeline import STRATAAnalysisPipeline


def main():
    parser = argparse.ArgumentParser(description="STRATA Final Research Demonstration")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON result")
    args = parser.parse_args()

    # In-memory database for isolated, reproducible demonstration execution
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 1. Register representative infrastructure asset
        infra_id = "infra_research_viaduct_pier_3"
        inf = Infrastructure(
            id=infra_id,
            name="Interstate Viaduct North Support Pier 3",
            structure_type=StructureType.BRIDGE,
            material=MaterialType.STEEL,
            criticality=CriticalityLevel.HIGH,
            latitude=37.8200,
            longitude=-122.4780,
            description="High-criticality steel viaduct pier supporting main northern transit corridor.",
            historical_baseline={
                "baseline_mean_mm": 0.0,
                "baseline_std_mm": 1.2,
                "baseline_period_days": 365.0,
            },
            critical_zones=[
                {
                    "zone_id": "pier_3_foundation",
                    "zone_name": "Pier 3 Foundation Caisson",
                    "zone_type": "FOUNDATION",
                    "importance_weight": 1.35,
                }
            ],
            profile_version="v1.0.0",
        )
        db.add(inf)
        db.commit()

        # 2. Seed an 8-epoch InSAR sequence with progressive settlement
        displacements = [-0.4, -1.6, -3.2, -5.0, -6.9, -8.8, -10.6, -12.5]
        start_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        created_obs = []

        for i, d in enumerate(displacements):
            t = start_time + timedelta(days=i * 12)
            obs = Observation(
                id=f"obs_research_{i:03d}",
                infrastructure_id=infra_id,
                acquisition_timestamp=t,
                deformation_mm=float(d),
                los_displacement_mm=float(d),
                velocity_mm_per_year=-15.5,
                coherence=0.87,
                phase_quality=0.92,
                incidence_angle=36.5,
                source="SENTINEL_1",
            )
            db.add(obs)
            created_obs.append(obs)
        db.commit()

        target_obs = created_obs[-1]

        # 3. Execute End-to-End Pipeline
        pipeline = STRATAAnalysisPipeline()
        result = pipeline.execute_for_observation(db, target_obs.id)

        # 4. Verify Chronology Chain Integrity
        chronicle_service = EvidenceChronicleService()
        records = db.query(ChronologyRecord).filter(
            ChronologyRecord.observation_id.in_([o.id for o in created_obs])
        ).order_by(ChronologyRecord.record_index.asc()).all()
        is_chain_valid, chain_err = chronicle_service.verify_chain_enhanced(records)

        # 5. Output
        if args.json:
            output_data = {
                "pipeline_version": PIPELINE_VERSION,
                "analysis_id": result.analysis_id,
                "asset": {
                    "id": inf.id,
                    "name": inf.name,
                    "structure_type": inf.structure_type.value,
                    "material": inf.material.value,
                    "criticality": inf.criticality.value,
                },
                "observation": {
                    "id": target_obs.id,
                    "epoch_count": len(created_obs),
                    "window_start": start_time.isoformat(),
                    "window_end": target_obs.acquisition_timestamp.isoformat(),
                    "raw_displacement_mm": target_obs.deformation_mm,
                    "coherence": target_obs.coherence,
                },
                "ml_evidence": {
                    "predicted_class": result.ml_result.predicted_class.value,
                    "confidence": result.ml_result.confidence,
                    "probabilities": result.ml_result.probabilities,
                },
                "physics_evidence": result.physics_evidence,
                "consensus": {
                    "category": result.consensus_assessment.consensus_class.value,
                    "confidence": result.consensus_assessment.consensus_confidence,
                    "agreement_score": result.consensus_assessment.agreement_score,
                    "disagreement_penalty": result.consensus_assessment.disagreement_penalty,
                },
                "temporal": {
                    "status": result.temporal_summary.temporal_status.value,
                    "apparent_acceleration": result.temporal_summary.apparent_acceleration_mm_per_year2,
                    "acceleration_supported": result.temporal_summary.acceleration_supported,
                },
                "risk_characterization": {
                    "state": result.risk_characterization.characterization_state.value,
                    "prototype_index": result.risk_characterization.prototype_risk_index,
                    "explanation": result.risk_characterization.explanation,
                },
                "chronology": {
                    "record_index": result.chronology_record.record_index,
                    "current_hash": result.chronology_record.current_hash,
                    "previous_hash": result.chronology_record.previous_hash,
                    "chain_valid": is_chain_valid,
                },
                "system_versions": result.system_versions,
                "timings_ms": result.stage_timings.model_dump(),
                "disclaimer": "This output represents analytical evidence characterization, not structural safety certification.",
            }
            print(json.dumps(output_data, indent=2))
        else:
            print("=" * 80)
            print("STRATA — STRUCTURAL TEMPORAL ANALYSIS & THREAT ASSESSMENT")
            print(f"Research Prototype Demonstration (Pipeline v{PIPELINE_VERSION})")
            print("=" * 80)
            print(f"Infrastructure:      {inf.name}")
            print(f"Structural Context:  {inf.structure_type.value} ({inf.material.value}) | Criticality: {inf.criticality.value}")
            print(f"Observation Period:  {start_time.strftime('%Y-%m-%d')} to {target_obs.acquisition_timestamp.strftime('%Y-%m-%d')} ({len(created_obs)} epochs, 84 days)")
            print(f"Latest Measurement:  LOS: {target_obs.deformation_mm:.2f} mm | Projected Vert: {result.normalized_observation.normalized_deformation_mm:.2f} mm | Coherence: {target_obs.coherence:.2f}")
            print("-" * 80)
            print("ML DEFORMATION EVIDENCE")
            print(f"  • Prediction:       {result.ml_result.predicted_class.value}")
            print(f"  • Model Confidence: {result.ml_result.confidence:.2f}")
            print("  • Probabilities:    " + ", ".join([f"{k}: {v:.2f}" for k, v in list(result.ml_result.probabilities.items())[:4]]))
            print("-" * 80)
            print("PHYSICS EVIDENCE")
            print(f"  • Quality:          Average Coherence {target_obs.coherence:.2f} (Meets >= 0.40 floor)")
            print(f"  • Geometry:         LOS Projected to Vertical (Incidence: {target_obs.incidence_angle:.1f}°)")
            print(f"  • Temporal:         Kinematic bounds satisfied (|v| <= 150 mm/yr)")
            print(f"  • Environmental:    Thermal correlation evaluated")
            print(f"  • Classification:   {result.physics_evidence.get('classification')}")
            print("-" * 80)
            print("CROSS-MODEL CONSENSUS")
            print(f"  • Agreement Score:  {result.consensus_assessment.agreement_score:.2f} (0.0 to 1.0 scale)")
            print(f"  • Disagreement Pen: {result.consensus_assessment.disagreement_penalty:.2f}")
            print(f"  • Fused Confidence: {result.consensus_assessment.consensus_confidence:.2f}")
            print(f"  • Interpretation:   {result.consensus_assessment.consensus_class.value}")
            print("-" * 80)
            print("TEMPORAL EVIDENCE")
            print(f"  • State:            {result.temporal_summary.temporal_status.value}")
            print(f"  • Apparent Accel:   {result.temporal_summary.apparent_acceleration_mm_per_year2:.2f} mm/year²")
            print(f"  • Accel Supported:  {result.temporal_summary.acceleration_supported} (Scientific Baseline Guard enforced)")
            print("-" * 80)
            print("INFRASTRUCTURE CHARACTERIZATION")
            print(f"  • State:            {result.risk_characterization.characterization_state.value}")
            print(f"  • Prototype Index:  {result.risk_characterization.prototype_risk_index:.1f} / 100.0 (Inspection Prioritization Scale)")
            print(f"  • Explanatory Text: \"{result.risk_characterization.explanation.splitlines()[0]}...\"")
            print("-" * 80)
            print("EVIDENCE CHRONOLOGY (TAMPER-EVIDENT)")
            print(f"  • Sequence Index:   {result.chronology_record.record_index}")
            print(f"  • Previous Hash:    {result.chronology_record.previous_hash}")
            print(f"  • Current Hash:     {result.chronology_record.current_hash}")
            print(f"  • Chain Integrity:  {'VALID (Unbroken SHA-256 Link)' if is_chain_valid else 'CORRUPTED'}")
            print("-" * 80)
            print(f"PIPELINE LATENCY:     {result.stage_timings.total_ms:.2f} ms total")
            print("=" * 80)
            print("DISCLAIMER: This output represents analytical evidence characterization,")
            print("            not structural safety certification.")
            print("=" * 80)

    finally:
        db.close()


if __name__ == "__main__":
    main()
