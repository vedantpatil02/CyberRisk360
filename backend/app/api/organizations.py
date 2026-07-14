"""
CyberRisk360

Purpose:
Platform organization (tenant) management. Restricted to the platform
super-admin - org provisioning is a cross-tenant, platform-level action.
"""

from typing import List

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.core.constants import ROLE_SUPER_ADMIN

from app.schemas.organization import OrganizationCreate, OrganizationOut
from app.repositories.organizations.organization_repository import (
    get_all_organizations,
    get_organization_by_slug,
    create_organization,
)
from app.services.audit.audit import record_audit, client_ip


router = APIRouter()


@router.get("/organizations", response_model=List[OrganizationOut])
def list_organizations(
    db: Session = Depends(get_db),
    current_user=Depends(require_role(ROLE_SUPER_ADMIN)),
):
    """
    List every organization (platform super-admin only).
    """

    return get_all_organizations(db)


@router.post("/organizations", response_model=OrganizationOut, status_code=201)
def create_org(
    payload: OrganizationCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(require_role(ROLE_SUPER_ADMIN)),
):
    """
    Create a new organization (platform super-admin only).
    """

    if get_organization_by_slug(db, payload.slug):
        raise HTTPException(
            status_code=409,
            detail="Organization slug already exists",
        )

    organization = create_organization(db, name=payload.name, slug=payload.slug)

    record_audit(
        db,
        action="organization.create",
        actor=current_user.get("sub"),
        entity_type="organization",
        entity_id=organization.id,
        ip_address=client_ip(request),
        detail=f"slug={organization.slug}",
        org_id=organization.id,
    )

    return organization
