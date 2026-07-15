"""
CyberRisk360

Purpose:
Import framework controls
from JSON files.
"""

import re

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

# Matches everything before the final "." or "-" delimited segment
# of a control_id, e.g. "PR.AC-3" -> "PR.AC", "A.5.1" -> "A.5".
_CATEGORY_CODE_PATTERN = re.compile(r"^(.*)[.\-][^.\-]+$")


def _derive_category_code(
    control_id: str
) -> str:
    """
    Best-effort, framework-agnostic category code derived from a
    control_id's structure. Falls back to the full control_id when
    it has no delimiter (e.g. "V5"), so the control still lands in
    its own category rather than a catch-all bucket.
    """

    match = _CATEGORY_CODE_PATTERN.match(control_id)

    return match.group(1) if match else control_id


def import_framework(
    metadata: dict,
    controls: list,
    db
):
    """
    Import a framework's metadata and its controls, deriving
    categories from each control_id's structure and skipping
    controls that already exist.
    """

    framework = get_or_create_framework(
        db,
        metadata
    )

    imported_count = 0

    for control in controls:

        existing_control = get_control_by_code(
            db,
            control["control_id"]
        )

        if existing_control:
            continue

        category_code = _derive_category_code(
            control["control_id"]
        )

        category = get_or_create_category(
            db,
            framework.id,
            category_code,
            category_code
        )

        control_fields = {
            "control_id": control["control_id"],
            "title": control["name"],
            "description": control["description"],
            "category_id": category.id,
            "status": CONTROL_STATUS_MISSING
        }

        # Optional, source-provided metadata (e.g. ASVS's official
        # Level column, NIST's official Implementation Examples).
        # Only set when the source JSON actually provides them, so
        # frameworks that don't (e.g. the still-placeholder CIS/ISO
        # data) keep relying on the model's own defaults rather than
        # having them overridden with an explicit None.
        if "priority" in control:
            control_fields["priority"] = control["priority"]

        if "implementation_guidance" in control:
            control_fields["implementation_guidance"] = (
                control["implementation_guidance"]
            )

        new_control = Control(**control_fields)

        db.add(
            new_control
        )

        imported_count += 1

    db.commit()

    return imported_count
