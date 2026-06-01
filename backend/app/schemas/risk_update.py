"""
CyberRisk360

Purpose:
Schema used when updating an existing risk.

Unlike RiskCreate, all fields are optional
because users may update only specific
attributes of a risk.
"""

from typing import Optional

from pydantic import BaseModel


class RiskUpdate(BaseModel):
    """
    Risk update request schema.
    """

    # Updated risk title
    title: Optional[str] = None

    # Updated description
    description: Optional[str] = None

    # Updated impact score (1-5)
    impact: Optional[int] = None

    # Updated likelihood score (1-5)
    likelihood: Optional[int] = None

    # Updated risk owner
    owner: Optional[str] = None

    # Updated risk status
    status: Optional[str] = None