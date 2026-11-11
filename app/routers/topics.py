from typing import Optional

from fastapi import APIRouter

from app import services
from app.schemas import Difficulty, ProblemCreate, ProblemOut, TopicCreate, TopicOut, TopicUpdate

router = APIRouter(prefix="/topics", tags=["Topics"])


@router.post("", response_model=TopicOut, status_code=201)
def create_topic(data: TopicCreate):
    return services.create_topic(data)


@router.get("", response_model=list[TopicOut])
def list_topics(grade: Optional[int] = None, search: Optional[str] = None):
    return services.list_topics(grade, search)


@router.get("/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: int):
    return services.get_topic(topic_id)


@router.patch("/{topic_id}", response_model=TopicOut)
def update_topic(topic_id: int, teacher_id: int, data: TopicUpdate):
    return services.update_topic(topic_id, teacher_id, data)


@router.delete("/{topic_id}", status_code=204)
def delete_topic(topic_id: int, teacher_id: int):
    services.delete_topic(topic_id, teacher_id)


@router.post("/{topic_id}/problems", response_model=ProblemOut, status_code=201)
def create_problem(topic_id: int, teacher_id: int, data: ProblemCreate):
    return services.create_problem(topic_id, teacher_id, data)


@router.get("/{topic_id}/problems", response_model=list[ProblemOut])
def list_problems(topic_id: int, difficulty: Optional[Difficulty] = None):
    return services.list_problems(topic_id, difficulty)
