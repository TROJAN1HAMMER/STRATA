from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.db.database import get_db
from backend.app.db.models import Infrastructure, Observation
from backend.app.schemas.observation import ObservationCreate, ObservationRead

router = APIRouter(tags=["Observations"])


@router.post(
    "/observations",
    response_model=ObservationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit satellite observation epoch",
)
def submit_observation(
    payload: ObservationCreate,
    db: Session = Depends(get_db),
) -> Observation:
    # Ensure foreign key integrity
    infra = db.query(Infrastructure).filter(Infrastructure.id == payload.infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Cannot record observation: Infrastructure asset '{payload.infrastructure_id}' does not exist.",
        )

    obs = Observation(
        infrastructure_id=payload.infrastructure_id,
        acquisition_timestamp=payload.acquisition_timestamp,
        deformation_mm=payload.deformation_mm,
        velocity_mm_per_year=payload.velocity_mm_per_year,
        coherence=payload.coherence,
        phase_quality=payload.phase_quality,
        incidence_angle=payload.incidence_angle,
        los_displacement_mm=payload.los_displacement_mm,
        atmospheric_indicator=payload.atmospheric_indicator,
        source=payload.source,
        observation_metadata=payload.metadata,
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs


@router.get(
    "/infrastructure/{infrastructure_id}/observations",
    response_model=List[ObservationRead],
    summary="Get chronological observation history for an infrastructure asset",
)
def get_observation_history(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> List[Observation]:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )

    observations = (
        db.query(Observation)
        .filter(Observation.infrastructure_id == infrastructure_id)
        .order_by(Observation.acquisition_timestamp.asc())
        .all()
    )
    return observations
