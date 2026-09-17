import math
from typing import List, Optional
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import GeometryEvidence, GeometryStatus

NOMINAL_INCIDENCE_MIN_DEG: float = 15.0  # Literature: typical lower limit for spaceborne SAR
NOMINAL_INCIDENCE_MAX_DEG: float = 60.0  # Literature: upper limit for spaceborne SAR


def evaluate_geometry(observations: List[ObservationRead]) -> GeometryEvidence:
    """
    Evaluates SAR radar look geometry, incidence angle limits, and LOS vs vertical projection.
    Strictly keeps LOS displacement separate from projected vertical displacement.
    """
    if not observations:
        return GeometryEvidence(
            status=GeometryStatus.INVALID_GEOMETRY,
            incidence_angle_deg=None,
            mean_los_displacement_mm=None,
            mean_projected_vertical_mm=None,
            geometric_sensitivity_factor=None,
            explanation=["No observations available for geometric evaluation."],
        )

    incidence_angles = [obs.incidence_angle for obs in observations if obs.incidence_angle is not None]
    los_displacements = [obs.los_displacement_mm for obs in observations if obs.los_displacement_mm is not None]
    deformations = [obs.deformation_mm for obs in observations if obs.deformation_mm is not None]

    explanations: List[str] = []

    mean_angle: Optional[float] = None
    sensitivity_factor: Optional[float] = None
    if incidence_angles:
        mean_angle = sum(incidence_angles) / len(incidence_angles)

    mean_los: Optional[float] = None
    if los_displacements:
        mean_los = sum(los_displacements) / len(los_displacements)
    elif deformations:
        mean_los = sum(deformations) / len(deformations)
        explanations.append("LOS displacement not explicitly provided; using general deformation field.")

    status = GeometryStatus.VALID_GEOMETRY

    if mean_angle is None:
        status = GeometryStatus.WEAK_GEOMETRY
        explanations.append("Incidence angle not recorded; 1D line-of-sight cannot be projected to vertical component.")
        mean_projected_vertical = mean_los
    elif mean_angle <= 0.0 or mean_angle >= 90.0:
        status = GeometryStatus.INVALID_GEOMETRY
        explanations.append(f"Incidence angle {mean_angle:.1f}° is physically invalid.")
        mean_projected_vertical = None
    else:
        rad = math.radians(mean_angle)
        sensitivity_factor = round(math.cos(rad), 4)

        if not (NOMINAL_INCIDENCE_MIN_DEG <= mean_angle <= NOMINAL_INCIDENCE_MAX_DEG):
            status = GeometryStatus.WEAK_GEOMETRY
            explanations.append(
                f"Incidence angle {mean_angle:.1f}° is outside nominal spaceborne range "
                f"[{NOMINAL_INCIDENCE_MIN_DEG}°, {NOMINAL_INCIDENCE_MAX_DEG}°]."
            )
        else:
            explanations.append(
                f"Incidence angle {mean_angle:.1f}° is within nominal spaceborne SAR range; "
                f"vertical sensitivity cos(theta) = {sensitivity_factor:.3f}."
            )

        if mean_los is not None and sensitivity_factor > 1e-4:
            mean_projected_vertical = round(mean_los / sensitivity_factor, 3)
            explanations.append(
                f"Reported mean LOS: {mean_los:.2f} mm -> Projected vertical: {mean_projected_vertical:.2f} mm."
            )
        else:
            mean_projected_vertical = None

    return GeometryEvidence(
        status=status,
        incidence_angle_deg=round(mean_angle, 2) if mean_angle is not None else None,
        mean_los_displacement_mm=round(mean_los, 3) if mean_los is not None else None,
        mean_projected_vertical_mm=mean_projected_vertical,
        geometric_sensitivity_factor=sensitivity_factor,
        explanation=explanations,
    )
