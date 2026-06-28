import json
import queue
import threading
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from app.schemas import RootResponse, HealthResponse, UrlValidationRequest, UrlValidationResponse, ContentTypeRequest, ContentTypeResponse, HtmlIngestRequest, HtmlIngestResponse, CrawlRequest, CrawlResponse, IngestUrlRequest, IngestUrlResponse, IngestWebsiteRequest, IngestWebsiteResponse, ChatRequest, ChatResponse, IndexedPagesResponse
from app.ingestion.url_validator import validate_url
from app.ingestion.content_type_detector import detect_content_type
from app.ingestion.html_ingestor import ingest_html
from app.ingestion.ingestion_router import ingest_url
from app.crawler.generic_crawler import crawl_website
from app.services.ingest_service import ingest_website
from app.services.chat_service import chat_with_website
from app import config





# Initialize FastAPI App
app = FastAPI(title="WebMind – RAG Powered Website Chatbot")

@app.on_event("startup")
async def startup_event():
    import logging
    logging.info(f"GROQ_API_KEY is configured: {bool(config.GROQ_API_KEY)}")
    print(f"INFO:     GROQ_API_KEY is configured: {bool(config.GROQ_API_KEY)}")

# Configure CORS origins
import os
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
cors_env = os.getenv("CORS_ORIGINS", "")
if cors_env:
    origins.extend([o.strip() for o in cors_env.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_model=RootResponse)
async def read_root():
    """Root endpoint to check if the backend service is running."""
    return {"message": "WebMind backend is running"}

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint evaluating both backend and Groq API connectivity."""
    # Since we now rely on local embeddings and Groq (which doesn't have a simple ping endpoint without paying),
    # we just verify the key is present.
    if config.GROQ_API_KEY:
        return HealthResponse(
            backend_status="healthy",
            gemini_status="connected", # Kept as gemini_status for frontend backwards compatibility
            chat_model=config.GROQ_MODEL,
            embedding_model="sentence-transformers/all-MiniLM-L6-v2"
        )
    else:
        return HealthResponse(
            backend_status="healthy",
            gemini_status="not_connected",
            message="GROQ_API_KEY is not configured"
        )

@app.post("/validate-url", response_model=UrlValidationResponse)
async def validate_url_endpoint(payload: UrlValidationRequest):
    """Endpoint to validate and normalize a target crawling URL safely against SSRF."""
    result = validate_url(payload.url)
    return UrlValidationResponse(
        valid=result["valid"],
        normalized_url=result["normalized_url"],
        message=result["message"]
    )

@app.post("/detect-content-type", response_model=ContentTypeResponse)
async def detect_content_type_endpoint(payload: ContentTypeRequest):
    """Endpoint to detect the content type of a target URL after validating it."""
    # 1. Validate the URL first
    validation = validate_url(payload.url)
    if not validation["valid"]:
        return ContentTypeResponse(
            success=False,
            final_url=None,
            status_code=None,
            content_type="unknown",
            raw_content_type=None,
            message=f"URL validation failed: {validation['message']}"
        )

    # 2. Detect the content type
    result = detect_content_type(validation["normalized_url"])
    return ContentTypeResponse(
        success=result["success"],
        final_url=result["final_url"],
        status_code=result["status_code"],
        content_type=result["content_type"],
        raw_content_type=result["raw_content_type"],
        message=result["message"]
    )

@app.post("/ingest-html", response_model=HtmlIngestResponse)
async def ingest_html_endpoint(payload: HtmlIngestRequest):
    """Endpoint to validate, detect content type, and ingest static HTML site contents."""
    # 1. Validate the URL first
    validation = validate_url(payload.url)
    if not validation["valid"]:
        return HtmlIngestResponse(
            success=False,
            final_url=None,
            title="",
            description="",
            headings=[],
            text="",
            links=[],
            text_length=0,
            message=f"URL validation failed: {validation['message']}"
        )

    normalized_url = validation["normalized_url"]

    # 2. Detect Content Type
    type_detection = detect_content_type(normalized_url)
    if not type_detection["success"]:
        return HtmlIngestResponse(
            success=False,
            final_url=None,
            title="",
            description="",
            headings=[],
            text="",
            links=[],
            text_length=0,
            message=f"Content type detection failed: {type_detection['message']}"
        )

    if type_detection["content_type"] != "html":
        return HtmlIngestResponse(
            success=False,
            final_url=type_detection["final_url"],
            title="",
            description="",
            headings=[],
            text="",
            links=[],
            text_length=0,
            message=f"This URL is not an HTML website. Detected type: {type_detection['content_type']}"
        )

    # 3. Ingest HTML content
    result = ingest_html(type_detection["final_url"])
    return HtmlIngestResponse(
        success=result["success"],
        final_url=result["final_url"],
        title=result["title"],
        description=result["description"],
        headings=result["headings"],
        text=result["text"],
        links=result["links"],
        text_length=result["text_length"],
        message=result["message"]
    )

@app.post("/crawl", response_model=CrawlResponse)
async def crawl_endpoint(payload: CrawlRequest):
    """Endpoint to crawl multiple same-domain pages recursively starting at a target URL."""
    result = crawl_website(payload.url, payload.max_pages)
    return CrawlResponse(
        success=result["success"],
        start_url=result["start_url"],
        pages_crawled=result["pages_crawled"],
        pages=result["pages"],
        visited_urls=result["visited_urls"],
        failed_urls=result["failed_urls"],
        message=result["message"]
    )

@app.post("/ingest-url", response_model=IngestUrlResponse)
async def ingest_url_endpoint(payload: IngestUrlRequest):
    """Endpoint to validate, detect content type, and ingest HTML/PDF/JSON content safely."""
    result = ingest_url(payload.url)
    return IngestUrlResponse(
        success=result["success"],
        final_url=result["final_url"],
        content_type=result.get("content_type"),
        title=result.get("title"),
        description=result.get("description"),
        headings=result.get("headings"),
        text=result.get("text"),
        combined_text=result.get("combined_text"),
        links=result.get("links"),
        pages=result.get("pages"),
        page_count=result.get("page_count"),
        data=result.get("data"),
        text_length=result.get("text_length", 0),
        message=result["message"]
    )

@app.post("/ingest")
async def ingest_website_endpoint(payload: IngestWebsiteRequest):
    """
    Streams NDJSON progress events during website crawling, embedding, and indexing.
    Each line is a JSON object with a 'stage' field.  The final line contains all
    IngestWebsiteResponse fields when stage == 'completed' or stage == 'failed'.
    """
    if payload.max_pages and payload.max_pages > 100:
        raise HTTPException(status_code=422, detail="Maximum allowed crawl limit is 100 pages.")

    # Thread-safe queue for progress events produced by the background worker
    event_queue: queue.Queue = queue.Queue()
    _SENTINEL = object()  # signals that the worker is done

    def run_ingestion():
        def on_progress(event: dict):
            event_queue.put(event)

        result = ingest_website(
            url=payload.url,
            max_pages=payload.max_pages or 25,
            initial_question=payload.initial_question or "",
            progress_callback=on_progress
        )
        # Merge final result into the last event so the frontend gets all fields
        event_queue.put({**result, "stage": result.get("stage", "completed" if result.get("success") else "failed")})
        event_queue.put(_SENTINEL)

    worker = threading.Thread(target=run_ingestion, daemon=True)
    worker.start()

    def generate():
        while True:
            item = event_queue.get()
            if item is _SENTINEL:
                break
            yield json.dumps(item) + "\n"

    return StreamingResponse(generate(), media_type="application/x-ndjson")

@app.get("/test_retrieval")
async def test_retrieval(website_id: str, question: str):
    from app.rag.retriever import retrieve_relevant_chunks
    res = retrieve_relevant_chunks(website_id, question, top_k=20)
    return res

@app.get("/test_retrieval2")
async def test_retrieval2(website_id: str, question: str):
    from app.rag.retriever import retrieve_relevant_chunks
    res = retrieve_relevant_chunks(website_id, question, top_k=20)
    return res

@app.get("/test_metadata")
async def test_metadata(website_id: str, url: str = None):
    import json
    from pathlib import Path
    from app import config
    
    meta_path = Path(config.VECTOR_DATA_DIR) / website_id / "metadata.json"
    index_path = Path(config.VECTOR_DATA_DIR) / website_id / "index.faiss"
    if not meta_path.is_absolute():
        meta_path = Path(config.BASE_DIR) / meta_path
        index_path = Path(config.BASE_DIR) / index_path
        
    with open(meta_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
        
    import faiss
    try:
        index = faiss.read_index(str(index_path))
        ntotal = index.ntotal
    except Exception as e:
        ntotal = -1
        
    if url:
        chunks = [m for m in metadata if m.get("source_url") == url]
    else:
        chunks = metadata
    return {"ntotal": ntotal, "length": len(metadata), "chunks": chunks}

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(payload: ChatRequest):
    """Endpoint to submit user questions and receive context-grounded RAG answers with citations."""
    result = chat_with_website(
        website_id=payload.website_id,
        question=payload.question,
        top_k=payload.top_k or 15
    )
    return ChatResponse(
        success=result["success"],
        website_id=result["website_id"],
        question=result["question"],
        answer=result["answer"],
        sources=result["sources"],
        retrieved_chunks_count=result["retrieved_chunks_count"],
        used_context_fallback=result["used_context_fallback"],
        message=result["message"],
        generator=result.get("generator", "context_fallback"),
        top_relevance_score=result.get("top_relevance_score"),
        retrieval_relevant=result.get("retrieval_relevant"),
        answer_mode=result.get("answer_mode"),
        is_grounded=result.get("is_grounded", False)
    )


@app.get("/websites/{website_id}/indexed-pages", response_model=IndexedPagesResponse)
async def get_indexed_pages_endpoint(website_id: str):
    """
    Retrieves the list of crawled and indexed pages for a given website from FAISS metadata.
    Uses metadata-only loading (skips the heavy FAISS binary) for fast response times.
    """
    from app.rag.vector_store import WebsiteVectorStore, sanitize_website_id
    from urllib.parse import urlparse
    import json as _json

    try:
        sanitized_id = sanitize_website_id(website_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    store = WebsiteVectorStore(sanitized_id)

    # Use metadata-only load — avoids deserializing the full FAISS binary which can be slow
    if not store.load_metadata_only() or not store.metadata_store:
        raise HTTPException(status_code=404, detail=f"Website ID '{website_id}' not found or index files are missing.")

    # Read vector count from store_info.json (already saved during indexing) to avoid loading FAISS
    info_path = store.storage_path / "store_info.json"
    vectors_stored = len(store.metadata_store)  # fallback
    if info_path.exists():
        try:
            with open(info_path, "r", encoding="utf-8") as _f:
                info = _json.load(_f)
            vectors_stored = info.get("vector_count", vectors_stored)
        except Exception:
            pass

    # Group chunks by source_url
    url_groups = {}
    for chunk in store.metadata_store:
        url = chunk.get("source_url") or ""
        if not url:
            continue
        if url not in url_groups:
            url_groups[url] = {
                "url": url,
                "title": chunk.get("title") or "Untitled Page",
                "chunks_count": 0,
                "status": "indexed"
            }
        url_groups[url]["chunks_count"] += 1

    if not url_groups:
        raise HTTPException(status_code=404, detail=f"No indexed pages found for Website ID '{website_id}'.")

    # Helper function to find the homepage URL (closest to root domain)
    def get_homepage_url(urls: list[str]) -> str:
        if not urls:
            return ""
        def url_key(u):
            parsed = urlparse(u)
            path = parsed.path.rstrip('/')
            path_segments = [seg for seg in path.split('/') if seg]
            return (len(path_segments), len(path), len(parsed.query), len(u))
        return min(urls, key=url_key)

    homepage_url = get_homepage_url(list(url_groups.keys()))

    # Sort pages: homepage first, then descending chunks_count, then alphabetical title
    pages = list(url_groups.values())
    pages.sort(key=lambda x: (
        x["url"] != homepage_url,  # False (0) for homepage, True (1) for others -> homepage first
        -x["chunks_count"],        # descending chunks_count
        x["title"]                 # alphabetical title
    ))

    pages_indexed = len(url_groups)
    chunks_created = len(store.metadata_store)

    return IndexedPagesResponse(
        success=True,
        website_id=sanitized_id,
        source_url=homepage_url,
        stats={
            "pages_indexed": pages_indexed,
            "chunks_created": chunks_created,
            "vectors_stored": vectors_stored
        },
        pages=pages
    )

@app.delete("/websites/{website_id}")
async def delete_website_endpoint(website_id: str):
    """Deletes an indexed website's vector store and metadata."""
    from app.rag.vector_store import WebsiteVectorStore, sanitize_website_id
    try:
        sanitized_id = sanitize_website_id(website_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
        
    store = WebsiteVectorStore(sanitized_id)
    try:
        store.clear()
        return {"success": True, "message": f"Website '{website_id}' deleted successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete website: {str(e)}")
