# Pydantic schemas: what the API accepts and what it returns.
from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class Role(str, Enum):
    teacher = "teacher"
    student = "student"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class FromDB(BaseModel):
    # lets Pydantic read data straight from SQLAlchemy objects
    model_config = ConfigDict(from_attributes=True)


# ----- users -----
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)
    role: Role


class UserUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[str] = Field(default=None, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=120)


class UserOut(FromDB):
    id: int
    name: str
    email: str
    role: Role


# ----- topics -----
class TopicCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    grade: int = Field(ge=5, le=11)
    teacher_id: int


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    grade: Optional[int] = Field(default=None, ge=5, le=11)


class TopicOut(FromDB):
    id: int
    title: str
    description: Optional[str]
    grade: int
    is_published: bool
    teacher_id: int
    problem_count: int


class EnrollRequest(BaseModel):
    student_id: int


class EnrollmentOut(FromDB):
    id: int
    student_id: int
    topic_id: int
    enrolled_at: datetime


# ----- problems -----
class ProblemCreate(BaseModel):
    question: str = Field(min_length=5, max_length=500)
    answer: str = Field(min_length=1, max_length=100)
    difficulty: Difficulty = Difficulty.easy
    points: int = Field(default=10, ge=1, le=100)
    max_attempts: int = Field(default=3, ge=1, le=5)
    hint: Optional[str] = Field(default=None, max_length=300)


class ProblemUpdate(BaseModel):
    question: Optional[str] = Field(default=None, min_length=5, max_length=500)
    answer: Optional[str] = Field(default=None, min_length=1, max_length=100)
    difficulty: Optional[Difficulty] = None
    points: Optional[int] = Field(default=None, ge=1, le=100)
    max_attempts: Optional[int] = Field(default=None, ge=1, le=5)
    hint: Optional[str] = Field(default=None, max_length=300)


class ProblemOut(FromDB):
    # no "answer" and no "hint": students must not see them
    id: int
    topic_id: int
    question: str
    difficulty: Difficulty
    points: int
    max_attempts: int


# ----- attempts -----
class AttemptCreate(BaseModel):
    student_id: int
    answer: str = Field(min_length=1, max_length=100)


class AttemptOut(FromDB):
    id: int
    problem_id: int
    student_id: int
    answer: str
    is_correct: bool
    attempt_number: int
    points: int
    created_at: datetime


class AttemptResult(AttemptOut):
    late: bool = False  # answered after the assignment deadline (half points)
    message: str
    attempts_left: int
    hint: Optional[str] = None
    correct_answer: Optional[str] = None  # shown only when all attempts are used


class ResetResult(BaseModel):
    problem_id: int
    deleted_attempts: int


# ----- progress and statistics -----
class TopicProgress(BaseModel):
    topic_id: int
    title: str
    solved: int
    total_problems: int
    score: int
    max_score: int


class StudentProgress(BaseModel):
    student_id: int
    name: str
    total_score: int
    topics: list[TopicProgress]


class LeaderboardEntry(BaseModel):
    rank: int
    student_id: int
    name: str
    score: int
    solved: int


class ProblemStats(BaseModel):
    problem_id: int
    question: str
    total_attempts: int
    students_tried: int
    students_solved: int
    success_rate: float


class TopicStats(BaseModel):
    topic_id: int
    title: str
    enrolled_students: int
    problems: list[ProblemStats]


# ----- assignments (homework with a deadline) -----
class AssignmentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    due_at: datetime = Field(description="Deadline, e.g. 2026-12-01T18:00:00+05:00")
    problem_ids: list[int] = Field(min_length=1, max_length=50)


class AssignmentUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    due_at: Optional[datetime] = None


class AssignmentOut(FromDB):
    id: int
    topic_id: int
    title: str
    due_at: datetime
    problem_ids: list[int]


class AssignmentStatus(str, Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    overdue = "overdue"


class StudentAssignment(BaseModel):
    assignment_id: int
    title: str
    topic_id: int
    due_at: datetime
    status: AssignmentStatus
    solved: int
    total: int


class ReportRow(BaseModel):
    student_id: int
    name: str
    status: AssignmentStatus
    solved: int
    total: int


class AssignmentReport(BaseModel):
    assignment_id: int
    title: str
    due_at: datetime
    students: list[ReportRow]


# ----- problems as one student sees them (with levels) -----
class ProblemStatus(str, Enum):
    locked = "locked"        # previous level is not finished yet
    available = "available"  # can be solved
    solved = "solved"
    failed = "failed"        # all attempts used without a correct answer


class StudentProblem(BaseModel):
    id: int
    question: str
    difficulty: Difficulty
    points: int
    status: ProblemStatus
    attempts_used: int
    max_attempts: int
    assignment_id: Optional[int]
