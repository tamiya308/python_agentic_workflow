"""Student records API: FastAPI + SQLite.

Run from the project root:
    .\\.venv\\Scripts\\python -m uvicorn tools.student_api:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

import sqlite3
from contextlib import asynccontextmanager, contextmanager
from datetime import date
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "students.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    email         TEXT NOT NULL UNIQUE,
    date_of_birth TEXT,
    grade         INTEGER
)
"""

COLUMNS = ("first_name", "last_name", "email", "date_of_birth", "grade")


class StudentIn(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    date_of_birth: date | None = None
    grade: int | None = Field(default=None, ge=0)


class Student(StudentIn):
    id: int


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


def row_to_student(row: sqlite3.Row) -> Student:
    return Student(**dict(row))


def to_params(student: StudentIn) -> tuple:
    data = student.model_dump()
    if data["date_of_birth"] is not None:
        data["date_of_birth"] = data["date_of_birth"].isoformat()
    return tuple(data[c] for c in COLUMNS)


def fetch_student(conn: sqlite3.Connection, student_id: int) -> Student:
    row = conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Student {student_id} not found")
    return row_to_student(row)


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Student Records API", lifespan=lifespan)


@app.get("/students", response_model=list[Student])
def get_all_students():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    return [row_to_student(r) for r in rows]


@app.get("/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    with connect() as conn:
        return fetch_student(conn, student_id)


@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED)
def post_student(student: StudentIn):
    try:
        with connect() as conn:
            cur = conn.execute(
                f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES (?, ?, ?, ?, ?)",
                to_params(student),
            )
            return fetch_student(conn, cur.lastrowid)
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Email {student.email} already exists")


@app.put("/students/{student_id}", response_model=Student)
def put_student(student_id: int, student: StudentIn):
    try:
        with connect() as conn:
            fetch_student(conn, student_id)  # 404 if missing
            conn.execute(
                f"UPDATE students SET {', '.join(f'{c} = ?' for c in COLUMNS)} WHERE id = ?",
                (*to_params(student), student_id),
            )
            return fetch_student(conn, student_id)
    except sqlite3.IntegrityError:
        raise HTTPException(status.HTTP_409_CONFLICT, f"Email {student.email} already exists")
