# app/models/chat_model.py
# ADD the missing_info column to your existing ChatMessage model.
# If your file looks different, just add the two lines marked with # ← ADD

from sqlalchemy import Column, DateTime, Integer, JSON, String, Text  # ← ensure JSON is imported
from app.common.utils import now_utc
from app.core.database import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True, nullable=False)
    customer_id = Column(Integer, nullable=True, index=True)
    user_message = Column(Text, nullable=True)
    ai_message = Column(Text, nullable=True)
    missing_info = Column(JSON, nullable=True, default=list)   # ← ADD THIS LINE
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)