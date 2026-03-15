from __future__ import annotations
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class EventChatMessage(Base):
    __tablename__ = "event_chat_messages"  
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("MSG"))
    event_id = Column(String, index=True, nullable=False)
    sender = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    sent_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)