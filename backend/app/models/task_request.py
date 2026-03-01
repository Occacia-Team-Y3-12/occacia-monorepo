from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class TaskRequest(Base):
    __tablename__ = "task_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("TQR"))

    task_id = Column(String, index=True, nullable=False)
    vendor_id = Column(String, index=True, nullable=False)
    offering_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False, default="SENT")

    requested_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    respond_by = Column(DateTime(timezone=True), nullable=True)
    responded_at = Column(DateTime(timezone=True), nullable=True)
    response_note = Column(Text, nullable=True)
    attempt_no = Column(Integer, nullable=False, default=1)

