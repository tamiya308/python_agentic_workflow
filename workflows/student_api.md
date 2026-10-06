# Student Records API

## Objective
Run the local REST API for creating, reading and updating student records, and seed it with sample data when needed.

## Original request
- Basic Python API to fetch and post student records
- Data persisted in a SQLite database in a `data/` folder in the project
- Local venv so pip packages stay in this project
- Endpoints: getStudent, putStudent, GetAllStudents, postStudent
- 9 sample students added to the database
- Install the Ruff extension code formatter 
- Add a rule in the .claude/settings.local.json file to permit "running of Ruff formater without asking for permission"
- Add a new property couseName into the student model. Also add this to the sql lite database 
- Set course_name to "nothing" for the existing students. course_name stays optional, so new students don't need one
- Write automated unit tests for the project using a popular Python testing framework (pytest)
- Make git commits every time a series of instructions is carried out (see "Git commits" below)
- Restructure: Move all the classes into a "projectRootDir\src\models" folder.
- Restructure: Move all startup code into "projectRootDir\src\main.py"
- Restructure: In [@main.py] perform the initial students routing to the [@student_api.py] file
- Move the [@student_api.py] file into the "projectRootDir\src\api" directory
- Move the [@test_student_api.py] file into the "projectRootDir\tests" directory
- Move the [@seed_students.py] file into the "projectRootDir\src\migrations" directory
- Generate a [@course_api.py] file with functions that serve as endpoints for basic GET, POST, PUT and DELETE verbs. Create these functions but don't put anything in them (just return empty HTTP 200 responses). Also update the [@main.py] file to point HTTP requests with "course" in the path to this [@course_api.py] file
- Move connect, init_db, DB_PATH and the schema into a db.py
- Rename src/migrations to src/seeds (it holds seed data, not migrations)
- Add a course model (src/models/course.py) and a courses table with basic fields; no course records are inserted
- Replace students.course_name with course_id, a nullable foreign key to courses.id; seed students get a null course_id

## Inputs
None required. Student data is stored in `data/students.db` (SQLite). The folder and table are created automatically.

## Code layout
- `src/main.py`: startup. Builds the FastAPI app, runs `db.init_db()` on startup, and routes `/students` and `/courses` to the API modules
- `src/models/student.py`: Pydantic models (`StudentIn`, `Student`), re-exported from `src.models`
- `src/models/course.py`: Pydantic models (`CourseIn`, `Course`), re-exported from `src.models`
- `src/db.py`: SQLite storage: `DB_PATH`, `COURSES_SCHEMA`, `SCHEMA`, `COLUMNS`, `connect()` (turns on foreign key checks) and `init_db()` (creates both tables and upgrades old databases)
- `src/api/student_api.py`: student endpoints (an `APIRouter` with prefix `/students`) plus helpers that convert between `StudentIn`/`Student` and database rows
- `src/api/course_api.py`: placeholder course endpoints (prefix `/courses`); each returns an empty 200
- `src/seeds/seed_students.py`: inserts 9 sample students; safe to re-run (it skips existing emails)
- `tests/test_student_api.py`: pytest unit tests for every student endpoint, validation, the database migration and the seed script
- `tests/test_course_api.py`: checks each course endpoint returns an empty 200
- `tools/RunUnitTests.ps1`: runs the full pytest suite with the project's `.venv`; run it from the project root
- `tools/SeedData.ps1`: inserts the sample students into `data/students.db` with the project's `.venv`; run it from the project root
- `tools/StartServer.ps1`: starts the API with uvicorn (auto-reload on code changes) using the project's `.venv`; run it from the project root
- `tools/FormatPythonFile.ps1`: formats the Python code in `src/` and `tests/` with Ruff; run it from the project root
- `tools/PreCommitCheck.ps1`: formats `src/` and `tests/` with Ruff, then runs the full pytest suite; run it before every commit

## Steps
1. **One-time setup**, if `.venv/` is missing:
   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python -m pip install -e ".[dev]"
   ```
   `[dev]` adds the test and formatting tools (pytest, httpx2, ruff).
   Install any new packages only with `.\.venv\Scripts\python -m pip install <pkg>`, and add them to `pyproject.toml`.
2. **Seed sample data** (optional), from the project root: `.\tools\SeedData.ps1`
3. **Start the server**, from the project root: `.\tools\StartServer.ps1`
4. **Use it.** Interactive docs are at http://127.0.0.1:8000/docs.
5. **Run the tests** after every code change, from the project root: `.\tools\RunUnitTests.ps1`. All tests must pass before committing.

## Git commits
Every time I ask for a series of instructions to be carried out, finish with a git commit:
1. Run `.\tools\PreCommitCheck.ps1` (formats with Ruff, then runs the tests). Don't commit if a test fails; fix it or report it first.
2. Commit only project files (`src/`, `tests/`, `tools/`, `workflows/`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`). Never commit `.env`, `credentials.json`, `token.json`, `data/*.db` or `.venv/`; `.gitignore` already excludes them.
3. Make one commit per logical change, with a message that says what changed and why.

## Endpoints
| Name | Request | Responses |
|---|---|---|
| GetAllStudents | `GET /students` | 200 with the list |
| getStudent | `GET /students/{id}` | 200, or 404 if the id doesn't exist |
| postStudent | `POST /students` | 201 with the new id; 409 on a duplicate email; 422 on invalid input or an unknown `course_id` |
| putStudent | `PUT /students/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate email, 422 on an unknown `course_id` |
| (courses, placeholder) | `GET /courses`, `POST /courses`, `PUT /courses/{id}`, `DELETE /courses/{id}` | Empty 200 for now |

Fields: `first_name`, `last_name`, `email` (must be unique), `date_of_birth` (YYYY-MM-DD, optional), `grade` (integer, optional), `course_id` (optional; must be the `id` of an existing course).

Course fields (`courses` table): `name` (required, unique), `description` (text, optional), `credits` (integer, optional). The table starts empty.

## Edge cases and notes
- Run every command from the project root. The `src.` module imports depend on it.
- To reset the data, stop the server and delete `data/students.db`. It is recreated on the next start.
- Foreign keys: SQLite only enforces them when `PRAGMA foreign_keys = ON` is set on each connection. `connect()` does this, so always open connections through it.
- Upgrading old databases: `init_db()` adds `course_id` and drops the old `course_name` column (needs SQLite 3.35+). Values in `course_name` are lost; they were free text and can't be mapped to course ids.
- New columns: add them to `SCHEMA` and `COLUMNS` in `src/db.py` and to `StudentIn` in `src/models/student.py`, plus an `ALTER TABLE` check in `init_db()` so existing databases are upgraded on the next start without losing data.
- Format code with `.\tools\FormatPythonFile.ps1`, which runs `ruff format src tests` (Ruff is installed in `.venv`). Don't run `ruff format *`, which also reaches other directories.
- Tests use a temporary database for each test (pytest's `tmp_path`), so they never touch `data/students.db`.
- New routers: create the module in `src/api/` with an `APIRouter(prefix=...)` and register it in `src/main.py` with `app.include_router(...)`.
- Any test that uses `TestClient(app)` triggers startup, which runs `init_db()`. Point `db.DB_PATH` at `tmp_path` first so the real database isn't touched.
- pytest collects from `tests/`, and `pyproject.toml` puts the project root on the path (`pythonpath = ["."]`) so `import src...` works.
- Use `httpx2`, not `httpx`, for FastAPI's `TestClient`. With `httpx` this Starlette version prints a deprecation warning.
- PUT replaces the whole record. Send every field, or the omitted optional fields become null.
