"""Unit tests for the placeholder course endpoints: each returns an empty HTTP 200."""

import pytest
from fastapi.testclient import TestClient

from src import db
from src.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Startup still runs init_db, so keep it away from data/students.db.
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "students.db")
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize(
    "method, path",
    [
        ("GET", "/courses"),
        ("POST", "/courses"),
        ("PUT", "/courses/1"),
        ("DELETE", "/courses/1"),
    ],
)
def test_course_endpoints_return_empty_200(client, method, path):
    response = client.request(method, path)
    assert response.status_code == 200
    assert response.content == b""
