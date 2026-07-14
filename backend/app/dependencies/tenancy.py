"""
CyberRisk360

Purpose:
Resolve the organization scope for a request from the authenticated
user, so endpoints and repositories filter to the caller's tenant.

Two related values:
  * scope   - the org_id used to FILTER reads. `None` means "no filter"
              (a platform super-admin sees every organization).
  * home_id - the org_id new rows are WRITTEN under. Always a concrete
              org (a super-admin writes under their own org).
"""

from fastapi import Depends

from app.dependencies.security import get_current_user
from app.core.constants import ROLE_SUPER_ADMIN


def is_super_admin(current_user) -> bool:
    return current_user.get("role") == ROLE_SUPER_ADMIN


def org_scope(current_user=Depends(get_current_user)):
    """
    org_id to filter reads by. None for a super-admin (all orgs).
    """

    if is_super_admin(current_user):
        return None

    return current_user.get("org_id")


def org_home(current_user=Depends(get_current_user)):
    """
    Concrete org_id to write new rows under (the caller's own org).
    """

    return current_user.get("org_id")
