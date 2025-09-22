# backend/app/orchestration/indexer.py
from backend.app.services.enrichment import EnrichmentPipeline
from backend.app.services.embeddings import AzureEmbeddings
from backend.app.adapters.azure_search_adapter import AzureSearchAdapter
from backend.app.logging.search_lineage_logger import SearchLineageLogger
import uuid

class Indexer:
    def __init__(self):
        self.enr = EnrichmentPipeline()
        self.embed = AzureEmbeddings()
        self.search = AzureSearchAdapter()
        self.logger = SearchLineageLogger()

    def index_blob(self, blob_path: str, doc_id: str = None):
        """
        Enrich a document, chunk it (simple whole-document chunk), embed and upload to Azure Search.
        doc_id: optional stable id; otherwise generate.
        """
        if doc_id is None:
            doc_id = str(uuid.uuid4())
        enriched = self.enr.enrich_document(blob_path)
        content = enriched["content"]
        # naive chunking: in MVP put whole doc as one chunk; later split into multiple chunks
        chunk_id = f"{doc_id}_0"
        embedding = self.embed.get_embeddings([content])[0]
        doc = {
            "@search.action": "upload",
            "id": chunk_id,
            "doc_id": doc_id,
            "chunk_index": 0,
            "content": content,
            "content_vector": embedding,
            "category_l0": enriched["category"]["Validated_L0"],
            "category_l1": enriched["category"]["Validated_L1"],
            "amount": enriched["amount"]
        }
        resp = self.search.upload_documents([doc])
        # lineage
        self.logger.log_index(doc_id=doc_id, source=blob_path, enrichment_version="v1", embedding_version=self.embed.deployment)
        return resp