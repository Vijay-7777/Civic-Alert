import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parent.parent / '.env')

# LLM Configuration - Ollama
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
# Recommended models under 3B for better reasoning:
# - qwen2.5:3b (Qwen2.5-3B-Instruct) - Best reasoning, multilingual
# - llama3.2:3b (Llama-3.2-3B-Instruct) - Good reasoning, well-supported
# - phi3:mini (Phi-3-mini 3.8B) - Excellent reasoning, slightly over 3B
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")

# Gemini API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "models/gemini-2.0-flash")
USE_GEMINI_API = os.getenv("USE_GEMINI_API", "false").lower() == "true"

# Agent Configuration
USE_LANGCHAIN_AGENT = os.getenv("USE_LANGCHAIN_AGENT", "false").lower() == "true"
USE_ADVANCED_AGENT = os.getenv("USE_ADVANCED_AGENT", "false").lower() == "true"

# Database Configuration - SQLite (same as frontend)
import os
from pathlib import Path

# Use absolute path to the database
BASE_DIR = Path(__file__).resolve().parent.parent.parent  # Go up to the project root
# Normalize DATABASE_PATH to an absolute path; prefer default under project when env is relative
_raw_db = os.getenv("DATABASE_PATH")
if _raw_db:
    _p = Path(_raw_db)
    if not _p.is_absolute():
        _p = (BASE_DIR / _raw_db).resolve()
    else:
        _p = _p.resolve()
    if _p.exists():
        DATABASE_PATH = str(_p)
    else:
        DATABASE_PATH = str((BASE_DIR / "frontend" / "data" / "crime_lens.db").resolve())
else:
    DATABASE_PATH = str((BASE_DIR / "frontend" / "data" / "crime_lens.db").resolve())

# Vector Database Configuration
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
QDRANT_COLLECTION = "issues"

# API Keys
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")

# Embeddings
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
