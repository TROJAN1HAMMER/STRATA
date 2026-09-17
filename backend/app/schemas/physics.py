import enum
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.observation import ObservationRead


class PhysicsClassification(str, enum.Enum):
    STABLE_NO_SIGNIFICANT_DEFORMATION = "STABLE_NO_SIGNIFICANT_DEFORMATION"
    STRUCTURALLY_CONSISTENT = "STRUCTURALLY_CONSISTENT"
    ATMOSPHERICALLY_SUSPECT = "ATMOSPHERICALLY_SUSPECT"
    SEASONALLY_SUSPECT = "SEASONALLY_SUSPECT"
    TEMPORALLY_INCONSISTENT = "TEMPORALLY_INCONSISTENT"
    LOW_QUALITY = "LOW_QUALITY"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class GeometryStatus(str, enum.Enum):
    VALID_GEOMETRY = "VALID_GEOMETRY"
    WEAK_GEOMETRY = "WEAK_GEOMETRY"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"


class TemporalTrendPattern(str, enum.Enum):
    STABLE = "STABLE"
    MONOTONIC = "MONOTONIC"
    ACCELERATING = "ACCELERATING"
    TRANSIENT = "TRANSIENT"
    PERIODIC_SEASONAL = "PERIODIC_SEASONAL"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    VOLATILE = "VOLATILE"
    UNDETERMINED = "UNDETERMINED"


class MeasurementQualityEvidence(BaseModel):
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Overall normalized measurement quality [0.0, 1.0]")
    coherence_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized coherence quality evidence")
    phase_quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Normalized phase quality evidence")
    missing_fields_count: int = Field(default=0, ge=0)
    has_sufficient_coherence: bool = Field(...)
    explanation: List[str] = Field(default_factory=list)


class GeometryEvidence(BaseModel):
    status: GeometryStatus
    incidence_angle_deg: Optional[float] = Field(None, description="Reported incidence angle in degrees")
    mean_los_displacement_mm: Optional[float] = None
    mean_projected_vertical_mm: Optional[float] = None
    geometric_sensitivity_factor: Optional[float] = Field(
        None, description="cos(theta) projection factor from vertical to radar LOS"
    )
    explanation: List[str] = Field(default_factory=list)


class KinematicEvidence(BaseModel):
    kinematic_consistency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Consistency between displacement derivatives and reported velocity"
    )
    mean_kinematic_residual_mm_yr: Optional[float] = Field(
        None, description="Average absolute residual between empirical velocity and reported velocity"
    )
    explanation: List[str] = Field(default_factory=list)


class TemporalEvidence(BaseModel):
    persistence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Measure of deformation presence across epochs"
    )
    directional_consistency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Alignment of deformation vectors along persistent direction"
    )
    rate_consistency: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Steadiness of epoch-to-epoch rate of change"
    )
    abrupt_inconsistency_score: float = Field(
        0.0, ge=0.0, le=1.0, description="Degree of isolated reversals or sudden unexplained jumps"
    )
    data_sufficiency: float = Field(
        ..., ge=0.0, le=1.0, description="Evaluation confidence based on number and distribution of epochs"
    )
    trend_pattern: TemporalTrendPattern = Field(default=TemporalTrendPattern.UNDETERMINED)
    total_displacement_mm: Optional[float] = None
    mean_velocity_mm_yr: Optional[float] = None
    epoch_count: int = Field(..., ge=0)
    explanation: List[str] = Field(default_factory=list)


class AtmosphericEvidence(BaseModel):
    atmospheric_suspect_score: float = Field(
        ..., ge=0.0, le=1.0, description="Degree to which deformation signature matches atmospheric artifact profiles"
    )
    has_transient_spike: bool = Field(default=False)
    atmospheric_indicator_reported: Optional[str] = None
    atmospheric_data_status: str = Field(
        ..., description="E.g. AVAILABLE, ATMOSPHERIC_DATA_UNAVAILABLE"
    )
    explanation: List[str] = Field(default_factory=list)


class EnvironmentalEvidence(BaseModel):
    periodicity_detected: bool = Field(
        default=False,
        description="Indicates whether repeated cyclical zero-crossings and directional reversals are present",
    )
    seasonal_pattern_strength: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Confidence in periodic seasonal/environmental oscillation [0.0, 1.0]",
    )
    reversal_consistency: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Regularity of sign transitions across cycles [0.0, 1.0]",
    )
    cycle_count: int = Field(
        default=0,
        ge=0,
        description="Number of detected half or full zero-crossing oscillation cycles",
    )
    environmental_suspect_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Composite score indicating likelihood of environmental/thermal rather than structural deformation",
    )
    explanation: List[str] = Field(default_factory=list)


class ObservationSequence(BaseModel):
    infrastructure_id: str
    observations: List[ObservationRead]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    epoch_count: int = Field(..., ge=0)


class PhysicsEvidence(BaseModel):
    classification: PhysicsClassification
    measurement_quality: MeasurementQualityEvidence
    geometry_evidence: GeometryEvidence
    kinematic_evidence: KinematicEvidence
    temporal_evidence: TemporalEvidence
    atmospheric_evidence: AtmosphericEvidence
    environmental_evidence: EnvironmentalEvidence
    overall_confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Confidence in consistency assessment (NOT structural safety)"
    )
    explanation: List[str] = Field(..., description="Human and machine-readable scientific justification")
    is_stub: bool = Field(
        default=False,
        description="False for deterministic physics engine",
    )
    provenance: Dict[str, Any] = Field(..., description="Engine name, version, and configuration tracking")
    scientific_disclaimer: str = Field(
        default=(
            "STRATA Physics InSAR Consistency Engine evaluates data consistency with progressive structural deformation "
            "versus seasonal/environmental cycles, atmospheric artifacts, or interferometric noise. "
            "STRUCTURALLY_CONSISTENT does NOT imply structural failure, imminent collapse, or safety certification."
        )
    )


class PhysicsAssessmentRead(BaseModel):
    id: str
    infrastructure_id: str
    classification: PhysicsClassification
    overall_confidence: Optional[float]
    epoch_count: int
    evidence_payload: Dict[str, Any]
    provenance: Dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
