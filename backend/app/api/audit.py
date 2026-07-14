"""
CyberRisk360

Purpose:
Read-only access to the audit trail. Restricted to admins and auditors -
the roles responsible for oversight and audit evidence.
"""

from typing import List, Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope
from app.core.constants import OVERSIGHT_ROLES

from app.schemas.audit import AuditLogOut
from app.repositories.audit.audit_repository import get_audit_logs


router = APIRouter()


@router.get("/audit-logs", response_model=List[AuditLogOut])
def list_audit_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = None,
    actor: Optional[str] = None,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(*OVERSIGHT_ROLES)
    )
):
    """
    Return audit-trail entries for the caller's organization, most
    recent first, with optional `action`/`actor` filters and
    `limit`/`offset` pagination.
    """

    return get_audit_logs(
        db,
        org_id=scope,
        limit=limit,
        offset=offset,
        action=action,
        actor=actor,
    )
