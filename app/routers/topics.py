from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app import services
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (Difficulty, EnrollmentOut, LeaderboardEntry, ProblemCreate, ProblemOut,
                         StudentProblem, TopicCreate, TopicOut, TopicStats, TopicUpdate, UserOut)

router = APIRouter(prefix="/topics", tags=["Topics"])


# ----- public: anyone can browse topics -----
@router.get("", response_model=list[TopicOut])
def list_topics(grade: Optional[int] = Query(None, ge=5, le=11), search: Optional[str] = None,
                published: Optional[bool] = None, db: Session = Depends(get_db)):
    return services.list_topics(db, grade, search, published)


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: int, db: Session = Depends(get_db)):
    return services.get_topic(db, topic_id)


@router.get("/{topic_id}/problems", response_model=list[ProblemOut])
def list_problems(topic_id: int, difficulty: Optional[Difficulty] = None, db: Session = Depends(get_db)):
    return services.list_problems(db, topic_id, difficulty)


@router.get("/{topic_id}/leaderboard", response_model=list[LeaderboardEntry])
def leaderboard(topic_id: int, limit: int = Query(10, ge=1, le=50), db: Session = Depends(get_db)):
    return services.leaderboard(db, topic_id, limit)


# ----- teacher (author of the topic) -----
@router.post("", response_model=TopicOut, status_code=201)
def create_topic(data: TopicCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.create_topic(db, current_user.id, data)


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, data: TopicUpdate, db: Session = Depends(get_db),
                 current_user: User = Depends(get_current_user)):
    return services.update_topic(db, topic_id, current_user.id, data)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services.delete_topic(db, topic_id, current_user.id)


@router.post("/{topic_id}/publish", response_model=TopicOut)
def publish_topic(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.publish_topic(db, topic_id, current_user.id)


@router.post("/{topic_id}/problems", response_model=ProblemOut, status_code=201)
def create_problem(topic_id: int, data: ProblemCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return services.create_problem(db, topic_id, current_user.id, data)


@router.get("/{topic_id}/students", response_model=list[UserOut])
def list_topic_students(topic_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return services.list_topic_students(db, topic_id, current_user.id)


@router.get("/{topic_id}/stats", response_model=TopicStats)
def topic_stats(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.topic_stats(db, topic_id, current_user.id)


# ----- student -----
@router.post("/{topic_id}/enrollments", response_model=EnrollmentOut, status_code=201)
def enroll(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.enroll(db, topic_id, current_user.id)


@router.get("/{topic_id}/my-problems", response_model=list[StudentProblem])
def my_problems(topic_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.student_problems(db, topic_id, current_user.id)
