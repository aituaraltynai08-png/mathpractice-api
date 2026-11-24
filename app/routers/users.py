from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import Role, StudentProgress, UserOut, UserUpdate

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=list[UserOut])
def list_users(role: Optional[Role] = None, db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    return services.list_users(db, role)


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(user_id: int, data: UserUpdate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    return services.update_user(db, user_id, current_user, data)


@router.delete("/{user_id}", status_code=204)
def delete_user(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    services.delete_user(db, user_id, current_user)


@router.get("/{user_id}/progress", response_model=StudentProgress)
def get_progress(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return services.student_progress(db, user_id, current_user)
