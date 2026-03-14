"""
Zapier Triggers API — A platform primitive for event ingestion and reliable delivery.

Delivery Guarantee: At-least-once with idempotency keys.
Retry Policy: Exponential backoff, 7 attempts, then dead-letter queue.
Lock Pattern: SQS-style visibility timeout (30s) on /inbox.
"""
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.redis_client import redis_client
from app.routers import events, subscriptions, metrics, health, auth
from app.services.delivery_worker import process_pending_events, retry_failed_events

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown."""
    # Startup
    logger.info("Starting Zapier Triggers API")
    init_db()

    # Start background workers
    worker_task = asyncio.create_task(process_pending_events(redis_client))
    retry_task = asyncio.create_task(retry_failed_events())

    yield

    # Shutdown
    logger.info("Shutting down Zapier Triggers API")
    worker_task.cancel()
    retry_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        pass
    try:
        await retry_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Zapier Triggers API",
    description=(
        "A platform primitive for event ingestion, reliable delivery, and consumption. "
        "Supports both push (webhook) and pull (inbox polling) delivery with at-least-once guarantees."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(events.router)
app.include_router(subscriptions.router)
app.include_router(metrics.router)
