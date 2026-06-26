import sys
import uuid
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from typing import Callable, Optional

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.ingestion.url_validator import validate_url
from app.ingestion.content_type_detector import detect_content_type
from app.ingestion.pdf_ingestor import ingest_pdf
from app.ingestion.json_ingestor import ingest_json
from app.crawler.generic_crawler import crawl_website
from app.extractors.extraction_router import extract_structured_content
from app.rag.chunker import chunk_document, chunk_pdf_pages
from app.rag.embeddings import embed_chunks
from app.rag.vector_store import WebsiteVectorStore
from app import config


def _emit(callback: Optional[Callable], stage: str, message: str, extra: dict = None):
    """Helper to emit a progress event via callback if provided."""
    if callback is None:
        return
    payload = {"stage": stage, "message": message}
    if extra:
        payload.update(extra)
    try:
        callback(payload)
    except Exception:
        pass


def ingest_website(
    url: str,
    max_pages: int = 25,
    initial_question: str = "",
    progress_callback: Optional[Callable[[dict], None]] = None
) -> dict:
    """
    Orchestrates the ingestion, chunking, embedding, and indexing of a website
    (supporting HTML crawling, PDF downloading, and JSON ingestion).

    Emits real-time progress events via progress_callback if provided.
    """
    timings: dict = {}
    pipeline_start = time.perf_counter()

    # -------------------------------------------------------------------------
    # A. Validate input
    # -------------------------------------------------------------------------
    _emit(progress_callback, "validating_url", "Validating URL...")
    t0 = time.perf_counter()

    if not (1 <= max_pages <= 100):
        _emit(progress_callback, "failed", "Validation Error: max_pages must be between 1 and 100.")
        return {
            "success": False,
            "message": "Validation Error: max_pages must be between 1 and 100."
        }

    validation = validate_url(url)
    if not validation["valid"]:
        msg = f"URL validation failed: {validation['message']}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    normalized_url = validation["normalized_url"]
    timings["validating_url"] = round(time.perf_counter() - t0, 3)
    print(f"[TIMING] validating_url: {timings['validating_url']}s")

    # -------------------------------------------------------------------------
    # B. Create website_id deterministically
    # -------------------------------------------------------------------------
    print(f"Starting crawl with max_pages={max_pages}")
    try:
        parsed_url = urlparse(normalized_url)
        hostname = parsed_url.hostname or ""
        domain_clean = hostname.replace("www.", "").replace(".", "_")
        domain_clean = re.sub(r"[^a-zA-Z0-9_]", "", domain_clean)
        if not domain_clean:
            domain_clean = "website"
        short_uuid = str(uuid.uuid4())[:8]
        website_id = f"{domain_clean}_{short_uuid}"
    except Exception as e:
        msg = f"Failed to generate website ID: {str(e)}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    # -------------------------------------------------------------------------
    # C. Detect Content Type
    # -------------------------------------------------------------------------
    _emit(progress_callback, "detecting_content_type", "Detecting content type...")
    t0 = time.perf_counter()

    type_detection = detect_content_type(normalized_url)
    if not type_detection["success"]:
        msg = f"Content type detection failed: {type_detection['message']}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    content_type = type_detection["content_type"]
    final_url = type_detection["final_url"] or normalized_url
    timings["detecting_content_type"] = round(time.perf_counter() - t0, 3)
    print(f"[TIMING] detecting_content_type: {timings['detecting_content_type']}s")

    all_chunks = []
    pages_crawled = 0
    documents_processed = 0

    # -------------------------------------------------------------------------
    # D. Handle content types
    # -------------------------------------------------------------------------
    if content_type == "html":
        # -- Crawl --
        _emit(progress_callback, "crawling_pages", f"Crawling up to {max_pages} pages...")
        t0 = time.perf_counter()

        crawl_result = crawl_website(final_url, max_pages, initial_question)
        if not crawl_result.get("success"):
            msg = f"Website crawl failed: {crawl_result.get('message', 'unknown error')}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}

        pages = crawl_result.get("pages", [])
        pages_crawled = crawl_result.get("pages_crawled", 0)
        timings["crawling_pages"] = round(time.perf_counter() - t0, 3)
        print(f"[TIMING] crawling_pages: {timings['crawling_pages']}s  ({pages_crawled} pages)")

        # -- Extract content --
        _emit(progress_callback, "extracting_content", f"Extracting content from {pages_crawled} pages...")
        t0 = time.perf_counter()

        extracted_docs = []
        for p in pages:
            raw_html = p.get("raw_html") or p.get("html")
            if raw_html:
                try:
                    struct_res = extract_structured_content(raw_html)
                    clean_text = struct_res.get("clean_text", "") or p.get("text", "")
                except Exception:
                    clean_text = p.get("text", "")
            else:
                clean_text = p.get("text", "")

            extracted_docs.append({
                "url": p.get("url"),
                "title": p.get("title", "Untitled Page"),
                "text": clean_text,
                "content_type": "html",
                "headings": p.get("headings", [])
            })

        timings["extracting_content"] = round(time.perf_counter() - t0, 3)
        print(f"[TIMING] extracting_content: {timings['extracting_content']}s")

        # -- Chunk content --
        _emit(progress_callback, "chunking_content", "Chunking extracted content...")
        t0 = time.perf_counter()

        for doc in extracted_docs:
            try:
                chunks = chunk_document(doc)
                all_chunks.extend(chunks)
                documents_processed += 1
            except Exception as e:
                print(f"[WARNING] Chunking failed for page {doc.get('url')}: {str(e)}")

        timings["chunking_content"] = round(time.perf_counter() - t0, 3)
        print(f"[TIMING] chunking_content: {timings['chunking_content']}s  ({len(all_chunks)} raw chunks)")

    elif content_type == "pdf":
        _emit(progress_callback, "crawling_pages", "Downloading PDF...")
        t0 = time.perf_counter()
        pdf_result = ingest_pdf(final_url)
        if not pdf_result.get("success"):
            msg = f"PDF download or ingestion failed: {pdf_result.get('message', 'unknown error')}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}
        timings["crawling_pages"] = round(time.perf_counter() - t0, 3)

        _emit(progress_callback, "chunking_content", "Chunking PDF pages...")
        t0 = time.perf_counter()
        try:
            chunks = chunk_pdf_pages(pdf_result, final_url)
            all_chunks.extend(chunks)
            documents_processed = 1
            pages_crawled = pdf_result.get("page_count", 1)
        except Exception as e:
            msg = f"PDF chunking failed: {str(e)}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}
        timings["chunking_content"] = round(time.perf_counter() - t0, 3)

    elif content_type == "json":
        _emit(progress_callback, "crawling_pages", "Downloading JSON document...")
        t0 = time.perf_counter()
        json_result = ingest_json(final_url)
        if not json_result.get("success"):
            msg = f"JSON download or ingestion failed: {json_result.get('message', 'unknown error')}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}
        timings["crawling_pages"] = round(time.perf_counter() - t0, 3)

        _emit(progress_callback, "chunking_content", "Chunking JSON content...")
        t0 = time.perf_counter()
        doc = {
            "url": final_url,
            "title": json_result.get("title") or "JSON Document",
            "text": json_result.get("text", ""),
            "content_type": "json",
            "headings": []
        }
        try:
            chunks = chunk_document(doc)
            all_chunks.extend(chunks)
            documents_processed = 1
            pages_crawled = 1
        except Exception as e:
            msg = f"JSON chunking failed: {str(e)}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}
        timings["chunking_content"] = round(time.perf_counter() - t0, 3)

    elif content_type == "text":
        msg = "Plain text ingestion is not supported at this time."
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}
    else:
        msg = f"Unsupported content type: {content_type}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    # -------------------------------------------------------------------------
    # E. Deduplication and minimum length filtering
    # -------------------------------------------------------------------------
    original_count = len(all_chunks)
    seen_texts: set = set()
    unique_chunks = []
    for chunk in all_chunks:
        normalized = chunk.get("text", "").strip().lower()
        if len(normalized) < config.MIN_CHUNK_LENGTH:
            continue
        if normalized in seen_texts:
            continue
        seen_texts.add(normalized)
        unique_chunks.append(chunk)

    removed_count = original_count - len(unique_chunks)
    all_chunks = unique_chunks
    print(f"Chunks: original={original_count}, unique={len(all_chunks)}, removed={removed_count}")

    if not all_chunks:
        msg = "No text chunks were generated from the source document(s). Indexing aborted."
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    print(f"Created {len(all_chunks)} chunks")

    # -------------------------------------------------------------------------
    # F. Embeddings
    # -------------------------------------------------------------------------
    _emit(progress_callback, "creating_embeddings",
          f"Creating embeddings for {len(all_chunks)} chunks...",
          {"total_chunks": len(all_chunks), "processed_chunks": 0, "percentage": 0})
    t0 = time.perf_counter()

    try:
        embedded_chunks = embed_chunks(all_chunks, progress_callback=progress_callback)
    except Exception as embed_err:
        msg = f"Embedding generation failed: {str(embed_err)}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    timings["creating_embeddings"] = round(time.perf_counter() - t0, 3)
    print(f"[TIMING] creating_embeddings: {timings['creating_embeddings']}s")

    chunks_embedded = 0
    chunks_failed = 0
    for chunk in embedded_chunks:
        if "embedding" in chunk and "embedding_error" not in chunk:
            chunks_embedded += 1
        else:
            chunks_failed += 1

    print(f"Embedded {chunks_embedded} chunks")

    if chunks_embedded == 0:
        try:
            store = WebsiteVectorStore(website_id)
            store.clear()
        except Exception:
            pass
        msg = "All chunk embeddings failed. Indexing aborted."
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    # -------------------------------------------------------------------------
    # G. Build FAISS index
    # -------------------------------------------------------------------------
    _emit(progress_callback, "building_faiss_index", "Building FAISS vector index...")
    t0 = time.perf_counter()

    try:
        store = WebsiteVectorStore(website_id)
        store.clear()
        add_res = store.add_embedded_chunks(embedded_chunks)
        if not add_res.get("success"):
            store.clear()
            msg = f"Failed to add vectors to FAISS index: {add_res.get('message', 'unknown error')}"
            _emit(progress_callback, "failed", msg)
            return {"success": False, "message": msg}
    except Exception as faiss_err:
        try:
            WebsiteVectorStore(website_id).clear()
        except Exception:
            pass
        msg = f"FAISS index build failed: {str(faiss_err)}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    timings["building_faiss_index"] = round(time.perf_counter() - t0, 3)
    print(f"[TIMING] building_faiss_index: {timings['building_faiss_index']}s")

    # -------------------------------------------------------------------------
    # H. Save metadata
    # -------------------------------------------------------------------------
    _emit(progress_callback, "saving_metadata", "Saving index to disk...")
    t0 = time.perf_counter()

    try:
        store.save()
    except Exception as save_err:
        try:
            store.clear()
        except Exception:
            pass
        msg = f"FAISS index storage failed: {str(save_err)}"
        _emit(progress_callback, "failed", msg)
        return {"success": False, "message": msg}

    timings["saving_metadata"] = round(time.perf_counter() - t0, 3)
    print(f"[TIMING] saving_metadata: {timings['saving_metadata']}s")

    stats = store.get_stats()
    timings["total"] = round(time.perf_counter() - pipeline_start, 3)
    print(f"[TIMING] total pipeline: {timings['total']}s")

    # -------------------------------------------------------------------------
    # I. Completed
    # -------------------------------------------------------------------------
    _emit(progress_callback, "completed", "Website indexed successfully!")

    return {
        "success": True,
        "website_id": website_id,
        "source_url": final_url,
        "content_type": content_type,
        "pages_crawled": pages_crawled,
        "documents_processed": documents_processed,
        "chunks_created": len(all_chunks),
        "chunks_embedded": chunks_embedded,
        "chunks_failed": chunks_failed,
        "vector_store_stats": {
            "vector_count": stats.get("vector_count", 0),
            "dimension": stats.get("dimension", 0)
        },
        "timings": timings,
        "message": "Website crawled and indexed successfully"
    }


