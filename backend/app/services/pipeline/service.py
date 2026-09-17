"""
STRATA End-to-End Analysis Pipeline Orchestration Service (Phase 9).
Coordinates input validation, normalization, frozen ML inference, deterministic physics consistency,
cross-model consensus fusion, temporal kinematics, infrastructure-specific risk characterization,
and tamper-evident chronology append within an atomic, idempotent database transaction.

CRITICAL SCIENTIFIC PRINCIPLES:
- HARD RULE: Does NOT retrain ML model or tune scientific thresholds.
- Enforces strict input validation (bounds, NaN/Inf, geometry).
- Guarantees idempotency (no duplicate chronology entries on re-execution).
- Guarantees transactional atomicity (rollback on failure prevents partial/misleading states).
- Preserves full audit versioning and provenance.
"""
from datetime import datetime, timezone
import math
import time
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from backend.app.core.logging import logger
from backend.app.core.versions import (
    PIPELINE_VERSION,
    get_system_versions,
)
from backend.app.db.models import (
    AnalysisResult,
    ChronologyRecord,
    Infrastructure,
    Observation,
    RiskCharacterization,
    RiskLevel,
)
from backend.app.schemas.consensus import ConsensusAssessment
from backend.app.schemas.ml import MLClassificationResult
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import (
    ObservationSequence,
    PhysicsEvidence,
)
from backend.app.schemas.risk import RiskCharacterizationRead
from backend.app.schemas.synthetic import GroundTruthClass
from backend.app.schemas.temporal import TemporalEvidenceSummary
from backend.app.services.chronology import EvidenceChronicleService
from backend.app.services.consensus import ConsensusEngine
from backend.app.services.ml.classifier import MLDeformationClassifier
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.pipeline.schemas import (
    ChronologySummary,
    NormalizedObservationData,
    PipelineExecutionError,
    PipelineResult,
    ProcessingStatus,
    StageTimings,
)
from backend.app.services.real_data.normalization import (
    convert_displacement_to_mm,
    normalize_coherence,
    normalize_timestamp,
    project_los_to_vertical,
)
from backend.app.services.risk import InfrastructureRiskCharacterizationEngine
from backend.app.services.temporal import TemporalEvidenceEngine


