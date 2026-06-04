"""
CyberRisk360

Purpose:
Response schema for Nessus imports.
"""

from pydantic import BaseModel


class NessusImportResponse(
    BaseModel
):
    imported: int

    skipped: int

    failed: int