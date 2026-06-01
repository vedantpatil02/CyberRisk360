"""
CyberRisk360

Purpose:
Risk scoring engine.
"""


def calculate_risk_score(
    impact: int,
    likelihood: int
):
    """
    Calculate risk score.

    Formula:
    Risk Score = Impact × Likelihood

    Example:
    Impact = 5
    Likelihood = 5

    Result = 25
    """

    return impact * likelihood


def calculate_risk_level(
    score: int
):
    """
    Convert numerical score into
    qualitative risk level.
    """

    if score >= 20:
        return "Critical"

    if score >= 15:
        return "High"

    if score >= 10:
        return "Medium"

    return "Low"