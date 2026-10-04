"""Seed the student records database with sample students.

Run from the project root:
    .\\.venv\\Scripts\\python -m tools.seed_students
Safe to re-run: students whose email already exists are skipped.
"""

from tools.student_api import (
    COLUMNS,
    PLACEHOLDERS,
    StudentIn,
    connect,
    init_db,
    to_params,
)

SAMPLE_STUDENTS = [
    StudentIn(
        first_name="Alan",
        last_name="Turing",
        email="alan.turing@example.com",
        date_of_birth="2009-06-23",
        grade=10,
    ),
    StudentIn(
        first_name="Grace",
        last_name="Hopper",
        email="grace.hopper@example.com",
        date_of_birth="2008-12-09",
        grade=11,
    ),
    StudentIn(
        first_name="Katherine",
        last_name="Johnson",
        email="katherine.johnson@example.com",
        date_of_birth="2010-08-26",
        grade=9,
    ),
    StudentIn(
        first_name="Linus",
        last_name="Torvalds",
        email="linus.torvalds@example.com",
        date_of_birth="2009-12-28",
        grade=10,
    ),
    StudentIn(
        first_name="Margaret",
        last_name="Hamilton",
        email="margaret.hamilton@example.com",
        date_of_birth="2008-08-17",
        grade=12,
    ),
    StudentIn(
        first_name="Tim",
        last_name="Berners-Lee",
        email="tim.bernerslee@example.com",
        date_of_birth="2010-06-08",
        grade=9,
    ),
    StudentIn(
        first_name="Barbara",
        last_name="Liskov",
        email="barbara.liskov@example.com",
        date_of_birth="2009-11-07",
        grade=10,
    ),
    StudentIn(
        first_name="Dennis",
        last_name="Ritchie",
        email="dennis.ritchie@example.com",
        date_of_birth="2008-09-09",
        grade=11,
    ),
    StudentIn(
        first_name="Hedy",
        last_name="Lamarr",
        email="hedy.lamarr@example.com",
        date_of_birth="2008-11-09",
        grade=12,
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
