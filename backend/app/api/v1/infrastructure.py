"""
Infrastructure management and longitudinal evidence endpoints.
Provides infrastructure registration, listing, chronology auditing, and temporal evidence summaries.
"""
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.db.database import get_db
from backend.app.db.models import (
    ChronologyRecord,
    Infrastructure,
    Observation,
    RiskCharacterization,
    StructureType,
    MaterialType,
    CriticalityLevel,
)
from backend.app.schemas.analysis import ChronologyRecordRead
from backend.app.schemas.infrastructure import (
    InfrastructureCreate,
    InfrastructureRead,
    InfrastructureUpdate,
)
from backend.app.schemas.risk import (
    CriticalZone,
    HistoricalBaseline,
    CalibrationProfile,
    ExpectedDeformationBehavior,
    InfrastructureProfileRead,
    InfrastructureProfileUpdate,
    RiskCharacterizationRead,
)
from backend.app.schemas.temporal import (
    ChronologyVerificationResult,
    TemporalEvidenceSummary,
)
from backend.app.services.chronology import EvidenceChronicleService
from backend.app.services.temporal import TemporalEvidenceEngine
from backend.app.services.risk import InfrastructureRiskCharacterizationEngine

router = APIRouter(prefix="/infrastructure", tags=["Infrastructure"])

chronicle_service = EvidenceChronicleService()
temporal_engine = TemporalEvidenceEngine()
risk_engine = InfrastructureRiskCharacterizationEngine(temporal_engine=temporal_engine)


@router.post(
    "",
    response_model=InfrastructureRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register new infrastructure asset",
)
def create_infrastructure(
    payload: InfrastructureCreate,
    db: Session = Depends(get_db),
) -> Infrastructure:
    infra = Infrastructure(
        name=payload.name,
        structure_type=payload.structure_type,
        material=payload.material,
        criticality=payload.criticality,
        latitude=payload.latitude,
        longitude=payload.longitude,
        description=payload.description,
        expected_behavior=[b.value for b in payload.expected_behavior] if payload.expected_behavior else None,
        geometry_context=payload.geometry_context,
        critical_zones=[z.model_dump() for z in payload.critical_zones] if payload.critical_zones else None,
        historical_baseline=payload.historical_baseline.model_dump() if payload.historical_baseline else None,
        calibration_profile=payload.calibration_profile.model_dump() if payload.calibration_profile else None,
        profile_version=payload.profile_version or "v1.0.0",
    )
    db.add(infra)
    db.commit()
    db.refresh(infra)
    return infra


