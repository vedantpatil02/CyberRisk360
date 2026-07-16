"""
CyberRisk360

Purpose:
Audit engagement management API - schedule/track a compliance audit
(optionally scoped to one framework) and record findings during it.

Distinct from app/api/audit.py (GET /audit-logs), the generic
security/activity trail.
"""

from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Query
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope, org_home
from app.core.constants import OVERSIGHT_ROLES, READ_ROLES

from app.schemas.audit_engagement import AuditCreate, AuditUpdate
from app.schemas.audit_finding import AuditFindingCreate, AuditFindingUpdate

from app.repositories.audits.audit_repository import (
    query_audits as db_query_audits,
    get_audit as db_get_audit,
    create_audit as db_create_audit,
    update_audit as db_update_audit,
)
from app.repositories.audits.audit_finding_repository import (
    list_findings_for_audit as db_list_findings_for_audit,
    create_finding as db_create_finding,
    update_finding as db_update_finding,
    get_finding as db_get_finding,
)
from app.services.audits.audit_workflow import (
    close_audit,
    update_finding_status,
)
from app.repositories.frameworks.framework_repository import get_framework
from app.repositories.controls.control_repository import get_control
from app.repositories.users.user_repository import get_by_id_in_org

from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_AUDIT_CREATE,
    ACTION_AUDIT_CLOSE,
    ACTION_AUDIT_FINDING_CREATE,
)


router = APIRouter()


def _validate_framework(db, framework_id):
    if framework_id is None:
        return
    if not get_framework(db, framework_id):
        raise HTTPException(status_code=404, detail="Framework not found")


def _validate_lead_auditor(db, lead_auditor_id, org_id):
    if lead_auditor_id is None:
        return
    if not get_by_id_in_org(db, lead_auditor_id, org_id=org_id):
        raise HTTPException(status_code=404, detail="Lead auditor not found")


def _validate_control(db, control_id):
    if control_id is None:
        return
    if not get_control(db, control_id):
        raise HTTPException(status_code=404, detail="Control not found")


@router.post("/audits")
def create_audit(
    audit: AuditCreate,
    request: Request,
    db: Session = Depends(get_db),
    org_id=Depends(org_home),
    current_user=Depends(require_role(*OVERSIGHT_ROLES)),
):
    """
    Schedule a new audit engagement.
    """

    _validate_framework(db, audit.framework_id)
    _validate_lead_auditor(db, audit.lead_auditor_id, org_id)

    created = db_create_audit(
        db,
        title=audit.title,
        framework_id=audit.framework_id,
        lead_auditor_id=audit.lead_auditor_id,
        scope=audit.scope,
        start_date=audit.start_date,
        end_date=audit.end_date,
        org_id=org_id,
    )

    record_audit(
        db,
        action=ACTION_AUDIT_CREATE,
        actor=current_user.get("sub"),
        entity_type="audit",
        entity_id=created.id,
        ip_address=client_ip(request),
        org_id=org_id,
    )

    db.refresh(created)

    return created


@router.get("/audits")
def get_audits(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None,
    framework_id: Optional[int] = None,
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES)),
):
    """
    List audit engagements (scoped to the caller's organization).
    Optional `status`/`framework_id` filters, `sort_by` + `order`, and
    `limit`/`offset` pagination.
    """

    return db_query_audits(
        db,
        org_id=scope,
        limit=limit,
        offset=offset,
        status=status,
        framework_id=framework_id,
        sort_by=sort_by,
        order=order,
    )


@router.get("/audits/{audit_id}")
def get_audit_by_id(
    audit_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES)),
):
    """
    Retrieve a single audit engagement.
    """

    audit = db_get_audit(db, audit_id, org_id=scope)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    return audit


@router.put("/audits/{audit_id}")
def update_audit_by_id(
    audit_id: int,
    audit_update: AuditUpdate,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*OVERSIGHT_ROLES)),
):
    """
    Update an existing audit engagement.
    """

    audit = db_get_audit(db, audit_id, org_id=scope)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    update_data = audit_update.model_dump(exclude_unset=True)

    if "framework_id" in update_data:
        _validate_framework(db, update_data["framework_id"])

    if "lead_auditor_id" in update_data:
        _validate_lead_auditor(db, update_data["lead_auditor_id"], scope)

    return db_update_audit(db, audit, update_data)


@router.patch("/audits/{audit_id}/close")
def close_audit_by_id(
    audit_id: int,
    request: Request,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*OVERSIGHT_ROLES)),
):
    """
    Close an audit engagement.
    """

    try:
        audit = close_audit(db, audit_id, org_id=scope)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    record_audit(
        db,
        action=ACTION_AUDIT_CLOSE,
        actor=current_user.get("sub"),
        entity_type="audit",
        entity_id=audit_id,
        ip_address=client_ip(request),
        org_id=audit.org_id,
    )

    db.refresh(audit)

    return audit


@router.post("/audits/{audit_id}/findings")
def create_audit_finding(
    audit_id: int,
    finding: AuditFindingCreate,
    request: Request,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*OVERSIGHT_ROLES)),
):
    """
    Record a finding for an audit engagement.
    """

    audit = db_get_audit(db, audit_id, org_id=scope)

    if not audit:
        raise HTTPException(status_code=404, detail="Audit not found")

    _validate_control(db, finding.control_id)

    created = db_create_finding(
        db,
        audit_id=audit_id,
        control_id=finding.control_id,
        title=finding.title,
        description=finding.description,
        severity=finding.severity,
    )

    record_audit(
        db,
        action=ACTION_AUDIT_FINDING_CREATE,
        actor=current_user.get("sub"),
        entity_type="audit_finding",
        entity_id=created.id,
        ip_address=client_ip(request),
        org_id=audit.org_id,
    )

    db.refresh(created)

    return created


@router.get("/audits/{audit_id}/findings")
def get_audit_findings(
    audit_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES)),
):
    """
    List findings recorded for an audit engagement.
    """

    if not db_get_audit(db, audit_id, org_id=scope):
        raise HTTPException(status_code=404, detail="Audit not found")

    return db_list_findings_for_audit(db, audit_id)


@router.put("/findings/{finding_id}")
def update_audit_finding(
    finding_id: int,
    finding_update: AuditFindingUpdate,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*OVERSIGHT_ROLES)),
):
    """
    Update an audit finding (e.g. mark Remediated).
    """

    finding = db_get_finding(db, finding_id)

    if not finding or (scope is not None and finding.audit.org_id != scope):
        raise HTTPException(status_code=404, detail="Finding not found")

    update_data = finding_update.model_dump(exclude_unset=True)

    if "control_id" in update_data:
        _validate_control(db, update_data["control_id"])

    # status changes go through the workflow service (kept consistent
    # even though this endpoint also allows other fields to change in
    # the same request) so a status-only PATCH-via-PUT still reads as
    # one coherent operation rather than two different code paths.
    if "status" in update_data and len(update_data) == 1:
        return update_finding_status(db, finding_id, update_data["status"], org_id=scope)

    return db_update_finding(db, finding, update_data)
