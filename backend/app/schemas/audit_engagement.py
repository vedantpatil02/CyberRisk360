"""
CyberRisk360

Purpose:
Schemas for audit engagement (Audit model) create/update requests.

Named audit_engagement.py, not audit.py, to avoid collision with the
existing schemas/audit.py (AuditLogOut - the unrelated generic
activity-log response schema).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AuditCreate(BaseModel):

    title: str

    framework_id: Optional[int] = None

    lead_auditor_id: Optional[int] = None

    scope: Optional[str] = None

    start_date: Optional[datetime] = None

    end_date: Optional[datetime] = None


class AuditUpdate(BaseModel):
    """
    All fields optional - callers update only specific attributes.
    """

    title: Optional[str] = None

    framework_id: Optional[int] = None

    lead_auditor_id: Optional[int] = None

    scope: Optional[str] = None

    status: Optional[str] = None

    start_date: Optional[datetime] = None

    end_date: Optional[datetime] = None
