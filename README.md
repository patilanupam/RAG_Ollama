# 🧠 RAG Chatbot - Counsellor Expert

AI-powered document Q&A system. Upload documents, ask questions, get cited answers.

---

## ✨ Features

- 📄 **Multi-format**: PDF, Markdown, TXT, web URLs
- 🎨 **Dual UI**: Streamlit or FastAPI + Custom Frontend
- 🔍 **Smart Search**: Semantic search with ChromaDB
- 💬 **Memory**: Remembers last 10 conversation turns
- 📚 **Citations**: Every answer includes source references

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          USER INTERFACE                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   [Streamlit UI]          OR          [FastAPI + Frontend]           │
│   Port: 8501                          Port: 8000                     │
│                                                                       │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────────┐
│                          RAG PIPELINE                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [Ingestion] → [Chunker] → [Embedder] → [Vector Store]              │
│  PDF/MD/URL    600 tokens   Gemini API   ChromaDB                   │
│                100 overlap  768-dim                                  │
│                                                                       │
│                            ↓                                         │
│                                                                       │
│  [Retriever] → [Generator]                                           │
│  Top-K Search  Gemini 2.5 Flash                                     │
│                                                                       │
└────────────────────────────┬──────────────────────────────────────────┘
                             │
┌─────────────────────────────────────────────────────────────────────┐
│                    STORAGE & EXTERNAL SERVICES                       │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  [ChromaDB]         [Google Gemini API]         [Data Folder]       │
│  ./chroma_db/       Embeddings + Generation     ./data/             │
│  Persistent         768-dim vectors             Source Files         │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Flow Diagrams

### 1️⃣ Document Ingestion Flow

```
┌──────────────┐
│   Document   │  (PDF / Markdown / TXT / Web URL)
│  📕 📝 📄 🌐 │
└──────┬───────┘
       │
       ▼
┌─────────────────────────┐
│  📄 Text Extraction     │
│  ─────────────────────  │
│  • PyMuPDF for PDF      │
│  • BeautifulSoup for URL│
│  • Preserve metadata    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  ✂️  Text Chunking      │
│  ─────────────────────  │
│  • 600 tokens/chunk     │
│  • 100 token overlap    │
│  • tiktoken (cl100k)    │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  🔢 Embedding           │
│  ─────────────────────  │
│  • Gemini API call      │
│  • 768 dimensions       │
│  • Batch processing     │
└──────────┬──────────────┘
           │
           ▼
┌─────────────────────────┐
│  💾 Store in ChromaDB   │
│  ─────────────────────  │
│  • Cosine similarity    │
│  • Persistent storage   │
│  • Ready for retrieval  │
└─────────────────────────┘

⏱️  Time: ~5-10 seconds for 10-page PDF
```

---

### 2️⃣ Query Processing Flow

