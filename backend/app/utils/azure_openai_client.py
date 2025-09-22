# backend/app/utils/azure_openai_client.py
import requests
from typing import Any, Dict, List
from backend.app.core.config import settings

class AzureOpenAIClient:
    def __init__(self, timeout: int = 60):
        self.endpoint = settings.azure_openai_endpoint.rstrip("/") + "/"
        self.key = settings.azure_openai_key
        self.deployment = settings.azure_openai_deployment
        self.api_version = settings.azure_openai_api_version
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.key,
        }
        self.timeout = timeout

    def chat_completion(self, messages: List[Dict[str, Any]], temperature: float = 0.0, max_tokens: int = 512) -> Dict[str, Any]:
        url = f"{self.endpoint}openai/deployments/{self.deployment}/chat/completions?api-version={self.api_version}"
        payload = {
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        r = requests.post(url, headers=self.headers, json=payload, timeout=self.timeout)
        r.raise_for_status()
        return r.json()

    def simple_completion_text(self, messages: List[Dict[str, Any]], temperature: float = 0.0, max_tokens: int = 512) -> str:
        resp = self.chat_completion(messages=messages, temperature=temperature, max_tokens=max_tokens)
        # Try several shapes
        if isinstance(resp, dict):
            choices = resp.get("choices") or []
            if choices:
                # Azure returns {'choices': [{'message': {'role':'assistant','content':'...'}}]}
                first = choices[0]
                msg = first.get("message") or {}
                return msg.get("content", "")
        return str(resp)