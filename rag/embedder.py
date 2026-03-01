"""
embedder.py — Embed text using Google's text-embedding-004 model.
"""

import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

EMBED_MODEL = "gemini-embedding-001"


def _client() -> genai.Client:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise EnvironmentError("GOOGLE_API_KEY not set. Copy .env.example to .env and add your key.")
    return genai.Client(api_key=api_key)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Return a list of embedding vectors for the given texts (document task).
    Sends in batches of 100 to respect the API limit.
    """
    client = _client()
    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i:i + 100]
        result = client.models.embed_content(
            model=EMBED_MODEL,
            contents=batch,
            config=types.EmbedContentConfig(task_type="retrieval_document"),
        )
        all_embeddings.extend([e.values for e in result.embeddings])
    return all_embeddings


def embed_query(query: str) -> list[float]:
    """Embed a single query string (query task type for better retrieval)."""
    client = _client()
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[query],
        config=types.EmbedContentConfig(task_type="retrieval_query"),
    )
    return result.embeddings[0].values
