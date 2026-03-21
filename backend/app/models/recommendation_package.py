from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class RecommendationPackage(Base):
    __tablename__ = "recommendation_packages"

    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("PKG"))

    event_id = Column(String, index=True, nullable=False)
    package_type = Column(String, nullable=False)
    package_total_price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    is_customized = Column(Boolean, default=False, nullable=False)
    base_package_id = Column(String, nullable=True)
    created_by_customer_id = Column(String, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    generated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)
