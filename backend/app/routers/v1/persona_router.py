from __future__ import annotations
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.customer import Customer
from app.schemas.persona_schema import PersonaCreate, PersonaResponse, PersonaListResponse
from app.services.persona_service import persona_service

router = APIRouter(prefix="/personas", tags=["Personas"])

@router.post(
    "/",
    response_model=PersonaResponse,
    status_code=status.HTTP_201_CREATED
)
def create_persona(
    payload: PersonaCreate,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    return persona_service.create_persona(db, str(current_customer.customer_id), payload)

@router.get(
    "/",
    response_model=PersonaListResponse
)
def list_personas(
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    personas = persona_service.get_personas(db, str(current_customer.customer_id))
    return PersonaListResponse(personas=personas, total=len(personas))

@router.get(
    "/{persona_id}",
    response_model=PersonaResponse
)
def get_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    return persona_service.get_persona(db, str(current_customer.customer_id), persona_id)

@router.delete("/{persona_id}")
def delete_persona(
    persona_id: str,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer)
):
    return persona_service.delete_persona(db, str(current_customer.customer_id), persona_id)