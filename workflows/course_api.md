## Specs for
Courses & courseUnits endpoints in the Student Records API

## Objective
Serve basic GET, POST, PUT and DELETE endpoints for courses and their course units, backed by the SQLite database in `data/students.db`.

## Instructions
- Create or update the `courses` & `courseUnits` endpoints and database structure. Add sample seed data for courses when needed (`src/seeds/seed_courses.py`); `courseUnits` has no seed data.
- `src/api/course_api.py` serves `/courses`; `src/api/course_unit_api.py` serves `/courseUnits`. Both routers are registered in `src/main.py` with `app.include_router(...)`.
- Naming: database tables, columns and JSON/model fields are camelCase (`courseUnits`, `courseId`). Python functions and variables stay snake_case (`get_all_course_units`). The endpoint names below are labels, not Python names.

## Table structure
- `courses` table: `name` (required, unique, text, minlen=1), `description` (optional, text), `credits` (optional, integer, ge=0)
- `courseUnits` table: `name` (required, string, minlen=1), `description` (optional, text), `courseId` (required, integer, FK to `courses.id`). `UNIQUE(courseId, name)`: unit names only need to be unique within a course. No `ON DELETE CASCADE`. The table starts empty.
- `init_db()` in `src/db.py` creates both tables with `CREATE TABLE IF NOT EXISTS`, so existing databases get `courseUnits` on the next start without losing data.

## Model structure
Pydantic models in `src/models/course.py`, exported from `src/models/__init__.py`:
- `CourseIn` (request body) / `Course` (`CourseIn` + `id`)
- `CourseUnitIn` (request body) / `CourseUnit` (`CourseUnitIn` + `id`)

## Endpoint structure
| Name | Request | Responses |
|---|---|---|
| getAllCourses | `GET /courses` | 200 with the list, ordered by id |
| getCourse | `GET /courses/{id}` | 200, or 404 if the id doesn't exist |
| postCourse | `POST /courses` | 201 with the created record; 409 on a duplicate `name`; 422 on invalid input |
| putCourse | `PUT /courses/{id}` | 200 with the record; replaces the whole record; 404 if missing, 409 on a duplicate `name`, 422 on invalid input |
| deleteCourse | `DELETE /courses/{id}` | 204 on success; 404 if missing; 409 "Course {id} still has students or course units" if any students or courseUnits still reference it |

| Name | Request | Responses |
|---|---|---|
| getAllCourseUnits | `GET /courseUnits` | 200 with the list, ordered by id |
| getCourseUnit | `GET /courseUnits/{id}` | 200, or 404 if the id doesn't exist |
| postCourseUnit | `POST /courseUnits` | 201 with the created record; 409 on a duplicate `name` within the same course; 422 on invalid input or an unknown `courseId` |
| putCourseUnit | `PUT /courseUnits/{id}` | 200 with the record; replaces the whole record; 404 if missing, 409 on a duplicate `name` within the same course, 422 on invalid input or an unknown `courseId` |
| deleteCourseUnit | `DELETE /courseUnits/{id}` | 204 on success; 404 if missing |

## Inputs
- Request bodies as JSON matching `CourseIn` / `CourseUnitIn`. PUT replaces the whole record, so omitted optional fields become null.
- To test by hand: seed data with `.\tools\SeedData.ps1`, or add one course with `/seed-course`.

## Tools
| Step | Tool |
|---|---|
| Start the API (docs at http://127.0.0.1:8000/docs) | `.\tools\StartServer.ps1` |
| Seed sample courses and students | `.\tools\SeedData.ps1` |
| Reset the database (stop the server first) | `.\tools\DeleteDatabase.ps1` |
| Run the tests after every change | `.\tools\RunUnitTests.ps1` |
| Format, then test, before committing | `.\tools\PreCommitCheck.ps1` |

## Outputs
- `src/api/course_api.py`, `src/api/course_unit_api.py`, `src/models/course.py`, and the schemas in `src/db.py`
- Tests in `tests/test_course_api.py` and `tests/test_course_unit_api.py`, covering every response code in the tables above. Each test uses a temporary database (`tmp_path`).
- One git commit per logical change, after `PreCommitCheck.ps1` passes

## Edge cases
- **Unknown `courseId` vs duplicate name**: SQLite raises `sqlite3.IntegrityError` for both. Return 422 when the message contains `FOREIGN KEY`, otherwise 409 (same check as `student_api.py`).
- **Foreign keys** are only enforced when connections are opened through `connect()`, which sets `PRAGMA foreign_keys = ON`.
- **Deleting a course** that still has students or units fails with an `IntegrityError` and returns 409. Reassign or delete those first.
- **Same unit name in different courses** is allowed; only `(courseId, name)` must be unique.
- **PUT keeping its own name** succeeds; the uniqueness check only conflicts with other rows.
- A failed POST or PUT (404/409/422) leaves the database unchanged.
