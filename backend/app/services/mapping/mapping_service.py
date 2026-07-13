"""
CyberRisk360

Purpose:
Business logic for reviewing and querying vulnerability-control
mappings produced by the mapping engine.
"""

from app.core.constants import (
    MAPPING_STATUS_APPROVED,
    MAPPING_STATUS_REJECTED
)

from app.repositories.vulnerability_control_mappings.mapping_repository import (
    get_mapping,
    get_by_vulnerability,
    get_pending_mappings,
    update_mapping_status
)

from app.repositories.vulnerability_control_mappings.mapping_history_repository import (
    get_history_for_mapping,
    record_history
)


def list_mappings_for_vulnerability(db, vulnerability_id):
    return get_by_vulnerability(db, vulnerability_id)


def list_pending_mappings(db):
    return get_pending_mappings(db)


def get_mapping_history(db, mapping_id):
    return get_history_for_mapping(db, mapping_id)


def review_mapping(db, mapping_id, approve: bool, reviewer: str = None, note: str = None):
    """
    Approve or reject a pending mapping. Returns None if the mapping
    doesn't exist so the API layer can turn that into a 404.
    """

    mapping = get_mapping(db, mapping_id)

    if not mapping:
        return None

    previous_status = mapping.status
    new_status = MAPPING_STATUS_APPROVED if approve else MAPPING_STATUS_REJECTED

    update_mapping_status(db, mapping, new_status, reviewed_by=reviewer)

    record_history(
        db,
        mapping_id=mapping.id,
        action="approved" if approve else "rejected",
        previous_status=previous_status,
        new_status=new_status,
        actor=reviewer,
        note=note
    )

    db.commit()
    db.refresh(mapping)

    return mapping
