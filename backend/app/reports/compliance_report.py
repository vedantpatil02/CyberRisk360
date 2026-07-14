"""
CyberRisk360

Purpose:
Compliance Assessment report - a per-framework audit-readiness view
combining compliance posture, control gaps, and control risk.
"""

from app.repositories.frameworks.framework_repository import (
    get_framework_by_short_name
)
from app.repositories.controls.control_repository import (
    get_controls_by_framework
)

from app.analytics.compliance import (
    calculate_compliance_summary
)
from app.analytics.gap_analysis import (
    get_framework_gaps
)
from app.analytics.control_risk_analysis import (
    get_control_risk_analysis
)

from app.reports.common import build_envelope


class FrameworkNotFound(Exception):
    """
    Raised when a compliance report is requested for a framework
    short_name that does not exist. The API layer maps this to a 404.
    """


def build_compliance_report(db, framework_name: str, generated_by=None, org_id=None):
    """
    Build the structured Compliance Assessment report for one framework,
    scoped to `org_id` (None = all orgs). Gap and control-risk views use
    the org's mappings; control implementation status is global.
    """

    framework = get_framework_by_short_name(db, framework_name)

    if framework is None:
        raise FrameworkNotFound(framework_name)

    controls = get_controls_by_framework(db, framework_name)

    summary = calculate_compliance_summary(controls)
    gaps = get_framework_gaps(db, framework_name, org_id=org_id)
    risk_analysis = get_control_risk_analysis(db, framework_name, org_id=org_id)

    report = build_envelope(
        report_type="Compliance Assessment Report",
        title=f"Compliance Assessment - {framework.name}",
        generated_by=generated_by
    )

    report["sections"] = {
        "framework": {
            "name": framework.name,
            "short_name": framework.short_name,
            "version": framework.version,
        },
        "compliance_summary": summary,
        "gaps": {
            "total_controls": gaps["total_controls"],
            "affected_controls": gaps["affected_controls"],
            "unaffected_controls": gaps["unaffected_controls"],
        },
        "control_risk": risk_analysis["controls"],
    }

    return report
