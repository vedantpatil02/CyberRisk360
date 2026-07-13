"""
CyberRisk360

Purpose:
Import framework controls
from JSON files.
"""

from app.models.control import (
    Control
)

from app.core.constants import (
    CONTROL_STATUS_MISSING
)

from app.repositories.frameworks.framework_repository import (
    get_or_create_framework
)

from app.repositories.categories.category_repository import (
    get_or_create_category
)

from app.repositories.controls.control_repository import (
    get_control_by_code
)


def import_framework(
    metadata: dict,
    controls: list,
    db
):
    """
    Import a framework's metadata, a default
    category, and its controls, skipping duplicates.
    """

    framework = get_or_create_framework(
        db,
        metadata
    )

    category = get_or_create_category(
        db,
        framework.id,
        "GENERAL",
        "General Controls"
    )

    imported_count = 0

    for control in controls:

        existing_control = get_control_by_code(
            db,
            control["control_id"]
        )

        if existing_control:
            continue

        new_control = Control(
            control_id=control["control_id"],
            title=control["name"],
            description=control["description"],
            category_id=category.id,
            status=CONTROL_STATUS_MISSING
        )

        db.add(
            new_control
        )

        imported_count += 1

    db.commit()

    return imported_count
