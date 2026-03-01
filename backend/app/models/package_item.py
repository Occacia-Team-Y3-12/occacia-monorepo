from __future__ import annotations

from sqlalchemy import Column, Float, Integer, String

from app.common.utils import generate_prefixed_id
from app.core.database import Base


class PackageItem(Base):
    __tablename__ = "package_items"

    id = Column(Integer, primary_key=True, index=True)
    package_item_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("PKI"))

    package_id = Column(String, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=False)
    offering_id = Column(String, index=True, nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)

