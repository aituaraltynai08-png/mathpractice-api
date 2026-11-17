from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import (AssignmentCreate, AssignmentOut, AssignmentReport, AssignmentUpdate,
                         StudentAssignment)

router = APIRouter(tags=["Assignments"])


@router.post("/topics/{topic_id}/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(topic_id: int, teacher_id: int, data: AssignmentCreate, db: Session = Depends(get_db)):
    return services.create_assignment(db, topic_id, teacher_id, data)


@router.get("/topics/{topic_id}/assignments", response_model=list[AssignmentOut])
def list_assignments(topic_id: int, db: Session = Depends(get_db)):
    return services.list_assignments(db, topic_id)


@router.get("/assignments/{assignment_id}", response_model=AssignmentOut)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    return services.get_assignment(db, assignment_id)


@router.patch("/assignments/{assignment_id}", response_model=AssignmentOut)
def update_assignment(assignment_id: int, teacher_id: int, data: AssignmentUpdate, db: Session = Depends(get_db)):
    return services.update_assignment(db, assignment_id, teacher_id, data)


@router.delete("/assignments/{assignment_id}", status_code=204)
def delete_assignment(assignment_id: int, teacher_id: int, db: Session = Depends(get_db)):
    services.delete_assignment(db, assignment_id, teacher_id)


@router.get("/assignments/{assignment_id}/report", response_model=AssignmentReport)
def assignment_report(assignment_id: int, teacher_id: int, db: Session = Depends(get_db)):
    return services.assignment_report(db, assignment_id, teacher_id)


@router.get("/users/{student_id}/assignments", response_model=list[StudentAssignment])
def student_assignments(student_id: int, db: Session = Depends(get_db)):
    return services.student_assignments(db, student_id)
