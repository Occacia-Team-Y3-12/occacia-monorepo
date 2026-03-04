from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("EVT"))

    customer_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    location_text = Column(String, nullable=True)
    start_at = Column(DateTime(timezone=True), nullable=True)
    end_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String, nullable=False, default="DRAFT")
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

