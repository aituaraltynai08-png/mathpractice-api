from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Role(str, Enum):
    teacher = "teacher"
    student = "student"


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


# ----- users -----
class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    role: Role


class UserOut(BaseModel):
    id: int
    name: str
    role: Role


# ----- topics -----
class TopicCreate(BaseModel):
    title: str = Field(min_length=3, max_length=100)
    grade: int = Field(ge=5, le=11)
    teacher_id: int


class TopicUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=3, max_length=100)
    grade: Optional[int] = Field(default=None, ge=5, le=11)


class TopicOut(BaseModel):
    id: int
    title: str
    grade: int
    teacher_id: int


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
    hint: Optional[str] = Field(default=None, max_length=300)


class ProblemOut(BaseModel):
    # no "answer" and no "hint" here, so students can't see them
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


class AttemptOut(BaseModel):
    id: int
    problem_id: int
    student_id: int
    answer: str
    is_correct: bool
    points: int


class AttemptResult(AttemptOut):
    message: str
    attempts_left: int
    hint: Optional[str] = None


class TopicProgress(BaseModel):
    topic_id: int
    title: str
    solved: int
    total_problems: int
    score: int


class StudentProgress(BaseModel):
    student_id: int
    name: str
    total_score: int
    topics: list[TopicProgress]
