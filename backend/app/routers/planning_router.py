import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.plan_schema import PlanRequest, PlanResponse, VenueDisplay
from app.services.ai_service import ai_service
from app.services.vendor_service import vendor_service

# 1. SETUP LOGGING
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/planning", tags=["Planning"])

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanRequest, db: Session = Depends(get_db)):
    logger.info(f"📥 Processing Query: {request.user_query}")

    # PHASE 1: AI Understanding
    try:
        ai_analysis = await ai_service.generate_date_plan(request.user_query)
        logger.info(f"🧠 AI Analysis complete. Intent: {ai_analysis.get('intent')}")
    except Exception as e:
        logger.error(f"⚠️ AI Critical Error: {e}")
        ai_analysis = {"intent": "chat", "reasoning": "AI error occurred. Using fallback."}

    # PHASE 2: Database Matching (Smart Filter)
    # Fixed logic: Only define matches ONCE
    matches = []
    
    if ai_analysis.get("intent") == "planning":
         logger.info("🔎 Planning Intent detected. Searching Database...")
         matches = vendor_service.find_perfect_matches(db, ai_analysis)
         logger.info(f"✅ Found {len(matches)} venues.")
    else:
         logger.info("💬 Chat Intent detected. Skipping Database search.")

    # PHASE 3: Response
    return PlanResponse(
        intent=ai_analysis.get("intent", "planning"),
        reasoning=ai_analysis.get("reasoning", ""),
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