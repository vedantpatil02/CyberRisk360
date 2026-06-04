from fastapi import APIRouter
from fastapi import Depends
from fastapi import UploadFile
from fastapi import File

import os

from app.services.nessus_importer import (
    parse_nessus_csv
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

router = APIRouter()


@router.post(
    "/imports/nessus_report_upload"
)
def upload_report(
    file: UploadFile = File(...),
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

    os.makedirs(
        "uploads",
        exist_ok=True
    )

    upload_path = (
        f"uploads/{file.filename}"
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

    return result