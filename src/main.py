"""Startup for the student records API: builds the app and routes requests.

Run from the project root:
    .\\.venv\\Scripts\\python -m uvicorn src.main:app --reload
Interactive docs: http://127.0.0.1:8000/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api import student_api


@asynccontextmanager
async def lifespan(_: FastAPI):
    student_api.init_db()
    yield


app = FastAPI(title="Student Records API", lifespan=lifespan)
app.include_router(student_api.router)
