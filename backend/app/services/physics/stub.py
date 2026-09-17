from typing import Dict, List
from backend.app.core.logging import logger
from backend.app.services.insar.interface import InSARNormalizedFeatures
from backend.app.services.physics.interface import (
    PhysicsConsistencyEngineInterface,
    PhysicsConsistencyOutput,
)


class StubPhysicsConsistencyEngine(PhysicsConsistencyEngineInterface):
    """
    Phase 1 Physics Consistency Engine:
    Performs physical boundary and interferometric admissibility checks.
    Does NOT invent fake physics confidence scores.
    """

    MAX_PLAUSIBLE_DEFORMATION_MM: float = 2000.0
    MAX_PLAUSIBLE_VELOCITY_MM_YEAR: float = 1000.0

    def verify_consistency(self, features: InSARNormalizedFeatures) -> PhysicsConsistencyOutput:
        anomalies: List[str] = []
        boundary_checks: Dict[str, bool] = {
            "coherence_threshold": features.is_sufficient_coherence,
            "incidence_angle_valid": True,
            "deformation_bounds": True,
            "velocity_bounds": True,
        }

        if features.incidence_angle_deg is not None:
            if not (15.0 <= features.incidence_angle_deg <= 60.0):
                boundary_checks["incidence_angle_valid"] = False
                anomalies.append(
                    f"Incidence angle {features.incidence_angle_deg}° is outside typical spaceborne SAR range (15°-60°)."
                )

        if features.los_displacement_mm is not None:
            if abs(features.los_displacement_mm) > self.MAX_PLAUSIBLE_DEFORMATION_MM:
                boundary_checks["deformation_bounds"] = False
                anomalies.append(
                    f"LOS displacement {features.los_displacement_mm} mm exceeds plausible civil threshold ({self.MAX_PLAUSIBLE_DEFORMATION_MM} mm)."
                )

        if features.velocity_mm_per_year is not None:
            if abs(features.velocity_mm_per_year) > self.MAX_PLAUSIBLE_VELOCITY_MM_YEAR:
                boundary_checks["velocity_bounds"] = False
                anomalies.append(
                    f"Deformation velocity {features.velocity_mm_per_year} mm/yr exceeds physical civil limit ({self.MAX_PLAUSIBLE_VELOCITY_MM_YEAR} mm/yr)."
                )

        is_admissible = all(boundary_checks.values())

        logger.info(
            f"Physics Engine [VALIDATION STUB] evaluated observation {features.observation_id}: "
            f"admissible={is_admissible}, anomalies={len(anomalies)}"
        )

        return PhysicsConsistencyOutput(
            is_physically_admissible=is_admissible,
            physics_classification="UNEVALUATED_STUB",
            physics_confidence=None,  # Intentionally None: No fake physics score
            boundary_checks=boundary_checks,
            anomalies_detected=anomalies,
            is_stub=True,
            status="VALIDATION_STUB_ONLY",
            metadata={
                "engine": "kinematic_boundary_validator",
                "ruleset_version": "0.1.0-boundary-only",
            },
            scientific_notice="STRATA Phase 1: Physics engine verifies boundary feasibility only. Deterministic structural physics modeling is unasserted.",
        )
