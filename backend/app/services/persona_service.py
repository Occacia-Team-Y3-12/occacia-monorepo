from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.persona import Persona

logger = logging.getLogger(__name__)


# --- Data Helpers ---

def _to_list(val) -> list:
    """Coerce JSON/None/string to a plain Python list."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    if isinstance(val, str):
        return [s.strip() for s in val.split(",") if s.strip()]
    return list(val)


def _persona_to_dict(p: Persona) -> dict:
    return {
        "id":               p.id,
        "persona_id":       p.persona_id,
        "customer_id":      p.customer_id,
        "name":             p.name,
        "relationship":     p.relationship,
        "birthday":         p.birthday.isoformat() if p.birthday else None,
        "personality":      p.personality,
        "preferences_json": _to_list(p.preferences_json),
        "food_preferences":  _to_list(p.food_preferences),
        "color_preferences": _to_list(p.color_preferences),
        "music_preferences": _to_list(p.music_preferences),
        "personality_tags":  _to_list(p.personality_tags),
        "is_confirmed":     p.is_confirmed,
        "confirmed_at":     p.confirmed_at.isoformat() if p.confirmed_at else None,
        "created_at":       p.created_at.isoformat() if p.created_at else None,
        "updated_at":       p.updated_at.isoformat() if p.updated_at else None,
    }


class PersonaService:

    # --- Read ---

    def get_personas(self, db: Session, customer_id: str) -> List[Persona]:
        """Return all personas for a customer, sorting confirmed ones first."""
        rows = (
            db.query(Persona)
            .filter(Persona.customer_id == str(customer_id))
            .order_by(Persona.is_confirmed.desc(), Persona.created_at.asc())
            .all()
        )
        logger.debug("get_personas: customer=%s -> %d rows", customer_id, len(rows))
        return rows

    def get_persona_by_id(self, db: Session, persona_id: str, customer_id: str) -> Optional[Persona]:
        return (
            db.query(Persona)
            .filter(
                Persona.persona_id == persona_id,
                Persona.customer_id == str(customer_id),
            )
            .first()
        )

    def get_persona_by_internal_id(self, db: Session, pk: int, customer_id: str) -> Optional[Persona]:
        return (
            db.query(Persona)
            .filter(Persona.id == pk, Persona.customer_id == str(customer_id))
            .first()
        )

    # --- Create ---

    def create_persona(self, db: Session, customer_id: str, data: dict) -> Persona:
        if not data.get("name"):
            raise HTTPException(status_code=422, detail="name is required")

        birthday = None
        raw_bday = data.get("birthday")
        if raw_bday:
            try:
                birthday = datetime.fromisoformat(str(raw_bday).replace("Z", "+00:00"))
            except Exception:
                raise HTTPException(status_code=422, detail=f"Invalid birthday format: {raw_bday!r}")

        persona = Persona(
            customer_id       = str(customer_id),
            name              = data["name"].strip(),
            relationship      = data.get("relationship"),
            birthday          = birthday,
            personality       = data.get("personality"),
            preferences_json  = _to_list(data.get("preferences_json")),
            food_preferences  = _to_list(data.get("food_preferences")),
            color_preferences = _to_list(data.get("color_preferences")),
            music_preferences = _to_list(data.get("music_preferences")),
            personality_tags  = _to_list(data.get("personality_tags")),
            is_confirmed      = False,
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        logger.info("Persona created: %s for customer %s", persona.persona_id, customer_id)
        return persona

    # --- Update ---

    def update_persona(self, db: Session, persona_id: str, customer_id: str, data: dict) -> Persona:
        """Partial update — only fields present in `data` are modified."""
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        updatable = [
            "name", "relationship", "personality",
            "preferences_json",
            "food_preferences", "color_preferences",
            "music_preferences", "personality_tags",
        ]
        
        for field in updatable:
            if field in data:
                val = data[field]
                if field in ("preferences_json", "food_preferences",
                             "color_preferences", "music_preferences",
                             "personality_tags"):
                    val = _to_list(val)
                setattr(persona, field, val)

        if "birthday" in data:
            if data["birthday"] is not None:
                try:
                    persona.birthday = datetime.fromisoformat(str(data["birthday"]).replace("Z", "+00:00"))
                except Exception:
                    raise HTTPException(status_code=422, detail=f"Invalid birthday format: {data['birthday']!r}")
            else:
                persona.birthday = None

        db.commit()
        db.refresh(persona)
        logger.info("Persona updated: %s", persona_id)
        return persona

    # --- Delete ---

    def delete_persona(self, db: Session, persona_id: str, customer_id: str) -> bool:
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        db.delete(persona)
        db.commit()
        logger.info("Persona deleted: %s", persona_id)
        return True

    # --- Confirmation ---

    def confirm_persona(self, db: Session, persona_id: str, customer_id: str) -> Persona:
        """Marks a persona as confirmed for use in a planning session."""
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        persona.is_confirmed = True
        persona.confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(persona)
        logger.info("Persona confirmed: %s for customer %s", persona_id, customer_id)
        return persona

    def unconfirm_persona(self, db: Session, persona_id: str, customer_id: str) -> Persona:
        """Removes the confirmed state from a persona."""
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")

        persona.is_confirmed = False
        persona.confirmed_at = None
        db.commit()
        db.refresh(persona)
        logger.info("Persona unconfirmed: %s", persona_id)
        return persona

    def get_confirmed_personas(self, db: Session, customer_id: str) -> List[Persona]:
        """Returns only confirmed personas for the AI context."""
        return (
            db.query(Persona)
            .filter(
                Persona.customer_id == str(customer_id),
                Persona.is_confirmed == True,
            )
            .order_by(Persona.confirmed_at.asc())
            .all()
        )

    # --- Serialization ---

    def to_dict(self, persona: Persona) -> dict:
        return _persona_to_dict(persona)


persona_service = PersonaService()