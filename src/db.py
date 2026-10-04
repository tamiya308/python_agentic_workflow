"""SQLite storage: database location, schema, connections and setup."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    date_of_birth TEXT,
    grade         INTEGER,
    course_name   TEXT
)
"""

COLUMNS = ("first_name", "last_name", "email", "date_of_birth", "grade", "course_name")
PLACEHOLDERS = ", ".join("?" for _ in COLUMNS)


@contextmanager
def connect():
    """Yield a connection that commits on success, rolls back on error, and always closes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute(SCHEMA)
        # Databases created before course_name existed need the column added.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(students)")}
        if "course_name" not in existing:
            conn.execute("ALTER TABLE students ADD COLUMN course_name TEXT")
