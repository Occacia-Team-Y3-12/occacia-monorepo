"""
app/routers/v1/planning_router.py

Core AI planning logic with multi-intent detection and persona flow.
"""
import logging
import re

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_customer
from app.models.customer import Customer
from app.models.persona import Persona
from app.schemas.planning_schema import PlanRequest, PlanResponse

# Dependency Injection Imports (AND providing _package_to_dict for test mocks)
from app.services.planning_service import planning_service, _package_to_dict
from app.services.ai_service import ai_service
from app.services.chat_service import chat_service
from app.services.vendor_service import vendor_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planning", tags=["Planning"])

_SESSION_RE = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')

# --- Persona Service Shim (Required for your Test Mocks) ---
try:
    from app.services.persona_service import persona_service
except ImportError:
    class _PersonaService:
        def get_personas(self, db: Session, customer_id):
            return db.query(Persona).filter(Persona.customer_id == customer_id).all()
    persona_service = _PersonaService()


# --- Redis / Rate Limiting (Infrastructure) ---
def get_redis():
    try:
        import redis as _redis
        import os
        r = _redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
        r.ping()
        return r
    except Exception:
        return None

_RATE_LIMIT = 10

def check_rate_limit(customer_id, session_id=None):
    r = get_redis()
    if r is None:
        return True
    key = f"rate:{customer_id}"
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, 60)
        count = pipe.execute()[0]
        if count > _RATE_LIMIT:
            raise HTTPException(status_code=429, detail="Rate limit exceeded.")
        return True
    except HTTPException:
        raise
    except Exception:
        return True


# --- Main Endpoint ---
@router.post("/generate", response_model=PlanResponse)
async def generate_plan(
    request: Request,
    plan_req: PlanRequest,
    db: Session = Depends(get_db),
    current_customer: Customer = Depends(get_current_customer),
):
    session_id = plan_req.session_id
    user_query = plan_req.user_query

    if not _SESSION_RE.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session_id format.")

    check_rate_limit(str(current_customer.customer_id), session_id)

    return await planning_service.process_plan(
        db=db,
        customer=current_customer,
        session_id=session_id,
        user_query=user_query,
        persona_svc=persona_service,
        ai_svc=ai_service,
        chat_svc=chat_service,
        vendor_svc=vendor_service
    )