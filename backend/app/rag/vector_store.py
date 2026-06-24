import os
import json
import re
import sys
from pathlib import Path
import numpy as np
import faiss

# Add the parent directory of this file to sys.path to support running this script directly
parent_dir = Path(__file__).resolve().parent.parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from app import config

def sanitize_website_id(website_id: str) -> str:
    """
    Sanitizes website_id to prevent directory/path traversal vulnerabilities
    and restricts folder name characters to alphanumeric, dots, underscores, and hyphens.
    """
    if not website_id:
        raise ValueError("website_id cannot be empty or null.")

    # Reject explicit path traversal characters
    if ".." in website_id or "/" in website_id or "\\" in website_id:
        raise ValueError("Invalid website_id: path traversal sequences ('..', '/', '\\') are not allowed.")

    # Strip out any remaining unsafe characters
    sanitized = re.sub(r"[^a-zA-Z0-9_\-\.]", "", website_id)
    if not sanitized:
        raise ValueError("Invalid website_id: contains no valid alphanumeric or allowed punctuation characters.")

    return sanitized

class WebsiteVectorStore:
    def __init__(self, website_id: str):
        self.website_id = sanitize_website_id(website_id)

        # Resolve storage directory relative to VECTOR_DATA_DIR configuration
        base_dir = Path(config.VECTOR_DATA_DIR)
        if not base_dir.is_absolute():
            base_dir = Path(config.BASE_DIR) / base_dir

        # Ensure VECTOR_DATA_DIR is created
        base_dir.mkdir(parents=True, exist_ok=True)

        self.storage_path = base_dir / self.website_id
        
        # Create directories automatically if they do not exist
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.index = None
        self.metadata_store = []

    def create_index(self, dimension: int) -> None:
        """Initializes a new FAISS Flat Inner Product index for Cosine Similarity search."""
        self.index = faiss.IndexFlatIP(dimension)
        self.metadata_store = []

    def add_embedded_chunks(self, embedded_chunks: list[dict]) -> dict:
        """
        Validates, normalizes, and appends embedded chunks to the FAISS index and metadata.
        Skips failed or missing embedding chunks.
        """
        if not embedded_chunks:
            return {
                "success": True,
                "vectors_added": 0,
                "skipped_chunks": 0,
                "dimension": self.index.d if self.index else 0,
                "message": "No chunks provided to add"
            }

        valid_chunks = []
        skipped_chunks = 0
        dimensions = set()

        for chunk in embedded_chunks:
            if not isinstance(chunk, dict):
                skipped_chunks += 1
                continue

            if "embedding_error" in chunk or "embedding" not in chunk:
                skipped_chunks += 1
                continue

            emb = chunk["embedding"]
            if not isinstance(emb, list) or not emb:
                skipped_chunks += 1
                continue

            dimensions.add(len(emb))
            valid_chunks.append(chunk)

        if not valid_chunks:
            return {
                "success": True,
                "vectors_added": 0,
                "skipped_chunks": skipped_chunks,
                "dimension": self.index.d if self.index else 0,
                "message": "No valid embedded chunks were found to add."
            }

        # Verify consistency of dimensions among incoming chunks
        if len(dimensions) > 1:
            return {
                "success": False,
                "vectors_added": 0,
                "skipped_chunks": len(embedded_chunks),
                "dimension": 0,
                "message": f"Inconsistent dimensions found in the input chunks: {list(dimensions)}"
            }

        chunk_dim = list(dimensions)[0]

        # Initialize index if it doesn't exist
        if self.index is None:
            self.create_index(chunk_dim)

        # Validate against existing index dimension
        if chunk_dim != self.index.d:
            return {
                "success": False,
                "vectors_added": 0,
                "skipped_chunks": len(embedded_chunks),
                "dimension": self.index.d,
                "message": f"Dimension mismatch: input chunks have dimension {chunk_dim}, but the index expects {self.index.d}."
            }

        # Convert list of floats to float32 NumPy array
        embeddings_matrix = np.array([chk["embedding"] for chk in valid_chunks], dtype=np.float32)

        # Normalize vectors to L2 norm (making IP index equivalent to Cosine Similarity)
        norms = np.linalg.norm(embeddings_matrix, axis=1, keepdims=True)
        norms = np.where(norms == 0, 1e-10, norms)  # Guard against divide-by-zero
        normalized_matrix = embeddings_matrix / norms

        # Add normalized vectors to FAISS
        self.index.add(normalized_matrix)

        # Store metadata (stripping out the raw vector to save space and prevent JSON clutter)
        for chk in valid_chunks:
            meta = {
                "chunk_id": chk.get("chunk_id", ""),
                "text": chk.get("text", ""),
                "source_url": chk.get("source_url", ""),
                "title": chk.get("title", ""),
                "heading": chk.get("heading", ""),
                "content_type": chk.get("content_type", "html"),
                "page_number": chk.get("page_number"),
                "chunk_index": chk.get("chunk_index", 0),
                "char_start": chk.get("char_start", 0),
                "char_end": chk.get("char_end", 0),
                "embedding_dimension": chk.get("embedding_dimension", chunk_dim)
            }
            if "embedding_error" in chk:
                meta["embedding_error"] = chk["embedding_error"]

            self.metadata_store.append(meta)

        return {
            "success": True,
            "vectors_added": len(valid_chunks),
            "skipped_chunks": skipped_chunks,
            "dimension": chunk_dim,
            "message": "Vectors added successfully"
        }

    def save(self) -> None:
        """Saves the FAISS index and chunk metadata JSON files to disk."""
        if self.index is None:
            return

        # Always safely recreate parent VECTOR_DATA_DIR and the storage path folder before saving
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        index_path = self.storage_path / "index.faiss"
        metadata_path = self.storage_path / "metadata.json"
        info_path = self.storage_path / "store_info.json"

        # Serialize FAISS index
        faiss.write_index(self.index, str(index_path))

        # Serialize metadata mapping
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self.metadata_store, f, indent=2, ensure_ascii=False)

        # Serialize indexing stats
        info = {
            "website_id": self.website_id,
            "dimension": self.index.d,
            "vector_count": self.index.ntotal,
            "storage_path": str(self.storage_path)
        }
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(info, f, indent=2, ensure_ascii=False)

    def load(self) -> bool:
        """Loads index and metadata files if they exist. Safely handles file corruption."""
        index_path = self.storage_path / "index.faiss"
        metadata_path = self.storage_path / "metadata.json"

        if not index_path.exists() or not metadata_path.exists():
            return False

        try:
            self.index = faiss.read_index(str(index_path))
            with open(metadata_path, "r", encoding="utf-8") as f:
                self.metadata_store = json.load(f)
            return True
        except Exception:
            # Handle corrupt/malformed files cleanly
            self.index = None
            self.metadata_store = []
            return False

    def get_stats(self) -> dict:
        """Returns statistics of the vector store index."""
        return {
            "website_id": self.website_id,
            "vector_count": self.index.ntotal if self.index else 0,
            "dimension": self.index.d if self.index else 0,
            "metadata_count": len(self.metadata_store),
            "storage_path": str(self.storage_path)
        }

    def clear(self) -> dict:
        """Deletes storage files and directories related *only* to this website."""
        try:
            index_path = self.storage_path / "index.faiss"
            metadata_path = self.storage_path / "metadata.json"
            info_path = self.storage_path / "store_info.json"

            # Remove index files if they exist
            for path in [index_path, metadata_path, info_path]:
                if path.exists():
                    path.unlink()

            # Remove website folder if it is now empty
            if self.storage_path.exists() and not list(self.storage_path.iterdir()):
                self.storage_path.rmdir()

            self.index = None
            self.metadata_store = []

            return {
                "success": True,
                "message": f"Local storage for website '{self.website_id}' cleared successfully."
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to clear storage files: {str(e)}"
            }

    def is_ready(self) -> bool:
        """Checks if index is loaded and holds vector keys."""
        return self.index is not None and len(self.metadata_store) > 0

