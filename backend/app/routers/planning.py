from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.plan_schema import PlanRequest, PlanResponse, VenueDisplay
from app.services.ai_service import ai_service
from app.services.vendor_service import vendor_service

router = APIRouter(prefix="/planning", tags=["Planning"])

@router.post("/generate", response_model=PlanResponse)
async def generate_plan(request: PlanRequest, db: Session = Depends(get_db)):
    print(f"📥 Processing Query: {request.user_query}")

    # PHASE 1: AI Understanding
    try:
        ai_analysis = await ai_service.generate_date_plan(request.user_query)
    except Exception as e:
        print(f"⚠️ AI Error: {e}")
        ai_analysis = {"intent": "chat", "reasoning": "AI error occurred. Using fallback."}

    # PHASE 2: Database Matching
    matches = vendor_service.find_perfect_matches(db, ai_analysis)

    # Only search the DB if the intent is "planning"
    if ai_analysis.get("intent") == "planning":
         matches = vendor_service.find_perfect_matches(db, ai_analysis)
    else:
         matches = [] # Don't show venues for simple chat/gift questions

    # PHASE 3: Response
    # ✅ THE FIX: using 'or []' ensures that if the value is None, it becomes an empty list.
    return PlanResponse(
        intent=ai_analysis.get("intent", "planning"),
        reasoning=ai_analysis.get("reasoning", ""),
        personality_profile=ai_analysis.get("personality_profile"),
        chat_response=ai_analysis.get("chat_response"),
        gift_suggestion=ai_analysis.get("gift_suggestion"),
        event_type=ai_analysis.get("event_type"),
        location=ai_analysis.get("location", "Any"),
        budget_per_head=float(ai_analysis.get("budget_per_head") or 0),  # Handle None for numbers too
        guest_count=int(ai_analysis.get("guest_count") or 0),            # Handle None for numbers too
        venue_tags=ai_analysis.get("venue_tags") or [],                  # 🛑 FIXED THE CRASH HERE
        missing_info=ai_analysis.get("missing_info") or [],              # Safety for this list too
        matched_venues=[VenueDisplay.model_validate(m) for m in matches] # Ensure objects are converted
    )