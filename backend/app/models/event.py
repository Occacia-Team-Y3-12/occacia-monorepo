from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship

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
    timezone = Column(String, nullable=True)
    is_all_day = Column(Boolean, nullable=False, default=False)
    recurrence_rule = Column(String, nullable=True)
    recurrence_until = Column(DateTime(timezone=True), nullable=True)
    recurrence_count = Column(Integer, nullable=True)
    reminders_enabled = Column(Boolean, nullable=False, default=False)
    reminder_channels = Column(JSON, nullable=False, default=list)
    reminder_offsets = Column(JSON, nullable=False, default=list)
    reminder_schedule_status = Column(String, nullable=True)
    calendar_sync_state = Column(String, nullable=False, default="DISABLED")
    calendar_sync_provider = Column(String, nullable=True)
    calendar_sync_calendar_id = Column(String, nullable=True)
    external_calendar_event_id = Column(String, nullable=True)
    calendar_last_sync_at = Column(DateTime(timezone=True), nullable=True)
    calendar_last_sync_status = Column(String, nullable=True)
    status = Column(String, nullable=False, default="DRAFT", index=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Vendor task board relations
    tasks = relationship("VendorTask", back_populates="event")
