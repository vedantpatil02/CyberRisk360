"""
CyberRisk360

Purpose:
Expose compliance framework data.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query

from app.dependencies.rbac import (
    require_role
)

from app.core.constants import (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_AUDITOR
)

from app.services.framework_loader import (
    load_framework
)

router = APIRouter()


@router.get(
    "/frameworks/{framework_name}/search"
)
def search_framework_controls(
    framework_name: str,
    keyword: str = Query(...),
    current_user=Depends(
        require_role(
            ROLE_ADMIN,
            ROLE_ANALYST,
            ROLE_AUDITOR
        )
    )
):
    """
    Search controls within a framework.
    """

    framework_files = {
        "owasp-asvs": "frameworks/owasp_asvs.json",
        "nist-csf": "frameworks/nist_csf.json",
        "iso27001": "frameworks/iso27001.json",
        "cis": "frameworks/cis_controls.json"
    }

    print(f"Framework requested: {framework_name}")

    if framework_name not in framework_files:

        return {
            "message": "Framework not found",
            "available_frameworks": list(
                framework_files.keys()
            )
        }

    controls = load_framework(
    framework_files[
        framework_name
    ]
)

    results = []

    for control in controls:

        if (
            keyword.lower()
            in control["name"].lower()
            or
            keyword.lower()
            in control["description"].lower()
        ):

            results.append(
                control
            )

    return results