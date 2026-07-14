"""
CyberRisk360

Purpose:
Schemas for the organization (tenant) management API.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class OrganizationCreate(BaseModel):
    name: str = Field(min_length=1)
    slug: str = Field(min_length=1, pattern="^[a-z0-9][a-z0-9-]*$")


class OrganizationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    slug: str
    created_at: Optional[datetime] = None
