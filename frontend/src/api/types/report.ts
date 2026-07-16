// Hand-maintained against the report builders in backend/app/reports/
// (executive_report.py, technical_report.py, compliance_report.py) -
// there's no response_model on any /reports/* route, so these mirror
// the plain dicts those builders return.

import type { FrameworkGapControl } from './framework';

export interface ReportEnvelope<Sections> {
  report_type: string;
  title: string;
  generated_at: string; // ISO datetime
  generated_by: string; // email, or "system"
  sections: Sections;
}

export interface SeverityBreakdown {
  critical: number;
  high: number;
  medium: number;
  low: number;
}

export interface StatusBreakdown {
  open: number;
  closed: number;
}

// sections.top_risk_assets (executive)
export interface AssetRiskRow {
  asset: string;
  critical: number;
  high: number;
  medium: number;
  low: number;
  risk_score: number;
  total_vulnerabilities: number;
}

// sections.framework_compliance (executive)
export interface FrameworkComplianceRow {
  framework: string;
  short_name: string;
  version: string;
  total_controls: number;
  implemented: number;
  partial: number;
  missing: number;
  compliance_score: number;
}

// sections.top_risk_controls (executive, includes `framework`) and
// sections.control_risk (compliance, no `framework` - single-framework
// report already scopes it) - one type covers both.
export interface ControlRiskRow {
  framework?: string;
  control_id: string;
  name: string;
  affected_vulnerabilities: number;
  critical: number;
  high: number;
  medium: number;
  low: number;
  risk_score: number;
}

// sections.findings_by_severity[].findings[] (technical)
export interface Finding {
  id: number;
  title: string;
  severity: string;
  cvss_score: number | null;
  cve_id: string | null;
  plugin_id: string | null;
  ip_address: string | null;
  asset: string | null;
  status: string;
  owner: string | null;
  description: string | null;
  solution: string | null;
}

export interface FindingGroup {
  // Lowercase ("critical"|"high"|"medium"|"low"|"unknown") - unlike
  // Finding.severity, which keeps its original stored casing.
  severity: string;
  findings: Finding[];
}

export interface ExecutiveReportSections {
  overview: {
    total_assets: number;
    total_vulnerabilities: number;
    total_controls: number;
    overall_control_risk_score: number;
  };
  vulnerabilities: {
    by_severity: SeverityBreakdown;
    by_status: StatusBreakdown;
  };
  top_risk_assets: AssetRiskRow[];
  framework_compliance: FrameworkComplianceRow[];
  top_risk_controls: ControlRiskRow[];
}

export interface TechnicalReportSections {
  summary: {
    total_findings: number;
    by_severity: SeverityBreakdown;
    by_status: StatusBreakdown;
    affected_assets: number;
  };
  findings_by_severity: FindingGroup[];
}

export interface ComplianceReportSections {
  framework: {
    name: string;
    short_name: string;
    version: string;
  };
  compliance_summary: {
    total_controls: number;
    implemented: number;
    partial: number;
    missing: number;
    compliance_score: number;
  };
  gaps: {
    total_controls: number;
    affected_controls: FrameworkGapControl[];
    unaffected_controls: FrameworkGapControl[];
  };
  control_risk: ControlRiskRow[];
}

export type ExecutiveReport = ReportEnvelope<ExecutiveReportSections>;
export type TechnicalReport = ReportEnvelope<TechnicalReportSections>;
export type ComplianceReport = ReportEnvelope<ComplianceReportSections>;
