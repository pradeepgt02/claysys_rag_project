import sys
from pathlib import Path

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.rag.retriever import retrieve_relevant_chunks
from app.rag.answer_generator import generate_rag_answer

def chat_with_website(
    website_id: str,
    question: str,
    top_k: int = 5
) -> dict:
    """
    Orchestrates website chat question answering:
    - Validates inputs.
    - Semantic search retrieval using FAISS.
    - Generates RAG grounded response using Gemini.
    - Keeps raw embedding coordinates and API keys concealed.
    """
    # A. Validate inputs
    if not website_id or website_id.strip() == "":
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "answer": "",
            "sources": [],
            "retrieved_chunks_count": 0,
            "used_context_fallback": False,
            "message": "Validation Error: website_id must not be empty."
        }

    if not question or question.strip() == "":
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "answer": "",
            "sources": [],
            "retrieved_chunks_count": 0,
            "used_context_fallback": False,
            "message": "Validation Error: question must not be empty."
        }

    if not (1 <= top_k <= 10):
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "answer": "",
            "sources": [],
            "retrieved_chunks_count": 0,
            "used_context_fallback": False,
            "message": "Validation Error: top_k must be between 1 and 10."
        }

    # B. Call retrieval query
    retrieval_result = retrieve_relevant_chunks(
        website_id=website_id,
        question=question,
        top_k=top_k
    )

    # C. Handle retrieval failures
    if not retrieval_result.get("success", False):
        return {
            "success": False,
            "website_id": website_id,
            "question": question,
            "answer": "",
            "sources": [],
            "retrieved_chunks_count": 0,
            "used_context_fallback": False,
            "message": "No indexed website data found for this website_id."
        }

    retrieved_chunks = retrieval_result.get("results", [])

    # D. Generate answer using grounded prompt context
    ans_result = generate_rag_answer(question, retrieved_chunks)

    # E. Combine details to output response payload
    return {
        "success": ans_result.get("success", False),
        "website_id": website_id,
        "question": question,
        "answer": ans_result.get("answer", ""),
        "sources": ans_result.get("sources", []),
        "retrieved_chunks_count": len(retrieved_chunks),
        "used_context_fallback": ans_result.get("used_context_fallback", False),
        "message": ans_result.get("message", "Answer generated successfully")
    }

if __name__ == "__main__":
    from app import config
    
    print("=" * 70)
    print("Running Chat Service self-tests...")
    print("=" * 70)
    
    test_id = "python_org_f830ae59"
    
    # Resolve indices directory
    base_dir = Path(config.VECTOR_DATA_DIR)
    if not base_dir.is_absolute():
        base_dir = Path(config.BASE_DIR) / base_dir
    index_path = base_dir / test_id / "index.faiss"
    
    if not index_path.exists():
        print(f"\n[ERROR] Website ID '{test_id}' does not exist.")
        print("Please run the ingestion service first to crawl and index the target website:")
        print("  python -m app.services.ingest_service")
        print("\nThen, rerun this self-test script.")
        print("=" * 70)
        sys.exit(0)

    # Test A: Known Question
    q_known = "How can I download Python?"
    print(f"\n[Test A] Question: '{q_known}'")
    ans_known = chat_with_website(test_id, q_known)
    
    print("\nResult:")
    print(f"Success:                 {ans_known['success']}")
    print(f"Answer:                  {ans_known['answer']}")
    print(f"Retrieved Chunks Count:  {ans_known['retrieved_chunks_count']}")
    print(f"Used Context Fallback:   {ans_known['used_context_fallback']}")
    print(f"Message:                 {ans_known['message']}")
    print("Sources:")
    for src in ans_known.get("sources", []):
        print(f" - Title: '{src.get('title')}' | URL: {src.get('url')}")

    # Test B: Unknown Question
    q_unknown = "What is the CEO salary of Python.org?"
    print(f"\n[Test B] Question: '{q_unknown}'")
    ans_unknown = chat_with_website(test_id, q_unknown)
    
    print("\nResult:")
    print(f"Success:                 {ans_unknown['success']}")
    print(f"Answer:                  {ans_unknown['answer']}")
    print(f"Retrieved Chunks Count:  {ans_unknown['retrieved_chunks_count']}")
    print(f"Used Context Fallback:   {ans_unknown['used_context_fallback']}")
    print(f"Message:                 {ans_unknown['message']}")
    print("Sources:")
    for src in ans_unknown.get("sources", []):
        print(f" - Title: '{src.get('title')}' | URL: {src.get('url')}")
        
    print("\n" + "=" * 70)
    print("Chat Service self-test completed!")
    print("=" * 70)
