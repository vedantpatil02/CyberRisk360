from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate
from app.dependencies.database import get_db
from app.repositories.users.user_repository import get_by_email
from app.services.users.user_service import (
    register_user as register_user_account,
    VALID_ROLES
)

router = APIRouter()

"""
Register a new user account.
"""
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    if get_by_email(db, user.email):

        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    if user.role not in VALID_ROLES:

        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    register_user_account(db, user)

    return {
        "message": "User created successfully"
    }
