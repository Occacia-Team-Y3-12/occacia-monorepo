from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.common.utils import generate_prefixed_id
from app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("CUS"))

    # EERD attributes
    full_name = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    locale = Column(String, nullable=True)

    # Auth / account fields used by current endpoints
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    address = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="PENDING_VERIFICATION", nullable=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)
    calendar_provider = Column(String, nullable=True)
    calendar_default_id = Column(String, nullable=True)
    calendar_connected_at = Column(DateTime(timezone=True), nullable=True)
    calendar_last_sync_at = Column(DateTime(timezone=True), nullable=True)
    calendar_oauth_state = Column(String, nullable=True)
