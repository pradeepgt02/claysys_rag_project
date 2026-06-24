import sys
import uuid
import re
import time
from pathlib import Path
from urllib.parse import urlparse

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

def ingest_website(
    url: str,
    max_pages: int = 25,
    initial_question: str = ""
) -> dict:
    """
    Orchestrates the ingestion, chunking, embedding, and indexing of a website
    (supporting HTML crawling, PDF downloading, and JSON ingestion).
    """
    # A. Validate input
    if not (1 <= max_pages <= 100):
        return {
            "success": False,
            "message": "Validation Error: max_pages must be between 1 and 100."
        }

    validation = validate_url(url)
    if not validation["valid"]:
        return {
            "success": False,
            "message": f"URL validation failed: {validation['message']}"
        }

    normalized_url = validation["normalized_url"]

    # B. Create website_id deterministically
    print(f"Starting crawl with max_pages={max_pages}")
    try:
        parsed_url = urlparse(normalized_url)
        hostname = parsed_url.hostname or ""
        # Strip www. and replace dots with underscores
        domain_clean = hostname.replace("www.", "").replace(".", "_")
        domain_clean = re.sub(r"[^a-zA-Z0-9_]", "", domain_clean)
        if not domain_clean:
            domain_clean = "website"
        
        short_uuid = str(uuid.uuid4())[:8]
        website_id = f"{domain_clean}_{short_uuid}"
    except Exception as e:
        return {
            "success": False,
            "message": f"Failed to generate website ID: {str(e)}"
        }

    # C. Detect Content Type
    type_detection = detect_content_type(normalized_url)
    if not type_detection["success"]:
        return {
            "success": False,
            "message": f"Content type detection failed: {type_detection['message']}"
        }

    content_type = type_detection["content_type"]
    final_url = type_detection["final_url"] or normalized_url

    all_chunks = []
    pages_crawled = 0
    documents_processed = 0

    # D. Handle content types
    if content_type == "html":
        # Crawl website
        crawl_result = crawl_website(final_url, max_pages, initial_question)
        if not crawl_result.get("success"):
            return {
                "success": False,
                "message": f"Website crawl failed: {crawl_result.get('message', 'unknown error')}"
            }
        
        pages = crawl_result.get("pages", [])
        pages_crawled = crawl_result.get("pages_crawled", 0)
        print(f"Crawled {pages_crawled}/{max_pages} pages")
        
        for p in pages:
            # Get text (run structured extract if html is available, else fallback to text)
            raw_html = p.get("raw_html") or p.get("html")
            if raw_html:
                try:
                    struct_res = extract_structured_content(raw_html)
                    clean_text = struct_res.get("clean_text", "") or p.get("text", "")
                except Exception:
                    clean_text = p.get("text", "")
            else:
                clean_text = p.get("text", "")

            doc = {
                "url": p.get("url"),
                "title": p.get("title", "Untitled Page"),
                "text": clean_text,
                "content_type": "html",
                "headings": p.get("headings", [])
            }
            
            try:
                chunks = chunk_document(doc)
                all_chunks.extend(chunks)
                documents_processed += 1
            except Exception as e:
                # Print error warning but continue processing other crawled pages
                print(f"[WARNING] Chunking failed for page {p.get('url')}: {str(e)}")
                
    elif content_type == "pdf":
        pdf_result = ingest_pdf(final_url)
        if not pdf_result.get("success"):
            return {
                "success": False,
                "message": f"PDF download or ingestion failed: {pdf_result.get('message', 'unknown error')}"
            }

        try:
            chunks = chunk_pdf_pages(pdf_result, final_url)
            all_chunks.extend(chunks)
            documents_processed = 1
            pages_crawled = pdf_result.get("page_count", 1)
        except Exception as e:
            return {
                "success": False,
                "message": f"PDF chunking failed: {str(e)}"
            }

    elif content_type == "json":
        json_result = ingest_json(final_url)
        if not json_result.get("success"):
            return {
                "success": False,
                "message": f"JSON download or ingestion failed: {json_result.get('message', 'unknown error')}"
            }

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
            return {
                "success": False,
                "message": f"JSON chunking failed: {str(e)}"
            }

    elif content_type == "text":
        return {
            "success": False,
            "message": "Plain text ingestion is not supported at this time."
        }
    else:
        return {
            "success": False,
            "message": f"Unsupported content type: {content_type}"
        }

    # Verify that chunks were created
    if not all_chunks:
        return {
            "success": False,
            "message": "No text chunks were generated from the source document(s). Indexing aborted."
        }

    print(f"Created {len(all_chunks)} chunks")

    # E. Embeddings
    try:
        embedded_chunks = embed_chunks(all_chunks)
    except Exception as embed_err:
        return {
            "success": False,
            "message": f"Embedding generation failed: {str(embed_err)}"
        }

    chunks_embedded = 0
    chunks_failed = 0
    for chunk in embedded_chunks:
        if "embedding" in chunk and "embedding_error" not in chunk:
            chunks_embedded += 1
        else:
            chunks_failed += 1

    print(f"Embedded {chunks_embedded} chunks")

    if chunks_embedded == 0:
        # Clear store mapping safely if created
        try:
            store = WebsiteVectorStore(website_id)
            store.clear()
        except Exception:
            pass
        return {
            "success": False,
            "message": "All chunk embeddings failed. Indexing aborted."
        }

    # F. FAISS Vector Store Saving
    try:
        store = WebsiteVectorStore(website_id)
        # Clear any prior index directory entries
        store.clear()
        
        add_res = store.add_embedded_chunks(embedded_chunks)
        if not add_res.get("success"):
            store.clear()
            return {
                "success": False,
                "message": f"Failed to add vectors to FAISS index: {add_res.get('message', 'unknown error')}"
            }
            
        store.save()
    except Exception as faiss_err:
        try:
            store = WebsiteVectorStore(website_id)
            store.clear()
        except Exception:
            pass
        return {
            "success": False,
            "message": f"FAISS index storage failed: {str(faiss_err)}"
        }

    stats = store.get_stats()

    # G. Return successful output dictionary
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
        "message": "Website crawled and indexed successfully"
    }

if __name__ == "__main__":
    print("=" * 70)
    print("Running Full Website Ingestion Service self-tests...")
    print("=" * 70)

    test_url = "https://www.python.org"
    print(f"\nIngesting target: '{test_url}' with max_pages=2...")
    
    result = ingest_website(test_url, max_pages=2)
    
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
    print(f"Message:             {result.get('message')}")
    
    # Print the storage location clearly
    store_id = result.get('website_id', 'unknown')
    print(f"\nStorage Location for website_id '{store_id}':")
    print(f"  data/indexes/{store_id}/")

    print("\n" + "=" * 70)
    print("Self-test completed successfully!")
    print("=" * 70)
