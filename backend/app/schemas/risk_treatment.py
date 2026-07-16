"""
CyberRisk360

Purpose:
Schemas for the Risk Treatment + Approval workflow. Reviewer identity
comes from the authenticated user, not the request body - same
convention as schemas/mapping_review.py.
"""

from typing import Optional

from pydantic import BaseModel
from pydantic import field_validator

from app.core.constants import RISK_TREATMENT_STATUS_BY_TYPE


class RiskTreatmentPropose(BaseModel):

    treatment_type: str

    justification: str

    @field_validator("treatment_type")
    @classmethod
    def validate_treatment_type(cls, value: str) -> str:
        if value not in RISK_TREATMENT_STATUS_BY_TYPE:
            allowed = ", ".join(sorted(RISK_TREATMENT_STATUS_BY_TYPE))
            raise ValueError(f"treatment_type must be one of: {allowed}")
        return value


class RiskTreatmentReview(BaseModel):

    note: Optional[str] = None
