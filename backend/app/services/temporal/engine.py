"""
STRATA Temporal Evidence Engine (Phase 6).
Coordinates multi-epoch observation ordering, kinematics, persistence evaluation,
state transitions, and transparent longitudinal evidence explanation.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Union
import numpy as np

from backend.app.schemas.consensus import ConsensusAssessment, ConsensusCategory
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import ObservationSequence
from backend.app.schemas.temporal import (
    ConfidenceDataPoint,
    TemporalEvidenceSummary,
    TemporalStatus,
)
from backend.app.services.consensus import ConsensusEngine
from backend.app.services.ml.classifier import MLDeformationClassifier
from backend.app.services.physics.engine import PhysicsInSARConsistencyEngine
from backend.app.services.temporal.kinematics import calculate_temporal_kinematics
from backend.app.services.temporal.ordering import (
    _get_id,
    _get_timestamp,
    canonicalize_and_order_observations,
)
from backend.app.services.temporal.persistence import calculate_structural_persistence_score
from backend.app.services.temporal.state_machine import evaluate_temporal_state_machine

# Programmatic Leakage Firewall: strictly forbid hidden synthetic generator keys
FORBIDDEN_GROUND_TRUTH_KEYS: Set[str] = {
    "ground_truth_class",
    "true_structural_displacement_mm",
    "true_environmental_displacement_mm",
    "true_atmospheric_displacement_mm",
    "true_noise_mm",
    "seasonal_amplitude_mm",
    "seasonal_period_days",
    "linear_velocity_mm_yr",
    "acceleration_mm_yr2",
    "step_epoch_idx",
    "step_magnitude_mm",
    "noise_std_mm",
    "spatial_wavelength_m",
    "spike_magnitude_mm",
}


def _verify_temporal_leakage(data: Any, path: str = "input") -> None:
    """Recursively checks and blocks hidden synthetic ground truth parameters."""
    if isinstance(data, dict):
        for k, v in data.items():
            if k in FORBIDDEN_GROUND_TRUTH_KEYS:
                raise ValueError(
                    f"Ground-truth leakage firewall violation at '{path}.{k}': "
                    f"Temporal evidence engine strictly rejects hidden synthetic generator fields."
                )
            if isinstance(v, (dict, list)):
                _verify_temporal_leakage(v, f"{path}.{k}")
    elif isinstance(data, list):
        for idx, item in enumerate(data):
            if isinstance(item, (dict, list)):
                _verify_temporal_leakage(item, f"{path}[{idx}]")


def _generate_temporal_explanation(
    status: TemporalStatus,
    observation_count: int,
    coverage_days: float,
    mean_conf: float,
    persistence_score: float,
    trend_rate: Optional[float],
    accel: Optional[float],
    accel_supported: bool,
    accel_reason: Optional[str],
    missing_epochs: int,
) -> str:
    """Produces concise, human-readable temporal evidence justification without ungrounded failure claims."""
    parts: List[str] = []

    # 1. State explanation
    if status == TemporalStatus.INSUFFICIENT_HISTORY:
        parts.append(
            f"Evidence is currently insufficient to characterize a persistent deformation pattern "
            f"due to limited temporal coverage ({observation_count} epochs over {coverage_days:.1f} days)."
        )
    elif status == TemporalStatus.BASELINE:
        parts.append(
            f"Consistent nominal baseline stability observed across {observation_count} epochs over {coverage_days:.1f} days."
        )
    elif status == TemporalStatus.PERSISTENT:
        parts.append(
            f"Persistent multi-epoch deformation candidate pattern identified across {observation_count} epochs "
            f"(persistence score: {persistence_score:.2f}) with consistent cross-model support."
        )
    elif status == TemporalStatus.EMERGING:
        parts.append(
            f"An emerging deformation candidate pattern is forming across recent observation epochs."
        )
    elif status == TemporalStatus.ENVIRONMENTAL_PATTERN:
        parts.append(
            "The observed deformation pattern is recurring and seasonally structured; temporal accumulation "
            "is therefore treated as environmental evidence rather than structural persistence."
        )
    elif status == TemporalStatus.ATMOSPHERIC_EVENT:
        parts.append(
            "An isolated transient phase disturbance consistent with atmospheric delay was detected and resolved."
        )
    elif status == TemporalStatus.REVERTED:
        parts.append(
            "A previously detected deformation signal has attenuated and returned to the baseline stability profile."
        )
    elif status == TemporalStatus.CONFLICTED:
        parts.append(
            "Material model disagreement across recent observations reduces analytical confidence in the current interpretation."
        )
    elif status == TemporalStatus.LOW_QUALITY:
        parts.append(
            "Interferometric measurement quality is degraded by low coherence, restricting reliable temporal inference."
        )

    # 2. Kinematics context (Computed vs Supported Acceleration)
    if trend_rate is not None:
        parts.append(f"Observed linear deformation trend rate is estimated at {trend_rate:.2f} mm/year.")
        if accel is not None:
            if accel_supported:
                parts.append(f"Apparent deformation-rate change of {accel:.2f} mm/year² is supported by the temporal baseline.")
            elif status == TemporalStatus.BASELINE:
                parts.append(
                    f"Apparent acceleration is mathematically detectable ({accel:.2f} mm/year²), "
                    f"but the sequence remains within the nominal baseline stability envelope and is not treated as supported deformation acceleration."
                )
            else:
                parts.append(
                    f"A numerical acceleration was calculated ({accel:.2f} mm/year²), "
                    f"but the available temporal coverage is insufficient to treat it as supported acceleration evidence."
                )

    # 3. Missing epochs note
    if missing_epochs > 0:
        parts.append(f"Note: Approximately {missing_epochs} acquisition epochs were skipped or missing.")

    # 4. Confidence summary
    parts.append(f"Mean cross-model analytical confidence across the baseline is {mean_conf * 100:.1f}%.")

    return " ".join(parts)


class TemporalEvidenceEngine:
    """
    STRATA Temporal Evidence Engine.
    Processes multi-epoch observation histories, evaluates kinematic rates,
    tracks temporal state transitions, and enforces scientific integrity.
    """

    def __init__(
        self,
        physics_engine: Optional[PhysicsInSARConsistencyEngine] = None,
        ml_classifier: Optional[MLDeformationClassifier] = None,
        consensus_engine: Optional[ConsensusEngine] = None,
    ):
        self.physics_engine = physics_engine or PhysicsInSARConsistencyEngine()
        self.ml_classifier = ml_classifier or MLDeformationClassifier()
        self.consensus_engine = consensus_engine or ConsensusEngine()

    def evaluate_summary(
        self,
        infrastructure_id: str,
        observations: List[Any],
        consensus_history: Optional[List[ConsensusAssessment]] = None,
        **kwargs: Any,
    ) -> TemporalEvidenceSummary:
        """
        Synthesizes raw InSAR observations and consensus history into a TemporalEvidenceSummary.

        Parameters:
          infrastructure_id: Unique asset identifier
          observations: List of observation objects or dicts (can arrive out-of-order)
          consensus_history: Optional pre-evaluated consensus results.
                             If None, sequentially evaluated from observations.
        """
        # 1. Enforce ground-truth leakage firewall
        _verify_temporal_leakage(kwargs, path="extra_kwargs")
        if observations:
            first_obs = observations[0]
            if isinstance(first_obs, dict):
                _verify_temporal_leakage(first_obs, path="observation[0]")
            elif hasattr(first_obs, "__dict__"):
                _verify_temporal_leakage(vars(first_obs), path="observation[0]")

        # 2. Canonical ordering and deduplication
        ordered_obs, intervals_days, missing_epochs, total_coverage_days = (
            canonicalize_and_order_observations(observations)
        )

        n_obs = len(ordered_obs)
        if n_obs == 0:
            return TemporalEvidenceSummary(
                infrastructure_id=infrastructure_id,
                observation_count=0,
                valid_observation_count=0,
                first_observation_time=None,
                last_observation_time=None,
                coverage_duration_days=0.0,
                temporal_status=TemporalStatus.INSUFFICIENT_HISTORY,
                confidence_trajectory=[],
                mean_confidence=0.0,
                recent_confidence=0.0,
                consensus_category_history=[],
                agreement_history=[],
                structural_candidate_count=0,
                environmental_pattern_count=0,
                atmospheric_event_count=0,
                state_transitions=[],
                persistence_score=0.0,
                trend_rate_mm_per_year=None,
                apparent_acceleration_mm_per_year2=None,
                trend_acceleration_mm_per_year2=None,
                acceleration_supported=False,
                acceleration_support_reason=None,
                missing_epoch_count=0,
                max_interval_days=0.0,
                mean_interval_days=0.0,
                quality_summary={},
                explanation="No observations available for this infrastructure asset.",
            )

        first_time = _get_timestamp(ordered_obs[0])
        last_time = _get_timestamp(ordered_obs[-1])

        # 3. Sequential Consensus Evaluation (if not already provided)
        if consensus_history is None or len(consensus_history) != n_obs:
            consensus_history = []
            # Progressively evaluate consensus for each prefix sequence
            for idx in range(n_obs):
                prefix_obs = ordered_obs[: idx + 1]
                pydantic_obs = []
                for o_idx, o_item in enumerate(prefix_obs):
                    if isinstance(o_item, ObservationRead):
                        pydantic_obs.append(o_item)
                    elif isinstance(o_item, dict):
                        pydantic_obs.append(
                            ObservationRead(
                                id=str(o_item.get("id", f"obs_{o_idx}")),
                                infrastructure_id=str(o_item.get("infrastructure_id", infrastructure_id)),
                                acquisition_timestamp=_get_timestamp(o_item),
                                deformation_mm=o_item.get("deformation_mm", o_item.get("observed_displacement_mm", 0.0)),
                                coherence=o_item.get("coherence", 0.8),
                                phase_quality=o_item.get("phase_quality", 0.8),
                                incidence_angle=o_item.get("incidence_angle", o_item.get("incidence_angle_deg", 35.0)),
                                source=str(o_item.get("source", "SYNTHETIC")),
                                created_at=datetime.now(timezone.utc),
                            )
                        )
                    else:
                        pydantic_obs.append(ObservationRead.model_validate(o_item))
                seq = ObservationSequence(
                    infrastructure_id=infrastructure_id,
                    observations=pydantic_obs,
                    start_time=_get_timestamp(prefix_obs[0]),
                    end_time=_get_timestamp(prefix_obs[-1]),
                    epoch_count=len(prefix_obs),
                )
                phys_evidence = self.physics_engine.evaluate_sequence(seq)
                if len(prefix_obs) < 2:
                    from backend.app.schemas.synthetic import GroundTruthClass
                    from backend.app.schemas.ml import MLClassificationResult
                    all_gt = [c.value for c in GroundTruthClass]
                    uniform_p = {c: round(1.0 / len(all_gt), 4) for c in all_gt}
                    ml_res = MLClassificationResult(
                        predicted_class=GroundTruthClass.STABLE,
                        probabilities=uniform_p,
                        confidence=round(1.0 / len(all_gt), 4),
                        entropy=1.0,
                        model_version="strata_ml_v0_1_0",
                        feature_version="strata_features_v0_1_0",
                    )
                else:
                    ml_res = self.ml_classifier.predict(seq)
                assessment = self.consensus_engine.evaluate(
                    ml_result=ml_res,
                    physics_evidence=phys_evidence,
                    epoch_count=len(prefix_obs),
                )
                consensus_history.append(assessment)

        # 4. Kinematics calculations
        trend_rate, trend_accel, accel_supported, accel_reason = calculate_temporal_kinematics(ordered_obs)

        # 5. Multi-epoch persistence calculation
        persistence_score = calculate_structural_persistence_score(
            consensus_history, missing_epoch_count=missing_epochs
        )

        # 6. Sequential state machine evaluation
        temporal_status, transitions = evaluate_temporal_state_machine(
            ordered_observations=ordered_obs,
            consensus_history=consensus_history,
        )

        # 7. Post-state kinematics semantic check (Phase 6.2: Stable sequences must not report supported deformation acceleration)
        if temporal_status == TemporalStatus.BASELINE and trend_accel is not None:
            accel_supported = False
            accel_reason = (
                "Apparent acceleration is mathematically detectable, but the sequence remains "
                "within the nominal baseline stability envelope and is not treated as supported deformation acceleration."
            )

        # 8. Aggregate trajectory & metrics
        trajectory: List[ConfidenceDataPoint] = []
        conf_list: List[float] = []
        agreement_list: List[float] = []
        cat_history: List[str] = []
        structural_count = 0
        seasonal_count = 0
        atmo_count = 0

        for i, a in enumerate(consensus_history):
            obs = ordered_obs[i]
            point = ConfidenceDataPoint(
                observation_id=_get_id(obs),
                timestamp=_get_timestamp(obs),
                consensus_category=a.consensus_class.value,
                confidence=a.consensus_confidence,
                agreement_score=a.agreement_score,
                evidence_quality_score=a.evidence_quality_score,
            )
            trajectory.append(point)
            conf_list.append(a.consensus_confidence)
            agreement_list.append(a.agreement_score)
            cat_history.append(a.consensus_class.value)

            if a.consensus_class == ConsensusCategory.STRUCTURAL:
                structural_count += 1
            elif a.consensus_class == ConsensusCategory.SEASONAL:
                seasonal_count += 1
            elif a.consensus_class == ConsensusCategory.ATMOSPHERIC:
                atmo_count += 1

        mean_conf = float(round(float(np.mean(conf_list)), 4)) if conf_list else 0.0
        recent_conf = float(round(conf_list[-1], 4)) if conf_list else 0.0

        max_int = float(round(max(intervals_days), 2)) if intervals_days else 0.0
        mean_int = float(round(float(np.mean(intervals_days)), 2)) if intervals_days else 0.0

        # Quality metrics
        coherence_vals = []
        for o in ordered_obs:
            c = getattr(o, "coherence", None)
            if c is None and isinstance(o, dict):
                c = o.get("coherence")
            if c is not None and isinstance(c, (int, float)):
                coherence_vals.append(float(c))
        mean_coh = float(round(float(np.mean(coherence_vals)), 4)) if coherence_vals else 0.80

        quality_summary = {
            "mean_coherence": mean_coh,
            "low_quality_epoch_count": cat_history.count(ConsensusCategory.LOW_QUALITY.value),
            "total_epochs": n_obs,
        }

        # 8. Transparent Explanation Synthesis
        explanation = _generate_temporal_explanation(
            status=temporal_status,
            observation_count=n_obs,
            coverage_days=total_coverage_days,
            mean_conf=mean_conf,
            persistence_score=persistence_score,
            trend_rate=trend_rate,
            accel=trend_accel,
            accel_supported=accel_supported,
            accel_reason=accel_reason,
            missing_epochs=missing_epochs,
        )

        return TemporalEvidenceSummary(
            infrastructure_id=infrastructure_id,
            observation_count=n_obs,
            valid_observation_count=n_obs,
            first_observation_time=first_time,
            last_observation_time=last_time,
            coverage_duration_days=round(total_coverage_days, 2),
            temporal_status=temporal_status,
            confidence_trajectory=trajectory,
            mean_confidence=mean_conf,
            recent_confidence=recent_conf,
            consensus_category_history=cat_history,
            agreement_history=agreement_list,
            structural_candidate_count=structural_count,
            environmental_pattern_count=seasonal_count,
            atmospheric_event_count=atmo_count,
            state_transitions=transitions,
            persistence_score=persistence_score,
            trend_rate_mm_per_year=trend_rate,
            apparent_acceleration_mm_per_year2=trend_accel,
            trend_acceleration_mm_per_year2=trend_accel,
            acceleration_supported=accel_supported,
            acceleration_support_reason=accel_reason,
            missing_epoch_count=missing_epochs,
            max_interval_days=max_int,
            mean_interval_days=mean_int,
            quality_summary=quality_summary,
            explanation=explanation,
        )
