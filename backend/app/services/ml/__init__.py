"""
STRATA Machine Learning Deformation Classification Package (Phase 4).
"""
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FEATURE_GROUP_A_QUALITY,
    FEATURE_GROUP_B_DISPLACEMENT,
    FEATURE_GROUP_C_TEMPORAL_KINEMATIC,
    FEATURE_GROUP_D_PERIODICITY,
    FEATURE_GROUP_E_GEOMETRY,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_COLUMNS,
    extract_features_from_sequence,
    validate_feature_dataframe,
)
from backend.app.services.ml.interface import (
    MLDeformationEngineInterface,
    MLPredictionOutput,
)
from backend.app.services.ml.stub import StubMLDeformationEngine
from backend.app.services.ml.preprocessing import MLPreprocessor
from backend.app.services.ml.calibration import (
    calibrate_classifier,
    calculate_multiclass_brier_score,
    evaluate_calibration_metrics,
)
from backend.app.services.ml.registry import (
    save_model_bundle,
    load_model_bundle,
)
from backend.app.services.ml.classifier import (
    MLDeformationClassifier,
    compute_normalized_entropy,
)
from backend.app.services.ml.evaluation import (
    evaluate_classifier_performance,
    perform_confidence_analysis,
    perform_error_analysis,
    perform_ablation_study,
)

__all__ = [
    "MLDeformationEngineInterface",
    "MLPredictionOutput",
    "StubMLDeformationEngine",
    "FEATURE_ALLOWLIST",
    "FEATURE_GROUP_A_QUALITY",
    "FEATURE_GROUP_B_DISPLACEMENT",
    "FEATURE_GROUP_C_TEMPORAL_KINEMATIC",
    "FEATURE_GROUP_D_PERIODICITY",
    "FEATURE_GROUP_E_GEOMETRY",
    "FEATURE_SCHEMA_VERSION",
    "FORBIDDEN_COLUMNS",
    "extract_features_from_sequence",
    "validate_feature_dataframe",
    "MLPreprocessor",
    "calibrate_classifier",
    "calculate_multiclass_brier_score",
    "evaluate_calibration_metrics",
    "save_model_bundle",
    "load_model_bundle",
    "MLDeformationClassifier",
    "compute_normalized_entropy",
    "evaluate_classifier_performance",
    "perform_confidence_analysis",
    "perform_error_analysis",
    "perform_ablation_study",
]

