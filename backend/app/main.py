from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.api.v1 import api_v1_router
from backend.app.core.config import get_settings
from backend.app.core.logging import logger
from backend.app.db.database import Base, engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Initialize database tables on application launch
    logger.info("Initializing STRATA database schema...")
    Base.metadata.create_all(bind=engine)
    logger.info("STRATA backend startup complete.")
    yield
    logger.info("STRATA backend shutting down.")


def create_application() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="STRATA — Structural Temporal Analysis & Threat Assessment",
        description=(
            "Non-invasive Structural Health Monitoring (SHM) platform for bridges, dams, "
            "and retaining walls using multi-epoch satellite SAR/InSAR observations."
        ),
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url=f"{settings.API_V1_STR}/docs",
        redoc_url=f"{settings.API_V1_STR}/redoc",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount API routers under /api/v1
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    @app.get("/", tags=["Root"])
    def root():
        return {
            "name": settings.PROJECT_NAME,
            "version": settings.VERSION,
            "documentation": f"{settings.API_V1_STR}/docs",
            "health": f"{settings.API_V1_STR}/health",
            "status": "Operational (Phase 1 Project Foundation)",
        }

    return app


app = create_application()
