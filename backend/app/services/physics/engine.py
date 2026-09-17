from typing import Any, Dict, List, Optional
from backend.app.core.logging import logger
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import (
    GeometryStatus,
    ObservationSequence,
    PhysicsClassification,
    PhysicsEvidence,
    TemporalTrendPattern,
)
from backend.app.services.physics.atmospheric import evaluate_atmospheric_suspect
from backend.app.services.physics.environmental import evaluate_environmental_evidence
from backend.app.services.physics.geometry import evaluate_geometry
from backend.app.services.physics.kinematics import evaluate_kinematics
from backend.app.services.physics.quality import evaluate_measurement_quality
from backend.app.services.physics.temporal import evaluate_temporal_consistency

ENGINE_NAME: str = "STRATA_PhysicsInSARConsistencyEngine"
ENGINE_VERSION: str = "0.2.1"
CONFIG_VERSION: str = "prototype_v0.2.1_environmental_refinement"


class PhysicsInSARConsistencyEngine:
    """
    Deterministic InSAR Physics Consistency Engine (Phase 2.1):
    Evaluates whether multi-epoch InSAR deformation measurements are consistent
    with genuine progressive structural displacement vs periodic environmental/seasonal cycles,
    atmospheric turbulence, radar decorrelation, geometric weakness, or temporal volatility.

    Preserves component-level evidence without premature score collapse.
    """

    def __init__(
        self,
        engine_name: str = ENGINE_NAME,
        engine_version: str = ENGINE_VERSION,
        config_version: str = CONFIG_VERSION,
    ):
        self.engine_name = engine_name
        self.engine_version = engine_version
        self.config_version = config_version

    def evaluate_sequence(self, sequence: ObservationSequence) -> PhysicsEvidence:
        observations = sequence.observations
        epoch_count = len(observations)

        logger.info(
            f"Evaluating InSAR physics consistency for infrastructure {sequence.infrastructure_id} "
            f"across {epoch_count} epoch(s)."
        )

        # 1. Independent component evidence evaluations
        meas_qual = evaluate_measurement_quality(observations)
        geom_ev = evaluate_geometry(observations)
        kinem_ev = evaluate_kinematics(observations)
        temp_ev = evaluate_temporal_consistency(observations)
        atm_ev = evaluate_atmospheric_suspect(observations, temp_ev)
        env_ev = evaluate_environmental_evidence(observations, temp_ev)

        # 2. Conservative deterministic classification logic
        classification, primary_reasons = self._classify(
            epoch_count=epoch_count,
            meas_qual=meas_qual,
            geom_ev=geom_ev,
            temp_ev=temp_ev,
            atm_ev=atm_ev,
            env_ev=env_ev,
        )

        # 3. Overall confidence calculation
        # Confidence reflects certainty in the consistency assessment, NOT structural safety.
        overall_confidence: Optional[float] = None
        if classification != PhysicsClassification.INSUFFICIENT_EVIDENCE:
            raw_conf = (
                meas_qual.quality_score * 0.40
                + temp_ev.data_sufficiency * 0.40
                + (1.0 - atm_ev.atmospheric_suspect_score) * 0.20
            )
            overall_confidence = round(max(0.10, min(0.95, raw_conf)), 3)

        # Compile comprehensive explainability summary
        all_explanations: List[str] = list(primary_reasons)
        all_explanations.extend(meas_qual.explanation[:2])
        all_explanations.extend(geom_ev.explanation[:2])
        all_explanations.extend(temp_ev.explanation[:2])
        all_explanations.extend(env_ev.explanation[:2])
        all_explanations.extend(atm_ev.explanation[:2])

        provenance: Dict[str, Any] = {
            "engine_name": self.engine_name,
            "engine_version": self.engine_version,
            "config_version": self.config_version,
            "epoch_count_evaluated": epoch_count,
            "is_deterministic": True,
            "scientific_status": "Phase 2.1 environmental discrimination refinement active.",
        }

        return PhysicsEvidence(
            classification=classification,
            measurement_quality=meas_qual,
            geometry_evidence=geom_ev,
            kinematic_evidence=kinem_ev,
            temporal_evidence=temp_ev,
            atmospheric_evidence=atm_ev,
            environmental_evidence=env_ev,
            overall_confidence=overall_confidence,
            explanation=all_explanations,
            is_stub=False,
            provenance=provenance,
        )

    def _classify(
        self,
        epoch_count: int,
        meas_qual,
        geom_ev,
        temp_ev,
        atm_ev,
        env_ev,
    ) -> tuple[PhysicsClassification, List[str]]:
        reasons: List[str] = []

        # Rule 1: Low Quality (decorrelated radar signal, missing fields, or invalid geometry)
        if not meas_qual.has_sufficient_coherence or meas_qual.quality_score < 0.35:
            reasons.append(
                f"Observation sequence exhibits low interferometric quality (score {meas_qual.quality_score:.2f}); "
                f"phase noise prevents reliable deformation characterization."
            )
            return PhysicsClassification.LOW_QUALITY, reasons

        if geom_ev.status == GeometryStatus.INVALID_GEOMETRY:
            reasons.append(
                "Invalid radar incidence angle prevents geometric interpretation of line-of-sight displacement."
            )
            return PhysicsClassification.LOW_QUALITY, reasons

        # Rule 2: Insufficient Data (conservative priority)
        if epoch_count < 3 or temp_ev.data_sufficiency < 0.50:
            reasons.append(
                f"Fewer than 3 observation epochs ({epoch_count}) available; insufficient temporal history to establish persistence."
            )
            return PhysicsClassification.INSUFFICIENT_EVIDENCE, reasons

        # Rule 3: Atmospheric Suspect (transient spike or high atmospheric score)
        if atm_ev.atmospheric_suspect_score >= 0.55 or atm_ev.has_transient_spike:
            reasons.append(
                f"Observed displacement signature contains transient anomalies characteristic of tropospheric phase delays "
                f"(atmospheric suspect score: {atm_ev.atmospheric_suspect_score:.2f})."
            )
            return PhysicsClassification.ATMOSPHERICALLY_SUSPECT, reasons

        # Rule 4: Seasonal / Periodic Environmental Pattern
        # Temporal persistence must NOT be treated as sufficient evidence of progressive structural deformation
        if env_ev.periodicity_detected or env_ev.environmental_suspect_score >= 0.50 or temp_ev.trend_pattern == TemporalTrendPattern.PERIODIC_SEASONAL:
            reasons.append(
                f"Signal exhibits characteristic periodic zero-crossing cycles with bounded amplitude "
                f"(seasonal pattern strength: {env_ev.seasonal_pattern_strength:.2f}). "
                "Classified as seasonally suspect environmental/thermal response rather than progressive structural deformation."
            )
            return PhysicsClassification.SEASONALLY_SUSPECT, reasons

        # Rule 5: Stable Signal Without Significant Deformation
        # Absence of significant deformation should not be described as structural deformation
        if temp_ev.trend_pattern == TemporalTrendPattern.STABLE:
            reasons.append(
                "Observed displacements remain within the nominal millimeter stability noise margin; "
                "no significant progressive structural movement detected."
            )
            return PhysicsClassification.STABLE_NO_SIGNIFICANT_DEFORMATION, reasons

        # Rule 6: Temporal Inconsistency (abrupt jumps and reversals without periodic consistency)
        if temp_ev.abrupt_inconsistency_score >= 0.50 or temp_ev.trend_pattern in (TemporalTrendPattern.VOLATILE, TemporalTrendPattern.TRANSIENT):
            reasons.append(
                f"Displacement trajectory exhibits erratic temporal fluctuations or immediate reversals "
                f"(abrupt inconsistency score: {temp_ev.abrupt_inconsistency_score:.2f})."
            )
            return PhysicsClassification.TEMPORALLY_INCONSISTENT, reasons

        # Rule 7: Persistent Non-Periodic Deformation with Good Measurement & Temporal Consistency
        persistence = temp_ev.persistence or 0.0
        directional = temp_ev.directional_consistency or 0.0

        if persistence >= 0.50 and directional >= 0.65 and not env_ev.periodicity_detected:
            reasons.append(
                f"Available InSAR evidence is consistent with a continuous, non-periodic structural deformation process "
                f"(persistence={persistence:.2f}, directional_consistency={directional:.2f}, pattern={temp_ev.trend_pattern.value})."
            )
            return PhysicsClassification.STRUCTURALLY_CONSISTENT, reasons

        # Fallback for weak or ambiguous signals
        reasons.append("Observed deformation trend is ambiguous across evaluated epochs.")
        return PhysicsClassification.TEMPORALLY_INCONSISTENT, reasons
