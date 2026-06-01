from fastapi import APIRouter
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.user import User

from app.schemas.auth import LoginRequest

from app.services.security import verify_password
from app.services.auth import create_access_token

router = APIRouter()


@router.post("/login")
def login(
    request: LoginRequest
):

    db: Session = SessionLocal()

    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    if not user:

        return {
            "message": "Invalid credentials"
        }

    if not verify_password(
        request.password,
        user.password
    ):

        return {
            "message": "Invalid credentials"
        }

    token = create_access_token(
        {
            "sub": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }