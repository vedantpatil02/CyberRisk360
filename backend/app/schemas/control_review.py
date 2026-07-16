"""
CyberRisk360

Purpose:
Schema for submitting a control implementation-status review.
Reviewer identity comes from the authenticated user, not the request
body - same convention as schemas/mapping_review.py.
"""

from typing import Optional

from pydantic import BaseModel


class ControlReviewCreate(BaseModel):

    new_status: str

    notes: Optional[str] = None
