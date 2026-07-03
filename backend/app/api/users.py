from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.models.user import User
from app.schemas.user import UserCreate
from app.services.security.security import hash_password
from app.dependencies.database import get_db

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
# Checks for valid role input
    if user.role not in [
        "admin",
        "analyst",
        "auditor"
    ]:
        return {
            "message": "Invalid role"
        }

# Create new database user object
    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(
            user.password
        ),
        role=user.role
    )

# Store user record in database
    db.add(new_user)
    db.commit()

    return {
        "message": "User created successfully"
    }