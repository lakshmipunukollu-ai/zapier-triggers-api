"""Pydantic schemas for metrics API."""
from pydantic import BaseModel


class MetricsResponse(BaseModel):
    total_events: int
    pending: int
    delivered: int
    acked: int
    failed: int
    dead: int
    avg_delivery_time_ms: float
