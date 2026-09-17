import math
from typing import List, Optional
from backend.app.core.logging import logger
from backend.app.db.models import Observation
from backend.app.services.insar.interface import (
    InSARNormalizationServiceInterface,
    InSARNormalizedFeatures,
)


class InSARNormalizationService(InSARNormalizationServiceInterface):
    """
    Phase 1 InSAR Service:
    Provides validation, missing-data handling, and geometrical projection (LOS to vertical).
    Explicitly does NOT perform raw SAR / Sentinel-1 interferometric processing (e.g. coregistration, phase unwrapping).
    """

    MIN_RELIABLE_COHERENCE: float = 0.25

    def normalize_observation(self, observation: Observation) -> InSARNormalizedFeatures:
        warnings: List[str] = []

        # Validate coherence
        is_sufficient_coherence = True
        if observation.coherence is None:
            warnings.append("Missing coherence value; measurement reliability cannot be verified.")
            is_sufficient_coherence = False
        elif observation.coherence < self.MIN_RELIABLE_COHERENCE:
            warnings.append(
                f"Low coherence ({observation.coherence:.3f} < {self.MIN_RELIABLE_COHERENCE}); high noise probability."
            )
            is_sufficient_coherence = False

        # Geometric projection from Line-of-Sight (LOS) to vertical displacement if incidence angle is known
        projected_vertical: Optional[float] = None
        if observation.los_displacement_mm is not None:
            if observation.incidence_angle is not None and 0.0 < observation.incidence_angle < 90.0:
                rad = math.radians(observation.incidence_angle)
                cos_theta = math.cos(rad)
                if abs(cos_theta) > 1e-4:
                    projected_vertical = round(observation.los_displacement_mm / cos_theta, 4)
            else:
                # If no incidence angle, fall back to deformation_mm or los_displacement
                projected_vertical = observation.deformation_mm

        if observation.phase_quality is None:
            warnings.append("Phase quality metric is omitted.")

        logger.debug(
            f"Normalized observation {observation.id}: coherence={observation.coherence}, warnings={len(warnings)}"
        )

        return InSARNormalizedFeatures(
            observation_id=str(observation.id),
            coherence=observation.coherence,
            phase_quality=observation.phase_quality,
            incidence_angle_deg=observation.incidence_angle,
            los_displacement_mm=observation.los_displacement_mm,
            projected_vertical_displacement_mm=projected_vertical,
            velocity_mm_per_year=observation.velocity_mm_per_year,
            atmospheric_screen=observation.atmospheric_indicator,
            is_sufficient_coherence=is_sufficient_coherence,
            validation_warnings=warnings,
            is_simulated_pipeline=True,
            notice="Phase 1 InSAR Feature Validation/Normalization Stub. No raw SAR processing performed.",
        )
