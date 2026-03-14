"""Pydantic schemas for subscription API."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class SubscriptionCreate(BaseModel):
    consumer_id: str = Field(..., min_length=1, max_length=255)
    event_type: Optional[str] = Field(None, max_length=255)
    source: Optional[str] = Field(None, max_length=255)
    webhook_url: Optional[str] = Field(None, max_length=2048)


class SubscriptionResponse(BaseModel):
    id: str
    consumer_id: str
    event_type: Optional[str] = None
    source: Optional[str] = None
    webhook_url: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SubscriptionListResponse(BaseModel):
    subscriptions: List[SubscriptionResponse]
    count: int
