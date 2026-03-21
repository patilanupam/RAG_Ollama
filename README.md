# Ask Me Anything - RAG System

A Retrieval-Augmented Generation (RAG) system that lets you chat with your documents using AI.

## Features

- 📄 **Multiple document formats**: PDF, Markdown, TXT, Web URLs
- 🔍 **Smart search**: Vector-based semantic search using ChromaDB
- 🤖 **Powered by DeepSeek**: Uses Ollama with DeepSeek v3.1 for high-quality answers
- 💬 **Chat memory**: Remembers your conversation context
- 🎨 **Clean UI**: Modern chat interface with dark/light mode
- 📊 **OCR support**: Reads text from scanned documents
- 📚 **Source citations**: Every answer includes references

---

## Quick Start

### 1. Prerequisites

- **Python 3.11+**
- **Ollama** (for running AI models)

### 2. Install Ollama

Download and install from: https://ollama.com/download

After installation, sign in and pull the required models:

```bash
ollama signin
ollama pull deepseek-v3.1:671b-cloud
ollama pull nomic-embed-text
```

### 3. Install Python Dependencies

```bash
cd RAG_Drive
pip install -r requirements.txt
```

### 4. Configure Environment

The `.env` file is already set up for local Ollama:

```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
OLLAMA_EMBED_MODEL=nomic-embed-text
```

No API key needed when using local Ollama!

### 5. Run the Server

**Option A: Using run.py (recommended)**
```bash
python run.py
```

**Option B: Direct uvicorn (for monitoring/development)**
```bash
uvicorn backend.api.server:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-restart when you change code files.

### 6. Open in Browser

Go to: **http://localhost:8000**

---

## Usage

### Upload Documents

1. **Upload files**: Click "Choose File" or drag & drop PDFs/Markdown/TXT files
2. **Web URLs**: Enter a URL in the URL field and click "Ingest URL"
3. **From data/ folder**: Place files in `storage/data/` and select from the dropdown

Documents are stored persistently - you only need to upload once!

### Ask Questions

Type your question in the chat box. The AI will:
- Search your documents for relevant information
- Generate an answer with inline citations like [1], [2]
- Show source documents with page numbers
- Remember your conversation for follow-up questions

### Manage Documents

- View all uploaded documents in the "Uploaded Documents" section
- Delete individual documents by clicking the delete button
- Clear all data using the "Clear" button (removes all documents and chat history)

---

## Project Structure

```
RAG_Drive/
├── run.py                     # Application entry point
├── .env                       # Configuration (Ollama settings)
├── requirements.txt           # Python dependencies
│
├── backend/                   # Backend application
│   ├── api/
│   │   └── server.py          # FastAPI routes & endpoints
│   ├── core/
│   │   ├── config.py          # Centralized configuration
│   │   └── rag/               # RAG pipeline modules
│   │       ├── ingestion.py   # PDF/Markdown/URL loaders
│   │       ├── chunker.py     # Text splitting with overlap
│   │       ├── embedder.py    # Ollama embeddings
│   │       ├── vectorstore.py # ChromaDB vector database
│   │       ├── retriever.py   # Semantic search
│   │       └── generator.py   # Answer generation
│   ├── database/
│   │   └── manager.py         # SQLite document database
│   └── services/
│       ├── file_manager.py    # File upload & storage
│       └── health.py          # System health checks
│
├── frontend/                  # Frontend UI
│   └── static/
│       ├── index.html         # Main page
│       ├── css/
│       │   └── style.css      # Styling
│       └── js/
│           └── app.js         # JavaScript logic
│
├── storage/                   # Auto-created on first run
│   ├── data/                  # Manual document storage
│   ├── uploads/               # Uploaded documents (persistent)
│   ├── chroma_db/             # Vector database
│   ├── logs/                  # Application logs
│   └── documents.db           # Document metadata (SQLite)
│
└── tests/                     # Test files
```

---

## Configuration

### Change AI Model

Edit `.env` and change `OLLAMA_MODEL` to any supported model:

```env
# Cloud models (require signin)
OLLAMA_MODEL=deepseek-v3.1:671b-cloud
OLLAMA_MODEL=gpt-oss:120b-cloud

# Local models (faster, free)
OLLAMA_MODEL=qwen3:30b
OLLAMA_MODEL=gemma3:27b
```

Then pull the model: `ollama pull <model-name>`

### Change Embedding Model

```env
OLLAMA_EMBED_MODEL=nomic-embed-text
```

### Adjust Chunk Size

Edit `backend/core/config.py`:

```python
CHUNK_SIZE = 600      # tokens per chunk
CHUNK_OVERLAP = 100   # overlap between chunks
```

---

## Troubleshooting

### "Failed to connect to Ollama"

Make sure Ollama is running:
- **Windows**: Check system tray for Ollama icon
- **Mac/Linux**: Run `ollama serve` in terminal

### "Model not found"

Pull the model first:
```bash
ollama pull deepseek-v3.1:671b-cloud
ollama pull nomic-embed-text
```

### "Collection expecting embedding with dimension X"

Your database has old embeddings. Clear it by clicking the "Clear" button in the UI, or delete the `storage/` folder and restart the server.

### Slow processing

- **For cloud models**: Speed depends on internet connection
- **For large PDFs**: OCR takes time on scanned pages
- **First run**: Models need to load into memory

---

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **AI Models**: DeepSeek v3.1 (via Ollama)
- **Embeddings**: Nomic Embed Text (768 dimensions)
- **Vector DB**: ChromaDB
- **OCR**: Tesseract + pdf2image
- **Frontend**: Vanilla HTML/CSS/JavaScript

---

## License

MIT License - feel free to use this for your projects!

---

## Need Help?

- **Ollama Docs**: https://docs.ollama.com
- **DeepSeek Models**: https://ollama.com/library/deepseek-v3.1
- **ChromaDB**: https://docs.trychroma.com
