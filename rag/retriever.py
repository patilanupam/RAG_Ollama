"""
retriever.py — Embed a query and retrieve the top-k most relevant chunks.
"""

from rag.embedder import embed_query
from rag.vectorstore import query_chunks


def retrieve(query: str, k: int = 5) -> list[dict]:
    """
    Embed the query and return top-k relevant chunks with metadata.
    Each returned dict: {text, source, page, chunk_index, score}
    """
    query_emb = embed_query(query)
    return query_chunks(query_emb, k=k)
