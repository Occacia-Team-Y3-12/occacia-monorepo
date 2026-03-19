from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    registration_number = Column(String(100), unique=True, nullable=True)
    tax_id = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    status = Column(String(50), default="pending", nullable=False)
    status_reason = Column(Text, nullable=True)
    reviewed_by = Column(Integer, nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    business_license_url = Column(String(500), nullable=True)
    tax_certificate_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
