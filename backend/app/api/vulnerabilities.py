"""
CyberRisk360

Purpose:
Manage vulnerability records and
associate them with assets and risks.
"""

from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Query
from fastapi import Request
from fastapi import UploadFile
from fastapi import File

from sqlalchemy.orm import Session

from app.schemas.vulnerability import (
    VulnerabilityCreate
)

from app.dependencies.database import (
    get_db
)

from app.dependencies.rbac import (
    require_role
)

from app.dependencies.tenancy import org_scope, org_home

from app.services.security.cvss import (
    calculate_severity
)

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    WRITE_ROLES,
    READ_ROLES,
    VULNERABILITY_STATUS_OPEN,
    VULNERABILITY_STATUS_CLOSED
)

from app.schemas.vulnerability_update import (
    VulnerabilityUpdate
)

from app.services.security.validators import (
    validate_cvss_score
)

from app.services.vulnerabilities.vulnerability_summary import (
    get_vulnerability_summary as generate_summary
)

from app.services.controls.control_suggester import (
    suggest_control_names
)

from app.services.vulnerabilities.vulnerability_summary import (
    get_top_critical_vulnerabilities
)

from app.services.remediation.sla import compute_due_date
from app.services.remediation.evidence import save_evidence, serialize_evidence

from app.repositories.vulnerabilities.vulnerability_repository import (
    get_all_vulnerabilities,
    query_vulnerabilities,
    get_vulnerability as db_get_vulnerability,
    create_vulnerability as db_create_vulnerability,
    update_vulnerability as db_update_vulnerability
)
from app.repositories.controls.control_repository import (
    search_controls_by_title,
    get_controls_by_vulnerability
)
from app.repositories.assets.asset_repository import (
    get_asset
)
from app.repositories.risks.risk_repository import (
    get_risk
)
from app.repositories.users.user_repository import (
    get_by_id_in_org,
    get_by_email
)
from app.repositories.remediation.evidence_repository import (
    list_by_vulnerability
)
from app.services.mapping.mapping_engine import (
    map_vulnerability_to_controls
)
from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_VULNERABILITY_ASSIGN
)


router = APIRouter()


def _validate_assignee(db, assignee_id, scope):
    """
    404 (not 403) on a nonexistent or cross-org assignee_id, so a
    cross-org user id isn't confirmed to exist - same convention as
    app/api/users.py::_get_managed_user.
    """

    if assignee_id is None:
        return

    if not get_by_id_in_org(db, assignee_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Assignee not found"
        )


