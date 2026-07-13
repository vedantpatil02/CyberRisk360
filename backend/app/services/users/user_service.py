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
    Create a new user account.

    Assumes the caller (API layer) has already validated that the
    email is unique and the role is valid - this just does the write.
    """

    created_user = create_user(
        db,
        username=user.username,
        email=user.email,
        password=hash_password(user.password),
        role=user.role
    )

    return created_user


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
