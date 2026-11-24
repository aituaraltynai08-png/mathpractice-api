from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import AttemptCreate, AttemptOut, AttemptResult, ProblemOut, ProblemUpdate, ResetResult

router = APIRouter(tags=["Problems and attempts"])


@router.get("/problems/{problem_id}", response_model=ProblemOut)
def get_problem(problem_id: int, db: Session = Depends(get_db)):
    return services.get_problem(db, problem_id)


@router.patch("/problems/{problem_id}", response_model=ProblemOut)
def update_problem(problem_id: int, data: ProblemUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return services.update_problem(db, problem_id, current_user.id, data)


@router.delete("/problems/{problem_id}", status_code=204)
def delete_problem(problem_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services.delete_problem(db, problem_id, current_user.id)


@router.post("/problems/{problem_id}/attempts", response_model=AttemptResult, status_code=201)
def submit_attempt(problem_id: int, data: AttemptCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return services.submit_attempt(db, problem_id, current_user.id, data)


@router.delete("/problems/{problem_id}/attempts", response_model=ResetResult)
def reset_attempts(problem_id: int, student_id: Optional[int] = None, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    return services.reset_attempts(db, problem_id, current_user.id, student_id)


@router.get("/attempts", response_model=list[AttemptOut])
def list_attempts(student_id: Optional[int] = None, problem_id: Optional[int] = None,
                  is_correct: Optional[bool] = None, db: Session = Depends(get_db),
                  current_user: User = Depends(get_current_user)):
    return services.list_attempts(db, current_user, student_id, problem_id, is_correct)
