"""
Real-Data Adapter and Validation Services for STRATA Phase 8 & 8.1.
"""
from backend.app.services.real_data.adapter import (
    RealDataIngestionService,
    verify_no_leakage,
)
from backend.app.services.real_data.audit import (
    DatasetProvenanceRecord,
    ErrorCase,
    FailureMode,
    ProvenanceStatus,
    ThresholdAction,
    ThresholdOriginType,
    ThresholdRecord,
    compute_distribution_metrics,
    get_formal_phase7_index_disclaimer,
    get_prototype_threshold_registry,
    get_provenance_registry,
)
from backend.app.services.real_data.models import (
    DisplacementType,
    ExternalDatasetMetadata,
    ExternalReference,
    RawObservationRecord,
    ReferenceStrength,
    ReferenceType,
)
from backend.app.services.real_data.normalization import (
    convert_acceleration_to_mm_per_year2,
    convert_displacement_to_mm,
    convert_velocity_to_mm_per_year,
    normalize_coherence,
    normalize_timestamp,
    project_los_to_vertical,
)

__all__ = [
    "RealDataIngestionService",
    "verify_no_leakage",
    "ExternalDatasetMetadata",
    "ExternalReference",
    "RawObservationRecord",
    "ReferenceType",
    "ReferenceStrength",
    "DisplacementType",
    "convert_displacement_to_mm",
    "convert_velocity_to_mm_per_year",
    "convert_acceleration_to_mm_per_year2",
    "normalize_timestamp",
    "project_los_to_vertical",
    "normalize_coherence",
    "ThresholdAction",
    "ThresholdOriginType",
    "ThresholdRecord",
    "ProvenanceStatus",
    "DatasetProvenanceRecord",
    "FailureMode",
    "ErrorCase",
    "get_formal_phase7_index_disclaimer",
    "get_prototype_threshold_registry",
    "get_provenance_registry",
    "compute_distribution_metrics",
]
