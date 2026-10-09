## Specs for
- courses & courseUnits end points in the Students Api

## Instructions
- Create or update the courses & courseUnits end points & database structure. Update them with sample seed data when needed.
- CReate or updatethe [@course_api.py] file with functions that serve as endpoints for basic GET, POST, PUT and DELETE verbs. Create these functions but don't put anything in them (just return empty HTTP 200 responses). Also update the [@main.py] file to point HTTP requests with "courses" in the path to this [@course_api.py] file
- Add a course model (src/models/course.py) and a courses table with basic fields

## Table structure
- Create a new courseUnits table. Also create the corresponding model inside the models/course.py file
- The courses fields (`courses` table): `name` (required, unique, text, minlen=1), `description` (optional, text), `credits` (optional, integer, ge=0)
- The courseUnits fields (`courseUnits` table): `name` (required, unique), `description` (text, optional), `courseId` (required, integer, FK to courses.id). The table starts empty.

## Model structure
-Create or update the models\course.py class. Put the Course class & CourseUnits classes in here. Use the Pydantic model. 

## Endpoint structure
| Name | Request | Responses |
|---|---|---|
| getAllCourses | `GET /courses` | 200 with the list |
| getCourse | `GET /courses/{id}` | 200, or 404 if the id doesn't exist |
| postCourse | `POST /courses` | 201 with the new id; 409 on a duplicate `name`; 422 on invalid input |
| putCourse | `PUT /courses/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate `name`, 422 on invalid input |
| deleteCourse | `DELETE /courses/{id}` | 204 on success; 404 if missing; 409 if any students or courseUnits still reference the course |

| Name | Request | Responses |
|---|---|---|
| getAllCourseUnits | `GET /courseUnits` | 200 with the list |
| getCourseUnit | `GET /courseUnits/{id}` | 200, or 404 if the id doesn't exist |
| postCourseUnit | `POST /courseUnits` | 201 with the new id; 409 on a duplicate `name`; 422 on invalid input or an unknown `courseId` |
| putCourseUnit | `PUT /courseUnits/{id}` | Replaces the whole record; 404 if missing, 409 on a duplicate `name`, 422 on invalid input or an unknown `courseId` |
| deleteCourseUnit | `DELETE /courseUnits/{id}` | 204 on success; 404 if missing |
