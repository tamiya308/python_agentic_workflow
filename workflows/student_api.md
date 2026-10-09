## Specs for
Student Records API

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
- Move connect, init_db, DB_PATH and the schema into a db.py
- Rename src/migrations to src/seeds (it holds seed data, not migrations)
- Replace students.course_name with course_id, a nullable foreign key to courses.id; seed students get a null course_id
- Rename all fields to camelCase (firstName, lastName, dateOfBirth, courseId) in the database, models and JSON. Python functions and variables stay snake_case. init_db() renames the columns in existing databases and keeps their data

## Endpoints
| Name | Request | Responses |
|---|---|---|
| GetAllStudents | `GET /students` | 200 with the list |
| getStudent | `GET /students/{id}` | 200, or 404 if the id doesn't exist |
| postStudent | `POST /students` | 201 with the new id; 409 on a duplicate email; 422 on invalid input or an unknown `courseId` |
| putStudent | `PUT /students/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate email, 422 on an unknown `courseId` |
| (courses, placeholder) | `GET /courses`, `POST /courses`, `PUT /courses/{id}`, `DELETE /courses/{id}` | Empty 200 for now |

Fields: `firstName`, `lastName`, `email` (must be unique), `dateOfBirth` (YYYY-MM-DD, optional), `grade` (integer, optional), `courseId` (optional; must be the `id` of an existing course).

