from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.utils import generate_prefixed_id
from app.core.database import Base


class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("VEN"))

    # EERD attributes
    display_name = Column(String, nullable=True)
    contact_phone = Column(String, nullable=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True, index=True)
    approval_status = Column(String, default="PENDING", index=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    # Legacy attributes used by current endpoints/services
    business_name = Column(String, index=True)
    location_base = Column(String, nullable=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    password_hash = Column(String, nullable=True)

    # Relationships
    offerings = relationship("Offering", back_populates="vendor", cascade="all, delete-orphan")
    vendor_tasks = relationship("VendorTask", back_populates="vendor", cascade="all, delete-orphan")
    organization = relationship("Organization")
