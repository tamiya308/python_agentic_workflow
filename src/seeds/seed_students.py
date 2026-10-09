"""Seed the student records database with sample students.

Run from the project root:
    .\\.venv\\Scripts\\python -m src.seeds.seed_students
Safe to re-run: students whose email already exists are skipped.
"""

from src.api.student_api import to_params
from src.db import COLUMNS, PLACEHOLDERS, connect, init_db
from src.models import StudentIn

SAMPLE_STUDENTS = [
    StudentIn(
        firstName="Alan",
        lastName="Turing",
        email="alan.turing@example.com",
        dateOfBirth="2009-06-23",
        grade=10,
        courseId=None,
    ),
    StudentIn(
        firstName="Grace",
        lastName="Hopper",
        email="grace.hopper@example.com",
        dateOfBirth="2008-12-09",
        grade=11,
        courseId=None,
    ),
    StudentIn(
        firstName="Katherine",
        lastName="Johnson",
        email="katherine.johnson@example.com",
        dateOfBirth="2010-08-26",
        grade=9,
        courseId=None,
    ),
    StudentIn(
        firstName="Linus",
        lastName="Torvalds",
        email="linus.torvalds@example.com",
        dateOfBirth="2009-12-28",
        grade=10,
        courseId=None,
    ),
    StudentIn(
        firstName="Margaret",
        lastName="Hamilton",
        email="margaret.hamilton@example.com",
        dateOfBirth="2008-08-17",
        grade=12,
        courseId=None,
    ),
    StudentIn(
        firstName="Tim",
        lastName="Berners-Lee",
        email="tim.bernerslee@example.com",
        dateOfBirth="2010-06-08",
        grade=9,
        courseId=None,
    ),
    StudentIn(
        firstName="Barbara",
        lastName="Liskov",
        email="barbara.liskov@example.com",
        dateOfBirth="2009-11-07",
        grade=10,
        courseId=None,
    ),
    StudentIn(
        firstName="Dennis",
        lastName="Ritchie",
        email="dennis.ritchie@example.com",
        dateOfBirth="2008-09-09",
        grade=11,
        courseId=None,
    ),
    StudentIn(
        firstName="Hedy",
        lastName="Lamarr",
        email="hedy.lamarr@example.com",
        dateOfBirth="2008-11-09",
        grade=12,
        courseId=None,
    ),
]


def main() -> None:
    init_db()
    with connect() as conn:
        inserted = 0
        for student in SAMPLE_STUDENTS:
            cur = conn.execute(
                f"INSERT OR IGNORE INTO students ({', '.join(COLUMNS)}) VALUES ({PLACEHOLDERS})",
                to_params(student),
            )
            inserted += cur.rowcount
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    print(
        f"Inserted {inserted} student(s), skipped {len(SAMPLE_STUDENTS) - inserted}. Total in DB: {total}"
    )


if __name__ == "__main__":
    main()
