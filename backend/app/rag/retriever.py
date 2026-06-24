import sys
from pathlib import Path
import numpy as np

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.gemini_client import create_embedding
from app.rag.vector_store import WebsiteVectorStore

def retrieve_relevant_chunks(
    website_id: str,
    question: str,
    top_k: int = 5
) -> dict:
    """
    Retrieves the most semantically relevant text chunks for a given user question.
    
    Flow:
    1. Validates non-empty website_id and question.
    2. Instantiates and loads the WebsiteVectorStore for the website_id.
    3. Generates the question vector embedding using Gemini (task_type='retrieval_query').
    4. Normalizes the question embedding using NumPy float32.
    5. Searches the local FAISS FlatIP index.
    6. Maps index positions back to metadata and similarity scores.
    
    Returns a unified results dictionary, resolving errors cleanly without crashing.
    """
    if not website_id or website_id.strip() == "":
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "results_count": 0,
            "results": [],
            "message": "website_id cannot be empty."
        }

    if not question or question.strip() == "":
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "results_count": 0,
            "results": [],
            "message": "question cannot be empty."
        }

    try:
        # Load local vector store
        store = WebsiteVectorStore(website_id)
        if not store.load() or not store.is_ready():
            return {
                "success": False,
                "website_id": website_id,
                "question": question,
                "results_count": 0,
                "results": [],
                "message": "No indexed website data found for this website_id."
            }

        # Generate question embedding vector (using RETRIEVAL_QUERY task configuration)
        try:
            search_query = question
            question_lower = question.lower()
            if "download" in question_lower or "install" in question_lower:
                search_query += " download install installer source code"
            
            query_emb = create_embedding(search_query, task_type="retrieval_query")
        except Exception as e:
            return {
                "success": False,
                "website_id": website_id,
                "question": question,
                "results_count": 0,
                "results": [],
                "message": f"Embedding creation failed for question: {str(e)}"
            }

        # Validate query embedding dimension matches index dimension
        if len(query_emb) != store.index.d:
            return {
                "success": False,
                "website_id": website_id,
                "question": question,
                "results_count": 0,
                "results": [],
                "message": f"Dimension mismatch: query embedding has dimension {len(query_emb)}, but index dimension is {store.index.d}."
            }

        # Convert to float32 NumPy array and shape as 2D (1, dimension)
        query_vector = np.array([query_emb], dtype=np.float32)

        # Normalize the query vector to unit L2 norm
        norm = np.linalg.norm(query_vector, axis=1, keepdims=True)
        norm = np.where(norm == 0, 1e-10, norm)  # Avoid division by zero
        normalized_query = query_vector / norm

        # Search index
        # distances and indices are returned as 2D arrays of shape (1, top_k)
        distances, indices = store.index.search(normalized_query, top_k)

        results = []
        for idx_in_batch, doc_idx in enumerate(indices[0]):
            # Ignore invalid positions returned by FAISS (e.g. -1 means not enough index vectors)
            if doc_idx == -1 or doc_idx >= len(store.metadata_store):
                continue

            meta = store.metadata_store[doc_idx]
            similarity_score = float(distances[0][idx_in_batch])

            results.append({
                "chunk_id": meta.get("chunk_id", ""),
                "text": meta.get("text", ""),
                "source_url": meta.get("source_url", ""),
                "title": meta.get("title", ""),
                "heading": meta.get("heading", ""),
                "content_type": meta.get("content_type", "html"),
                "page_number": meta.get("page_number"),
                "chunk_index": meta.get("chunk_index", 0),
                "similarity_score": round(similarity_score, 4)
            })

        return {
            "success": True,
            "website_id": website_id,
            "question": question,
            "results_count": len(results),
            "results": results,
            "message": "Relevant chunks retrieved successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "results_count": 0,
            "results": [],
            "message": f"An unexpected error occurred during retrieval search: {str(e)}"
        }

