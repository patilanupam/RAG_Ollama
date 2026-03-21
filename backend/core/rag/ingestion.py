"""
ingestion.py — Load documents from PDF, Markdown files, or web URLs.
Returns a list of {"text": str, "source": str, "page": int | None}.
"""

import logging
import pathlib
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import fitz  # pymupdf — more robust PDF extraction

# Suppress pypdf encoding warnings (e.g. /SymbolSetEncoding not implemented)
logging.getLogger("pypdf").setLevel(logging.ERROR)


def load_pdf(file_path: str) -> list[dict]:
    """Extract text page-by-page from a PDF file.
    Uses pymupdf (fitz) as primary extractor; falls back to pypdf per-page.
    """
    docs = []
    fitz_doc = fitz.open(file_path)
    for i, fitz_page in enumerate(fitz_doc):
        text = fitz_page.get_text("text").strip()
        if not text:
            # Fallback: try pypdf for this page
            try:
                reader = PdfReader(file_path)
                if i < len(reader.pages):
                    text = (reader.pages[i].extract_text() or "").strip()
            except Exception:
                pass
        if text:
            docs.append({"text": text, "source": str(file_path), "page": i + 1})
    fitz_doc.close()
    return docs


def load_markdown(file_path: str) -> list[dict]:
    """Read a Markdown file as a single document."""
    text = pathlib.Path(file_path).read_text(encoding="utf-8")
    return [{"text": text, "source": str(file_path), "page": None}]


def load_url(url: str) -> list[dict]:
    """Fetch a web page and extract visible text via BeautifulSoup."""
    headers = {"User-Agent": "Mozilla/5.0 (RAG-bot)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # Remove script/style noise
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n", strip=True)
    return [{"text": text, "source": url, "page": None}]


def load_document(source: str) -> list[dict]:
    """Auto-detect source type and load accordingly."""
    if source.startswith("http://") or source.startswith("https://"):
        return load_url(source)
    path = pathlib.Path(source)
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return load_pdf(source)
    if suffix in (".md", ".markdown", ".txt"):
        return load_markdown(source)
    raise ValueError(f"Unsupported file type: {suffix!r}. Use PDF, Markdown, or a URL.")
