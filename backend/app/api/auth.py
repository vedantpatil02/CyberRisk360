from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.services.auth.auth import create_access_token
from app.services.users.user_service import (
    attempt_login,
    LOGIN_INVALID,
    LOGIN_LOCKED,
    LOGIN_INACTIVE,
)
from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_LOGIN_SUCCESS,
    ACTION_LOGIN_FAILURE,
    ACTION_LOGIN_LOCKED,
)
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

    Rate-limited to 5/minute per IP (network-level brute-force defense).
    In addition, per-account lockout kicks in after repeated failures
    (see `services/users/user_service.attempt_login`), and every attempt
    is written to the audit trail.
    """

    email = form_data.username

    user, error = attempt_login(
        db,
        email,
        form_data.password
    )

    if error is not None:

        # A locked account is the security-interesting case; everything
        # else (bad password, unknown email, disabled account) is a
        # generic failure in the trail and to the caller.
        action = (
            ACTION_LOGIN_LOCKED
            if error == LOGIN_LOCKED
            else ACTION_LOGIN_FAILURE
        )

        record_audit(
            db,
            action=action,
            actor=email,
            entity_type="user",
            entity_id=(user.id if user else None),
            ip_address=client_ip(request),
            detail=f"reason={error}",
        )

        if error == LOGIN_LOCKED:
            raise HTTPException(
                status_code=403,
                detail="Account locked due to repeated failed logins. "
                       "Try again later."
            )

        if error == LOGIN_INACTIVE:
            raise HTTPException(
                status_code=403,
                detail="Account is disabled"
            )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    record_audit(
        db,
        action=ACTION_LOGIN_SUCCESS,
        actor=user.email,
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
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