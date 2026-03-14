"""Delivery log database model."""
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from app.database import Base


class DeliveryLog(Base):
    __tablename__ = "delivery_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(24), ForeignKey("events.id"), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    duration_ms = Column(Integer, nullable=True)
    attempted_at = Column(DateTime, nullable=False, default=datetime.utcnow)
