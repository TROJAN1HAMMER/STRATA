from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.logging import logger
from backend.app.db.database import get_db
from backend.app.db.models import (
    AnalysisResult,
    ChronologyRecord,
    Observation,
)
from backend.app.schemas.analysis import (
    AnalysisPipelineResponse,
    AnalysisResultRead,
    ChronologyRecordRead,
)
from backend.app.schemas.consensus import ConsensusAssessment
from backend.app.schemas.ml import MLClassificationResult
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.services.insar import InSARNormalizationService
from backend.app.services.ml import StubMLDeformationEngine
from backend.app.services.ml.classifier import MLDeformationClassifier
from backend.app.services.physics import StubPhysicsConsistencyEngine
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.consensus import ConsensusEngine, StubConsensusEngine
from backend.app.services.chronology import EvidenceChronicleService
from backend.app.services.pipeline import (
    STRATAAnalysisPipeline,
    PipelineResult,
    PipelineExecutionError,
)

router = APIRouter(prefix="/analysis", tags=["Analysis"])

# Instantiating service singletons for dependency injection / execution
insar_service = InSARNormalizationService()
ml_engine = StubMLDeformationEngine()
physics_engine = StubPhysicsConsistencyEngine()
consensus_engine = StubConsensusEngine()
chronicle_service = EvidenceChronicleService()

# Phase 5 real decoupled analytical engines
real_physics_engine = PhysicsInSARConsistencyEngine()
real_ml_classifier = MLDeformationClassifier()
real_consensus_engine = ConsensusEngine()


def _evaluate_ml_safely(sequence: ObservationSequence) -> MLClassificationResult:
    if sequence.epoch_count < 2:
        all_gt = [c.value for c in GroundTruthClass]
        uniform_p = {c: round(1.0 / len(all_gt), 4) for c in all_gt}
        return MLClassificationResult(
            predicted_class=GroundTruthClass.STABLE,
            probabilities=uniform_p,
            confidence=round(1.0 / len(all_gt), 4),
            entropy=1.0,
            model_version=real_ml_classifier.metadata.model_version if real_ml_classifier.metadata else "strata_ml_v0_1_0",
            feature_version="strata_features_v0_1_0",
        )
    return real_ml_classifier.predict(sequence)


@router.post(
    "/{observation_id}",
    response_model=AnalysisPipelineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute multi-engine analysis pipeline on observation",
)
def analyze_observation(
    observation_id: str,
    db: Session = Depends(get_db),
) -> AnalysisPipelineResponse:
    # 1. Fetch observation
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )

    # 2. Count historical observations for this infrastructure to feed temporal evidence
    historical_count = (
        db.query(Observation)
        .filter(
            Observation.infrastructure_id == obs.infrastructure_id,
            Observation.acquisition_timestamp <= obs.acquisition_timestamp,
        )
        .count()
    )

    # 3. Execute InSAR Normalization & Feature Extraction (Phase 1 normalization active)
    insar_features = insar_service.normalize_observation(obs)

    # 4. Execute ML Deformation Classifier (Explicit Stub)
    ml_output = ml_engine.evaluate(insar_features)

    # 5. Execute Physics Consistency Engine (Sanity Boundary Check Stub)
    physics_output = physics_engine.verify_consistency(insar_features)

    # 6. Execute Consensus Engine (Pending Scientific Specification Stub)
    consensus_output = consensus_engine.evaluate_consensus(
        features=insar_features,
        ml_output=ml_output,
        physics_output=physics_output,
        historical_records_count=historical_count,
    )

    # 7. Persist AnalysisResult in DB
    component_breakdown: Dict[str, Any] = {
        "insar_normalization": {
            "is_implemented": True,
            "description": "Geometrical projection and parameter range validation",
            "is_sufficient_coherence": insar_features.is_sufficient_coherence,
            "projected_vertical_displacement_mm": insar_features.projected_vertical_displacement_mm,
            "warnings": insar_features.validation_warnings,
        },
        "ml_engine": {
            "is_implemented": False,
            "is_stub": ml_output.is_stub,
            "status": ml_output.status,
            "classification": ml_output.classification,
            "confidence": ml_output.confidence,
            "features_used": ml_output.features_used,
            "notice": ml_output.scientific_notice,
        },
        "physics_engine": {
            "is_implemented": False,
            "is_stub": physics_output.is_stub,
            "status": physics_output.status,
            "is_physically_admissible": physics_output.is_physically_admissible,
            "boundary_checks": physics_output.boundary_checks,
            "anomalies": physics_output.anomalies_detected,
            "notice": physics_output.scientific_notice,
        },
        "consensus_engine": {
            "is_implemented": False,
            "is_stub": consensus_output.is_stub,
            "status": consensus_output.status,
            "classification": consensus_output.consensus_classification,
            "confidence": consensus_output.consensus_confidence,
            "disagreement_metric": consensus_output.disagreement_metric,
            "notice": consensus_output.scientific_notice,
        },
    }

    analysis_entity = AnalysisResult(
        observation_id=obs.id,
        ml_classification=ml_output.classification,
        ml_confidence=ml_output.confidence,
        physics_classification=physics_output.physics_classification,
        physics_confidence=physics_output.physics_confidence,
        consensus_confidence=consensus_output.consensus_confidence,
        consensus_classification=consensus_output.consensus_classification,
        temporal_confidence=consensus_output.temporal_confidence,
        risk_level=consensus_output.risk_level,
        execution_metadata=component_breakdown,
    )
    db.add(analysis_entity)
    db.flush()

    # 8. Append to Longitudinal SHA-256 Evidence Chronicle
    chronicle_record = chronicle_service.append_record(
        db=db,
        observation_id=obs.id,
        analysis_result_id=analysis_entity.id,
        analysis_summary={
            "risk_level": str(analysis_entity.risk_level),
            "consensus_classification": analysis_entity.consensus_classification,
            "is_stub": True,
        },
        processing_metadata={
            "pipeline_stage": "phase_1_prototype",
            "insar_coherence": insar_features.coherence,
            "warnings_count": len(insar_features.validation_warnings),
        },
    )

    db.commit()
    db.refresh(analysis_entity)
    db.refresh(chronicle_record)

    logger.info(f"Successfully processed analysis pipeline for observation {observation_id}")

    return AnalysisPipelineResponse(
        analysis_result=AnalysisResultRead.model_validate(analysis_entity),
        is_development_stub=True,
        component_breakdown=component_breakdown,
        chronology_record=ChronologyRecordRead.model_validate(chronicle_record),
        scientific_integrity_notice=(
            "STRATA Phase 1 Prototype: ML, physics, and consensus calculations are explicitly stubbed. "
            "No real structural failure or Sentinel-1 inference is asserted."
        ),
    )


