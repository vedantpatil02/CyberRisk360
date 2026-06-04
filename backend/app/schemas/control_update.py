"""
CyberRisk360

Purpose:
Update control status.
"""

from pydantic import BaseModel


class ControlUpdate(
    BaseModel
):
    status: str