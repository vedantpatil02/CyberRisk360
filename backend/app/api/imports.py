from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File

import os
import uuid

from app.importers.nessus_pdf_parser import (
    extract_findings
)

from app.dependencies.rbac import (
    require_role
)

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST
)

from app.services.report_processor import (
    process_report
)

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_db
)

from app.services.vulnerability_importer import (
    import_findings
)

router = APIRouter()


@router.post(
    "/imports/nessus_report_upload"
)
def upload_report(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
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

    os.makedirs(
        "uploads",
        exist_ok=True
    )

    upload_path = (
        f"uploads/{uuid.uuid4()}_{file.filename}"
    )

    with open(
        upload_path,
        "wb"
    ) as buffer:

        buffer.write(
            file.file.read()
        )

    result = process_report(
        upload_path
    )

    if result["file_type"] == "pdf":

        try:
            
            # print("BEFORE IMPORT")
            import_result = (
                import_findings(
                    db,
                    result["findings"]
                )
            )

            # print("AFTER IMPORT")

            result["import_result"] = (
                import_result
            )

        except Exception as error:

            import traceback

            traceback.print_exc()

            return {
                "error": str(error)
            }

    return result