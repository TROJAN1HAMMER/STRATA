"""
Probability Calibration for STRATA ML Deformation Classifiers.
Calibrates model probability outputs using the validation split.
Compatible with modern scikit-learn FrozenEstimator and legacy cv='prefit'.
"""
from typing import Any, Dict, List, Tuple
import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, log_loss

try:
    from sklearn.frozen import FrozenEstimator
    HAS_FROZEN = True
except ImportError:
    HAS_FROZEN = False


def calibrate_classifier(
    fitted_base_estimator: Any,
    X_val: np.ndarray,
    y_val: np.ndarray,
    method: str = "sigmoid",
) -> CalibratedClassifierCV:
    """
    Fits probability calibration using the validation split.
    Guarantees no test set leakage into calibration parameters.
    """
    if HAS_FROZEN:
        calibrated = CalibratedClassifierCV(
            estimator=FrozenEstimator(fitted_base_estimator),
            method=method,
        )
    else:
        calibrated = CalibratedClassifierCV(
            estimator=fitted_base_estimator,
            method=method,
            cv="prefit",
        )
    calibrated.fit(X_val, y_val)
    return calibrated


def calculate_multiclass_brier_score(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    classes: List[str],
) -> float:
    """
    Computes generalized multi-class Brier score:
    Brier = (1/N) * sum_{i=1}^N sum_{k=1}^K (p_{ik} - y_{ik})^2
    Range: [0.0, 2.0], lower is better.
    """
    n_samples = len(y_true)
    class_to_idx = {c: i for i, c in enumerate(classes)}
    y_one_hot = np.zeros((n_samples, len(classes)), dtype=np.float64)
    for idx, c in enumerate(y_true):
        if c in class_to_idx:
            y_one_hot[idx, class_to_idx[c]] = 1.0

    sq_err = np.sum((y_prob - y_one_hot) ** 2, axis=1)
    return float(np.mean(sq_err))


def evaluate_calibration_metrics(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    classes: List[str],
) -> Dict[str, float]:
    """
    Evaluates probabilistic calibration quality (Brier score and Log Loss).
    """
    sorted_classes = sorted(classes)
    brier = calculate_multiclass_brier_score(y_true, y_prob, sorted_classes)
    try:
        loss = float(log_loss(y_true, y_prob, labels=sorted_classes))
    except Exception:
        loss = float("nan")

    return {
        "brier_score": round(brier, 4),
        "log_loss": round(loss, 4),
    }
