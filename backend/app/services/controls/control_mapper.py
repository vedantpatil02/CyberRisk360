"""
CyberRisk360

Purpose:
Automatically maps imported
vulnerabilities to compliance
controls based on vulnerability
characteristics.
"""

from app.repositories.controls.control_repository import (
    get_control_by_code
)
from app.repositories.vulnerability_control_mappings.mapping_repository import (
    mapping_exists,
    create_mapping
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

        control = get_control_by_code(db, code)

        if not control:
            continue

        if mapping_exists(db, vulnerability.id, control.id):
            continue

        create_mapping(db, vulnerability.id, control.id)