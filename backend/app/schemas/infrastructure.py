from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field
from backend.app.db.models import (
    StructureType,
    MaterialType,
    CriticalityLevel,
)
from backend.app.schemas.risk import (
    CriticalZone,
    HistoricalBaseline,
    CalibrationProfile,
    ExpectedDeformationBehavior,
)


class InfrastructureBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Identifier or name of the infrastructure asset")
    structure_type: StructureType = Field(default=StructureType.OTHER, description="Civil structural classification")
    material: MaterialType = Field(default=MaterialType.UNKNOWN, description="Primary structural material")
    criticality: CriticalityLevel = Field(default=CriticalityLevel.UNKNOWN, description="Operational importance/criticality level")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="WGS84 latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="WGS84 longitude coordinate")
    description: Optional[str] = Field(default=None, max_length=2000, description="Asset context or engineering description")

    expected_behavior: Optional[List[ExpectedDeformationBehavior]] = Field(default=None, description="Expected deformation modes")
    geometry_context: Optional[Dict[str, Any]] = Field(default=None, description="Spatial orientation or dimensions")
    critical_zones: Optional[List[CriticalZone]] = Field(default=None, description="Monitored critical structural zones")
    historical_baseline: Optional[HistoricalBaseline] = Field(default=None, description="Historical displacement baseline")
    calibration_profile: Optional[CalibrationProfile] = Field(default=None, description="Asset calibration weighting parameters")
    profile_version: Optional[str] = Field(default="v1.0.0", description="Profile version")


class InfrastructureCreate(InfrastructureBase):
    pass


class InfrastructureUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    structure_type: Optional[StructureType] = None
    material: Optional[MaterialType] = None
    criticality: Optional[CriticalityLevel] = None
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    description: Optional[str] = Field(default=None, max_length=2000)

    expected_behavior: Optional[List[ExpectedDeformationBehavior]] = None
    geometry_context: Optional[Dict[str, Any]] = None
    critical_zones: Optional[List[CriticalZone]] = None
    historical_baseline: Optional[HistoricalBaseline] = None
    calibration_profile: Optional[CalibrationProfile] = None
    profile_version: Optional[str] = None


class InfrastructureRead(InfrastructureBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

