from typing import List, Optional
from backend.app.schemas.observation import ObservationRead
from backend.app.schemas.physics import KinematicEvidence

# Tolerance threshold for empirical vs reported velocity residual in mm/year
KINEMATIC_RESIDUAL_SCALE_MM_YR: float = 15.0  # PROTOTYPE_ASSUMPTION


def evaluate_kinematics(observations: List[ObservationRead]) -> KinematicEvidence:
    """
    Evaluates kinematic consistency between observed displacement increments (dd/dt)
    and reported instantaneous velocities.
    """
    if len(observations) < 2:
        return KinematicEvidence(
            kinematic_consistency=None,
            mean_kinematic_residual_mm_yr=None,
            explanation=["At least 2 observation epochs required for kinematic rate comparison."],
        )

    residuals: List[float] = []
    explanations: List[str] = []

    for i in range(len(observations) - 1):
        obs1 = observations[i]
        obs2 = observations[i + 1]

        d1 = obs1.los_displacement_mm if obs1.los_displacement_mm is not None else obs1.deformation_mm
        d2 = obs2.los_displacement_mm if obs2.los_displacement_mm is not None else obs2.deformation_mm

        if d1 is None or d2 is None:
            continue

        dt_seconds = (obs2.acquisition_timestamp - obs1.acquisition_timestamp).total_seconds()
        if dt_seconds <= 0:
            continue

        dt_years = dt_seconds / (365.25 * 86400.0)
        empirical_velocity_mm_yr = (d2 - d1) / dt_years

        reported_vel = obs2.velocity_mm_per_year
        if reported_vel is None:
            reported_vel = obs1.velocity_mm_per_year

        if reported_vel is not None:
            res = abs(empirical_velocity_mm_yr - reported_vel)
            residuals.append(res)

    if not residuals:
        return KinematicEvidence(
            kinematic_consistency=None,
            mean_kinematic_residual_mm_yr=None,
            explanation=["Velocity field not provided on observations; kinematic validation bypassed."],
        )

    mean_res = sum(residuals) / len(residuals)
    # Normalized consistency metric: 1.0 when residual is 0, decaying towards 0 as residual grows
    consistency_score = round(1.0 / (1.0 + (mean_res / KINEMATIC_RESIDUAL_SCALE_MM_YR)), 3)

    explanations.append(
        f"Mean kinematic rate residual: {mean_res:.2f} mm/yr across {len(residuals)} intervals. "
        f"Kinematic consistency score: {consistency_score:.3f}."
    )

    return KinematicEvidence(
        kinematic_consistency=consistency_score,
        mean_kinematic_residual_mm_yr=round(mean_res, 3),
        explanation=explanations,
    )
