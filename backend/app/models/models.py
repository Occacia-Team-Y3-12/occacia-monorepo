from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone  # <--- IMPORT timezone
from app.core.database import Base


class Vendor(Base):  # <--- THIS is what Python is looking for
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    location_base = Column(String)
    phone = Column(String)
    is_verified = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)  # ✅ ADD THIS LINE
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
