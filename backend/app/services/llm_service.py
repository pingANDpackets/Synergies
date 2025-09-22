# backend/app/services/llm_service.py
from backend.app.utils.azure_openai_client import AzureOpenAIClient
from typing import List, Dict, Any

class LLMService:
    def __init__(self):
        self.client = AzureOpenAIClient()

    def generate_text(self, messages: List[Dict[str, Any]], temperature: float = 0.0, max_tokens: int = 512) -> str:
        return self.client.simple_completion_text(messages=messages, temperature=temperature, max_tokens=max_tokens)