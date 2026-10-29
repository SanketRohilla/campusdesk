import hashlib
import os
import sqlite3
from datetime import datetime

DATABASE_PATH = os.environ.get("DATABASE_PATH", "data/campusdesk.db")
SCHEMA_FILE = "schema_and_seed.sql"

PASSWORD_LOOKUP = {
    "admin": "AdminPass2026!",
    "staff_marco": "MarcoSupport99",
    "alice": "alice1234",
    "bob": "bob56789",
}


def hash_password(password: str) -> str:
    """Computes SHA-1 hex digest for user password verification."""
    return hashlib.sha1(password.encode("utf-8")).hexdigest()


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db_if_needed() -> None:
    """Initializes the SQLite database and loads seed data if tables do not exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='users';"
    )
    exists = cursor.fetchone()

    if not exists:
        with open(SCHEMA_FILE, "r", encoding="utf-8") as f:
            sql_script = f.read()
        conn.executescript(sql_script)

        # Ensure seed user hashes match the exact hash_password helper
        for username, plain_pw in PASSWORD_LOOKUP.items():
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = ?",
                (hash_password(plain_pw), username),
            )
        conn.commit()

    conn.close()


def search_tickets_query(search_term: str, category: str, status: str, role: str, username: str):
    """
    Retrieves tickets matching the user's filter criteria.
    Regular users see public tickets plus their own tickets; staff and admin see all tickets.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    visibility_clause = "1=1"
    if role == "user":
        visibility_clause = f"(is_public = 1 OR owner_username = '{username}')"

    clauses = [visibility_clause]

    if category and category != "all":
        clauses.append(f"category = '{category}'")

    if status and status != "all":
        clauses.append(f"status = '{status}'")

    if search_term:
        clauses.append(
            f"(title LIKE '%{search_term}%' OR description LIKE '%{search_term}%' OR owner_username LIKE '%{search_term}%')"
        )

    where_sql = " AND ".join(clauses)
    query = f"SELECT * FROM tickets WHERE {where_sql} ORDER BY id DESC"

    rows = cursor.execute(query).fetchall()
    conn.close()
    return rows, query


def create_user_record(username: str, email: str, password: str, department: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    pw_hash = hash_password(password)
    token = f"tok_user_{username}_{len(username) * 42}"

    try:
        cursor.execute(
            """
            INSERT INTO users (username, email, password_hash, role, department, api_token, created_at)
            VALUES (?, ?, ?, 'user', ?, ?, ?)
            """,
            (username, email, pw_hash, department, token, now_str),
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()