```
┌─────────────────────────┐
│  💬 User Question       │
│  "What is counselling?" │
└──────────┬──────────────┘
           │
           ├─────────────────────────┐
           │                         │
           ▼                         ▼
┌──────────────────────┐   ┌─────────────────┐
│  🔢 Embed Query      │   │ 💭 Conversation │
│  Gemini API          │   │    History      │
│  768-dim vector      │   │  (Last 10 turns)│
└──────────┬───────────┘   └────────┬────────┘
           │                        │
           ▼                        │
┌──────────────────────┐            │
│  🔍 Search ChromaDB  │            │
│  Cosine Similarity   │            │
│  Retrieve Top-K=5    │            │
└──────────┬───────────┘            │
           │                        │
           ▼                        │
┌──────────────────────┐            │
│  📄 Top 5 Chunks     │            │
│  Ranked by relevance │            │
└──────────┬───────────┘            │
           │                        │
           └────────┬───────────────┘
                    │
                    ▼
           ┌────────────────────┐
           │  📋 Build Context  │
           │  Query + Chunks +  │
           │     History        │
           └─────────┬──────────┘
                     │
                     ▼
           ┌────────────────────┐
           │  ✨ Generate       │
           │  Gemini 2.5 Flash  │
           │  With citations    │
           └─────────┬──────────┘
                     │
                     ▼
           ┌────────────────────┐
           │  💬 AI Response    │
           │  "Counselling is   │
           │   [1] ... [2] ..." │
           │                    │
           │  📚 Sources: [1]   │
           │  doc.pdf page 3    │
           └────────────────────┘

⏱️  Time: ~3-4 seconds per query
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

Create/edit `.env`:
```env
GOOGLE_API_KEY=your_api_key_here
```

🔑 Get free key: https://aistudio.google.com

### 3. Run Application

**Option A: Streamlit** (Beginner-friendly)
```bash
streamlit run app.py
```
→ Open http://localhost:8501

**Option B: FastAPI** (Production-ready)
```bash
uvicorn server:app --reload --port 8000
```
→ Open http://localhost:8000

### 4. Use It

1. 📤 Upload documents (sidebar/UI)
2. ⏳ Wait for indexing (~5-10s)
3. 💬 Ask questions
4. 📚 Get answers with citations

---

## 📁 Project Structure

```
RAG_Drive/
│
├── app.py                 # Streamlit UI
├── server.py             # FastAPI backend
├── requirements.txt      # Python dependencies
├── .env                  # API keys (SECRET - DO NOT COMMIT)
│
├── rag/                  # Core RAG modules
│   ├── ingestion.py      # Load PDF/MD/URL
│   ├── chunker.py        # Split text (tiktoken)
│   ├── embedder.py       # Gemini embeddings
│   ├── vectorstore.py    # ChromaDB operations
│   ├── retriever.py      # Semantic search
│   └── generator.py      # Answer generation
│
├── static/               # Frontend assets (FastAPI)
│   ├── index.html
│   ├── app.js
│   └── style.css
│
├── data/                 # Place your documents here
└── chroma_db/           # Vector database (auto-created)
```

---

## 🛠️ Technology Stack

```
┌─────────────────────────────────────────────────────────┐
│  Backend       │  Python 3.11+, FastAPI, Streamlit      │
├─────────────────────────────────────────────────────────┤
│  Vector DB     │  ChromaDB 0.5+ (local, persistent)     │
├─────────────────────────────────────────────────────────┤
│  Embeddings    │  Google Gemini (768 dimensions)        │
├─────────────────────────────────────────────────────────┤
│  LLM           │  Google Gemini 2.5 Flash               │
├─────────────────────────────────────────────────────────┤
│  PDF Parser    │  PyMuPDF + pypdf (fallback)            │
├─────────────────────────────────────────────────────────┤
│  Chunking      │  tiktoken (cl100k_base)                │
└─────────────────────────────────────────────────────────┘
```

---

## 🌐 API Endpoints (FastAPI)

```
GET    /api/status              → Get chunk count
GET    /api/files               → List data/ folder files
POST   /api/chat                → Send message, get answer
POST   /api/ingest/file         → Upload & ingest file
POST   /api/ingest/url          → Ingest from web URL
POST   /api/ingest/datafile     → Ingest from data/ folder
POST   /api/clear               → Clear all data
```

**Example**:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is counselling?", "top_k": 5}'
```

---

## ⚙️ Configuration

### Environment Variables
```env
GOOGLE_API_KEY=required              # Get from aistudio.google.com
GEMINI_MODEL=gemini-2.5-flash       # Optional: gemini-2.5-pro
```

### Adjust Chunking
Edit `rag/chunker.py`:
```python
CHUNK_SIZE = 600        # tokens per chunk
CHUNK_OVERLAP = 100     # overlap between chunks
```

### Retrieval Settings
- **Top-K**: 1-10 (adjustable in UI)
- **Recommended**: 5 for balance, 3 for speed

---

## ⚡ Performance Metrics

