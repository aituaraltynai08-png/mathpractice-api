from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.database import get_db
from app.schemas import Role, StudentProgress, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db)):
    return services.create_user(db, data)


@router.get("", response_model=list[UserOut])
def list_users(role: Optional[Role] = None, db: Session = Depends(get_db)):
    return services.list_users(db, role)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db)):
    return services.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db)):
    return services.update_user(db, user_id, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    services.delete_user(db, user_id)


@router.get("/{user_id}/progress", response_model=StudentProgress)
def get_progress(user_id: int, db: Session = Depends(get_db)):
    return services.student_progress(db, user_id)
