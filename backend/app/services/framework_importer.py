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


def import_framework(
    framework_name: str,
    controls: list,
    db
):
    """
    Import controls and skip duplicates.
    """

    imported_count = 0

    for control in controls:

        existing_control = (
            db.query(Control)
            .filter(
                Control.control_id == control["control_id"],
                Control.framework == framework_name
            )
            .first()
        )

        if existing_control:
            continue

        new_control = Control(
            control_id=control["control_id"],
            name=control["name"],
            description=control["description"],
            framework=framework_name,
            status=CONTROL_STATUS_MISSING
        )

        db.add(
            new_control
        )

        imported_count += 1

    db.commit()

    return imported_count
