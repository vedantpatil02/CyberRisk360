"""
CyberRisk360

Purpose:
Schema used when approving or rejecting a vulnerability-control
mapping. Reviewer identity comes from the authenticated user, not
the request body.
"""

from typing import Optional

from pydantic import BaseModel


class MappingReview(BaseModel):

    note: Optional[str] = None