@router.get(
    "/chronicle/verify",
    summary="Cryptographically verify SHA-256 evidence chain integrity",
)
def verify_chronicle_integrity(
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    records = db.query(ChronologyRecord).order_by(ChronologyRecord.record_index.asc()).all()
    is_valid, reason = chronicle_service.verify_chain(records)

    return {
        "chain_length": len(records),
        "is_intact": is_valid,
        "verification_status": "VALID" if is_valid else "CORRUPTED_OR_TAMPERED",
        "error_detail": reason,
    }


@router.post(
    "/consensus/{observation_id}",
    response_model=ConsensusAssessment,
    status_code=status.HTTP_200_OK,
    summary="Execute STRATA Cross-Model Consensus on an observation sequence",
)
def evaluate_observation_consensus(
    observation_id: str,
    db: Session = Depends(get_db),
) -> ConsensusAssessment:
    # 1. Fetch target observation
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )

    # 2. Fetch all historical observations for this infrastructure chronologically up to obs
    db_observations = (
        db.query(Observation)
        .filter(
            Observation.infrastructure_id == obs.infrastructure_id,
            Observation.acquisition_timestamp <= obs.acquisition_timestamp,
        )
        .order_by(Observation.acquisition_timestamp.asc())
        .all()
    )
    pydantic_observations = [ObservationRead.model_validate(o) for o in db_observations]

    # 3. Construct sequence
    start_time = pydantic_observations[0].acquisition_timestamp if pydantic_observations else None
    end_time = pydantic_observations[-1].acquisition_timestamp if pydantic_observations else None
    sequence = ObservationSequence(
        infrastructure_id=obs.infrastructure_id,
        observations=pydantic_observations,
        start_time=start_time,
        end_time=end_time,
        epoch_count=len(pydantic_observations),
    )

    # 4. Independent Physics Consistency Engine
    physics_evidence = real_physics_engine.evaluate_sequence(sequence)

    # 5. Independent ML Deformation Classifier
    ml_result = _evaluate_ml_safely(sequence)

    # 6. Cross-Model Consensus Engine
    consensus_assessment = real_consensus_engine.evaluate(
        ml_result=ml_result,
        physics_evidence=physics_evidence,
        epoch_count=len(pydantic_observations),
    )

    return consensus_assessment


