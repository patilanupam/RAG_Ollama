"""
chunker.py — Split raw document text into overlapping token-bounded chunks.

Target: 500–700 tokens per chunk, ~100 token overlap.
Uses tiktoken (cl100k_base) for accurate token counting.
"""

import tiktoken

TOKENIZER = tiktoken.get_encoding("cl100k_base")
CHUNK_SIZE = 600      # target tokens per chunk
CHUNK_OVERLAP = 100   # overlap tokens between consecutive chunks


def _tokenize(text: str) -> list[int]:
    return TOKENIZER.encode(text)


def _decode(tokens: list[int]) -> str:
    return TOKENIZER.decode(tokens)


def chunk_document(doc: dict) -> list[dict]:
    """
    Split a single document dict into chunks.
    Each chunk inherits source/page metadata and gets a chunk_index.
    """
    tokens = _tokenize(doc["text"])
    chunks = []
    start = 0
    index = 0
    while start < len(tokens):
        end = min(start + CHUNK_SIZE, len(tokens))
        chunk_tokens = tokens[start:end]
        chunk_text = _decode(chunk_tokens)
        chunks.append({
            "text": chunk_text,
            "source": doc["source"],
            "page": doc.get("page"),
            "chunk_index": index,
            "token_count": len(chunk_tokens),
        })
        index += 1
        if end == len(tokens):
            break
        start = end - CHUNK_OVERLAP  # slide back for overlap
    return chunks


def chunk_documents(docs: list[dict]) -> list[dict]:
    """Chunk a list of document dicts."""
    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunk_document(doc))
    return all_chunks
