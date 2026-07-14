from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from sqlalchemy.orm import Session

from app.schemas.user import UserCreate, PasswordChange, PasswordReset
from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.security import get_current_user
from app.dependencies.tenancy import is_super_admin
from app.core.constants import ROLE_ADMIN
from app.repositories.users.user_repository import get_by_email, get_by_id
from app.repositories.organizations.organization_repository import (
    get_organization_by_slug
)
from app.services.security.security import verify_password
from app.services.users.user_service import (
    register_user as register_user_account,
    change_password as change_user_password,
    set_active,
    VALID_ROLES
)

DEFAULT_ORG_SLUG = "default"


def _get_managed_user(db, user_id, current_user):
    """
    Fetch a target user for an admin action, enforcing tenant isolation:
    an org admin can only act on users in their own org; a super-admin
    can act on any. A cross-org target is reported as 404 (not 403) so
    the endpoint doesn't confirm the user exists in another org.
    """

    user = get_by_id(db, user_id)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if (
        not is_super_admin(current_user)
        and user.org_id != current_user.get("org_id")
    ):
        raise HTTPException(status_code=404, detail="User not found")

    return user
from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_USER_REGISTER,
    ACTION_USER_PASSWORD_CHANGE,
    ACTION_USER_PASSWORD_RESET,
    ACTION_USER_ACTIVATE,
    ACTION_USER_DEACTIVATE,
)

router = APIRouter()

"""
Register a new user account.
"""
@router.post("/register")
def register_user(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):

    if get_by_email(db, user.email):

        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    if user.role not in VALID_ROLES:

        raise HTTPException(
            status_code=400,
            detail="Invalid role"
        )

    organization = get_organization_by_slug(
        db, user.org_slug or DEFAULT_ORG_SLUG
    )

    if organization is None:

        raise HTTPException(
            status_code=404,
            detail="Organization not found"
        )

    created = register_user_account(db, user, organization.id)

    record_audit(
        db,
        action=ACTION_USER_REGISTER,
        actor=user.email,
        entity_type="user",
        entity_id=created.id,
        ip_address=client_ip(request),
        detail=f"role={created.role}",
        org_id=organization.id,
    )

    return {
        "message": "User created successfully"
    }


@router.post("/users/me/change-password")
def change_own_password(
    payload: PasswordChange,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """
    Let an authenticated user change their own password, after proving
    knowledge of the current one.
    """

    user = get_by_email(db, current_user["sub"])

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(payload.current_password, user.password):
        raise HTTPException(
            status_code=400,
            detail="Current password is incorrect"
        )

    change_user_password(db, user, payload.new_password)

    record_audit(
        db,
        action=ACTION_USER_PASSWORD_CHANGE,
        actor=user.email,
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
        org_id=user.org_id,
    )

    return {"message": "Password changed"}


@router.post("/users/{user_id}/reset-password")
def admin_reset_password(
    user_id: int,
    payload: PasswordReset,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(ROLE_ADMIN))
):
    """
    Admin-initiated password reset for another account. (Self-service
    token-based reset is deferred until notifications/email exist -
    see ROADMAP.md Phase 5.)
    """

    user = _get_managed_user(db, user_id, current_user)

    change_user_password(db, user, payload.new_password)

    record_audit(
        db,
        action=ACTION_USER_PASSWORD_RESET,
        actor=current_user["sub"],
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
        org_id=user.org_id,
    )

    return {"message": "Password reset"}


@router.post("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(ROLE_ADMIN))
):
    """
    Disable an account. Deactivated users are rejected at login but
    retain their history and audit trail.
    """

    user = _get_managed_user(db, user_id, current_user)

    set_active(db, user, False)

    record_audit(
        db,
        action=ACTION_USER_DEACTIVATE,
        actor=current_user["sub"],
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
        org_id=user.org_id,
    )

    return {"message": "User deactivated"}


@router.post("/users/{user_id}/activate")
def activate_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(ROLE_ADMIN))
):
    """
    Re-enable a disabled account and clear any lockout state.
    """

    user = _get_managed_user(db, user_id, current_user)

    set_active(db, user, True)

    record_audit(
        db,
        action=ACTION_USER_ACTIVATE,
        actor=current_user["sub"],
        entity_type="user",
        entity_id=user.id,
        ip_address=client_ip(request),
        org_id=user.org_id,
    )

    return {"message": "User activated"}
