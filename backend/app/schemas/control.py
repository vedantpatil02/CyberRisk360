"""
CyberRisk360

Purpose:
Schema used for creating
security controls.
"""

from pydantic import BaseModel


class ControlCreate(BaseModel):
    """
    Control creation schema.
    """

    control_id: str

    title: str

    description: str

    category_id: int