"""
CyberRisk360

Purpose:
Risk scoring engine.
"""
from app.core.constants import *

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
        return RISK_LEVEL_CRITICAL

    if score >= 15:
        return RISK_LEVEL_HIGH

    if score >= 10:
        return RISK_LEVEL_MEDIUM

    return RISK_LEVEL_LOW