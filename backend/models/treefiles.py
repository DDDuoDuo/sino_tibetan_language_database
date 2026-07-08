import os
import uuid
from db import get_connection
from typing import Optional, Dict
from werkzeug.utils import secure_filename

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads", "treefiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)

def _safe_file_path(stored_name: str) -> Optional[str]:
    """Resolve a DB stored_name inside UPLOAD_DIR without allowing path traversal."""
    if not stored_name:
        return None
    normalized = os.path.normpath(stored_name).replace("\\", "/")
    if normalized.startswith("../") or normalized == ".." or os.path.isabs(normalized):
        return None

    upload_root = os.path.abspath(UPLOAD_DIR)
    path = os.path.abspath(os.path.join(upload_root, normalized))
    if os.path.commonpath([upload_root, path]) != upload_root:
        return None
    return path

def _save_file_to_disk(file_storage, project_id: str) -> tuple:
    """Save an uploaded file to disk. Returns (file_name, stored_name, mime_type)."""
    original_name = file_storage.filename or "treefile"
    mime_type = file_storage.content_type or "application/octet-stream"
    safe_project_id = secure_filename(project_id) or uuid.uuid4().hex
    safe_file_name = secure_filename(original_name) or f"treefile_{uuid.uuid4().hex[:8]}"
    project_dir = os.path.join(UPLOAD_DIR, safe_project_id)
    os.makedirs(project_dir, exist_ok=True)

    stored_name = f"{safe_project_id}/{safe_file_name}"
    path = _safe_file_path(stored_name)
    if not path:
        raise ValueError("Invalid treefile path")

    if os.path.exists(path):
        base, ext = os.path.splitext(safe_file_name)
        stored_name = f"{safe_project_id}/{base}_{uuid.uuid4().hex[:8]}{ext}"
        path = _safe_file_path(stored_name)
        if not path:
            raise ValueError("Invalid treefile path")

    file_storage.save(path)
    return original_name, stored_name, mime_type

def _delete_file_from_disk(stored_name: str) -> None:
    """Remove a file from disk if it exists."""
    path = _safe_file_path(stored_name)
    if not path:
        return
    if os.path.isfile(path):
        os.remove(path)

def upsert_project_tree_file(project_id: str, file_storage) -> Dict:
    """Save an uploaded file (werkzeug FileStorage) to disk and record in DB."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Remove old file from disk + DB
            cursor.execute(
                "SELECT stored_name FROM project_tree_files WHERE project_id=%s",
                (project_id,)
            )
            old = cursor.fetchone()
            if old:
                _delete_file_from_disk(old.get("stored_name"))
                cursor.execute("DELETE FROM project_tree_files WHERE project_id=%s", (project_id,))

            original_name, stored_name, mime_type = _save_file_to_disk(file_storage, project_id)

            cursor.execute("""
                INSERT INTO project_tree_files
                (project_id, file_name, stored_name, mime_type, updated_at)
                VALUES (%s, %s, %s, %s, NOW())
            """, (project_id, original_name, stored_name, mime_type))

            cursor.execute(
                "UPDATE projects SET has_treefile=1 WHERE id=%s", (project_id,)
            )

        conn.commit()
        return {"file_name": original_name, "stored_name": stored_name, "mime_type": mime_type}
    finally:
        conn.close()

def delete_project_tree_file(project_id: str) -> None:
    """Remove treefile from disk and DB."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT stored_name FROM project_tree_files WHERE project_id=%s",
                (project_id,)
            )
            old = cursor.fetchone()
            if old:
                _delete_file_from_disk(old.get("stored_name"))

            cursor.execute("DELETE FROM project_tree_files WHERE project_id=%s", (project_id,))
            cursor.execute("UPDATE projects SET has_treefile=0 WHERE id=%s", (project_id,))
        conn.commit()
    finally:
        conn.close()

def get_project_tree_file(project_id: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT project_id, file_name, stored_name, mime_type, updated_at
                FROM project_tree_files
                WHERE project_id = %s
                LIMIT 1
            """, (project_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_file_path(stored_name: str) -> Optional[str]:
    """Return the full disk path for a stored file, or None if missing."""
    path = _safe_file_path(stored_name)
    if not path:
        return None
    return path if os.path.isfile(path) else None
