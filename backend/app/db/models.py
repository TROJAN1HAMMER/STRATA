import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Column,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    Enum as SQLEnum,
    JSON,
    Integer,
)
from sqlalchemy.orm import relationship
from backend.app.db.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class StructureType(str, enum.Enum):
    BRIDGE = "BRIDGE"
    DAM = "DAM"
    TUNNEL = "TUNNEL"
    BUILDING = "BUILDING"
    RETAINING_STRUCTURE = "RETAINING_STRUCTURE"
    RETAINING_WALL = "RETAINING_WALL"  # Backward compatibility alias
    EMBANKMENT = "EMBANKMENT"
    PIPELINE = "PIPELINE"
    OTHER = "OTHER"


class MaterialType(str, enum.Enum):
    CONCRETE = "CONCRETE"
    STEEL = "STEEL"
    MASONRY = "MASONRY"
    EARTH = "EARTH"
    ROCK = "ROCK"
    COMPOSITE = "COMPOSITE"
    UNKNOWN = "UNKNOWN"


class CriticalityLevel(str, enum.Enum):
    LOW = "LOW"
    MODERATE = "MODERATE"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    UNKNOWN = "UNKNOWN"


class RiskCharacterizationState(str, enum.Enum):
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    BASELINE = "BASELINE"
    ENVIRONMENTAL_PATTERN = "ENVIRONMENTAL_PATTERN"
    MONITOR = "MONITOR"
    ELEVATED_ATTENTION = "ELEVATED_ATTENTION"
    HIGH_ATTENTION = "HIGH_ATTENTION"


class RiskLevel(str, enum.Enum):
    UNKNOWN = "UNKNOWN"
    NOMINAL = "NOMINAL"
    WATCH = "WATCH"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class Infrastructure(Base):
    __tablename__ = "infrastructures"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(255), nullable=False, index=True)
    structure_type = Column(
        SQLEnum(StructureType, native_enum=False, length=50),
        nullable=False,
        default=StructureType.OTHER,
        index=True,
    )
    material = Column(
        SQLEnum(MaterialType, native_enum=False, length=50),
        nullable=False,
        default=MaterialType.UNKNOWN,
        index=True,
    )
    criticality = Column(
        SQLEnum(CriticalityLevel, native_enum=False, length=50),
        nullable=False,
        default=CriticalityLevel.UNKNOWN,
        index=True,
    )
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    description = Column(Text, nullable=True)

    expected_behavior = Column(JSON, nullable=True)
    geometry_context = Column(JSON, nullable=True)
    critical_zones = Column(JSON, nullable=True)
    historical_baseline = Column(JSON, nullable=True)
    calibration_profile = Column(JSON, nullable=True)
    profile_version = Column(String(50), nullable=False, default="v1.0.0")

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    # Relationships
    observations = relationship(
        "Observation",
        back_populates="infrastructure",
        cascade="all, delete-orphan",
        order_by="Observation.acquisition_timestamp.asc()",
    )
    physics_assessments = relationship(
        "PhysicsAssessment",
        back_populates="infrastructure",
        cascade="all, delete-orphan",
        order_by="PhysicsAssessment.created_at.desc()",
    )
    chronology_records = relationship(
        "ChronologyRecord",
        back_populates="infrastructure",
        cascade="all, delete-orphan",
        order_by="ChronologyRecord.record_index.asc()",
    )
    risk_characterizations = relationship(
        "RiskCharacterization",
        back_populates="infrastructure",
        cascade="all, delete-orphan",
        order_by="RiskCharacterization.created_at.desc()",
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    infrastructure_id = Column(
        String(36),
        ForeignKey("infrastructures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    acquisition_timestamp = Column(DateTime(timezone=True), nullable=False, index=True)

    deformation_mm = Column(Float, nullable=True)
    velocity_mm_per_year = Column(Float, nullable=True)
    coherence = Column(Float, nullable=True)
    phase_quality = Column(Float, nullable=True)

    incidence_angle = Column(Float, nullable=True)
    los_displacement_mm = Column(Float, nullable=True)

    atmospheric_indicator = Column(String(100), nullable=True)

    source = Column(String(100), nullable=False, default="SENTINEL_1")
    observation_metadata = Column("metadata", JSON, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    infrastructure = relationship("Infrastructure", back_populates="observations")
    analysis_results = relationship(
        "AnalysisResult",
        back_populates="observation",
        cascade="all, delete-orphan",
    )
    chronology_records = relationship(
        "ChronologyRecord",
        back_populates="observation",
        cascade="all, delete-orphan",
    )


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    observation_id = Column(
        String(36),
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    ml_classification = Column(String(100), nullable=True)
    ml_confidence = Column(Float, nullable=True)

    physics_classification = Column(String(100), nullable=True)
    physics_confidence = Column(Float, nullable=True)

    consensus_confidence = Column(Float, nullable=True)
    consensus_classification = Column(String(100), nullable=True)

    temporal_confidence = Column(Float, nullable=True)

    risk_level = Column(
        SQLEnum(RiskLevel, native_enum=False, length=50),
        nullable=False,
        default=RiskLevel.UNKNOWN,
        index=True,
    )

    execution_metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    observation = relationship("Observation", back_populates="analysis_results")
    chronology_records = relationship(
        "ChronologyRecord",
        back_populates="analysis_result",
        cascade="all, delete-orphan",
    )


class ChronologyRecord(Base):
    __tablename__ = "chronology_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    observation_id = Column(
        String(36),
        ForeignKey("observations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    analysis_result_id = Column(
        String(36),
        ForeignKey("analysis_results.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    infrastructure_id = Column(
        String(36),
        ForeignKey("infrastructures.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    record_index = Column(Integer, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=utc_now)
    payload = Column(JSON, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    previous_hash = Column(String(64), nullable=False)
    current_hash = Column(String(64), nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    observation = relationship("Observation", back_populates="chronology_records")
    analysis_result = relationship("AnalysisResult", back_populates="chronology_records")
    infrastructure = relationship("Infrastructure", back_populates="chronology_records")


class PhysicsAssessment(Base):
    __tablename__ = "physics_assessments"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    infrastructure_id = Column(
        String(36),
        ForeignKey("infrastructures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    classification = Column(String(50), nullable=False, index=True)
    overall_confidence = Column(Float, nullable=True)
    epoch_count = Column(Integer, nullable=False, default=0)
    evidence_payload = Column(JSON, nullable=False)
    provenance = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    infrastructure = relationship("Infrastructure", back_populates="physics_assessments")


class RiskCharacterization(Base):
    __tablename__ = "risk_characterizations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    infrastructure_id = Column(
        String(36),
        ForeignKey("infrastructures.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    observation_window_start = Column(DateTime(timezone=True), nullable=True)
    observation_window_end = Column(DateTime(timezone=True), nullable=True)
    epoch_count = Column(Integer, nullable=False, default=0)

    characterization_state = Column(
        SQLEnum(RiskCharacterizationState, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    confidence = Column(Float, nullable=False, default=0.0)
    prototype_risk_index = Column(Float, nullable=True)

    evidence_components = Column(JSON, nullable=False)
    supporting_factors = Column(JSON, nullable=False)
    suppressing_factors = Column(JSON, nullable=False)
    uncertainty_factors = Column(JSON, nullable=False)
    explanation = Column(Text, nullable=False)
    version_metadata = Column(JSON, nullable=False)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utc_now)

    # Relationships
    infrastructure = relationship("Infrastructure", back_populates="risk_characterizations")


