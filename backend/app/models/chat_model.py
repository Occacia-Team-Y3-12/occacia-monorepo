from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime
from app.core.database import Base  # Inherit from your existing Base

class ChatMessage(Base):
    __tablename__ = "chat_history"

    # Primary Key for the database
    id = Column(Integer, primary_key=True, index=True)
    
    # Session ID links multiple messages to one user/conversation
    session_id = Column(String, index=True, nullable=False)
    
    # Store the actual conversation text
    user_message = Column(Text, nullable=False)
    ai_message = Column(Text, nullable=True)
    
    # Timestamp for sorting history chronologically
    created_at = Column(DateTime, default=datetime.utcnow)