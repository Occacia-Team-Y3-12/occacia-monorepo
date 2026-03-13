from __future__ import annotations

from sqlalchemy import JSON, Boolean, Column, DateTime, Integer, String, Text

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(
        String,
        unique=True,
        index=True,
        default=lambda: generate_prefixed_id("PER"),
    )

    customer_id = Column(String, index=True, nullable=False)

    name = Column(String, nullable=False)
    relationship = Column(String, nullable=True)
    birthday = Column(DateTime(timezone=True), nullable=True)
    personality = Column(Text, nullable=True)

    # Legacy preferences retained for backward compatibility
    preferences_json = Column(JSON, nullable=True)

    # Structured preference fields
    food_preferences = Column(JSON, nullable=True)
    color_preferences = Column(JSON, nullable=True)
    music_preferences = Column(JSON, nullable=True)
    personality_tags = Column(JSON, nullable=True)

    # Confirmation state for planning sessions
    is_confirmed = Column(Boolean, default=False, nullable=False)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(
        DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False
    )