# Database tables (SQLAlchemy models).
from datetime import datetime
from typing import Optional

from sqlalchemy import (Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, Text,
                        UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("role IN ('teacher', 'student')", name="ck_users_role"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(120), unique=True)
    role: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # one teacher -> many topics
    topics: Mapped[list["Topic"]] = relationship(back_populates="teacher")
    # one student -> many attempts / enrollments (deleted together with the student)
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Topic(Base):
    __tablename__ = "topics"
    __table_args__ = (
        UniqueConstraint("teacher_id", "title", name="uq_topics_teacher_title"),
        CheckConstraint("grade BETWEEN 5 AND 11", name="ck_topics_grade"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(100))
    description: Mapped[Optional[str]] = mapped_column(Text)
    grade: Mapped[int] = mapped_column(Integer)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    teacher: Mapped["User"] = relationship(back_populates="topics")
    # one topic -> many problems
    problems: Mapped[list["Problem"]] = relationship(back_populates="topic", cascade="all, delete-orphan")
    enrollments: Mapped[list["Enrollment"]] = relationship(back_populates="topic", cascade="all, delete-orphan")
    # one topic -> many assignments
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="topic", cascade="all, delete-orphan")

    @property
    def problem_count(self) -> int:
        return len(self.problems)


class Problem(Base):
    __tablename__ = "problems"
    __table_args__ = (
        CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name="ck_problems_difficulty"),
        CheckConstraint("points BETWEEN 1 AND 100", name="ck_problems_points"),
        CheckConstraint("max_attempts BETWEEN 1 AND 5", name="ck_problems_max_attempts"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    question: Mapped[str] = mapped_column(Text)
    answer: Mapped[str] = mapped_column(String(100))
    difficulty: Mapped[str] = mapped_column(String(10), default="easy")
    points: Mapped[int] = mapped_column(Integer, default=10)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    hint: Mapped[Optional[str]] = mapped_column(Text)
    # a problem can be part of one assignment (or none)
    assignment_id: Mapped[Optional[int]] = mapped_column(ForeignKey("assignments.id", ondelete="SET NULL"))

    topic: Mapped["Topic"] = relationship(back_populates="problems")
    assignment: Mapped[Optional["Assignment"]] = relationship(back_populates="problems")
    # one problem -> many attempts
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="problem", cascade="all, delete-orphan")


class Assignment(Base):
    """Homework: a set of problems from one topic with a deadline."""
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(primary_key=True)
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(100))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    topic: Mapped["Topic"] = relationship(back_populates="assignments")
    # one assignment -> many problems (problems stay if the assignment is deleted)
    problems: Mapped[list["Problem"]] = relationship(back_populates="assignment")

    @property
    def problem_ids(self) -> list[int]:
        return [p.id for p in self.problems]


class Enrollment(Base):
    """Which student studies which topic (students <-> topics, many-to-many)."""
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "topic_id", name="uq_enrollments_student_topic"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    topic_id: Mapped[int] = mapped_column(ForeignKey("topics.id", ondelete="CASCADE"))
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    student: Mapped["User"] = relationship(back_populates="enrollments")
    topic: Mapped["Topic"] = relationship(back_populates="enrollments")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    answer: Mapped[str] = mapped_column(String(100))
    is_correct: Mapped[bool] = mapped_column(Boolean)
    attempt_number: Mapped[int] = mapped_column(Integer)
    points: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    problem: Mapped["Problem"] = relationship(back_populates="attempts")
    student: Mapped["User"] = relationship(back_populates="attempts")
