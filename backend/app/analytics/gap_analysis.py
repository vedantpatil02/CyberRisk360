"""
CyberRisk360

Purpose:
Generate framework gap analysis.
"""

from app.repositories.controls.control_repository import (
    get_controls_by_framework
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    count_by_control
)


def get_framework_gaps(
    db,
    framework_name: str
):
    """
    Return affected and
    unaffected controls.
    """

    controls = get_controls_by_framework(db, framework_name)

    affected_controls = []
    unaffected_controls = []

    for control in controls:

        mapping_count = count_by_control(db, control.id)

        control_data = {
            "control_id":
                control.control_id,

            "name":
                control.title,

            "affected_vulnerabilities":
                mapping_count
        }

        if mapping_count > 0:

            affected_controls.append(
                control_data
            )

        else:

            unaffected_controls.append(
                control_data
            )

    return {
        "framework":
            framework_name,

        "total_controls":
            len(controls),

        "affected_controls":
            affected_controls,

        "unaffected_controls":
            unaffected_controls
    }
