"""Startup for the student records API: builds the app and routes requests.

Run from the project root:
    .\\.venv\\Scripts\\python -m uvicorn src.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .api import course_api, course_unit_api, student_api


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Student Records API", lifespan=lifespan)
app.include_router(student_api.router)
app.include_router(course_api.router)
app.include_router(course_unit_api.router)
