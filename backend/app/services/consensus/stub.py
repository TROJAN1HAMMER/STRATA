from backend.app.core.logging import logger
from backend.app.db.models import RiskLevel
from backend.app.services.consensus.interface import (
    ConsensusEngineInterface,
    ConsensusEngineOutput,
)
from backend.app.services.insar.interface import InSARNormalizedFeatures
from backend.app.services.ml.interface import MLPredictionOutput
from backend.app.services.physics.interface import PhysicsConsistencyOutput


class StubConsensusEngine(ConsensusEngineInterface):
    """
    Phase 1 Consensus Engine:
    Contract-satisfying development stub.
    Intentionally does not invent final consensus mathematics or risk scores.
    """

    def evaluate_consensus(
        self,
        features: InSARNormalizedFeatures,
        ml_output: MLPredictionOutput,
        physics_output: PhysicsConsistencyOutput,
        historical_records_count: int = 0,
    ) -> ConsensusEngineOutput:
        logger.info(
            f"Consensus Engine [STUB] processing observation {features.observation_id} with "
            f"{historical_records_count} historical epochs. Consensus algorithm pending scientific specification."
        )

        return ConsensusEngineOutput(
            consensus_classification="PENDING_CONSENSUS_SPECIFICATION",
            consensus_confidence=None,  # Intentionally unasserted
            temporal_confidence=None,
            risk_level=RiskLevel.UNKNOWN,  # Do not assert structural threat without validated model
            disagreement_metric=None,
            is_stub=True,
            status="PENDING_SCIENTIFIC_SPECIFICATION",
            metadata={
                "evidence_sources_evaluated": ["insar_normalized", "ml_stub", "physics_stub"],
                "historical_epochs_considered": historical_records_count,
                "algorithm_status": "Phase 1 interface active; mathematical formulation deferred to Phase 2",
            },
            scientific_notice="STRATA Phase 1: Consensus engine algorithm is pending scientific specification. Risk level unasserted.",
        )
