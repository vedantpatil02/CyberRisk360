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

