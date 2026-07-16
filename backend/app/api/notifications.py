"""
CyberRisk360

Purpose:
In-app notification list (currently: evidence expiry).
"""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope
from app.core.constants import READ_ROLES

from app.analytics.notifications import get_notifications


router = APIRouter()


@router.get("/notifications")
def list_notifications(
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES)),
):
    """
    Return the caller's org-scoped notifications, soonest-expiry
    first. No restriction beyond authentication (READ_ROLES = every
    org role) - same tier as Dashboard/Reports.
    """

    return get_notifications(db, org_id=scope)
