"""
Unit normalization, timestamp canonicalization, and radar geometry projection utilities
for external InSAR dataset ingestion in STRATA Phase 8.

CRITICAL SCIENTIFIC PRINCIPLE:
- Never assume LOS displacement equals vertical displacement.
- Project LOS to vertical ONLY when valid incidence geometry is provided: d_v = d_los / cos(theta).
- If incidence angle is absent, mark geometry as UNAVAILABLE rather than inventing geometry.
- Explicitly convert all units (m, cm -> mm, datetime -> UTC datetime).
"""
from datetime import datetime, timezone
import math
from typing import Any, Optional, Tuple


def convert_displacement_to_mm(value: float, unit: str) -> float:
    """
    Normalizes displacement measurement to millimeters (mm).
    Raises ValueError on unrecognized units.
    """
    u = unit.strip().lower()
    if u in {"mm", "millimeter", "millimeters"}:
        return float(value)
    elif u in {"cm", "centimeter", "centimeters"}:
        return float(value * 10.0)
    elif u in {"m", "meter", "meters"}:
        return float(value * 1000.0)
    else:
        raise ValueError(f"Unsupported displacement unit '{unit}'. Must be 'mm', 'cm', or 'm'.")


def convert_velocity_to_mm_per_year(value: float, unit: str) -> float:
    """
    Normalizes velocity measurement to mm/year.
    """
    u = unit.strip().lower()
    if u in {"mm/year", "mm/yr", "mm/a"}:
        return float(value)
    elif u in {"cm/year", "cm/yr", "cm/a"}:
        return float(value * 10.0)
    elif u in {"m/year", "m/yr", "m/a"}:
        return float(value * 1000.0)
    else:
        raise ValueError(f"Unsupported velocity unit '{unit}'. Must be 'mm/yr', 'cm/yr', or 'm/yr'.")


def convert_acceleration_to_mm_per_year2(value: float, unit: str) -> float:
    """
    Normalizes apparent acceleration measurement to mm/year^2.
    """
    u = unit.strip().lower()
    if u in {"mm/year2", "mm/yr2", "mm/year^2", "mm/yr^2", "mm/a2"}:
        return float(value)
    elif u in {"m/year2", "m/yr2", "m/year^2", "m/yr^2"}:
        return float(value * 1000.0)
    else:
        raise ValueError(f"Unsupported acceleration unit '{unit}'. Must be 'mm/yr^2' or 'm/yr^2'.")


def normalize_timestamp(ts_input: Any) -> datetime:
    """
    Converts various timestamp representations into a timezone-aware UTC datetime.
    """
    if isinstance(ts_input, datetime):
        if ts_input.tzinfo is None:
            return ts_input.replace(tzinfo=timezone.utc)
        return ts_input.astimezone(timezone.utc)
    
    if isinstance(ts_input, str):
        # Support ISO formats (including 'Z' suffix)
        cleaned = ts_input.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    
    raise TypeError(f"Cannot normalize timestamp of type {type(ts_input).__name__}: {ts_input}")


def project_los_to_vertical(
    los_displacement_mm: float,
    incidence_angle_deg: Optional[float],
) -> Tuple[Optional[float], bool]:
    """
    Scientifically projects Line-of-Sight (LOS) displacement to vertical displacement:
        d_v = d_los / cos(theta)

    Returns:
        (vertical_displacement_mm, geometry_available_flag)
    
    If incidence_angle_deg is None or outside valid radar geometry (0 < theta < 90),
    returns (None, False) to prevent inventing geometry.
    """
    if incidence_angle_deg is None:
        return None, False
    
    if not (0.0 < incidence_angle_deg < 90.0):
        return None, False
    
    theta_rad = math.radians(incidence_angle_deg)
    cos_theta = math.cos(theta_rad)
    if cos_theta <= 1e-6:
        return None, False
    
    vertical_mm = los_displacement_mm / cos_theta
    return float(vertical_mm), True


def normalize_coherence(coherence: Optional[float]) -> Tuple[Optional[float], bool]:
    """
    Validates coherence metric in [0.0, 1.0].
    Returns (coherence_val, is_present).
    """
    if coherence is None:
        return None, False
    
    c = float(coherence)
    if 0.0 <= c <= 1.0:
        return c, True
    
    # Clipped if slightly out of numerical bounds
    clipped = max(0.0, min(1.0, c))
    return clipped, True
