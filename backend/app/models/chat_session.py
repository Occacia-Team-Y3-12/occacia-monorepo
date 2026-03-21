"""
app/models/chat_session.py
Stores conversation state for the planning flow per event.
Used as the source of truth when Redis is unavailable.
Redis is a fast cache on top — this is the write-through backing store.

Columns
-------
event_id            — matches Event.event_id, one session per event
step                — current flow step (matches _STEP_* constants in planning_service)
persona_draft       — JSON: persona fields collected in-memory this session
chosen_persona_id   — persona_id of the confirmed persona (existing or newly saved)
venue_data          — JSON: {budget, guest_count, location, event_date, tags, vibe}
rec_ids             — JSON list: package ids shown in last recommendation round
gift_rec_ids        — JSON list: gift package ids shown in last recommendation round
pending_save        — JSON: persona data awaiting save confirmation
booking_id          — set after PackageExecutionRequest created
ai_fallback_venues  — JSON list: AI-generated venue concepts when DB has no matches
ai_fallback_gifts   — JSON list: AI-generated gift concepts when DB has no matches
is_ai_fallback      — "true"/"false": whether current recs are AI-generated
updated_at          — auto-updated on every write
"""
from __future__ import annotations
from sqlalchemy import Column, DateTime, Integer, String, Text
from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id                  = Column(Integer, primary_key=True, index=True)
    event_id            = Column(String, unique=True, index=True, nullable=False)
    step                = Column(String, nullable=False, default="0")
    persona_draft       = Column(Text, nullable=True)        # JSON string
    chosen_persona_id   = Column(String, nullable=True)
    venue_data          = Column(Text, nullable=True)         # JSON string
    rec_ids             = Column(Text, nullable=True)         # JSON list string
    gift_rec_ids        = Column(Text, nullable=True)         # JSON list string
    pending_save        = Column(Text, nullable=True)         # JSON string
    booking_id          = Column(String, nullable=True)

    # AI fallback state
    ai_fallback_venues  = Column(Text, nullable=True)         # JSON list string
    ai_fallback_gifts   = Column(Text, nullable=True)         # JSON list string
    is_ai_fallback      = Column(String, nullable=True, default="false")  # "true"/"false"

    updated_at          = Column(
        DateTime(timezone=True),
        default=now_utc,
        onupdate=now_utc,
        nullable=False,
    )