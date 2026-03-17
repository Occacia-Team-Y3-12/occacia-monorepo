from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from app.common.utils import now_utc
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    # 🚨 FIXED: Changed from Integer to String to support "CUS-xxxx" format
    customer_id = Column(String, nullable=True, index=True) 
    user_message = Column(Text, nullable=True)
    ai_message = Column(Text, nullable=True)
    missing_info = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)