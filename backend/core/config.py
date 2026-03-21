"""
config.py - Centralized configuration management
"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# Paths (relative to project root)
DATA_DIR = Path("./storage/data")
CHROMA_DIR = Path("./storage/chroma_db")
LOGS_DIR = Path("./storage/logs")

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Ollama Configuration
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "deepseek-v3.1:671b-cloud")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")

# Chunking Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "600"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "100"))

# Retrieval Configuration
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "5"))
MAX_TOP_K = int(os.getenv("MAX_TOP_K", "10"))

# Conversation Configuration
MAX_HISTORY_TURNS = int(os.getenv("MAX_HISTORY_TURNS", "10"))

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# Supported file extensions
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}

# OCR Configuration (if you enable it)
ENABLE_OCR = os.getenv("ENABLE_OCR", "false").lower() == "true"
