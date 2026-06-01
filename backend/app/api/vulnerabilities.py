"""
CyberRisk360

Purpose:
Manage vulnerability records and
associate them with assets and risks.
"""

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.models.vulnerability import (
    Vulnerability
)

from app.schemas.vulnerability import (
    VulnerabilityCreate
)

from app.dependencies.database import (
    get_db
)

from app.dependencies.rbac import (
    require_role
)

from app.services.cvss import (
    calculate_severity
)

from app.core.constants import *

from app.schemas.vulnerability_update import (
    VulnerabilityUpdate
)

from app.services.validators import (
    validate_cvss_score
)

from app.services.vulnerability_summary import (
    initialize_vulnerability_summary
)

router = APIRouter()


@router.post("/vulnerabilities")
def create_vulnerability(
    vulnerability: VulnerabilityCreate,
    db: Session = Depends(get_db),
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

    # Calculate severity from CVSS score
    severity = calculate_severity(
        vulnerability.cvss_score
    )

    # Create database object
    new_vulnerability = Vulnerability(
        title=vulnerability.title,
        description=vulnerability.description,
        asset_id=vulnerability.asset_id,
        risk_id=vulnerability.risk_id,
        cvss_score=vulnerability.cvss_score,
        severity=severity,
        owner=vulnerability.owner,
        status=VULNERABILITY_STATUS_OPEN
    )

    db.add(
        new_vulnerability
    )

    db.commit()

    return {
        "message": "Vulnerability created",
        "severity": severity
    }


@router.get("/vulnerabilities")
def get_vulnerabilities(
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
    Retrieve all vulnerabilities.
    """

    return db.query(
        Vulnerability
    ).all()


@router.get(
    "/vulnerabilities/{vulnerability_id}"
)
def get_vulnerability(
    vulnerability_id: int,
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
    Retrieve a specific vulnerability.
    """

    vulnerability = (
        db.query(
            Vulnerability
        )
        .filter(
            Vulnerability.id
            ==
            vulnerability_id
        )
        .first()
    )

    if not vulnerability:

        return {
            "message":
            "Vulnerability not found"
        }

    return vulnerability

@router.put(
    "/vulnerabilities/{vulnerability_id}"
)
def update_vulnerability(
    vulnerability_id: int,
    vulnerability_update: VulnerabilityUpdate,
    db: Session = Depends(get_db),
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

    vulnerability = (
        db.query(
            Vulnerability
        )
        .filter(
            Vulnerability.id
            ==
            vulnerability_id
        )
        .first()
    )

    if not vulnerability:

        return {
            "message":
            "Vulnerability not found"
        }

    # Validate CVSS score
    if (
        vulnerability_update.cvss_score
        is not None
    ):

        if not validate_cvss_score(
            vulnerability_update.cvss_score
        ):

            return {
                "message":
                "Invalid CVSS score"
            }

    update_data = (
        vulnerability_update
        .model_dump(
            exclude_unset=True
        )
    )

    for field, value in update_data.items():

        setattr(
            vulnerability,
            field,
            value
        )

    # Recalculate severity
    if (
        vulnerability_update.cvss_score
        is not None
    ):

        vulnerability.severity = (
            calculate_severity(
                vulnerability.cvss_score
            )
        )

    db.commit()

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

    vulnerability = (
        db.query(
            Vulnerability
        )
        .filter(
            Vulnerability.id
            ==
            vulnerability_id
        )
        .first()
    )

    if not vulnerability:

        return {
            "message":
            "Vulnerability not found"
        }

    vulnerability.status = (
        VULNERABILITY_STATUS_CLOSED
    )

    db.commit()

    return {
        "message":
        "Vulnerability closed"
    }

@router.get(
    "/vulnerability-summary"
)
def get_vulnerability_summary(
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
    Return vulnerability dashboard statistics.
    """

    vulnerabilities = (
        db.query(
            Vulnerability
        )
        .all()
    )

    summary = (
        initialize_vulnerability_summary()
    )

    for vulnerability in vulnerabilities:

        # Count severities
        if vulnerability.severity:

            severity = (
                vulnerability.severity.lower()
            )

            if severity in summary:

                summary[severity] += 1

        # Count open vulnerabilities
        if (
            vulnerability.status
            ==
            VULNERABILITY_STATUS_OPEN
        ):

            summary["open"] += 1

        # Count closed vulnerabilities
        elif (
            vulnerability.status
            ==
            VULNERABILITY_STATUS_CLOSED
        ):

            summary["closed"] += 1

    return summary