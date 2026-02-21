from sqlalchemy import (
    ARRAY,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from app.core.database import Base

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

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    email_verified = Column(Boolean, default=False, nullable=False)
    status = Column(String, default="PENDING_VERIFICATION", nullable=False)
    verification_token = Column(String, nullable=True)
    verification_token_expires_at = Column(DateTime(timezone=True), nullable=True)

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