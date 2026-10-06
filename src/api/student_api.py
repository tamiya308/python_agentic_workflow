"""Student endpoints. Routed from src/main.py under /students."""

import sqlite3

from fastapi import APIRouter, HTTPException, status

from src.db import COLUMNS, PLACEHOLDERS, connect
from src.models import Student, StudentIn


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
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Student {student_id} not found"
        )
    return row_to_student(row)


def integrity_error(student: StudentIn, error: sqlite3.IntegrityError) -> HTTPException:
    if "FOREIGN KEY" in str(error):
        return HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Course {student.course_id} does not exist",
        )
    return HTTPException(
        status.HTTP_409_CONFLICT, f"Email {student.email} already exists"
    )


router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[Student])
def get_all_students():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    return [row_to_student(r) for r in rows]


@router.get("/{student_id}", response_model=Student)
def get_student(student_id: int):
    with connect() as conn:
        return fetch_student(conn, student_id)


@router.post("", response_model=Student, status_code=status.HTTP_201_CREATED)
def post_student(student: StudentIn):
    try:
        with connect() as conn:
            cur = conn.execute(
                f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES ({PLACEHOLDERS})",
                to_params(student),
            )
            return fetch_student(conn, cur.lastrowid)
    except sqlite3.IntegrityError as error:
        raise integrity_error(student, error)


@router.put("/{student_id}", response_model=Student)
def put_student(student_id: int, student: StudentIn):
    try:
        with connect() as conn:
            fetch_student(conn, student_id)  # 404 if missing
            conn.execute(
                f"UPDATE students SET {', '.join(f'{c} = ?' for c in COLUMNS)} WHERE id = ?",
                (*to_params(student), student_id),
            )
            return fetch_student(conn, student_id)
    except sqlite3.IntegrityError as error:
        raise integrity_error(student, error)
