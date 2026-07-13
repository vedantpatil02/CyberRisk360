from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File
from fastapi import HTTPException

import os
import uuid

from app.dependencies.rbac import (
    require_role
)

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

router = APIRouter()

import time


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

    # start = time.time()

    result = process_report(
        upload_path
    )

    # print(
    #     "PROCESS REPORT:",
    #     round(
    #         time.time() - start,
    #         2
    #     ),
    #     "seconds"
    # )

    if result["file_type"] == "pdf":

        try:

            # start = time.time()

            import_result = (
                import_findings(
                    db,
                    result["findings"]
                )
            )

            # print(
            #     "IMPORT FINDINGS:",
            #     round(
            #         time.time() - start,
            #         2
            #     ),
            #     "seconds"
            # )

            result["import_result"] = (
                import_result
            )

        except Exception:

            import traceback

            # Full traceback stays server-side; the client only gets
            # a generic message so internal details (paths, query
            # text, etc.) aren't leaked.
            traceback.print_exc()

            raise HTTPException(
                status_code=500,
                detail="Failed to process import findings"
            )

    return result