// POST /imports/nessus_report_upload - matches
// backend/app/services/imports/report_processor.py::process_report +
// vulnerability_importer.py::import_findings exactly. `import_result`
// is only present when at least one finding was extracted.
export interface ImportResult {
  file_type: 'pdf' | 'csv' | 'nessus';
  findings_detected: number;
  findings?: unknown[];
  import_result?: {
    created: number;
    duplicates: number;
  };
}
