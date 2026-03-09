"""
app/routers/v1/customers_router.py

Routes per OpenAPI contract:
  GET /customers/me   — get current customer profile
  PUT /customers/me   — update current customer profile
"""
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.routers.v1.auth_router import get_current_customer

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/customers", tags=["Customer"])


# ── GET /customers/me ─────────────────────────────────────────────────

@router.get("/me")
def get_customer_me(current_customer=Depends(get_current_customer)):
    """Get current customer profile. Spec: GET /customers/me"""
    return {
        "customerId": getattr(current_customer, "customer_id", None),
        "email":      current_customer.email,
        "fullName":   current_customer.full_name,
        "phone":      getattr(current_customer, "phone", None),
        "locale":     getattr(current_customer, "locale", None),
        "status":     getattr(current_customer, "status", None),
    }


# ── PUT /customers/me ─────────────────────────────────────────────────

@router.put("/me")
def update_customer_me(
    body: dict,
    db: Session = Depends(get_db),
    current_customer=Depends(get_current_customer),
):
    """Update current customer profile. Spec: PUT /customers/me"""
    if body.get("fullName"):
        current_customer.full_name = body["fullName"]
    if "phone" in body and hasattr(current_customer, "phone"):
        current_customer.phone = body.get("phone")
    if "locale" in body and hasattr(current_customer, "locale"):
        current_customer.locale = body.get("locale")
    db.commit()
    db.refresh(current_customer)
    return {
        "customerId": getattr(current_customer, "customer_id", None),
        "email":      current_customer.email,
        "fullName":   current_customer.full_name,
        "phone":      getattr(current_customer, "phone", None),
        "locale":     getattr(current_customer, "locale", None),
        "status":     getattr(current_customer, "status", None),
    }