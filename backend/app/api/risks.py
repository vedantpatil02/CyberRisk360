from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from sqlalchemy.orm import Session

from app.schemas.risk import RiskCreate

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.core.constants import *

from app.services.risks.risk import calculate_risk_score, calculate_risk_level
from app.schemas.risk_update import RiskUpdate
from app.analytics.risk_summary import initialize_summary

from app.repositories.risks.risk_repository import (
    get_all_risks as db_get_all_risks,
    get_risk as db_get_risk,
    create_risk as db_create_risk,
    update_risk as db_update_risk
)
from app.repositories.assets.asset_repository import (
    get_asset
)


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

    if not get_asset(db, risk.asset_id):

        raise HTTPException(
            status_code=404,
            detail="Asset not found"
        )

    score = calculate_risk_score(
        risk.impact,
        risk.likelihood
    )

    level = calculate_risk_level(
        score
    )

    db_create_risk(
        db,
        title=risk.title,
        description=risk.description,
        asset_id=risk.asset_id,
        impact=risk.impact,
        likelihood=risk.likelihood,
        risk_score=score,
        risk_level=level,
        owner=risk.owner
    )

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

    risk = db_get_risk(db, risk_id)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

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

    risk = db_get_risk(db, risk_id)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    update_data = risk_update.model_dump(
        exclude_unset=True
    )

    # Recalculate score if impact or likelihood changes
    if (
        risk_update.impact is not None
        or
        risk_update.likelihood is not None
    ):

        new_impact = update_data.get(
            "impact", risk.impact
        )

        new_likelihood = update_data.get(
            "likelihood", risk.likelihood
        )

        update_data["risk_score"] = calculate_risk_score(
            new_impact,
            new_likelihood
        )

        update_data["risk_level"] = calculate_risk_level(
            update_data["risk_score"]
        )

    db_update_risk(db, risk, update_data)

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

    risk = db_get_risk(db, risk_id)

    if not risk:

        raise HTTPException(
            status_code=404,
            detail="Risk not found"
        )

    db_update_risk(
        db,
        risk,
        {"status": RISK_STATUS_CLOSED}
    )

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
    Return dashboard statistics
    for all risks.
    """

    risks = db_get_all_risks(db)

    summary = initialize_summary()

    for risk in risks:

        if risk.risk_level:

            level = (
                risk.risk_level.lower()
            )

            if level in summary:

                summary[level] += 1

        if (
            risk.status
            ==
            RISK_STATUS_OPEN
        ):

            summary[SUMMARY_OPEN] += 1

        elif (
            risk.status
            ==
            RISK_STATUS_CLOSED
        ):

            summary[SUMMARY_CLOSED] += 1

    return summary
