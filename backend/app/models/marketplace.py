from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
from app.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, index=True)
    location_base = Column(String) # e.g., "Kandy", "Colombo"
    email = Column(String, unique=True, index=True) # <--- The field we were missing!
    phone = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)
    
    # Relationships
    packages = relationship("Package", back_populates="vendor")

class Package(Base):
    __tablename__ = "packages"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"))
    name = Column(String)
    description = Column(Text)
    price = Column(Float) # Standard price per head or total
    price_per_head = Column(Float, nullable=True) # Specific field for per-head calculation
    min_guests = Column(Integer)
    max_guests = Column(Integer)
    tags = Column(ARRAY(String)) # ["outdoor", "wifi", "vegan"]
    location_coverage = Column(String, nullable=True)

    vendor = relationship("Vendor", back_populates="packages")