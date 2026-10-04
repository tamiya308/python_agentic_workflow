# Student Records API

## Objective
Run the local REST API for creating, reading and updating student records, and seed it with sample data when needed.

## Original request
- Basic Python API to fetch and post student records
- Data persisted in a SQLite database in a `data/` folder in the project
- Local venv so pip packages stay in this project
- Endpoints: getStudent, putStudent, GetAllStudents, postStudent
- Later: 9 sample students added to the database
- Later: Install the Ruff extension code formatter 
- Later: Add a rule in the .claude/settings.local.json file to permit "running of Ruff formater without asking for permission"
- Later: Add a new property couseName into the student model. Also add this to the sql lite database 
- Later: Set course_name to "nothing" for the existing students. course_name stays optional, so new students don't need one
- Later: Write automated unit tests for the project using a popular Python testing framework (pytest)
- Later: Make git commits every time a series of instructions is carried out (see "Git commits" below)

## Inputs
None required. Student data is stored in `data/students.db` (SQLite). The folder and table are created automatically.

## Tools
- `tools/student_api.py`: FastAPI app with the endpoints below
- `tools/seed_students.py`: inserts 9 sample students; safe to re-run (it skips existing emails)
- `tools/test_student_api.py`: pytest unit tests for every endpoint, validation, the database migration and the seed script

## Steps
1. **One-time setup**, if `.venv/` is missing:
   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python -m pip install -e ".[dev]"
   ```
   `[dev]` adds the test and formatting tools (pytest, httpx2, ruff).
   Install any new packages only with `.\.venv\Scripts\python -m pip install <pkg>`, and add them to `pyproject.toml`.
2. **Seed sample data** (optional): `.\.venv\Scripts\python -m tools.seed_students`
3. **Start the server** from the project root:
   `.\.venv\Scripts\python -m uvicorn tools.student_api:app --reload`
4. **Use it.** Interactive docs are at http://127.0.0.1:8000/docs.
5. **Run the tests** after every code change: `.\.venv\Scripts\python -m pytest`
   All tests must pass before committing.

## Git commits
Every time I ask for a series of instructions to be carried out, finish with a git commit:
1. Run `ruff format tools/` and `.\.venv\Scripts\python -m pytest`. Don't commit if a test fails; fix it or report it first.
2. Commit only project files (`tools/`, `workflows/`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`). Never commit `.env`, `credentials.json`, `token.json`, `data/*.db` or `.venv/`; `.gitignore` already excludes them.
3. Make one commit per logical change, with a message that says what changed and why.

## Endpoints
| Name | Request | Responses |
|---|---|---|
| GetAllStudents | `GET /students` | 200 with the list |
| getStudent | `GET /students/{id}` | 200, or 404 if the id doesn't exist |
| postStudent | `POST /students` | 201 with the new id; 409 on a duplicate email; 422 on invalid input |
| putStudent | `PUT /students/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate email |

Fields: `first_name`, `last_name`, `email` (must be unique), `date_of_birth` (YYYY-MM-DD, optional), `grade` (integer, optional), `course_name` (text, optional).

## Edge cases and notes
- Run every command from the project root. The `tools.` module imports depend on it.
- To reset the data, stop the server and delete `data/students.db`. It is recreated on the next start.
- New columns: add them to `SCHEMA`, `COLUMNS` and `StudentIn` in `tools/student_api.py`, plus an `ALTER TABLE` check in `init_db()` so existing databases are upgraded on the next start without losing data.
- Format code with `ruff format tools/` (Ruff is installed in `.venv`). Don't run `ruff format *`, which also reaches other directories.
- Tests use a temporary database for each test (pytest's `tmp_path`), so they never touch `data/students.db`.
- Tests live in `tools/` rather than a `tests/` folder, because `CLAUDE.md` only allows the listed directories.
- Use `httpx2`, not `httpx`, for FastAPI's `TestClient`. With `httpx` this Starlette version prints a deprecation warning.
- PUT replaces the whole record. Send every field, or the omitted optional fields become null.
