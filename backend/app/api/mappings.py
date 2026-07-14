"""
CyberRisk360

Purpose:
Review vulnerability-control mappings produced by the mapping
engine: list pending mappings, inspect a mapping's audit history,
and approve or reject a mapping.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_db
)

from app.dependencies.rbac import (
    require_role
)

from app.dependencies.tenancy import org_scope

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR
)

from app.schemas.mapping_review import (
    MappingReview
)

from app.services.mapping.mapping_service import (
    list_mappings_for_vulnerability,
    list_pending_mappings,
    get_mapping_history,
    review_mapping
)

from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_MAPPING_APPROVE,
    ACTION_MAPPING_REJECT
)

router = APIRouter()


@router.get(
    "/mappings/pending"
)
def get_pending_mappings(
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    List mappings awaiting manual approval.
    """

    return list_pending_mappings(db, org_id=scope)


@router.get(
    "/vulnerabilities/{vulnerability_id}/mappings"
)
def get_vulnerability_mappings(
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
    List all control mappings (any status) for a vulnerability.
    """

    return list_mappings_for_vulnerability(db, vulnerability_id)


@router.get(
    "/mappings/{mapping_id}/history"
)
def get_mapping_history_endpoint(
    mapping_id: int,
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
    Return the audit trail for a mapping (created/approved/rejected).
    """

    return get_mapping_history(db, mapping_id)


@router.patch(
    "/mappings/{mapping_id}/approve"
)
def approve_mapping(
    mapping_id: int,
    request: Request,
    review: MappingReview = MappingReview(),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Approve a pending mapping.
    """

    mapping = review_mapping(
        db,
        mapping_id,
        approve=True,
        reviewer=current_user.get("sub"),
        note=review.note,
        org_id=scope
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Mapping not found"
        )

    record_audit(
        db,
        action=ACTION_MAPPING_APPROVE,
        actor=current_user.get("sub"),
        entity_type="mapping",
        entity_id=mapping_id,
        ip_address=client_ip(request),
        org_id=mapping.org_id,
    )

    # The audit commit expires `mapping`; reload it so the response
    # serializes its columns rather than an empty object.
    db.refresh(mapping)

    return mapping


@router.patch(
    "/mappings/{mapping_id}/reject"
)
def reject_mapping(
    mapping_id: int,
    request: Request,
    review: MappingReview = MappingReview(),
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Reject a pending mapping.
    """

    mapping = review_mapping(
        db,
        mapping_id,
        approve=False,
        reviewer=current_user.get("sub"),
        note=review.note,
        org_id=scope
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Mapping not found"
        )

    record_audit(
        db,
        action=ACTION_MAPPING_REJECT,
        actor=current_user.get("sub"),
        entity_type="mapping",
        entity_id=mapping_id,
        ip_address=client_ip(request),
        org_id=mapping.org_id,
    )

    # The audit commit expires `mapping`; reload it so the response
    # serializes its columns rather than an empty object.
    db.refresh(mapping)

    return mapping
