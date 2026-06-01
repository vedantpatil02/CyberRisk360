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

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR,
    VULNERABILITY_STATUS_OPEN
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

