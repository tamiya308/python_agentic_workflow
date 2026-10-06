"""SQLite storage: database location, schema, connections and setup."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "students.db"

COURSES_SCHEMA = """
CREATE TABLE IF NOT EXISTS courses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,
    description TEXT,
    credits     INTEGER
)
"""

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    date_of_birth TEXT,
    grade         INTEGER,
    course_id     INTEGER REFERENCES courses(id)
)
"""

COLUMNS = ("first_name", "last_name", "email", "date_of_birth", "grade", "course_id")
PLACEHOLDERS = ", ".join("?" for _ in COLUMNS)


@contextmanager
def connect():
    """Yield a connection that commits on success, rolls back on error, and always closes."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # SQLite leaves FK checks off by default
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.execute(COURSES_SCHEMA)
        conn.execute(SCHEMA)
        # Older databases have course_name (free text) instead of course_id.
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(students)")}
        if "course_id" not in existing:
            conn.execute(
                "ALTER TABLE students ADD COLUMN course_id INTEGER REFERENCES courses(id)"
            )
        if "course_name" in existing:
            conn.execute("ALTER TABLE students DROP COLUMN course_name")
