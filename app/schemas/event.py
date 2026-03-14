"""Pydantic schemas for event API."""
from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    source: str = Field(..., min_length=1, max_length=255, description="Event source, e.g. 'github.com'")
    event_type: str = Field(..., min_length=1, max_length=255, description="Event type, e.g. 'push'")
    payload: Dict[str, Any] = Field(..., description="Arbitrary event data")


class EventResponse(BaseModel):
    id: str
    source: str
    event_type: str
    payload: Dict[str, Any]
    delivery_status: str
    delivery_attempts: int
    consumer_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventListResponse(BaseModel):
    events: List[EventResponse]
    count: int


class EventAck(BaseModel):
    consumer_id: str = Field(..., min_length=1, max_length=255)


class EventAckResponse(BaseModel):
    id: str
    delivery_status: str
    acked_at: Optional[datetime] = None


class EventDeleteResponse(BaseModel):
    deleted: bool
    id: str


class DeliveryLogEntry(BaseModel):
    attempt: int
    status_code: Optional[int] = None
    error: Optional[str] = None
    duration_ms: Optional[int] = None
    at: datetime


class EventStatusResponse(BaseModel):
    id: str
    source: str
    event_type: str
    delivery_status: str
    delivery_attempts: int
    last_attempt_at: Optional[datetime] = None
    acked_at: Optional[datetime] = None
    created_at: datetime
    delivery_log: List[DeliveryLogEntry]
