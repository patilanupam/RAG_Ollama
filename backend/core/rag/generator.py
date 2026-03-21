"""
generator.py — Generate answers using Ollama (DeepSeek, etc.)
with inline source citations.
"""

import ollama
from backend.core.config import OLLAMA_MODEL, OLLAMA_BASE_URL


def _client():
    """Return Ollama client (no auth - local daemon handles it)."""
    return ollama.Client(host=OLLAMA_BASE_URL)


def _build_prompt(query: str, chunks: list[dict], history: list[dict] | None = None) -> str:
    context_parts = []
    for i, chunk in enumerate(chunks, 1):
        source_label = chunk["source"]
        if chunk.get("page"):
            source_label += f", page {chunk['page']}"
        context_parts.append(f"[{i}] (Source: {source_label})\n{chunk['text']}")

    context = "\n\n---\n\n".join(context_parts)

    history_text = ""
    if history:
        turns = []
        for msg in history:
            role = "User" if msg["role"] == "user" else "Assistant"
            turns.append(f"{role}: {msg['content']}")
        history_text = "\n".join(turns)

    return f"""You are a smart, flexible document assistant. Your job is to answer questions accurately based on the documents provided.

## Core Rules
1. **Use the document context** to answer questions — always cite sources using [N] inline.
2. **Use conversation history** for personal/conversational questions (e.g. "what is my name?", "what did we discuss?") — never say the context doesn't contain personal info that was shared in chat.
3. **Be honest** — if the answer genuinely isn't in the documents or history, say so in one sentence, then offer what you do know that's related.
4. **Never invent facts** — only state what the documents actually say.

## Output Format
- Use **bold** for key terms and important points.
- Use bullet points or numbered lists when listing multiple items.
- Use headings (e.g. **Overview**, **Key Points**) for longer answers.
- Keep answers focused and well-structured — not too short, not padded.
- End with a citation summary if sources were used.

## Conversation History
{history_text if history_text else "(no previous messages)"}

## Document Context
{context}

## Current Question
{query}

## Answer
"""


def generate_answer(query: str, chunks: list[dict], history: list[dict] | None = None) -> dict:
    """
    Generate an answer for the query grounded in the retrieved chunks.

    Returns:
        {
          "answer": str,           # Model's response with [N] citations
          "sources": list[dict],   # the chunks used, with source/page info
        }
    """
    client = _client()
    prompt = _build_prompt(query, chunks, history)
    
    response = client.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}]
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
