"""
Pydantic schemas for STRATA Cross-Model Consensus & Evidence Fusion (Phase 5).
Combines independent ML Deformation Classifier outputs and deterministic Physics
InSAR Consistency Engine evidence into a unified, traceable consensus interpretation.
"""
import enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ConsensusCategory(str, enum.Enum):
    """
    Unified semantic vocabulary for STRATA cross-model consensus.
    Bridges ML ground-truth class predictions and Physics consistency classifications.
    """
    STABLE = "STABLE"
    STRUCTURAL = "STRUCTURAL"
    SEASONAL = "SEASONAL"
    ATMOSPHERIC = "ATMOSPHERIC"
    LOW_QUALITY = "LOW_QUALITY"
    TEMPORALLY_INCONSISTENT = "TEMPORALLY_INCONSISTENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class ConsensusFlag(str, enum.Enum):
    """
    Diagnostic condition flags generated during consensus analysis.
    """
    MODEL_AGREEMENT = "MODEL_AGREEMENT"
    STRONG_MODEL_AGREEMENT = "STRONG_MODEL_AGREEMENT"
    MODEL_DISAGREEMENT = "MODEL_DISAGREEMENT"
    STRONG_MODEL_DISAGREEMENT = "STRONG_MODEL_DISAGREEMENT"
    ENVIRONMENTAL_STRUCTURAL_CONFLICT = "ENVIRONMENTAL_STRUCTURAL_CONFLICT"
    ATMOSPHERIC_STRUCTURAL_CONFLICT = "ATMOSPHERIC_STRUCTURAL_CONFLICT"
    LOW_QUALITY_EVIDENCE = "LOW_QUALITY_EVIDENCE"
    INSUFFICIENT_EVIDENCE_SUPPRESSION = "INSUFFICIENT_EVIDENCE_SUPPRESSION"
    TEMPORAL_INCONSISTENCY_FLAG = "TEMPORAL_INCONSISTENCY_FLAG"


class ConsensusAssessment(BaseModel):
    """
    Structured assessment resulting from cross-model consensus and evidence fusion.
    Preserves underlying ML probabilities, physics evidence, diagnostic flags,
    and mathematical contributions without discarding primary evidence.
    """
    consensus_class: ConsensusCategory = Field(
        ...,
        description="Unified cross-model consensus classification",
    )
    consensus_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score in the consensus interpretation [0.0, 1.0]",
    )
    agreement_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Continuous degree of cross-model agreement based on ML probability mass [0.0, 1.0]",
    )
    disagreement_penalty: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Quantified penalty derived from cross-model disagreement [0.0, 1.0]",
    )
    evidence_quality_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in observation quality (coherence, phase, sufficiency) [0.0, 1.0]",
    )
    temporal_persistence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Strength of temporal kinematic persistence across epochs [0.0, 1.0]",
    )
    ml_contribution: Dict[str, Any] = Field(
        ...,
        description="Preserved ML classifier output (predicted class, probabilities, confidence, entropy)",
    )
    physics_contribution: Dict[str, Any] = Field(
        ...,
        description="Preserved Physics engine output (classification, evidence strength, summary)",
    )
    explanation: str = Field(
        ...,
        description="Transparent, human- and machine-readable scientific justification",
    )
    flags: List[str] = Field(
        default_factory=list,
        description="Diagnostic flags indicating agreement, conflict, or quality warnings",
    )
    model_versions: Dict[str, str] = Field(
        ...,
        description="Semantic version tracking of all participating analytical components",
    )
    consensus_engine_version: str = Field(
        default="strata_consensus_v0.1.0",
        description="Semantic version of the STRATA Consensus Engine",
    )
    scientific_disclaimer: str = Field(
        default=(
            "STRATA Cross-Model Consensus combines independent machine-learning predictions with deterministic "
            "InSAR physics evidence. Consensus confidence represents confidence in the analytical interpretation "
            "of available evidence; it is not a probability of structural failure and does not constitute an "
            "engineering safety determination or collapse prediction."
        ),
        description="Mandatory scientific and legal boundary disclaimer",
    )

    model_config = ConfigDict(frozen=True)
