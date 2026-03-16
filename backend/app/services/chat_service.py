import logging
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.chat_model import ChatMessage

logger = logging.getLogger(__name__)

CONTEXT_RECENT_TURNS = 5


class ChatService:

    # --- Save ---

    def save_message(
        self,
        db: Session,
        session_id: str,
        user_msg: str,
        ai_msg: str,
        customer_id: Optional[int] = None,
        missing_info: Optional[List[str]] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            session_id=session_id,
            customer_id=customer_id,
            user_message=user_msg,
            ai_message=ai_msg,
            missing_info=missing_info or [],
        )
        db.add(msg)
        db.commit()
        db.refresh(msg)
        return msg

    # --- Retrieve ---

    def get_session_history(self, db: Session, session_id: str) -> List[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )

    def get_last_missing_info(self, db: Session, session_id: str) -> List[str]:
        """
        Return missing_info from the most recent message in a session.
        Guards against the value being a dict (legacy storage format) or None.
        Always returns a plain list.
        """
        last = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .first()
        )
        if not last or not last.missing_info:
            return []

        val = last.missing_info

        # Plain list — normal case
        if isinstance(val, list):
            return val

        # Dict — written by older code that embedded state alongside missing_info
        if isinstance(val, dict):
            items = val.get("items", [])
            return items if isinstance(items, list) else []

        return []

    # --- Context Compression ---

    def build_context_string(self, history: List[ChatMessage]) -> str:
        """
        Convert chat history into a compact context string for the AI prompt.
        Anchors turn 1, compresses the middle, and keeps the tail verbatim.
        """
        if not history:
            return ""

        if len(history) <= CONTEXT_RECENT_TURNS + 1:
            lines = ["CONVERSATION HISTORY:"]
            for msg in history:
                lines.append(f"User: {msg.user_message}")
                lines.append(f"Assistant: {msg.ai_message}")
            return "\n".join(lines)

        turn_1 = history[0]
        middle = history[1:-CONTEXT_RECENT_TURNS]
        recent = history[-CONTEXT_RECENT_TURNS:]

        lines = [
            "ORIGINAL REQUIREMENTS (turn 1 — always keep):",
            f"User: {turn_1.user_message}",
            f"Assistant: {turn_1.ai_message}",
        ]

        if middle:
            summary = self._build_summary(middle)
            lines += [
                "",
                f"CONVERSATION SUMMARY ({len(middle)} middle turns compressed):",
                summary,
            ]

        lines += [
            "",
            f"RECENT CONVERSATION (last {CONTEXT_RECENT_TURNS} turns — verbatim):",
        ]
        for msg in recent:
            lines.append(f"User: {msg.user_message}")
            lines.append(f"Assistant: {msg.ai_message}")

        logger.info(
            f"Context compressed: turn-1 anchored + "
            f"{len(middle)} middle turns -> summary + "
            f"{len(recent)} recent turns verbatim."
        )
        return "\n".join(lines)

    def _build_summary(self, turns: List[ChatMessage]) -> str:
        facts = []

        for msg in turns:
            text = (msg.user_message or "").lower()

            for keyword in [
                "birthday", "wedding", "anniversary", "proposal",
                "dinner", "party", "retreat", "corporate",
            ]:
                if keyword in text and f"event: {keyword}" not in facts:
                    facts.append(f"event: {keyword}")

            budget_match = re.search(r"(?:budget|spend|cost)[^\d]*(\d[\d,]*)", text)
            if budget_match:
                facts.append(f"budget: {budget_match.group(1)}")

            guest_match = re.search(r"(\d+)\s*(?:people|guests|persons|pax)", text)
            if guest_match:
                facts.append(f"guests: {guest_match.group(1)}")

            for city in [
                "colombo", "kandy", "galle", "negombo", "ella",
                "nuwara eliya", "trincomalee", "jaffna", "bentota",
            ]:
                if city in text and f"location: {city}" not in facts:
                    facts.append(f"location: {city}")

        seen = set()
        deduped = []
        for f in facts:
            key = f.split(":")[0]
            if key not in seen:
                seen.add(key)
                deduped.append(f)

        if deduped:
            return (
                f"Earlier in this conversation the user discussed planning an event. "
                f"Key details established: {'; '.join(deduped)}. "
                f"The conversation has been ongoing for {len(turns)} exchanges."
            )
        return (
            f"The user has been planning an event across {len(turns)} exchanges. "
            f"No specific details were definitively confirmed in those earlier turns."
        )


chat_service = ChatService()