@router.post(
    "/chronology/{observation_id}",
    response_model=ChronologyRecordRead,
    status_code=status.HTTP_201_CREATED,
    summary="Evaluate consensus and append tamper-evident SHA-256 record to evidence chronicle",
)
def record_observation_chronology(
    observation_id: str,
    db: Session = Depends(get_db),
) -> ChronologyRecord:
    # 1. Fetch observation
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )

    # 2. Fetch all historical observations for this infrastructure chronologically up to obs
    db_observations = (
        db.query(Observation)
        .filter(
            Observation.infrastructure_id == obs.infrastructure_id,
            Observation.acquisition_timestamp <= obs.acquisition_timestamp,
        )
        .order_by(Observation.acquisition_timestamp.asc())
        .all()
    )
    pydantic_observations = [ObservationRead.model_validate(o) for o in db_observations]

    # 3. Construct sequence
    start_time = pydantic_observations[0].acquisition_timestamp if pydantic_observations else None
    end_time = pydantic_observations[-1].acquisition_timestamp if pydantic_observations else None
    sequence = ObservationSequence(
        infrastructure_id=obs.infrastructure_id,
        observations=pydantic_observations,
        start_time=start_time,
        end_time=end_time,
        epoch_count=len(pydantic_observations),
    )

    # 4. Independent Physics Consistency Engine
    physics_evidence = real_physics_engine.evaluate_sequence(sequence)

    # 5. Independent ML Deformation Classifier
    ml_result = _evaluate_ml_safely(sequence)

    # 6. Cross-Model Consensus Engine
    consensus_assessment = real_consensus_engine.evaluate(
        ml_result=ml_result,
        physics_evidence=physics_evidence,
        epoch_count=len(pydantic_observations),
    )

    # 7. Append to Longitudinal SHA-256 Evidence Chronicle
    record = chronicle_service.append_consensus_record(
        db=db,
        observation_id=obs.id,
        infrastructure_id=obs.infrastructure_id,
        consensus_assessment=consensus_assessment,
        acquisition_timestamp=obs.acquisition_timestamp,
    )

    db.commit()
    db.refresh(record)
    return record


@router.post(
    "/pipeline/{observation_id}",
    response_model=PipelineResult,
    status_code=status.HTTP_201_CREATED,
    summary="Execute unified end-to-end STRATA analysis pipeline (Phase 9)",
)
def execute_pipeline(
    observation_id: str,
    force_recompute: bool = False,
    db: Session = Depends(get_db),
) -> PipelineResult:
    """
    Executes the hardened STRATA end-to-end analysis pipeline:
    1. Validation & bounds checking
    2. InSAR normalization
    3. Frozen ML classifier evaluation
    4. Deterministic physics consistency evaluation
    5. Cross-model consensus fusion
    6. Multi-epoch temporal kinematics & acceleration analysis
    7. Infrastructure-specific risk characterization (Phase 7)
    8. Tamper-evident SHA-256 chronology append (Phase 6)
    All operations execute within an atomic, idempotent database transaction.
    """
    try:
        pipeline = STRATAAnalysisPipeline()
        result = pipeline.execute_for_observation(
            db=db,
            observation_id=observation_id,
            force_recompute=force_recompute,
        )
        return result
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=msg,
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=msg,
        )
    except PipelineExecutionError as exc:
        msg = exc.message.lower()
        if "not found" in msg:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=exc.message,
            )
        if exc.failed_stage == "VALIDATED" or "invalid" in msg or "nan" in msg or "inf" in msg:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=exc.message,
            )
        logger.error(f"Pipeline execution failed at stage {exc.failed_stage}: {exc.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Pipeline failure at stage {exc.failed_stage}: {exc.message}",
        )
    except Exception as exc:
        logger.error(f"Unexpected pipeline execution error: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected pipeline execution failure: {str(exc)}",
        )


@router.get(
    "/pipeline/{observation_id}",
    response_model=PipelineResult,
    summary="Retrieve the latest end-to-end pipeline analysis result for an observation",
)
def get_pipeline_result(
    observation_id: str,
    db: Session = Depends(get_db),
) -> PipelineResult:
    """
    Retrieves the pipeline analysis result for an observation via idempotent execution replay.
    """
    obs = db.query(Observation).filter(Observation.id == observation_id).first()
    if not obs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with ID '{observation_id}' not found.",
        )

    pipeline = STRATAAnalysisPipeline()
    try:
        result = pipeline.execute_for_observation(
            db=db,
            observation_id=observation_id,
            force_recompute=False,
        )
        return result
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        logger.error(f"Error retrieving pipeline result: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve pipeline result: {str(exc)}",
        )
