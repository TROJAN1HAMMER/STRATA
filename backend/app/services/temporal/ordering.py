"""
Canonical observation ordering, deduplication, and irregular acquisition interval analysis.
Enforces deterministic chronological processing regardless of input ingestion order.
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple, Union
import numpy as np

from backend.app.schemas.observation import ObservationRead


def _get_timestamp(obs: Any) -> datetime:
    """Extracts timezone-aware UTC datetime from observation object or dict."""
    ts = getattr(obs, "acquisition_timestamp", None)
    if ts is None and isinstance(obs, dict):
        ts = obs.get("acquisition_timestamp")

    if isinstance(ts, str):
        ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts
    raise ValueError(f"Unable to extract valid acquisition_timestamp from observation: {obs}")


def _get_id(obs: Any) -> str:
    """Extracts unique ID from observation object or dict."""
    obs_id = getattr(obs, "id", None)
    if obs_id is None and isinstance(obs, dict):
        obs_id = obs.get("id")
    if not obs_id:
        raise ValueError(f"Observation missing mandatory ID: {obs}")
    return str(obs_id)


def canonicalize_and_order_observations(
    observations: List[Any],
) -> Tuple[List[Any], List[float], int, float]:
    """
    Validates, deduplicates, and canonically orders observations oldest to newest.

    Returns:
      Tuple of:
        - ordered_observations: List[Any] sorted strictly by (timestamp, id)
        - intervals_days: List[float] of consecutive delta days
        - estimated_missing_epochs: int
        - total_coverage_days: float

    Raises:
      ValueError if duplicate observation IDs are detected.
    """
    if not observations:
        return [], [], 0, 0.0

    # 1. Deduplication check
    seen_ids = set()
    for obs in observations:
        obs_id = _get_id(obs)
        if obs_id in seen_ids:
            raise ValueError(f"Duplicate observation ID detected in sequence: '{obs_id}'")
        seen_ids.add(obs_id)

    # 2. Canonical sorting (timestamp ascending, tie-broken deterministically by ID)
    ordered = sorted(observations, key=lambda o: (_get_timestamp(o), _get_id(o)))

    if len(ordered) == 1:
        return ordered, [], 0, 0.0

    # 3. Calculate irregular acquisition intervals (in days)
    intervals_days: List[float] = []
    for i in range(1, len(ordered)):
        t_prev = _get_timestamp(ordered[i - 1])
        t_curr = _get_timestamp(ordered[i])
        delta = (t_curr - t_prev).total_seconds() / 86400.0
        intervals_days.append(max(0.0, delta))

    total_coverage_days = sum(intervals_days)

    # 4. Estimate missing epochs based on median acquisition interval
    estimated_missing_epochs = 0
    if intervals_days:
        median_interval = float(np.median(intervals_days))
        # Sentinel-1 typical orbit repeat is 6 or 12 days; if an interval exceeds 2.5x median, flag gap
        if median_interval > 0:
            for dt in intervals_days:
                if dt > 2.5 * median_interval:
                    missed = int(round(dt / median_interval)) - 1
                    estimated_missing_epochs += max(0, missed)

    return ordered, intervals_days, estimated_missing_epochs, total_coverage_days
