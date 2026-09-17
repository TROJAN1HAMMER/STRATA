"""
STRATA Phase 7 Risk Characterization Service Layer.
Exposes the infrastructure risk characterization engine, decision hierarchy, and normalization utilities.
"""
from backend.app.services.risk.engine import (
    InfrastructureRiskCharacterizationEngine,
    CHARACTERIZATION_VERSION,
    DEFAULT_PROFILE_VERSION,
)
from backend.app.services.risk.decision_hierarchy import evaluate_decision_hierarchy
from backend.app.services.risk.normalization import (
    calculate_evidence_components,
    _verify_risk_leakage,
)
from backend.app.services.risk.explanation import generate_structured_explanation

__all__ = [
    "InfrastructureRiskCharacterizationEngine",
    "CHARACTERIZATION_VERSION",
    "DEFAULT_PROFILE_VERSION",
    "evaluate_decision_hierarchy",
    "calculate_evidence_components",
    "_verify_risk_leakage",
    "generate_structured_explanation",
]
