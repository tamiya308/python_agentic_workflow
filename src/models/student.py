"""Pydantic models for student records."""

from datetime import date

from pydantic import BaseModel, Field


class StudentIn(BaseModel):
    firstName: str = Field(min_length=1)
    lastName: str = Field(min_length=1)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    dateOfBirth: date | None = None
    grade: int | None = Field(default=None, ge=0)
    courseId: int | None = None


class Student(StudentIn):
    id: int
