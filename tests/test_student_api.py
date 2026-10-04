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
    "course_name": "Mathematics",
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
        course_name=None,
        email="min@example.com",
    )
    assert created["date_of_birth"] is None
    assert created["grade"] is None
    assert created["course_name"] is None


def test_post_student_without_course_name(client):
    payload = {k: v for k, v in ADA.items() if k != "course_name"}
    response = client.post("/students", json=payload)
    assert response.status_code == 201
    assert response.json()["course_name"] is None


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
    updated = {**ADA, "course_name": "Physics", "grade": 12}
    response = client.put(f"/students/{created['id']}", json=updated)
    assert response.status_code == 200
    assert response.json() == {**updated, "id": created["id"]}
    assert client.get(f"/students/{created['id']}").json()["course_name"] == "Physics"


def test_put_student_omitted_optional_fields_become_null(client):
    created = create(client)
    payload = {k: ADA[k] for k in ("first_name", "last_name", "email")}
    response = client.put(f"/students/{created['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["course_name"] is None
    assert response.json()["grade"] is None


def test_put_student_not_found(client):
    response = client.put("/students/999", json=ADA)
    assert response.status_code == 404


def test_put_student_duplicate_email(client):
    create(client)
    other = create(client, email="grace@example.com")
    response = client.put(f"/students/{other['id']}", json=ADA)
    assert response.status_code == 409


# Database setup and migration


def test_init_db_adds_course_name_to_old_database(temp_db):
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
    assert "course_name" in columns
    assert row["email"] == "old@example.com"
    assert row["course_name"] is None


# Seed script


def test_seed_inserts_samples_and_is_rerunnable(capsys):
    seed.main()
    seed.main()
    with db.connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    assert total == len(seed.SAMPLE_STUDENTS)
    assert "Inserted 0 student(s)" in capsys.readouterr().out
