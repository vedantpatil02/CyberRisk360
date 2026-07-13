from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services.auth.auth import create_access_token
from app.services.users.user_service import authenticate_user
from app.dependencies.database import get_db
from app.dependencies.security import get_current_user
from app.core.rate_limiter import limiter

router = APIRouter()



@router.post("/login")
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT token.

    Rate-limited to 5/minute per IP as a practical substitute for
    full account lockout - mitigates brute-force credential guessing.
    """

    user = authenticate_user(
        db,
        form_data.username,
        form_data.password
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

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