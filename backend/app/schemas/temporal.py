"""
Pydantic schemas for STRATA Temporal Evidence & Chronology Layer (Phase 6).
Defines temporal status vocabulary, confidence trajectories, state transitions,
and longitudinal evidence summaries.
"""
import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class TemporalStatus(str, enum.Enum):
    """
    Explicit temporal evidence status vocabulary for multi-epoch InSAR analysis.

    IMPORTANT SCIENTIFIC DISTINCTION:
      - PERSISTENT indicates that observed deformation evidence has persisted across
        multiple epochs with cross-model support. It does NOT mean confirmed structural damage,
        nor does it predict failure or collapse.
      - EMERGING indicates an initial coherent deformation signal is beginning to form.
      - REVERTED indicates a previously detected deformation trend is no longer observed.
      - CONFLICTED indicates material contradictions between analytical models or alternating epochs.
    """
    INSUFFICIENT_HISTORY = "INSUFFICIENT_HISTORY"
    BASELINE = "BASELINE"
    EMERGING = "EMERGING"
    PERSISTENT = "PERSISTENT"
    REVERTED = "REVERTED"
    ENVIRONMENTAL_PATTERN = "ENVIRONMENTAL_PATTERN"
    ATMOSPHERIC_EVENT = "ATMOSPHERIC_EVENT"
    CONFLICTED = "CONFLICTED"
    LOW_QUALITY = "LOW_QUALITY"


class ConfidenceDataPoint(BaseModel):
    """Single epoch confidence and agreement observation in trajectory."""
    observation_id: str
    timestamp: datetime
    consensus_category: str
    confidence: float = Field(..., ge=0.0, le=1.0, description="Consensus confidence [0.0, 1.0]")
    agreement_score: float = Field(..., ge=0.0, le=1.0, description="Continuous cross-model agreement [0.0, 1.0]")
    evidence_quality_score: float = Field(..., ge=0.0, le=1.0, description="Observation quality score [0.0, 1.0]")

    model_config = ConfigDict(frozen=True)


class TemporalStateTransition(BaseModel):
    """Record of an explicit transition between temporal evidence states."""
    previous_state: TemporalStatus
    new_state: TemporalStatus
    observation_id: str
    timestamp: datetime
    reason: str = Field(..., description="Deterministic trigger justification for state change")
    confidence_before: float = Field(..., ge=0.0, le=1.0)
    confidence_after: float = Field(..., ge=0.0, le=1.0)

    model_config = ConfigDict(frozen=True)


class TemporalEvidenceSummary(BaseModel):
    """
    Comprehensive multi-epoch temporal evidence summary for an infrastructure asset.
    All kinematic and temporal metrics have explicit physical units.
    """
    infrastructure_id: str
    observation_count: int = Field(..., ge=0, description="Total ingested observations for asset")
    valid_observation_count: int = Field(..., ge=0, description="Number of valid, non-corrupted observations")
    first_observation_time: Optional[datetime] = Field(None, description="Earliest observation timestamp")
    last_observation_time: Optional[datetime] = Field(None, description="Latest observation timestamp")
    coverage_duration_days: float = Field(..., ge=0.0, description="Total elapsed observation span in days")
    temporal_status: TemporalStatus = Field(..., description="Current temporal evidence state")
    confidence_trajectory: List[ConfidenceDataPoint] = Field(
        default_factory=list,
        description="Chronological confidence and agreement progression",
    )
    mean_confidence: float = Field(..., ge=0.0, le=1.0, description="Average consensus confidence across epochs")
    recent_confidence: float = Field(..., ge=0.0, le=1.0, description="Consensus confidence of the latest epoch")
    consensus_category_history: List[str] = Field(
        default_factory=list,
        description="Ordered sequence of consensus category interpretations",
    )
    agreement_history: List[float] = Field(
        default_factory=list,
        description="Ordered sequence of cross-model agreement scores",
    )
    structural_candidate_count: int = Field(0, ge=0, description="Count of epochs classified as STRUCTURAL")
    environmental_pattern_count: int = Field(0, ge=0, description="Count of epochs classified as SEASONAL")
    atmospheric_event_count: int = Field(0, ge=0, description="Count of epochs classified as ATMOSPHERIC")
    state_transitions: List[TemporalStateTransition] = Field(
        default_factory=list,
        description="Chronological history of temporal state machine transitions",
    )
    persistence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Multi-epoch evidence persistence score [0.0, 1.0] (modifier, NOT proof of failure)",
    )
    trend_rate_mm_per_year: Optional[float] = Field(
        None,
        description="Observed deformation trend rate in millimeters per year (linear regression over elapsed time)",
    )
    apparent_acceleration_mm_per_year2: Optional[float] = Field(
        None,
        description="Apparent mathematically calculated change in deformation rate in mm/year² (2nd order polynomial fit)",
    )
    trend_acceleration_mm_per_year2: Optional[float] = Field(
        None,
        description="Backward-compatible alias for apparent_acceleration_mm_per_year2",
    )
    acceleration_supported: bool = Field(
        False,
        description="Whether mathematical apparent acceleration is scientifically supported by temporal coverage and data quality",
    )
    acceleration_support_reason: Optional[str] = Field(
        None,
        description="Explicit scientific justification for acceleration support status",
    )
    missing_epoch_count: int = Field(0, ge=0, description="Estimated missing or skipped acquisition epochs")
    max_interval_days: float = Field(0.0, ge=0.0, description="Maximum interval between consecutive epochs in days")
    mean_interval_days: float = Field(0.0, ge=0.0, description="Average interval between consecutive epochs in days")
    quality_summary: Dict[str, Any] = Field(
        default_factory=dict,
        description="Aggregate measurement quality metrics (mean coherence, low quality ratio)",
    )
    explanation: str = Field(..., description="Human- and machine-readable scientific justification")

    model_config = ConfigDict(frozen=True)


class ChronologyVerificationResult(BaseModel):
    """Cryptographic chain verification result."""
    chain_length: int = Field(..., ge=0)
    is_intact: bool
    verification_status: str = Field(..., description="'VALID' or 'CORRUPTED_OR_TAMPERED'")
    error_detail: Optional[str] = None
    infrastructure_id: Optional[str] = None

    model_config = ConfigDict(frozen=True)
