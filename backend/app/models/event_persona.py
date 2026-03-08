from __future__ import annotations

from sqlalchemy import Column, ForeignKey, String

from app.core.database import Base


class EventPersona(Base):
    __tablename__ = "event_personas"

    event_id = Column(String, ForeignKey("events.event_id"), primary_key=True)
    persona_id = Column(String, ForeignKey("personas.persona_id"), primary_key=True)

