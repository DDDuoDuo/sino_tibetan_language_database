from db import get_connection
from typing import List, Dict, Optional
from datetime import datetime, timezone

def list_projects_by_author(author_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT 
                    p.*,
                    u.username AS author_username
                FROM projects p
                LEFT JOIN users u ON p.author_id = u.id
                WHERE p.author_id = %s
                ORDER BY p.updated_at DESC
            """
            cursor.execute(sql, (author_id,))
            return cursor.fetchall()
    finally:
        conn.close()

def list_public_projects() -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT
                    p.*,
                    u.username AS author_username
                FROM projects p
                LEFT JOIN users u ON p.author_id = u.id
                WHERE p.is_public = 1
                ORDER BY p.updated_at DESC
            """
            cursor.execute(sql)
            return cursor.fetchall()
    finally:
        conn.close()

def get_project(project_id: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM projects WHERE id=%s", (project_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def upsert_project(project_data: Dict) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id FROM projects WHERE id=%s", (project_data["id"],))
            existing = cursor.fetchone()

            time_range = project_data.get("projectTimeRange", {}) or {}
            upper = time_range.get("upper")
            upperEra = time_range.get("upperEra")
            lower = time_range.get("lower")
            lowerEra = time_range.get("lowerEra")
            num_vocab = len(project_data.get("vocabList", []))

            if existing:
                sql = """
                    UPDATE projects
                    SET author_id=%s,
                        project_name=%s,
                        project_desc=%s,
                        project_type=%s,
                        references_text=%s,
                        is_public=%s,
                        time_upper=%s,
                        time_upper_era=%s,
                        time_lower=%s,
                        time_lower_era=%s,
                        num_vocab=%s,
                        updated_at=NOW()
                    WHERE id=%s
                """
                cursor.execute(sql, (
                    project_data["authorId"],
                    project_data["projectName"],
                    project_data.get("projectDesc", ""),
                    project_data.get("projectType", ""),
                    project_data.get("references", ""),
                    int(bool(project_data.get("isPublic"))),
                    upper,
                    upperEra,
                    lower,
                    lowerEra,
                    num_vocab,
                    project_data["id"],
                ))
            else:
                created_at_raw = project_data.get("createdAt")
                created_at_dt = None
                if created_at_raw:
                    try:
                        created_at_dt = datetime.strptime(created_at_raw, "%m/%d/%Y, %I:%M:%S %p")
                    except ValueError:
                        created_at_dt = None

                sql = """
                    INSERT INTO projects (
                        id, author_id, project_name, project_desc, project_type,
                        references_text, is_public,
                        time_upper, time_upper_era,
                        time_lower, time_lower_era,
                        num_vocab, 
                        created_at, updated_at
                    ) VALUES (
                        %s,%s,%s,%s,%s,%s,%s,
                        %s,%s,%s,%s,%s,%s,%s
                    )
                """
                now_dt = datetime.now(timezone.utc)
                cursor.execute(sql, (
                    project_data["id"],
                    project_data["authorId"],
                    project_data["projectName"],
                    project_data.get("projectDesc", ""),
                    project_data.get("projectType", ""),
                    project_data.get("references", ""),
                    int(bool(project_data.get("isPublic"))),
                    upper,
                    upperEra,
                    lower,
                    lowerEra,
                    num_vocab,
                    created_at_dt or now_dt,
                    now_dt,
                ))
        conn.commit()
    finally:
        conn.close()

def set_project_public(project_id: str, is_public: bool) -> None:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE projects SET is_public=%s, updated_at=NOW() WHERE id=%s",
                (int(bool(is_public)), project_id)
            )
        conn.commit()
    finally:
        conn.close()

def delete_project(project_id: str) -> None:
    from models.treefiles import delete_project_tree_file
    # Remove treefile from disk first
    delete_project_tree_file(project_id)

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "DELETE FROM project_languages WHERE project_id=%s",
                (project_id,)
            )

            cursor.execute(
                "DELETE FROM vocab WHERE project_id=%s",
                (project_id,)
            )

            cursor.execute(
                "DELETE FROM project_tree_files WHERE project_id=%s",
                (project_id,)
            )

            cursor.execute(
                "DELETE FROM projects WHERE id=%s",
                (project_id,)
            )

        conn.commit()
    finally:
        conn.close()
