"""
generator.py — Generate answers using Ollama (DeepSeek, etc.)
with inline source citations.

FIXED based on r/Rag best practices:
✅ Proper conversation memory (messages array, not single prompt)
✅ Simplified system prompt (10 lines, not 117)
✅ Document vs chunk counting (unique filenames)
✅ Context clarity (when to ask for clarification)
"""

import ollama
from backend.core.config import OLLAMA_MODEL, OLLAMA_BASE_URL


def _client():
    """Return Ollama client (no auth - local daemon handles it)."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def _build_messages(query: str, chunks: list[dict], history: list[dict] | None = None) -> list[dict]:
    """Build messages array with system prompt, history, and current query.
    
    Based on r/Rag best practices:
    - System role for consistent behavior
    - Full conversation history for memory
    - Clear document vs chunk distinction
    """
    
    # Count unique documents (not chunks!) - r/Rag best practice
    unique_docs = set(chunk["source"] for chunk in chunks)
    doc_count = len(unique_docs)
    chunk_count = len(chunks)
    
    # Build context from chunks
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = chunk["source"]
        if chunk.get("page"):
            source_label += f", page {chunk['page']}"
        context_parts.append(f"[{i}] (Source: {source_label})\n{chunk['text']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    # System prompt - SIMPLIFIED (r/Rag: don't over-instruct formatting)
    system_prompt = f"""You are a helpful document assistant. You have access to {doc_count} document(s) containing {chunk_count} text chunks.

CRITICAL RULES:
1. Answer ONLY using the provided document context
2. Always cite sources using [1], [2], [3] etc. from the context
3. If answer is not in context, say "I don't have that information in the documents"
4. When asked "how many documents", count unique filenames ({doc_count}), NOT chunks ({chunk_count})
5. You have full conversation history - reference previous questions naturally
6. If query is vague (like "what's in X.pdf?"), ask user to be specific about WHAT they want to know

FORMATTING:
- Use clear paragraphs with one blank line between them
- Use **bold** for key terms
- Use bullet points (•) for lists
- Use ## for section headings
- Keep responses well-structured and readable

NEVER say "I cannot see previous messages" - you have the full conversation history."""

    # Build messages array
    messages = [
        {"role": "system", "content": system_prompt}
    ]
    
    # Add conversation history if present (already pruned to last 10 in server.py)
    if history:
        messages.extend(history)
    
    # Add current query with document context
    user_message = f"""# DOCUMENT CONTEXT

{context}

# USER QUESTION
{query}

Answer using ONLY the information from the document context above. Cite sources with [1], [2], etc."""

    messages.append({"role": "user", "content": user_message})
    
    return messages


def generate_answer(query: str, chunks: list[dict], history: list[dict] | None = None) -> dict:
    """
    Generate an answer for the query grounded in the retrieved chunks.
    Uses proper message array format for conversation memory (r/Rag best practice).

    Args:
        query: User's question
        chunks: Retrieved document chunks with metadata
        history: Previous conversation messages (already pruned to last 10)

    Returns:
        {
          "answer": str,           # Model's response with [N] citations
          "sources": list[dict],   # the chunks used, with source/page info
        }
    """
    client = _client()
    messages = _build_messages(query, chunks, history)
    
    # Use messages array (NOT single prompt) for proper conversation memory
    # This is the KEY fix from r/Rag research
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=messages
    )
    
    answer_text = response['message']['content'].strip()

    # Build a deduplicated source list for the UI
    seen = set()
    sources = []
    for i, chunk in enumerate(chunks, 1):
        key = (chunk["source"], chunk.get("page"))
        if key not in seen:
            seen.add(key)
            sources.append({
                "index": i,
                "source": chunk["source"],
                "page": chunk.get("page"),
                "score": chunk.get("score"),
            })

    return {"answer": answer_text, "sources": sources}
