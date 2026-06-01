from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.security import hash_password
from app.dependencies import get_db

router = APIRouter()

"""
Register a new user account.
"""
@router.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):



    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

# Check whether a user already exists
    if existing_user:
        return {
            "message": "User already exists"
        }

# Create new database user object
    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )

# Store user record in database
    db.add(new_user)
    db.commit()

    return {
        "message": "User created successfully"
    }