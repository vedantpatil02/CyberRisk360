"""
CyberRisk360

Purpose:
Manage compliance controls.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.schemas.control import ControlCreate

from app.dependencies.database import get_db

from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope, org_home

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    CONTROL_STATUS_MISSING,
    MAPPING_STATUS_APPROVED,
    COMPLIANCE_ROLES,
    READ_ROLES,
)

from app.analytics.compliance import calculate_compliance_summary

from app.schemas.control_update import ControlUpdate
from app.schemas.control_review import ControlReviewCreate

from app.repositories.controls.control_repository import (
    get_all_controls,
    get_control as db_get_control,
    create_control as db_create_control,
    update_control_status as db_update_control_status,
    get_controls_by_framework
)
from app.repositories.controls.control_review_repository import (
    list_reviews_for_control
)
from app.services.controls.control_review import submit_review
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_by_control
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    count_by_control
)
from app.repositories.categories.category_repository import (
    get_category
)

router = APIRouter()

@router.post("/controls")
def create_control(
    control: ControlCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Create a compliance control.
    """

    if not get_category(db, control.category_id):

        raise HTTPException(
            status_code=404,
            detail="Category not found"
        )

    db_create_control(
        db,
        control_id=control.control_id,
        title=control.title,
        description=control.description,
        category_id=control.category_id,
        status=CONTROL_STATUS_MISSING
    )

    return {
        "message":
        "Control created"
    }

@router.get("/controls")
def get_controls(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Retrieve all controls.
    """

    return get_all_controls(db)

@router.get(
    "/controls/{control_id}"
)
def get_control(
    control_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Retrieve a specific control.
    """

    control = db_get_control(db, control_id)

    if not control:

        raise HTTPException(
            status_code=404,
            detail="Control not found"
        )

    return control

@router.get(
    "/compliance-summary"
)
def get_compliance_summary(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Return compliance dashboard
    statistics.
    """

    controls = get_all_controls(db)

    return (
        calculate_compliance_summary(
            controls
        )
    )

@router.patch(
    "/controls/{control_id}/status"
)
def update_control_status(
    control_id: int,
    control_update: ControlUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Update control status.
    """

    control = db_get_control(db, control_id)

    if not control:

        raise HTTPException(
            status_code=404,
            detail="Control not found"
        )

    db_update_control_status(
        db,
        control,
        control_update.status
    )

    return {
        "message":
        "Control updated"
    }

@router.post(
    "/controls/{control_id}/review"
)
def review_control(
    control_id: int,
    review: ControlReviewCreate,
    db: Session = Depends(get_db),
    org_id=Depends(org_home),
    current_user=Depends(require_role(*COMPLIANCE_ROLES))
):
    """
    Submit a review of a control's implementation status, recording
    who reviewed it, what changed, and why - unlike
    PATCH /controls/{control_id}/status, which changes the status with
    no trail at all.
    """

    created = submit_review(
        db,
        control_id,
        new_status=review.new_status,
        notes=review.notes,
        reviewer=current_user.get("sub"),
        org_id=org_id,
    )

    if not created:
        raise HTTPException(status_code=404, detail="Control not found")

    return created


@router.get(
    "/controls/{control_id}/reviews"
)
def get_control_reviews(
    control_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(*READ_ROLES))
):
    """
    Return the review history for a control.
    """

    if not db_get_control(db, control_id):
        raise HTTPException(status_code=404, detail="Control not found")

    return list_reviews_for_control(db, control_id)


@router.get(
    "/controls/{control_id}/vulnerabilities"
)
def get_control_vulnerabilities(
    control_id: int,
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
    Return vulnerabilities mapped
    to a compliance control.
    """

    control = db_get_control(db, control_id)

    if not control:

        raise HTTPException(
            status_code=404,
            detail="Control not found"
        )

    vulnerabilities = get_by_control(db, control_id, org_id=scope)

    results = []

    for vulnerability in vulnerabilities:

        results.append(
            {
                "id":
                    vulnerability.id,

                "plugin_id":
                    vulnerability.plugin_id,

                "title":
                    vulnerability.title,

                "severity":
                    vulnerability.severity,

                "cvss_score":
                    vulnerability.cvss_score,

                "status":
                    vulnerability.status
            }
        )

    return {
        "control_id":
            control.control_id,

        "control_name":
            control.title,

        "framework":
            control.category.framework.short_name,

        "affected_vulnerabilities":
            len(vulnerabilities),

        "vulnerabilities":
            results
    }

@router.get(
    "/frameworks/{framework_name}/summary"
)
def get_framework_summary(
    framework_name: str,
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
    Return vulnerability-mapping coverage for a framework's controls.

    This is deliberately NOT called "compliance_score" - that name is
    owned by analytics/compliance.py (% of controls manually marked
    "Implemented", used by /compliance-summary and
    /dashboard/grc/{name}). This endpoint measures something different
    (100% minus % of controls with an approved vulnerability mapping)
    and the two could disagree for the same framework at the same
    time if both were called "compliance_score".
    """

    controls = get_controls_by_framework(db, framework_name)

    total_controls = len(
        controls
    )

    affected_controls = 0

    affected_vulnerabilities = 0

    for control in controls:

        # Only approved mappings count toward compliance - a
        # pending, unreviewed match shouldn't move the score.
        vulnerability_count = count_by_control(
            db, control.id, status=MAPPING_STATUS_APPROVED, org_id=scope
        )

        if vulnerability_count > 0:

            affected_controls += 1

            affected_vulnerabilities += (
                vulnerability_count
            )

    vulnerability_coverage_score = (
        (
            total_controls
            - affected_controls
        )
        /
        total_controls
        * 100
        if total_controls > 0
        else 0
    )

    return {
        "framework":
            framework_name,

        "total_controls":
            total_controls,

        "affected_controls":
            affected_controls,

        "affected_vulnerabilities":
            affected_vulnerabilities,

        "vulnerability_coverage_score":
            round(
                vulnerability_coverage_score,
                2
            )
    }
