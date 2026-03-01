"""
vectorstore.py — Persistent ChromaDB vector store for RAG chunks.
"""

import hashlib
import chromadb
from chromadb.config import Settings

DB_PATH = "./chroma_db"
COLLECTION_NAME = "rag_chunks"

_client = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=DB_PATH)
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


def query_chunks(query_embedding: list[float], k: int = 5) -> list[dict]:
    """Return top-k chunks closest to the query embedding."""
    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(k, collection.count() or 1),
        include=["documents", "metadatas", "distances"],
    )
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
