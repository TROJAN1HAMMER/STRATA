#!/usr/bin/env python3
"""
STRATA — End-to-End Analytical Pipeline Demonstration (Phase 9).

Executes the full, hardened STRATA pipeline on a deterministic infrastructure
sequence:
  1. Input Validation & Bounds Enforcement
  2. InSAR Normalization & Geometry Preservation
  3. Frozen ML Deformation Classifier
  4. Deterministic Physics InSAR Consistency Engine
  5. Cross-Model Consensus Fusion
  6. Multi-Epoch Temporal Kinematics & Acceleration Guard
  7. Infrastructure-Specific Risk Characterization
  8. SHA-256 Tamper-Evident Evidence Chronicle Append
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
    parser = argparse.ArgumentParser(description="Run STRATA End-to-End Pipeline Demonstration")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON result")
    parser.add_argument("--scenario", choices=["stable", "subsidence", "seasonal"], default="subsidence", help="Scenario to execute")
    args = parser.parse_args()

    # 1. Setup in-memory SQLite database
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 2. Register test infrastructure asset
        infra_id = "infra_demo_golden_gate"
        inf = Infrastructure(
            id=infra_id,
            name="Approach Viaduct Pier 4",
            structure_type=StructureType.BRIDGE,
            material=MaterialType.STEEL,
            criticality=CriticalityLevel.HIGH,
            latitude=37.8199,
            longitude=-122.4783,
            description="Steel approach viaduct supporting northern approach spans.",
            historical_baseline={
                "baseline_mean_mm": 0.0,
                "baseline_std_mm": 1.2,
                "baseline_period_days": 365.0,
            },
            critical_zones=[
                {
                    "zone_id": "pier_4_bearing",
                    "zone_name": "Pier 4 Expansion Bearing",
                    "zone_type": "FOUNDATION",
                    "importance_weight": 1.4,
                }
            ],
            profile_version="v1.0.0",
        )
        db.add(inf)
        db.commit()

        # 3. Seed multi-epoch InSAR observation sequence
        if args.scenario == "subsidence":
            displacements = [-0.5, -1.8, -3.1, -4.9, -6.8, -8.7, -10.5, -12.4]
        elif args.scenario == "seasonal":
            displacements = [0.0, 4.2, 5.8, 3.9, -0.2, -4.1, -5.9, -3.8]
        else:
            displacements = [0.1, -0.2, 0.0, 0.3, -0.1, 0.2, -0.1, 0.0]

        start_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        created_obs = []
        for i, d in enumerate(displacements):
            t = start_time + timedelta(days=i * 12)
            obs = Observation(
                id=f"obs_demo_{i:03d}",
                infrastructure_id=infra_id,
                acquisition_timestamp=t,
                deformation_mm=float(d),
                los_displacement_mm=float(d),
                velocity_mm_per_year=-15.0 if args.scenario == "subsidence" else 0.0,
                coherence=0.86,
                phase_quality=0.91,
                incidence_angle=36.5,
                source="SENTINEL_1",
            )
            db.add(obs)
            created_obs.append(obs)
        db.commit()

        target_obs = created_obs[-1]

        # 4. Execute End-to-End Pipeline
        pipeline = STRATAAnalysisPipeline()
        result = pipeline.execute_for_observation(db, target_obs.id)

        # 5. Verify Chronology Chain Integrity
        chronicle_service = EvidenceChronicleService()
        records = db.query(ChronologyRecord).filter(
            ChronologyRecord.observation_id.in_([o.id for o in created_obs])
        ).order_by(ChronologyRecord.record_index.asc()).all()
        is_chain_valid, chain_err = chronicle_service.verify_chain_enhanced(records)

        # 6. Presentation
        if args.json:
            out = {
                "pipeline_version": PIPELINE_VERSION,
                "analysis_id": result.analysis_id,
                "observation_id": result.observation_id,
                "infrastructure_id": result.infrastructure_id,
                "status": result.processing_status.value,
                "stage_timings": result.stage_timings.model_dump(),
                "normalized_deformation_mm": result.normalized_observation.normalized_deformation_mm,
                "ml_prediction": {
                    "class": result.ml_result.predicted_class.value,
                    "confidence": result.ml_result.confidence,
                },
                "physics_classification": result.physics_evidence.get("classification"),
                "consensus": {
                    "category": result.consensus_assessment.consensus_class.value,
                    "confidence": result.consensus_assessment.consensus_confidence,
                    "agreement_score": result.consensus_assessment.agreement_score,
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
            }
            print(json.dumps(out, indent=2))
        else:
            print("=" * 78)
            print(f"STRATA — INTEGRATED PIPELINE DEMONSTRATION (v{PIPELINE_VERSION})")
            print("=" * 78)
            print(f"Infrastructure:     {inf.name} ({inf.structure_type.value}, {inf.material.value})")
            print(f"Observation ID:     {target_obs.id} (Epoch 8 of 8)")
            print(f"Acquisition Time:   {target_obs.acquisition_timestamp.isoformat()}")
            print(f"Raw LOS Disp:       {target_obs.deformation_mm:.2f} mm | Coherence: {target_obs.coherence:.2f}")
            print("-" * 78)
            print("ANALYTICAL ENGINE RESULTS:")
            print(f"  • InSAR Normalization:   {result.normalized_observation.normalized_deformation_mm:.2f} mm vertical")
            print(f"  • ML Classifier:         {result.ml_result.predicted_class.value} (conf={result.ml_result.confidence:.2f})")
            print(f"  • Physics Engine:        {result.physics_evidence.get('classification')}")
            print(f"  • Cross-Model Consensus: {result.consensus_assessment.consensus_class.value} (conf={result.consensus_assessment.consensus_confidence:.2f}, agreement={result.consensus_assessment.agreement_score:.2f})")
            print(f"  • Temporal Kinematics:   {result.temporal_summary.temporal_status.value} (accel_supported={result.temporal_summary.acceleration_supported})")
            print(f"  • Risk Characterization: {result.risk_characterization.characterization_state.value} [Index: {result.risk_characterization.prototype_risk_index:.1f}/100]")
            print("-" * 78)
            print("EXPLANATORY CHARACTERIZATION:")
            print(f"  \"{result.risk_characterization.explanation}\"")
            print("-" * 78)
            print("CHRONOLOGY & INTEGRITY AUDIT:")
            print(f"  • Record Index:          {result.chronology_record.record_index}")
            print(f"  • SHA-256 Current Hash:  {result.chronology_record.current_hash}")
            print(f"  • SHA-256 Previous Hash: {result.chronology_record.previous_hash}")
            print(f"  • Chain Integrity Valid: {is_chain_valid} (Error: {chain_err})")
            print("-" * 78)
            print(f"EXECUTION LATENCY: {result.stage_timings.total_ms:.2f} ms total")
            print(f"  [Validation: {result.stage_timings.validation_ms:.2f}ms | Normalization: {result.stage_timings.normalization_ms:.2f}ms | ML: {result.stage_timings.ml_ms:.2f}ms | Physics: {result.stage_timings.physics_ms:.2f}ms | Consensus: {result.stage_timings.consensus_ms:.2f}ms | Temporal: {result.stage_timings.temporal_ms:.2f}ms | Risk: {result.stage_timings.characterization_ms:.2f}ms | Chronology: {result.stage_timings.chronology_ms:.2f}ms]")
            print("=" * 78)
            print("DISCLAIMER: Prototype analytical characterization index for engineering evaluation only.")
            print("            Does NOT indicate failure probability, remaining life, or structural safety certification.")
            print("=" * 78)

    finally:
        db.close()


if __name__ == "__main__":
    main()
