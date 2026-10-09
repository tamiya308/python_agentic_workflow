"""Unit tests for the student records API.

Run from the project root:
    .\\.venv\\Scripts\\python -m pytest
Each test gets its own temporary SQLite database, so data/students.db is never touched.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

import src.seeds.seed_students as seed
from src import db
from src.main import app

ADA = {
    "firstName": "Ada",
    "lastName": "Lovelace",
    "email": "ada@example.com",
    "dateOfBirth": "1815-12-10",
    "grade": 11,
    "courseId": None,
}


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "students.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def client():
    with TestClient(app) as c:  # the context manager runs the lifespan (init_db)
        yield c


def add_course(name="Mathematics"):
    with db.connect() as conn:
        return conn.execute("INSERT INTO courses (name) VALUES (?)", (name,)).lastrowid


def create(client, **overrides):
    response = client.post("/students", json={**ADA, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


# GetAllStudents


def test_get_all_students_empty(client):
    response = client.get("/students")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_students_ordered_by_id(client):
    first = create(client)
    second = create(client, email="grace@example.com", firstName="Grace")
    ids = [s["id"] for s in client.get("/students").json()]
    assert ids == [first["id"], second["id"]]


# getStudent


def test_get_student(client):
    created = create(client)
    response = client.get(f"/students/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_student_not_found(client):
    response = client.get("/students/999")
    assert response.status_code == 404


# postStudent


def test_post_student_returns_all_fields(client):
    created = create(client)
    assert created == {**ADA, "id": created["id"]}


def test_post_student_optional_fields_default_to_null(client):
    created = create(
        client,
        dateOfBirth=None,
        grade=None,
        courseId=None,
        email="min@example.com",
    )
    assert created["dateOfBirth"] is None
    assert created["grade"] is None
    assert created["courseId"] is None


def test_post_student_without_course_id(client):
    payload = {k: v for k, v in ADA.items() if k != "courseId"}
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    assert response.json()["courseId"] is None


def test_post_student_with_course(client):
    course_id = add_course()
    created = create(client, courseId=course_id)
    assert created["courseId"] == course_id


def test_post_student_unknown_course(client):
    response = client.post("/students", json={**ADA, "courseId": 999})
    assert response.status_code == 422


def test_post_student_duplicate_email(client):
    create(client)
    response = client.post("/students", json=ADA)
    assert response.status_code == 409


@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "not-an-email"),
        ("firstName", ""),
        ("lastName", ""),
        ("grade", -1),
        ("dateOfBirth", "10/12/1815"),
    ],
)
def test_post_student_invalid_input(client, field, value):
    response = client.post("/students", json={**ADA, field: value})
    assert response.status_code == 422


def test_post_student_missing_required_field(client):
    payload = {k: v for k, v in ADA.items() if k != "email"}
    response = client.post("/students", json=payload)
    assert response.status_code == 422


# putStudent


def test_put_student_replaces_record(client):
    created = create(client)
    physics = add_course("Physics")
    updated = {**ADA, "courseId": physics, "grade": 12}
    response = client.put(f"/students/{created['id']}", json=updated)
    assert response.status_code == 200
    assert response.json() == {**updated, "id": created["id"]}
    assert client.get(f"/students/{created['id']}").json()["courseId"] == physics


def test_put_student_omitted_optional_fields_become_null(client):
    created = create(client, courseId=add_course())
    payload = {k: ADA[k] for k in ("firstName", "lastName", "email")}
    response = client.put(f"/students/{created['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["courseId"] is None
    assert response.json()["grade"] is None


def test_put_student_not_found(client):
    response = client.put("/students/999", json=ADA)
    assert response.status_code == 404


def test_put_student_unknown_course(client):
    created = create(client)
    response = client.put(f"/students/{created['id']}", json={**ADA, "courseId": 999})
    assert response.status_code == 422


def test_put_student_duplicate_email(client):
    create(client)
    other = create(client, email="grace@example.com")
    response = client.put(f"/students/{other['id']}", json=ADA)
    assert response.status_code == 409


# Database setup and migration


def test_init_db_upgrades_database_without_course_columns(temp_db):
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            "CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL,"
            " last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, date_of_birth TEXT, grade INTEGER)"
        )
        conn.execute(
            "INSERT INTO students (first_name, last_name, email) VALUES ('Old', 'Row', 'old@example.com')"
        )
    conn.close()

    db.init_db()
    db.init_db()  # running twice must be safe

    with db.connect() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(students)")]
        row = conn.execute("SELECT * FROM students").fetchone()
    assert "courseId" in columns
    assert row["email"] == "old@example.com"
    assert row["courseId"] is None


def test_init_db_replaces_course_name_with_course_id(temp_db):
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            "CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL,"
            " last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, date_of_birth TEXT, grade INTEGER,"
            " course_name TEXT)"
        )
        conn.execute(
            "INSERT INTO students (first_name, last_name, email, course_name)"
            " VALUES ('Old', 'Row', 'old@example.com', 'nothing')"
        )
    conn.close()

    db.init_db()
    db.init_db()  # running twice must be safe

    with db.connect() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(students)")]
        fks = [dict(r) for r in conn.execute("PRAGMA foreign_key_list(students)")]
        row = conn.execute("SELECT * FROM students").fetchone()
    assert "course_name" not in columns
    assert "courseId" in columns
    assert fks[0]["table"] == "courses" and fks[0]["from"] == "courseId"
    assert row["email"] == "old@example.com"
    assert row["courseId"] is None


def test_init_db_renames_snake_case_columns_and_keeps_data(temp_db):
    with sqlite3.connect(temp_db) as conn:
        conn.execute(
            "CREATE TABLE courses (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL UNIQUE,"
            " description TEXT, credits INTEGER)"
        )
        conn.execute("INSERT INTO courses (name) VALUES ('Physics')")
        conn.execute(
            "CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL,"
            " last_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE, date_of_birth TEXT, grade INTEGER,"
            " course_id INTEGER REFERENCES courses(id))"
        )
        conn.execute(
            "INSERT INTO students (first_name, last_name, email, date_of_birth, grade, course_id)"
            " VALUES ('Old', 'Row', 'old@example.com', '2009-01-02', 10, 1)"
        )
    conn.close()

    db.init_db()
    db.init_db()  # running twice must be safe

    with db.connect() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(students)")]
        fks = [dict(r) for r in conn.execute("PRAGMA foreign_key_list(students)")]
        row = dict(conn.execute("SELECT * FROM students").fetchone())
    assert columns == ["id", *db.COLUMNS]
    assert fks[0]["table"] == "courses" and fks[0]["from"] == "courseId"
    assert row == {
        "id": 1,
        "firstName": "Old",
        "lastName": "Row",
        "email": "old@example.com",
        "dateOfBirth": "2009-01-02",
        "grade": 10,
        "courseId": 1,
    }


def test_init_db_creates_empty_courses_table(temp_db):
    db.init_db()
    with db.connect() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(courses)")]
        total = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    assert columns == ["id", "name", "description", "credits"]
    assert total == 0


# Seed script


def test_seed_inserts_samples_and_is_rerunnable(capsys):
    seed.main()
    seed.main()
    with db.connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    assert total == len(seed.SAMPLE_STUDENTS)
    assert "Inserted 0 student(s)" in capsys.readouterr().out


# Additional course-related coverage


def test_put_student_assigns_existing_course(client):
    created = create(client)
    course_id = add_course("Physics")
    response = client.put(
        f"/students/{created['id']}", json={**ADA, "courseId": course_id}
    )
    assert response.status_code == 200
    assert response.json()["courseId"] == course_id
    assert client.get(f"/students/{created['id']}").json()["courseId"] == course_id


def test_put_student_can_unassign_course(client):
    course_id = add_course()
    created = create(client, courseId=course_id)
    response = client.put(f"/students/{created['id']}", json={**ADA, "courseId": None})
    assert response.status_code == 200
    assert response.json()["courseId"] is None


def test_put_student_unknown_course_leaves_record_unchanged(client):
    created = create(client)
    response = client.put(
        f"/students/{created['id']}", json={**ADA, "courseId": 999, "grade": 5}
    )
    assert response.status_code in (404, 409, 422)
    assert client.get(f"/students/{created['id']}").json() == created


# Additional coverage for the endpoint table

PUT_INVALID = [
    ("email", "not-an-email"),
    ("firstName", ""),
    ("lastName", ""),
    ("grade", -1),
    ("dateOfBirth", "10/12/1815"),
]


@pytest.mark.parametrize("field, value", PUT_INVALID)
def test_put_student_invalid_input(client, field, value):
    created = create(client)
    response = client.put(f"/students/{created['id']}", json={**ADA, field: value})
    assert response.status_code == 422
    assert client.get(f"/students/{created['id']}").json() == created


def test_put_student_missing_required_field(client):
    created = create(client)
    payload = {k: v for k, v in ADA.items() if k != "lastName"}
    response = client.put(f"/students/{created['id']}", json=payload)
    assert response.status_code == 422


def test_put_student_keeping_own_email_succeeds(client):
    created = create(client)
    response = client.put(f"/students/{created['id']}", json={**ADA, "grade": 12})
    assert response.status_code == 200
    assert response.json()["grade"] == 12


def test_put_student_duplicate_email_leaves_record_unchanged(client):
    create(client)
    other = create(client, email="grace@example.com")
    client.put(f"/students/{other['id']}", json=ADA)
    assert client.get(f"/students/{other['id']}").json() == other


def test_post_student_duplicate_email_does_not_add_row(client):
    create(client)
    client.post("/students", json=ADA)
    assert len(client.get("/students").json()) == 1


def test_post_student_unknown_course_does_not_add_row(client):
    client.post("/students", json={**ADA, "courseId": 999})
    assert client.get("/students").json() == []
