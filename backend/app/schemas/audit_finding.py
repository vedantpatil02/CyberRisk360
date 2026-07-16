"""
CyberRisk360

Purpose:
Schemas for audit finding create/update requests.
"""

from typing import Optional

from pydantic import BaseModel


class AuditFindingCreate(BaseModel):

    title: str

    description: Optional[str] = None

    control_id: Optional[int] = None

    severity: str = "Medium"


class AuditFindingUpdate(BaseModel):
    """
    All fields optional - callers update only specific attributes.
    """

    title: Optional[str] = None

    description: Optional[str] = None

    severity: Optional[str] = None

    status: Optional[str] = None
