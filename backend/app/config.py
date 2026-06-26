import os
from pathlib import Path
from dotenv import load_dotenv

# Define the base directory of the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path, override=True)

# Retrieve configuration variables
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_FALLBACK_API_KEY = os.getenv("GROQ_FALLBACK_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Validate configuration
if not GROQ_API_KEY or GROQ_API_KEY.strip() == "" or GROQ_API_KEY == "your_groq_api_key":
    raise ValueError(
        "Configuration Error: GROQ_API_KEY is missing or invalid in your .env file.\n"
        "Please ensure backend/.env contains your real API keys."
    )

# Playwright Fallback Configurations
DYNAMIC_PAGE_TEXT_THRESHOLD = int(os.getenv("DYNAMIC_PAGE_TEXT_THRESHOLD", "300"))
PLAYWRIGHT_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "45000"))

# Vector Database Configurations
VECTOR_DATA_DIR = os.getenv("VECTOR_DATA_DIR", "data/indexes")
RAG_MIN_RELEVANCE_SCORE = float(os.getenv("RAG_MIN_RELEVANCE_SCORE", "0.20"))


# Chunking Configurations
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "700"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))
MIN_CHUNK_LENGTH = int(os.getenv("MIN_CHUNK_LENGTH", "100"))

# Embedding Configurations
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "10"))

