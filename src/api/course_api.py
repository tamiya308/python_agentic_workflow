"""Course endpoints. Routed from src/main.py under /courses."""

import sqlite3

from fastapi import APIRouter, HTTPException, Response, status

from src.db import connect
from src.models import Course, CourseIn

COURSE_COLUMNS = ("name", "description", "credits")


def row_to_course(row: sqlite3.Row) -> Course:
    return Course(**dict(row))


def to_params(course: CourseIn) -> tuple:
    data = course.model_dump()
    return tuple(data[c] for c in COURSE_COLUMNS)


def fetch_course(conn: sqlite3.Connection, course_id: int) -> Course:
    row = conn.execute("SELECT * FROM courses WHERE id = ?", (course_id,)).fetchone()
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Course {course_id} not found")
    return row_to_course(row)


def name_conflict(course: CourseIn) -> HTTPException:
    return HTTPException(
        status.HTTP_409_CONFLICT, f"Course name {course.name} already exists"
    )


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=list[Course])
def get_all_courses():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM courses ORDER BY id").fetchall()
    return [row_to_course(r) for r in rows]


@router.get("/{course_id}", response_model=Course)
def get_course(course_id: int):
    with connect() as conn:
        return fetch_course(conn, course_id)


@router.post("", response_model=Course, status_code=status.HTTP_201_CREATED)
def post_course(course: CourseIn):
    try:
        with connect() as conn:
            cur = conn.execute(
                f"INSERT INTO courses ({', '.join(COURSE_COLUMNS)}) VALUES (?, ?, ?)",
                to_params(course),
            )
            return fetch_course(conn, cur.lastrowid)
    except sqlite3.IntegrityError:
        raise name_conflict(course)


@router.put("/{course_id}", response_model=Course)
def put_course(course_id: int, course: CourseIn):
    try:
        with connect() as conn:
            fetch_course(conn, course_id)  # 404 if missing
            conn.execute(
                f"UPDATE courses SET {', '.join(f'{c} = ?' for c in COURSE_COLUMNS)} WHERE id = ?",
                (*to_params(course), course_id),
            )
            return fetch_course(conn, course_id)
    except sqlite3.IntegrityError:
        raise name_conflict(course)


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int):
    try:
        with connect() as conn:
            fetch_course(conn, course_id)  # 404 if missing
            conn.execute("DELETE FROM courses WHERE id = ?", (course_id,))
    except sqlite3.IntegrityError:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Course {course_id} still has students enrolled",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
