"""
CyberRisk360

Purpose:
Convert CVSS scores into severity ratings.
"""


def calculate_severity(
    cvss_score: float
):
    """
    Convert CVSS score into severity.

    CVSS v3.1 Reference:

    0.1 - 3.9  = Low
    4.0 - 6.9  = Medium
    7.0 - 8.9  = High
    9.0 - 10.0 = Critical
    """

    if cvss_score >= 9.0:
        return "Critical"

    if cvss_score >= 7.0:
        return "High"

    if cvss_score >= 4.0:
        return "Medium"

    return "Low"