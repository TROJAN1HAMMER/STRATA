from typing import List
from backend.app.core.logging import logger
from backend.app.services.insar.interface import InSARNormalizedFeatures
from backend.app.services.ml.interface import (
    MLDeformationEngineInterface,
    MLPredictionOutput,
)


class StubMLDeformationEngine(MLDeformationEngineInterface):
    """
    Phase 1 Development Stub for ML Deformation Engine.
    Strictly satisfies interface contract without fabricating predictions.
    """

    def evaluate(self, features: InSARNormalizedFeatures) -> MLPredictionOutput:
        features_used: List[str] = [
            k for k in ["coherence", "los_displacement_mm", "projected_vertical_displacement_mm", "velocity_mm_per_year"]
            if getattr(features, k) is not None
        ]

        logger.info(
            f"ML Engine [STUB] evaluated observation {features.observation_id}. "
            f"Features present: {features_used}. Model execution bypassed (Phase 1 prototype)."
        )

        return MLPredictionOutput(
            classification="UNASSESSED_STUB",
            confidence=None,
            features_used=features_used,
            is_stub=True,
            status="PENDING_MODEL_INTEGRATION",
            metadata={
                "engine_version": "0.1.0-stub",
                "model_artifact": None,
                "input_warnings": features.validation_warnings,
            },
            scientific_notice="STRATA Phase 1: Machine learning model inference is not implemented. Classification is unasserted.",
        )
