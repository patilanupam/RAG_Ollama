"""
server.py — FastAPI backend for Ask Me Anything RAG system
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Import from backend modules
from backend.core.rag.ingestion import load_document
from backend.core.rag.chunker import chunk_documents
from backend.core.rag.embedder import embed_texts
from backend.core.rag.vectorstore import (
    add_chunks, collection_count, clear_collection,
    delete_chunks_by_source, get_all_sources
)
from backend.core.rag.retriever import retrieve
from backend.core.rag.generator import generate_answer
from backend.services.health import get_system_health
from backend.database.manager import get_db
from backend.services.file_manager import (
    save_uploaded_file, get_file_path, delete_document_file,
    get_all_stored_documents, get_storage_stats, calculate_file_hash
)

app = FastAPI(title="Ask Me Anything", version="1.0.0")

# Mount static files from frontend directory
STATIC_DIR = Path(__file__).parent.parent.parent / "frontend" / "static"
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

_chat_history: list[dict] = []


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    get_db()
    print("Document database initialized")


@app.get("/")
def serve_ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/status")
def status():
    try:
        return {"chunk_count": collection_count()}
    except Exception as e:
        return {"chunk_count": 0, "error": str(e)}


@app.get("/api/health")
def health():
    """System health check - checks Ollama, ChromaDB, and models."""
    return get_system_health()


@app.get("/api/files")
def list_data_files():
    try:
        data_dir = Path("./storage/data")
        if not data_dir.exists():
            return {"files": []}
        exts = {".pdf", ".md", ".markdown", ".txt"}
        return {"files": [f.name for f in sorted(data_dir.glob("*")) if f.suffix.lower() in exts]}
    except Exception as e:
        return {"files": [], "error": str(e)}


@app.post("/api/clear")
def clear_all():
    global _chat_history
    clear_collection()
    _chat_history = []
    return {"ok": True}


@app.post("/api/ingest/file")
async def ingest_file(file: UploadFile = File(...)):
    """Upload and ingest a file. Stores file permanently and tracks in database."""
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".md", ".markdown", ".txt"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")

    try:
        # Read file content
        file_content = await file.read()
        file_hash = calculate_file_hash(file_content)

        # Check if already uploaded
        db = get_db()
        existing_doc = db.get_document_by_hash(file_hash)

        if existing_doc:
            return {
                "ok": True,
                "status": "already_exists",
                "message": "Document already uploaded",
                "document": existing_doc,
                "chunks": existing_doc['chunk_count']
            }

        # Save file permanently
        result = save_uploaded_file(file_content, file.filename, suffix)

        # Process document
        doc_info = result['document']
        file_path = Path(doc_info['file_path'])

        docs = load_document(str(file_path))
        chunks = chunk_documents(docs)
        for c in chunks:
            c["source"] = file.filename

        embs = embed_texts([c["text"] for c in chunks])
        count = add_chunks(chunks, embs)

        # Update chunk count in database
        db.update_chunk_count(file_hash, count)

        return {
            "ok": True,
            "status": "uploaded",
            "chunks": count,
            "source": file.filename,
            "document": doc_info
        }
    except Exception as e:
        raise HTTPException(500, str(e))


class URLReq(BaseModel):
    url: str


@app.post("/api/ingest/url")
def ingest_url(req: URLReq):
    try:
        docs = load_document(req.url)
        chunks = chunk_documents(docs)
        embs = embed_texts([c["text"] for c in chunks])
        count = add_chunks(chunks, embs)
        return {"ok": True, "chunks": count, "source": req.url}
    except Exception as e:
        raise HTTPException(500, str(e))


class DataFileReq(BaseModel):
    filename: str


@app.post("/api/ingest/datafile")
def ingest_datafile(req: DataFileReq):
    path = Path("./storage/data") / req.filename
    if not path.exists():
        raise HTTPException(404, "File not found in data/ folder")
    try:
        docs = load_document(str(path))
        chunks = chunk_documents(docs)
        embs = embed_texts([c["text"] for c in chunks])
        count = add_chunks(chunks, embs)
        return {"ok": True, "chunks": count, "source": req.filename}
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/documents")
def list_documents():
    """List all uploaded documents with metadata."""
    try:
        documents = get_all_stored_documents()
        stats = get_storage_stats()
        return {
            "documents": documents,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/documents/{doc_id}")
def get_document_info(doc_id: int):
    """Get detailed information about a specific document."""
    try:
        db = get_db()
        doc = db.get_document_by_id(doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")
        return doc
    except Exception as e:
        raise HTTPException(500, str(e))


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: int):
    """Delete a document and its chunks from the system."""
    try:
        db = get_db()
        doc = db.get_document_by_id(doc_id)
        if not doc:
            raise HTTPException(404, "Document not found")

        # Delete chunks from vector store
        chunks_deleted = delete_chunks_by_source(doc['original_filename'])

        # Delete file and database entry
        success = delete_document_file(doc_id)

        if not success:
            raise HTTPException(500, "Failed to delete document")

        return {
            "ok": True,
            "message": "Document deleted successfully",
            "chunks_deleted": chunks_deleted
        }
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/documents/stats")
def document_stats():
    """Get storage and document statistics."""
    try:
        return get_storage_stats()
    except Exception as e:
        raise HTTPException(500, str(e))


@app.get("/api/sources")
def list_sources():
    """List all unique document sources in the vector store."""
    try:
        sources = get_all_sources()
        return {"sources": sources}
    except Exception as e:
        raise HTTPException(500, str(e))


class ChatReq(BaseModel):
    message: str
    top_k: int = 5
    source_filter: str = None  # Optional: filter by specific document filename


@app.post("/api/chat")
def chat(req: ChatReq):
    global _chat_history
    try:
        if collection_count() == 0:
            return {
                "answer": "Please ingest some documents first so I can help you! 📄",
                "sources": [], "chunks": [],
            }
        chunks = retrieve(req.message, k=req.top_k, source_filter=req.source_filter)
        if not chunks:
            ans = "I couldn't find relevant information in your documents. Could you rephrase your question?"
            _chat_history += [{"role": "user", "content": req.message}, {"role": "assistant", "content": ans}]
            return {"answer": ans, "sources": [], "chunks": []}

        result = generate_answer(req.message, chunks, history=_chat_history[-10:])
        _chat_history += [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": result["answer"]},
        ]
        return {
            "answer": result["answer"],
            "sources": result["sources"],
            "chunks": [
                {"text": c["text"][:500], "source": c["source"],
                 "page": c.get("page"), "score": c.get("score")}
                for c in chunks
            ],
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
