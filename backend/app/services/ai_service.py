import httpx
import json
import logging
from typing import List
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

# 1. SETUP LOGGING
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.base_url = settings.LANGFLOW_URL
        self.token = settings.LANGFLOW_TOKEN
        self.org_id = settings.LANGFLOW_ORG_ID

        if not self.token or not self.base_url:
            logger.critical("🚨 CRITICAL: Missing LANGFLOW_TOKEN or URL in .env!")

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=5),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def generate_date_plan(self, raw_query: str, history: List = None):
        """
        Stateful AI Service with Dynamic Field Discovery and Detailed Error Reporting.
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-DataStax-Current-Org": self.org_id
        }
        
        # --- 🧠 DYNAMIC CONTEXT INJECTION ---
        context_string = ""
        if history:
            formatted_turns = []
            for m in history:
                # 🔍 DYNAMIC DISCOVERY: We look for the correct DB field name
                # This prevents the 'AttributeError' that crashed your last run.
                u_msg = getattr(m, 'user_query', getattr(m, 'user_msg', getattr(m, 'user_message', None)))
                a_msg = getattr(m, 'chat_response', getattr(m, 'ai_msg', getattr(m, 'ai_message', None)))

                if u_msg is None or a_msg is None:
                    # 🔥 CRITICAL LOG: This tells you exactly what the DB object actually contains
                    logger.error(f"❌ FIELD MISMATCH: DB object has no recognized message fields. Keys available: {m.__dict__.keys()}")
                    continue
                
                formatted_turns.append(f"PREVIOUS_USER: {u_msg}\nPREVIOUS_AI: {a_msg}")

            context_string = "\n".join(formatted_turns)
            logger.info(f"🧠 MEMORY LOADED: Injecting {len(formatted_turns)} turns into prompt.")

        # --- 📝 PROMPT CONSTRUCTION ---
        if context_string:
            full_input = (
                "SYSTEM: You are a stateful assistant. Use the following conversation history as context.\n"
                f"{context_string}\n"
                f"CURRENT_USER_INPUT: {raw_query}"
            )
        else:
            full_input = raw_query
        
        payload = {
            "input_value": full_input,
            "inputType": "chat",
            "outputType": "chat",
            "tweaks": {}
        }

        # Debug: Total payload length (If this is only the length of your query, history failed)
        logger.info(f"📡 OUTGOING TO LANGFLOW | Total Payload Length: {len(full_input)}")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(self.base_url, json=payload, headers=headers, timeout=40.0)
                response.raise_for_status()
            except Exception as e:
                logger.error(f"🔥 LANGFLOW CONNECTION ERROR: {str(e)}")
                raise

            data = response.json()
            try:
                # Extracting raw text from LangFlow's nested structure
                outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                
                # Handling AI Markdown (```json ... ```)
                clean_json = outputs.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean_json)
                
                logger.info("✅ SUCCESS: AI response parsed correctly.")
                return parsed_data
                
            except Exception as e:
                logger.warning(f"⚠️ PARSE FAILED: AI returned plain text. Raw: {outputs[:100]}...", e)
                return {
                    "intent": "chat",
                    "chat_response": outputs,
                    "reasoning": "AI did not return structured JSON context.",
                    "missing_info": ["history_context_sync"]
                }

ai_service = AIService()