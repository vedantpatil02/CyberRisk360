"""
CyberRisk360

Purpose:
Application-wide constants.
"""

from pathlib import Path

# User Roles
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"
ROLE_AUDITOR = "auditor"


# Risk Statuses
RISK_STATUS_OPEN = "Open"
RISK_STATUS_UNDER_REVIEW = "Under Review"
RISK_STATUS_MITIGATED = "Mitigated"
RISK_STATUS_ACCEPTED = "Accepted"
RISK_STATUS_CLOSED = "Closed"

RISK_LEVEL_LOW = "Low"
RISK_LEVEL_MEDIUM = "Medium"
RISK_LEVEL_HIGH = "High"
RISK_LEVEL_CRITICAL = "Critical"

SUMMARY_OPEN = "open"
SUMMARY_CLOSED = "closed"



VULNERABILITY_STATUS_OPEN = "Open"
VULNERABILITY_STATUS_CLOSED = "Closed"
VULNERABILITY_STATUS_IN_PROGRESS = "In Progress"
VULNERABILITY_STATUS_VERIFIED = "Verified"

SUMMARY_CRITICAL = "critical"
SUMMARY_HIGH = "high"
SUMMARY_MEDIUM = "medium"
SUMMARY_LOW = "low"

CONTROL_STATUS_IMPLEMENTED = "Implemented"
CONTROL_STATUS_PARTIAL = "Partially Implemented"
CONTROL_STATUS_MISSING = "Missing"

FRAMEWORK_ISO27001 = "iso27001"
FRAMEWORK_NIST_CSF = "nist-csf"
FRAMEWORK_OWASP_ASVS = "owasp-asvs"
FRAMEWORK_CIS = "cis"

# backend/app/core/constants.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
FRAMEWORKS_DIR = BACKEND_DIR / "frameworks"

FRAMEWORK_VERSION_DIRS = {
    "owasp-asvs": FRAMEWORKS_DIR / "owasp-asvs" / "v4.0.3",
    "nist-csf": FRAMEWORKS_DIR / "nist-csf" / "v2.0",
    "iso27001": FRAMEWORKS_DIR / "iso27001" / "2022",
    "cis": FRAMEWORKS_DIR / "cis-controls" / "v8",
}

FRAMEWORK_FILES = {
    key: str(path / "framework.json")
    for key, path in FRAMEWORK_VERSION_DIRS.items()
}

FRAMEWORK_METADATA_FILES = {
    key: str(path / "metadata.json")
    for key, path in FRAMEWORK_VERSION_DIRS.items()
}

UPLOAD_DIR = "uploads"