"""
file_manager.py - File storage and management utilities
Handles saving, loading, and managing uploaded documents
"""
import shutil
import hashlib
from pathlib import Path
from typing import Optional, BinaryIO
from backend.database.manager import get_db, UPLOAD_DIR


def save_uploaded_file(
    file_content: bytes,
    original_filename: str,
    file_type: str
) -> dict:
    """
    Save uploaded file to disk and add to database.
    Returns document metadata.
    """
    db = get_db()

    # Calculate file hash for deduplication
    file_hash = hashlib.sha256(file_content).hexdigest()

    # Check if file already exists
    existing_doc = db.get_document_by_hash(file_hash)
    if existing_doc:
        return {
            "status": "exists",
            "document": existing_doc,
            "message": "Document already uploaded"
        }

    # Create unique filename
    filename = f"{file_hash[:12]}_{Path(original_filename).name}"
    file_path = UPLOAD_DIR / filename

    # Save file to disk
    file_path.write_bytes(file_content)

    # Add to database
    doc = db.add_document(
        original_filename=original_filename,
        file_path=str(file_path),
        file_content=file_content,
        file_type=file_type,
        chunk_count=0  # Will be updated after processing
    )

    return {
        "status": "uploaded",
        "document": doc,
        "message": "Document uploaded successfully"
    }


def get_file_path(doc_id: int) -> Optional[Path]:
    """Get file path for a document by ID."""
    db = get_db()
    doc = db.get_document_by_id(doc_id)

    if not doc:
        return None

    file_path = Path(doc['file_path'])
    if not file_path.exists():
        return None

    return file_path


def get_file_path_by_hash(file_hash: str) -> Optional[Path]:
    """Get file path by file hash."""
    db = get_db()
    doc = db.get_document_by_hash(file_hash)

    if not doc:
        return None

    file_path = Path(doc['file_path'])
    if not file_path.exists():
        return None

    return file_path


def delete_document_file(doc_id: int) -> bool:
    """Delete document file and database entry."""
    db = get_db()
    return db.delete_document(doc_id)


def get_all_stored_documents() -> list:
    """Get all documents from database."""
    db = get_db()
    return db.get_all_documents()


def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA256 hash of file content."""
    return hashlib.sha256(file_content).hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_storage_stats() -> dict:
    """Get storage statistics."""
    db = get_db()
    stats = db.get_stats()

    # Format total size
    if stats['total_size']:
        stats['total_size_formatted'] = format_file_size(stats['total_size'])
    else:
        stats['total_size_formatted'] = "0 B"

    return stats
