from __future__ import annotations

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    notification_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("NTF"))

    user_id = Column(String, index=True, nullable=False)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    event_id = Column(String, index=True, nullable=True)
    task_id = Column(String, index=True, nullable=True)
    channel = Column(String, nullable=False, default="EMAIL")
    type = Column(String, index=True, nullable=False)
    status = Column(String, index=True, nullable=False)
    dedupe_key = Column(String, index=True, nullable=True)
    payload = Column(JSON, nullable=False, default=dict)
    subject = Column(String, nullable=False)
    body_text = Column(Text, nullable=False)
    body_html = Column(Text, nullable=True)
    provider = Column(String, nullable=True)
    provider_message_id = Column(String, nullable=True)
    attempt_count = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=4)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)
    next_attempt_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