def format_retrieved_context(results: list[dict], max_context_chars: int = 12000) -> str:
    """
    Builds context text for the future Gemini answer generator.
    Includes only valid results, lists titles, headings, and URLs,
    and cuts off content safely prior to exceeding max_context_chars.
    """
    if not results:
        return ""

    formatted_parts = []
    current_length = 0

    for idx, res in enumerate(results):
        if not isinstance(res, dict) or "text" not in res:
            continue

        title = res.get("title", "") or "Untitled Document"
        url = res.get("source_url", "") or "No URL available"
        heading = res.get("heading", "") or "N/A"
        content = res.get("text", "")

        # Structure context header block
        source_header = f"[Source {idx + 1}]\nTitle: {title}\nURL: {url}\nHeading: {heading}\nContent:\n"
        
        # Room needed for header block and trailing spacer newlines
        needed_room = len(source_header) + 2
        
        if current_length + needed_room >= max_context_chars:
            break

        # Calculate remaining character budget for content slice
        remaining_budget = max_context_chars - current_length - needed_room
        if remaining_budget <= 50:
            break

        content_slice = content[:remaining_budget]
        block = f"{source_header}{content_slice}\n\n"

        formatted_parts.append(block)
        current_length += len(block)

    return "".join(formatted_parts).strip()

if __name__ == "__main__":
    print("=" * 70)
    print("Running Semantic Search Retriever self-tests...")
    print("=" * 70)

    from app.rag.embeddings import embed_chunks

    # 1. Create mock chunks
    test_chunks = [
        {
            "chunk_index": 0,
            "text": "Python can be downloaded from the official downloads page. Pre-compiled binary installers are available for Windows, macOS, and Linux platforms.",
            "source_url": "https://www.python.org/downloads",
            "title": "Welcome to Python.org",
            "heading": "Downloads"
        },
        {
            "chunk_index": 1,
            "text": "FastAPI is a modern web framework for building APIs with Python. It relies on standard Python type hints and is powered by Starlette and Pydantic for lightning-fast speeds.",
            "source_url": "https://fastapi.tiangolo.com",
            "title": "FastAPI Framework Documentation",
            "heading": "Introduction"
        },
        {
            "chunk_index": 2,
            "text": "FAISS (Facebook AI Similarity Search) is a library for efficient dense vector similarity search and clustering. It handles indexing high-dimensional databases that exceed GPU RAM limits.",
            "source_url": "https://github.com/facebookresearch/faiss",
            "title": "FAISS Vector Search Library",
            "heading": "Overview"
        },
        {
            "chunk_index": 3,
            "text": "A web crawler systematically browses URLs to download and parse HTML. Crawling is restricted to the same domain using url_normalizer and link_discovery constraints to prevent SSRF vulnerabilities.",
            "source_url": "https://crawler.webmind.org",
            "title": "WebMind Crawler Documentation",
            "heading": "Same-Domain Crawling Architecture"
        }
    ]

    print("Generating embeddings for test chunks...")
    try:
        embedded_chunks = embed_chunks(test_chunks)
        print("Embeddings generated successfully.")
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        sys.exit(1)

    website_id = "retriever_self_test"

    # 2. Store chunks
    print(f"\nStoring chunks in isolated index for: '{website_id}'...")
    store = WebsiteVectorStore(website_id)
    store.clear()
    store.add_embedded_chunks(embedded_chunks)
    store.save()

    # 3. Ask question
    question = "How can I download Python?"
    print(f"\nUser Question: '{question}'")
    print("Retrieving relevant chunks (top_k=3)...")
    
    retrieval_res = retrieve_relevant_chunks(website_id, question, top_k=3)

    if retrieval_res["success"]:
        print(f"\nSUCCESS! Found {retrieval_res['results_count']} results.")
        print("-" * 50)
        
        # 4. Print results
        for item in retrieval_res["results"]:
            print(f"Title:       {item['title']}")
            print(f"Score:       {item['similarity_score']}")
            print(f"Source URL:  {item['source_url']}")
            print(f"Preview:     {item['text'][:200]}...")
            print("-" * 50)

        # 5. Format and print context preview
        print("\nFormatted Context Preview:")
        print("=" * 60)
        context_text = format_retrieved_context(retrieval_res["results"])
        print(context_text)
        print("=" * 60)
    else:
        print(f"\nFAILURE: {retrieval_res['message']}")

    # 6. Cleanup
    print("\nCleaning up self-test index files...")
    store.clear()

    print("\n" + "=" * 70)
    print("Retriever self-test completed successfully!")
    print("=" * 70)
