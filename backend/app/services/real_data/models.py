"""
Data models and schemas for real-world InSAR dataset ingestion and provenance.
Enforces strict separation between observational radar data and external reference labels.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ReferenceType(str, Enum):
    INDEPENDENT_REFERENCE = "INDEPENDENT_REFERENCE"
    DOCUMENTED_EVENT = "DOCUMENTED_EVENT"
    EXPERT_ANNOTATION = "EXPERT_ANNOTATION"
    KNOWN_DEFORMATION = "KNOWN_DEFORMATION"
    UNKNOWN = "UNKNOWN"


class ReferenceStrength(str, Enum):
    HIGH = "HIGH"
    MODERATE = "MODERATE"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"


class DisplacementType(str, Enum):
    LOS = "LOS"
    VERTICAL = "VERTICAL"
    UNKNOWN = "UNKNOWN"


class ExternalReference(BaseModel):
    """
    Independent ground-truth or reference context from external surveys,
    geotechnical logs, or literature. Kept strictly isolated from model features.
    """
    reference_type: ReferenceType = Field(..., description="Classification of reference source authority")
    reference_source: str = Field(..., description="Authoritative external source (e.g. USGS GNSS, in-situ sensor)")
    reference_strength: ReferenceStrength = Field(default=ReferenceStrength.MODERATE, description="Reliability grade")
    reference_date: Optional[str] = Field(default=None, description="Date or epoch of external reference documentation")
    reference_limitations: str = Field(default="", description="Known limitations of external reference")
    documented_behavior: str = Field(..., description="Behavior documented by external source")
    expected_strata_behavior: str = Field(..., description="Expected analytical characterization in STRATA")


class ExternalDatasetMetadata(BaseModel):
    """
    Complete provenance and acquisition metadata for an external InSAR dataset.
    """
    dataset_id: str = Field(..., description="Unique alphanumeric identifier of dataset")
    dataset_name: str = Field(..., description="Full descriptive title of dataset")
    category: str = Field(..., description="Validation category (A: Stable, B: Deformation, C: Seasonal, D: Atmospheric, E: Low-quality)")
    source: str = Field(..., description="Publishing body or repository (Copernicus, ESA, USGS, ASF, etc.)")
    license: str = Field(..., description="Open data license or usage terms")
    geographic_region: str = Field(..., description="Geographical location and coordinates")
    sensor: str = Field(..., description="SAR Satellite instrument (e.g. Sentinel-1A, TerraSAR-X, PAZ)")
    acquisition_period: Dict[str, str] = Field(..., description="Start and end dates of observation sequence")
    spatial_resolution: str = Field(..., description="Spatial resolution of interferometric product")
    temporal_resolution: str = Field(..., description="Nominal repeat cycle of satellite")
    processing_method: str = Field(..., description="InSAR processing workflow (e.g. PS-InSAR, SBAS, DInSAR)")
    displacement_representation: DisplacementType = Field(..., description="LOS or already projected VERTICAL")
    incidence_angle_deg: Optional[float] = Field(default=None, description="Nominal radar incidence angle in degrees")
    heading_angle_deg: Optional[float] = Field(default=None, description="Satellite orbital heading angle in degrees")
    available_quality_metrics: List[str] = Field(default_factory=list, description="Quality indicators present (e.g. coherence, phase_quality)")
    known_limitations: List[str] = Field(default_factory=list, description="Documented limitations of dataset")
    independent_reference: ExternalReference = Field(..., description="External validation reference metadata")
    checksum_sha256: Optional[str] = Field(default=None, description="SHA-256 integrity checksum of raw dataset")


class RawObservationRecord(BaseModel):
    """
    External observation epoch record before canonical normalization.
    """
    timestamp: str = Field(..., description="Acquisition epoch timestamp (ISO format)")
    displacement: float = Field(..., description="Displacement measurement value")
    displacement_unit: str = Field(default="mm", description="Source unit ('mm', 'm', 'cm')")
    displacement_type: DisplacementType = Field(default=DisplacementType.LOS, description="LOS or VERTICAL")
    coherence: Optional[float] = Field(default=None, description="Interferometric coherence [0.0, 1.0]")
    phase_quality: Optional[float] = Field(default=None, description="Interferometric phase quality metric [0.0, 1.0]")
    incidence_angle: Optional[float] = Field(default=None, description="Epoch-specific incidence angle if variable")
    atmospheric_indicator: Optional[str] = Field(default=None, description="Atmospheric condition indicator if provided")
    flags: List[str] = Field(default_factory=list, description="Data flags (e.g. UNCORRECTED_ATMOSPHERE, FILTERED)")
    raw_metadata: Dict[str, Any] = Field(default_factory=dict, description="Raw provider metadata")

    @field_validator("displacement_unit")
    @classmethod
    def validate_unit(cls, v: str) -> str:
        valid_units = {"mm", "cm", "m"}
        if v.lower() not in valid_units:
            raise ValueError(f"Unsupported displacement unit '{v}'. Supported units: {valid_units}")
        return v.lower()
