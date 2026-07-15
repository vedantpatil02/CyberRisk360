"""
CyberRisk360

Purpose:
Schema used when creating a new risk.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class RiskCreate(BaseModel):

    title: str

    description: str

    asset_id: int

    impact: int

    likelihood: int

    owner: str

    assignee_id: Optional[int] = None

    due_date: Optional[datetime] = None