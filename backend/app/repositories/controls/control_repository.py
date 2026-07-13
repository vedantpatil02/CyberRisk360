from sqlalchemy.orm import Session

from app.models.control import Control
from app.models.category import Category
from app.models.framework import Framework
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
)



def get_all_controls(
    db: Session
):
    return (
        db.query(Control)
        .all()
    )

def get_controls_by_framework(
    db: Session,
    framework_short_name: str
):
    return (
        db.query(Control)
        .join(Category)
        .join(Framework)
        .filter(
            Framework.short_name ==
            framework_short_name
        )
        .all()
    )

def get_control(
    db: Session,
    control_id: int
):
    return (
        db.query(Control)
        .filter(
            Control.id == control_id
        )
        .first()
    )

def get_control_by_code(
    db: Session,
    control_code: str
):
    return (
        db.query(Control)
        .filter(
            Control.control_id ==
            control_code
        )
        .first()
    )

def create_control(
    db: Session,
    **fields
):
    control = Control(**fields)

    db.add(control)
    db.commit()
    db.refresh(control)

    return control

def update_control_status(
    db: Session,
    control: Control,
    status: str
):
    control.status = status
    db.commit()

    return control

def search_controls_by_title(
    db: Session,
    keyword: str
):
    return (
        db.query(Control)
        .filter(
            Control.title.ilike(
                f"%{keyword}%"
            )
        )
        .all()
    )

def get_controls_by_vulnerability(
    db: Session,
    vulnerability_id: int
):
    return (
        db.query(Control)
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