"""Pydantic models for student records."""

from datetime import date

from pydantic import BaseModel, Field


class StudentIn(BaseModel):
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    date_of_birth: date | None = None
    grade: int | None = Field(default=None, ge=0)
    course_name: str | None = None


class Student(StudentIn):
    id: int
