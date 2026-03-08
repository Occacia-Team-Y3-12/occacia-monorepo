import logging
from typing import List, Optional
from app.models.chat_model import ChatMessage
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CONTEXT_RECENT_TURNS = 5   # always keep the last N turns verbatim
                            # (hard cap — prevents token bloat after turn 10+)


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

    # ── Context compression (hard cap) ───────────────────────────────────────

    def build_context_string(self, history: List[ChatMessage]) -> str:
        """
        Convert chat history into a compact context string for the AI prompt.

        Strategy (prevents Langflow token-limit issues after ~10 turns):
          • Turn 1 is ALWAYS included verbatim — it contains the original
            event requirements (location, budget, guest count, occasion type).
          • Turns 2 … (N-CONTEXT_RECENT_TURNS) are compressed into a one-line
            factual summary extracted by _build_summary().
          • The last CONTEXT_RECENT_TURNS turns are always included verbatim
            so the AI has full conversational context for the current reply.

        For short conversations (≤ CONTEXT_RECENT_TURNS+1 turns) everything
        is included verbatim — no compression needed.
        """
        if not history:
            return ""

        # Short path — no compression needed
        if len(history) <= CONTEXT_RECENT_TURNS + 1:
            lines = ["CONVERSATION HISTORY:"]
            for msg in history:
                lines.append(f"User: {msg.user_message}")
                lines.append(f"Assistant: {msg.ai_message}")
            return "\n".join(lines)

        # Long path — anchor turn 1, compress middle, keep tail verbatim
        turn_1      = history[0]
        middle      = history[1:-CONTEXT_RECENT_TURNS]   # may be empty if len==N+2
        recent      = history[-CONTEXT_RECENT_TURNS:]

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

        lines += ["", "RECENT CONVERSATION (last 5 turns — verbatim):"]
        for msg in recent:
            lines.append(f"User: {msg.user_message}")
            lines.append(f"Assistant: {msg.ai_message}")

        logger.info(
            f"📝 CONTEXT COMPRESSED: turn-1 anchored + "
            f"{len(middle)} middle turns → summary + "
            f"{len(recent)} recent turns verbatim."
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