"""
CyberRisk360

Purpose:
Executive GRC dashboard
aggregating compliance,
gaps, and risk analysis.
"""

from app.analytics.compliance import (
    calculate_compliance_summary
)

from app.analytics.gap_analysis import (
    get_framework_gaps
)

from app.analytics.control_risk_analysis import (
    get_control_risk_analysis
)

from app.repositories.controls.control_repository import (
    get_controls_by_framework
)

def get_grc_dashboard(
    db,
    framework_name: str,
    org_id=None
):
    """
    Return executive GRC dashboard for the organization scope.

    Note: control implementation status (implemented/partial/missing) is
    global today because controls are shared reference data; the gap and
    risk views below are org-scoped via the org's mappings.
    """

    controls = get_controls_by_framework(db, framework_name)

    summary = (
        calculate_compliance_summary(
            controls
        )
    )

    gaps = (
        get_framework_gaps(
            db,
            framework_name,
            org_id=org_id
        )
    )

    risk_analysis = (
        get_control_risk_analysis(
            db,
            framework_name,
            org_id=org_id
        )
    )

    top_risky_controls = sorted(
        risk_analysis["controls"],
        key=lambda control:
            control["risk_score"],
        reverse=True
    )[:5]

    overall_risk_score = sum(
        control["risk_score"]
        for control in
        risk_analysis["controls"]
    )

    return {
        "framework":
            framework_name,

        "compliance_score":
            summary["compliance_score"],

        "total_controls":
            summary["total_controls"],

        "implemented_controls":
            summary["implemented"],

        "partial_controls":
            summary["partial"],

        "missing_controls":
            summary["missing"],

        "overall_risk_score":
            overall_risk_score,

        "top_risky_controls":
            top_risky_controls,

        "gap_summary": {
            "affected_controls":
                len(
                    gaps["affected_controls"]
                ),

            "unaffected_controls":
                len(
                    gaps["unaffected_controls"]
                )
        }
    }