---
description: Insert a handful of basic course units for each course in data/students.db, optionally for one course and with a given count
argument-hint: "[course id or name], [units per course]"
---

Add a handful of basic units to the courses in `data/students.db`. Run every command from the project root with the project's `.venv`.

Arguments: `$ARGUMENTS`

## 1. Read the arguments
The arguments are optional and comma-separated, in the order **course, units per course**.

- No arguments: seed every course that has no units yet, with 4 units each.
- One value: a whole number is the `units per course` (for every course without units); anything else is the course, given by `id` or by `name` (matched case-insensitively).
- Two values: the course, then the `units per course`.
- `units per course` must be a whole number from 1 to 10. The default is 4.
- Trim spaces around each value. An empty value (as in `, 3`) counts as not given.

Examples:
- `/seed-course-units` → 4 units for every course without units
- `/seed-course-units 3` → 3 units for every course without units
- `/seed-course-units Physics I` → 4 units for that course only
- `/seed-course-units 2, 5` → 5 units for the course with id 2

## 2. Make sure the database exists
Run `.\.venv\Scripts\python -c "from src.db import init_db; init_db()"`. This creates the `courses`, `courseUnits` and `students` tables if they're missing, without deleting any rows.

## 3. Look at the existing courses and units
```powershell
@'
from src.db import connect
with connect() as conn:
    for table in ("courses", "courseUnits"):
        print(f"--- {table}")
        for row in conn.execute(f"SELECT * FROM {table} ORDER BY id"):
            print(dict(row))
'@ | .\.venv\Scripts\python -
```

If the `courses` table is empty, stop and tell me. Don't insert a course to have one to attach units to.

## 4. Pick the courses
- **A course I gave**: use it even if it already has units. If no course matches the id or name, stop and tell me.
- **No course given**: use every course that has no units yet. If every course already has units, stop and tell me there's nothing to seed.

## 5. Choose the units
For each picked course, choose the given number of units:

| Field | Rule |
|---|---|
| `name` | Non-empty text. A basic, introductory topic that fits the course name (and description, if it has one). Must not match a unit name the course already has, compared case-insensitively (the table has `UNIQUE(courseId, name)`) |
| `description` | Non-empty text, one short sentence describing the unit |
| `courseId` | The `id` of the picked course. Never make up an id |

- Order the units the way they'd be taught, from the basics to more advanced topics.
- Units in different courses may share a name; only names within the same course must be unique.

Example for "Introduction to Computer Science": Variables and Data Types, Control Flow, Functions, Basic Algorithms.

## 6. Insert them
Insert through the project's own model and helpers, so validation matches the API. Put every unit for every picked course in the `units` list and insert them in one connection:

```powershell
@'
from src.api.course_unit_api import COURSE_UNIT_COLUMNS, to_params
from src.db import connect
from src.models import CourseUnitIn

units = [
    CourseUnitIn(name="<name>", description="<description>", courseId=<courseId>),
    # ...one line per unit
]
with connect() as conn:
    for unit in units:
        cur = conn.execute(
            f"INSERT INTO courseUnits ({', '.join(COURSE_UNIT_COLUMNS)}) VALUES (?, ?, ?)",
            to_params(unit),
        )
        print("Inserted id", cur.lastrowid, unit.courseId, unit.name)
'@ | .\.venv\Scripts\python -
```

Escape any double quotes or backslashes inside the values so the Python strings stay valid. Use a plain `INSERT` (not `INSERT OR IGNORE`) so a duplicate name fails loudly. Because all the inserts share one connection, a failure rolls the whole batch back. If it fails with `UNIQUE constraint failed`, rename the clashing unit and rerun the whole batch. If it fails with `FOREIGN KEY constraint failed`, a `courseId` is wrong: check it against the list in step 3. If `CourseUnitIn` raises a validation error, fix the offending value.

## 7. Verify
List the units of each picked course again. Confirm every field is populated and the unit count went up by exactly the number inserted. Report the inserted units back to me, grouped by course (course id and name, then each unit's id, name and description).

## Don'ts
- Don't modify or delete existing courses, course units or students.
- Don't insert courses.
- Don't add units to courses that already have units unless I named the course.
- Don't edit `src/seeds/seed_courses.py` or add a seed script; this is a one-off insert, not a change to the sample data.
