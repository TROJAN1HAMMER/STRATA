from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models import (
    Infrastructure,
    Observation,
    PhysicsAssessment,
)
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import (
    ObservationSequence,
    PhysicsAssessmentRead,
    PhysicsEvidence,
)
from backend.app.services.chronology import EvidenceChronicleService
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine

router = APIRouter(tags=["Physics InSAR Engine"])

physics_engine = PhysicsInSARConsistencyEngine()
chronicle_service = EvidenceChronicleService()


@router.post(
    "/analysis/physics/{infrastructure_id}",
    response_model=PhysicsEvidence,
    status_code=status.HTTP_200_OK,
    summary="Execute deterministic multi-epoch InSAR physics consistency engine",
)
def analyze_infrastructure_physics(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> PhysicsEvidence:
    # 1. Fetch infrastructure
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset '{infrastructure_id}' not found.",
        )

    # 2. Fetch observations chronologically
    db_observations = (
        db.query(Observation)
        .filter(Observation.infrastructure_id == infrastructure_id)
        .order_by(Observation.acquisition_timestamp.asc())
        .all()
    )

    pydantic_observations = [ObservationRead.model_validate(obs) for obs in db_observations]

    start_time = pydantic_observations[0].acquisition_timestamp if pydantic_observations else None
    end_time = pydantic_observations[-1].acquisition_timestamp if pydantic_observations else None

    # 3. Construct multi-epoch observation sequence
    sequence = ObservationSequence(
        infrastructure_id=infrastructure_id,
        observations=pydantic_observations,
        start_time=start_time,
        end_time=end_time,
        epoch_count=len(pydantic_observations),
    )

    # 4. Run deterministic physics engine
    evidence = physics_engine.evaluate_sequence(sequence)

    # 5. Persist PhysicsAssessment entity
    assessment = PhysicsAssessment(
        infrastructure_id=infrastructure_id,
        classification=evidence.classification.value,
        overall_confidence=evidence.overall_confidence,
        epoch_count=len(pydantic_observations),
        evidence_payload=evidence.model_dump(mode="json"),
        provenance=evidence.provenance,
    )
    db.add(assessment)
    db.flush()

    # 6. Append to SHA-256 Longitudinal Evidence Chronicle if observations exist
    if db_observations:
        latest_obs_id = db_observations[-1].id
        chronicle_service.append_record(
            db=db,
            observation_id=latest_obs_id,
            analysis_result_id=assessment.id,
            analysis_summary={
                "classification": evidence.classification.value,
                "overall_confidence": evidence.overall_confidence,
                "epoch_count": len(pydantic_observations),
                "measurement_quality": evidence.measurement_quality.quality_score,
                "trend_pattern": evidence.temporal_evidence.trend_pattern.value,
            },
            processing_metadata={
                "engine": evidence.provenance.get("engine_name"),
                "version": evidence.provenance.get("engine_version"),
                "is_deterministic": True,
            },
        )

    db.commit()
    db.refresh(assessment)

    logger.info(
        f"Persisted Physics Assessment {assessment.id} for infrastructure {infrastructure_id}: "
        f"{evidence.classification.value}"
    )

    return evidence


@router.get(
    "/infrastructure/{infrastructure_id}/physics",
    response_model=PhysicsAssessmentRead,
    summary="Get latest InSAR physics consistency assessment for an infrastructure asset",
)
def get_latest_physics_assessment(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> PhysicsAssessment:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset '{infrastructure_id}' not found.",
        )

    assessment = (
        db.query(PhysicsAssessment)
        .filter(PhysicsAssessment.infrastructure_id == infrastructure_id)
        .order_by(PhysicsAssessment.created_at.desc())
        .first()
    )

    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No physics assessment has been generated for infrastructure '{infrastructure_id}'.",
        )

    return assessment
