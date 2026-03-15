# backend/app/models/marketplace.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class VendorStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class OrganizationStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class VendorType(str, enum.Enum):
    INDIVIDUAL = "individual"
    ORGANIZATION = "organization"

class Vendor(Base):
    __tablename__ = "vendors"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    business_name = Column(String(255), nullable=False)
    business_email = Column(String(255), unique=True, nullable=False)
    business_phone = Column(String(50))
    business_address = Column(Text)
    business_type = Column(String(100))
    description = Column(Text)
    logo_url = Column(String(500))
    
    # Status fields
    status = Column(Enum(VendorStatus), default=VendorStatus.PENDING)
    status_reason = Column(Text)  # Reason for rejection or additional info
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Vendor type
    vendor_type = Column(Enum(VendorType), default=VendorType.INDIVIDUAL)
    organization_id = Column(Integer, ForeignKey("organizations.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="vendor_profile")
    organization = relationship("Organization", back_populates="vendors")
    packages = relationship("Package", back_populates="vendor")
    orders = relationship("Order", back_populates="vendor")

class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=False)
    registration_number = Column(String(100), unique=True)
    tax_id = Column(String(100))
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50))
    address = Column(Text)
    website = Column(String(255))
    description = Column(Text)
    logo_url = Column(String(500))
    
    # Status fields
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.PENDING)
    status_reason = Column(Text)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Documents
    business_license_url = Column(String(500))
    tax_certificate_url = Column(String(500))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    vendors = relationship("Vendor", back_populates="organization")
    admin_users = relationship("User", back_populates="managed_organization")

class Package(Base):
    __tablename__ = "packages"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(100))
    images = Column(Text)  # JSON array of image URLs
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    vendor = relationship("Vendor", back_populates="packages")
    orders = relationship("Order", back_populates="package")

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    package_id = Column(Integer, ForeignKey("packages.id"), nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(50), default="pending")
    total_amount = Column(Float, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    package = relationship("Package", back_populates="orders")
    vendor = relationship("Vendor", back_populates="orders")

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())