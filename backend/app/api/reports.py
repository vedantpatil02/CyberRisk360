"""
CyberRisk360

Purpose:
Reporting API - serves the Executive Summary, Technical Vulnerability,
and Compliance Assessment reports as JSON, HTML, or a downloadable PDF.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.responses import HTMLResponse
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.dependencies.rbac import require_role
from app.dependencies.tenancy import org_scope
from app.core.constants import READ_ROLES

from app.schemas.report import ReportFormat

from app.reports.executive_report import build_executive_report
from app.reports.technical_report import build_technical_report
from app.reports.compliance_report import (
    build_compliance_report,
    FrameworkNotFound
)
from app.reports.renderers import (
    render_html,
    render_pdf,
    ReportRenderError
)


router = APIRouter()


def _serialize(report: dict, report_format: ReportFormat):
    """
    Return the report in the requested format.

    JSON returns the structured dict directly; HTML and PDF go through
    the renderers. A rendering failure surfaces as a 500.
    """

    if report_format == ReportFormat.JSON:
        return report

    try:

        if report_format == ReportFormat.HTML:
            return HTMLResponse(content=render_html(report))

        pdf_bytes = render_pdf(report)

    except ReportRenderError as error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(error)
        )

    filename = (
        report["report_type"]
        .lower()
        .replace(" ", "_")
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
                f'attachment; filename="{filename}.pdf"'
        }
    )


@router.get("/reports/executive")
def executive_report(
    format: ReportFormat = ReportFormat.JSON,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(*READ_ROLES)
    )
):
    """
    Board-level Executive Summary across assets, vulnerabilities,
    compliance, and risk.
    """

    report = build_executive_report(
        db, generated_by=current_user.get("sub"), org_id=scope
    )

    return _serialize(report, format)


@router.get("/reports/technical")
def technical_report(
    format: ReportFormat = ReportFormat.JSON,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(*READ_ROLES)
    )
):
    """
    Full vulnerability register grouped by severity, for analysts.
    """

    report = build_technical_report(
        db, generated_by=current_user.get("sub"), org_id=scope
    )

    return _serialize(report, format)


@router.get("/reports/compliance/{framework_name}")
def compliance_report(
    framework_name: str,
    format: ReportFormat = ReportFormat.JSON,
    db: Session = Depends(get_db),
    scope=Depends(org_scope),
    current_user=Depends(
        require_role(*READ_ROLES)
    )
):
    """
    Per-framework Compliance Assessment (posture, gaps, control risk).
    """

    try:
        report = build_compliance_report(
            db,
            framework_name,
            generated_by=current_user.get("sub"),
            org_id=scope
        )

    except FrameworkNotFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework not found: {framework_name}"
        )

    return _serialize(report, format)
