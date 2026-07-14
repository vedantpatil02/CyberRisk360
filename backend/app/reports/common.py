"""
CyberRisk360

Purpose:
Shared helpers for report builders - a common report "envelope"
(metadata wrapper) and vulnerability aggregation used by more than one
report type.
"""

from datetime import datetime, timezone


def build_envelope(
    report_type: str,
    title: str,
    generated_by=None
):
    """
    Return the metadata wrapper every report shares.

    Concrete builders attach their own `sections` payload to this.
    """

    return {
        "report_type": report_type,
        "title": title,
        "generated_at":
            datetime.now(timezone.utc).isoformat(),
        "generated_by":
            generated_by or "system",
    }


def severity_breakdown(vulnerabilities):
    """
    Count vulnerabilities by severity (case-insensitive).
    """

    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    for vulnerability in vulnerabilities:

        severity = (
            (vulnerability.severity or "")
            .lower()
        )

        if severity in counts:
            counts[severity] += 1

    return counts


def status_breakdown(vulnerabilities):
    """
    Count vulnerabilities by open/closed status.

    Anything not explicitly "Closed" is treated as open (an in-progress
    or verified finding is still an unresolved exposure).
    """

    counts = {
        "open": 0,
        "closed": 0,
    }

    for vulnerability in vulnerabilities:

        status = (
            (vulnerability.status or "")
            .lower()
        )

        if status == "closed":
            counts["closed"] += 1

        else:
            counts["open"] += 1

    return counts
