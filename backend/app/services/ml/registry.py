"""
Lightweight Model Registry for STRATA ML Deformation Classifiers.
Handles artifact serialization, loading, and version tracking.
"""
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import joblib

from backend.app.schemas.ml import ModelMetadata
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FEATURE_GROUP_A_QUALITY,
    FEATURE_GROUP_B_DISPLACEMENT,
    FEATURE_GROUP_C_TEMPORAL_KINEMATIC,
    FEATURE_GROUP_D_PERIODICITY,
    FEATURE_GROUP_E_GEOMETRY,
    FEATURE_SCHEMA_VERSION,
    FORBIDDEN_COLUMNS,
)
from backend.app.services.ml.preprocessing import MLPreprocessor


def save_model_bundle(
    model_dir: str,
    classifier: Any,
    preprocessor: MLPreprocessor,
    metadata: ModelMetadata,
) -> None:
    """
    Serializes a trained model bundle into a versioned model directory.
    Saves:
      - model.joblib (classifier + preprocessor)
      - metadata.json (training provenance and test metrics)
      - feature_schema.json (feature allowlist and groupings)
    """
    os.makedirs(model_dir, exist_ok=True)

    # 1. Save serialized model & preprocessor
    bundle = {
        "classifier": classifier,
        "preprocessor": preprocessor,
        "classes": getattr(classifier, "classes_", None),
        "model_version": metadata.model_version,
    }
    model_path = os.path.join(model_dir, "model.joblib")
    joblib.dump(bundle, model_path)

    # 2. Save metadata.json
    meta_path = os.path.join(model_dir, "metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata.model_dump(), f, indent=2)

    # 3. Save feature_schema.json
    schema_path = os.path.join(model_dir, "feature_schema.json")
    schema_data = {
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "feature_count": len(FEATURE_ALLOWLIST),
        "feature_allowlist": FEATURE_ALLOWLIST,
        "feature_groups": {
            "group_a_quality": FEATURE_GROUP_A_QUALITY,
            "group_b_displacement": FEATURE_GROUP_B_DISPLACEMENT,
            "group_c_temporal_kinematic": FEATURE_GROUP_C_TEMPORAL_KINEMATIC,
            "group_d_periodicity": FEATURE_GROUP_D_PERIODICITY,
            "group_e_geometry": FEATURE_GROUP_E_GEOMETRY,
        },
        "forbidden_columns": sorted(list(FORBIDDEN_COLUMNS)),
    }
    with open(schema_path, "w", encoding="utf-8") as f:
        json.dump(schema_data, f, indent=2)


def load_model_bundle(model_dir: str) -> Tuple[Any, MLPreprocessor, ModelMetadata]:
    """
    Loads model, preprocessor, and metadata from versioned model directory.
    """
    model_path = os.path.join(model_dir, "model.joblib")
    meta_path = os.path.join(model_dir, "metadata.json")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model artifact not found at: {model_path}")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Model metadata not found at: {meta_path}")

    bundle = joblib.load(model_path)
    classifier = bundle["classifier"]
    preprocessor = bundle["preprocessor"]

    with open(meta_path, "r", encoding="utf-8") as f:
        meta_dict = json.load(f)
    metadata = ModelMetadata.model_validate(meta_dict)

    return classifier, preprocessor, metadata
