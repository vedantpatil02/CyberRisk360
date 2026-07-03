"""
CyberRisk360

Purpose:
Calculate risk scores for
compliance controls.
"""

from app.models.control import Control
from app.models.vulnerability import (
    Vulnerability
)
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
)


def get_control_risk_analysis(
    db,
    framework_name: str
):
    """
    Return risk scores for
    controls within a framework.
    """

    controls = (
        db.query(Control)
        .filter(
            Control.framework
            == framework_name
        )
        .all()
    )

    results = []

    for control in controls:

        mappings = (
            db.query(
                VulnerabilityControlMapping
            )
            .filter(
                VulnerabilityControlMapping.control_id
                == control.id
            )
            .all()
        )

        critical = 0
        high = 0
        medium = 0
        low = 0

        for mapping in mappings:

            vulnerability = (
                db.query(Vulnerability)
                .filter(
                    Vulnerability.id
                    ==
                    mapping.vulnerability_id
                )
                .first()
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
                    control.name,

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