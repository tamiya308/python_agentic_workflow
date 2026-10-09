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
    "first_name": "Ada",
    "last_name": "Lovelace",
    "email": "ada@example.com",
    "date_of_birth": "1815-12-10",
    "grade": 11,
    "course_id": None,
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
    second = create(client, email="grace@example.com", first_name="Grace")
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
        date_of_birth=None,
        grade=None,
        course_id=None,
        email="min@example.com",
    )
    assert created["date_of_birth"] is None
    assert created["grade"] is None
    assert created["course_id"] is None


def test_post_student_without_course_id(client):
    payload = {k: v for k, v in ADA.items() if k != "course_id"}
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    assert response.json()["course_id"] is None


def test_post_student_with_course(client):
    course_id = add_course()
    created = create(client, course_id=course_id)
    assert created["course_id"] == course_id


def test_post_student_unknown_course(client):
    response = client.post("/students", json={**ADA, "course_id": 999})
    assert response.status_code == 422


def test_post_student_duplicate_email(client):
    create(client)
    response = client.post("/students", json=ADA)
    assert response.status_code == 409


@pytest.mark.parametrize(
    "field, value",
    [
        ("email", "not-an-email"),
        ("first_name", ""),
        ("last_name", ""),
        ("grade", -1),
        ("date_of_birth", "10/12/1815"),
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
    updated = {**ADA, "course_id": physics, "grade": 12}
    response = client.put(f"/students/{created['id']}", json=updated)
    assert response.status_code == 200
    assert response.json() == {**updated, "id": created["id"]}
    assert client.get(f"/students/{created['id']}").json()["course_id"] == physics


def test_put_student_omitted_optional_fields_become_null(client):
    created = create(client, course_id=add_course())
    payload = {k: ADA[k] for k in ("first_name", "last_name", "email")}
    response = client.put(f"/students/{created['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["course_id"] is None
    assert response.json()["grade"] is None


def test_put_student_not_found(client):
    response = client.put("/students/999", json=ADA)
    assert response.status_code == 404


def test_put_student_unknown_course(client):
    created = create(client)
    response = client.put(f"/students/{created['id']}", json={**ADA, "course_id": 999})
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
    assert "course_id" in columns
    assert row["email"] == "old@example.com"
    assert row["course_id"] is None


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
    assert "course_id" in columns
    assert fks[0]["table"] == "courses" and fks[0]["from"] == "course_id"
    assert row["email"] == "old@example.com"
    assert row["course_id"] is None


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
        f"/students/{created['id']}", json={**ADA, "course_id": course_id}
    )
    assert response.status_code == 200
    assert response.json()["course_id"] == course_id
    assert client.get(f"/students/{created['id']}").json()["course_id"] == course_id


def test_put_student_can_unassign_course(client):
    course_id = add_course()
    created = create(client, course_id=course_id)
    response = client.put(f"/students/{created['id']}", json={**ADA, "course_id": None})
    assert response.status_code == 200
    assert response.json()["course_id"] is None


def test_put_student_unknown_course_leaves_record_unchanged(client):
    created = create(client)
    response = client.put(
        f"/students/{created['id']}", json={**ADA, "course_id": 999, "grade": 5}
    )
    assert response.status_code in (404, 409, 422)
    assert client.get(f"/students/{created['id']}").json() == created
