from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ObservationBase(BaseModel):
    infrastructure_id: str = Field(..., description="UUID of associated infrastructure asset")
    acquisition_timestamp: datetime = Field(..., description="Timestamp of satellite acquisition epoch (UTC)")

    deformation_mm: Optional[float] = Field(
        default=None,
        ge=-10000.0,
        le=10000.0,
        description="Estimated structural deformation in millimeters",
    )
    velocity_mm_per_year: Optional[float] = Field(
        default=None,
        ge=-5000.0,
        le=5000.0,
        description="Long-term deformation velocity in mm/year",
    )
    coherence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Interferometric coherence value in range [0.0, 1.0]",
    )
    phase_quality: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Interferometric phase quality metric in range [0.0, 1.0]",
    )
    incidence_angle: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=90.0,
        description="Radar beam incidence angle in degrees [0.0, 90.0]",
    )
    los_displacement_mm: Optional[float] = Field(
        default=None,
        ge=-10000.0,
        le=10000.0,
        description="Radar Line-of-Sight (LOS) displacement in millimeters",
    )
    atmospheric_indicator: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Atmospheric phase screen (APS) indicator or category",
    )
    source: str = Field(
        default="SENTINEL_1",
        min_length=1,
        max_length=100,
        description="Data origin (e.g. SENTINEL_1, PAZ, TSX, SYNTHETIC)",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Scientific metadata (orbit number, polarization, sensor mode)",
    )

    @field_validator("coherence")
    @classmethod
    def validate_coherence(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 1.0):
            raise ValueError("Interferometric coherence must be within [0.0, 1.0]")
        return v

    @field_validator("incidence_angle")
    @classmethod
    def validate_incidence_angle(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and not (0.0 <= v <= 90.0):
            raise ValueError("Radar incidence angle must be within [0.0, 90.0] degrees")
        return v


class ObservationCreate(ObservationBase):
    pass


class ObservationRead(BaseModel):
    id: str
    infrastructure_id: str
    acquisition_timestamp: datetime
    deformation_mm: Optional[float] = None
    velocity_mm_per_year: Optional[float] = None
    coherence: Optional[float] = None
    phase_quality: Optional[float] = None
    incidence_angle: Optional[float] = None
    los_displacement_mm: Optional[float] = None
    atmospheric_indicator: Optional[str] = None
    source: str
    metadata: Optional[Dict[str, Any]] = Field(default=None, alias="observation_metadata")
    created_at: datetime

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)
