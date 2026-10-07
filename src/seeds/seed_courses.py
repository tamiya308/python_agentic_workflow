"""Seed the student records database with sample courses.

Run from the project root:
    .\\.venv\\Scripts\\python -m src.seeds.seed_courses
Safe to re-run: courses whose name already exists are skipped.
"""

from src.api.course_api import COURSE_COLUMNS, to_params
from src.db import connect, init_db
from src.models import CourseIn

SAMPLE_COURSES = [
    CourseIn(
        name="Introduction to Computer Science",
        description="Foundations of programming, algorithms and problem solving.",
        credits=4,
    ),
    CourseIn(
        name="Algebra II",
        description="Functions, polynomials, logarithms and systems of equations.",
        credits=3,
    ),
    CourseIn(
        name="Physics I",
        description="Mechanics, energy and motion with hands-on lab work.",
        credits=4,
    ),
]


def main() -> None:
    init_db()
    with connect() as conn:
        inserted = 0
        for course in SAMPLE_COURSES:
            cur = conn.execute(
                f"INSERT OR IGNORE INTO courses ({', '.join(COURSE_COLUMNS)}) VALUES (?, ?, ?)",
                to_params(course),
            )
            inserted += cur.rowcount
        total = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    print(
        f"Inserted {inserted} course(s), skipped {len(SAMPLE_COURSES) - inserted}. Total in DB: {total}"
    )


if __name__ == "__main__":
    main()
