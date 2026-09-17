"""
Pydantic schemas for STRATA Machine Learning Deformation Classifier (Phase 4).
"""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.synthetic import GroundTruthClass


class MLClassificationResult(BaseModel):
    """
    Inference result from the ML deformation classifier.
    Outputs calibrated class probabilities, confidence, and entropy.
    Completely independent of physics engine outputs.
    """
    predicted_class: GroundTruthClass = Field(
        ...,
        description="Predicted deformation ground-truth class",
    )
    probabilities: Dict[str, float] = Field(
        ...,
        description="Normalized probability distribution over all 7 classes summing to 1.0",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (highest class probability)",
    )
    entropy: float = Field(
        ...,
        ge=0.0,
        description="Normalized Shannon entropy of probability distribution (0.0=certain, 1.0=maximum uncertainty)",
    )
    model_version: str = Field(..., description="Semantic version of the trained ML model")
    feature_version: str = Field(..., description="Semantic version of the feature extraction schema")
    extracted_features: Optional[Dict[str, float]] = Field(
        default=None,
        description="Observable features extracted from the observation sequence",
    )

    model_config = ConfigDict(frozen=True)


class ModelMetadata(BaseModel):
    """
    Lightweight model registry metadata artifact.
    """
    model_version: str
    model_type: str
    training_dataset_version: str
    feature_schema_version: str
    training_timestamp: str
    random_seed: int
    hyperparameters: Dict[str, Any]
    feature_allowlist: List[str]
    forbidden_features_checked: List[str]
    test_metrics: Optional[Dict[str, Any]] = None
    calibration_method: Optional[str] = None
    calibrated_brier_score: Optional[float] = None
    calibrated_log_loss: Optional[float] = None
