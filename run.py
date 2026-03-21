"""
run.py - Entry point for the RAG application
"""

import uvicorn
from backend.core.config import HOST, PORT, DEBUG

if __name__ == "__main__":
    print("Starting Ask Me Anything RAG Server...")
    print(f"Server running at http://{HOST}:{PORT}")
    print("Open http://localhost:8000 in your browser")

    # Enable reload for development (watches for file changes)
    reload_enabled = True  # Change to False for production

    if reload_enabled:
        print("Auto-reload enabled - server will restart on code changes")
    print("Press CTRL+C to stop\n")

    uvicorn.run(
        "backend.api.server:app",
        host=HOST,
        port=PORT,
        reload=reload_enabled,
        log_level="info"
    )
