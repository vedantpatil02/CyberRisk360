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

from sqlalchemy.orm import Session

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

from app.schemas.mapping_review import (
    MappingReview
)

from app.services.mapping.mapping_service import (
    list_mappings_for_vulnerability,
    list_pending_mappings,
    get_mapping_history,
    review_mapping
)

router = APIRouter()


@router.get(
    "/mappings/pending"
)
def get_pending_mappings(
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
    List mappings awaiting manual approval.
    """

    return list_pending_mappings(db)


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
    review: MappingReview = MappingReview(),
    db: Session = Depends(get_db),
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
        note=review.note
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Mapping not found"
        )

    return mapping


@router.patch(
    "/mappings/{mapping_id}/reject"
)
def reject_mapping(
    mapping_id: int,
    review: MappingReview = MappingReview(),
    db: Session = Depends(get_db),
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
        note=review.note
    )

    if not mapping:
        raise HTTPException(
            status_code=404,
            detail="Mapping not found"
        )

    return mapping
