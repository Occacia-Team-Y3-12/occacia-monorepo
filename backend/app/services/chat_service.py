import logging
from typing import List, Optional
from app.models.chat_model import ChatMessage
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

SUMMARY_THRESHOLD = 8   # summarise when history exceeds this many turns
RECENT_TURNS_KEPT  = 4  # always keep the last N turns verbatim


class ChatService:

    # ── Save ────────────────────────────────────────────────────────────────

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

    # ── Retrieve ─────────────────────────────────────────────────────────────

    def get_session_history(self, db: Session, session_id: str) -> List[ChatMessage]:
        return (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.asc())
            .all()
        )

    def get_last_missing_info(self, db: Session, session_id: str) -> List[str]:
        """Return missing_info from the most recent message in a session."""
        last = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.id.desc())
            .first()
        )
        if last and last.missing_info:
            return last.missing_info
        return []

    # ── FIX 1: Conversation summary compression ───────────────────────────────

    def build_context_string(self, history: List[ChatMessage]) -> str:
        """
        Convert chat history into a context string for the AI prompt.

        If the conversation is short (≤ SUMMARY_THRESHOLD turns) we include
        every turn verbatim.  Once it grows beyond that we compress the older
        portion into a one-paragraph summary and keep only the most-recent
        RECENT_TURNS_KEPT turns verbatim.  This stops the prompt from ballooning
        after many exchanges.
        """
        if not history:
            return ""

        if len(history) <= SUMMARY_THRESHOLD:
            # Short conversation — include everything verbatim
            lines = ["CONVERSATION HISTORY:"]
            for msg in history:
                lines.append(f"User: {msg.user_message}")
                lines.append(f"Assistant: {msg.ai_message}")
            return "\n".join(lines)

        # Long conversation — summarise the old part, keep recent turns verbatim
        old_turns   = history[:-RECENT_TURNS_KEPT]
        recent_turns = history[-RECENT_TURNS_KEPT:]

        summary = self._build_summary(old_turns)

        lines = [
            "CONVERSATION SUMMARY (earlier turns):",
            summary,
            "",
            "RECENT CONVERSATION (verbatim):",
        ]
        for msg in recent_turns:
            lines.append(f"User: {msg.user_message}")
            lines.append(f"Assistant: {msg.ai_message}")

        logger.info(
            f"📝 CONTEXT COMPRESSED: {len(old_turns)} old turns → summary "
            f"+ {len(recent_turns)} recent turns verbatim."
        )
        return "\n".join(lines)

    def _build_summary(self, turns: List[ChatMessage]) -> str:
        """
        Build a concise factual summary from a list of old chat turns.
        Extracts: event type, location, budget, guest count, date, any
        confirmed preferences — anything that was established.
        """
        facts = []

        for msg in turns:
            text = (msg.user_message or "").lower()

            # Event type hints
            for keyword in ["birthday", "wedding", "anniversary", "proposal",
                            "dinner", "party", "retreat", "corporate"]:
                if keyword in text and f"event: {keyword}" not in facts:
                    facts.append(f"event: {keyword}")

            # Budget
            import re
            budget_match = re.search(
                r"(?:budget|spend|cost)[^\d]*(\d[\d,]*)", text
            )
            if budget_match:
                facts.append(f"budget: {budget_match.group(1)}")

            # Guest count
            guest_match = re.search(
                r"(\d+)\s*(?:people|guests|persons|pax)", text
            )
            if guest_match:
                facts.append(f"guests: {guest_match.group(1)}")

            # Location
            for city in ["colombo", "kandy", "galle", "negombo", "ella",
                         "nuwara eliya", "trincomalee", "jaffna", "bentota"]:
                if city in text and f"location: {city}" not in facts:
                    facts.append(f"location: {city}")

        # De-duplicate while preserving order
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