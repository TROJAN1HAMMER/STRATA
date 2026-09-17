"""
Pydantic Schemas, Contracts, and Processing Lifecycles for STRATA Analysis Pipeline.
Defines explicit processing states, stage latencies, canonical observation data,
and comprehensive traceable analytical results.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.consensus import ConsensusAssessment
from backend.app.schemas.ml import MLClassificationResult
from backend.app.schemas.risk import RiskCharacterizationRead
from backend.app.schemas.temporal import TemporalEvidenceSummary


class ProcessingStatus(str, Enum):
    """Explicit deterministic state progression for pipeline execution."""
    RECEIVED = "RECEIVED"
    VALIDATED = "VALIDATED"
    NORMALIZED = "NORMALIZED"
    ML_ANALYZED = "ML_ANALYZED"
    PHYSICS_ANALYZED = "PHYSICS_ANALYZED"
    CONSENSUS_ANALYZED = "CONSENSUS_ANALYZED"
    TEMPORAL_ANALYZED = "TEMPORAL_ANALYZED"
    CHARACTERIZED = "CHARACTERIZED"
    CHRONICLED = "CHRONICLED"
    COMPLETED = "COMPLETED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class StageTimings(BaseModel):
    """Fine-grained execution latency tracking per analytical stage in milliseconds."""
    validation_ms: float = Field(default=0.0, description="Input validation duration")
    normalization_ms: float = Field(default=0.0, description="Unit and geometry normalization duration")
    ml_ms: float = Field(default=0.0, description="Machine learning classifier inference duration")
    physics_ms: float = Field(default=0.0, description="Physics consistency evaluation duration")
    consensus_ms: float = Field(default=0.0, description="Cross-model consensus fusion duration")
    temporal_ms: float = Field(default=0.0, description="Temporal kinematics and persistence evaluation duration")
    characterization_ms: float = Field(default=0.0, description="Infrastructure-specific risk characterization duration")
    chronology_ms: float = Field(default=0.0, description="SHA-256 evidence chronicle append duration")
    total_ms: float = Field(default=0.0, description="Total pipeline execution latency")


class NormalizedObservationData(BaseModel):
    """Preserved raw and normalized observation parameters for full provenance."""
    observation_id: str
    infrastructure_id: str
    acquisition_timestamp: datetime
    original_displacement: Optional[float] = None
    original_unit: str = "mm"
    original_representation: str = "LOS"
    normalized_deformation_mm: Optional[float] = None
    normalized_los_displacement_mm: Optional[float] = None
    coherence: Optional[float] = None
    phase_quality: Optional[float] = None
    incidence_angle: Optional[float] = None
    geometry_available: bool = True
    normalization_flags: List[str] = Field(default_factory=list)


class ChronologySummary(BaseModel):
    """Summary of the tamper-evident hash-chained record created for this analysis."""
    record_id: str
    record_index: int
    current_hash: str
    previous_hash: str
    payload_hash: str
    timestamp: datetime


class PipelineResult(BaseModel):
    """
    Unified end-to-end analytical contract for STRATA analysis pipeline.
    Preserves all intermediate evidence without premature flattening or score collapse.
    """
    analysis_id: str = Field(..., description="Unique execution correlation ID")
    observation_id: str = Field(..., description="Target observation UUID")
    infrastructure_id: str = Field(..., description="Associated infrastructure asset UUID")
    processing_status: ProcessingStatus = Field(..., description="Current processing lifecycle status")
    execution_timestamp: datetime = Field(..., description="Timestamp of analysis execution (UTC)")

    normalized_observation: NormalizedObservationData = Field(..., description="Canonical observation data")
    ml_result: Optional[MLClassificationResult] = Field(default=None, description="ML deformation classification")
    physics_evidence: Optional[Dict[str, Any]] = Field(default=None, description="Deterministic physics evidence")
    consensus_assessment: Optional[ConsensusAssessment] = Field(default=None, description="Cross-model consensus interpretation")
    temporal_summary: Optional[TemporalEvidenceSummary] = Field(default=None, description="Temporal kinematics and persistence")
    risk_characterization: Optional[RiskCharacterizationRead] = Field(default=None, description="Infrastructure characterization")
    chronology_record: Optional[ChronologySummary] = Field(default=None, description="Tamper-evident record details")

    stage_timings: StageTimings = Field(default_factory=StageTimings, description="Latency benchmark per stage")
    system_versions: Dict[str, str] = Field(default_factory=dict, description="Semantic versions of all participating components")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal analytical warnings")
    errors: List[str] = Field(default_factory=list, description="Diagnostic errors if execution failed")
    idempotent_replay: bool = Field(default=False, description="True if result was returned from existing analysis")

    model_config = ConfigDict(from_attributes=True)


class PipelineExecutionError(Exception):
    """Custom exception raised when an analytical pipeline stage encounters an unrecoverable failure."""
    def __init__(
        self,
        failed_stage: ProcessingStatus,
        message: str,
        diagnostic_context: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.failed_stage = failed_stage
        self.message = message
        self.diagnostic_context = diagnostic_context or {}
