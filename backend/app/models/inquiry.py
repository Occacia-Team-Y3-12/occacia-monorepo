"""
app/models/inquiry.py

Support ticket submitted by a customer or vendor to Occacia support.
UC-30: Handle Inquiries
"""
from __future__ import annotations

from sqlalchemy import Column, DateTime, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Inquiry(Base):
    __tablename__ = "inquiries"

    id = Column(
        String,
        primary_key=True,
        index=True,
        default=lambda: generate_prefixed_id("INQ"),
    )
    inquiry_id = Column(
        String,
        unique=True,
        index=True,
        default=lambda: generate_prefixed_id("INQ"),
    )

    created_by_user_id = Column(String, nullable=False, index=True)
    created_by_role = Column(String, nullable=False)

    subject = Column(String, nullable=True)
    message = Column(Text, nullable=False)

    status = Column(String, nullable=False, default="OPEN", index=True)

    handled_by_admin_id = Column(String, nullable=True)
    admin_reply = Column(Text, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
