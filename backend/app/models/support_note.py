from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class SupportNote(Base):
    __tablename__ = "support_notes"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("SUP"))

    admin_id = Column(String, index=True, nullable=False)
    event_id = Column(String, index=True, nullable=True)
    task_id = Column(String, index=True, nullable=True)
    vendor_id = Column(String, index=True, nullable=True)
    action_type = Column(String, nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

