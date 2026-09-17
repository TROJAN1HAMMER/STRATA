from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from backend.app.db.models import Observation


@dataclass(frozen=True)
class InSARNormalizedFeatures:
    observation_id: str
    coherence: Optional[float]
    phase_quality: Optional[float]
    incidence_angle_deg: Optional[float]
    los_displacement_mm: Optional[float]
    projected_vertical_displacement_mm: Optional[float]
    velocity_mm_per_year: Optional[float]
    atmospheric_screen: Optional[str]
    is_sufficient_coherence: bool
    validation_warnings: List[str]
    is_simulated_pipeline: bool = True
    notice: str = "Normalized InSAR feature container (Phase 1 validation/normalization only. No raw SLC/InSAR radar processing performed)."


class InSARNormalizationServiceInterface(ABC):
    @abstractmethod
    def normalize_observation(self, observation: Observation) -> InSARNormalizedFeatures:
        """
        Validates observation parameters and computes geometry-normalized features.
        Does NOT perform raw interferogram generation or phase unwrapping.
        """
        pass
