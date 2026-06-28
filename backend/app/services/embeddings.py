import numpy as np
from sentence_transformers import SentenceTransformer

# Load the model lazily to save memory during import
_model = None

def get_model():
    global _model
    if _model is None:
        # This will download the model weights on first run if not cached
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model

def create_embedding(text: str, task_type: str = None) -> list[float]:
    """
    Creates a 384-dimensional normalized float32 vector for a single text string.
    The task_type argument is ignored but kept for compatibility.
    """
    model = get_model()
    # SentenceTransformer encodes and returns a numpy array
    embedding = model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
    # Convert numpy array of float32 to a standard python list of floats
    return embedding.tolist()

def create_embeddings(texts: list[str], batch_size: int = 32, task_type: str = None) -> list[list[float]]:
    """
    Creates embeddings for a list of text strings using batching.
    The task_type argument is ignored but kept for compatibility.
    """
    model = get_model()
    # encode handles batching internally if batch_size is specified
    embeddings = model.encode(texts, batch_size=batch_size, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings.tolist()
