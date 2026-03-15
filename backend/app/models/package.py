from __future__ import annotations
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Float, ForeignKey, Integer, String, Text, JSON
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
    tags = Column(JSON, default=list)
    location_coverage = Column(String, nullable=True)

    blocked_dates = Column(JSON, nullable=True, default=list)
    
    vendor = relationship("Vendor")