---
description: Insert one unique course into data/students.db, optionally from given name, description and credits
argument-hint: "[name], [description], [credits]"
---

Add exactly one course to `data/students.db`. Run every command from the project root with the project's `.venv`.

Arguments: `$ARGUMENTS`

## 1. Read the arguments
The arguments are optional and comma-separated, in the order **name, description, credits**. Any of them can be left out or left blank, and you fill in the missing ones in step 4.

- No arguments: choose all three values yourself.
- One value: it is the `name`.
- Two values: `name`, then `credits` if the second is a whole number, otherwise `description`.
- Three or more: the first is `name`, the last is `credits`, and everything in between (commas included) is the `description`. If the last value isn't a whole number, treat it as part of the description and leave `credits` to be chosen.
- A value wrapped in double quotes is taken as one value even if it contains commas, for example `"Art, Design and Media", Studio work, 2`.
- Trim spaces around each value. An empty value (as in `Chemistry, , 3`) counts as not given.

Examples:
- `/seed-course` → choose everything
- `/seed-course Chemistry` → name only
- `/seed-course Chemistry, 3` → name and credits
- `/seed-course Chemistry, Atoms, bonding and reactions, 3` → all three

## 2. Make sure the database exists
Run `.\.venv\Scripts\python -c "from src.db import init_db; init_db()"`. This creates the `courses` and `students` tables if they're missing, without deleting any rows.

## 3. Look at the existing courses
```powershell
@'
from src.db import connect
with connect() as conn:
    for row in conn.execute("SELECT * FROM courses ORDER BY id"):
        print(dict(row))
'@ | .\.venv\Scripts\python -
```

## 4. Settle the values
Every field must be filled in:

| Field | Rule |
|---|---|
| `name` | Non-empty text. Must not match any existing course name, compared case-insensitively (the column is `UNIQUE`) |
| `description` | Non-empty text that describes the course |
| `credits` | Whole number, 0 or higher |

- **Values I gave**: use them exactly as given. If one breaks a rule (the name already exists, credits isn't a whole number or is negative), stop and tell me which value and why. Don't change it or substitute your own.
- **Values I left out**: choose realistic ones for a school course (credits usually 1 to 5). A chosen name must not repeat an existing one, and the description should fit the name.

## 5. Insert it
Insert through the project's own model and helpers, so validation matches the API:

```powershell
@'
from src.api.course_api import COURSE_COLUMNS, to_params
from src.db import connect
from src.models import CourseIn

course = CourseIn(
    name="<name>",
    description="<description>",
    credits=<credits>,
)
with connect() as conn:
    cur = conn.execute(
        f"INSERT INTO courses ({', '.join(COURSE_COLUMNS)}) VALUES (?, ?, ?)",
        to_params(course),
    )
    print("Inserted id", cur.lastrowid)
'@ | .\.venv\Scripts\python -
```

Escape any double quotes or backslashes inside the values so the Python strings stay valid. Use a plain `INSERT` (not `INSERT OR IGNORE`) so a duplicate name fails loudly. If it fails with `UNIQUE constraint failed`: when you chose the name, pick another and retry; when I gave it, stop and tell me. If `CourseIn` raises a validation error, report it the same way.

## 6. Verify
Fetch the new row by its id. Confirm every field is populated and the course count went up by exactly one. Report the inserted course (id and all fields) back to me, and say which values came from my arguments and which you chose.

## Don'ts
- Don't modify or delete existing courses or students.
- Don't insert more than one course.
- Don't edit `src/seeds/seed_courses.py`; this is a one-off insert, not a change to the sample data.
