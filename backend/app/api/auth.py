from fastapi import APIRouter
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.models.user import User


from app.services.security.security import verify_password
from app.services.auth.auth import create_access_token
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

    user = (
        db.query(User)
        .filter(
            User.email == form_data.username
        )
        .first()
    )

    if not user:

        return {
            "message": "Invalid credentials"
        }

    if not verify_password(
        form_data.password,
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