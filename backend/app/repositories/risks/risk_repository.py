from sqlalchemy.orm import Session

from app.models.risk import Risk


def get_all_risks(
    db: Session
):
    return (
        db.query(Risk)
        .all()
    )


def get_risk(
    db: Session,
    risk_id: int
):
    return (
        db.query(Risk)
        .filter(
            Risk.id == risk_id
        )
        .first()
    )


def get_auto_risk_by_asset(
    db: Session,
    asset_id: int
):
    """
    Return the engine-generated ("auto") risk for an asset, if any.
    There is at most one per asset; manual risks are never returned.
    """

    return (
        db.query(Risk)
        .filter(
            Risk.asset_id == asset_id,
            Risk.source == "auto"
        )
        .first()
    )


def create_risk(
    db: Session,
    **fields
):
    risk = Risk(**fields)

    db.add(risk)
    db.commit()
    db.refresh(risk)

    return risk


def update_risk(
    db: Session,
    risk: Risk,
    updates: dict
):
    for field, value in updates.items():
        setattr(risk, field, value)

    db.commit()

    return risk
