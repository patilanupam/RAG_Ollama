# 📁 Professional Project Structure

## New Organization

```
RAG_Drive/
├── backend/              # Backend application
│   ├── api/             # FastAPI application
│   │   ├── routes/      # API route handlers
│   │   └── server.py    # Main FastAPI app
│   ├── core/            # Core business logic
│   │   ├── config.py    # Configuration
│   │   └── rag/         # RAG pipeline
│   ├── database/        # Database layer
│   │   ├── models.py    # SQLite models
│   │   └── manager.py   # Database operations
│   └── services/        # Service layer
│       ├── file_manager.py
│       └── health.py
├── frontend/            # Frontend applications
│   ├── static/          # Static web UI
│   │   ├── js/
│   │   ├── css/
│   │   └── index.html
│   └── streamlit/       # Streamlit app
├── storage/             # Data storage
│   ├── uploads/         # Uploaded documents
│   ├── data/            # Static data
│   └── chroma_db/       # Vector database
├── docs/                # Documentation
├── tests/               # Test suite
├── logs/                # Application logs
├── .env                 # Environment config
├── .gitignore
├── requirements.txt
└── run.py               # Application entry point
```
