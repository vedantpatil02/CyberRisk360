"""
CyberRisk360

Purpose:
Manage compliance controls.
"""

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.models.control import Control

from app.schemas.control import ControlCreate

from app.dependencies.database import get_db

from app.dependencies.rbac import require_role

from app.core.constants import ROLE_ADMIN, ROLE_ANALYST, ROLE_AUDITOR, CONTROL_STATUS_MISSING

from app.services.compliance_summary import calculate_compliance_summary

from app.schemas.control_update import ControlUpdate

from app.models.vulnerability import Vulnerability
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
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

    new_control = Control(
        control_id=control.control_id,
        name=control.name,
        description=control.description,
        framework=control.framework,
        status=CONTROL_STATUS_MISSING
    )

    db.add(
        new_control
    )

    db.commit()

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

    return db.query(
        Control
    ).all()

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

    control = (
        db.query(
            Control
        )
        .filter(
            Control.id
            ==
            control_id
        )
        .first()
    )

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

    controls = (
        db.query(Control)
        .all()
    )

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

    control = (
        db.query(Control)
        .filter(
            Control.id
            ==
            control_id
        )
        .first()
    )

    if not control:

        return {
            "message":
            "Control not found"
        }

    control.status = (
        control_update.status
    )

    db.commit()

    return {
        "message":
        "Control updated"
    }

@router.get(
    "/controls/{control_id}/vulnerabilities"
)
def get_control_vulnerabilities(
    control_id: int,
    db: Session = Depends(get_db)
):
    """
    Return vulnerabilities mapped
    to a compliance control.
    """

    control = (
        db.query(Control)
        .filter(
            Control.id == control_id
        )
        .first()
    )

    if not control:

        return {
            "message":
            "Control not found"
        }

    vulnerabilities = (
        db.query(
            Vulnerability
        )
        .join(
            VulnerabilityControlMapping,
            VulnerabilityControlMapping.vulnerability_id
            == Vulnerability.id
        )
        .filter(
            VulnerabilityControlMapping.control_id
            == control_id
        )
        .all()
    )

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
            control.name,

        "framework":
            control.framework,

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
    db: Session = Depends(get_db)
):
    """
    Return compliance summary
    for a framework.
    """

    controls = (
        db.query(Control)
        .filter(
            Control.framework
            == framework_name
        )
        .all()
    )

    total_controls = len(
        controls
    )

    affected_controls = 0

    affected_vulnerabilities = 0

    for control in controls:

        vulnerability_count = (
            db.query(
                VulnerabilityControlMapping
            )
            .filter(
                VulnerabilityControlMapping.control_id
                == control.id
            )
            .count()
        )

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