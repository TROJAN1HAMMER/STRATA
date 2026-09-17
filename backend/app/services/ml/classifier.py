"""
Inference API for STRATA Machine Learning Deformation Classifier.
Completely decoupled from the deterministic physics engine.
"""
import math
import os
from typing import Any, Dict, List, Optional, Union
import numpy as np

from backend.app.schemas.ml import MLClassificationResult, ModelMetadata
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.synthetic import GroundTruthClass, SyntheticSequenceSample
from backend.app.services.ml.features import (
    FEATURE_ALLOWLIST,
    FEATURE_SCHEMA_VERSION,
    extract_features_from_sequence,
)
from backend.app.services.ml.preprocessing import MLPreprocessor
from backend.app.services.ml.registry import load_model_bundle


DEFAULT_MODEL_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "models", "strata_ml_v0_1_0")
)


def compute_normalized_entropy(probs: np.ndarray) -> float:
    """
    Computes normalized Shannon entropy: H = -sum(p * log2(p)) / log2(K).
    Returns value in [0.0, 1.0]: 0.0 = completely certain, 1.0 = maximum uncertainty.
    """
    k = len(probs)
    if k <= 1:
        return 0.0
    # Avoid log(0)
    eps = 1e-12
    p = np.clip(probs, eps, 1.0)
    p = p / np.sum(p)
    raw_entropy = -float(np.sum(p * np.log2(p)))
    max_entropy = math.log2(k)
    return round(float(max(0.0, min(1.0, raw_entropy / max_entropy))), 4)


class MLDeformationClassifier:
    """
    Independent Machine Learning Deformation Classifier.
    Evaluates multi-epoch InSAR sequences into 7 ground-truth classes with
    calibrated probabilities and uncertainty entropy.
    """

    def __init__(
        self,
        model_dir: str = DEFAULT_MODEL_DIR,
        classifier: Optional[Any] = None,
        preprocessor: Optional[MLPreprocessor] = None,
        metadata: Optional[ModelMetadata] = None,
    ):
        self.model_dir = model_dir

        if classifier is not None and preprocessor is not None and metadata is not None:
            self.classifier = classifier
            self.preprocessor = preprocessor
            self.metadata = metadata
        elif os.path.exists(os.path.join(model_dir, "model.joblib")):
            self.classifier, self.preprocessor, self.metadata = load_model_bundle(model_dir)
        else:
            self.classifier = None
            self.preprocessor = None
            self.metadata = None

    @property
    def is_loaded(self) -> bool:
        return self.classifier is not None and self.preprocessor is not None

    def predict(
        self,
        sequence: Union[ObservationSequence, SyntheticSequenceSample, List[ObservationRead], List[Dict[str, Any]]],
    ) -> MLClassificationResult:
        """
        Runs inference on an InSAR observation sequence.
        Extracts observable features, transforms, and produces calibrated class probabilities.
        """
        if not self.is_loaded:
            raise RuntimeError(f"ML model is not loaded. Model artifacts not found in {self.model_dir}")

        # 1. Extract purely observable features
        features = extract_features_from_sequence(sequence)

        return self.predict_features(features)

    def predict_features(self, features: Dict[str, float]) -> MLClassificationResult:
        """
        Runs inference directly from pre-extracted observable features.
        """
        if not self.is_loaded:
            raise RuntimeError("ML model is not loaded.")

        # 2. Preprocessing (imputation, scaling)
        X_trans = self.preprocessor.transform(features)

        # 3. Probability estimation
        probs_raw = self.classifier.predict_proba(X_trans)[0]

        # Model classes mapping
        model_classes = list(getattr(self.classifier, "classes_", []))
        all_gt_classes = [c.value for c in GroundTruthClass]

        prob_dict: Dict[str, float] = {}
        for c_name in all_gt_classes:
            if c_name in model_classes:
                idx = model_classes.index(c_name)
                prob_dict[c_name] = round(float(probs_raw[idx]), 4)
            else:
                prob_dict[c_name] = 0.0

        # Renormalize to guarantee exact sum = 1.0
        total_p = sum(prob_dict.values())
        if total_p > 0:
            prob_dict = {k: round(v / total_p, 4) for k, v in prob_dict.items()}

        # 4. Determine argmax class and confidence
        pred_class_str = max(prob_dict.items(), key=lambda item: item[1])[0]
        confidence = prob_dict[pred_class_str]

        # 5. Calculate Shannon entropy
        prob_values = np.array([prob_dict[c] for c in all_gt_classes], dtype=np.float64)
        entropy = compute_normalized_entropy(prob_values)

        return MLClassificationResult(
            predicted_class=GroundTruthClass(pred_class_str),
            probabilities=prob_dict,
            confidence=round(confidence, 4),
            entropy=entropy,
            model_version=self.metadata.model_version if self.metadata else "strata_ml_v0_1_0",
            feature_version=FEATURE_SCHEMA_VERSION,
            extracted_features=features,
        )
