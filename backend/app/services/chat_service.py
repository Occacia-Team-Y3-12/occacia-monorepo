"""
app/services/chat_service.py

Fixes:
- Summary carries forward last known missing_info so the AI never resets state
- Summary preserves extracted facts (event type, budget, guests, location)
- Anti-loop: summary notes when conversation was mostly idle/noise
- build_context_string returns turn count so the AI knows where it is
"""

import logging
import re
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.chat_model import ChatMessage

logger = logging.getLogger(__name__)

CONTEXT_RECENT_TURNS = 5


class ChatService:

    # ── Save ──────────────────────────────────────────────────────────────────

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

    # ── Retrieve ──────────────────────────────────────────────────────────────

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
        Guards against dict (legacy format) or None.
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

        if isinstance(val, list):
            return val

        if isinstance(val, dict):
            items = val.get("items", [])
            return items if isinstance(items, list) else []

        return []

    # ── Context Compression ───────────────────────────────────────────────────

    def build_context_string(self, history: List[ChatMessage]) -> str:
        """
        Convert chat history into a compact context string for the AI prompt.

        Structure:
          CONVERSATION STATE       — total turns + what's still missing
          ORIGINAL REQUIREMENTS    — turn 1 (always anchored)
          SUMMARY                  — compressed middle turns with real facts
          RECENT TURNS             — last N turns verbatim
        """
        if not history:
            return ""

        total_turns = len(history)

        # Short conversation — send everything verbatim
        if total_turns <= CONTEXT_RECENT_TURNS + 1:
            lines = [
                f"CONVERSATION STATE: {total_turns} turns so far. "
                f"This is an active conversation — do NOT re-introduce yourself.",
                "",
                "CONVERSATION HISTORY:",
            ]
            for msg in history:
                lines.append(f"User: {msg.user_message}")
                lines.append(f"Assistant: {msg.ai_message}")
            return "\n".join(lines)

        # Long conversation — anchor + summary + recent
        turn_1 = history[0]
        middle = history[1:-CONTEXT_RECENT_TURNS]
        recent = history[-CONTEXT_RECENT_TURNS:]

        # Build the state header with last known missing info
        last_missing = self._get_last_missing_from_history(history)
        state_parts = [f"CONVERSATION STATE: {total_turns} turns so far."]
        if last_missing:
            state_parts.append(f"Still missing: {', '.join(last_missing)}.")
        state_parts.append("Do NOT re-introduce yourself. The conversation is already in progress.")

        # Detect if the last user message was substantive but got a generic reply
        last_ignored = self._detect_ignored_message(history)
        if last_ignored:
            state_parts.append(
                f'⚠️ CRITICAL: The user previously said "{last_ignored}" and you ignored it '
                f"with a generic greeting. Do NOT do that again. Respond to what they actually said."
            )

        lines = [" ".join(state_parts), ""]

        lines += [
            "ORIGINAL REQUIREMENTS (turn 1):",
            f"User: {turn_1.user_message}",
            f"Assistant: {turn_1.ai_message}",
        ]

        if middle:
            summary = self._build_summary(middle)
            lines += [
                "",
                f"CONVERSATION SUMMARY ({len(middle)} turns compressed):",
                summary,
            ]

        lines += [
            "",
            f"RECENT TURNS (last {len(recent)}, verbatim):",
        ]
        seen_ai_responses: set[str] = set()
        for msg in recent:
            lines.append(f"User: {msg.user_message}")
            ai_reply = (msg.ai_message or "").strip()
            # If the AI gave a duplicate/looping response, replace it with a
            # placeholder so the model doesn't learn to repeat it
            if ai_reply in seen_ai_responses:
                lines.append("Assistant: [previous response was repeated — do not repeat it]")
            else:
                seen_ai_responses.add(ai_reply)
                lines.append(f"Assistant: {ai_reply}")

        logger.info(
            f"Context compressed: turn-1 anchored + "
            f"{len(middle)} middle turns -> summary + "
            f"{len(recent)} recent turns verbatim."
        )
        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _detect_ignored_message(self, history: List[ChatMessage]) -> str | None:
        """
        Look at the last few turns. If the user said something substantive
        (more than 4 chars, contains a planning keyword) but the AI replied
        with a generic greeting/intro, return that user message so we can
        call it out in the state header.
        """
        GENERIC_PHRASES = [
            "hey there! i'm occi",
            "hello! i'm occi",
            "i'm occi, your",
            "what are we celebrating today",
            "how can i assist you today",
            "what's on your mind today",
            "it's lovely to connect",
            "it's lovely to start",
            "i'm here to help you with any",
            "how can i make your day",
        ]
        SUBSTANTIVE_KEYWORDS = [
            "plan", "birthday", "party", "dinner", "wedding", "anniversary",
            "book", "venue", "event", "celebrate", "budget", "guests",
            "want to", "need", "looking for", "help me",
        ]

        for msg in reversed(history[-5:]):
            user_text = (msg.user_message or "").strip()
            ai_text = (msg.ai_message or "").strip().lower()

            if len(user_text) <= 4:
                continue

            user_lower = user_text.lower()
            is_substantive = any(kw in user_lower for kw in SUBSTANTIVE_KEYWORDS)
            ai_is_generic = any(phrase in ai_text for phrase in GENERIC_PHRASES)

            if is_substantive and ai_is_generic:
                return user_text

        return None

    def _get_last_missing_from_history(self, history: List[ChatMessage]) -> List[str]:
        """Walk backwards through history to find the most recent non-empty missing_info."""
        for msg in reversed(history):
            val = getattr(msg, "missing_info", None)
            if isinstance(val, list) and val:
                return val
            if isinstance(val, dict):
                items = val.get("items", [])
                if items:
                    return items
        return []

    def _build_summary(self, turns: List[ChatMessage]) -> str:
        """
        Extract real facts from the middle turns.
        Always includes: what was collected, what was still missing,
        and an honest note if the turns were mostly noise.
        """
        facts: dict[str, str] = {}
        last_missing: List[str] = []
        noise_count = 0

        for msg in turns:
            text = (msg.user_message or "").strip()

            # Track noise turns (very short messages with no planning signal)
            if len(text) <= 4:
                noise_count += 1

            text_lower = text.lower()

            # Event type
            for keyword in [
                "birthday", "wedding", "anniversary", "proposal",
                "dinner", "party", "retreat", "corporate", "date",
            ]:
                if keyword in text_lower and "event" not in facts:
                    facts["event"] = keyword

            # Budget
            if "budget" not in facts:
                budget_match = re.search(r"(?:budget|spend|cost)[^\d]*(\d[\d,]*)", text_lower)
                if budget_match:
                    facts["budget"] = budget_match.group(1)
                # Shorthand: 50k, 5k
                shorthand = re.search(r"(\d+)\s*k\b", text_lower)
                if shorthand:
                    facts["budget"] = str(int(shorthand.group(1)) * 1000)

            # Guest count
            if "guests" not in facts:
                guest_match = re.search(r"(\d+)\s*(?:people|guests|persons|pax)", text_lower)
                if guest_match:
                    facts["guests"] = guest_match.group(1)

            # Location
            if "location" not in facts:
                for city in [
                    "colombo", "kandy", "galle", "negombo", "ella",
                    "nuwara eliya", "trincomalee", "jaffna", "bentota", "mirissa",
                ]:
                    if city in text_lower:
                        facts["location"] = city.title()
                        break

            # Carry forward missing_info from AI response
            val = getattr(msg, "missing_info", None)
            if isinstance(val, list) and val:
                last_missing = val
            elif isinstance(val, dict):
                items = val.get("items", [])
                if items:
                    last_missing = items

        # Build summary string
        parts = []

        if facts:
            fact_str = "; ".join(f"{k}: {v}" for k, v in facts.items())
            parts.append(f"Established so far — {fact_str}.")
        else:
            parts.append("No specific event details confirmed in these turns.")

        if noise_count > len(turns) // 2:
            parts.append(
                f"Note: {noise_count} of {len(turns)} turns were short/noisy messages "
                "(greetings, test inputs). Ignore those — focus on the event context."
            )

        if last_missing:
            parts.append(f"Still needed: {', '.join(last_missing)}.")

        parts.append(f"Conversation active for {len(turns)} exchanges.")

        return " ".join(parts)


chat_service = ChatService()