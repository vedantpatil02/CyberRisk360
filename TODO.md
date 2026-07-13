# CyberRisk360 — TODO

Working punch list of near-term follow-ups. For the full long-term roadmap
see `PRODUCT_DESIGN_DOCUMENT.md` (Section 13) and `ARCHITECTURE.md`
(Section 16-17).

## Done

- [x] Repository layer implemented and wired (`services`/`analytics`/`api`
      no longer bypass it)
- [x] Control schema migration completed repository-wide
- [x] Framework import pipeline fixed (paths, importer, metadata.json)
- [x] RBAC gaps closed on 5 previously-open endpoints
- [x] `SECRET_KEY` externalized to environment
- [x] `backend/scripts/bootstrap_database.py` — create tables, import all
      frameworks, verify, idempotent

## Next up

- [ ] Write real test coverage — `backend/app/tests/*.py` are all empty
      stubs; `pytest` isn't in `requirements.txt` yet
- [ ] Populate `mapping_rules.json` per framework (currently 0 bytes for
      all four) so controls import into real categories instead of a
      single "General" placeholder category
- [ ] Replace the hardcoded `CONTROL_RULES` keyword dict in
      `services/controls/control_mapper.py` with mapping-rules-driven
      auto-mapping once the above is populated
- [ ] Fix the Nessus PDF parser's multi-host bug
      (`app/importers/nessus_pdf_parser.py` attributes every finding in a
      report to the first IP address found in the document)
- [ ] Reduce reliance on live tenable.com scraping in
      `services/enrichment/plugin_enrichment.py` (fragile, no persistent
      cache, no retry/backoff)

## Deferred (explicitly out of scope per Phase 1 Stabilization)

- [ ] CSV / native `.nessus` XML importers (`services/imports/report_processor.py`
      stubs)
- [ ] `services/enrichment/cve_enrichment.py` (currently a no-op)
- [ ] `backend/app/reports/*.py` report generation (all empty stubs)
- [ ] PostgreSQL + Alembic migration tooling
- [ ] Additional frameworks: PCI DSS, SOC 2, HIPAA, NIST SP 800-53
- [ ] Docker / Kubernetes deployment
- [ ] React frontend
