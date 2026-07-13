from app.core.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_AUDITOR
from app.repositories.users.user_repository import (
    get_by_email,
    create_user
)
from app.services.security.security import (
    hash_password,
    verify_password
)

VALID_ROLES = [ROLE_ADMIN, ROLE_ANALYST, ROLE_AUDITOR]


def register_user(db, user):
    """
    Validate and create a new user account.
    Returns a result dict describing the outcome.
    """

    if get_by_email(db, user.email):
        return {"message": "User already exists"}

    if user.role not in VALID_ROLES:
        return {"message": "Invalid role"}

    create_user(
        db,
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )

    return {"message": "User created successfully"}


def authenticate_user(db, email, password):
    """
    Return the User if email/password are valid, else None.
    """

    user = get_by_email(db, email)

    if not user:
        return None

    if not verify_password(password, user.password):
        return None

    return user
