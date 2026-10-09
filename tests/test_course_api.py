"""Unit tests for the course endpoints.

Run from the project root:
    .\\.venv\\Scripts\\python -m pytest
Each test gets its own temporary SQLite database, so data/students.db is never touched.
"""

import pytest
from fastapi.testclient import TestClient

import src.seeds.seed_courses as seed
from src import db
from src.main import app

MATH = {"name": "Mathematics", "description": "Algebra and geometry", "credits": 3}


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
    response = client.post("/courses", json={**MATH, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


def enroll_student(course_id):
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO students (first_name, last_name, email, course_id) VALUES (?, ?, ?, ?)",
            ("Ada", "Lovelace", "ada@example.com", course_id),
        )


# getAllCourses


def test_get_all_courses_empty(client):
    response = client.get("/courses")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_courses_ordered_by_id(client):
    first = create(client)
    second = create(client, name="Physics")
    ids = [c["id"] for c in client.get("/courses").json()]
    assert ids == [first["id"], second["id"]]


# getCourse


def test_get_course(client):
    created = create(client)
    response = client.get(f"/courses/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_course_not_found(client):
    response = client.get("/courses/999")
    assert response.status_code == 404


# postCourse


def test_post_course_returns_all_fields(client):
    created = create(client)
    assert created == {**MATH, "id": created["id"]}


def test_post_course_optional_fields_default_to_null(client):
    response = client.post("/courses", json={"name": "Art"})
    assert response.status_code == 201
    assert response.json()["description"] is None
    assert response.json()["credits"] is None


def test_post_course_duplicate_name(client):
    create(client)
    response = client.post("/courses", json=MATH)
    assert response.status_code == 409


@pytest.mark.parametrize("field, value", [("name", ""), ("credits", -1)])
def test_post_course_invalid_input(client, field, value):
    response = client.post("/courses", json={**MATH, field: value})
    assert response.status_code == 422


def test_post_course_missing_name(client):
    response = client.post("/courses", json={"credits": 3})
    assert response.status_code == 422


# putCourse


def test_put_course_replaces_record(client):
    created = create(client)
    updated = {"name": "Advanced Mathematics", "description": "Calculus", "credits": 4}
    response = client.put(f"/courses/{created['id']}", json=updated)
    assert response.status_code == 200
    assert response.json() == {**updated, "id": created["id"]}
    assert client.get(f"/courses/{created['id']}").json() == response.json()


def test_put_course_omitted_optional_fields_become_null(client):
    created = create(client)
    response = client.put(f"/courses/{created['id']}", json={"name": "Mathematics"})
    assert response.status_code == 200
    assert response.json()["description"] is None
    assert response.json()["credits"] is None


def test_put_course_not_found(client):
    response = client.put("/courses/999", json=MATH)
    assert response.status_code == 404


def test_put_course_duplicate_name(client):
    create(client)
    other = create(client, name="Physics")
    response = client.put(f"/courses/{other['id']}", json=MATH)
    assert response.status_code == 409


@pytest.mark.parametrize(
    "field, value", [("name", ""), ("credits", -1), ("credits", "many")]
)
def test_put_course_invalid_input(client, field, value):
    created = create(client)
    response = client.put(f"/courses/{created['id']}", json={**MATH, field: value})
    assert response.status_code == 422
    assert client.get(f"/courses/{created['id']}").json() == created


def test_put_course_keeping_own_name_succeeds(client):
    created = create(client)
    response = client.put(f"/courses/{created['id']}", json={**MATH, "credits": 5})
    assert response.status_code == 200
    assert response.json()["credits"] == 5


def test_put_course_duplicate_name_leaves_record_unchanged(client):
    create(client)
    other = create(client, name="Physics")
    client.put(f"/courses/{other['id']}", json=MATH)
    assert client.get(f"/courses/{other['id']}").json() == other


def test_post_course_zero_credits_is_allowed(client):
    response = client.post("/courses", json={**MATH, "credits": 0})
    assert response.status_code == 201
    assert response.json()["credits"] == 0


def test_delete_course_succeeds_after_students_unassigned(client):
    created = create(client)
    enroll_student(created["id"])
    with db.connect() as conn:
        conn.execute("UPDATE students SET course_id = NULL")
    assert client.delete(f"/courses/{created['id']}").status_code == 204


# deleteCourse


def test_delete_course(client):
    created = create(client)
    response = client.delete(f"/courses/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/courses/{created['id']}").status_code == 404


def test_delete_course_not_found(client):
    response = client.delete("/courses/999")
    assert response.status_code == 404


def test_delete_course_with_students_enrolled(client):
    created = create(client)
    enroll_student(created["id"])
    response = client.delete(f"/courses/{created['id']}")
    assert response.status_code == 409
    assert client.get(f"/courses/{created['id']}").status_code == 200


# Seed script


def test_seed_inserts_samples_and_is_rerunnable(capsys):
    seed.main()
    seed.main()
    with db.connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM courses").fetchone()[0]
    assert total == len(seed.SAMPLE_COURSES)
    assert "Inserted 0 course(s)" in capsys.readouterr().out
