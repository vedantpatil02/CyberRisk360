"""
CyberRisk360

Purpose:
Manage risk-control mappings.
"""

from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.database import SessionLocal

from app.models.risk import Risk
from app.models.control import Control
from app.models.risk_control_mapping import (
    RiskControlMapping
)

from app.schemas.risk_control_mapping import (
    RiskControlMappingCreate
)

from app.dependencies.database import (
    get_db
)

from app.dependencies.rbac import (
    require_role
)

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR
)

router = APIRouter()

@router.post(
    "/risk-control-mappings"
)
def create_mapping(
    mapping: RiskControlMappingCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Map a control to a risk.
    """

    risk = (
        db.query(Risk)
        .filter(
            Risk.id
            ==
            mapping.risk_id
        )
        .first()
    )

    if not risk:

        return {
            "message":
            "Risk not found"
        }

    control = (
        db.query(Control)
        .filter(
            Control.id
            ==
            mapping.control_id
        )
        .first()
    )

    if not control:

        return {
            "message":
            "Control not found"
        }

    new_mapping = (
        RiskControlMapping(
            risk_id=mapping.risk_id,
            control_id=mapping.control_id
        )
    )

    db.add(
        new_mapping
    )

    db.commit()

    return {
        "message":
        "Mapping created"
    }

@router.get(
    "/risk-control-mappings"
)
def get_mappings(
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
    Retrieve all mappings.
    """

    return db.query(
        RiskControlMapping
    ).all()


