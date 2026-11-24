# MathPractice API

Teachers create math topics and problems, publish topics and give homework with deadlines.
Students register, log in, enroll, unlock levels (easy -> medium -> hard), solve problems and do homework.
The API checks answers, gives hints, counts points, and shows progress, leaderboards and statistics.

Stack: FastAPI, Pydantic, PostgreSQL, SQLAlchemy, Alembic, JWT (PyJWT), bcrypt.

## Run

1. Create a PostgreSQL database named `mathpractice`.
2. Copy `.env.example` to `.env` and fill in `DATABASE_URL` and `JWT_SECRET_KEY`.
3. Install and start:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head      # creates all tables
python -m app.seed        # demo data (only once)
python -m uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs

## Demo users

All demo users have the password `password123`.

- teacher@mail.kz - teacher, author of all demo topics
- teacher2@mail.kz - teacher without topics (to test ownership)
- student1@mail.kz, student2@mail.kz - students

## Authentication

- `POST /auth/register` - create an account (name, email, password, role). The password is stored as a bcrypt hash.
- `POST /auth/login` - email and password -> JWT access token.
- `GET /auth/me` - who am I (needs a token).

In Swagger: log in, copy `access_token`, click **Authorize** at the top, paste the token and confirm.
After that every request is sent with the header `Authorization: Bearer <token>`.

The token contains the user id (`sub`) and an expiry time (`exp`), and is signed with `JWT_SECRET_KEY`.
`get_current_user` in `app/auth.py` reads the token on every protected request and returns the user.

Status codes: 401 - no token, invalid or expired token, wrong email or password;
403 - logged in but not allowed (wrong role or not your resource).

## Who can do what

- Anyone (no token): browse topics, problems, leaderboards and homework lists.
- Teacher: create topics; edit, publish and delete only their own topics, problems and homework;
  see stats, students and reports only for their own topics; reset attempts in their own topics.
- Student: enroll, see "my problems", submit answers, see their own progress, homework and attempts.
- Everyone logged in: edit or delete only their own account. Teachers can see any student's progress.

## Structure

- `app/main.py` - creates the app, connects routers
- `app/database.py` - database connection (from `DATABASE_URL`), session for each request
- `app/auth.py` - password hashing, JWT tokens, `get_current_user` dependency
- `app/models.py` - SQLAlchemy tables and relationships
- `app/schemas.py` - Pydantic request and response models
- `app/services.py` - business logic and access rules
- `app/routers/` - endpoints (auth, users, topics, problems, assignments)
- `app/seed.py` - demo data
- `alembic/versions/` - database migrations (0001 tables, 0002 assignments, 0003 password hash)

## Tables and relationships

- users: one teacher -> many topics (one-to-many)
- topics: one topic -> many problems (one-to-many)
- problems: one problem -> many attempts (one-to-many)
- assignments: one topic -> many assignments, one assignment -> many problems (one-to-many)
- enrollments: students <-> topics (many-to-many)

## Business rules

- a topic needs at least one problem to be published; a topic with problems can't be deleted
- a problem's answer can't be changed (and it can't be deleted) after students answered
- students enroll only in published topics, once, and answer only problems of their topics
- medium opens when all easy problems are solved, hard - when all medium are solved
- limited attempts; hint after a wrong answer; correct answer shown when attempts run out
- points: 100% on the 1st try, 75% on the 2nd, 50% on the 3rd, 25% later; half points after a homework deadline
- homework status: not_started, in_progress, completed, overdue
