import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.plan_schema import PlanRequest, PlanResponse, VenueDisplay
from app.services.ai_service import ai_service
from app.services.vendor_service import vendor_service
from app.services.chat_service import chat_service

# 1. SETUP LOGGING
# Essential for tracing how context flows between users and the AI.
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/planning", tags=["Planning"])

@router.post("/generate", 
             response_model=PlanResponse, 
             response_model_exclude_none=True)
async def generate_plan(request: PlanRequest, db: Session = Depends(get_db)):
    """
    Main entry point for the AI Chatbot. 
    Handles multi-user session management by injecting past history 
    into the current AI prompt.
    """
    session_id = request.session_id
    user_query = request.user_query
    
    logger.info(f"📥 Session {session_id} | New Query: {user_query}")

    # PHASE 1: Fetch History (Context Retrieval)
    # We pull the last 5 turns to keep the prompt size manageable while 
    # ensuring the AI 'remembers' the girlfriend's preferences, budget, etc.
    history = chat_service.get_session_history(db, session_id, limit=5)
    
    # PHASE 2: AI Understanding with Context
    try:
        # We pass the history list to the AI service for 'Context Injection'
        ai_analysis = await ai_service.generate_date_plan(user_query, history=history)
        intent = ai_analysis.get("intent", "chat")
    except Exception as e:
        logger.error(f"⚠️ AI Critical Error for Session {session_id}: {e}")
        return PlanResponse(intent="chat", chat_response="My memory is a bit foggy right now. Could you repeat that?")

    # PHASE 3: Database Matching (Smart Filtering)
    # Only triggered if the AI decides we have enough info to search for venues.
    matches = []
    if intent == "planning":
        logger.info(f"🔎 Planning Intent: Searching Postgres for session {session_id}...")
        matches = vendor_service.find_perfect_matches(db, ai_analysis)

    # PHASE 4: Persist the Conversation (The Memory Save)
    # We save both parts of the turn to the DB so the NEXT request has context.
    chat_service.save_message(
        db, 
        session_id=session_id, 
        user_msg=user_query, 
        ai_msg=ai_analysis.get("chat_response") or ai_analysis.get("reasoning")
    )

    # PHASE 5: Tailored Response Construction
    # CASE A: Standard Chat
    if intent == "chat":
        return PlanResponse(
            intent="chat",
            chat_response=ai_analysis.get("chat_response"),
            missing_info=ai_analysis.get("missing_info") if ai_analysis.get("missing_info") else None
        )

    # CASE B: Structured Planning
    # Merge Reasoning and Personality Profile into one block for a clean UI.
    merged_text = (
        f"Analysis: {ai_analysis.get('reasoning', 'Thinking...')}\n\n"
        f"Profile: {ai_analysis.get('personality_profile', 'Guest')}"
    )

    return PlanResponse(
        intent="planning",
        reasoning=merged_text,
        gift_suggestion=ai_analysis.get("gift_suggestion"),
        event_type=ai_analysis.get("event_type"),
        location=ai_analysis.get("location", "Any"),
        budget_per_head=float(ai_analysis.get("budget_per_head") or 0),
        guest_count=int(ai_analysis.get("guest_count") or 0),
        venue_tags=ai_analysis.get("venue_tags") or [],
        missing_info=ai_analysis.get("missing_info") if ai_analysis.get("missing_info") else None,
        matched_venues=[VenueDisplay.model_validate(m) for m in matches]
    )