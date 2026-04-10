"""
One-time migration script: converts existing base64 treefile data in the DB
to files on disk and updates the DB to store just the file path.

Run AFTER applying the MySQL schema changes listed below.

Usage:
    cd backend
    python migrate_treefiles.py
"""

import os
import sys
import base64
import uuid

# Ensure the backend modules are importable
sys.path.insert(0, os.path.dirname(__file__))

from db import get_connection

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads", "treefiles")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def migrate():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check if the old 'content' column still exists
            cursor.execute("SHOW COLUMNS FROM project_tree_files LIKE 'content'")
            if not cursor.fetchone():
                print("Column 'content' not found — migration may have already run.")
                return

            cursor.execute("SELECT project_id, file_name, mime_type, content FROM project_tree_files")
            rows = cursor.fetchall()

        if not rows:
            print("No treefile rows to migrate.")
            return

        print(f"Migrating {len(rows)} treefile(s)...")

        for row in rows:
            project_id = row["project_id"]
            file_name = row["file_name"] or "treefile"
            mime_type = row["mime_type"] or "application/octet-stream"
            raw_content = row["content"]

            if not raw_content:
                print(f"  [{project_id}] empty content, skipping")
                continue

            # Decode content — it may be a data:URI or raw base64 or raw bytes
            if isinstance(raw_content, (bytes, bytearray)):
                file_bytes = raw_content
            elif isinstance(raw_content, str):
                if raw_content.startswith("data:"):
                    # Strip data:mime;base64, prefix
                    _, _, b64part = raw_content.partition(",")
                    file_bytes = base64.b64decode(b64part)
                else:
                    try:
                        file_bytes = base64.b64decode(raw_content)
                    except Exception:
                        file_bytes = raw_content.encode("utf-8")
            else:
                print(f"  [{project_id}] unexpected content type {type(raw_content)}, skipping")
                continue

            # Write to disk
            ext = os.path.splitext(file_name)[1] or ".bin"
            stored_name = f"{project_id}_{uuid.uuid4().hex[:8]}{ext}"
            path = os.path.join(UPLOAD_DIR, stored_name)

            with open(path, "wb") as f:
                f.write(file_bytes)

            # Update DB row
            with conn.cursor() as cursor:
                cursor.execute(
                    "UPDATE project_tree_files SET stored_name=%s WHERE project_id=%s",
                    (stored_name, project_id),
                )

            print(f"  [{project_id}] -> {stored_name} ({len(file_bytes)} bytes)")

        conn.commit()
        print("Migration complete!")
        print()
        print("You can now drop the old 'content' column:")
        print("  ALTER TABLE project_tree_files DROP COLUMN content;")

    finally:
        conn.close()


if __name__ == "__main__":
    migrate()
