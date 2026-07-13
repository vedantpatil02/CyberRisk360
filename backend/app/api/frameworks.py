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
    load_framework,
    discover_frameworks
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

from app.schemas.framework import (
    FrameworkCreate,
    FrameworkUpdate
)

from app.services.frameworks.framework_service import (
    list_frameworks as service_list_frameworks,
    get_framework_detail,
    create_framework as service_create_framework,
    update_framework as service_update_framework,
    delete_framework as service_delete_framework
)

router = APIRouter()

@router.get(
    "/frameworks"
)
def list_frameworks(
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
    Retrieve all compliance frameworks.
    """

    return service_list_frameworks(db)


@router.get(
    "/frameworks/{framework_id}"
)
def get_framework(
    framework_id: int,
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
    Retrieve a single compliance framework.
    """

    framework = get_framework_detail(db, framework_id)

    if not framework:
        raise HTTPException(
            status_code=404,
            detail="Framework not found"
        )

    return framework


@router.post(
    "/frameworks"
)
def create_framework(
    framework: FrameworkCreate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN
        )
    )
):
    """
    Create a compliance framework.
    """

    created = service_create_framework(db, framework)

    if not created:
        raise HTTPException(
            status_code=409,
            detail="Framework with this short_name already exists"
        )

    return created


@router.patch(
    "/frameworks/{framework_id}"
)
def update_framework(
    framework_id: int,
    framework_update: FrameworkUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN
        )
    )
):
    """
    Update a compliance framework.
    """

    updates = framework_update.model_dump(exclude_unset=True)

    updated = service_update_framework(db, framework_id, updates)

    if not updated:
        raise HTTPException(
            status_code=404,
            detail="Framework not found"
        )

    return updated


@router.delete(
    "/frameworks/{framework_id}"
)
def delete_framework(
    framework_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(
        require_role(
            ROLE_ADMIN
        )
    )
):
    """
    Delete a compliance framework.
    """

    deleted = service_delete_framework(db, framework_id)

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail="Framework not found"
        )

    return {
        "message": "Framework deleted"
    }


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

    available_frameworks = discover_frameworks(
        FRAMEWORKS_DIR
    )

    if (
        framework_name
        not in
        available_frameworks
    ):
        raise HTTPException(
            status_code=404,
            detail="Framework not found"
        )

    controls = load_framework(
        available_frameworks[
            framework_name
        ]["framework_path"]
    )

    metadata = load_framework(
        available_frameworks[
            framework_name
        ]["metadata_path"]
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

    available_frameworks = discover_frameworks(
        FRAMEWORKS_DIR
    )

    if framework_name not in available_frameworks:

        raise HTTPException(
            status_code=404,
            detail={
                "message": "Framework not found",
                "available_frameworks": list(
                    available_frameworks.keys()
                )
            }
        )

    controls = load_framework(
        available_frameworks[
            framework_name
        ]["framework_path"]
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