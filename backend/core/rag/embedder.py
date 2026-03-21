"""
embedder.py — Embed text using Ollama (local daemon proxies cloud when needed).
"""

import ollama
from backend.core.config import OLLAMA_EMBED_MODEL, OLLAMA_BASE_URL


def _client():
    """Return Ollama client (no auth - local daemon handles it)."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return a list of embedding vectors for the given texts.
    Uses batch API call for much faster processing.
    """
    if not texts:
        return []
    
    client = _client()
    # Ollama embed() supports batch input
    response = client.embed(model=OLLAMA_EMBED_MODEL, input=texts)
    return response['embeddings']


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    client = _client()
    response = client.embed(model=OLLAMA_EMBED_MODEL, input=query)
    return response['embeddings'][0]