if __name__ == "__main__":
    print("=" * 70)
    print("Running Full Website Ingestion Service self-tests...")
    print("=" * 70)

    test_url = "https://www.python.org"
    print(f"\nIngesting target: '{test_url}' with max_pages=2...")

    def print_progress(event: dict):
        stage = event.get("stage", "")
        msg = event.get("message", "")
        pct = event.get("percentage")
        if pct is not None:
            print(f"  [PROGRESS] {stage}: {msg} ({pct}%)")
        else:
            print(f"  [PROGRESS] {stage}: {msg}")

    result = ingest_website(test_url, max_pages=2, progress_callback=print_progress)

    print("\nResult Highlights:")
    print(f"Success:             {result.get('success')}")
    print(f"Website ID:          {result.get('website_id')}")
    print(f"Source URL:          {result.get('source_url')}")
    print(f"Content Type:        {result.get('content_type')}")
    print(f"Pages Crawled:       {result.get('pages_crawled')}")
    print(f"Documents Processed: {result.get('documents_processed')}")
    print(f"Chunks Created:      {result.get('chunks_created')}")
    print(f"Chunks Embedded:     {result.get('chunks_embedded')}")
    print(f"FAISS Vector Count:  {result.get('vector_store_stats', {}).get('vector_count')}")
    print(f"Timings:             {result.get('timings')}")
    print(f"Message:             {result.get('message')}")

    store_id = result.get('website_id', 'unknown')
    print(f"\nStorage Location for website_id '{store_id}':")
    print(f"  data/indexes/{store_id}/")

    print("\n" + "=" * 70)
    print("Self-test completed successfully!")
    print("=" * 70)
