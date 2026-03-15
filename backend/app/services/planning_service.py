"""
app/services/planning_service.py
"""
import logging
import re
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.planning_schema import PlanResponse

logger = logging.getLogger(__name__)

_BUDGET_RE = re.compile(
    r'(?:budget|spend|spending|cost|costs|afford|price)[^\d]{0,10}(\d[\d,]*)',
    re.IGNORECASE,
)
_GUEST_RE = re.compile(r'(\d+)\s*(?:people|guests?|persons?|pax)', re.IGNORECASE)
_DATE_RE  = re.compile(r'(\d{4}-\d{2}-\d{2})')

def _extract_budget(text: str) -> Optional[float]:
    m = _BUDGET_RE.search(text)
    if m:
        try: return float(m.group(1).replace(",", ""))
        except ValueError: pass
    return None

def _extract_guests(text: str) -> Optional[int]:
    m = _GUEST_RE.search(text)
    if m:
        try: return int(m.group(1))
        except ValueError: pass
    return None

def _extract_date(text: str) -> Optional[str]:
    m = _DATE_RE.search(text)
    if m:
        try:
            date.fromisoformat(m.group(1))
            return m.group(1)
        except ValueError: pass
    return None

def _package_to_dict(pkg, requested_tags: list = None) -> dict:
    state = getattr(pkg, "__dict__", None) or {}
    vendor_name = None
    try:
        vendor_loaded = "vendor" in state
        if vendor_loaded:
            v = state["vendor"]
            if v is not None:
                vendor_name = (getattr(v, "display_name", None) or getattr(v, "business_name", None))
        elif hasattr(pkg, "vendor") and not hasattr(type(pkg), "__tablename__"):
            v = pkg.vendor
            if v is not None:
                vendor_name = (getattr(v, "display_name", None) or getattr(v, "business_name", None))
    except Exception:
        vendor_name = None

    pkg_tags = pkg.tags or []
    if isinstance(pkg_tags, str):
        import json as _json
        try: pkg_tags = _json.loads(pkg_tags)
        except Exception: pkg_tags = []

    if requested_tags:
        matched   = len(set(requested_tags) & set(pkg_tags))
        total     = len(set(requested_tags))
        match_score       = matched
        match_score_max   = total
        match_score_label = f"{matched} of {total} tags matched"
    else:
        match_score       = None
        match_score_max   = None
        match_score_label = None

    return {
        "id":                pkg.id,
        "name":              pkg.name,
        "description":       pkg.description,
        "price_per_head":    getattr(pkg, "price_per_head", None),
        "tags":              pkg_tags,
        "location":          getattr(pkg, "location_coverage", None),
        "vendor_name":       vendor_name,
        "match_score":       match_score,
        "match_score_max":   match_score_max,
        "match_score_label": match_score_label,
    }


