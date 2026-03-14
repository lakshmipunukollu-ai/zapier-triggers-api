"""Subscription database model."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Boolean, DateTime
from app.database import Base


def generate_subscription_id():
    return f"sub_{uuid4().hex[:16]}"


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(String(24), primary_key=True, default=generate_subscription_id)
    consumer_id = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    webhook_url = Column(String(2048), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
