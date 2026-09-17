from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from backend.app.db.models import RiskLevel
from backend.app.services.insar.interface import InSARNormalizedFeatures
from backend.app.services.ml.interface import MLPredictionOutput
from backend.app.services.physics.interface import PhysicsConsistencyOutput


@dataclass(frozen=True)
class ConsensusEngineOutput:
    consensus_classification: Optional[str]
    consensus_confidence: Optional[float]
    temporal_confidence: Optional[float]
    risk_level: RiskLevel
    disagreement_metric: Optional[float]
    is_stub: bool
    status: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    scientific_notice: str = "Phase 1 Consensus Engine: Data contract active. Multi-evidence consensus algorithm pending scientific specification."


class ConsensusEngineInterface(ABC):
    @abstractmethod
    def evaluate_consensus(
        self,
        features: InSARNormalizedFeatures,
        ml_output: MLPredictionOutput,
        physics_output: PhysicsConsistencyOutput,
        historical_records_count: int = 0,
    ) -> ConsensusEngineOutput:
        """
        Synthesizes multi-source evidence (ML + Physics + Temporal) with disagreement penalty.
        In Phase 1, strictly fulfills contract as stub pending scientific specification.
        """
        pass
