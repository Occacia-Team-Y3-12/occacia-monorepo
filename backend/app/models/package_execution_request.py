from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class PackageExecutionRequest(Base):
    __tablename__ = "package_execution_requests"

    id = Column(Integer, primary_key=True, index=True)
    execution_request_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("EXE"))

    event_id = Column(String, index=True, nullable=False)
    package_id = Column(String, index=True, nullable=False)
    idempotency_key = Column(String, unique=True, index=True, nullable=False)
    currency = Column(String, nullable=False)
    package_total_price = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="CREATED", index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    status_updated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

