import os
from pathlib import Path
from dotenv import load_dotenv

# Define the base directory of the backend folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from the .env file if it exists
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)

# Retrieve configuration variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")

# Validate configuration
if not GEMINI_API_KEY or GEMINI_API_KEY.strip() == "" or GEMINI_API_KEY == "your_gemini_api_key_here":
    raise ValueError(
        "Configuration Error: GEMINI_API_KEY is missing or invalid in your .env file.\n"
        "Please perform the following steps:\n"
        "  1. Copy '.env.example' to '.env' inside the 'backend' folder.\n"
        "  2. Replace 'your_gemini_api_key_here' with your real API key from Google AI Studio (https://aistudio.google.com/)."
    )

# Playwright Fallback Configurations
DYNAMIC_PAGE_TEXT_THRESHOLD = int(os.getenv("DYNAMIC_PAGE_TEXT_THRESHOLD", "300"))
PLAYWRIGHT_TIMEOUT_MS = int(os.getenv("PLAYWRIGHT_TIMEOUT_MS", "45000"))

# Vector Database Configurations
VECTOR_DATA_DIR = os.getenv("VECTOR_DATA_DIR", "data/indexes")

# Ollama Fallback Configurations
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
USE_OLLAMA_FALLBACK = os.getenv("USE_OLLAMA_FALLBACK", "true").lower() == "true"


