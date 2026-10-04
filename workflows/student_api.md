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
- Later: Restructure: Move all the classes into a "projectRootDir\src\models" folder.
- Later: Restructure: Move all startup code into "projectRootDir\src\main.py"
- Later: Restructure: In [@main.py] perform the initial students routing to the [@student_api.py] file
- Later: Move the [@student_api.py] file into the "projectRootDir\src\api" directory
- Later: Move the [@test_student_api.py] file into the "projectRootDir\tests" directory
- Later: Move the [@seed_students.py] file into the "projectRootDir\src\migrations" directory
- Later: Generate a [@course_api.py] file with functions that serve as endpoints for basic GET, POST, PUT and DELETE verbs. Create these functions but don't put anything in them (just return empty HTTP 200 responses). Also update the [@main.py] file to point HTTP requests with "course" in the path to this [@course_api.py] file

## Inputs
None required. Student data is stored in `data/students.db` (SQLite). The folder and table are created automatically.

## Code layout
- `src/main.py`: startup. Builds the FastAPI app, runs `init_db()` on startup, and routes `/students` and `/courses` to the API modules
- `src/models/student.py`: Pydantic models (`StudentIn`, `Student`), re-exported from `src.models`
- `src/api/student_api.py`: student endpoints (an `APIRouter` with prefix `/students`) plus the SQLite helpers (`connect`, `init_db`, `SCHEMA`, `COLUMNS`)
- `src/api/course_api.py`: placeholder course endpoints (prefix `/courses`); each returns an empty 200
- `src/migrations/seed_students.py`: inserts 9 sample students; safe to re-run (it skips existing emails)
- `tests/test_student_api.py`: pytest unit tests for every student endpoint, validation, the database migration and the seed script
- `tests/test_course_api.py`: checks each course endpoint returns an empty 200

## Steps
1. **One-time setup**, if `.venv/` is missing:
   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python -m pip install -e ".[dev]"
   ```
   `[dev]` adds the test and formatting tools (pytest, httpx2, ruff).
   Install any new packages only with `.\.venv\Scripts\python -m pip install <pkg>`, and add them to `pyproject.toml`.
2. **Seed sample data** (optional): `.\.venv\Scripts\python -m src.migrations.seed_students`
3. **Start the server** from the project root:
   `.\.venv\Scripts\python -m uvicorn src.main:app --reload`
4. **Use it.** Interactive docs are at http://127.0.0.1:8000/docs.
5. **Run the tests** after every code change: `.\.venv\Scripts\python -m pytest`
   All tests must pass before committing.

## Git commits
Every time I ask for a series of instructions to be carried out, finish with a git commit:
1. Run `ruff format src tests` and `.\.venv\Scripts\python -m pytest`. Don't commit if a test fails; fix it or report it first.
2. Commit only project files (`src/`, `tests/`, `tools/`, `workflows/`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`). Never commit `.env`, `credentials.json`, `token.json`, `data/*.db` or `.venv/`; `.gitignore` already excludes them.
3. Make one commit per logical change, with a message that says what changed and why.

## Endpoints
| Name | Request | Responses |
|---|---|---|
| GetAllStudents | `GET /students` | 200 with the list |
| getStudent | `GET /students/{id}` | 200, or 404 if the id doesn't exist |
| postStudent | `POST /students` | 201 with the new id; 409 on a duplicate email; 422 on invalid input |
| putStudent | `PUT /students/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate email |
| (courses, placeholder) | `GET /courses`, `POST /courses`, `PUT /courses/{id}`, `DELETE /courses/{id}` | Empty 200 for now |

Fields: `first_name`, `last_name`, `email` (must be unique), `date_of_birth` (YYYY-MM-DD, optional), `grade` (integer, optional), `course_name` (text, optional).

## Edge cases and notes
- Run every command from the project root. The `src.` module imports depend on it.
- To reset the data, stop the server and delete `data/students.db`. It is recreated on the next start.
- New columns: add them to `SCHEMA` and `COLUMNS` in `src/api/student_api.py` and to `StudentIn` in `src/models/student.py`, plus an `ALTER TABLE` check in `init_db()` so existing databases are upgraded on the next start without losing data.
- Format code with `ruff format src tests` (Ruff is installed in `.venv`). Don't run `ruff format *`, which also reaches other directories.
- Tests use a temporary database for each test (pytest's `tmp_path`), so they never touch `data/students.db`.
- New routers: create the module in `src/api/` with an `APIRouter(prefix=...)` and register it in `src/main.py` with `app.include_router(...)`.
- Any test that uses `TestClient(app)` triggers startup, which runs `init_db()`. Point `student_api.DB_PATH` at `tmp_path` first so the real database isn't touched.
- pytest collects from `tests/`, and `pyproject.toml` puts the project root on the path (`pythonpath = ["."]`) so `import src...` works.
- Use `httpx2`, not `httpx`, for FastAPI's `TestClient`. With `httpx` this Starlette version prints a deprecation warning.
- PUT replaces the whole record. Send every field, or the omitted optional fields become null.
