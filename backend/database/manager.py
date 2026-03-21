"""
database.py - Document metadata database (SQLite)
Tracks uploaded documents, their status, and metadata
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import hashlib

# Database and upload paths (relative to project root)
DB_PATH = Path("./storage/documents.db")
UPLOAD_DIR = Path("./storage/uploads")

# Ensure directories exist
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


class DocumentDB:
    """Manage document metadata in SQLite database."""

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database schema."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                file_hash TEXT UNIQUE NOT NULL,
                file_path TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                file_type TEXT NOT NULL,
                chunk_count INTEGER DEFAULT 0,
                upload_date TEXT NOT NULL,
                last_accessed TEXT,
                status TEXT DEFAULT 'indexed',
                metadata TEXT
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_hash ON documents(file_hash)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_filename ON documents(filename)
        """)

        conn.commit()
        conn.close()

    def _get_connection(self):
        """Get database connection with Row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def add_document(
        self,
        original_filename: str,
        file_path: str,
        file_content: bytes,
        file_type: str,
        chunk_count: int = 0
    ) -> Dict:
        """Add a new document to the database."""
        # Calculate file hash to detect duplicates
        file_hash = hashlib.sha256(file_content).hexdigest()
        file_size = len(file_content)
        upload_date = datetime.now().isoformat()

        # Generate unique filename using hash prefix
        filename = f"{file_hash[:12]}_{Path(original_filename).name}"

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Check if document already exists
            cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
            existing = cursor.fetchone()

            if existing:
                # Update last_accessed
                cursor.execute(
                    "UPDATE documents SET last_accessed = ? WHERE file_hash = ?",
                    (upload_date, file_hash)
                )
                conn.commit()
                return dict(existing)

            # Insert new document
            cursor.execute("""
                INSERT INTO documents (
                    filename, original_filename, file_hash, file_path,
                    file_size, file_type, chunk_count, upload_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                filename, original_filename, file_hash, file_path,
                file_size, file_type, chunk_count, upload_date, 'indexed'
            ))

            doc_id = cursor.lastrowid
            conn.commit()

            # Return the inserted document
            cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
            return dict(cursor.fetchone())

        finally:
            conn.close()

    def get_document_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get document by file hash."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents WHERE file_hash = ?", (file_hash,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_document_by_id(self, doc_id: int) -> Optional[Dict]:
        """Get document by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()

        return dict(row) if row else None

    def get_all_documents(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get all documents with pagination."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM documents
            ORDER BY upload_date DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def update_chunk_count(self, file_hash: str, chunk_count: int):
        """Update chunk count for a document."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE documents SET chunk_count = ? WHERE file_hash = ?
        """, (chunk_count, file_hash))

        conn.commit()
        conn.close()

    def delete_document(self, doc_id: int) -> bool:
        """Delete a document from database."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get file path before deleting
        cursor.execute("SELECT file_path FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False

        file_path = Path(row['file_path'])

        # Delete from database
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
        conn.close()

        # Delete physical file
        if file_path.exists():
            file_path.unlink()

        return True

    def get_stats(self) -> Dict:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total_documents,
                SUM(file_size) as total_size,
                SUM(chunk_count) as total_chunks,
                COUNT(DISTINCT file_type) as unique_types
            FROM documents
        """)

        stats = dict(cursor.fetchone())
        conn.close()

        return stats

    def search_documents(self, query: str) -> List[Dict]:
        """Search documents by filename."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM documents
            WHERE original_filename LIKE ?
            ORDER BY upload_date DESC
        """, (f"%{query}%",))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]


# Global instance
_db_instance = None


def get_db() -> DocumentDB:
    """Get or create database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DocumentDB()
    return _db_instance
