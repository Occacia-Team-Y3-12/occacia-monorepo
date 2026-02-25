from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from app.core.database import Base

# --- EXISTING VENDOR MODEL ---
class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, unique=True, index=True) # OCA-85
    email = Column(String, unique=True, index=True)         # OCA-85
    business_type = Column(String)
    contact_number = Column(String)
    address = Column(String)
    
    # OCA-87: Default status
    status = Column(String, default="Pending Approval") 
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # OCA-90

# --- NEW CUSTOMER MODEL (Added for UC-07) ---
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    
    # Basic Profile Info
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Reset Password Fields
    reset_token = Column(String, nullable=True, unique=True)
    reset_token_expires = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))