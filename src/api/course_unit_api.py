"""Course unit endpoints. Routed from src/main.py under /courseUnits."""

import sqlite3

from fastapi import APIRouter, HTTPException, Response, status

from src.db import connect
from src.models import CourseUnit, CourseUnitIn

COURSE_UNIT_COLUMNS = ("name", "description", "courseId")


def row_to_course_unit(row: sqlite3.Row) -> CourseUnit:
    return CourseUnit(**dict(row))


def to_params(unit: CourseUnitIn) -> tuple:
    data = unit.model_dump()
    return tuple(data[c] for c in COURSE_UNIT_COLUMNS)


def fetch_course_unit(conn: sqlite3.Connection, unit_id: int) -> CourseUnit:
    row = conn.execute("SELECT * FROM courseUnits WHERE id = ?", (unit_id,)).fetchone()
    if row is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, f"Course unit {unit_id} not found"
        )
    return row_to_course_unit(row)


def integrity_error(unit: CourseUnitIn, error: sqlite3.IntegrityError) -> HTTPException:
    if "FOREIGN KEY" in str(error):
        return HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            f"Course {unit.courseId} does not exist",
        )
    return HTTPException(
        status.HTTP_409_CONFLICT,
        f"Course {unit.courseId} already has a unit named {unit.name}",
    )


router = APIRouter(prefix="/courseUnits", tags=["courseUnits"])


@router.get("", response_model=list[CourseUnit])
def get_all_course_units():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM courseUnits ORDER BY id").fetchall()
    return [row_to_course_unit(r) for r in rows]


@router.get("/{unit_id}", response_model=CourseUnit)
def get_course_unit(unit_id: int):
    with connect() as conn:
        return fetch_course_unit(conn, unit_id)


@router.post("", response_model=CourseUnit, status_code=status.HTTP_201_CREATED)
def post_course_unit(unit: CourseUnitIn):
    try:
        with connect() as conn:
            cur = conn.execute(
                f"INSERT INTO courseUnits ({', '.join(COURSE_UNIT_COLUMNS)}) VALUES (?, ?, ?)",
                to_params(unit),
            )
            return fetch_course_unit(conn, cur.lastrowid)
    except sqlite3.IntegrityError as error:
        raise integrity_error(unit, error)


@router.put("/{unit_id}", response_model=CourseUnit)
def put_course_unit(unit_id: int, unit: CourseUnitIn):
    try:
        with connect() as conn:
            fetch_course_unit(conn, unit_id)  # 404 if missing
            conn.execute(
                f"UPDATE courseUnits SET {', '.join(f'{c} = ?' for c in COURSE_UNIT_COLUMNS)} WHERE id = ?",
                (*to_params(unit), unit_id),
            )
            return fetch_course_unit(conn, unit_id)
    except sqlite3.IntegrityError as error:
        raise integrity_error(unit, error)


@router.delete("/{unit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course_unit(unit_id: int):
    with connect() as conn:
        fetch_course_unit(conn, unit_id)  # 404 if missing
        conn.execute("DELETE FROM courseUnits WHERE id = ?", (unit_id,))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
