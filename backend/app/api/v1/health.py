from datetime import datetime, timezone
from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from backend.app.core.config import get_settings
from backend.app.db.database import get_db

router = APIRouter(tags=["Health"])


@router.get("/health", summary="Service Health & Diagnostic Status")
def get_health(db: Session = Depends(get_db)) -> Dict[str, Any]:
    settings = get_settings()
    db_status = "connected"

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
