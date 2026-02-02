import httpx
import json
import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

# 1. SETUP LOGGING
# Essential for tracing the 'Context Injection' process during debugging.
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.base_url = settings.LANGFLOW_URL
        self.token = settings.LANGFLOW_TOKEN
        self.org_id = settings.LANGFLOW_ORG_ID

        if not self.token:
            logger.critical("🚨 CRITICAL: LANGFLOW_TOKEN is missing from settings!")
        else:
            logger.info("🔧 AI Service initialized with Memory/Session Support.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def generate_date_plan(self, raw_query: str, history: Optional[List] = None):
        """
        Injects past conversation turns into the prompt before calling Langflow.
        This provides the 'Contextual Memory' needed for multi-user sessions.
        """
        
        # --- PHASE 1: CONTEXT INJECTION ---
        # We transform SQLAlchemy history objects into a readable string for the LLM.
        context_block = ""
        if history:
            # We reverse the order if needed to ensure Oldest -> Newest flow
            context_block = "\n".join([
                f"User: {msg.user_message}\nAI: {msg.ai_message}" 
                for msg in history if msg.ai_message
            ])
            logger.info(f"🧠 Context Injection: {len(history)} messages added to prompt.")

        # The 'Final Prompt' is the secret sauce. It tells the AI exactly what happened before.
        full_input = (
            f"Conversation History:\n{context_block}\n\n"
            f"Current User Message: {raw_query}"
        )
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-DataStax-Current-Org": self.org_id
        }
        
        payload = {
            "input_value": full_input,
            "inputType": "chat",
            "outputType": "chat",
            "tweaks": {} # Add specific Langflow tweaks here if necessary
        }

        # --- PHASE 2: EXECUTION ---
        async with httpx.AsyncClient() as client:
            logger.info("🚀 Dispatching query to Langflow (Astra)...")
            
            response = await client.post(
                self.base_url, 
                json=payload, 
                headers=headers, 
                timeout=60.0
            )
            response.raise_for_status()
            
            data = response.json()
            
            # --- PHASE 3: OUTPUT SANITIZATION ---
            try:
                # Navigating Langflow's nested JSON structure
                raw_text = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                
                # Remove Markdown code fences (```json ... ```) that LLMs often add
                clean_json = raw_text.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean_json)
                
                logger.info("✅ Valid structured response received from AI.")
                return parsed_data
                
            except Exception as e:
                logger.error(f"⚠️ AI Response Parsing Failed: {e}. Raw: {raw_text[:100]}")
                return {
                    "intent": "chat",
                    "reasoning": "Failed to parse structured AI output.",
                    "chat_response": "I understood that, but I'm having trouble formatting my plan. Could you try asking in a different way?"
                }

# Singleton instance for the app
ai_service = AIService()