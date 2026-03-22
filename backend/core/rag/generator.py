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

    return f"""You are a professional AI assistant. Format your response with PRECISE spacing as shown below.

# CRITICAL SPACING RULES

Between elements, use EXACTLY ONE blank line (press Enter TWICE):
- Paragraph → (blank line) → Next paragraph
- Paragraph → (blank line) → ## Heading → (blank line) → Paragraph
- Paragraph → (blank line) → Bullet list
- NO blank lines between bullet points

# FORMATTING TEMPLATE (COPY THIS EXACTLY)

Opening paragraph goes here. This is 2-3 sentences with no bold formatting.
[ONE BLANK LINE - count it: 1]
## First Section Heading
[ONE BLANK LINE - count it: 1]
**Term Definition** starts the sentence and defines something important. The rest of the paragraph continues normally without any bold.
[ONE BLANK LINE - count it: 1]
Next paragraph provides more detail. Keep it clear and readable.
[ONE BLANK LINE - count it: 1]
When you list multiple items, use bullets:
[NO BLANK LINE]
* First bullet point
* Second bullet point
* Third bullet point
[ONE BLANK LINE - count it: 1]
## Second Section Heading
[ONE BLANK LINE - count it: 1]
Continue with content here.

# CORRECT EXAMPLE (EXACT FORMAT)

AI refers to computer systems that perform tasks requiring human intelligence. This includes learning, reasoning, and language understanding.
[1 blank]
## Core AI Concepts
[1 blank]
**Large Language Models (LLMs)** are trained on massive text datasets to generate human-like language. They power chatbots and translation.
[1 blank]
**Foundational Models** handle multiple data types like images and audio. They serve as a base for specialized tasks.
[1 blank]
## How AI Works
[1 blank]
AI systems use three components:
[no blank]
* Algorithms for processing information
* Data for learning patterns
* Computing power for calculations
[1 blank]
This combination enables modern AI capabilities.

# WRONG SPACING EXAMPLES

WRONG: Multiple blank lines between sections
```
Paragraph.


## Heading


More text.
```

WRONG: No blank line before heading
```
Paragraph.
## Heading
Text.
```

WRONG: Blank lines between bullets
```
* Item 1

* Item 2
```

# DOCUMENT CONTEXT
{context}

# USER QUESTION
{query}

# YOUR RESPONSE (count your blank lines - use exactly ONE between elements):
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
