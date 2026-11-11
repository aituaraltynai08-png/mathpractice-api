from fastapi import APIRouter

from app import database as db
from app import services
from app.schemas import StudentProgress, UserCreate, UserOut

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserOut, status_code=201)
def create_user(data: UserCreate):
    return services.create_user(data)


@router.get("", response_model=list[UserOut])
def list_users():
    return list(db.users.values())


@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: int):
    return services.get_user(user_id)


@router.get("/{user_id}/progress", response_model=StudentProgress)
def get_progress(user_id: int):
    return services.student_progress(user_id)
