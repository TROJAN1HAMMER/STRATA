"""
Pydantic schemas for STRATA Phase 7: Infrastructure-Specific Risk Characterization.
Defines schemas for infrastructure engineering profiles, critical zones, baselines,
calibration profiles, normalized evidence components, and immutable characterization outputs.

CRITICAL SCIENTIFIC PRINCIPLES:
- Characterization states are semantic analytical attention levels, NOT structural failure or collapse predictions.
- No safety certification or engineering sign-off is claimed.
- Prototype characterization indices are bounded (0-100) and decomposed into evidence components.
"""
from datetime import datetime
import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.app.db.models import (
    StructureType,
    MaterialType,
    CriticalityLevel,
    RiskCharacterizationState,
)


class CriticalZoneType(str, enum.Enum):
    SUPPORT = "SUPPORT"
    FOUNDATION = "FOUNDATION"
    PIER = "PIER"
    ABUTMENT = "ABUTMENT"
    DECK = "DECK"
    CREST = "CREST"
    BODY = "BODY"
    SLOPE = "SLOPE"
    JOINT = "JOINT"
    OTHER = "OTHER"


class ExpectedDeformationBehavior(str, enum.Enum):
    MONOTONIC = "MONOTONIC"
    SEASONAL = "SEASONAL"
    STABLE = "STABLE"
    CYCLIC = "CYCLIC"
    UNKNOWN = "UNKNOWN"


class CriticalZone(BaseModel):
    zone_id: str = Field(..., description="Unique zone identifier within the asset")
    zone_name: str = Field(..., description="Descriptive name of structural region")
    zone_type: CriticalZoneType = Field(default=CriticalZoneType.OTHER, description="Civil structural component type")
    importance_weight: float = Field(default=1.0, ge=0.0, le=2.0, description="Prototype contextual importance weighting")
    expected_behavior: Optional[ExpectedDeformationBehavior] = Field(default=None, description="Expected deformation mode")
    baseline: Optional[Dict[str, Any]] = Field(default=None, description="Zone-specific historical baseline if known")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Engineering or inspection notes")


class HistoricalBaseline(BaseModel):
    baseline_mean_mm: float = Field(..., description="Historical mean displacement in mm")
    baseline_std_mm: float = Field(..., ge=0.0, description="Historical standard deviation of displacement in mm")
    baseline_min_mm: Optional[float] = Field(default=None, description="Minimum observed historical displacement in mm")
    baseline_max_mm: Optional[float] = Field(default=None, description="Maximum observed historical displacement in mm")
    baseline_period_days: Optional[float] = Field(default=None, ge=0.0, description="Duration of historical baseline monitoring in days")
    baseline_observation_count: Optional[int] = Field(default=None, ge=1, description="Number of baseline observation epochs")
    baseline_source: Optional[str] = Field(default="HISTORICAL_INSAR", description="Origin of baseline data")


class CalibrationProfile(BaseModel):
    profile_version: str = Field(default="v1.0.0_prototype", description="Versioned calibration profile identifier")
    deformation_reference_range_mm: float = Field(default=10.0, gt=0.0, description="Prototype reference displacement scale (mm)")
    baseline_deviation_factor: float = Field(default=1.0, ge=0.0, description="Weighting factor for baseline z-score deviation")
    persistence_weight: float = Field(default=0.35, ge=0.0, le=1.0, description="Prototype weight for structural persistence")
    acceleration_weight: float = Field(default=0.25, ge=0.0, le=1.0, description="Prototype weight for supported acceleration")
    consensus_weight: float = Field(default=0.20, ge=0.0, le=1.0, description="Prototype weight for cross-model agreement")
    quality_weight: float = Field(default=0.10, ge=0.0, le=1.0, description="Prototype weight for measurement quality")
    critical_zone_weight: float = Field(default=0.10, ge=0.0, le=1.0, description="Prototype weight for critical zone location")
    criticality_context_weight: float = Field(default=1.0, ge=0.5, le=2.0, description="Contextual attention multiplier based on asset criticality")
    seasonal_suppression_active: bool = Field(default=True, description="Enforces environmental recurrence suppression")


class InfrastructureProfileUpdate(BaseModel):
    structure_type: Optional[StructureType] = None
    material: Optional[MaterialType] = None
    criticality: Optional[CriticalityLevel] = None
    expected_behavior: Optional[List[ExpectedDeformationBehavior]] = None
    geometry_context: Optional[Dict[str, Any]] = None
    critical_zones: Optional[List[CriticalZone]] = None
    historical_baseline: Optional[HistoricalBaseline] = None
    calibration_profile: Optional[CalibrationProfile] = None


class InfrastructureProfileRead(BaseModel):
    infrastructure_id: str
    name: str
    structure_type: StructureType
    material: MaterialType
    criticality: CriticalityLevel
    expected_behavior: List[ExpectedDeformationBehavior]
    geometry_context: Optional[Dict[str, Any]] = None
    critical_zones: List[CriticalZone] = []
    historical_baseline: Optional[HistoricalBaseline] = None
    calibration_profile: CalibrationProfile
    profile_version: str

    model_config = ConfigDict(from_attributes=True)


class EvidenceComponents(BaseModel):
    measurement_quality: float = Field(..., ge=0.0, le=1.0, description="Normalized interferometric quality (0-1)")
    consensus_support: float = Field(..., ge=0.0, le=1.0, description="Normalized cross-model agreement and confidence (0-1)")
    temporal_persistence: float = Field(..., ge=0.0, le=1.0, description="Multi-epoch structural persistence score (0-1)")
    trend_significance: float = Field(..., ge=0.0, le=1.0, description="Normalized linear rate relative to structural reference range (0-1)")
    acceleration_support: float = Field(..., ge=0.0, le=1.0, description="Supported deformation acceleration score (0 if unsupported)")
    environmental_suppression: float = Field(..., ge=0.0, le=1.0, description="Suppression factor (1.0 = full environmental suppression)")
    critical_zone_context: float = Field(..., ge=1.0, le=2.0, description="Contextual spatial modifier based on critical zones")
    baseline_deviation_mm: Optional[float] = Field(default=None, description="Difference between recent deformation and baseline mean (mm)")
    baseline_z_score: Optional[float] = Field(default=None, description="Standardized deviation z-score if historical baseline exists")


class RiskCharacterizationRead(BaseModel):
    id: str
    infrastructure_id: str
    observation_window_start: Optional[datetime] = None
    observation_window_end: Optional[datetime] = None
    epoch_count: int
    characterization_state: RiskCharacterizationState
    confidence: float = Field(..., ge=0.0, le=1.0)
    prototype_risk_index: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Prototype analytical characterization index (0-100)")

    evidence_components: EvidenceComponents
    supporting_factors: List[str]
    suppressing_factors: List[str]
    uncertainty_factors: List[str]
    explanation: str
    version_metadata: Dict[str, str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
