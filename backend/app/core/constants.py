"""
CyberRisk360

Purpose:
Application-wide constants.
"""

from pathlib import Path

# Platform super-admin: spans all organizations. Provisioned out-of-band
# (bootstrap/seed), never via open registration, so it can't be
# self-assigned as a privilege escalation. Deliberately excluded from
# VALID_ROLES below.
ROLE_SUPER_ADMIN = "super_admin"

# User Roles - one operational admin role plus the six personas from the
# product design doc (§5). All of these are ORG-SCOPED.
ROLE_ADMIN = "admin"
ROLE_ANALYST = "analyst"          # Security Analyst
ROLE_PENTESTER = "pentester"      # Penetration Tester
ROLE_GRC_ANALYST = "grc_analyst"  # GRC Analyst
ROLE_AUDITOR = "auditor"          # Auditor
ROLE_MANAGER = "manager"          # Security Manager
ROLE_CISO = "ciso"               # CISO

# Every recognized role.
ALL_ROLES = (
    ROLE_ADMIN,
    ROLE_ANALYST,
    ROLE_PENTESTER,
    ROLE_GRC_ANALYST,
    ROLE_AUDITOR,
    ROLE_MANAGER,
    ROLE_CISO,
)

# Semantic role groups, used at endpoints instead of hard-coding role
# lists. Keeping the tiers here (rather than per-endpoint) is what lets a
# new persona be slotted in without editing every router.
#
# WRITE_ROLES     - may create/modify technical findings & inventory
# COMPLIANCE_ROLES- may manage controls/compliance state
# OVERSIGHT_ROLES - may read the audit trail
# READ_ROLES      - may view dashboards, reports, and read-only data
WRITE_ROLES = (ROLE_ADMIN, ROLE_ANALYST, ROLE_PENTESTER)
COMPLIANCE_ROLES = (ROLE_ADMIN, ROLE_ANALYST, ROLE_GRC_ANALYST)
OVERSIGHT_ROLES = (ROLE_ADMIN, ROLE_AUDITOR, ROLE_CISO, ROLE_MANAGER)
READ_ROLES = ALL_ROLES

# Account lockout (brute-force protection). After this many consecutive
# failed logins, the account is locked for the cooldown window; a
# successful login resets the counter.
MAX_FAILED_LOGIN_ATTEMPTS = 5
ACCOUNT_LOCKOUT_MINUTES = 15


# Risk Statuses
RISK_STATUS_OPEN = "Open"
RISK_STATUS_UNDER_REVIEW = "Under Review"
RISK_STATUS_MITIGATED = "Mitigated"
RISK_STATUS_ACCEPTED = "Accepted"
# Terminal outcomes of the "transfer"/"avoid" treatment types below -
# Mitigated/Accepted already existed as statuses (treatment predates this
# workflow); these two were missing since nothing previously recorded a
# transfer/avoid decision.
RISK_STATUS_TRANSFERRED = "Transferred"
RISK_STATUS_AVOIDED = "Avoided"
RISK_STATUS_CLOSED = "Closed"

# Risk Treatment Workflow: what was proposed. Approval drives
# Risk.status to the matching terminal value above (see
# app/services/risks/risk_treatment.py).
RISK_TREATMENT_MITIGATE = "mitigate"
RISK_TREATMENT_ACCEPT = "accept"
RISK_TREATMENT_TRANSFER = "transfer"
RISK_TREATMENT_AVOID = "avoid"

RISK_TREATMENT_STATUS_BY_TYPE = {
    RISK_TREATMENT_MITIGATE: RISK_STATUS_MITIGATED,
    RISK_TREATMENT_ACCEPT: RISK_STATUS_ACCEPTED,
    RISK_TREATMENT_TRANSFER: RISK_STATUS_TRANSFERRED,
    RISK_TREATMENT_AVOID: RISK_STATUS_AVOIDED,
}

RISK_APPROVAL_PENDING = "pending"
RISK_APPROVAL_APPROVED = "approved"
RISK_APPROVAL_REJECTED = "rejected"

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

# Vulnerability-Control Mapping Engine
MATCH_TYPE_CVE = "cve"
MATCH_TYPE_CWE = "cwe"
MATCH_TYPE_PLUGIN_ID = "plugin_id"
MATCH_TYPE_KEYWORD = "keyword"

# Confidence by match specificity: exact identifier matches (CVE,
# Plugin ID) score highest, CWE (a weakness class, not an exact
# instance) next, free-text keyword matches lowest.
MAPPING_CONFIDENCE_BY_MATCH_TYPE = {
    MATCH_TYPE_CVE: 0.95,
    MATCH_TYPE_PLUGIN_ID: 0.9,
    MATCH_TYPE_CWE: 0.85,
    MATCH_TYPE_KEYWORD: 0.5,
}

MAPPING_STATUS_PENDING = "pending"
MAPPING_STATUS_APPROVED = "approved"
MAPPING_STATUS_REJECTED = "rejected"

# Audit Management (GRC audit engagements) - distinct from the
# AuditLog/audit_logs activity trail.
AUDIT_STATUS_PLANNED = "Planned"
AUDIT_STATUS_IN_PROGRESS = "In Progress"
AUDIT_STATUS_COMPLETED = "Completed"
AUDIT_STATUS_CLOSED = "Closed"

AUDIT_FINDING_STATUS_OPEN = "Open"
AUDIT_FINDING_STATUS_REMEDIATED = "Remediated"
AUDIT_FINDING_STATUS_ACCEPTED = "Accepted"
AUDIT_FINDING_STATUS_CLOSED = "Closed"

import os

# backend/app/core/constants.py -> backend/
BACKEND_DIR = Path(__file__).resolve().parents[2]
FRAMEWORKS_DIR = BACKEND_DIR / "frameworks"

# Where uploaded scan reports are stored. Env-configurable so the path
# can point at a mounted volume in a container (and, as a stepping stone
# to object storage, live outside the app image). Defaults to
# backend/uploads for local dev.
UPLOAD_DIR = Path(
    os.environ.get("UPLOAD_DIR", str(BACKEND_DIR / "uploads"))
)