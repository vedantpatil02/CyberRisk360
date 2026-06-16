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

    CONTROL_RULES = {

        "ssh": [
            "PR.AC-1",
            "PR.AC-3",
            "PR.DS-1"
        ],

        "cipher": [
            "PR.DS-1",
            "PR.IP-1"
        ],

        "tls": [
            "PR.DS-1"
        ],

        "ssl": [
            "PR.DS-1"
        ],

        "password": [
            "PR.AC-1"
        ],

        "authentication": [
            "PR.AC-1"
        ],

        "account": [
            "PR.AC-1"
        ],

        "remote": [
            "PR.AC-3"
        ],

        "configuration": [
            "PR.IP-1"
        ],

        "vulnerability": [
            "ID.RA-1"
        ]
    }

    
    for keyword, controls in (
    CONTROL_RULES.items()
    ):

        if keyword in title:

            control_codes.extend(
                controls
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