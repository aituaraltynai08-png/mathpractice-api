from typing import Optional

from fastapi import APIRouter

from app import services
from app.schemas import AttemptCreate, AttemptOut, AttemptResult, ProblemOut, ProblemUpdate

router = APIRouter(tags=["Problems and attempts"])


@router.get("/problems/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id: int):
    return services.get_problem(problem_id)


@router.patch("/problems/{problem_id}", response_model=ProblemOut)
def update_problem(problem_id: int, teacher_id: int, data: ProblemUpdate):
    return services.update_problem(problem_id, teacher_id, data)


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int, teacher_id: int):
    services.delete_problem(problem_id, teacher_id)


@router.post("/problems/{problem_id}/attempts", response_model=AttemptResult, status_code=201)
def submit_attempt(problem_id: int, data: AttemptCreate):
    return services.submit_attempt(problem_id, data)


@router.get("/attempts", response_model=list[AttemptOut])
def list_attempts(student_id: Optional[int] = None, problem_id: Optional[int] = None):
    return services.list_attempts(student_id, problem_id)
