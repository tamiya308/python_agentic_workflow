# Student Records API

## Objective
Run the local REST API for creating, reading and updating student records, and seed it with sample data when needed.

## Original request
- Basic Python API to fetch and post student records
- Data persisted in a SQLite database in a `data/` folder in the project
- Local venv so pip packages stay in this project
- Endpoints: getStudent, putStudent, GetAllStudents, postStudent
- Later: 9 sample students added to the database
- Later2: Install the Ruff extension code formatter 
- Later2: Add a rule in the .claude/settings.local.json file to permit "running of Ruff formater without asking for permission" 

## Inputs
None required. Student data is stored in `data/students.db` (SQLite). The folder and table are created automatically.

## Tools
- `tools/student_api.py`: FastAPI app with the endpoints below
- `tools/seed_students.py`: inserts 9 sample students; safe to re-run (it skips existing emails)

## Steps
1. **One-time setup**, if `.venv/` is missing:
   ```powershell
   py -3.14 -m venv .venv
   .\.venv\Scripts\python -m pip install -e .
   ```
   Install any new packages only with `.\.venv\Scripts\python -m pip install <pkg>`, and add them to `pyproject.toml`.
2. **Seed sample data** (optional): `.\.venv\Scripts\python -m tools.seed_students`
3. **Start the server** from the project root:
   `.\.venv\Scripts\python -m uvicorn tools.student_api:app --reload`
4. **Use it.** Interactive docs are at http://127.0.0.1:8000/docs.

## Endpoints
| Name | Request | Responses |
|---|---|---|
| GetAllStudents | `GET /students` | 200 with the list |
| getStudent | `GET /students/{id}` | 200, or 404 if the id doesn't exist |
| postStudent | `POST /students` | 201 with the new id; 409 on a duplicate email; 422 on invalid input |
| putStudent | `PUT /students/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate email |

Fields: `first_name`, `last_name`, `email` (must be unique), `date_of_birth` (YYYY-MM-DD, optional), `grade` (integer, optional).

## Edge cases and notes
- Run every command from the project root. The `tools.` module imports depend on it.
- To reset the data, stop the server and delete `data/students.db`. It is recreated on the next start.
- PUT replaces the whole record. Send every field, or the omitted optional fields become null.
