from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException
from fastapi import Request

import os
import uuid

from app.core.logging import get_logger

from app.dependencies.rbac import (
    require_role
)

from app.dependencies.tenancy import org_home

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    UPLOAD_DIR
)

from app.services.imports.report_processor import (
    process_report
)

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_db
)

from app.services.vulnerabilities.vulnerability_importer import (
    import_findings
)

from app.services.audit.audit import (
    record_audit,
    client_ip,
    ACTION_IMPORT_UPLOAD
)

router = APIRouter()

logger = get_logger("imports")

ALLOWED_REPORT_EXTENSIONS = {"pdf", "csv", "nessus"}


@router.post(
    "/imports/nessus_report_upload"
)
def upload_report(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    org_id=Depends(org_home),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST
        )
    )
):
    """
    Upload and process
    security reports.
    """

    # print("UPLOAD REQUEST RECEIVED")

    file_extension = (
        (file.filename or "")
        .split(".")[-1]
        .lower()
    )

    if file_extension not in ALLOWED_REPORT_EXTENSIONS:

        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type - allowed: "
                + ", ".join(sorted(ALLOWED_REPORT_EXTENSIONS))
            )
        )

    os.makedirs(
        UPLOAD_DIR,
        exist_ok=True
    )

    upload_path = (
        f"{UPLOAD_DIR}/"
        f"{uuid.uuid4()}_{file.filename}"
    )

    with open(
        upload_path,
        "wb"
    ) as buffer:

        buffer.write(
            file.file.read()
        )

    try:

        result = process_report(
            upload_path
        )

    except Exception:

        # Full traceback stays server-side; the client only gets a
        # generic message so internal details (paths, parser
        # internals, etc.) aren't leaked. Covers malformed CSV/XML
        # and any other unexpected parse failure.
        logger.exception("Failed to parse uploaded report")

        raise HTTPException(
            status_code=400,
            detail="Failed to parse report"
        )

    if result.get("findings"):

        try:

            import_result = (
                import_findings(
                    db,
                    result["findings"],
                    org_id
                )
            )

            result["import_result"] = (
                import_result
            )

        except Exception:

            # Full traceback stays server-side; the client only gets
            # a generic message so internal details (paths, query
            # text, etc.) aren't leaked.
            logger.exception("Failed to process import findings")

            raise HTTPException(
                status_code=500,
                detail="Failed to process import findings"
            )

    record_audit(
        db,
        action=ACTION_IMPORT_UPLOAD,
        actor=current_user.get("sub"),
        entity_type="import",
        ip_address=client_ip(request),
        detail=(
            f"file_type={file_extension}, "
            f"findings={len(result.get('findings') or [])}"
        ),
        org_id=org_id,
    )

    return result
