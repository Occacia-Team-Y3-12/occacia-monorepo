import os
import httpx
import json
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

class AIService:
    def __init__(self):
        # ✅ Reading from injected environment variables
        self.base_url = os.getenv("LANGFLOW_URL")
        self.token = os.getenv("LANGFLOW_TOKEN")
        self.org_id = os.getenv("LANGFLOW_ORG_ID")

        # Initialization check for logs
        if not self.token:
            print("🚨 CRITICAL: LANGFLOW_TOKEN not found in environment!")
        else:
            print("🔧 AI Service initialized with secure credentials.")

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
            print(f"🧠 Sending to Langflow: {raw_query}")
            response = await client.post(self.base_url, json=payload, headers=headers, timeout=45.0)
            response.raise_for_status()
            
            data = response.json()
            try:
                # Extracting text from Langflow nested structure
                outputs = data["outputs"][0]["outputs"][0]["results"]["message"]["text"]
                
                # Remove markdown code blocks if present
                clean_json = outputs.replace("```json", "").replace("```", "").strip()
                parsed_data = json.loads(clean_json)
                
                print("✅ Received Valid JSON from Langflow")
                return parsed_data
                
            except Exception as e:
                print(f"⚠️ JSON Parse Error: {e}. Raw Output: {outputs[:100]}...")
                return {
                    "intent": "chat",
                    "reasoning": "AI returned unstructured data.",
                    "chat_response": "I'm having trouble formatting my thoughts. Can you try again?"
                }

ai_service = AIService()