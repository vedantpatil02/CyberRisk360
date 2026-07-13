from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate
from app.dependencies.database import get_db
from app.services.users.user_service import register_user as register_user_account

router = APIRouter()

"""
Register a new user account.
"""
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):

    return register_user_account(db, user)
