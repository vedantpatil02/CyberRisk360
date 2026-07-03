"""
CyberRisk360

Purpose:
Suggest controls based on
vulnerability titles.
"""

CONTROL_MAPPINGS = {

    "sql injection": [
        "Input Validation"
    ],

    "xss": [
        "Output Encoding"
    ],

    "csrf": [
        "Session Protection"
    ],

    "password": [
        "Authentication"
    ],

    "tls": [
        "Data Protection"
    ],

    "encryption": [
        "Data Protection"
    ],

    "account": [
        "Account Management"
    ]
}


def suggest_control_names(
    vulnerability_title: str
):
    """
    Return matching control names.
    """

    title = vulnerability_title.lower()

    suggestions = []

    for keyword, controls in (
        CONTROL_MAPPINGS.items()
    ):

        if keyword in title:

            suggestions.extend(
                controls
            )

    return suggestions