"""
retriever.py — Embed a query and retrieve the top-k most relevant chunks.
Uses document-level re-ranking to prevent large documents from dominating results.
"""

from collections import defaultdict
from backend.core.rag.embedder import embed_query
from backend.core.rag.vectorstore import query_chunks


def retrieve(query: str, k: int = 5, source_filter: str = None, use_reranking: bool = True) -> list[dict]:
    """
    Embed the query and return top-k relevant chunks with metadata.

    Uses document-level re-ranking to ensure fair representation across documents
    when no source filter is applied.

    Args:
        query: The search query
        k: Number of results to return
        source_filter: Optional filename to search within specific document
        use_reranking: If True, applies document-level re-ranking for diversity

    Returns:
        List of dicts: {text, source, page, chunk_index, score}
    """
    query_emb = embed_query(query)

    # If filtering by document, no need for re-ranking
    if source_filter:
        return query_chunks(query_emb, k=k, source_filter=source_filter)

    # If re-ranking disabled, use simple retrieval
    if not use_reranking:
        return query_chunks(query_emb, k=k, source_filter=None)

    # DOCUMENT-LEVEL RE-RANKING:
    # Retrieve more chunks initially to get diverse document pool
    initial_k = min(k * 5, 100)  # 5x chunks, max 100
    candidates = query_chunks(query_emb, k=initial_k, source_filter=None)

    if not candidates:
        return []

    # Group chunks by document and calculate document-level scores
    doc_chunks = defaultdict(list)
    doc_scores = defaultdict(list)

    for chunk in candidates:
        doc_name = chunk["source"]
        doc_chunks[doc_name].append(chunk)
        doc_scores[doc_name].append(chunk["score"])

    # Calculate document relevance: max score + average score (hybrid metric)
    doc_relevance = {}
    for doc_name, scores in doc_scores.items():
        max_score = max(scores)
        avg_score = sum(scores) / len(scores)
        # Weighted: 70% max relevance, 30% average (favors documents with high-quality matches)
        doc_relevance[doc_name] = (max_score * 0.7) + (avg_score * 0.3)

    # Sort documents by relevance
    sorted_docs = sorted(doc_relevance.items(), key=lambda x: x[1], reverse=True)

    # DIVERSIFIED SELECTION: Distribute chunks across top documents
    result = []
    chunks_per_doc = max(2, k // min(len(sorted_docs), 3))  # At least 2 chunks per top doc

    # First pass: Take top chunks from each top document
    for doc_name, _ in sorted_docs[:3]:  # Top 3 documents
        doc_chunk_list = sorted(doc_chunks[doc_name], key=lambda x: x["score"], reverse=True)
        result.extend(doc_chunk_list[:chunks_per_doc])
        if len(result) >= k:
            break

    # Second pass: Fill remaining slots with highest-scoring chunks overall
    if len(result) < k:
        remaining_chunks = [c for c in candidates if c not in result]
        remaining_chunks.sort(key=lambda x: x["score"], reverse=True)
        result.extend(remaining_chunks[:k - len(result)])

    # Sort final results by score and return top-k
    result.sort(key=lambda x: x["score"], reverse=True)
    return result[:k]
