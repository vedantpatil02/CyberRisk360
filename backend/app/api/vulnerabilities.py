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

from app.schemas.vulnerability_update import (
    VulnerabilityUpdate
)

from app.services.validators import (
    validate_cvss_score
)

from app.services.vulnerability_summary import (
    get_vulnerability_summary as generate_summary
)

from app.services.control_suggester import (
    suggest_control_names
)

from app.services.vulnerability_summary import (
    get_top_critical_vulnerabilities
)

from app.models.control import Control
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
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
    "/vulnerabilities/top-critical"
)
def top_critical_vulnerabilities(
    db: Session = Depends(get_db),
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
            db
        )
    )

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

@router.get("/vulnerability-summary")
def vulnerability_summary(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    return generate_summary(db)



@router.get(
    "/vulnerabilities/{vulnerability_id}/suggested-controls"
)
def get_suggested_controls(
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

    # Retrieve vulnerability
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

    # Get suggested control names
    control_names = (
        suggest_control_names(
            vulnerability.title
        )
    )

    recommended_controls = []

    # Search controls table
    for control_name in control_names:

        controls = (
            db.query(Control)
            .filter(
                Control.name.ilike(
                    f"%{control_name}%"
                )
            )
            .all()
        )

        for control in controls:

            recommended_controls.append(
                {
                    "control_id":
                        control.control_id,

                    "name":
                        control.name,

                    "framework":
                        control.framework,

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
    db: Session = Depends(get_db)
):

    controls = (
        db.query(
            Control
        )
        .join(
            VulnerabilityControlMapping,
            VulnerabilityControlMapping.control_id
            == Control.id
        )
        .filter(
            VulnerabilityControlMapping.vulnerability_id
            == vulnerability_id
        )
        .all()
    )

    results = []

    for control in controls:

        results.append(
            {
                "control_id":
                    control.control_id,

                "name":
                    control.name,

                "framework":
                    control.framework,

                "status":
                    control.status
            }
        )

    return results