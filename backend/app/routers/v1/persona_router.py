"""
app/routers/v1/persona_router.py

Full REST API for Persona management.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.customer import Customer
from app.core.dependencies import get_current_customer
from app.services.persona_service import persona_service

# Import the Bouncer
from app.schemas.persona_schema import PersonaCreate, PersonaUpdate, PersonaResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/personas", tags=["Personas"])

# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/confirmed", response_model=List[PersonaResponse])
def list_confirmed_personas(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Return only confirmed personas for the current customer."""
    # We return the RAW SQLAlchemy model list. FastAPI + Pydantic formats it automatically.
    return persona_service.get_confirmed_personas(db, str(current_customer.customer_id))


@router.get("/", response_model=List[PersonaResponse])
def list_personas(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """List all personas for the authenticated customer, confirmed first."""
    return persona_service.get_personas(db, str(current_customer.customer_id))


@router.post("/", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
def create_persona(
    payload: PersonaCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Create a new recipient profile (persona)."""
    return persona_service.create_persona(
        db,
        customer_id=str(current_customer.customer_id),
        data=payload.model_dump(exclude_none=False), # exclude_none=False keeps explicit nulls
    )


@router.get("/{persona_id}", response_model=PersonaResponse)
def get_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Fetch a single persona by its public ID (PER-xxx)."""
    persona = persona_service.get_persona_by_id(db, persona_id, str(current_customer.customer_id))
    if not persona:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Persona not found")
    return persona


@router.put("/{persona_id}", response_model=PersonaResponse)
def update_persona(
    persona_id: str,
    payload: PersonaUpdate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Partial update — only fields included in the body are changed. (OCA-250)"""
    return persona_service.update_persona(
        db,
        persona_id=persona_id,
        customer_id=str(current_customer.customer_id),
        data=payload.model_dump(exclude_unset=True), # exclude_unset=True ignores missing fields
    )


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Delete a persona (PDPA-compliant data erasure)."""
    persona_service.delete_persona(db, persona_id, str(current_customer.customer_id))
    return None


@router.post("/{persona_id}/confirm", response_model=PersonaResponse)
def confirm_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Confirm a persona for the current planning session."""
    return persona_service.confirm_persona(db, persona_id, str(current_customer.customer_id))


@router.delete("/{persona_id}/confirm", response_model=PersonaResponse)
def unconfirm_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    """Remove confirmed state."""
    return persona_service.unconfirm_persona(db, persona_id, str(current_customer.customer_id))