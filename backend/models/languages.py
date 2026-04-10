from db import get_connection
from typing import List, Dict

def replace_project_languages(project_id: str, langs: List[Dict]) -> None:
    """
    langs: [{ name, lng, lat, sortOrder }, ...]
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM project_languages WHERE project_id=%s", (project_id,))
            if not langs:
                conn.commit()
                return
            sql = """
                INSERT INTO project_languages
                (project_id, name, longitude, latitude, sort_order)
                VALUES (%s,%s,%s,%s,%s)
            """
            for idx, lang in enumerate(langs):
                raw_lng = lang.get("lng")
                raw_lat = lang.get("lat")

                if raw_lng == "" or raw_lng is None:
                    lng = None
                else:
                    lng = raw_lng

                if raw_lat == "" or raw_lat is None:
                    lat = None
                else:
                    lat = raw_lat

                cursor.execute(sql, (
                    project_id,
                    lang.get("name"),
                    lng,
                    lat,
                    lang.get("sortOrder", idx)
                ))
        conn.commit()
    finally:
        conn.close()

def get_project_languages(project_id: str) -> List[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM project_languages WHERE project_id=%s ORDER BY sort_order ASC",
                (project_id,)
            )
            return cursor.fetchall()
    finally:
        conn.close()

def get_languages_for_projects(project_ids: List[str]) -> Dict[str, List[Dict]]:
    """Batch-fetch languages for multiple projects in one query."""
    if not project_ids:
        return {}
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            placeholders = ",".join(["%s"] * len(project_ids))
            cursor.execute(
                f"SELECT * FROM project_languages WHERE project_id IN ({placeholders}) ORDER BY sort_order ASC",
                tuple(project_ids),
            )
            rows = cursor.fetchall()
    finally:
        conn.close()
    result: Dict[str, List[Dict]] = {pid: [] for pid in project_ids}
    for row in rows:
        result[row["project_id"]].append(row)
    return result
