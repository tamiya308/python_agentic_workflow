"""Pydantic models for course and course unit records."""

from pydantic import BaseModel, Field


class CourseIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    credits: int | None = Field(default=None, ge=0)


class Course(CourseIn):
    id: int


class CourseUnitIn(BaseModel):
    name: str = Field(min_length=1)
    description: str | None = None
    courseId: int


class CourseUnit(CourseUnitIn):
    id: int
