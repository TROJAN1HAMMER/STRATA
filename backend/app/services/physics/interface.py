from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from backend.app.schemas.physics import ObservationSequence, PhysicsEvidence
from backend.app.services.insar.interface import InSARNormalizedFeatures


@dataclass(frozen=True)
class PhysicsConsistencyOutput:
    is_physically_admissible: bool
    physics_classification: Optional[str]
    physics_confidence: Optional[float]
    boundary_checks: Dict[str, bool]
    anomalies_detected: List[str]
    is_stub: bool
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    scientific_notice: str = "Phase 1 / 2 Kinematic Sanity Layer."


class PhysicsConsistencyEngineInterface(ABC):
    @abstractmethod
    def verify_consistency(self, features: InSARNormalizedFeatures) -> PhysicsConsistencyOutput:
        """Single-observation physical boundary validation."""
        pass


class MultiEpochPhysicsEngineInterface(ABC):
    @abstractmethod
    def evaluate_sequence(self, sequence: ObservationSequence) -> PhysicsEvidence:
        """Multi-epoch deterministic InSAR consistency evaluation."""
        pass
