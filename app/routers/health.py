"""Health check endpoint."""
from fastapi import APIRouter
from sqlalchemy import text
from app.database import engine
from app.redis_client import redis_client

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health check",
    description="Returns service health status including database and Redis connectivity.",
)
def health_check():
    db_status = "connected"
    redis_status = "connected"

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"

    try:
        redis_client.ping()
    except Exception:
        redis_status = "disconnected"

    status = "healthy" if db_status == "connected" and redis_status == "connected" else "degraded"

    return {
        "status": status,
        "database": db_status,
        "redis": redis_status,
    }
