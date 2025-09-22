# backend/app/services/embeddings.py
from typing import List
from azure.core.credentials import AzureKeyCredential
from azure.ai.openai import OpenAIClient
from backend.app.core.config import settings
import hashlib
import json
import os

# Simple file-based cache to avoid repeated calls during local dev
CACHE_DIR = "./data/emb_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

class AzureEmbeddings:
    def __init__(self):
        self.client = OpenAIClient(settings.azure_openai_endpoint, AzureKeyCredential(settings.azure_openai_key))
        # embedding deployment may be the same as chat; allow separate
        self.deployment = settings.azure_embeddings_deployment or settings.azure_openai_deployment

    def _cache_key(self, texts: List[str]) -> str:
        key = hashlib.sha256(json.dumps(texts, sort_keys=True).encode("utf-8")).hexdigest()
        return os.path.join(CACHE_DIR, f"{key}.json")

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        # check cache
        cache_path = self._cache_key(texts)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # call Azure
        resp = self.client.embeddings.create(deployment=self.deployment, input=texts)
        embeddings = [d.embedding for d in resp.data]
        # save cache
        try:
            with open(cache_path, "w", encoding="utf-8") as f:
                json.dump(embeddings, f)
        except Exception:
            pass
        return embeddings