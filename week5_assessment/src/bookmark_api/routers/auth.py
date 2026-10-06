from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from bookmark_api.auth import create_access_token, password_hasher
from bookmark_api.database import get_db
from bookmark_api.models import User
from bookmark_api.schemas import TokenResponse, UserCreate, UserLogin, UserResponse
from bookmark_api.utils import write_audit_log

router = APIRouter(prefix="", tags=["auth"])


@router.post("/users", response_model=UserResponse)
def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db),
):
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hasher.hash(user_data.password),
    )
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        # email has a unique constraint
        session.rollback()
        raise HTTPException(status_code=409, detail="Email already registered")

    background_tasks.add_task(write_audit_log, f"User created: {user.id}")
    return user


@router.post("/login", response_model=TokenResponse)
def login_user(login_data: UserLogin, session: Session = Depends(get_db)):
    user = session.scalar(select(User).where(User.email == login_data.email))

    # same response for unknown email and wrong password
    if user is None or not password_hasher.verify(login_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"access_token": create_access_token(user.id), "token_type": "bearer"}
