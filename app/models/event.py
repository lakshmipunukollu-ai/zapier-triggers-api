"""Event database model."""
import enum
from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, Integer, DateTime, Enum, Text
from sqlalchemy.dialects.postgresql import JSONB
from app.database import Base


class DeliveryStatus(str, enum.Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    ACKED = "acked"
    FAILED = "failed"
    DEAD = "dead"


def generate_event_id():
    return f"evt_{uuid4().hex[:16]}"


class Event(Base):
    __tablename__ = "events"

    id = Column(String(24), primary_key=True, default=generate_event_id)
    source = Column(String(255), nullable=False, index=True)
    event_type = Column(String(255), nullable=False, index=True)
    payload = Column(JSONB, nullable=False)
    idempotency_key = Column(String(64), unique=True, nullable=False, index=True)
    delivery_status = Column(
        Enum(DeliveryStatus, name="delivery_status_enum"),
        nullable=False,
        default=DeliveryStatus.PENDING,
        index=True,
    )
    delivery_attempts = Column(Integer, default=0)
    consumer_id = Column(String(255), nullable=True, index=True)
    locked_until = Column(DateTime, nullable=True)
    last_attempt_at = Column(DateTime, nullable=True)
    acked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
