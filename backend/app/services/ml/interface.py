from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.app.services.insar.interface import InSARNormalizedFeatures


@dataclass(frozen=True)
class MLPredictionOutput:
    classification: Optional[str]
    confidence: Optional[float]
    features_used: List[str]
    is_stub: bool
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    scientific_notice: str = "Phase 1 Stub: No actual ML model evaluation performed. Prediction is intentionally unasserted."


class MLDeformationEngineInterface(ABC):
    @abstractmethod
    def evaluate(self, features: InSARNormalizedFeatures) -> MLPredictionOutput:
        """
        Evaluates InSAR deformation features using machine learning.
        In Phase 1, strictly returns stub contract.
        """
        pass
