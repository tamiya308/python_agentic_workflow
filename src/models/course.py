"""Pydantic models for course records."""

from pydantic import BaseModel, Field


class CourseIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    credits: int | None = Field(default=None, ge=0)


class Course(CourseIn):
    id: int
