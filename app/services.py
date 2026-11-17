# Business logic. Routers only call these functions; all rules live here.
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import delete, desc, func, select
from sqlalchemy.orm import Session

from app.models import Assignment, Attempt, Enrollment, Problem, Topic, User

# share of points for the 1st, 2nd, 3rd try; later tries get 25%
POINTS_BY_TRY = {1: 1.0, 2: 0.75, 3: 0.5}
LATE_PENALTY = 0.5  # answers after the assignment deadline get half points
LEVELS = ["easy", "medium", "hard"]


def now():
    return datetime.now(timezone.utc)


def as_utc(moment: datetime) -> datetime:
    # a date without a time zone is treated as UTC
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)


# ================= users =================
def get_user(db: Session, user_id: int):
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return user


def check_role(db: Session, user_id: int, role: str):
    user = get_user(db, user_id)
    if user.role != role:
        raise HTTPException(status_code=403, detail=f"Only a {role} can do this")
    return user


def ensure_email_free(db: Session, email: str, exclude_id=None):
    stmt = select(User).where(User.email == email)
    if exclude_id is not None:
        stmt = stmt.where(User.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=409, detail="Email is already registered")


def create_user(db: Session, data):
    email = data.email.lower()
    ensure_email_free(db, email)
    user = User(name=data.name, email=email, role=data.role.value)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session, role):
    stmt = select(User).order_by(User.id)
    if role is not None:
        stmt = stmt.where(User.role == role.value)
    return db.scalars(stmt).all()


