"""
health.py - System health checks and diagnostics
"""
import ollama
from pathlib import Path
from backend.core.rag.vectorstore import collection_count
from backend.core.config import OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_EMBED_MODEL

def check_ollama_connection() -> dict:
    """Check if Ollama is accessible."""
    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        # Try to list models
        models = client.list()
        return {
            "status": "healthy",
            "models_available": len(models.get('models', [])),
            "base_url": OLLAMA_BASE_URL
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "base_url": OLLAMA_BASE_URL
        }

def check_models() -> dict:
    """Check if required models are available."""
    try:
        client = ollama.Client(host=OLLAMA_BASE_URL)
        models_list = client.list()
        available_models = [m.get('name', m.get('model', '')) for m in models_list.get('models', [])]

        return {
            "generation_model": {
                "name": OLLAMA_MODEL,
                "available": any(OLLAMA_MODEL in m for m in available_models)
            },
            "embedding_model": {
                "name": OLLAMA_EMBED_MODEL,
                "available": any(OLLAMA_EMBED_MODEL in m for m in available_models)
            },
            "all_models": available_models
        }
    except Exception as e:
        return {"error": str(e)}

def check_vector_store() -> dict:
    """Check ChromaDB status."""
    try:
        count = collection_count()
        return {
            "status": "healthy",
            "chunk_count": count,
            "initialized": True
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "initialized": False
        }

def check_data_directory() -> dict:
    """Check data directory status."""
    data_dir = Path("./storage/data")
    if not data_dir.exists():
        return {"status": "missing", "path": str(data_dir)}

    files = list(data_dir.glob("*"))
    return {
        "status": "healthy",
        "path": str(data_dir),
        "file_count": len(files),
        "files": [f.name for f in files[:10]]  # First 10 files
    }

def get_system_health() -> dict:
    """Run all health checks and return combined status."""
    return {
        "ollama": check_ollama_connection(),
        "models": check_models(),
        "vector_store": check_vector_store(),
        "data_directory": check_data_directory()
    }
