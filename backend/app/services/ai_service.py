import httpx
import json
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.core.config import settings

# 1. SETUP LOGGING
logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.base_url = settings.LANGFLOW_URL
        self.token = settings.LANGFLOW_TOKEN
        self.org_id = settings.LANGFLOW_ORG_ID

        # Initialization check
        if not self.token:
            logger.critical("🚨 CRITICAL: LANGFLOW_TOKEN is missing from Settings!")
        else:
            logger.info("🔧 AI Service initialized with secure credentials.")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def generate_date_plan(self, raw_query: str):
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "X-DataStax-Current-Org": self.org_id
        }
        
        payload = {
            "input_value": raw_query,
            "inputType": "chat",
            "outputType": "chat",
            "tweaks": {}
        }

        async with httpx.AsyncClient() as client:
            logger.info(f"🧠 Sending to Langflow: {raw_query}")
            
            response = await client.post(self.base_url, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            try:
                # Extracting text from Langflow nested structure
                outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                
                # Clean up markdown
                clean_json = outputs.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean_json)
                
                logger.info("✅ Received Valid JSON from Langflow")
                return parsed_data
                
            except Exception as e:
                # Safe failure mode
                error_snippet = str(outputs)[:100] if 'outputs' in locals() else "No output"
                logger.error(f"⚠️ JSON Parse Error: {e}. Raw Output Start: {error_snippet}...")
                
                return {
                    "intent": "chat",
                    "reasoning": "AI returned unstructured data.",
                    "chat_response": "I'm having trouble formatting my thoughts. Can you try again?"
                }

ai_service = AIService()