def update_user(db: Session, user_id: int, data):
    user = get_user(db, user_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if "email" in changes:
        changes["email"] = changes["email"].lower()
        ensure_email_free(db, changes["email"], exclude_id=user.id)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = get_user(db, user_id)
    if user.topics:
        raise HTTPException(status_code=409, detail=f"Teacher still has {len(user.topics)} topic(s). Delete them first")
    db.delete(user)  # a student's attempts and enrollments are deleted with them (cascade)
    db.commit()


# ================= topics =================
def get_topic(db: Session, topic_id: int):
    topic = db.get(Topic, topic_id)
    if topic is None:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
    return topic


def get_own_topic(db: Session, topic_id: int, teacher_id: int):
    topic = get_topic(db, topic_id)
    check_role(db, teacher_id, "teacher")
    if topic.teacher_id != teacher_id:
        raise HTTPException(status_code=403, detail="Only the author of the topic can change it")
    return topic


def ensure_title_free(db: Session, teacher_id: int, title: str, exclude_id=None):
    stmt = select(Topic).where(Topic.teacher_id == teacher_id, func.lower(Topic.title) == title.lower())
    if exclude_id is not None:
        stmt = stmt.where(Topic.id != exclude_id)
    if db.scalar(stmt):
        raise HTTPException(status_code=409, detail="You already have a topic with this title")


def create_topic(db: Session, data):
    check_role(db, data.teacher_id, "teacher")
    ensure_title_free(db, data.teacher_id, data.title)
    topic = Topic(**data.model_dump())
    db.add(topic)
    db.commit()
    db.refresh(topic)
    return topic


def list_topics(db: Session, grade, search, published):
    stmt = select(Topic).order_by(Topic.id)
    if grade is not None:
        stmt = stmt.where(Topic.grade == grade)
    if search:
        stmt = stmt.where(Topic.title.ilike(f"%{search}%"))
    if published is not None:
        stmt = stmt.where(Topic.is_published == published)
    return db.scalars(stmt).all()


def update_topic(db: Session, topic_id: int, teacher_id: int, data):
    topic = get_own_topic(db, topic_id, teacher_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if "title" in changes:
        ensure_title_free(db, teacher_id, changes["title"], exclude_id=topic.id)
    for field, value in changes.items():
        setattr(topic, field, value)
    db.commit()
    db.refresh(topic)
    return topic


def delete_topic(db: Session, topic_id: int, teacher_id: int):
    topic = get_own_topic(db, topic_id, teacher_id)
    if topic.problems:
        raise HTTPException(status_code=409, detail="Topic has problems. Delete them first")
    db.delete(topic)
    db.commit()


def publish_topic(db: Session, topic_id: int, teacher_id: int):
    topic = get_own_topic(db, topic_id, teacher_id)
    if topic.is_published:
        raise HTTPException(status_code=409, detail="Topic is already published")
    if not topic.problems:
        raise HTTPException(status_code=400, detail="Add at least one problem before publishing")
    topic.is_published = True
    db.commit()
    db.refresh(topic)
    return topic


# ================= enrollments =================
def find_enrollment(db: Session, student_id: int, topic_id: int):
    return db.scalar(select(Enrollment).where(Enrollment.student_id == student_id,
                                              Enrollment.topic_id == topic_id))


def enroll(db: Session, topic_id: int, student_id: int):
    topic = get_topic(db, topic_id)
    check_role(db, student_id, "student")
    if not topic.is_published:
        raise HTTPException(status_code=400, detail="Topic is not published yet")
    if find_enrollment(db, student_id, topic_id):
        raise HTTPException(status_code=409, detail="Student is already enrolled in this topic")
    enrollment = Enrollment(student_id=student_id, topic_id=topic_id)
    db.add(enrollment)
    db.commit()
    db.refresh(enrollment)
    return enrollment


def list_topic_students(db: Session, topic_id: int, teacher_id: int):
    topic = get_own_topic(db, topic_id, teacher_id)
    return [e.student for e in topic.enrollments]


# ================= problems =================
def create_problem(db: Session, topic_id: int, teacher_id: int, data):
    topic = get_own_topic(db, topic_id, teacher_id)
    if any(p.question.lower() == data.question.lower() for p in topic.problems):
        raise HTTPException(status_code=409, detail="This topic already has the same problem")
    problem = Problem(topic_id=topic.id, **data.model_dump(mode="json"))
    db.add(problem)
    db.commit()
    db.refresh(problem)
    return problem


def list_problems(db: Session, topic_id: int, difficulty):
    get_topic(db, topic_id)
    stmt = select(Problem).where(Problem.topic_id == topic_id).order_by(Problem.id)
    if difficulty is not None:
        stmt = stmt.where(Problem.difficulty == difficulty.value)
    return db.scalars(stmt).all()


def get_problem(db: Session, problem_id: int):
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found")
    return problem


def get_own_problem(db: Session, problem_id: int, teacher_id: int):
    problem = get_problem(db, problem_id)
    get_own_topic(db, problem.topic_id, teacher_id)
    return problem


def update_problem(db: Session, problem_id: int, teacher_id: int, data):
    problem = get_own_problem(db, problem_id, teacher_id)
    changes = data.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if "answer" in changes and problem.attempts:
        raise HTTPException(status_code=409, detail="Students already answered, the answer can't be changed")
    for field, value in changes.items():
        setattr(problem, field, value)
    db.commit()
    db.refresh(problem)
    return problem


def delete_problem(db: Session, problem_id: int, teacher_id: int):
    problem = get_own_problem(db, problem_id, teacher_id)
    if problem.attempts:
        raise HTTPException(status_code=409, detail="Students already answered, the problem can't be deleted")
    db.delete(problem)
    db.commit()


# ================= solving =================
def answers_match(given: str, correct: str) -> bool:
    # numbers: "5" == "5.0"; text: ignore case and spaces
    try:
        return float(given) == float(correct)
    except ValueError:
        return given.strip().lower() == correct.strip().lower()


def submit_attempt(db: Session, problem_id: int, data):
    problem = get_problem(db, problem_id)
    check_role(db, data.student_id, "student")
    if not find_enrollment(db, data.student_id, problem.topic_id):
        raise HTTPException(status_code=403, detail="Enroll in the topic first")
    check_level_unlocked(db, data.student_id, problem)

    previous = db.scalars(select(Attempt).where(Attempt.problem_id == problem_id,
                                                Attempt.student_id == data.student_id)).all()
    if any(a.is_correct for a in previous):
        raise HTTPException(status_code=409, detail="You already solved this problem")
    if len(previous) >= problem.max_attempts:
        raise HTTPException(status_code=409, detail="No attempts left")

    number = len(previous) + 1
    is_correct = answers_match(data.answer, problem.answer)
    late = problem.assignment is not None and now() > as_utc(problem.assignment.due_at)
    share = POINTS_BY_TRY.get(number, 0.25) * (LATE_PENALTY if late else 1)
    points = round(problem.points * share) if is_correct else 0

    attempt = Attempt(problem_id=problem_id, student_id=data.student_id, answer=data.answer,
                      is_correct=is_correct, attempt_number=number, points=points)
    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    left = 0 if is_correct else problem.max_attempts - number
    if is_correct:
        message = f"Correct! +{points} points" + (" (late: half points)" if late else "")
    elif left > 0:
        message = f"Wrong answer. Attempts left: {left}"
    else:
        message = "Wrong answer. No attempts left"

    return {
        "id": attempt.id, "problem_id": problem_id, "student_id": data.student_id,
        "answer": attempt.answer, "is_correct": is_correct, "attempt_number": number,
        "points": points, "created_at": attempt.created_at,
        "late": late, "message": message, "attempts_left": left,
        "hint": problem.hint if not is_correct and left > 0 else None,
        "correct_answer": problem.answer if not is_correct and left == 0 else None,
    }


def list_attempts(db: Session, student_id, problem_id, is_correct):
    stmt = select(Attempt).order_by(Attempt.id.desc())
    if student_id is not None:
        stmt = stmt.where(Attempt.student_id == student_id)
    if problem_id is not None:
        stmt = stmt.where(Attempt.problem_id == problem_id)
    if is_correct is not None:
        stmt = stmt.where(Attempt.is_correct == is_correct)
    return db.scalars(stmt).all()


def reset_attempts(db: Session, problem_id: int, teacher_id: int, student_id):
    problem = get_own_problem(db, problem_id, teacher_id)
    stmt = delete(Attempt).where(Attempt.problem_id == problem.id)
    if student_id is not None:
        get_user(db, student_id)
        stmt = stmt.where(Attempt.student_id == student_id)
    deleted = db.execute(stmt).rowcount
    db.commit()
    return {"problem_id": problem.id, "deleted_attempts": deleted}


# ================= progress and statistics =================
def student_progress(db: Session, student_id: int):
    student = get_user(db, student_id)
    if student.role != "student":
        raise HTTPException(status_code=400, detail="This user is not a student")

    topics = []
    for enrollment in student.enrollments:
        topic = enrollment.topic
        problem_ids = {p.id for p in topic.problems}
        attempts = [a for a in student.attempts if a.problem_id in problem_ids]
        topics.append({
            "topic_id": topic.id,
            "title": topic.title,
            "solved": sum(1 for a in attempts if a.is_correct),
            "total_problems": len(problem_ids),
            "score": sum(a.points for a in attempts),
            "max_score": sum(p.points for p in topic.problems),
        })
    return {"student_id": student.id, "name": student.name,
            "total_score": sum(t["score"] for t in topics), "topics": topics}


def leaderboard(db: Session, topic_id: int, limit: int):
    get_topic(db, topic_id)
    score = func.sum(Attempt.points).label("score")
    solved = func.count(Attempt.id).filter(Attempt.is_correct).label("solved")
    stmt = (
        select(User.id, User.name, score, solved)
        .join(Attempt, Attempt.student_id == User.id)
        .join(Problem, Problem.id == Attempt.problem_id)
        .where(Problem.topic_id == topic_id)
        .group_by(User.id, User.name)
        .order_by(desc("score"), desc("solved"), User.name)
        .limit(limit)
    )
    rows = db.execute(stmt).all()
    return [{"rank": i, "student_id": r.id, "name": r.name, "score": r.score, "solved": r.solved}
            for i, r in enumerate(rows, start=1)]


def topic_stats(db: Session, topic_id: int, teacher_id: int):
    topic = get_own_topic(db, topic_id, teacher_id)
    problems = []
    for p in topic.problems:
        tried = {a.student_id for a in p.attempts}
        solved = {a.student_id for a in p.attempts if a.is_correct}
        problems.append({
            "problem_id": p.id,
            "question": p.question,
            "total_attempts": len(p.attempts),
            "students_tried": len(tried),
            "students_solved": len(solved),
            "success_rate": round(100 * len(solved) / len(tried), 1) if tried else 0.0,
        })
    return {"topic_id": topic.id, "title": topic.title,
            "enrolled_students": len(topic.enrollments), "problems": problems}


# ================= levels: easy -> medium -> hard =================
def solved_problem_ids(db: Session, student_id: int) -> set[int]:
    stmt = select(Attempt.problem_id).where(Attempt.student_id == student_id, Attempt.is_correct)
    return set(db.scalars(stmt).all())


def unlocked_levels(topic, solved_ids: set[int]) -> set[str]:
    """Easy is always open. The next level opens when every problem of the previous level is solved."""
    unlocked = {"easy"}
    for previous, next_level in zip(LEVELS, LEVELS[1:]):
        previous_problems = [p for p in topic.problems if p.difficulty == previous]
        if all(p.id in solved_ids for p in previous_problems):
            unlocked.add(next_level)
        else:
            break
    return unlocked


def check_level_unlocked(db: Session, student_id: int, problem):
    levels = unlocked_levels(problem.topic, solved_problem_ids(db, student_id))
    if problem.difficulty not in levels:
        previous = LEVELS[LEVELS.index(problem.difficulty) - 1]
        raise HTTPException(status_code=403,
                            detail=f"Level '{problem.difficulty}' is locked. Solve all {previous} problems first")


def student_problems(db: Session, topic_id: int, student_id: int):
    """Problems of a topic with the status for one student: locked, available, solved, failed."""
    topic = get_topic(db, topic_id)
    check_role(db, student_id, "student")
    if not find_enrollment(db, student_id, topic_id):
        raise HTTPException(status_code=403, detail="Enroll in the topic first")

    solved_ids = solved_problem_ids(db, student_id)
    levels = unlocked_levels(topic, solved_ids)
    result = []
    for p in sorted(topic.problems, key=lambda p: (LEVELS.index(p.difficulty), p.id)):
        used = sum(1 for a in p.attempts if a.student_id == student_id)
        if p.id in solved_ids:
            status = "solved"
        elif p.difficulty not in levels:
            status = "locked"
        elif used >= p.max_attempts:
            status = "failed"
        else:
            status = "available"
        result.append({"id": p.id, "question": p.question, "difficulty": p.difficulty, "points": p.points,
                       "status": status, "attempts_used": used, "max_attempts": p.max_attempts,
                       "assignment_id": p.assignment_id})
    return result


# ================= assignments (homework with a deadline) =================
def get_assignment(db: Session, assignment_id: int):
    assignment = db.get(Assignment, assignment_id)
    if assignment is None:
        raise HTTPException(status_code=404, detail=f"Assignment {assignment_id} not found")
    return assignment


def get_own_assignment(db: Session, assignment_id: int, teacher_id: int):
    assignment = get_assignment(db, assignment_id)
    get_own_topic(db, assignment.topic_id, teacher_id)
    return assignment


def check_deadline_in_future(due_at: datetime):
    if as_utc(due_at) <= now():
        raise HTTPException(status_code=400, detail="Deadline must be in the future")


def create_assignment(db: Session, topic_id: int, teacher_id: int, data):
    topic = get_own_topic(db, topic_id, teacher_id)
    if not topic.is_published:
        raise HTTPException(status_code=400, detail="Publish the topic before giving homework")
    check_deadline_in_future(data.due_at)
    if len(set(data.problem_ids)) != len(data.problem_ids):
        raise HTTPException(status_code=400, detail="Problem ids must not repeat")

    problems = []
    for problem_id in data.problem_ids:
        problem = get_problem(db, problem_id)
        if problem.topic_id != topic.id:
            raise HTTPException(status_code=400, detail=f"Problem {problem_id} is not from this topic")
        if problem.assignment_id is not None:
            raise HTTPException(status_code=409,
                                detail=f"Problem {problem_id} is already in assignment {problem.assignment_id}")
        problems.append(problem)

    assignment = Assignment(topic_id=topic.id, title=data.title, due_at=data.due_at, problems=problems)
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def list_assignments(db: Session, topic_id: int):
    get_topic(db, topic_id)
    stmt = select(Assignment).where(Assignment.topic_id == topic_id).order_by(Assignment.due_at)
    return db.scalars(stmt).all()


def update_assignment(db: Session, assignment_id: int, teacher_id: int, data):
    assignment = get_own_assignment(db, assignment_id, teacher_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if "due_at" in changes:
        check_deadline_in_future(changes["due_at"])
    for field, value in changes.items():
        setattr(assignment, field, value)
    db.commit()
    db.refresh(assignment)
    return assignment


def delete_assignment(db: Session, assignment_id: int, teacher_id: int):
    assignment = get_own_assignment(db, assignment_id, teacher_id)
    db.delete(assignment)  # its problems stay in the topic, just without an assignment
    db.commit()


def assignment_status(assignment, student_id: int, solved_ids: set[int]):
    total = len(assignment.problems)
    solved = sum(1 for p in assignment.problems if p.id in solved_ids)
    started = any(a.student_id == student_id for p in assignment.problems for a in p.attempts)
    if total and solved == total:
        status = "completed"
    elif now() > as_utc(assignment.due_at):
        status = "overdue"
    elif started:
        status = "in_progress"
    else:
        status = "not_started"
    return status, solved, total


def student_assignments(db: Session, student_id: int):
    student = get_user(db, student_id)
    if student.role != "student":
        raise HTTPException(status_code=400, detail="This user is not a student")
    solved_ids = solved_problem_ids(db, student_id)
    result = []
    for enrollment in student.enrollments:
        for assignment in enrollment.topic.assignments:
            status, solved, total = assignment_status(assignment, student_id, solved_ids)
            result.append({"assignment_id": assignment.id, "title": assignment.title,
                           "topic_id": assignment.topic_id, "due_at": assignment.due_at,
                           "status": status, "solved": solved, "total": total})
    return sorted(result, key=lambda a: a["due_at"])


def assignment_report(db: Session, assignment_id: int, teacher_id: int):
    assignment = get_own_assignment(db, assignment_id, teacher_id)
    rows = []
    for enrollment in assignment.topic.enrollments:
        student = enrollment.student
        status, solved, total = assignment_status(assignment, student.id, solved_problem_ids(db, student.id))
        rows.append({"student_id": student.id, "name": student.name,
                     "status": status, "solved": solved, "total": total})
    return {"assignment_id": assignment.id, "title": assignment.title,
            "due_at": assignment.due_at, "students": rows}