class PlanningService:
    async def process_plan(
        self,
        db: Session,
        customer: Customer,
        session_id: str,
        user_query: str,
        persona_svc,
        ai_svc,
        chat_svc,
        vendor_svc
    ) -> PlanResponse:
        
        history = chat_svc.get_session_history(db, session_id)
        prev_missing = chat_svc.get_last_missing_info(db, session_id)

        all_text = user_query + " " + " ".join((m.user_message or "") for m in history[-5:])
        extracted_budget   = _extract_budget(all_text)
        extracted_guests   = _extract_guests(all_text)
        extracted_location = vendor_svc.extract_location_from_text(all_text)
        extracted_date     = _extract_date(all_text)

        active_missing = list(prev_missing or [])
        personas = persona_svc.get_personas(db, str(customer.customer_id))
        available_tags = vendor_svc.get_all_tags(db)
        availability_block = vendor_svc.get_availability_block(db, tags=available_tags[:20]) if available_tags else ""

        try:
            fact_parts = []
            if extracted_budget: fact_parts.append(f"budget={extracted_budget}")
            if extracted_guests: fact_parts.append(f"guests={extracted_guests}")
            if extracted_location: fact_parts.append(f"location={extracted_location}")
            if extracted_date: fact_parts.append(f"date={extracted_date}")

            enriched_query = user_query
            if fact_parts:
                enriched_query += f"\n[SYSTEM EXTRACTED FACTS: {', '.join(fact_parts)}]"
            if availability_block:
                enriched_query += availability_block

            ai_result = await ai_svc.generate_date_plan(
                raw_query      = enriched_query,
                history        = history,
                personas       = personas if personas else None,
                available_tags = available_tags if available_tags else None,
                missing_info   = active_missing if active_missing else None,
            )
        except Exception as exc:
            logger.error(f"AI call failed: {exc}")
            ai_result = {
                "intent": "chat",
                "chat_response": "Things are a bit foggy on our end right now. Could you try again in a moment?",
                "venue_tags": [],
                "missing_info": [],
            }

        intent          = ai_result.get("intent", "chat")
        venue_tags      = ai_result.get("venue_tags") or []
        new_missing     = ai_result.get("missing_info") or []
        chat_response   = ai_result.get("chat_response", "")
        gift_suggestion = ai_result.get("gift_suggestion")
        event_type      = ai_result.get("event_type")
        budget_for_filter = ai_result.get("budget_per_head") or extracted_budget
        location_for_filter = ai_result.get("location") or extracted_location

        save_persona_data = ai_result.get("save_persona")
        ask_save_persona  = ai_result.get("ask_save_persona", False)
        _query_lower_pers = user_query.lower().strip()
        _user_said_yes    = any(s in _query_lower_pers for s in ["yes", "sure", "ok", "okay", "save", "please", "yep", "yeah", "do it"])

        # FIX 1: Correctly parse the age and personality strings
        if save_persona_data and isinstance(save_persona_data, dict) and _user_said_yes:
            try:
                name = save_persona_data.get("name", "").strip()
                if name and not any(p.name.lower() == name.lower() for p in personas):
                    pdata = {
                        "name": name,
                        "relationship": save_persona_data.get("relationship"),
                        "personality": save_persona_data.get("personality") or "",
                        "food_preferences": save_persona_data.get("food_preferences") or [],
                        "music_preferences": save_persona_data.get("music_preferences") or [],
                        "personality_tags": save_persona_data.get("personality_tags") or [],
                        "color_preferences": save_persona_data.get("color_preferences") or [],
                    }
                    
                    age = save_persona_data.get("age")
                    if age:
                        pdata["personality"] = (pdata["personality"] + f" Age: {age}").strip()

                    new_persona = persona_svc.create_persona(db, customer_id=str(customer.customer_id), data=pdata)
                    persona_svc.confirm_persona(db, new_persona.persona_id, str(customer.customer_id))
                    personas = persona_svc.get_personas(db, str(customer.customer_id))
            except Exception as e: 
                logger.warning(f"Persona auto-save failed: {e}")

        use_persona_name = ai_result.get("use_persona_name", "").strip() if ai_result.get("use_persona_name") else ""
        if use_persona_name and personas:
            matched_persona = next((p for p in personas if p.name.lower() == use_persona_name.lower()), None)
            if matched_persona and not matched_persona.is_confirmed:
                try: persona_svc.confirm_persona(db, matched_persona.persona_id, str(customer.customer_id))
                except Exception: pass

        _query_lower = (user_query or "").lower()
        _has_gift = any(s in _query_lower for s in ["gift", "present", "buy", "surprise", "get her", "get him"])
        _has_plan = any(s in _query_lower for s in ["venue", "dinner", "restaurant", "party", "book", "plan", "event"])
        if _has_gift and _has_plan:
            intent = "multi"

        matched_venues   = []
        venue_match_tier = None

        if intent == "multi" and venue_tags:
            pkgs = vendor_svc.find_perfect_matches(
                db, criteria={"venue_tags": venue_tags, "budget_per_head": budget_for_filter, "location": location_for_filter, "guest_count": extracted_guests}
            )
            matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]

            gift_tags = list(venue_tags)
            response_lower = (chat_response or "").lower()
            for persona in personas:
                if persona.name and persona.name.lower() in response_lower:
                    def _parse_list(val):
                        if isinstance(val, str):
                            import json
                            try: return json.loads(val)
                            except: return [val]
                        return list(val or [])
                    
                    merged = list(set(_parse_list(persona.preferences_json) + _parse_list(persona.food_preferences) + _parse_list(persona.personality_tags)))
                    gift_tags = list(set(gift_tags + merged))
                    
            gift_pkgs = vendor_svc.find_gift_matches(db, gift_tags=gift_tags, budget=budget_for_filter)
            if gift_pkgs and not gift_suggestion:
                gift_suggestion = f"{gift_pkgs[0].name} - {getattr(gift_pkgs[0], 'description', '') or ''}".strip(" -")

        elif intent in ("planning", "date", "gift") and venue_tags:
            if intent == "gift":
                gift_tags = list(venue_tags)
                response_lower = (chat_response or "").lower()
                for persona in personas:
                    if persona.name and persona.name.lower() in response_lower:
                        def _parse_list(val):
                            if isinstance(val, str):
                                import json
                                try: return json.loads(val)
                                except: return [val]
                            return list(val or [])
                        merged = list(set(_parse_list(persona.preferences_json) + _parse_list(persona.food_preferences) + _parse_list(persona.personality_tags)))
                        gift_tags = list(set(gift_tags + merged))
                        
                pkgs = vendor_svc.find_gift_matches(db, gift_tags=gift_tags, budget=budget_for_filter)
            else:
                pkgs = vendor_svc.find_perfect_matches(
                    db, criteria={"venue_tags": venue_tags, "budget_per_head": budget_for_filter, "location": location_for_filter, "guest_count": extracted_guests}
                )

            matched_venues = [_package_to_dict(p, requested_tags=venue_tags) for p in pkgs]

            if pkgs:
                canonical_loc = vendor_svc.extract_location_from_text(location_for_filter or "")
                first = pkgs[0]
                pkg_tags = first.tags or []
                if isinstance(pkg_tags, str):
                    import json
                    try: pkg_tags = json.loads(pkg_tags)
                    except: pkg_tags = []
                
                all_tags_match = set(venue_tags).issubset(set(pkg_tags))
                loc_match = canonical_loc and canonical_loc in (getattr(first, "location_coverage", "") or "").lower()
                
                if all_tags_match and loc_match: venue_match_tier = 1
                elif all_tags_match: venue_match_tier = 2
                else: venue_match_tier = 3

        chat_svc.save_message(
            db, session_id=session_id, user_msg=user_query, ai_msg=chat_response or "",
            customer_id=customer.customer_id, missing_info=new_missing,
        )

        _persona_saved = (bool(save_persona_data) and _user_said_yes and isinstance(save_persona_data, dict) and bool(save_persona_data.get("name", "").strip()))
        _persona_confirmed = bool(use_persona_name)

        # FIX 2: Restored ai_result.get() fallbacks for parameters that regex failed to extract
        return PlanResponse(
            intent             = intent,
            reasoning          = ai_result.get("reasoning"),
            personality_profile= ai_result.get("personality_profile"),
            chat_response      = chat_response,
            gift_suggestion    = gift_suggestion,
            missing_info       = new_missing,
            venue_match_tier   = venue_match_tier,
            event_type         = event_type,
            event_date         = extracted_date,
            location           = ai_result.get("location") or extracted_location,
            budget_per_head    = ai_result.get("budget_per_head") or extracted_budget,
            guest_count        = ai_result.get("guest_count") or extracted_guests,
            venue_tags         = venue_tags,
            matched_venues     = matched_venues,
            ask_save_persona   = bool(ask_save_persona),
            persona_saved      = _persona_saved,
            persona_confirmed  = _persona_confirmed,
        )

planning_service = PlanningService()