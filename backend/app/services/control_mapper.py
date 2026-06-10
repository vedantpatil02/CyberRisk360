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
    if "openssh" in title:

        control_codes.extend(
            [
                "ID.RA-1",
                "PR.AC-1",
                "PR.DS-1"
            ]
        )

    # Weak cipher findings
    if "cipher" in title:

        control_codes.extend(
            [
                "PR.DS-1",
                "PR.IP-1"
            ]
        )

    # Weak key exchange
    if (
        "key exchange" in title
        or
        "weak key" in title
    ):

        control_codes.extend(
            [
                "PR.AC-3",
                "PR.DS-1"
            ]
        )

    # SSH configuration issues
    if "ssh" in title:

        control_codes.extend(
            [
                "PR.IP-1",
                "DE.CM-1"
            ]
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

        existing = (
            db.query(
                VulnerabilityControlMapping
            )
            .filter(
                VulnerabilityControlMapping.vulnerability_id
                == vulnerability.id,

                VulnerabilityControlMapping.control_id
                == control.id
            )
            .first()
        )

        if existing:
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