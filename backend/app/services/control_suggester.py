"""
CyberRisk360

Purpose:
Suggest controls based on
vulnerability characteristics.
"""


def suggest_controls(
    vulnerability_title: str
):
    """
    Return suggested controls
    based on vulnerability title.
    """

    title = vulnerability_title.lower()

    suggestions = []

    if "sql injection" in title:

        suggestions.append(
            "Input Validation"
        )

    if "xss" in title:

        suggestions.append(
            "Output Encoding"
        )

    if "password" in title:

        suggestions.append(
            "Authentication"
        )

    if "csrf" in title:

        suggestions.append(
            "Session Protection"
        )

    return suggestions