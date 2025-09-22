# backend/app/adapters/azure_search_adapter.py
import requests
from typing import List, Dict, Any
from backend.app.core.config import settings

class AzureSearchAdapter:
    def __init__(self):
        self.endpoint = settings.azure_search_endpoint.rstrip("/")
        self.api_key = settings.azure_search_key
        self.index = settings.azure_search_index
        self.headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }
        # API version used for vector search and indexing - adjust if Azure updates
        self.api_version = "2021-04-30-Preview"

    def upload_documents(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Uploads a batch of documents. Each doc must include '@search.action': 'upload' or 'mergeOrUpload'.
        """
        url = f"{self.endpoint}/indexes/{self.index}/docs/index?api-version={self.api_version}"
        payload = {"value": docs}
        r = requests.post(url, headers=self.headers, json=payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def vector_search(self, vector: List[float], top_k: int = 5, filter_query: str = None) -> Dict[str, Any]:
        """
        Uses Azure Cognitive Search vector search endpoint. The vector field name in the index is assumed 'content_vector'.
        """
        url = f"{self.endpoint}/indexes/{self.index}/docs/search?api-version={self.api_version}"
        search_payload = {
            "vector": {
                "value": vector,
                "fields": "content_vector",
                "k": top_k
            },
            "top": top_k
        }
        if filter_query:
            search_payload["filter"] = filter_query
        r = requests.post(url, headers=self.headers, json=search_payload, timeout=60)
        r.raise_for_status()
        return r.json()

    def create_index_if_not_exists(self, index_schema: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.endpoint}/indexes?api-version={self.api_version}"
        r = requests.get(url, headers=self.headers, timeout=30)
        if r.status_code == 200:
            # existing: you may want to inspect & decide; for now, skip creation
            return {"status": "exists"}
        # create index
        r2 = requests.post(url, headers=self.headers, json=index_schema, timeout=60)
        r2.raise_for_status()
        return r2.json()