# Demo data. Run once after migrations:  python -m app.seed
from datetime import datetime, timedelta, timezone

from app.database import SessionLocal
from app.models import Assignment, Attempt, Enrollment, Problem, Topic, User


def seed():
    db = SessionLocal()
    if db.query(User).first():
        print("Database already has data, seed skipped.")
        db.close()
        return

    teacher = User(name="Demo Teacher", email="teacher@mail.kz", role="teacher")
    teacher2 = User(name="Second Teacher", email="teacher2@mail.kz", role="teacher")
    s1 = User(name="Student One", email="student1@mail.kz", role="student")
    s2 = User(name="Student Two", email="student2@mail.kz", role="student")
    db.add_all([teacher, teacher2, s1, s2])
    db.flush()  # gives ids 1-4

    fractions = Topic(title="Fractions", grade=5, teacher_id=teacher.id, is_published=True,
                      description="Adding fractions")
    equations = Topic(title="Linear equations", grade=7, teacher_id=teacher.id, is_published=True,
                      description="Equations like ax + b = c")
    draft = Topic(title="Quadratic equations", grade=8, teacher_id=teacher.id,
                  description="Not published yet")
    db.add_all([fractions, equations, draft])
    db.flush()

    p1 = Problem(topic_id=fractions.id, question="1/2 + 1/4 = ? (decimal)", answer="0.75",
                 points=10, max_attempts=3, hint="1/2 = 0.5, 1/4 = 0.25")
    p2 = Problem(topic_id=equations.id, question="Solve: 3x + 5 = 20", answer="5",
                 points=10, max_attempts=3, hint="Subtract 5, then divide by 3")
    p3 = Problem(topic_id=equations.id, question="In ax + b = 0, what is a called?", answer="coefficient",
                 difficulty="medium", points=15, max_attempts=2)
    db.add_all([p1, p2, p3])
    db.flush()

    p4 = Problem(topic_id=fractions.id, question="3/4 - 1/2 = ? (decimal)", answer="0.25",
                 points=10, max_attempts=3, hint="0.75 - 0.5")
    p5 = Problem(topic_id=fractions.id, question="2/5 * 5/8 = ? (decimal)", answer="0.25",
                 difficulty="medium", points=15, max_attempts=3)
    db.add_all([p4, p5])
    db.flush()

    now = datetime.now(timezone.utc)
    db.add_all([
        # open homework: due in a week
        Assignment(topic_id=equations.id, title="Homework 1: equations", due_at=now + timedelta(days=7),
                   problems=[p2, p3]),
        # past homework: deadline already passed (late answers get half points)
        Assignment(topic_id=fractions.id, title="Homework 0: fractions", due_at=now - timedelta(days=1),
                   problems=[p4]),
    ])

    db.add_all([
        Enrollment(student_id=s1.id, topic_id=fractions.id),
        Enrollment(student_id=s1.id, topic_id=equations.id),
        Enrollment(student_id=s2.id, topic_id=fractions.id),
        Attempt(problem_id=p1.id, student_id=s1.id, answer="0.75", is_correct=True, attempt_number=1, points=10),
        Attempt(problem_id=p1.id, student_id=s2.id, answer="0.5", is_correct=False, attempt_number=1, points=0),
        Attempt(problem_id=p1.id, student_id=s2.id, answer="0.75", is_correct=True, attempt_number=2, points=8),
    ])
    db.commit()
    db.close()
    print("Demo data added.")


if __name__ == "__main__":
    seed()
