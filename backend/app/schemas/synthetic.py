from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class GroundTruthClass(str, Enum):
    """
    Explicit physical ground-truth classes reflecting the underlying generative process.
    Independent of physics engine inferences or ML predictions.
    """
    STABLE = "STABLE"
    STRUCTURAL_MONOTONIC = "STRUCTURAL_MONOTONIC"
    STRUCTURAL_ACCELERATING = "STRUCTURAL_ACCELERATING"
    SEASONAL_ENVIRONMENTAL = "SEASONAL_ENVIRONMENTAL"
    ATMOSPHERIC_TRANSIENT = "ATMOSPHERIC_TRANSIENT"
    LOW_QUALITY = "LOW_QUALITY"
    TEMPORALLY_INCONSISTENT = "TEMPORALLY_INCONSISTENT"


class EpochGroundTruthDecomposition(BaseModel):
    """
    Isolated ground-truth components used to synthesize the observed displacement.
    Mathematical invariant:
        observed_displacement_mm == (
            true_structural_displacement_mm
            + true_environmental_displacement_mm
            + true_atmospheric_displacement_mm
            + true_noise_mm
        )
    within numerical tolerance.
    """
    true_structural_displacement_mm: float = Field(
        ...,
        description="Ground-truth structural deformation component in mm",
    )
    true_environmental_displacement_mm: float = Field(
        ...,
        description="Ground-truth cyclic environmental/thermal component in mm",
    )
    true_atmospheric_displacement_mm: float = Field(
        ...,
        description="Ground-truth atmospheric phase screen / turbulence spike component in mm",
    )
    true_noise_mm: float = Field(
        ...,
        description="Ground-truth zero-mean measurement noise component in mm",
    )

    model_config = ConfigDict(frozen=True)

    @property
    def total_reconstructed_displacement_mm(self) -> float:
        return (
            self.true_structural_displacement_mm
            + self.true_environmental_displacement_mm
            + self.true_atmospheric_displacement_mm
            + self.true_noise_mm
        )


class SyntheticEpoch(BaseModel):
    """
    A single synthetic InSAR observation epoch.
    Contains both the public observation data and the isolated ground truth decomposition.
    """
    epoch_id: int = Field(..., ge=0, description="Sequential 0-indexed epoch sequence identifier")
    acquisition_timestamp: str = Field(..., description="ISO 8601 UTC timestamp of acquisition")
    observed_displacement_mm: float = Field(
        ...,
        description="Total synthesized observed line-of-sight/vertical displacement in mm",
    )
    los_displacement_mm: float = Field(
        ...,
        description="Projected radar Line-of-Sight (LOS) displacement in mm",
    )
    coherence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Interferometric spatial coherence in range [0.0, 1.0]",
    )
    incidence_angle_deg: float = Field(
        ...,
        ge=0.0,
        le=90.0,
        description="Radar beam incidence angle in degrees [0.0, 90.0]",
    )
    noise_estimate_mm: float = Field(
        ...,
        ge=0.0,
        description="Estimated instrument measurement noise standard deviation in mm",
    )
    phase_quality: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Phase unwrapping quality metric in range [0.0, 1.0]",
    )
    atmospheric_indicator: str = Field(
        default="CLEAR_NOMINAL",
        description="Atmospheric screening indicator or turbulence category",
    )
    ground_truth: EpochGroundTruthDecomposition = Field(
        ...,
        description="Isolated ground-truth decomposition components. NOT for model input or production API.",
    )

    @field_validator("coherence")
    @classmethod
    def validate_coherence(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"Coherence must be within [0.0, 1.0], got {v}")
        return v

    @field_validator("incidence_angle_deg")
    @classmethod
    def validate_incidence_angle(cls, v: float) -> float:
        if not (0.0 <= v <= 90.0):
            raise ValueError(f"Incidence angle must be within [0.0, 90.0], got {v}")
        return v

    def to_public_observation_dict(self, infrastructure_id: str) -> Dict[str, Any]:
        """
        Converts this synthetic epoch to a production STRATA ObservationCreate payload.
        Crucially excludes the `ground_truth` sub-container to prevent accidental leakage.
        """
        return {
            "infrastructure_id": infrastructure_id,
            "acquisition_timestamp": self.acquisition_timestamp,
            "deformation_mm": round(self.observed_displacement_mm, 4),
            "los_displacement_mm": round(self.los_displacement_mm, 4),
            "coherence": round(self.coherence, 4),
            "phase_quality": round(self.phase_quality, 4),
            "incidence_angle": round(self.incidence_angle_deg, 2),
            "atmospheric_indicator": self.atmospheric_indicator,
            "source": "SYNTHETIC",
            "metadata": {
                "synthetic_epoch_id": self.epoch_id,
                "noise_estimate_mm": round(self.noise_estimate_mm, 3),
            },
        }


class SyntheticSequenceSample(BaseModel):
    """
    Complete observation sequence representing an infrastructure monitoring timeline.
    """
    sample_id: str = Field(..., description="Unique sample UUID or deterministic identifier")
    scenario: str = Field(..., description="Descriptive scenario key")
    ground_truth_class: GroundTruthClass = Field(
        ...,
        description="Generative ground-truth classification",
    )
    random_seed: int = Field(..., description="Random seed used to generate this specific sample")
    epoch_count: int = Field(..., ge=2, description="Number of observation epochs in sequence")
    start_date: str = Field(..., description="ISO 8601 start date of observation sequence")
    temporal_spacing_days: float = Field(..., gt=0.0, description="Nominal temporal baseline in days")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="Physical parameter values used in generation",
    )
    is_edge_case: bool = Field(default=False, description="Flag indicating difficult edge case")
    edge_case_type: Optional[str] = Field(default=None, description="Category of edge case if applicable")
    epochs: List[SyntheticEpoch] = Field(..., min_length=2, description="Chronological sequence of epochs")
    split: Optional[str] = Field(
        default=None,
        description="Partition split: 'train', 'validation', or 'test'",
    )
