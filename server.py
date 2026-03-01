"""
server.py — FastAPI backend for Counsellor Expert RAG system.
Run: uvicorn server:app --reload --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import tempfile, os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

_key = os.getenv("GOOGLE_API_KEY", "")
print(f"[startup] GOOGLE_API_KEY loaded: {_key[:12]}... (len={len(_key)})")

from rag.ingestion import load_document
from rag.chunker import chunk_documents
from rag.embedder import embed_texts
from rag.vectorstore import add_chunks, collection_count, clear_collection
from rag.retriever import retrieve
from rag.generator import generate_answer

app = FastAPI(title="Ask Me Anything")
app.mount("/static", StaticFiles(directory="static"), name="static")

_chat_history: list[dict] = []


@app.get("/")
def serve_ui():
    return FileResponse("static/index.html")


@app.get("/api/status")
def status():
    try:
        return {"chunk_count": collection_count()}
    except Exception as e:
        return {"chunk_count": 0, "error": str(e)}


@app.get("/api/files")
def list_data_files():
    try:
        data_dir = Path("./data")
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
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".pdf", ".md", ".markdown", ".txt"}:
        raise HTTPException(400, f"Unsupported file type: {suffix}")
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        docs = load_document(tmp_path)
        chunks = chunk_documents(docs)
        for c in chunks:
            c["source"] = file.filename
        embs = embed_texts([c["text"] for c in chunks])
        count = add_chunks(chunks, embs)
        return {"ok": True, "chunks": count, "source": file.filename}
    except Exception as e:
        raise HTTPException(500, str(e))
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


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
    path = Path("./data") / req.filename
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


class ChatReq(BaseModel):
    message: str
    top_k: int = 5


@app.post("/api/chat")
def chat(req: ChatReq):
    global _chat_history
    try:
        if collection_count() == 0:
            return {
                "answer": "Please ingest some documents first so I can help you! 📄",
                "sources": [], "chunks": [],
            }
        chunks = retrieve(req.message, k=req.top_k)
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
