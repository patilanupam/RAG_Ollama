"""
retriever.py — Embed a query and retrieve the top-k most relevant chunks.
"""

from backend.core.rag.embedder import embed_query
from backend.core.rag.vectorstore import query_chunks


def retrieve(query: str, k: int = 5, source_filter: str = None) -> list[dict]:
    """
    Embed the query and return top-k relevant chunks with metadata.

    Args:
        query: The search query
        k: Number of results to return
        source_filter: Optional filename to search within specific document

    Returns:
        List of dicts: {text, source, page, chunk_index, score}
    """
    query_emb = embed_query(query)
    return query_chunks(query_emb, k=k, source_filter=source_filter)
