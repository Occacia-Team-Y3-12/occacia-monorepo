from __future__ import annotations

from sqlalchemy import ARRAY, Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    name = Column(String)
    description = Column(Text)
    price = Column(Float)
    price_per_head = Column(Float, nullable=True)
    min_guests = Column(Integer)
    max_guests = Column(Integer)
    tags = Column(ARRAY(String))
    location_coverage = Column(String, nullable=True)

    vendor = relationship("Vendor")