@router.get(
    "",
    response_model=List[InfrastructureRead],
    summary="List all monitored civil infrastructures",
)
def list_infrastructures(
    structure_type: Optional[StructureType] = Query(None, description="Filter by structural classification"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
) -> List[Infrastructure]:
    query = db.query(Infrastructure)
    if structure_type:
        query = query.filter(Infrastructure.structure_type == structure_type)
    return query.order_by(Infrastructure.created_at.desc()).offset(skip).limit(limit).all()


@router.get(
    "/{infrastructure_id}",
    response_model=InfrastructureRead,
    summary="Get infrastructure asset by ID",
)
def get_infrastructure(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> Infrastructure:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )
    return infra


@router.get(
    "/{infrastructure_id}/chronology",
    response_model=List[ChronologyRecordRead],
    summary="Retrieve chronological evidence records for an infrastructure asset",
)
def get_infrastructure_chronology(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> List[ChronologyRecord]:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )

    records = (
        db.query(ChronologyRecord)
        .join(Observation, ChronologyRecord.observation_id == Observation.id)
        .filter(Observation.infrastructure_id == infrastructure_id)
        .order_by(ChronologyRecord.record_index.asc())
        .all()
    )
    return records


@router.get(
    "/{infrastructure_id}/temporal-summary",
    response_model=TemporalEvidenceSummary,
    summary="Generate comprehensive longitudinal temporal evidence summary",
)
def get_infrastructure_temporal_summary(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> TemporalEvidenceSummary:
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

    summary = temporal_engine.evaluate_summary(
        infrastructure_id=infrastructure_id,
        observations=observations,
    )
    return summary


@router.get(
    "/{infrastructure_id}/chronology/verify",
    response_model=ChronologyVerificationResult,
    summary="Cryptographically verify SHA-256 evidence chain integrity for an asset",
)
def verify_infrastructure_chronology(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> ChronologyVerificationResult:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )

    is_valid, error, length = chronicle_service.verify_infrastructure_chain(db, infrastructure_id)
    return ChronologyVerificationResult(
        chain_length=length,
        is_intact=is_valid,
        verification_status="VALID" if is_valid else "CORRUPTED_OR_TAMPERED",
        error_detail=error,
        infrastructure_id=infrastructure_id,
    )


def _build_profile_read(infra: Infrastructure) -> InfrastructureProfileRead:
    cz_list: List[CriticalZone] = []
    if infra.critical_zones:
        for z in infra.critical_zones:
            cz_list.append(CriticalZone.model_validate(z) if isinstance(z, dict) else z)

    hb: Optional[HistoricalBaseline] = None
    if infra.historical_baseline:
        hb = HistoricalBaseline.model_validate(infra.historical_baseline) if isinstance(infra.historical_baseline, dict) else infra.historical_baseline

    cp = CalibrationProfile()
    if infra.calibration_profile:
        cp = CalibrationProfile.model_validate(infra.calibration_profile) if isinstance(infra.calibration_profile, dict) else infra.calibration_profile

    eb_list: List[ExpectedDeformationBehavior] = []
    if infra.expected_behavior:
        for b in infra.expected_behavior:
            if isinstance(b, ExpectedDeformationBehavior):
                eb_list.append(b)
            elif isinstance(b, str):
                try:
                    eb_list.append(ExpectedDeformationBehavior(b))
                except ValueError:
                    pass
    if not eb_list:
        eb_list = [ExpectedDeformationBehavior.UNKNOWN]

    return InfrastructureProfileRead(
        infrastructure_id=infra.id,
        name=infra.name,
        structure_type=infra.structure_type,
        material=infra.material or MaterialType.UNKNOWN,
        criticality=infra.criticality or CriticalityLevel.UNKNOWN,
        expected_behavior=eb_list,
        geometry_context=infra.geometry_context,
        critical_zones=cz_list,
        historical_baseline=hb,
        calibration_profile=cp,
        profile_version=infra.profile_version or "v1.0.0",
    )


@router.get(
    "/{infrastructure_id}/profile",
    response_model=InfrastructureProfileRead,
    summary="Retrieve civil infrastructure engineering profile",
)
def get_infrastructure_profile(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> InfrastructureProfileRead:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )
    return _build_profile_read(infra)


@router.post(
    "/{infrastructure_id}/profile",
    response_model=InfrastructureProfileRead,
    summary="Update civil infrastructure engineering profile",
)
def update_infrastructure_profile(
    infrastructure_id: str,
    payload: InfrastructureProfileUpdate,
    db: Session = Depends(get_db),
) -> InfrastructureProfileRead:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )

    if payload.structure_type is not None:
        infra.structure_type = payload.structure_type
    if payload.material is not None:
        infra.material = payload.material
    if payload.criticality is not None:
        infra.criticality = payload.criticality
    if payload.expected_behavior is not None:
        infra.expected_behavior = [b.value for b in payload.expected_behavior]
    if payload.geometry_context is not None:
        infra.geometry_context = payload.geometry_context
    if payload.critical_zones is not None:
        infra.critical_zones = [z.model_dump() for z in payload.critical_zones]
    if payload.historical_baseline is not None:
        infra.historical_baseline = payload.historical_baseline.model_dump()
    if payload.calibration_profile is not None:
        infra.calibration_profile = payload.calibration_profile.model_dump()
        infra.profile_version = payload.calibration_profile.profile_version

    db.commit()
    db.refresh(infra)
    return _build_profile_read(infra)


@router.post(
    "/{infrastructure_id}/risk-characterization",
    response_model=RiskCharacterizationRead,
    status_code=status.HTTP_201_CREATED,
    summary="Execute and persist infrastructure-specific risk characterization",
)
def create_infrastructure_risk_characterization(
    infrastructure_id: str,
    db: Session = Depends(get_db),
) -> RiskCharacterizationRead:
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

    characterization = risk_engine.evaluate_infrastructure(
        infrastructure=infra,
        observations=observations,
    )

    # Persist immutable record in database
    db_record = RiskCharacterization(
        id=characterization.id,
        infrastructure_id=infrastructure_id,
        observation_window_start=characterization.observation_window_start,
        observation_window_end=characterization.observation_window_end,
        epoch_count=characterization.epoch_count,
        characterization_state=characterization.characterization_state,
        confidence=characterization.confidence,
        prototype_risk_index=characterization.prototype_risk_index,
        evidence_components=characterization.evidence_components.model_dump(),
        supporting_factors=characterization.supporting_factors,
        suppressing_factors=characterization.suppressing_factors,
        uncertainty_factors=characterization.uncertainty_factors,
        explanation=characterization.explanation,
        version_metadata=characterization.version_metadata,
        created_at=characterization.created_at,
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)

    return characterization


@router.get(
    "/{infrastructure_id}/risk-characterization",
    response_model=Union[RiskCharacterizationRead, List[RiskCharacterizationRead]],
    summary="Retrieve latest risk characterization or history for an infrastructure asset",
)
def get_infrastructure_risk_characterization(
    infrastructure_id: str,
    history: bool = Query(False, description="If true, returns full chronological history; else returns latest"),
    db: Session = Depends(get_db),
) -> Any:
    infra = db.query(Infrastructure).filter(Infrastructure.id == infrastructure_id).first()
    if not infra:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Infrastructure asset with ID '{infrastructure_id}' not found.",
        )

    records = (
        db.query(RiskCharacterization)
        .filter(RiskCharacterization.infrastructure_id == infrastructure_id)
        .order_by(RiskCharacterization.created_at.desc())
        .all()
    )

    if history:
        result_list = []
        for r in records:
            result_list.append(
                RiskCharacterizationRead(
                    id=r.id,
                    infrastructure_id=r.infrastructure_id,
                    observation_window_start=r.observation_window_start,
                    observation_window_end=r.observation_window_end,
                    epoch_count=r.epoch_count,
                    characterization_state=r.characterization_state,
                    confidence=r.confidence,
                    prototype_risk_index=r.prototype_risk_index,
                    evidence_components=r.evidence_components,
                    supporting_factors=r.supporting_factors,
                    suppressing_factors=r.suppressing_factors,
                    uncertainty_factors=r.uncertainty_factors,
                    explanation=r.explanation,
                    version_metadata=r.version_metadata,
                    created_at=r.created_at,
                )
            )
        return result_list

    if records:
        r = records[0]
        return RiskCharacterizationRead(
            id=r.id,
            infrastructure_id=r.infrastructure_id,
            observation_window_start=r.observation_window_start,
            observation_window_end=r.observation_window_end,
            epoch_count=r.epoch_count,
            characterization_state=r.characterization_state,
            confidence=r.confidence,
            prototype_risk_index=r.prototype_risk_index,
            evidence_components=r.evidence_components,
            supporting_factors=r.supporting_factors,
            suppressing_factors=r.suppressing_factors,
            uncertainty_factors=r.uncertainty_factors,
            explanation=r.explanation,
            version_metadata=r.version_metadata,
            created_at=r.created_at,
        )

    # If no persisted evaluation exists yet, compute dynamically
    observations = (
        db.query(Observation)
        .filter(Observation.infrastructure_id == infrastructure_id)
        .order_by(Observation.acquisition_timestamp.asc())
        .all()
    )
    return risk_engine.evaluate_infrastructure(infrastructure=infra, observations=observations)

