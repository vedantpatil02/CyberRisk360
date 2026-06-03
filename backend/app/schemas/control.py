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

    name: str

    description: str

    framework: str