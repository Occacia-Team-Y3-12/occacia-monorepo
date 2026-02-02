from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone # <--- IMPORT timezone
from app.database import Base

class Vendor(Base):  # <--- THIS is what Python is looking for
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, unique=True, index=True) # OCA-85
    email = Column(String, unique=True, index=True)        # OCA-85
    business_type = Column(String)
    contact_number = Column(String)
    address = Column(String)
    
    # OCA-87: Default status
    status = Column(String, default="Pending Approval") 
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc)) # OCA-90
