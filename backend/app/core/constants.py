"""
CyberRisk360

Purpose:
Application-wide constants.
"""

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

RISK_STATUS_OPEN = "Open"
RISK_STATUS_CLOSED = "Closed"


VULNERABILITY_STATUS_OPEN = "Open"
VULNERABILITY_STATUS_CLOSED = "Closed"
VULNERABILITY_STATUS_IN_PROGRESS = "In Progress"
VULNERABILITY_STATUS_VERIFIED = "Verified"
VULNERABILITY_STATUS_CLOSED = "Closed"

SUMMARY_CRITICAL = "critical"
SUMMARY_HIGH = "high"
SUMMARY_MEDIUM = "medium"
SUMMARY_LOW = "low"

CONTROL_STATUS_IMPLEMENTED = "Implemented"
CONTROL_STATUS_PARTIAL = "Partially Implemented"
CONTROL_STATUS_MISSING = "Missing"

FRAMEWORK_ISO27001 = "ISO27001"
FRAMEWORK_NIST_CSF = "NIST-CSF"
FRAMEWORK_OWASP_ASVS = "OWASP-ASVS"
FRAMEWORK_CIS = "CIS"

FRAMEWORK_FILES = {
    "owasp-asvs": "frameworks/owasp_asvs.json",
    "nist-csf": "frameworks/nist_csf.json",
    "iso27001": "frameworks/iso27001.json",
    "cis": "frameworks/cis_controls.json"
}

