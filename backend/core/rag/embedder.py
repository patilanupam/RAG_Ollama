"""
embedder.py — Embed text using Ollama (local daemon proxies cloud when needed).
"""

import ollama
from backend.core.config import OLLAMA_EMBED_MODEL, OLLAMA_BASE_URL


def _client():
    """Return Ollama client (no auth - local daemon handles it)."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def embed_texts(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    """Return a list of embedding vectors for the given texts.
    Uses batch API call for much faster processing.
    Processes in batches to avoid context length errors with large files.
    Increased batch_size to 100 for faster large file processing.
    """
    if not texts:
        return []

    client = _client()
    all_embeddings = []

    # Process in batches to avoid overwhelming the embedding model
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        try:
            response = client.embed(model=OLLAMA_EMBED_MODEL, input=batch)
            all_embeddings.extend(response['embeddings'])
            # Progress indicator for large files
            progress = ((i + len(batch)) / len(texts)) * 100
            print(f"[Embedder] Progress: {progress:.0f}% ({i+len(batch)}/{len(texts)} chunks)")
        except Exception as e:
            error_msg = str(e)
            if "context length" in error_msg or "400" in error_msg:
                print(f"[Embedder] Batch too large, retrying with smaller batches...")
                # Retry with smaller batch size
                for text in batch:
                    try:
                        response = client.embed(model=OLLAMA_EMBED_MODEL, input=[text])
                        all_embeddings.extend(response['embeddings'])
                    except Exception as e2:
                        print(f"[Embedder] Failed to embed text (length: {len(text)}): {e2}")
                        # Use zero vector as fallback
                        all_embeddings.append([0.0] * 768)  # nomic-embed-text dimension
            else:
                raise

    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string."""
    client = _client()
    response = client.embed(model=OLLAMA_EMBED_MODEL, input=query)
    return response['embeddings'][0]
