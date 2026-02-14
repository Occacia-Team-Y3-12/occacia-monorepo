import logging
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.chat_model import ChatMessage

logger = logging.getLogger(__name__)

class ChatService:
    def save_message(self, db: Session, session_id: str, user_msg: str, ai_msg: str):
        """Saves a single turn of conversation to the database."""
        try:
            new_entry = ChatMessage(
                session_id=session_id,
                user_message=user_msg,
                ai_message=ai_msg
            )
            db.add(new_entry)
            db.commit()
            db.refresh(new_entry)
            return new_entry
        except Exception as e:
            db.rollback()
            logger.error(f"❌ Failed to save chat history: {e}")
            return None

    def get_session_history(self, db: Session, session_id: str, limit: int = 5):
        """Retrieves the last X messages for a specific session to provide context."""
        messages = db.query(ChatMessage)\
            .filter(ChatMessage.session_id == session_id)\
            .order_by(desc(ChatMessage.created_at))\
            .limit(limit)\
            .all()
        
        # We reverse them so they are in chronological order (Oldest -> Newest)
        return messages[::-1]

# Global instance for easy import
chat_service = ChatService()