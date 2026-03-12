"""
app/models/persona.py  — full Persona model with structured preference fields.

New columns (additive migration required):
    food_preferences    JSON  (list of strings)
    color_preferences   JSON
    music_preferences   JSON
    personality_tags    JSON
    is_confirmed        Boolean  default False
    confirmed_at        DateTime nullable

These new fields are what ai_service._build_structured_persona_context() already reads.
The legacy `preferences_json` column is retained for backward-compat.
"""
from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Persona(Base):
    __tablename__ = "personas"

    # ── Primary key / identity ──────────────────────────────────────────────
    id         = Column(Integer, primary_key=True, index=True)
    persona_id = Column(
        String, unique=True, index=True,
        default=lambda: generate_prefixed_id("PER"),
    )

    # ── Ownership ───────────────────────────────────────────────────────────
    customer_id = Column(String, index=True, nullable=False)  # "CUS-xxx"

    # ── Core identity ───────────────────────────────────────────────────────
    name         = Column(String, nullable=False)
    relationship = Column(String, nullable=True)   # e.g. "girlfriend", "mom"
    birthday     = Column(DateTime(timezone=True), nullable=True)
    personality  = Column(Text, nullable=True)     # free text description

    # ── Legacy preferences (hobbies list) — kept for backward compat ────────
    preferences_json = Column(JSON, nullable=True)

    # ── Structured preference fields (new — used by AI service) ─────────────
    food_preferences  = Column(JSON, nullable=True)  # ["sushi", "pizza"]
    color_preferences = Column(JSON, nullable=True)  # ["blue", "pastel"]
    music_preferences = Column(JSON, nullable=True)  # ["jazz", "pop"]
    personality_tags  = Column(JSON, nullable=True)  # ["adventurous", "cozy"]

    # ── Confirmation state ───────────────────────────────────────────────────
    # A persona is "confirmed" once the customer explicitly says "yes, use this
    # profile" during a planning session.  The planning router checks this flag
    # so it can prioritise confirmed personas over unconfirmed ones.
    is_confirmed  = Column(Boolean, default=False, nullable=False)
    confirmed_at  = Column(DateTime(timezone=True), nullable=True)

    # ── Timestamps ───────────────────────────────────────────────────────────
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )