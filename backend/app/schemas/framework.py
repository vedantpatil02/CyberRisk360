"""
CyberRisk360

Purpose:
Schemas for compliance framework management.
"""

from typing import Optional

from pydantic import BaseModel


class FrameworkCreate(BaseModel):
    """
    Framework creation schema.
    """

    name: str

    short_name: str

    version: str

    publisher: str

    description: Optional[str] = None

    release_year: Optional[int] = None


class FrameworkUpdate(BaseModel):
    """
    Framework update schema.

    All fields are optional because users may
    update only specific attributes.
    """

    name: Optional[str] = None

    version: Optional[str] = None

    publisher: Optional[str] = None

    description: Optional[str] = None

    release_year: Optional[int] = None
