import os
import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AIService:
    def __init__(self):
        # ✅ SECURE: Read credentials from the .env file
        # This prevents GitHub from blocking your push
        self.base_url = os.getenv("LANGFLOW_URL")
        self.token = os.getenv("LANGFLOW_TOKEN")
        self.org_id = os.getenv("LANGFLOW_ORG_ID")

        # Safety check to warn you if .env is missing
        if not self.token:
            print("⚠️ WARNING: LANGFLOW_TOKEN is missing from environment variables!")

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(httpx.HTTPStatusError)
    )
    async def generate_date_plan(self, raw_query: str):
        # 🚀 SIMPLIFIED: We send ONLY what the user typed.
        
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
            print(f"🧠 Sending to Langflow: {raw_query}")
            response = await client.post(self.base_url, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            try:
                # We expect JSON because your System Prompt enforces it
                outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                
                # Clean up markdown if AI adds it
                clean_json = outputs.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean_json)
                
                print("✅ Received Valid JSON from Langflow")
                return parsed_data
                
            except Exception as e:
                print(f"⚠️ JSON Parse Error: {e}")
                # Fallback structure
                return {
                    "intent": "chat",
                    "reasoning": "I couldn't process the response structure.",
                    "chat_response": "I'm having trouble connecting to my brain right now. Please try again."
                }

ai_service = AIService()