if __name__ == "__main__":
    print("=" * 70)
    print("Running FAISS Vector Store self-tests...")
    print("=" * 70)

    from app.rag.embeddings import embed_chunks

    # 1. Create mock chunks directly
    raw_chunks = [
        {"chunk_index": 0, "text": "Python can be downloaded from the official downloads page.", "source_url": "https://fastapi.tiangolo.com"},
        {"chunk_index": 1, "text": "FastAPI is a modern web framework for building APIs with Python.", "source_url": "https://fastapi.tiangolo.com"},
        {"chunk_index": 2, "text": "FAISS is used for efficient vector similarity search.", "source_url": "https://fastapi.tiangolo.com"}
    ]

    print("Generating embeddings for test chunks...")
    try:
        embedded_chunks = embed_chunks(raw_chunks)
        print("Embeddings generated successfully.")
    except Exception as e:
        print(f"Embedding generation failed: {e}")
        sys.exit(1)

    website_id = "self_test_fastapi"

    # 2. Initialize and clear old data
    print(f"\nInitializing store for website: '{website_id}'...")
    store = WebsiteVectorStore(website_id)
    print("Clearing old self-test data...")
    store.clear()

    # 3. Add embedded chunks
    print("Adding embedded chunks to the FAISS index...")
    add_result = store.add_embedded_chunks(embedded_chunks)
    print(f"Result: {add_result}")

    # 4. Save to disk
    print("Saving vector index and metadata mapping to disk...")
    store.save()

    # 5. Print stats
    stats = store.get_stats()
    print(f"Stats after save: {stats}")

    # 6. Create a second instance and load from files
    print(f"\nCreating second instance for '{website_id}' and loading from files...")
    store2 = WebsiteVectorStore(website_id)
    load_success = store2.load()
    print(f"Load result: {load_success}")

    # 7. Verify stats consistency
    stats2 = store2.get_stats()
    print(f"Loaded instance stats: {stats2}")

    assert stats["vector_count"] == stats2["vector_count"], "Error: Vector count mismatch!"
    assert stats["metadata_count"] == stats2["metadata_count"], "Error: Metadata count mismatch!"
    print("\nSUCCESS: Vector count and metadata count match exactly!")

    # 8. Cleanup at the end
    print("\nCleaning up self-test data files...")
    clear_result = store2.clear()
    print(f"Cleanup result: {clear_result}")

    print("\n" + "=" * 70)
    print("FAISS Vector Store self-test completed successfully!")
    print("=" * 70)
