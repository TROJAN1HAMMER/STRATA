"""
STRATA Temporal Evidence package.
Provides longitudinal kinematic analysis, state machine tracking, and evidence persistence.
"""
from backend.app.schemas.temporal import (
    ConfidenceDataPoint,
    TemporalEvidenceSummary,
    TemporalStateTransition,
    TemporalStatus,
)
from backend.app.services.temporal.engine import TemporalEvidenceEngine
from backend.app.services.temporal.kinematics import (
    calculate_temporal_kinematics,
    evaluate_acceleration_support,
)
from backend.app.services.temporal.ordering import canonicalize_and_order_observations
from backend.app.services.temporal.persistence import calculate_structural_persistence_score
from backend.app.services.temporal.state_machine import evaluate_temporal_state_machine

__all__ = [
    "ConfidenceDataPoint",
    "TemporalEvidenceSummary",
    "TemporalStateTransition",
    "TemporalStatus",
    "TemporalEvidenceEngine",
    "calculate_temporal_kinematics",
    "evaluate_acceleration_support",
    "canonicalize_and_order_observations",
    "calculate_structural_persistence_score",
    "evaluate_temporal_state_machine",
]
