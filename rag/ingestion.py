"""
ingestion.py — Load documents from PDF, Markdown files, or web URLs.
Returns a list of {"text": str, "source": str, "page": int | None}.

PDF extraction chain:
  1. pymupdf (fitz)  — fast, handles most PDFs
  2. pypdf            — fallback for pages fitz misses
  3. Tesseract OCR    — last resort for scanned/image-only pages
"""

import logging
import pathlib
import requests
from bs4 import BeautifulSoup
from pypdf import PdfReader
import fitz  # pymupdf

# Suppress pypdf encoding warnings (e.g. /SymbolSetEncoding not implemented)
logging.getLogger("pypdf").setLevel(logging.ERROR)

# ── OCR setup ────────────────────────────────────────────────────
_OCR_AVAILABLE = False
try:
    import pytesseract
    from pdf2image import convert_from_path
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    # Quick smoke-test
    pytesseract.get_tesseract_version()
    _OCR_AVAILABLE = True
    logging.info("OCR: Tesseract ready ✓")
except Exception as _e:
    logging.warning(f"OCR: Tesseract not available ({_e}) — scanned pages will be skipped")


def _ocr_page(file_path: str, page_number: int) -> str:
    """Render a single PDF page to an image and OCR it. page_number is 1-based."""
    try:
        images = convert_from_path(
            file_path, dpi=300,
            first_page=page_number, last_page=page_number,
            poppler_path=None  # use PATH
        )
        if images:
            return pytesseract.image_to_string(images[0]).strip()
    except Exception as e:
        logging.warning(f"OCR failed on page {page_number} of {file_path}: {e}")
    return ""


def load_pdf(file_path: str) -> list[dict]:
    """Extract text page-by-page from a PDF file.
    Chain: pymupdf → pypdf → Tesseract OCR (if installed).
    """
    docs = []
    fitz_doc = fitz.open(file_path)
    for i, fitz_page in enumerate(fitz_doc):
        text = fitz_page.get_text("text").strip()

        if not text:
            # Fallback 1: pypdf
            try:
                reader = PdfReader(file_path)
                if i < len(reader.pages):
                    text = (reader.pages[i].extract_text() or "").strip()
            except Exception:
                pass

        if not text and _OCR_AVAILABLE:
            # Fallback 2: OCR the rendered page image
            logging.info(f"OCR: running on page {i + 1} of {file_path}")
            text = _ocr_page(file_path, i + 1)

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
