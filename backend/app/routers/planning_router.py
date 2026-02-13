import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.plan_schema import PlanRequest, PlanResponse, VenueDisplay
from app.services.ai_service import ai_service
from app.services.vendor_service import vendor_service
from app.services.chat_service import chat_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/planning", tags=["Planning"])

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanRequest, db: Session = Depends(get_db)):
    # 🛡️ Safe Extraction: Fields now exist in PlanRequest
    session_id = request.session_id
    user_query = request.user_query
    
    logger.info(f"📥 Session {session_id} | New Query: {user_query}")

    # PHASE 1: Fetch History
    history = chat_service.get_session_history(db, session_id, limit=5)
    
    # PHASE 2: AI Execution
    try:
        ai_analysis = await ai_service.generate_date_plan(user_query, history=history)
        intent = ai_analysis.get("intent", "chat")
    except Exception as e:
        logger.error(f"⚠️ AI Critical Error for Session {session_id}: {e}")
        return PlanResponse(intent="chat", chat_response="My memory is foggy. Try again?")

    # PHASE 3: Database Matching
    matches = []
    if intent == "planning":
        logger.info(f"🔎 Searching Postgres for session {session_id}...")
        matches = vendor_service.find_perfect_matches(db, ai_analysis)

    # PHASE 4: Memory Persistence
    chat_service.save_message(
        db, 
        session_id=session_id, 
        user_msg=user_query, 
        ai_msg=ai_analysis.get("chat_response") or ai_analysis.get("reasoning")
    )

    # PHASE 5: Standardized Response Construction
    return PlanResponse(
        intent=intent,
        reasoning=ai_analysis.get("reasoning"),
        personality_profile=ai_analysis.get("personality_profile"),
        chat_response=ai_analysis.get("chat_response"),
        gift_suggestion=ai_analysis.get("gift_suggestion"),
        event_type=ai_analysis.get("event_type"),
        location=ai_analysis.get("location", "Any"),
        budget_per_head=float(ai_analysis.get("budget_per_head") or 0),
        guest_count=int(ai_analysis.get("guest_count") or 0),
        venue_tags=ai_analysis.get("venue_tags") or [],
        missing_info=ai_analysis.get("missing_info") or [],
        matched_venues=[VenueDisplay.model_validate(m) for m in matches]
    )