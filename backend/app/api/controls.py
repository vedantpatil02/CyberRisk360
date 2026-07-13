"""
CyberRisk360

Purpose:
Manage compliance controls.
"""

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.schemas.control import ControlCreate

from app.dependencies.database import get_db

from app.dependencies.rbac import require_role

from app.core.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_AUDITOR, CONTROL_STATUS_MISSING

from app.analytics.compliance import calculate_compliance_summary

from app.schemas.control_update import ControlUpdate

from app.repositories.controls.control_repository import (
    get_all_controls,
    get_control as db_get_control,
    create_control as db_create_control,
    update_control_status as db_update_control_status,
    get_controls_by_framework
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_by_control
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    count_by_control
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

        return {
            "message":
            "Control not found"
        }

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

        return {
            "message":
            "Control not found"
        }

    db_update_control_status(
        db,
        control,
        control_update.status
    )

    return {
        "message":
        "Control updated"
    }

@router.get(
    "/controls/{control_id}/vulnerabilities"
)
def get_control_vulnerabilities(
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
    Return vulnerabilities mapped
    to a compliance control.
    """

    control = db_get_control(db, control_id)

    if not control:

        return {
            "message":
            "Control not found"
        }

    vulnerabilities = get_by_control(db, control_id)

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
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Return compliance summary
    for a framework.
    """

    controls = get_controls_by_framework(db, framework_name)

    total_controls = len(
        controls
    )

    affected_controls = 0

    affected_vulnerabilities = 0

    for control in controls:

        vulnerability_count = count_by_control(db, control.id)

        if vulnerability_count > 0:

            affected_controls += 1

            affected_vulnerabilities += (
                vulnerability_count
            )

    compliance_score = (
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

        "compliance_score":
            round(
                compliance_score,
                2
            )
    }
