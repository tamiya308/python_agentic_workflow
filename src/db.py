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
    firstName     TEXT NOT NULL,
    lastName      TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    dateOfBirth   TEXT,
    grade         INTEGER,
    courseId      INTEGER REFERENCES courses(id)
)
"""

COURSE_UNITS_SCHEMA = """
CREATE TABLE IF NOT EXISTS courseUnits (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    courseId    INTEGER NOT NULL REFERENCES courses(id),
    UNIQUE (courseId, name)
)
"""

COLUMNS = ("firstName", "lastName", "email", "dateOfBirth", "grade", "courseId")
PLACEHOLDERS = ", ".join("?" for _ in COLUMNS)

# Older databases used snake_case column names.
RENAMED_COLUMNS = {
    "first_name": "firstName",
    "last_name": "lastName",
    "date_of_birth": "dateOfBirth",
    "course_id": "courseId",
}


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
        conn.execute(COURSE_UNITS_SCHEMA)
        existing = {row["name"] for row in conn.execute("PRAGMA table_info(students)")}
        for old, new in RENAMED_COLUMNS.items():
            if old in existing:
                conn.execute(f"ALTER TABLE students RENAME COLUMN {old} TO {new}")
                existing = (existing - {old}) | {new}
        # Older databases have courseName (free text) instead of a course id.
        if "courseId" not in existing:
            conn.execute(
                "ALTER TABLE students ADD COLUMN courseId INTEGER REFERENCES courses(id)"
            )
        if "courseName" in existing:
            conn.execute("ALTER TABLE students DROP COLUMN courseName")
