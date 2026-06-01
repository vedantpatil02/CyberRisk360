"""
CyberRisk360

Purpose:
Schema used when creating a new risk.
"""

from pydantic import BaseModel


class RiskCreate(BaseModel):

    title: str

    description: str

    asset_id: int

    impact: int

    likelihood: int

    owner: str