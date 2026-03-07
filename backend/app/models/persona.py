from __future__ import annotations
from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base

class Persona(Base):
    __tablename__ = "personas"

    id = Column(Integer, primary_key=True, index=True)
    persona_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("PER"))

    customer_id = Column(String, index=True, nullable=False)
    name = Column(String, nullable=False)
    relationship = Column(String, nullable=True)        # e.g. girlfriend, mom, colleague
    birthday = Column(DateTime(timezone=True), nullable=True)
    personality = Column(Text, nullable=True)           # e.g. "introverted, loves cozy things"
    preferences_json = Column(JSON, nullable=True)      # hobbies, interests list

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)