"""
CyberRisk360

Purpose:
Expose compliance framework data.
"""

from fastapi import (
    APIRouter,
    Depends,
    Query,
    HTTPException
)

from app.dependencies.rbac import (
    require_role
)

from app.core.constants import *

from app.services.frameworks.framework_loader import (
    load_framework
)

from sqlalchemy.orm import Session

from app.dependencies.database import (
    get_db
)

from app.services.frameworks.framework_importer import (
    import_framework
)

from app.analytics.gap_analysis import (
    get_framework_gaps
)

from app.analytics.control_risk_analysis import (
    get_control_risk_analysis
)

router = APIRouter()

@router.post(
    "/frameworks/import/{framework_name}"
)
def import_framework_controls(
    framework_name: str,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN
        )
    )
):
    """
    Import framework controls
    into database.
    """

    if (
        framework_name
        not in
        FRAMEWORK_FILES
    ):
        raise HTTPException(
            status_code=404,
            detail="Framework not found"
        )

    controls = load_framework(
        FRAMEWORK_FILES[
            framework_name
        ]
    )

    metadata = load_framework(
        FRAMEWORK_METADATA_FILES[
            framework_name
        ]
    )

    imported_count = (
        import_framework(
            metadata,
            controls,
            db
        )
    )

    return {
        "message":
        "Framework imported",
        "controls_imported":
        imported_count
    }


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

    if framework_name not in FRAMEWORK_FILES:

        return {
            "message": "Framework not found",
            "available_frameworks": list(
                FRAMEWORK_FILES.keys()
            )
        }

    controls = load_framework(
    FRAMEWORK_FILES[
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

@router.get(
    "/frameworks/{framework_name}/gaps"
)
def framework_gap_analysis(
    framework_name: str,
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
    Return framework gap analysis.
    """

    return get_framework_gaps(
        db,
        framework_name
    )

@router.get(
    "/frameworks/{framework_name}/risk-analysis"
)
def framework_risk_analysis(
    framework_name: str,
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
    Return control risk analysis.
    """

    return get_control_risk_analysis(
        db,
        framework_name
    )