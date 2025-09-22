# backend/app/core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Azure OpenAI
    azure_openai_endpoint: str
    azure_openai_key: str
    azure_openai_deployment: str
    azure_openai_api_version: str = "2023-03-15-preview"
    azure_embeddings_deployment: str = None

    # Azure Cognitive Search
    azure_search_endpoint: str
    azure_search_key: str
    azure_search_index: str

    # Local / tooling
    faiss_index_path: str = "./data/faiss.index"
    mlflow_tracking_uri: str = "http://localhost:5000"
    env: str = "development"

    class Config:
        env_file = ".env"

settings = Settings()