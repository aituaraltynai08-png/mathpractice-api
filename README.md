# MathPractice API

Teachers create math topics and problems, publish topics and give homework with deadlines.
Students enroll, unlock levels (easy -> medium -> hard), solve problems and do homework.
The API checks answers, gives hints, counts points, and shows progress, leaderboards and statistics.

Stack: FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic.

## Run

1. Create a PostgreSQL database named `mathpractice`.
2. Copy `.env.example` to `.env` and put your connection string in `DATABASE_URL`.
3. Install and start:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head      # creates all tables
python -m app.seed        # demo data (only once)
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

Demo users: 1, 2 = teachers; 3, 4 = students.
Topics: 1 Fractions and 2 Linear equations (published), 3 Quadratic equations (draft, no problems).
Homework: "Homework 1: equations" (due in a week), "Homework 0: fractions" (deadline passed).

## Structure

- `app/main.py` - creates the app, connects routers
- `app/database.py` - database connection (from `DATABASE_URL`), session for each request
- `app/models.py` - SQLAlchemy tables and relationships
- `app/schemas.py` - Pydantic request and response models
- `app/services.py` - business logic
- `app/routers/` - endpoints (users, topics, problems, assignments)
- `app/seed.py` - demo data
- `alembic/versions/` - database migrations

## Tables and relationships

- users: one teacher -> many topics (one-to-many)
- topics: one topic -> many problems (one-to-many)
- problems: one problem -> many attempts (one-to-many)
- assignments: one topic -> many assignments, one assignment -> many problems (one-to-many)
- enrollments: students <-> topics (many-to-many)
- attempts: belong to a problem and a student

Constraints: unique email, unique topic title per teacher, one enrollment per student and topic,
grade 5-11, points 1-100, max attempts 1-5, role and difficulty from fixed lists.

## Workflows and business rules

1. Teacher manages content
   - only teachers create topics; only the author edits, deletes or publishes
   - a topic needs at least one problem to be published
   - a topic with problems can't be deleted
   - a problem's answer can't be changed (and it can't be deleted) after students answered
   - the teacher can reset attempts for one or all students
2. Student learns
   - can enroll only in published topics, only once
   - can answer only problems from topics they are enrolled in
   - limited attempts; hint after a wrong answer; correct answer shown when attempts run out
   - points: 100% on the 1st try, 75% on the 2nd, 50% on the 3rd, 25% later
   - a solved problem can't be solved again
3. Levels
   - easy problems are always open
   - medium opens when all easy problems of the topic are solved, hard - when all medium are solved
   - `GET /topics/{id}/my-problems?student_id=` shows each problem as locked, available, solved or failed
4. Homework with deadlines
   - the author gives a published topic's problems as homework with a future deadline
   - a problem can be in only one assignment; all problems must be from the same topic
   - the deadline can be moved, but only to the future
   - status for a student: not_started, in_progress, completed, overdue
   - answers after the deadline still count, but give half points
   - the author sees a report: status of every enrolled student
5. Progress and analytics
   - student progress per enrolled topic
   - topic leaderboard (score, then solved problems)
   - topic statistics for the author: success rate of each problem
