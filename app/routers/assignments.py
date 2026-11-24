from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (AssignmentCreate, AssignmentOut, AssignmentReport, AssignmentUpdate,
                         StudentAssignment)

router = APIRouter(tags=["Assignments"])


@router.get("/topics/{topic_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(topic_id: int, db: Session = Depends(get_db)):
    return services.list_assignments(db, topic_id)


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    return services.get_assignment(db, assignment_id)


@router.post("/topics/{topic_id}/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(topic_id: int, data: AssignmentCreate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return services.create_assignment(db, topic_id, current_user.id, data)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(assignment_id: int, data: AssignmentUpdate, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return services.update_assignment(db, assignment_id, current_user.id, data)


@router.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    services.delete_assignment(db, assignment_id, current_user.id)


@router.get("/assignments/{assignment_id}/report", response_model=AssignmentReport)
def assignment_report(assignment_id: int, db: Session = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return services.assignment_report(db, assignment_id, current_user.id)


@router.get("/users/{student_id}/assignments", response_model=list[StudentAssignment])
def student_assignments(student_id: int, db: Session = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return services.student_assignments(db, student_id, current_user)
