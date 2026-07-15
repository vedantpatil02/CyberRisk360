from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import Query
from fastapi import UploadFile
from fastapi import File

from sqlalchemy.orm import Session

from app.schemas.risk import RiskCreate

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope, org_home
from app.core.constants import *

from app.services.risks.risk import calculate_risk_score, calculate_risk_level
from app.services.risks.risk_generation import generate_risks_for_assets
from app.services.remediation.evidence import save_evidence, serialize_evidence
from app.services.remediation.sla import compute_due_date
from app.schemas.risk_update import RiskUpdate
from app.analytics.risk_summary import initialize_summary

from app.repositories.risks.risk_repository import (
    get_all_risks as db_get_all_risks,
    query_risks as db_query_risks,
    get_risk as db_get_risk,
    create_risk as db_create_risk,
    update_risk as db_update_risk
)
from app.repositories.assets.asset_repository import (
    get_asset,
    get_all_assets
)
from app.repositories.users.user_repository import (
    get_by_id_in_org,
    get_by_email
)
from app.repositories.remediation.evidence_repository import (
    list_by_risk
)
from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_RISK_GENERATE,
    ACTION_RISK_ASSIGN
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


@router.post("/risks")
def create_risk(
    risk: RiskCreate,
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
    Create a new risk entry.

    Only Admins and Analysts
    can create risks.
    """

    if not get_asset(db, risk.asset_id, org_id=scope):

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    _validate_assignee(db, risk.assignee_id, scope)

    score = calculate_risk_score(
        risk.impact,
        risk.likelihood
    )

    level = calculate_risk_level(
        score
    )

    db_create_risk(
        db,
        title=risk.title,
        description=risk.description,
        asset_id=risk.asset_id,
        impact=risk.impact,
        likelihood=risk.likelihood,
        risk_score=score,
        risk_level=level,
        owner=risk.owner,
        assignee_id=risk.assignee_id,
        due_date=risk.due_date or compute_due_date(level),
        org_id=org_id
    )

    return {
        "message": "Risk created",
        "score": score,
        "level": level
    }


@router.post("/risks/generate")
def generate_risks(
    request: Request,
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
    Derive (or refresh) the per-asset aggregate risk from each asset's
    vulnerabilities and link those vulnerabilities to it.

    Idempotent: existing auto-generated risks are updated in place, so
    this is safe to re-run and is the way to backfill risks for data
    imported before auto-generation existed.
    """

    assets = get_all_assets(db, org_id=scope)

    generated = generate_risks_for_assets(db, assets)

    record_audit(
        db,
        action=ACTION_RISK_GENERATE,
        actor=current_user.get("sub"),
        entity_type="risk",
        ip_address=client_ip(request),
        detail=f"assets_with_risk={generated}",
        org_id=org_id,
    )

    return {
        "message": "Risk generation complete",
        "risks_generated": generated,
    }


@router.get("/risks")
def get_risks(
    limit: Optional[int] = Query(None, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    risk_level: Optional[str] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
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
    List risks (scoped to the caller's organization). Optional
    `risk_level`/`status`/`source`/`asset_id`/`assignee_id`/
    `sla_breached` filters, `sort_by` + `order`, and `limit`/`offset`
    pagination.
    """

    return db_query_risks(
        db,
        org_id=scope,
        limit=limit,
        offset=offset,
        risk_level=risk_level,
        status=status,
        source=source,
        asset_id=asset_id,
        assignee_id=assignee_id,
        sla_breached=sla_breached,
        sort_by=sort_by,
        order=order,
    )

@router.get("/risks/{risk_id}")
def get_risk(
    risk_id: int,
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
    Retrieve a specific risk.
    """

    risk = db_get_risk(db, risk_id, org_id=scope)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    return risk


@router.put("/risks/{risk_id}")
def update_risk(
    risk_id: int,
    risk_update: RiskUpdate,
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
    Update an existing risk.
    """

    risk = db_get_risk(db, risk_id, org_id=scope)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    update_data = risk_update.model_dump(
        exclude_unset=True
    )

    # Recalculate score if impact or likelihood changes. Deliberately
    # does NOT touch due_date - an SLA due date is a commitment set at
    # creation, not a floating derivation.
    if (
        risk_update.impact is not None
        or
        risk_update.likelihood is not None
    ):

        new_impact = update_data.get(
            "impact", risk.impact
        )

        new_likelihood = update_data.get(
            "likelihood", risk.likelihood
        )

        update_data["risk_score"] = calculate_risk_score(
            new_impact,
            new_likelihood
        )

        update_data["risk_level"] = calculate_risk_level(
            update_data["risk_score"]
        )

    if "assignee_id" in update_data:
        _validate_assignee(db, update_data["assignee_id"], scope)

    db_update_risk(db, risk, update_data)

    if "assignee_id" in update_data:
        record_audit(
            db,
            action=ACTION_RISK_ASSIGN,
            actor=current_user.get("sub"),
            entity_type="risk",
            entity_id=risk_id,
            ip_address=client_ip(request),
            detail=f"assignee_id={update_data['assignee_id']}",
            org_id=scope,
        )

    return {
        "message": "Risk updated"
    }

@router.patch(
    "/risks/{risk_id}/close"
)
def close_risk(
    risk_id: int,
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
    Close an existing risk.
    """

    risk = db_get_risk(db, risk_id, org_id=scope)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    db_update_risk(
        db,
        risk,
        {"status": RISK_STATUS_CLOSED}
    )

    return {
        "message": "Risk closed"
    }

@router.get("/risk-summary")
def get_risk_summary(
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
    Return dashboard statistics
    for all risks.
    """

    risks = db_get_all_risks(db, org_id=scope)

    summary = initialize_summary()

    for risk in risks:

        if risk.risk_level:

            level = (
                risk.risk_level.lower()
            )

            if level in summary:

                summary[level] += 1

        if (
            risk.status
            ==
            RISK_STATUS_OPEN
        ):

            summary[SUMMARY_OPEN] += 1

        elif (
            risk.status
            ==
            RISK_STATUS_CLOSED
        ):

            summary[SUMMARY_CLOSED] += 1

    return summary


@router.post(
    "/risks/{risk_id}/evidence"
)
def upload_risk_evidence(
    risk_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*WRITE_ROLES))
):
    """
    Upload a remediation-evidence file for a risk.
    """

    if not db_get_risk(db, risk_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Risk not found"
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
            risk_id=risk_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return serialize_evidence(attachment)


@router.get(
    "/risks/{risk_id}/evidence"
)
def get_risk_evidence(
    risk_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES))
):
    """
    List evidence attachments for a risk.
    """

    if not db_get_risk(db, risk_id, org_id=scope):
        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    return [
        serialize_evidence(a)
        for a in list_by_risk(db, risk_id, org_id=scope)
    ]
