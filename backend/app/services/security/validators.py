"""
CyberRisk360

Purpose:
Input validation helpers.
"""


def validate_cvss_score(
    score: float
):
    """
    Validate CVSS score.

    Valid Range:
    0.0 - 10.0
    """

    return 0 <= score <= 10