---
description: Insert one unique dummy student, with every field filled (course_id when a course exists), into data/students.db
---

Add exactly one dummy student to `data/students.db`. Run every command from the project root with the project's `.venv`.

## 1. Make sure the database exists
Run `.\.venv\Scripts\python -c "from src.db import init_db; init_db()"`. This creates the `courses` and `students` tables, or upgrades an older `students` table (adds `course_id`, drops the old `course_name`), without deleting any rows.

## 2. Look at the existing students and courses
List every current student and course so the new student can be checked against them:

```powershell
@'
from src.db import connect
with connect() as conn:
    for table in ("students", "courses"):
        print(f"--- {table}")
        for row in conn.execute(f"SELECT * FROM {table}"):
            print(dict(row))
'@ | .\.venv\Scripts\python -
```

## 3. Choose the new student's values
Fill in **every** field; none may be null or empty, except `course_id` when there are no courses:

| Field | Rule |
|---|---|
| `first_name` | Non-empty text |
| `last_name` | Non-empty text |
| `email` | Valid format (`name@domain.tld`); must not match any existing email (the column is `UNIQUE`) |
| `date_of_birth` | `YYYY-MM-DD`, a real date in the past |
| `grade` | Integer, 0 or higher |
| `course_id` | The `id` of an existing row in `courses` (it is a foreign key to `courses.id`). If the `courses` table is empty, use `None`. Never make up an id, and don't insert a course to have one to point to |

The record must be unique from every existing one:
- The `first_name` + `last_name` pair must not already exist.
- The `email` must not already exist (compare case-insensitively).
- The whole set of values must not repeat an existing row.

Use a clearly fake address on the `example.com` domain, for example `firstname.lastname@example.com`.

## 4. Insert it
Insert the record through the project's own model and helpers, so validation matches the API:

```powershell
@'
from src.api.student_api import to_params
from src.db import COLUMNS, PLACEHOLDERS, connect
from src.models import StudentIn

student = StudentIn(
    first_name="<first>",
    last_name="<last>",
    email="<email>",
    date_of_birth="<YYYY-MM-DD>",
    grade=<grade>,
    course_id=<course_id or None>,
)
with connect() as conn:
    cur = conn.execute(
        f"INSERT INTO students ({', '.join(COLUMNS)}) VALUES ({PLACEHOLDERS})",
        to_params(student),
    )
    print("Inserted id", cur.lastrowid)
'@ | .\.venv\Scripts\python -
```

Use a plain `INSERT` (not `INSERT OR IGNORE`) so a duplicate email fails loudly. If it fails with `UNIQUE constraint failed`, pick a different email and retry. If it fails with `FOREIGN KEY constraint failed`, the `course_id` doesn't exist in `courses`: pick one from the list in step 2, or use `None`. If `StudentIn` raises a validation error, fix the offending value.

## 5. Verify
Fetch the new row by its email and confirm that every field is populated (`course_id` may be null only when there are no courses) and that the total count went up by exactly one. Report the inserted record (id and all fields) back to me.

## Don'ts
- Don't modify or delete existing students.
- Don't insert more than one student.
- Don't insert, modify or delete courses.
- Don't edit `src/seeds/seed_students.py`; this is a one-off insert, not a change to the sample data.
