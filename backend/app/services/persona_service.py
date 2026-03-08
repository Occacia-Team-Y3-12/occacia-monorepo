from __future__ import annotations
import logging
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.persona import Persona
from app.schemas.persona_schema import PersonaCreate

logger = logging.getLogger(__name__)

class PersonaService:

    def create_persona(self, db: Session, customer_id: str, payload: PersonaCreate) -> Persona:
        persona = Persona(
            customer_id=customer_id,
            name=payload.name,
            relationship=payload.relationship,
            birthday=payload.birthday,
            personality=payload.personality,
            preferences_json=payload.preferences_json,
        )
        db.add(persona)
        db.commit()
        db.refresh(persona)
        logger.info(f"✅ Persona created: {persona.persona_id} for customer {customer_id}")
        return persona

    def get_personas(self, db: Session, customer_id: str) -> list[Persona]:
        return db.query(Persona).filter(Persona.customer_id == customer_id).all()

    def get_persona(self, db: Session, customer_id: str, persona_id: str) -> Persona:
        persona = db.query(Persona).filter(
            Persona.persona_id == persona_id,
            Persona.customer_id == customer_id
        ).first()
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found.")
        return persona

    def delete_persona(self, db: Session, customer_id: str, persona_id: str) -> dict:
        persona = self.get_persona(db, customer_id, persona_id)
        db.delete(persona)
        db.commit()
        logger.info(f"🗑️ Persona deleted: {persona_id}")
        return {"message": f"Persona '{persona.name}' deleted successfully."}

    def build_persona_context(self, personas: list[Persona]) -> str:
        """Formats all personas into a string for injection into the AI prompt."""
        if not personas:
            return ""
        lines = ["CUSTOMER'S SAVED GIFT PROFILES:"]
        for p in personas:
            parts = [f"- {p.name}"]
            if p.relationship:
                parts.append(f"({p.relationship})")
            if p.birthday:
                parts.append(f"Birthday: {p.birthday.strftime('%B %d')}")
            if p.personality:
                parts.append(f"Personality: {p.personality}")
            if p.preferences_json:
                interests = p.preferences_json
                if isinstance(interests, list):
                    parts.append(f"Interests: {', '.join(interests)}")
                elif isinstance(interests, dict):
                    parts.append(f"Interests: {interests}")
            lines.append(" | ".join(parts))
        return "\n".join(lines)

persona_service = PersonaService()