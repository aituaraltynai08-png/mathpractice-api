# Business logic. Routers only call these functions.
from fastapi import HTTPException

from app import database as db


# ----- users -----
def create_user(data):
    user_id = db.next_id("users")
    db.users[user_id] = {"id": user_id, "name": data.name, "role": data.role.value}
    return db.users[user_id]


def get_user(user_id):
    if user_id not in db.users:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")
    return db.users[user_id]


def check_teacher(teacher_id):
    user = get_user(teacher_id)
    if user["role"] != "teacher":
        raise HTTPException(status_code=403, detail="Only teachers can do this")
    return user


# ----- topics -----
def create_topic(data):
    check_teacher(data.teacher_id)
    for topic in db.topics.values():
        if topic["teacher_id"] == data.teacher_id and topic["title"].lower() == data.title.lower():
            raise HTTPException(status_code=409, detail="You already have a topic with this title")
    topic_id = db.next_id("topics")
    db.topics[topic_id] = {"id": topic_id, **data.model_dump()}
    return db.topics[topic_id]


def list_topics(grade, search):
    result = list(db.topics.values())
    if grade is not None:
        result = [t for t in result if t["grade"] == grade]
    if search:
        result = [t for t in result if search.lower() in t["title"].lower()]
    return result


def get_topic(topic_id):
    if topic_id not in db.topics:
        raise HTTPException(status_code=404, detail=f"Topic {topic_id} not found")
    return db.topics[topic_id]


def check_topic_owner(topic_id, teacher_id):
    topic = get_topic(topic_id)
    check_teacher(teacher_id)
    if topic["teacher_id"] != teacher_id:
        raise HTTPException(status_code=403, detail="Only the author of the topic can change it")
    return topic


def update_topic(topic_id, teacher_id, data):
    topic = check_topic_owner(topic_id, teacher_id)
    changes = data.model_dump(exclude_unset=True)
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    topic.update(changes)
    return topic


def delete_topic(topic_id, teacher_id):
    check_topic_owner(topic_id, teacher_id)
    if any(p["topic_id"] == topic_id for p in db.problems.values()):
        raise HTTPException(status_code=409, detail="Topic has problems. Delete them first")
    del db.topics[topic_id]


# ----- problems -----
def create_problem(topic_id, teacher_id, data):
    check_topic_owner(topic_id, teacher_id)
    problem_id = db.next_id("problems")
    db.problems[problem_id] = {"id": problem_id, "topic_id": topic_id, **data.model_dump(mode="json")}
    return db.problems[problem_id]


def list_problems(topic_id, difficulty):
    get_topic(topic_id)
    result = [p for p in db.problems.values() if p["topic_id"] == topic_id]
    if difficulty is not None:
        result = [p for p in result if p["difficulty"] == difficulty.value]
    return result


def get_problem(problem_id):
    if problem_id not in db.problems:
        raise HTTPException(status_code=404, detail=f"Problem {problem_id} not found")
    return db.problems[problem_id]


def problem_has_attempts(problem_id):
    return any(a["problem_id"] == problem_id for a in db.attempts.values())


def update_problem(problem_id, teacher_id, data):
    problem = get_problem(problem_id)
    check_topic_owner(problem["topic_id"], teacher_id)
    changes = data.model_dump(exclude_unset=True, mode="json")
    if not changes:
        raise HTTPException(status_code=400, detail="Nothing to update")
    if "answer" in changes and problem_has_attempts(problem_id):
        raise HTTPException(status_code=409, detail="Students already answered, the answer can't be changed")
    problem.update(changes)
    return problem


def delete_problem(problem_id, teacher_id):
    problem = get_problem(problem_id)
    check_topic_owner(problem["topic_id"], teacher_id)
    if problem_has_attempts(problem_id):
        raise HTTPException(status_code=409, detail="Students already answered, the problem can't be deleted")
    del db.problems[problem_id]


# ----- solving -----
def answers_match(given, correct):
    # numbers: "5" == "5.0"; text: ignore case and spaces
    try:
        return float(given) == float(correct)
    except ValueError:
        return given.strip().lower() == correct.strip().lower()


def submit_attempt(problem_id, data):
    problem = get_problem(problem_id)
    student = get_user(data.student_id)
    if student["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can answer problems")

    previous = [a for a in db.attempts.values()
                if a["problem_id"] == problem_id and a["student_id"] == data.student_id]
    if any(a["is_correct"] for a in previous):
        raise HTTPException(status_code=409, detail="You already solved this problem")
    if len(previous) >= problem["max_attempts"]:
        raise HTTPException(status_code=409, detail="No attempts left")

    is_correct = answers_match(data.answer, problem["answer"])
    points = problem["points"] if is_correct else 0

    attempt_id = db.next_id("attempts")
    attempt = {"id": attempt_id, "problem_id": problem_id, "student_id": data.student_id,
               "answer": data.answer, "is_correct": is_correct, "points": points}
    db.attempts[attempt_id] = attempt

    attempts_left = problem["max_attempts"] - len(previous) - 1
    if is_correct:
        message = f"Correct! +{points} points"
    else:
        message = f"Wrong answer. Attempts left: {attempts_left}"
    hint = problem["hint"] if not is_correct and attempts_left > 0 else None
    return {**attempt, "message": message, "attempts_left": 0 if is_correct else attempts_left, "hint": hint}


def list_attempts(student_id, problem_id):
    result = list(db.attempts.values())
    if student_id is not None:
        result = [a for a in result if a["student_id"] == student_id]
    if problem_id is not None:
        result = [a for a in result if a["problem_id"] == problem_id]
    return result


def student_progress(student_id):
    student = get_user(student_id)
    if student["role"] != "student":
        raise HTTPException(status_code=400, detail="This user is not a student")

    topics = []
    total_score = 0
    for topic in db.topics.values():
        problem_ids = [p["id"] for p in db.problems.values() if p["topic_id"] == topic["id"]]
        student_attempts = [a for a in db.attempts.values()
                            if a["student_id"] == student_id and a["problem_id"] in problem_ids]
        score = sum(a["points"] for a in student_attempts)
        solved = len([a for a in student_attempts if a["is_correct"]])
        total_score += score
        topics.append({"topic_id": topic["id"], "title": topic["title"], "solved": solved,
                       "total_problems": len(problem_ids), "score": score})
    return {"student_id": student_id, "name": student["name"], "total_score": total_score, "topics": topics}
