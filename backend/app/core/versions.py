"""
Centralized Analytical Versioning Registry for STRATA.
Provides a single source of truth for semantic versions across all pipeline engines.
"""
from typing import Dict

PIPELINE_VERSION: str = "1.0.0"
ML_MODEL_VERSION: str = "0.1.0"
FEATURE_SCHEMA_VERSION: str = "0.1.0"
PHYSICS_ENGINE_VERSION: str = "0.2.1"
CONSENSUS_ENGINE_VERSION: str = "strata_consensus_v0.1.0"
TEMPORAL_ENGINE_VERSION: str = "strata_temporal_v1_0_0"
RISK_CHARACTERIZATION_VERSION: str = "strata_risk_v1_0_0"
CHRONOLOGY_ENGINE_VERSION: str = "1.0.0"
THRESHOLD_REGISTRY_VERSION: str = "1.0.0"


def get_system_versions() -> Dict[str, str]:
    """Returns a dictionary of all component semantic versions for audit and traceability."""
    return {
        "pipeline_version": PIPELINE_VERSION,
        "ml_model_version": ML_MODEL_VERSION,
        "feature_schema_version": FEATURE_SCHEMA_VERSION,
        "physics_engine_version": PHYSICS_ENGINE_VERSION,
        "consensus_engine_version": CONSENSUS_ENGINE_VERSION,
        "temporal_engine_version": TEMPORAL_ENGINE_VERSION,
        "risk_characterization_version": RISK_CHARACTERIZATION_VERSION,
        "chronology_engine_version": CHRONOLOGY_ENGINE_VERSION,
        "threshold_registry_version": THRESHOLD_REGISTRY_VERSION,
    }


SYSTEM_VERSIONS = get_system_versions()
