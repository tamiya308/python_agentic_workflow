"""Unit tests for the course unit endpoints.

Run from the project root:
    .\\.venv\\Scripts\\python -m pytest
Each test gets its own temporary SQLite database, so data/students.db is never touched.
"""

import pytest
from fastapi.testclient import TestClient

from src import db
from src.main import app


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    db_path = tmp_path / "students.db"
    monkeypatch.setattr(db, "DB_PATH", db_path)
    return db_path


@pytest.fixture
def client():
    with TestClient(app) as c:  # the context manager runs the lifespan (init_db)
        yield c


def add_course(client, name="Mathematics"):
    response = client.post("/courses", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


@pytest.fixture
def course_id(client):
    return add_course(client)


def unit(course_id, **overrides):
    return {
        "name": "Algebra",
        "description": "Equations and inequalities",
        "courseId": course_id,
        **overrides,
    }


def create(client, course_id, **overrides):
    response = client.post("/courseUnits", json=unit(course_id, **overrides))
    assert response.status_code == 201, response.text
    return response.json()


# Database setup


def test_init_db_creates_empty_course_units_table(temp_db):
    db.init_db()
    with db.connect() as conn:
        columns = [r["name"] for r in conn.execute("PRAGMA table_info(courseUnits)")]
        fks = [dict(r) for r in conn.execute("PRAGMA foreign_key_list(courseUnits)")]
        total = conn.execute("SELECT COUNT(*) FROM courseUnits").fetchone()[0]
    assert columns == ["id", "name", "description", "courseId"]
    assert fks[0]["table"] == "courses" and fks[0]["from"] == "courseId"
    assert total == 0


# getAllCourseUnits


def test_get_all_course_units_empty(client):
    response = client.get("/courseUnits")
    assert response.status_code == 200
    assert response.json() == []


def test_get_all_course_units_ordered_by_id(client, course_id):
    first = create(client, course_id)
    second = create(client, course_id, name="Geometry")
    ids = [u["id"] for u in client.get("/courseUnits").json()]
    assert ids == [first["id"], second["id"]]


# getCourseUnit


def test_get_course_unit(client, course_id):
    created = create(client, course_id)
    response = client.get(f"/courseUnits/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


def test_get_course_unit_not_found(client):
    assert client.get("/courseUnits/999").status_code == 404


# postCourseUnit


def test_post_course_unit_returns_created_record(client, course_id):
    created = create(client, course_id)
    assert created == {**unit(course_id), "id": created["id"]}


def test_post_course_unit_description_is_optional(client, course_id):
    payload = {k: v for k, v in unit(course_id).items() if k != "description"}
    response = client.post("/courseUnits", json=payload)
    assert response.status_code == 201
    assert response.json()["description"] is None


def test_post_course_unit_duplicate_name_in_same_course(client, course_id):
    create(client, course_id)
    response = client.post("/courseUnits", json=unit(course_id))
    assert response.status_code == 409
    assert len(client.get("/courseUnits").json()) == 1


def test_post_course_unit_same_name_in_different_courses(client, course_id):
    physics = add_course(client, "Physics")
    create(client, course_id)
    create(client, physics)
    assert len(client.get("/courseUnits").json()) == 2


def test_post_course_unit_unknown_course(client):
    response = client.post("/courseUnits", json=unit(999))
    assert response.status_code == 422
    assert client.get("/courseUnits").json() == []


@pytest.mark.parametrize(
    "field, value",
    [("name", ""), ("name", None), ("courseId", None), ("courseId", "abc")],
)
def test_post_course_unit_invalid_input(client, course_id, field, value):
    response = client.post("/courseUnits", json=unit(course_id, **{field: value}))
    assert response.status_code == 422


@pytest.mark.parametrize("field", ["name", "courseId"])
def test_post_course_unit_missing_required_field(client, course_id, field):
    payload = {k: v for k, v in unit(course_id).items() if k != field}
    response = client.post("/courseUnits", json=payload)
    assert response.status_code == 422


# putCourseUnit


def test_put_course_unit_replaces_record(client, course_id):
    created = create(client, course_id)
    physics = add_course(client, "Physics")
    updated = unit(physics, name="Mechanics", description=None)
    response = client.put(f"/courseUnits/{created['id']}", json=updated)
    assert response.status_code == 200
    assert response.json() == {**updated, "id": created["id"]}
    assert client.get(f"/courseUnits/{created['id']}").json() == response.json()


def test_put_course_unit_omitted_description_becomes_null(client, course_id):
    created = create(client, course_id)
    payload = {"name": "Algebra", "courseId": course_id}
    response = client.put(f"/courseUnits/{created['id']}", json=payload)
    assert response.status_code == 200
    assert response.json()["description"] is None


def test_put_course_unit_keeping_own_name_succeeds(client, course_id):
    created = create(client, course_id)
    response = client.put(
        f"/courseUnits/{created['id']}", json=unit(course_id, description="New")
    )
    assert response.status_code == 200
    assert response.json()["description"] == "New"


def test_put_course_unit_not_found(client, course_id):
    response = client.put("/courseUnits/999", json=unit(course_id))
    assert response.status_code == 404


def test_put_course_unit_duplicate_name_in_same_course(client, course_id):
    create(client, course_id)
    other = create(client, course_id, name="Geometry")
    response = client.put(f"/courseUnits/{other['id']}", json=unit(course_id))
    assert response.status_code == 409
    assert client.get(f"/courseUnits/{other['id']}").json() == other


def test_put_course_unit_unknown_course(client, course_id):
    created = create(client, course_id)
    response = client.put(f"/courseUnits/{created['id']}", json=unit(999))
    assert response.status_code == 422
    assert client.get(f"/courseUnits/{created['id']}").json() == created


def test_put_course_unit_invalid_input(client, course_id):
    created = create(client, course_id)
    response = client.put(
        f"/courseUnits/{created['id']}", json=unit(course_id, name="")
    )
    assert response.status_code == 422
    assert client.get(f"/courseUnits/{created['id']}").json() == created


# deleteCourseUnit


def test_delete_course_unit(client, course_id):
    created = create(client, course_id)
    response = client.delete(f"/courseUnits/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"/courseUnits/{created['id']}").status_code == 404


def test_delete_course_unit_not_found(client):
    assert client.delete("/courseUnits/999").status_code == 404


# deleteCourse with units


def test_delete_course_with_units_is_blocked(client, course_id):
    create(client, course_id)
    response = client.delete(f"/courses/{course_id}")
    assert response.status_code == 409
    assert "course units" in response.json()["detail"]
    assert client.get(f"/courses/{course_id}").status_code == 200
    assert len(client.get("/courseUnits").json()) == 1


def test_delete_course_succeeds_after_units_deleted(client, course_id):
    created = create(client, course_id)
    client.delete(f"/courseUnits/{created['id']}")
    assert client.delete(f"/courses/{course_id}").status_code == 204
