"""
CyberRisk360

Purpose:
Schema used to map risks
to controls.
"""

from pydantic import BaseModel


class RiskControlMappingCreate(
    BaseModel
):
    risk_id: int

    control_id: int
    