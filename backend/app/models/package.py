from __future__ import annotations
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class Package(Base):
    __tablename__ = "packages"

    id                = Column(Integer, primary_key=True, index=True)
    vendor_id         = Column(String, nullable=False, index=True)
    name              = Column(String, nullable=False)
    description       = Column(Text)
    price             = Column(Float)
    price_per_head    = Column(Float, nullable=True)
    min_guests        = Column(Integer)
    max_guests        = Column(Integer)
    tags              = Column(JSON, default=list)
    location_coverage = Column(String, nullable=True)
    blocked_dates     = Column(JSON, nullable=True, default=list)

    # vendor_id is a String storing "VEN-xxx" — join on vendors.vendor_id not vendors.id
    vendor = relationship(
        "Vendor",
        primaryjoin="Package.vendor_id == foreign(Vendor.vendor_id)",
        uselist=False,
        viewonly=True,
    )