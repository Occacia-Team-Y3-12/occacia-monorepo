from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Offering(Base):
    __tablename__ = "offerings"

    id = Column(Integer, primary_key=True, index=True)
    offering_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("OFF"))

    vendor_id = Column(String, ForeignKey("vendors.vendor_id"), index=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    unit = Column(String, nullable=True)
    quality_tier = Column(String, nullable=False, default="MEDIUM")
    is_active = Column(Boolean, default=True, nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

    # Relationships
    vendor = relationship("Vendor", back_populates="offerings")
    task_offerings = relationship("TaskOffering", back_populates="offering", cascade="all, delete-orphan")
    tasks = relationship("VendorTask", back_populates="offering")
