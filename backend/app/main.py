# backend/app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
import uuid, os
from typing import Optional
from backend.app.orchestration.indexer import Indexer
from backend.app.services.llm_service import LLMService
from backend.app.adapters.azure_search_adapter import AzureSearchAdapter
from backend.app.logging.search_lineage_logger import SearchLineageLogger
from backend.app.services.embeddings import AzureEmbeddings

app = FastAPI(title="Procurement Synergy API")

UPLOAD_FOLDER = os.path.abspath("./data/uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

indexer = Indexer()
llm_service = LLMService()
search_adapter = AzureSearchAdapter()
lineage_logger = SearchLineageLogger()
emb_client = AzureEmbeddings()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        doc_id = str(uuid.uuid4())
        filename = f"{doc_id}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, "wb") as f:
            f.write(contents)
        return {"doc_id": doc_id, "filename": filename, "path": file_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/index")
def index_document(doc_id: str = Form(...), file_path: str = Form(...)):
    try:
        resp = indexer.index_blob(blob_path=file_path, doc_id=doc_id)
        return JSONResponse(content={"status": "indexed", "response": resp})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
def search_query(query: str = Form(...), top_k: int = Form(5), filters: Optional[str] = Form(None)):
    try:
        vector = emb_client.get_embeddings([query])[0]
        resp = search_adapter.vector_search(vector=vector, top_k=top_k, filter_query=filters)
        return JSONResponse(content=resp)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/qa")
def qa(query: str = Form(...), top_k: int = Form(5), filters: Optional[str] = Form(None)):
    try:
        # 1) embed
        vector = emb_client.get_embeddings([query])[0]
        # 2) search
        search_resp = search_adapter.vector_search(vector=vector, top_k=top_k, filter_query=filters)
        hits = []
        if isinstance(search_resp, dict) and "value" in search_resp:
            for item in search_resp["value"]:
                hits.append({
                    "id": item.get("id"),
                    "score": item.get("@search.score"),
                    "content": item.get("content"),
                    "metadata": {
                        "category_l0": item.get("category_l0"),
                        "category_l1": item.get("category_l1"),
                        "amount": item.get("amount")
                    }
                })
        else:
            hits = search_resp

        # 3) assemble prompt (simple stuffing - watch tokens)
        context_pieces = []
        for h in hits:
            snippet = h.get("content", "")[:1200]
            context_pieces.append(f"[DOC_ID:{h.get('id')}] {snippet}")
        prompt_context = "\n\n".join(context_pieces)
        system_prompt = ("You are an expert procurement analyst. Use ONLY the provided documents to answer. "
                         "Return JSON with fields: answer, citations (list of doc ids), confidence (0-1). If unsure, say 'I am not confident'.")
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Query: {query}\n\nContext:\n{prompt_context}"}
        ]
        answer_text = llm_service.generate_text(messages=messages, temperature=0.0, max_tokens=600)
        query_id = str(uuid.uuid4())
        lineage_logger.log_query(query_id=query_id, retrieval_hits=[h.get("id") for h in hits], prompt_template="default-stuff", user_id=None)
        return JSONResponse(content={"query_id": query_id, "answer": answer_text, "hits": hits})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))