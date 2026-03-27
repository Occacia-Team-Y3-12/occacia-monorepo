"""
app/services/persona_service.py
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.persona import Persona

logger = logging.getLogger(__name__)


class PersonaService:

    def get_personas(self, db: Session, customer_id: str) -> List[Persona]:
        return (
            db.query(Persona)
            .filter(Persona.customer_id == str(customer_id))
            .order_by(Persona.is_confirmed.desc(), Persona.created_at.asc())
            .all()
        )

    def get_persona_by_id(self, db: Session, persona_id: str, customer_id: str) -> Optional[Persona]:
        return (
            db.query(Persona)
            .filter(
                Persona.persona_id == persona_id,
                Persona.customer_id == str(customer_id),
            )
            .first()
        )

    def get_confirmed_personas(self, db: Session, customer_id: str) -> List[Persona]:
        return (
            db.query(Persona)
            .filter(
                Persona.customer_id == str(customer_id),
                Persona.is_confirmed == True,
            )
            .order_by(Persona.confirmed_at.asc())
            .all()
        )

    def create_persona(self, db: Session, customer_id: str, data: dict) -> Persona:
        persona = Persona(
            customer_id=str(customer_id),
            **data
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        logger.info(f"Persona created: {persona.persona_id} for customer {customer_id}")
        return persona

    def update_persona(self, db: Session, persona_id: str, customer_id: str, data: dict) -> Persona:
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
        for key, value in data.items():
            setattr(persona, key, value)
        db.commit()
        db.refresh(persona)
        logger.info(f"Persona updated: {persona_id}")
        return persona

    def delete_persona(self, db: Session, persona_id: str, customer_id: str) -> bool:
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
        db.delete(persona)
        db.commit()
        logger.info(f"Persona deleted: {persona_id}")
        return True

    def confirm_persona(self, db: Session, persona_id: str, customer_id: str) -> Persona:
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
        persona.is_confirmed = True
        persona.confirmed_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(persona)
        return persona

    def unconfirm_persona(self, db: Session, persona_id: str, customer_id: str) -> Persona:
        persona = self.get_persona_by_id(db, persona_id, customer_id)
        if not persona:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
        persona.is_confirmed = False
        persona.confirmed_at = None
        db.commit()
        db.refresh(persona)
        return persona

    def is_persona_complete(self, persona: Persona) -> bool:
        """
        A persona is considered 'complete' when it has enough info to
        generate meaningful event recommendations.
        Required: name, relationship
        Strongly desired: age OR birthday, gender, at least one preference.
        """
        if not persona.name or not persona.relationship:
            return False
        has_age = bool(getattr(persona, "age", None) or getattr(persona, "birthday", None))
        has_prefs = bool(
            (getattr(persona, "food_preferences", None) or [])
            or (getattr(persona, "music_preferences", None) or [])
            or (getattr(persona, "color_preferences", None) or [])
            or (getattr(persona, "personality_tags", None) or [])
        )
        return has_age and has_prefs

    def get_missing_persona_fields(self, persona: Persona) -> list[str]:
        """Return list of missing important fields for a persona."""
        missing = []
        if not getattr(persona, "name", None):
            missing.append("name")
        if not getattr(persona, "relationship", None):
            missing.append("relationship")
        if not getattr(persona, "age", None) and not getattr(persona, "birthday", None):
            missing.append("age or birthday")
        if not getattr(persona, "gender", None):
            missing.append("gender")
        if not (getattr(persona, "personality_tags", None) or []):
            missing.append("personality (introverted/extroverted, interests)")
        if not (getattr(persona, "food_preferences", None) or []):
            missing.append("food preferences")
        if not (getattr(persona, "music_preferences", None) or []):
            missing.append("music preferences")
        if not (getattr(persona, "color_preferences", None) or []):
            missing.append("favorite colors")
        return missing


persona_service = PersonaService()