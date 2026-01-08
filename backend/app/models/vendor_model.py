from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
from app.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, index=True)
    business_type = Column(String, default="General")
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    address = Column(String, nullable=True)
    
    # SECURITY
    hashed_password = Column(String, nullable=False)
    
    status = Column(String, default="Pending Approval")
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))