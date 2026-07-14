"""
CyberRisk360

Purpose:
Data access for organizations (tenants).
"""

from sqlalchemy.orm import Session

from app.models.organization import Organization


def get_all_organizations(db: Session):
    return db.query(Organization).order_by(Organization.id).all()


def get_organization(db: Session, org_id: int):
    return (
        db.query(Organization)
        .filter(Organization.id == org_id)
        .first()
    )


def get_organization_by_slug(db: Session, slug: str):
    return (
        db.query(Organization)
        .filter(Organization.slug == slug)
        .first()
    )


def create_organization(db: Session, name: str, slug: str):
    organization = Organization(name=name, slug=slug)

    db.add(organization)
    db.commit()
    db.refresh(organization)

    return organization
