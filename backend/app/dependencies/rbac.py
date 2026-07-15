from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

from app.dependencies.security import (
    get_current_user
)
from app.dependencies.tenancy import is_super_admin


def require_role(*roles):
    """
    Restrict an endpoint to the given roles - except a platform
    super-admin, which bypasses every role check here regardless of
    `roles`. Mirrors how tenancy.py's org_scope/org_home and
    users.py's _get_managed_user already special-case super_admin
    (unscoped reads, cross-org user management): a super-admin is
    meant to span every organization and every capability, not just
    the /organizations management API.
    """

    def role_checker(
        current_user=Depends(
            get_current_user
        )
    ):

        if (
            not is_super_admin(current_user)
            and current_user["role"] not in roles
        ):

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )

        return current_user

    return role_checker