class STRATAAnalysisPipeline:
    """
    Central orchestration service for end-to-end STRATA observation analysis.
    Combines all phase-separated engines into a robust, traceable execution pipeline.
    """

    def __init__(
        self,
        ml_classifier: Optional[MLDeformationClassifier] = None,
        physics_engine: Optional[PhysicsInSARConsistencyEngine] = None,
        consensus_engine: Optional[ConsensusEngine] = None,
        temporal_engine: Optional[TemporalEvidenceEngine] = None,
        risk_engine: Optional[InfrastructureRiskCharacterizationEngine] = None,
        chronicle_service: Optional[EvidenceChronicleService] = None,
    ):
        self.ml_classifier = ml_classifier or MLDeformationClassifier()
        self.physics_engine = physics_engine or PhysicsInSARConsistencyEngine()
        self.consensus_engine = consensus_engine or ConsensusEngine()
        self.temporal_engine = temporal_engine or TemporalEvidenceEngine(
            physics_engine=self.physics_engine,
            ml_classifier=self.ml_classifier,
            consensus_engine=self.consensus_engine,
        )
        self.risk_engine = risk_engine or InfrastructureRiskCharacterizationEngine(
            temporal_engine=self.temporal_engine
        )
        self.chronicle_service = chronicle_service or EvidenceChronicleService()

    def execute_for_observation(
        self,
        db: Session,
        observation_id: str,
        force_recompute: bool = False,
    ) -> PipelineResult:
        """
        Executes the full end-to-end STRATA pipeline for a given observation.
        Wrapped in a strict database transaction with rollback protection.
        """
        analysis_id = str(uuid.uuid4())
        start_total = time.perf_counter()
        timings = StageTimings()
        system_versions = get_system_versions()
        warnings: List[str] = []

        logger.info(f"[{analysis_id}] STRATA Pipeline execution started for observation {observation_id}")

        # ----------------------------------------------------------------------
        # Stage 1: Input Validation & Security Gating
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        current_status = ProcessingStatus.RECEIVED

        obs = db.query(Observation).filter(Observation.id == observation_id).first()
        if not obs:
            raise PipelineExecutionError(
                failed_stage=ProcessingStatus.VALIDATED,
                message=f"Target observation '{observation_id}' not found.",
            )

        inf = db.query(Infrastructure).filter(Infrastructure.id == obs.infrastructure_id).first()
        if not inf:
            raise PipelineExecutionError(
                failed_stage=ProcessingStatus.VALIDATED,
                message=f"Associated infrastructure asset '{obs.infrastructure_id}' not found.",
            )

        # Validation: NaN / Inf / Range security checks
        self._validate_numerical_integrity(obs)
        timings.validation_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        current_status = ProcessingStatus.VALIDATED
        logger.info(f"[{analysis_id}] Validation complete in {timings.validation_ms} ms")

        # ----------------------------------------------------------------------
        # Idempotency Check: Avoid duplicate chronology records if already executed
        # ----------------------------------------------------------------------
        if not force_recompute:
            existing_result = self._check_existing_analysis(db, obs.id)
            if existing_result:
                logger.info(f"[{analysis_id}] Idempotent match found for observation {obs.id}; returning cached result")
                existing_result.idempotent_replay = True
                return existing_result

        try:
            # ------------------------------------------------------------------
            # Stage 2: Observation Normalization & Representation
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            norm_data = self._normalize_observation(obs)
            timings.normalization_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.NORMALIZED
            logger.info(f"[{analysis_id}] Normalization complete in {timings.normalization_ms} ms")

            # ------------------------------------------------------------------
            # Stage 3: Historical Sequence Assembly
            # ------------------------------------------------------------------
            historical_obs = self._assemble_historical_sequence(db, obs, norm_data)

            # ------------------------------------------------------------------
            # Stage 4: Frozen ML Inference
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            ml_res = self._execute_ml_safely(historical_obs)
            timings.ml_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.ML_ANALYZED
            logger.info(f"[{analysis_id}] ML inference complete ({ml_res.predicted_class}) in {timings.ml_ms} ms")

            # ------------------------------------------------------------------
            # Stage 5: Physics Consistency Evaluation
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            seq_obj = ObservationSequence(
                infrastructure_id=obs.infrastructure_id,
                epoch_count=len(historical_obs),
                observations=historical_obs,
                start_time=historical_obs[0].acquisition_timestamp if historical_obs else None,
                end_time=historical_obs[-1].acquisition_timestamp if historical_obs else None,
            )
            phys_ev = self.physics_engine.evaluate_sequence(seq_obj)
            timings.physics_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.PHYSICS_ANALYZED
            logger.info(f"[{analysis_id}] Physics evaluation complete ({phys_ev.classification.value}) in {timings.physics_ms} ms")

            # ------------------------------------------------------------------
            # Stage 6: Cross-Model Consensus Fusion
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            consensus_res = self.consensus_engine.evaluate(
                ml_result=ml_res,
                physics_evidence=phys_ev,
                epoch_count=len(historical_obs),
            )
            timings.consensus_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.CONSENSUS_ANALYZED
            logger.info(f"[{analysis_id}] Consensus complete ({consensus_res.consensus_class.value}, conf={consensus_res.consensus_confidence:.2f}) in {timings.consensus_ms} ms")

            # ------------------------------------------------------------------
            # Stage 7: Temporal Kinematics & Persistence Assessment
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            temporal_sum = self.temporal_engine.evaluate_summary(
                infrastructure_id=obs.infrastructure_id,
                observations=historical_obs,
            )
            timings.temporal_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.TEMPORAL_ANALYZED
            logger.info(f"[{analysis_id}] Temporal evaluation complete ({temporal_sum.temporal_status.value}) in {timings.temporal_ms} ms")

            # ------------------------------------------------------------------
            # Stage 8: Infrastructure-Specific Risk Characterization
            # ------------------------------------------------------------------
            t0 = time.perf_counter()
            risk_char = self.risk_engine.evaluate_infrastructure(
                infrastructure=inf,
                observations=historical_obs,
                temporal_summary=temporal_sum,
            )
            timings.characterization_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.CHARACTERIZED
            logger.info(f"[{analysis_id}] Risk characterization complete ({risk_char.characterization_state.value}, index={risk_char.prototype_risk_index}) in {timings.characterization_ms} ms")

            # ------------------------------------------------------------------
            # Stage 9: Database Persistence & Tamper-Evident Chronology Append
            # ------------------------------------------------------------------
            t0 = time.perf_counter()

            # Map RiskCharacterizationState to legacy RiskLevel for AnalysisResult compatibility
            legacy_risk = self._map_to_legacy_risk_level(risk_char.characterization_state.value)

            analysis_record = AnalysisResult(
                id=analysis_id,
                observation_id=obs.id,
                ml_classification=ml_res.predicted_class.value if hasattr(ml_res.predicted_class, "value") else str(ml_res.predicted_class),
                ml_confidence=ml_res.confidence,
                physics_classification=phys_ev.classification.value,
                physics_confidence=getattr(phys_ev, "evidence_strength", 0.0),
                consensus_classification=consensus_res.consensus_class.value,
                consensus_confidence=consensus_res.consensus_confidence,
                temporal_confidence=consensus_res.temporal_persistence_score,
                risk_level=legacy_risk,
                execution_metadata={
                    "pipeline_version": PIPELINE_VERSION,
                    "analysis_id": analysis_id,
                    "system_versions": system_versions,
                    "characterization_state": risk_char.characterization_state.value,
                    "prototype_risk_index": risk_char.prototype_risk_index,
                    "agreement_score": consensus_res.agreement_score,
                    "disagreement_penalty": consensus_res.disagreement_penalty,
                    "flags": consensus_res.flags,
                },
            )
            db.add(analysis_record)
            db.flush()

            # Append complete analytical snapshot to the SHA-256 evidence chain
            chronology_entity = self._append_chronology_record(
                db=db,
                obs=obs,
                analysis_record=analysis_record,
                ml_res=ml_res,
                phys_ev=phys_ev,
                consensus_res=consensus_res,
                temporal_sum=temporal_sum,
                risk_char=risk_char,
                system_versions=system_versions,
            )

            # Persist RiskCharacterization DB record
            self._persist_risk_characterization(db, inf.id, risk_char, historical_obs)

            # Commit atomic transaction
            db.commit()

            timings.chronology_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            current_status = ProcessingStatus.COMPLETED

            chronology_summary = ChronologySummary(
                record_id=chronology_entity.id,
                record_index=chronology_entity.record_index,
                current_hash=chronology_entity.current_hash,
                previous_hash=chronology_entity.previous_hash,
                payload_hash=chronology_entity.payload_hash,
                timestamp=chronology_entity.timestamp,
            )

            timings.total_ms = round((time.perf_counter() - start_total) * 1000.0, 3)
            logger.info(f"[{analysis_id}] Pipeline completed successfully in {timings.total_ms} ms")

            return PipelineResult(
                analysis_id=analysis_id,
                observation_id=obs.id,
                infrastructure_id=obs.infrastructure_id,
                processing_status=ProcessingStatus.COMPLETED,
                execution_timestamp=datetime.now(timezone.utc),
                normalized_observation=norm_data,
                ml_result=ml_res,
                physics_evidence={
                    "classification": phys_ev.classification.value,
                    "evidence_factors": getattr(phys_ev, "evidence_factors", {}),
                },
                consensus_assessment=consensus_res,
                temporal_summary=temporal_sum,
                risk_characterization=risk_char,
                chronology_record=chronology_summary,
                stage_timings=timings,
                system_versions=system_versions,
                warnings=warnings,
                errors=[],
                idempotent_replay=False,
            )

        except Exception as exc:
            db.rollback()
            logger.error(f"[{analysis_id}] Pipeline failed at stage {current_status}: {str(exc)}", exc_info=True)
            if isinstance(exc, PipelineExecutionError):
                raise exc
            raise PipelineExecutionError(
                failed_stage=current_status,
                message=f"Pipeline failed during {current_status.value}: {str(exc)}",
                diagnostic_context={"analysis_id": analysis_id, "observation_id": observation_id},
            ) from exc

    def _validate_numerical_integrity(self, obs: Observation) -> None:
        """Validates numerical finiteness and physical sanity bounds."""
        if obs.deformation_mm is None and obs.los_displacement_mm is None:
            raise PipelineExecutionError(
                failed_stage=ProcessingStatus.VALIDATED,
                message="Observation missing displacement measurements: NaN or NULL detected.",
            )
        for attr in ["deformation_mm", "los_displacement_mm", "velocity_mm_per_year"]:
            val = getattr(obs, attr, None)
            if val is not None:
                if math.isnan(val) or math.isinf(val):
                    raise PipelineExecutionError(
                        failed_stage=ProcessingStatus.VALIDATED,
                        message=f"Invalid numerical value in '{attr}': NaN or Inf detected.",
                    )
                if abs(val) > 10000.0:
                    raise PipelineExecutionError(
                        failed_stage=ProcessingStatus.VALIDATED,
                        message=f"Impossible physical displacement magnitude ({val} mm) exceeds sanity ceiling.",
                    )

        if obs.coherence is not None:
            if math.isnan(obs.coherence) or math.isinf(obs.coherence):
                raise PipelineExecutionError(
                    failed_stage=ProcessingStatus.VALIDATED,
                    message="Invalid coherence value: NaN or Inf detected.",
                )
            if not (0.0 <= obs.coherence <= 1.0):
                raise PipelineExecutionError(
                    failed_stage=ProcessingStatus.VALIDATED,
                    message=f"Coherence value ({obs.coherence}) must be within [0.0, 1.0].",
                )

        if obs.incidence_angle is not None:
            if math.isnan(obs.incidence_angle) or math.isinf(obs.incidence_angle):
                raise PipelineExecutionError(
                    failed_stage=ProcessingStatus.VALIDATED,
                    message="Invalid incidence angle: NaN or Inf detected.",
                )
            if not (0.0 <= obs.incidence_angle <= 90.0):
                raise PipelineExecutionError(
                    failed_stage=ProcessingStatus.VALIDATED,
                    message=f"Incidence angle ({obs.incidence_angle}) must be within [0.0, 90.0] degrees.",
                )

    def _normalize_observation(self, obs: Observation) -> NormalizedObservationData:
        """Applies explicit unit normalization and radar geometry projections."""
        raw_meta = obs.observation_metadata or {}
        orig_unit = raw_meta.get("displacement_unit", "mm")
        orig_rep = raw_meta.get("displacement_representation", "LOS")
        flags = []

        norm_def_mm = None
        norm_los_mm = None
        geom_avail = True

        if obs.deformation_mm is not None:
            norm_def_mm = convert_displacement_to_mm(obs.deformation_mm, orig_unit)

        if obs.los_displacement_mm is not None:
            norm_los_mm = convert_displacement_to_mm(obs.los_displacement_mm, orig_unit)

        # LOS to vertical projection
        if norm_def_mm is None and norm_los_mm is not None:
            vert_mm, ok = project_los_to_vertical(norm_los_mm, obs.incidence_angle)
            if ok and vert_mm is not None:
                norm_def_mm = vert_mm
                flags.append("PROJECTED_FROM_LOS")
            else:
                geom_avail = False
                flags.append("GEOMETRY_UNAVAILABLE")
        elif norm_def_mm is not None and orig_rep.upper() == "VERTICAL":
            flags.append("EXTERNAL_VERTICAL_PROVIDED")

        coherence_val, has_coh = normalize_coherence(obs.coherence)
        if not has_coh:
            flags.append("COHERENCE_UNAVAILABLE")

        return NormalizedObservationData(
            observation_id=obs.id,
            infrastructure_id=obs.infrastructure_id,
            acquisition_timestamp=normalize_timestamp(obs.acquisition_timestamp),
            original_displacement=obs.deformation_mm if obs.deformation_mm is not None else obs.los_displacement_mm,
            original_unit=orig_unit,
            original_representation=orig_rep,
            normalized_deformation_mm=norm_def_mm,
            normalized_los_displacement_mm=norm_los_mm,
            coherence=coherence_val,
            phase_quality=obs.phase_quality,
            incidence_angle=obs.incidence_angle,
            geometry_available=geom_avail,
            normalization_flags=flags,
        )

    def _assemble_historical_sequence(
        self,
        db: Session,
        target_obs: Observation,
        target_norm: NormalizedObservationData,
    ) -> List[ObservationRead]:
        """Queries and assembles chronologically ordered observations up to target epoch."""
        db_obs_list = (
            db.query(Observation)
            .filter(
                Observation.infrastructure_id == target_obs.infrastructure_id,
                Observation.acquisition_timestamp <= target_obs.acquisition_timestamp,
            )
            .order_by(Observation.acquisition_timestamp.asc())
            .all()
        )

        pydantic_list: List[ObservationRead] = []
        for o in db_obs_list:
            if o.id == target_obs.id:
                # Use normalized values for target
                read_obs = ObservationRead(
                    id=o.id,
                    infrastructure_id=o.infrastructure_id,
                    acquisition_timestamp=target_norm.acquisition_timestamp,
                    deformation_mm=target_norm.normalized_deformation_mm,
                    velocity_mm_per_year=o.velocity_mm_per_year,
                    coherence=target_norm.coherence,
                    phase_quality=target_norm.phase_quality,
                    incidence_angle=target_norm.incidence_angle,
                    los_displacement_mm=target_norm.normalized_los_displacement_mm,
                    atmospheric_indicator=o.atmospheric_indicator,
                    source=o.source,
                    metadata={"flags": target_norm.normalization_flags},
                    created_at=o.created_at,
                )
            else:
                read_obs = ObservationRead.model_validate(o)

            if read_obs.acquisition_timestamp is not None and read_obs.acquisition_timestamp.tzinfo is None:
                read_obs = read_obs.model_copy(
                    update={"acquisition_timestamp": read_obs.acquisition_timestamp.replace(tzinfo=timezone.utc)}
                )
            pydantic_list.append(read_obs)

        return pydantic_list

    def _execute_ml_safely(self, sequence: List[ObservationRead]) -> MLClassificationResult:
        """Executes frozen ML classifier, safely handling sequences with < 2 epochs."""
        if len(sequence) < 2:
            all_classes = [c.value for c in GroundTruthClass]
            p_uniform = {c: round(1.0 / len(all_classes), 4) for c in all_classes}
            return MLClassificationResult(
                predicted_class=GroundTruthClass.STABLE,
                probabilities=p_uniform,
                confidence=round(1.0 / len(all_classes), 4),
                entropy=1.0,
                model_version=self.ml_classifier.metadata.model_version if self.ml_classifier.metadata else "0.1.0",
                feature_version="0.1.0",
                extracted_features=None,
            )
        return self.ml_classifier.predict(sequence)

    def _append_chronology_record(
        self,
        db: Session,
        obs: Observation,
        analysis_record: AnalysisResult,
        ml_res: MLClassificationResult,
        phys_ev: PhysicsEvidence,
        consensus_res: ConsensusAssessment,
        temporal_sum: TemporalEvidenceSummary,
        risk_char: RiskCharacterizationRead,
        system_versions: Dict[str, str],
    ) -> ChronologyRecord:
        """Constructs and appends complete unified analytical chronology payload."""
        latest_record = (
            db.query(ChronologyRecord)
            .order_by(ChronologyRecord.record_index.desc())
            .first()
        )

        if latest_record is None:
            record_index = 0
            previous_hash = self.chronicle_service.genesis_hash
        else:
            record_index = latest_record.record_index + 1
            previous_hash = latest_record.current_hash

        record_time = datetime.now(timezone.utc)

        payload: Dict[str, Any] = {
            "record_index": record_index,
            "analysis_id": analysis_record.id,
            "observation_id": obs.id,
            "infrastructure_id": obs.infrastructure_id,
            "acquisition_timestamp": normalize_timestamp(obs.acquisition_timestamp).isoformat(),
            "ml_classification": ml_res.predicted_class.value if hasattr(ml_res.predicted_class, "value") else str(ml_res.predicted_class),
            "ml_confidence": ml_res.confidence,
            "physics_classification": phys_ev.classification.value,
            "consensus_class": consensus_res.consensus_class.value,
            "consensus_confidence": consensus_res.consensus_confidence,
            "temporal_status": temporal_sum.temporal_status.value,
            "trend_rate_mm_per_year": temporal_sum.trend_rate_mm_per_year,
            "apparent_acceleration_mm_per_year2": temporal_sum.apparent_acceleration_mm_per_year2,
            "acceleration_supported": temporal_sum.acceleration_supported,
            "characterization_state": risk_char.characterization_state.value,
            "prototype_risk_index": risk_char.prototype_risk_index,
            "system_versions": system_versions,
            "flags": consensus_res.flags,
        }

        from backend.app.services.chronology.hasher import (
            compute_chained_record_hash,
            compute_payload_hash,
        )

        payload_hash = compute_payload_hash(payload)
        current_hash = compute_chained_record_hash(previous_hash, payload_hash)

        record = ChronologyRecord(
            observation_id=obs.id,
            analysis_result_id=analysis_record.id,
            infrastructure_id=obs.infrastructure_id,
            record_index=record_index,
            timestamp=record_time,
            payload=payload,
            payload_hash=payload_hash,
            previous_hash=previous_hash,
            current_hash=current_hash,
        )

        db.add(record)
        db.flush()
        return record

    def _persist_risk_characterization(
        self,
        db: Session,
        infrastructure_id: str,
        risk_char: RiskCharacterizationRead,
        observations: List[ObservationRead],
    ) -> None:
        """Persists Phase 7 RiskCharacterization entity in DB."""
        from backend.app.db.models import RiskCharacterizationState

        start_time = observations[0].acquisition_timestamp if observations else None
        end_time = observations[-1].acquisition_timestamp if observations else None

        char_entity = RiskCharacterization(
            id=risk_char.id,
            infrastructure_id=infrastructure_id,
            observation_window_start=start_time,
            observation_window_end=end_time,
            epoch_count=len(observations),
            characterization_state=RiskCharacterizationState(risk_char.characterization_state.value),
            confidence=risk_char.confidence,
            prototype_risk_index=risk_char.prototype_risk_index,
            evidence_components=risk_char.evidence_components.model_dump(),
            supporting_factors=risk_char.supporting_factors,
            suppressing_factors=risk_char.suppressing_factors,
            uncertainty_factors=risk_char.uncertainty_factors,
            explanation=risk_char.explanation,
            version_metadata=risk_char.version_metadata,
        )
        db.add(char_entity)
        db.flush()

    def _check_existing_analysis(self, db: Session, observation_id: str) -> Optional[PipelineResult]:
        """Queries for an existing completed analysis for this observation."""
        rec = (
            db.query(AnalysisResult)
            .filter(AnalysisResult.observation_id == observation_id)
            .order_by(AnalysisResult.created_at.desc())
            .first()
        )
        if not rec or not rec.execution_metadata:
            return None

        # Check if pipeline version matches
        if rec.execution_metadata.get("pipeline_version") != PIPELINE_VERSION:
            return None

        # Fetch associated chronology record
        chrono = (
            db.query(ChronologyRecord)
            .filter(ChronologyRecord.analysis_result_id == rec.id)
            .first()
        )
        if not chrono:
            return None

        obs = db.query(Observation).filter(Observation.id == observation_id).first()
        if not obs:
            return None

        norm_data = self._normalize_observation(obs)

        # Construct minimal replayed PipelineResult
        return PipelineResult(
            analysis_id=rec.id,
            observation_id=obs.id,
            infrastructure_id=obs.infrastructure_id,
            processing_status=ProcessingStatus.COMPLETED,
            execution_timestamp=rec.created_at,
            normalized_observation=norm_data,
            ml_result=None,
            physics_evidence=None,
            consensus_assessment=None,
            temporal_summary=None,
            risk_characterization=None,
            chronology_record=ChronologySummary(
                record_id=chrono.id,
                record_index=chrono.record_index,
                current_hash=chrono.current_hash,
                previous_hash=chrono.previous_hash,
                payload_hash=chrono.payload_hash,
                timestamp=chrono.timestamp,
            ),
            stage_timings=StageTimings(),
            system_versions=rec.execution_metadata.get("system_versions", {}),
            warnings=["Returned cached idempotent analysis result."],
            errors=[],
            idempotent_replay=True,
        )

    def _map_to_legacy_risk_level(self, char_state: str) -> RiskLevel:
        """Maps Phase 7 semantic state to legacy database RiskLevel enum."""
        mapping = {
            "INSUFFICIENT_EVIDENCE": RiskLevel.UNKNOWN,
            "BASELINE": RiskLevel.NOMINAL,
            "ENVIRONMENTAL_PATTERN": RiskLevel.NOMINAL,
            "MONITOR": RiskLevel.WATCH,
            "ELEVATED_ATTENTION": RiskLevel.WARNING,
            "HIGH_ATTENTION": RiskLevel.CRITICAL,
        }
        return mapping.get(char_state, RiskLevel.UNKNOWN)
