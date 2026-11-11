# In-memory storage. Data disappears when the server restarts.
users = {}
topics = {}
problems = {}
attempts = {}

counters = {"users": 0, "topics": 0, "problems": 0, "attempts": 0}


def next_id(table):
    counters[table] += 1
    return counters[table]


def add_demo_data():
    # users: 1 = teacher, 2 = teacher, 3 = student, 4 = student
    users[1] = {"id": 1, "name": "Demo Teacher", "role": "teacher"}
    users[2] = {"id": 2, "name": "Second Teacher", "role": "teacher"}
    users[3] = {"id": 3, "name": "Student One", "role": "student"}
    users[4] = {"id": 4, "name": "Student Two", "role": "student"}
    counters["users"] = 4

    topics[1] = {"id": 1, "title": "Fractions", "grade": 5, "teacher_id": 1}
    topics[2] = {"id": 2, "title": "Linear equations", "grade": 7, "teacher_id": 1}
    counters["topics"] = 2

    problems[1] = {"id": 1, "topic_id": 1, "question": "1/2 + 1/4 = ? (decimal)", "answer": "0.75",
                   "difficulty": "easy", "points": 10, "max_attempts": 3, "hint": "1/2 = 0.5, 1/4 = 0.25"}
    problems[2] = {"id": 2, "topic_id": 2, "question": "Solve: 3x + 5 = 20", "answer": "5",
                   "difficulty": "easy", "points": 10, "max_attempts": 3, "hint": "Subtract 5, then divide by 3"}
    problems[3] = {"id": 3, "topic_id": 2, "question": "In ax + b = 0, what is a called?", "answer": "coefficient",
                   "difficulty": "medium", "points": 15, "max_attempts": 2, "hint": None}
    counters["problems"] = 3
