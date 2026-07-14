"""
CyberRisk360

Purpose:
Executive Summary report - a board-level view composing asset,
vulnerability, compliance, and risk analytics into one structured
document.
"""

from app.repositories.assets.asset_repository import (
    get_all_assets
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_all_vulnerabilities
)
from app.repositories.controls.control_repository import (
    get_all_controls,
    get_controls_by_framework
)
from app.repositories.frameworks.framework_repository import (
    get_all_frameworks
)

from app.analytics.compliance import (
    calculate_compliance_summary
)
from app.analytics.asset_risk import (
    get_asset_risk_summary
)
from app.analytics.control_risk_analysis import (
    get_control_risk_analysis
)

from app.reports.common import (
    build_envelope,
    severity_breakdown,
    status_breakdown
)


# How many rows the "top" tables in the executive summary show. The
# executive audience wants the headline offenders, not the full register
# (that's the technical report's job).
TOP_ASSETS = 5
TOP_CONTROLS = 5


def build_executive_report(db, generated_by=None):
    """
    Build the structured Executive Summary report.
    """

    assets = get_all_assets(db)
    vulnerabilities = get_all_vulnerabilities(db)
    controls = get_all_controls(db)

    severity = severity_breakdown(vulnerabilities)
    status = status_breakdown(vulnerabilities)

    asset_risks = get_asset_risk_summary(db)
    top_assets = asset_risks[:TOP_ASSETS]

    frameworks = get_all_frameworks(db)

    framework_compliance = []
    overall_control_risk = 0
    top_controls = []

    for framework in frameworks:

        framework_controls = get_controls_by_framework(
            db, framework.short_name
        )

        summary = calculate_compliance_summary(
            framework_controls
        )

        framework_compliance.append(
            {
                "framework": framework.name,
                "short_name": framework.short_name,
                "version": framework.version,
                **summary,
            }
        )

        risk_analysis = get_control_risk_analysis(
            db, framework.short_name
        )

        for control in risk_analysis["controls"]:
            overall_control_risk += control["risk_score"]
            top_controls.append(
                {
                    "framework": framework.short_name,
                    **control,
                }
            )

    top_controls.sort(
        key=lambda control: control["risk_score"],
        reverse=True
    )

    report = build_envelope(
        report_type="Executive Summary",
        title="Cyber Risk Executive Summary",
        generated_by=generated_by
    )

    report["sections"] = {
        "overview": {
            "total_assets": len(assets),
            "total_vulnerabilities": len(vulnerabilities),
            "total_controls": len(controls),
            "overall_control_risk_score": overall_control_risk,
        },
        "vulnerabilities": {
            "by_severity": severity,
            "by_status": status,
        },
        "top_risk_assets": top_assets,
        "framework_compliance": framework_compliance,
        "top_risk_controls": top_controls[:TOP_CONTROLS],
    }

    return report
