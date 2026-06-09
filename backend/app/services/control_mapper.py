"""
CyberRisk360

Purpose:
Automatically maps imported
vulnerabilities to compliance
controls based on vulnerability
characteristics.
"""

from app.models.control import Control
from app.models.vulnerability_control_mapping import (
    VulnerabilityControlMapping
)


def map_controls(
    db,
    vulnerability
):
    """
    Automatically create
    control mappings for
    imported vulnerabilities.
    """

    # Normalize title for matching
    title = (
        vulnerability.title.lower()
    )

    control_codes = []

    # OpenSSH vulnerabilities
    # relate to vulnerability
    # management controls
    if "openssh" in title:

        control_codes.extend(
            [
                "RA-5",
                "SI-2"
            ]
        )

    # Weak cipher findings
    # relate to secure
    # configuration controls
    if "cipher" in title:

        control_codes.append(
            "CM-6"
        )

    # Create mappings
    for code in control_codes:

        control = (
            db.query(Control)
            .filter(
                Control.control_id
                == code
            )
            .first()
        )

        if not control:
            continue

        mapping = (
            VulnerabilityControlMapping(
                vulnerability_id=
                    vulnerability.id,

                control_id=
                    control.id
            )
        )

        db.add(mapping)