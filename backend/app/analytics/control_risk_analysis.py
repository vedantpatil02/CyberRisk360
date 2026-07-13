"""
CyberRisk360

Purpose:
Calculate risk scores for
compliance controls.
"""

from app.repositories.controls.control_repository import (
    get_controls_by_framework
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    get_by_control
)
from app.repositories.vulnerabilities.vulnerability_repository import (
    get_vulnerability
)


def get_control_risk_analysis(
    db,
    framework_name: str
):
    """
    Return risk scores for
    controls within a framework.
    """

    controls = get_controls_by_framework(db, framework_name)

    results = []

    for control in controls:

        mappings = get_by_control(db, control.id)

        critical = 0
        high = 0
        medium = 0
        low = 0

        for mapping in mappings:

            vulnerability = get_vulnerability(
                db,
                mapping.vulnerability_id
            )

            if not vulnerability:
                continue

            severity = (
                vulnerability.severity
                .upper()
            )

            if severity == "CRITICAL":
                critical += 1

            elif severity == "HIGH":
                high += 1

            elif severity == "MEDIUM":
                medium += 1

            elif severity == "LOW":
                low += 1

        risk_score = (
            critical * 10
            + high * 7
            + medium * 4
            + low * 1
        )

        results.append(
            {
                "control_id":
                    control.control_id,

                "name":
                    control.title,

                "affected_vulnerabilities":
                    len(mappings),

                "critical":
                    critical,

                "high":
                    high,

                "medium":
                    medium,

                "low":
                    low,

                "risk_score":
                    risk_score
            }
        )

    results.sort(
        key=lambda x:
            x["risk_score"],
        reverse=True
    )

    return {
        "framework":
            framework_name,

        "controls":
            results
    }