```
┌──────────────────────────────────────┬──────────────┐
│  Operation                           │  Time        │
├──────────────────────────────────────┼──────────────┤
│  PDF Ingestion (10 pages)            │  ~5-10s      │
│  Query Embedding                     │  ~0.5s       │
│  Vector Search (ChromaDB)            │  ~0.3s       │
│  Answer Generation (Gemini)          │  ~2-3s       │
├──────────────────────────────────────┼──────────────┤
│  Total Query Time                    │  ~3-4s       │
└──────────────────────────────────────┴──────────────┘

Capacity:
  • Documents: Unlimited (disk-limited)
  • Chunks: Millions (ChromaDB handles it efficiently)
  • Conversation History: Last 10 turns in memory
```

---

## 🐛 Troubleshooting

```
┌────────────────────────────────────────────────────────────────┐
│  Issue                         │  Solution                     │
├────────────────────────────────────────────────────────────────┤
│  GOOGLE_API_KEY not set        │  Add key to .env file         │
├────────────────────────────────────────────────────────────────┤
│  RESOURCE_EXHAUSTED / 429      │  Wait 24h or use gemini-pro   │
├────────────────────────────────────────────────────────────────┤
│  ChromaDB lock error           │  Close other app instances    │
├────────────────────────────────────────────────────────────────┤
│  Port already in use           │  Use --port 8001              │
└────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Deployment Guide

### ⚠️ Important: Storage Requirement

This app uses **local ChromaDB** storage (`./chroma_db/`) which requires **persistent disk**.

### ✅ Compatible Platforms

```
┌──────────────────────────┬──────────┬──────────────┬─────────────────┐
│  Platform                │  Cost    │  Persistent  │  Recommendation │
├──────────────────────────┼──────────┼──────────────┼─────────────────┤
│  Hugging Face Spaces     │  FREE    │  ✅ Yes      │  ⭐ Best free   │
├──────────────────────────┼──────────┼──────────────┼─────────────────┤
│  Fly.io                  │  FREE    │  ✅ Yes (3GB)│  ⭐ Excellent   │
├──────────────────────────┼──────────┼──────────────┼─────────────────┤
│  Render (Paid)           │  $7/mo   │  ✅ Yes      │  Production     │
├──────────────────────────┼──────────┼──────────────┼─────────────────┤
│  Railway                 │  ~$5 trial│ ✅ Yes      │  Testing        │
└──────────────────────────┴──────────┴──────────────┴─────────────────┘
```

### ❌ NOT Compatible

```
✗ Render Free Tier    → Ephemeral storage (data lost on restart)
✗ Vercel              → Serverless (no local storage)
✗ Netlify             → Serverless (no local storage)
```

### 🔄 For Serverless Platforms

Replace ChromaDB with cloud vector database:
- **Pinecone** (1M vectors free)
- **Weaviate Cloud** (free tier)
- **Supabase + pgvector** (free tier)

Modify `rag/vectorstore.py` to use cloud APIs.

---

## 🔒 Security Checklist

```
✅ .env file in .gitignore
✅ File upload validation by extension
✅ Frontend sanitizes markdown output
⚠️ No authentication (single-user design)
⚠️ Never commit .env to version control
```

---

## 📦 Dependencies

```python
# requirements.txt
google-genai>=1.0.0      # Gemini API
chromadb>=0.5.0          # Vector database
pypdf>=4.0.0             # PDF parsing
requests>=2.31.0         # HTTP client
beautifulsoup4>=4.12.0   # Web scraping
tiktoken>=0.7.0          # Tokenization
streamlit>=1.35.0        # UI framework
pymupdf>=1.24.0          # Robust PDF extraction
```

---

## 📄 License

Open source for educational and commercial use.

---

## 🙋 Need Help?

- 📖 Check Troubleshooting section above
- 🔧 [Google Gemini API Docs](https://ai.google.dev/)
- 🗄️ [ChromaDB Documentation](https://docs.trychroma.com/)

---

**Built with** ❤️ using **Google Gemini** + **ChromaDB** + **Python**
