from fastapi import APIRouter
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services.auth.auth import create_access_token
from app.services.users.user_service import authenticate_user
from app.dependencies.database import get_db
from app.dependencies.security import get_current_user

router = APIRouter()



@router.post("/login")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.
    """

    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:

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





@router.get("/me")
def get_me(
    current_user=Depends(
        get_current_user
    )
):
    """
    Return currently authenticated user.
    """

    return current_user