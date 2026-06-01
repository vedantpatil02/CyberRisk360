from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.schemas.risk import RiskCreate

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.core.constants import *

from app.services.risk import calculate_risk_score, calculate_risk_level
from app.schemas.risk_update import RiskUpdate

router = APIRouter()


@router.post("/risks")
def create_risk(
    risk: RiskCreate,
    db: Session = Depends(get_db),
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

    # Calculate risk score
    score = calculate_risk_score(
        risk.impact,
        risk.likelihood
    )

    # Determine risk severity
    level = calculate_risk_level(
        score
    )

    # Create database record
    new_risk = Risk(
        title=risk.title,
        description=risk.description,
        asset_id=risk.asset_id,
        impact=risk.impact,
        likelihood=risk.likelihood,
        risk_score=score,
        risk_level=level,
        owner=risk.owner
    )

    # Save risk into database
    db.add(new_risk)

    # Commit transaction
    db.commit()

    return {
        "message": "Risk created",
        "score": score,
        "level": level
    }

@router.get("/risks/{risk_id}")
def get_risk(
    risk_id: int,
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
    Retrieve a specific risk.
    """

    risk = (
        db.query(Risk)
        .filter(Risk.id == risk_id)
        .first()
    )

    if not risk:

        return {
            "message": "Risk not found"
        }

    return risk


@router.put("/risks/{risk_id}")
def update_risk(
    risk_id: int,
    risk_update: RiskUpdate,
    db: Session = Depends(get_db),
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

    risk = (
        db.query(Risk)
        .filter(Risk.id == risk_id)
        .first()
    )

    if not risk:

        return {
            "message": "Risk not found"
        }

    update_data = risk_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        setattr(
            risk,
            field,
            value
        )

    # Recalculate score if impact or likelihood changes
    if (
        risk_update.impact is not None
        or
        risk_update.likelihood is not None
    ):

        risk.risk_score = (
            calculate_risk_score(
                risk.impact,
                risk.likelihood
            )
        )

        risk.risk_level = (
            calculate_risk_level(
                risk.risk_score
            )
        )

    db.commit()

    return {
        "message": "Risk updated"
    }

@router.patch(
    "/risks/{risk_id}/close"
)
def close_risk(
    risk_id: int,
    db: Session = Depends(get_db),
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

    risk = (
        db.query(Risk)
        .filter(Risk.id == risk_id)
        .first()
    )

    if not risk:

        return {
            "message": "Risk not found"
        }

    risk.status = (
        RISK_STATUS_CLOSED
    )

    db.commit()

    return {
        "message": "Risk closed"
    }

@router.get("/risk-summary")
def get_risk_summary(
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
    Return risk statistics.
    """

    risks = db.query(
        Risk
    ).all()

    summary = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0
    }

    for risk in risks:

        level = (
            risk.risk_level.lower()
        )

        if level in summary:

            summary[level] += 1

    return summary