@router.post("/vulnerabilities")
def create_vulnerability(
    vulnerability: VulnerabilityCreate,
    db: Session = Depends(get_db),
    org_id=Depends(org_home),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Create a vulnerability record.
    """

    if not validate_cvss_score(
        vulnerability.cvss_score
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid CVSS score"
        )

    if not get_asset(db, vulnerability.asset_id, org_id=scope):

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    if not get_risk(db, vulnerability.risk_id, org_id=scope):

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    _validate_assignee(db, vulnerability.assignee_id, scope)

    severity = calculate_severity(
        vulnerability.cvss_score
    )

    created_vulnerability = db_create_vulnerability(
        db,
        title=vulnerability.title,
        description=vulnerability.description,
        asset_id=vulnerability.asset_id,
        risk_id=vulnerability.risk_id,
        cvss_score=vulnerability.cvss_score,
        severity=severity,
        owner=vulnerability.owner,
        status=VULNERABILITY_STATUS_OPEN,
        assignee_id=vulnerability.assignee_id,
        due_date=vulnerability.due_date or compute_due_date(severity),
        org_id=org_id
    )

    # Automatically map to controls (pending review - see
    # services/mapping/mapping_service.py), same as PDF-imported
    # vulnerabilities. Manually-created ones have no cve_id/plugin_id
    # (not part of this schema), so only keyword matches apply here.
    map_vulnerability_to_controls(
        db,
        created_vulnerability
    )

    db.commit()

    return {
        "message": "Vulnerability created",
        "severity": severity
    }


@router.get("/vulnerabilities")
def get_vulnerabilities(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    severity: Optional[str] = None,
    status: Optional[str] = None,
    asset_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    sla_breached: Optional[bool] = None,
    sort_by: str = Query("id"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    List vulnerabilities (scoped to the caller's organization).

    Optional `severity`/`status`/`asset_id`/`assignee_id`/
    `sla_breached` filters, `sort_by`
    (id/title/severity/cvss_score/status/due_date/assignee_id) +
    `order` (asc/desc), and `limit`/`offset` pagination.
    """

    return query_vulnerabilities(
        db,
        org_id=scope,
        limit=limit,
        offset=offset,
        severity=severity,
        status=status,
        asset_id=asset_id,
        assignee_id=assignee_id,
        sla_breached=sla_breached,
        sort_by=sort_by,
        order=order,
    )

@router.get(
    "/vulnerabilities/top-critical"
)
def top_critical_vulnerabilities(
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):

    return (
        get_top_critical_vulnerabilities(
            db,
            org_id=scope
        )
    )

@router.get(
    "/vulnerabilities/{vulnerability_id}"
)
def get_vulnerability(
    vulnerability_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Retrieve a specific vulnerability.
    """

    vulnerability = db_get_vulnerability(db, vulnerability_id, org_id=scope)

    if not vulnerability:

        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    return vulnerability

@router.put(
    "/vulnerabilities/{vulnerability_id}"
)
def update_vulnerability(
    vulnerability_id: int,
    vulnerability_update: VulnerabilityUpdate,
    request: Request,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Update vulnerability.
    """

    vulnerability = db_get_vulnerability(db, vulnerability_id, org_id=scope)

    if not vulnerability:

        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    # Validate CVSS score
    if (
        vulnerability_update.cvss_score
        is not None
    ):

        if not validate_cvss_score(
            vulnerability_update.cvss_score
        ):

            raise HTTPException(
                status_code=400,
                detail="Invalid CVSS score"
            )

    update_data = (
        vulnerability_update
        .model_dump(
            exclude_unset=True
        )
    )

    # Recalculate severity. Deliberately does NOT touch due_date - an
    # SLA due date is a commitment set at creation, not a floating
    # derivation that shifts every time severity is rescored.
    if (
        vulnerability_update.cvss_score
        is not None
    ):

        update_data["severity"] = (
            calculate_severity(
                vulnerability_update.cvss_score
            )
        )

    if "assignee_id" in update_data:
        _validate_assignee(db, update_data["assignee_id"], scope)

    db_update_vulnerability(db, vulnerability, update_data)

    if "assignee_id" in update_data:
        record_audit(
            db,
            action=ACTION_VULNERABILITY_ASSIGN,
            actor=current_user.get("sub"),
            entity_type="vulnerability",
            entity_id=vulnerability_id,
            ip_address=client_ip(request),
            detail=f"assignee_id={update_data['assignee_id']}",
            org_id=scope,
        )

    return {
        "message":
        "Vulnerability updated"
    }

@router.patch(
    "/vulnerabilities/{vulnerability_id}/close"
)
def close_vulnerability(
    vulnerability_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Close vulnerability.
    """

    vulnerability = db_get_vulnerability(db, vulnerability_id, org_id=scope)

    if not vulnerability:

        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    db_update_vulnerability(
        db,
        vulnerability,
        {"status": VULNERABILITY_STATUS_CLOSED}
    )

    return {
        "message":
        "Vulnerability closed"
    }

@router.get("/vulnerability-summary")
def vulnerability_summary(
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    return generate_summary(db, org_id=scope)



@router.get(
    "/vulnerabilities/{vulnerability_id}/suggested-controls"
)
def get_suggested_controls(
    vulnerability_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Suggest controls for a vulnerability.

    Workflow:
    Vulnerability
        ↓
    Keyword Match
        ↓
    Control Search
        ↓
    Recommended Controls
    """

    vulnerability = db_get_vulnerability(db, vulnerability_id, org_id=scope)

    if not vulnerability:

        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    # Get suggested control names
    control_names = (
        suggest_control_names(
            vulnerability.title
        )
    )

    recommended_controls = []

    # Search controls table
    for control_name in control_names:

        controls = search_controls_by_title(db, control_name)

        for control in controls:

            recommended_controls.append(
                {
                    "control_id":
                        control.control_id,

                    "name":
                        control.title,

                    "framework":
                        control.category.framework.short_name,

                    "status":
                        control.status
                }
            )

    return {
        "vulnerability":
            vulnerability.title,

        "recommended_controls":
            recommended_controls
    }


@router.get(
    "/vulnerabilities/{vulnerability_id}/controls"
)
def get_vulnerability_controls(
    vulnerability_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):

    # Ensure the vulnerability belongs to the caller's org (404 for
    # cross-org ids) before listing its mapped controls.
    if not db_get_vulnerability(db, vulnerability_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    controls = get_controls_by_vulnerability(db, vulnerability_id)

    results = []

    for control in controls:

        results.append(
            {
                "control_id":
                    control.control_id,

                "name":
                    control.title,

                "framework":
                    control.category.framework.short_name,

                "status":
                    control.status
            }
        )

    return results


@router.post(
    "/vulnerabilities/{vulnerability_id}/evidence"
)
def upload_vulnerability_evidence(
    vulnerability_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*WRITE_ROLES))
):
    """
    Upload a remediation-evidence file for a vulnerability.
    """

    if not db_get_vulnerability(db, vulnerability_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    uploader = get_by_email(db, current_user["sub"])

    if uploader is None:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        attachment = save_evidence(
            db,
            file=file,
            uploaded_by_id=uploader.id,
            org_id=scope,
            vulnerability_id=vulnerability_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return serialize_evidence(attachment)


@router.get(
    "/vulnerabilities/{vulnerability_id}/evidence"
)
def get_vulnerability_evidence(
    vulnerability_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES))
):
    """
    List evidence attachments for a vulnerability.
    """

    if not db_get_vulnerability(db, vulnerability_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Vulnerability not found"
        )

    return [
        serialize_evidence(a)
        for a in list_by_vulnerability(db, vulnerability_id, org_id=scope)
    ]
