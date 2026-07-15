"""
CyberRisk360

Purpose:
Save uploaded remediation-evidence files to disk and persist their
metadata. Mirrors the UPLOAD_DIR + uuid4()-prefixed-filename
convention already used for scan-report uploads in
app/api/imports.py, under a separate "evidence" subdirectory.
"""

import os
import uuid

from app.core.constants import UPLOAD_DIR

from app.repositories.remediation.evidence_repository import (
    create_evidence_attachment
)

EVIDENCE_DIR = UPLOAD_DIR / "evidence"

ALLOWED_EVIDENCE_EXTENSIONS = {
    "pdf", "png", "jpg", "jpeg", "csv", "txt", "docx", "xlsx", "log"
}


def save_evidence(
    db,
    *,
    file,
    uploaded_by_id: int,
    org_id: int,
    vulnerability_id: int = None,
    risk_id: int = None
):
    """
    Validate and persist one evidence upload. Exactly one of
    vulnerability_id / risk_id must be set - the caller (an
    endpoint nested under either /vulnerabilities or /risks) always
    passes exactly one, so this is a defensive check, not a normal
    user-facing error path.
    """

    if bool(vulnerability_id) == bool(risk_id):
        raise ValueError(
            "Exactly one of vulnerability_id/risk_id must be set"
        )

    file_extension = (
        (file.filename or "")
        .split(".")[-1]
        .lower()
    )

    if file_extension not in ALLOWED_EVIDENCE_EXTENSIONS:
        raise ValueError(
            "Unsupported file type - allowed: "
            + ", ".join(sorted(ALLOWED_EVIDENCE_EXTENSIONS))
        )

    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    stored_path = str(EVIDENCE_DIR / f"{uuid.uuid4()}_{file.filename}")

    contents = file.file.read()

    with open(stored_path, "wb") as buffer:
        buffer.write(contents)

    return create_evidence_attachment(
        db,
        vulnerability_id=vulnerability_id,
        risk_id=risk_id,
        file_name=file.filename,
        stored_path=stored_path,
        content_type=file.content_type,
        file_size=len(contents),
        uploaded_by_id=uploaded_by_id,
        org_id=org_id,
    )


def serialize_evidence(attachment):
    """
    API-facing representation of an evidence attachment. Deliberately
    omits stored_path - the on-disk location is a server-internal
    detail, not something a client needs (downloads go through
    GET /evidence/{id}/download by id).
    """

    return {
        "id": attachment.id,
        "vulnerability_id": attachment.vulnerability_id,
        "risk_id": attachment.risk_id,
        "file_name": attachment.file_name,
        "content_type": attachment.content_type,
        "file_size": attachment.file_size,
        "uploaded_by_id": attachment.uploaded_by_id,
        "org_id": attachment.org_id,
        "uploaded_at": attachment.uploaded_at,
    }
