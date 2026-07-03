"""
CyberRisk360

Purpose:
Generate framework gap analysis.
"""

from app.models.control import Control
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
)


def get_framework_gaps(
    db,
    framework_name: str
):
    """
    Return affected and
    unaffected controls.
    """

    controls = (
        db.query(Control)
        .filter(
            Control.framework
            == framework_name
        )
        .all()
    )

    affected_controls = []
    unaffected_controls = []

    for control in controls:

        mapping_count = (
            db.query(
                VulnerabilityControlMapping
            )
            .filter(
                VulnerabilityControlMapping.control_id
                == control.id
            )
            .count()
        )

        control_data = {
            "control_id":
                control.control_id,

            "name":
                control.name,

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