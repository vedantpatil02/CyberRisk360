"""
CyberRisk360

Purpose:
Shared schema types for the reporting API.
"""

from enum import Enum


class ReportFormat(str, Enum):
    """
    Output format for a generated report.
    """

    JSON = "json"
    HTML = "html"
    PDF = "pdf"
