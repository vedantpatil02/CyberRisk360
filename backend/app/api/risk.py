from fastapi import APIRouter
from fastapi import Depends

from sqlalchemy.orm import Session

from app.models.risk import Risk
from app.schemas.risk import RiskCreate

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role

from app.services.risk import (
    calculate_risk_score,
    calculate_risk_level
)

router = APIRouter()


@router.post("/risks")
def create_risk(
    risk: RiskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            "admin",
            "analyst"
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


@router.get("/risks")
def get_risks(
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            "admin",
            "analyst",
            "auditor"
        )
    )
):
    return db.query(Risk).all()