"""
app/routers/v1/persona_router.py

Full REST API for Persona management.

Endpoints
---------
GET    /api/v1/personas/                    — list all my personas
POST   /api/v1/personas/                    — create persona
GET    /api/v1/personas/{persona_id}        — get single persona
PUT    /api/v1/personas/{persona_id}        — full/partial update
DELETE /api/v1/personas/{persona_id}        — delete
POST   /api/v1/personas/{persona_id}/confirm    — mark as confirmed
DELETE /api/v1/personas/{persona_id}/confirm    — unconfirm
GET    /api/v1/personas/confirmed           — list only confirmed personas

All routes require customer JWT auth.
"""
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.routers.v1.auth_router import get_current_customer
from app.services.persona_service import persona_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/personas", tags=["Personas"])


# ── Pydantic schemas ──────────────────────────────────────────────────────────

class PersonaCreate(BaseModel):
    name:              str
    relationship:      Optional[str]        = None
    birthday:          Optional[str]        = None   # ISO date string
    personality:       Optional[str]        = None
    preferences_json:  Optional[List[str]]  = None   # legacy hobbies
    food_preferences:  Optional[List[str]]  = None
    color_preferences: Optional[List[str]]  = None
    music_preferences: Optional[List[str]]  = None
    personality_tags:  Optional[List[str]]  = None

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("name must not be empty")
        return v.strip()


class PersonaUpdate(BaseModel):
    """All fields optional — partial update."""
    name:              Optional[str]        = None
    relationship:      Optional[str]        = None
    birthday:          Optional[str]        = None
    personality:       Optional[str]        = None
    preferences_json:  Optional[List[str]]  = None
    food_preferences:  Optional[List[str]]  = None
    color_preferences: Optional[List[str]]  = None
    music_preferences: Optional[List[str]]  = None
    personality_tags:  Optional[List[str]]  = None


class PersonaResponse(BaseModel):
    id:               int
    persona_id:       str
    customer_id:      str
    name:             str
    relationship:     Optional[str]   = None
    birthday:         Optional[str]   = None
    personality:      Optional[str]   = None
    preferences_json: List[str]       = []
    food_preferences:  List[str]      = []
    color_preferences: List[str]      = []
    music_preferences: List[str]      = []
    personality_tags:  List[str]      = []
    is_confirmed:     bool            = False
    confirmed_at:     Optional[str]   = None
    created_at:       Optional[str]   = None
    updated_at:       Optional[str]   = None

    model_config = ConfigDict(from_attributes=True)


# ── Helper ────────────────────────────────────────────────────────────────────

def _resp(persona) -> PersonaResponse:
    d = persona_service.to_dict(persona)
    return PersonaResponse(**d)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/confirmed", response_model=List[PersonaResponse])
def list_confirmed_personas(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Return only confirmed personas for the current customer."""
    personas = persona_service.get_confirmed_personas(
        db, str(current_customer.customer_id)
    )
    return [_resp(p) for p in personas]


@router.get("/", response_model=List[PersonaResponse])
def list_personas(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """List all personas for the authenticated customer, confirmed first."""
    personas = persona_service.get_personas(
        db, str(current_customer.customer_id)
    )
    return [_resp(p) for p in personas]


@router.post("/", response_model=PersonaResponse, status_code=201)
def create_persona(
    payload: PersonaCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Create a new recipient profile (persona)."""
    persona = persona_service.create_persona(
        db,
        customer_id=str(current_customer.customer_id),
        data=payload.model_dump(exclude_none=False),
    )
    return _resp(persona)


@router.get("/{persona_id}", response_model=PersonaResponse)
def get_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Fetch a single persona by its public ID (PER-xxx)."""
    persona = persona_service.get_persona_by_id(
        db, persona_id, str(current_customer.customer_id)
    )
    if not persona:
        raise HTTPException(status_code=404, detail="Persona not found")
    return _resp(persona)


@router.put("/{persona_id}", response_model=PersonaResponse)
def update_persona(
    persona_id: str,
    payload: PersonaUpdate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Partial update — only fields included in the body are changed. (OCA-250)"""
    persona = persona_service.update_persona(
        db,
        persona_id=persona_id,
        customer_id=str(current_customer.customer_id),
        data=payload.model_dump(exclude_unset=True),
    )
    return _resp(persona)


@router.delete("/{persona_id}", status_code=204)
def delete_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Delete a persona (PDPA-compliant data erasure)."""
    persona_service.delete_persona(
        db, persona_id, str(current_customer.customer_id)
    )
    return None


@router.post("/{persona_id}/confirm", response_model=PersonaResponse)
def confirm_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Confirm a persona — the customer has explicitly chosen to use this profile
    for the current planning session.  Sets is_confirmed=True.
    """
    persona = persona_service.confirm_persona(
        db, persona_id, str(current_customer.customer_id)
    )
    return _resp(persona)


@router.delete("/{persona_id}/confirm", response_model=PersonaResponse)
def unconfirm_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """
    Remove confirmed state — customer decided not to use this profile.
    """
    persona = persona_service.unconfirm_persona(
        db, persona_id, str(current_customer.customer_id)
    )
    return _resp(persona)