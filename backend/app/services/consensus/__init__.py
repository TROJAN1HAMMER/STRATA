"""
STRATA Consensus Service package.
Exports the cross-model ConsensusEngine (Phase 5) alongside backward-compatible stubs (Phase 1).
"""
from backend.app.services.consensus.engine import (
    CONSENSUS_ENGINE_VERSION,
    ConsensusEngine,
)
from backend.app.services.consensus.interface import (
    ConsensusEngineInterface,
    ConsensusEngineOutput,
)
from backend.app.services.consensus.stub import StubConsensusEngine

__all__ = [
    "ConsensusEngine",
    "CONSENSUS_ENGINE_VERSION",
    "ConsensusEngineInterface",
    "ConsensusEngineOutput",
    "StubConsensusEngine",
]
