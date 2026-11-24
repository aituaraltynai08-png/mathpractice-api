from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import services
from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import LoginRequest, RegisterRequest, Token, UserOut

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: RegisterRequest, db: Session = Depends(get_db)):
    return services.register_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    return services.login(db, data)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
