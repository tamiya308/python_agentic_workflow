"""Course endpoints. Placeholders for now: each one returns an empty HTTP 200 response."""

from fastapi import APIRouter, Response

router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("")
def get_courses():
    return Response(status_code=200)


@router.post("")
def post_course():
    return Response(status_code=200)


@router.put("/{course_id}")
def put_course(course_id: int):
    return Response(status_code=200)


@router.delete("/{course_id}")
def delete_course(course_id: int):
    return Response(status_code=200)
