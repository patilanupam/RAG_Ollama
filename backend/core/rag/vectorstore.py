"""
vectorstore.py — Persistent ChromaDB vector store for RAG chunks.
"""

import hashlib
import chromadb
from chromadb.config import Settings
from backend.core.config import CHROMA_DIR

COLLECTION_NAME = "rag_chunks"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def _make_id(chunk: dict) -> str:
    """Stable deterministic ID from source + chunk_index."""
    key = f"{chunk['source']}::{chunk.get('page', '')}::{chunk['chunk_index']}"
    return hashlib.md5(key.encode()).hexdigest()


def add_chunks(chunks: list[dict], embeddings: list[list[float]]) -> int:
    """Add chunks + their embeddings to the collection. Returns count added."""
    collection = _get_collection()
    ids, docs, metas, embeds = [], [], [], []
    for chunk, emb in zip(chunks, embeddings):
        cid = _make_id(chunk)
        ids.append(cid)
        docs.append(chunk["text"])
        metas.append({
            "source": chunk["source"],
            "page": str(chunk.get("page") or ""),
            "chunk_index": chunk["chunk_index"],
            "token_count": chunk["token_count"],
        })
        embeds.append(emb)
    collection.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeds)
    return len(ids)


def query_chunks(query_embedding: list[float], k: int = 5, source_filter: str = None) -> list[dict]:
    """Return top-k chunks closest to the query embedding.
    
    Args:
        query_embedding: The query vector
        k: Number of results to return
        source_filter: Optional filename to filter by (e.g., "Counselling_pdf_india_gpt.pdf")
    """
    collection = _get_collection()
    
    # Build query parameters
    query_params = {
        "query_embeddings": [query_embedding],
        "n_results": min(k, collection.count() or 1),
        "include": ["documents", "metadatas", "distances"],
    }
    
    # Add source filter if specified
    if source_filter:
        query_params["where"] = {"source": source_filter}
    
    results = collection.query(**query_params)
    
    chunks = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": doc,
            "source": meta["source"],
            "page": meta["page"] or None,
            "chunk_index": meta["chunk_index"],
            "score": round(1 - dist, 4),  # cosine similarity
        })
    return chunks


def collection_count() -> int:
    """Return total number of chunks stored."""
    return _get_collection().count()


def clear_collection():
    """Delete all chunks (useful for re-indexing)."""
    global _collection
    if _client:
        _client.delete_collection(COLLECTION_NAME)
        _collection = None


def delete_chunks_by_source(source: str) -> int:
    """Delete all chunks from a specific document source."""
    collection = _get_collection()

    # Query all chunks from this source
    results = collection.get(
        where={"source": source},
        include=[]
    )

    if not results['ids']:
        return 0

    # Delete the chunks
    collection.delete(ids=results['ids'])
    return len(results['ids'])


def get_all_sources() -> list[dict]:
    """Get list of all unique document sources with their chunk counts."""
    collection = _get_collection()

    # Get all metadata
    results = collection.get(include=["metadatas"])

    if not results['metadatas']:
        return []

    # Count chunks per source
    source_counts = {}
    for meta in results['metadatas']:
        source = meta.get('source', 'unknown')
        source_counts[source] = source_counts.get(source, 0) + 1

    # Format as list
    return [
        {"source": source, "chunk_count": count}
        for source, count in sorted(source_counts.items())
    ]
