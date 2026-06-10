"""
CyberRisk360

Purpose:
Generate compliance dashboard
statistics.
"""


from app.core.constants import (
    CONTROL_STATUS_IMPLEMENTED,
    CONTROL_STATUS_PARTIAL,
    CONTROL_STATUS_MISSING
)


def initialize_compliance_summary():
    """
    Initialize compliance counters.
    """

    return {
        "total_controls": 0,
        "implemented": 0,
        "partial": 0,
        "missing": 0,
        "compliance_score": 0.0
    }


def calculate_compliance_summary(
    controls
):
    """
    Calculate compliance metrics.
    """

    summary = (
        initialize_compliance_summary()
    )

    summary["total_controls"] = (
        len(controls)
    )

    for control in controls:

        if (
            control.status
            ==
            CONTROL_STATUS_IMPLEMENTED
        ):

            summary["implemented"] += 1

        elif (
            control.status
            ==
            CONTROL_STATUS_PARTIAL
        ):

            summary["partial"] += 1

        elif (
            control.status
            ==
            CONTROL_STATUS_MISSING
        ):

            summary["missing"] += 1

    if summary["total_controls"] > 0:

        summary["compliance_score"] = round(
            (
                summary["implemented"]
                /
                summary["total_controls"]
            )
            * 100,
            2
        )

    return summary