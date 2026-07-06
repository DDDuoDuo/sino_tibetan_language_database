from db import get_connection
import uuid
import bcrypt
from typing import Optional, Dict

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # Fallback: if the stored password is not a bcrypt hash (legacy plaintext),
        # compare directly so existing users can still log in, then rehash on success.
        return plain == hashed

def create_user(email: str, username: str, password_plain: str,
                title: str = "教授", workplace: str = "") -> Dict:
    user_id = str(uuid.uuid4())
    pw_hash = hash_password(password_plain)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO users (id, email, username, password, title, workplace, account_type)
                VALUES (%s, %s, %s, %s, %s, %s, 'user')
            """
            cursor.execute(sql, (
                user_id, email, username, pw_hash, title, workplace
            ))

            cursor.execute(
                "SELECT created_at FROM users WHERE id=%s",
                (user_id,)
            )
            row = cursor.fetchone()
            created_at = row["created_at"] if row and "created_at" in row else None

        conn.commit()
        return {
            "id": user_id,
            "email": email,
            "username": username,
            "title": title,
            "workplace": workplace,
            "account_type": "user",
            "created_at": created_at,
        }
    finally:
        conn.close()

def get_user_by_email(email: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
            return cursor.fetchone()
    finally:
        conn.close()

def get_user_by_id(user_id: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def update_user_password_hash(user_id: str, new_hash: str) -> None:
    """Rehash a legacy plaintext password to bcrypt."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE users SET password=%s WHERE id=%s", (new_hash, user_id))
        conn.commit()
    finally:
        conn.close()

def update_user_profile(user_id: str, username: str, title: str, workplace: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                """
                UPDATE users
                SET username=%s,
                    title=%s,
                    workplace=%s
                WHERE id=%s
                """,
                (username, title, workplace, user_id),
            )
            conn.commit()

            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def update_user_account_type(user_id: str, account_type: str) -> Optional[Dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET account_type=%s WHERE id=%s",
                (account_type, user_id),
            )
            conn.commit()

            cursor.execute("SELECT * FROM users WHERE id=%s", (user_id,))
            return cursor.fetchone()
    finally:
        conn.close()

def list_contributors(page: int = 1, per_page: int = 10):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            offset = (page - 1) * per_page
            cursor.execute("SELECT COUNT(*) AS cnt FROM users")
            total = cursor.fetchone()["cnt"]
            sql = """
                SELECT
                    u.id,
                    u.username,
                    u.email,
                    u.workplace,
                    u.account_type,
                    u.created_at,
                    COUNT(p.id) AS project_count,
                    COALESCE(SUM(p.num_vocab), 0) AS vocab_count
                FROM users u
                LEFT JOIN projects p ON p.author_id = u.id
                GROUP BY u.id
                ORDER BY u.created_at DESC
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, (per_page, offset))
            rows = cursor.fetchall()

            return rows, total
    finally:
        conn.close()
