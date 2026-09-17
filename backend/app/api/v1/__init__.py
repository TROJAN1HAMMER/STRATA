from fastapi import APIRouter
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.infrastructure import router as infrastructure_router
from backend.app.api.v1.observations import router as observations_router
from backend.app.api.v1.analysis import router as analysis_router
from backend.app.api.v1.physics import router as physics_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router)
api_v1_router.include_router(infrastructure_router)
api_v1_router.include_router(observations_router)
api_v1_router.include_router(analysis_router)
api_v1_router.include_router(physics_router)

__all__ = ["api_v1_router"]
