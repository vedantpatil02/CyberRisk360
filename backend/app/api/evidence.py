"""
CyberRisk360

Purpose:
Generic evidence-attachment operations (download/delete) that aren't
tied to whether the attachment is on a vulnerability or a risk.
Upload/list are nested under /vulnerabilities/{id}/evidence and
/risks/{id}/evidence instead, since those need to validate the parent
record first.
"""

import os

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.responses import FileResponse

from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope

from app.core.constants import WRITE_ROLES, READ_ROLES

from app.repositories.remediation.evidence_repository import (
    get_evidence_attachment,
    delete_evidence_attachment
)

router = APIRouter()


@router.get("/evidence/{attachment_id}/download")
def download_evidence(
    attachment_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*READ_ROLES))
):
    attachment = get_evidence_attachment(db, attachment_id, org_id=scope)

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Evidence attachment not found"
        )

    return FileResponse(
        attachment.stored_path,
        filename=attachment.file_name,
        media_type=attachment.content_type or "application/octet-stream",
    )


@router.delete("/evidence/{attachment_id}")
def delete_evidence(
    attachment_id: int,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(require_role(*WRITE_ROLES))
):
    attachment = get_evidence_attachment(db, attachment_id, org_id=scope)

    if not attachment:
        raise HTTPException(
            status_code=404,
            detail="Evidence attachment not found"
        )

    # Best-effort file removal - the DB row is the source of truth;
    # a stale/missing file on disk shouldn't block deleting the record.
    try:
        os.remove(attachment.stored_path)
    except OSError:
        pass

    delete_evidence_attachment(db, attachment)

    return {"message": "Evidence attachment deleted"}
