import sys
from pathlib import Path

# Add parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app.gemini_client import create_embedding, create_embeddings

def embed_chunk(chunk: dict, task_type: str = "retrieval_document") -> dict:
    """
    Accepts a single chunk dictionary from chunker.py.
    Generates a vector embedding for its 'text' content.
    Returns the modified dictionary with 'embedding' and 'embedding_dimension' fields.
    """
    if not chunk or not isinstance(chunk, dict):
        return {}

    # Make a copy to avoid mutating the input argument directly
    chunk_copy = dict(chunk)
    text = chunk_copy.get("text", "")
    
    try:
        embedding_vector = create_embedding(text, task_type=task_type)
        chunk_copy["embedding"] = embedding_vector
        chunk_copy["embedding_dimension"] = len(embedding_vector)
    except Exception as e:
        chunk_copy["embedding_error"] = str(e)
        
    return chunk_copy

def embed_chunks(chunks: list[dict], batch_size: int = 20, task_type: str = "retrieval_document") -> list[dict]:
    """
    Embeds a list of chunk dictionaries using batching for maximum efficiency.
    Preserves original chunk ordering. If a batch call fails, it falls back
    to embedding chunks within that batch individually so that single failures
    do not crash the entire process.
    """
    if not chunks:
        return []

    # Copy list elements to avoid modifying inputs
    result_chunks = [dict(c) for c in chunks]

    # Process in batches
    for i in range(0, len(result_chunks), batch_size):
        batch_slice = result_chunks[i : i + batch_size]
        batch_texts = [c.get("text", "") for c in batch_slice]

        try:
            # Batch API call
            embeddings_list = create_embeddings(batch_texts, batch_size=batch_size, task_type=task_type)
            
            # Map values back to slice
            for idx, emb in enumerate(embeddings_list):
                chunk = batch_slice[idx]
                chunk["embedding"] = emb
                chunk["embedding_dimension"] = len(emb)
                # Ensure no previous error key remains if retried
                chunk.pop("embedding_error", None)

        except Exception as batch_err:
            # Fall back to individual embedding for chunks in this batch
            for chunk in batch_slice:
                text = chunk.get("text", "")
                try:
                    emb = create_embedding(text, task_type=task_type)
                    chunk["embedding"] = emb
                    chunk["embedding_dimension"] = len(emb)
                    chunk.pop("embedding_error", None)
                except Exception as ind_err:
                    chunk["embedding_error"] = str(ind_err)
                    chunk.pop("embedding", None)
                    chunk.pop("embedding_dimension", None)

    return result_chunks

def validate_embedding_dimensions(embedded_chunks: list[dict]) -> dict:
    """
    Checks that successful embeddings all have the same dimension.
    Returns validation status, dimension size, and count statistics.
    """
    successful_chunks = 0
    failed_chunks = 0
    dimensions = set()

    for chunk in embedded_chunks:
        if "embedding_error" in chunk:
            failed_chunks += 1
        elif "embedding" in chunk:
            successful_chunks += 1
            dimensions.add(chunk.get("embedding_dimension", 0))
        else:
            # Handled as failed if neither error nor embedding is present
            failed_chunks += 1

    if not dimensions:
        return {
            "valid": False,
            "dimension": 0,
            "successful_chunks": successful_chunks,
            "failed_chunks": failed_chunks,
            "message": "No successful embeddings found to validate."
        }

    if len(dimensions) > 1:
        return {
            "valid": False,
            "dimension": list(dimensions),
            "successful_chunks": successful_chunks,
            "failed_chunks": failed_chunks,
            "message": f"Inconsistent embedding dimensions found: {list(dimensions)}"
        }

    dim = list(dimensions)[0]
    return {
        "valid": True,
        "dimension": dim,
        "successful_chunks": successful_chunks,
        "failed_chunks": failed_chunks,
        "message": "All embeddings have consistent dimensions"
    }

if __name__ == "__main__":
    print("=" * 70)
    print("Running Gemini Embeddings self-tests...")
    print("=" * 70)

    # Directly defined test chunks (Requirement 3)
    test_chunks = [
        {"chunk_index": 0, "text": "Python can be downloaded from the official downloads page."},
        {"chunk_index": 1, "text": "FastAPI is a modern web framework for building APIs with Python."},
        {"chunk_index": 2, "text": "FAISS is used for efficient vector similarity search."}
    ]

    print(f"Feeding {len(test_chunks)} test chunks to embed_chunks()...")
    
    embedded = embed_chunks(test_chunks)
    val_result = validate_embedding_dimensions(embedded)
    
    print("\n--- TEST RESULTS ---")
    print(f"Total Chunks:        {len(embedded)}")
    print(f"Successful Chunks:   {val_result['successful_chunks']}")
    print(f"Failed Chunks:       {val_result['failed_chunks']}")
    print(f"Embedding Dimension: {val_result['dimension']}")
    print(f"Validation Msg:      {val_result['message']}")
    
    if val_result["successful_chunks"] > 0:
        first_emb = embedded[0]["embedding"]
        print("\nSnippet of First Embedding (First 10 values):")
        print(f" {first_emb[:10]}")
    else:
        print("\nCould not display embedding snippet because embedding failed.")
        if "embedding_error" in embedded[0]:
            print(f" Error detail: {embedded[0]['embedding_error']}")
            
    print("\n" + "=" * 70)
    print("Self-test execution completed.")
    print("=" * 70)
