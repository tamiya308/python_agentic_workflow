# CLAUDE.md
This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Agent Instructions
You're working inside the **WAT framework** (Workflows, Agents, Tools). This architecture separates concerns so that probabilistic AI handles reasoning while deterministic code handles execution. That separation is what makes this system reliable.

## The WAT Architecture
**Layer 1: Workflows (The Instructions)**
- Markdown SOPs stored in `workflows/`
- Each workflow defines the objective, required inputs, which tools to use, expected outputs, and how to handle edge cases
- Written in plain language, the same way you'd brief someone on your team

**Layer 2: Agents (The Decision-Maker)**
- This is your role. You're responsible for intelligent coordination.
- Read the relevant workflow, run tools in the correct sequence, handle failures gracefully, and ask clarifying questions when needed
- You connect intent to execution without trying to do everything yourself
- Example (illustrative only; these files don't exist yet): If you need to pull data from a website, don't attempt it directly. Read `workflows/scrape_website.md`, figure out the required inputs, then execute `tools/scrape_single_site.py`

**Layer 3: Tools (The Execution)**
- Python & powershell scripts in `tools/` that do the work
- API calls, data transformations, file operations, database queries
- Credentials and API keys are stored in `.env`
- These scripts are consistent, testable, and fast

## How to Operate
- Try to reuse exsting tools in the `tools/` folder.
- Ask clarifying questions if needed. 
- Create a plan for tasks with any complexity. Ask user to approve tasks before proceeding

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

## File Structure
**What goes where:**
- **Deliverables**: Final outputs go to cloud services (Google Sheets, Slides, etc.) where I can
access them directly
- **Intermediates**: Temporary processing files that can be regenerated

**Directory layout:**
```
.github/    * Git files
.tmp/		# Temporary files (scraped data, intermediate exports). Regenerated as needed.
tools/		# Python scripts for deterministic execution
workflows/	# Markdown SOPs defining what to do and how
.env		# API keys and environment variables (NEVER store secrets anywhere else)
out/		# Local final outputs, only when a deliverable can't go to a cloud service
credentials.json, token.json	# Google OAuth (gitignored). Loaded by tools only; don't open them directly
```

**Core principle:** Local files are just for processing. Anything I need to see or use lives in cloud
services. Everything in `.tmp/` is disposable.

**Plans:** Save agent working plans to `.tmp/plans/`. A plan I need to review or share goes to a cloud
service (or `out/` if it can't). A plan that should become a repeatable procedure goes in `workflows/`,
but only after asking me first.

## Context Boundaries (STRICT)
ALLOWED directories (you may read, write, and list):
- `src/*`
- `tests/`
- `tools/`
- `workflows/`
- `config/` (if present)
- `.tmp/` (for generated data only)
- `out/` (for final outputs)
- `data/` (SQLite database for the student records API)
- `.venv/` (project-local virtualenv; install packages here only)
- Root-level files only: `.env`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`

FORBIDDEN directories (you MUST NOT read, list, open, or access in any way):
- `docs/`
- Any other directory not listed above

This applies to you AND to any sub-agent you spawn. If you launch an Explore agent, constrain its scope to the allowed directories only. If you believe you need access to a forbidden directory, ask the user FIRST.

## Language Type
- Never make assumptions when important information is missing.
- Keep outputs concise and relevant.
- Do not add filler content to increase length.
- Stay within requested word counts and formats.
- Use practical examples whenever possible.
- When multiple approaches exist, explain the tradeoffs.
- If uncertain, ask before proceeding.
- Review outputs before final delivery.

## Git commits
Every time I ask for a series of instructions to be carried out, finish with a git commit:
1. Run `.\tools\PreCommitCheck.ps1` (formats with Ruff, then runs the tests). Don't commit if a test fails; fix it or report it first.
2. Commit only project files (`src/`, `tests/`, `tools/`, `workflows/`, `pyproject.toml`, `.gitignore`, `CLAUDE.md`). Never commit `.env`, `credentials.json`, `token.json`, `data/*.db` or `.venv/`; `.gitignore` already excludes them.
3. Make one commit per logical change, with a message that says what changed and why.

## Edge cases and notes
- Run every command from the project root. The `src.` module imports depend on it.
- To reset the data, stop the server and run `.\tools\DeleteDatabase.ps1`. It fails while the server is running, because the server keeps the file open. The database is recreated on the next start; run `.\tools\SeedData.ps1` to add the sample students back.
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
