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
- [x] Framework management CRUD (repository → service → API) with RBAC,
      backed by `app/tests/test_frameworks.py`; bootstrap-imported
      frameworks confirmed reachable through the new endpoints
- [x] Generic multi-framework support: `discover_frameworks()` scans
      `frameworks/` automatically (no hardcoded framework list anywhere);
      `framework_importer.py` derives categories from `control_id`
      structure instead of dumping everything into one `"GENERAL"`
      category; added OWASP Top 10 (5th framework) as pure data, no code
      changes required; `bootstrap_database.py` prints a
      Frameworks/Categories/Controls import summary
- [x] Generic Vulnerability Mapping Engine: CVE/CWE/Plugin ID/keyword
      matching with confidence scoring, pending → approved/rejected manual
      review workflow (`api/mappings.py`), and a `MappingHistory` audit
      trail. Replaced the hardcoded `services/controls/control_mapper.py`
      keyword dict; rules now live in `mapping_rules.json`, populated for
      `nist-csf` and `owasp-top10`
- [x] Compliance-scoring analytics (`gap_analysis.py`,
      `control_risk_analysis.py`, `GET /frameworks/{name}/summary`, and by
      extension the GRC/executive dashboards) now only count `"approved"`
      mappings - a `"pending"` mapping no longer moves compliance/risk
      numbers before a human reviews it. `GET /controls/{id}/vulnerabilities`
      deliberately still shows all mappings regardless of status (it's an
      inspection view, not a score)
- [x] Full endpoint walkthrough (all 52 routes, real auth, real PDF import)
      surfaced and fixed 3 bugs: `POST /controls` with a dangling
      `category_id` crashed `GET /controls/{id}/vulnerabilities` (500);
      `POST /risks` accepted nonexistent `asset_id`; `POST /vulnerabilities`
      accepted nonexistent `asset_id`/`risk_id` and skipped the CVSS range
      check that `PUT` already enforced. See `test_creation_validation.py`

## Next up

- [ ] **Two different, contradictory `compliance_score` definitions** for
      the same framework: `analytics/compliance.py` (used by
      `/compliance-summary` and `/dashboard/grc/{name}`) = % of controls
      manually marked `"Implemented"`; `api/controls.py`'s
      `GET /frameworks/{name}/summary` = 100% minus % of controls with an
      approved vulnerability mapping. These can read 0% and 100% for the
      same framework simultaneously. Needs a product decision on which is
      canonical (or rename one so it's not both called "compliance_score")
- [ ] Decide whether `POST /vulnerabilities` (manual entry) should also run
      the mapping engine - today only the PDF import pipeline
      (`import_findings`) calls `map_vulnerability_to_controls`, so
      manually-created vulnerabilities never get auto-mapped
- [ ] No `GET /risks` (list all) endpoint exists, unlike every other
      resource (`assets`, `controls`, `vulnerabilities`, `frameworks`)
- [ ] Write real test coverage for the rest of the API — only
      `test_frameworks.py`, `test_mapping_engine.py`,
      `test_mapping_status_analytics.py`, and `test_creation_validation.py`
      have tests now; `test_assets.py`, `test_auth.py`, `test_dashboard.py`,
      and `test_imports.py` are still empty stubs. `app/tests/conftest.py`
      (in-memory SQLite + dependency overrides + `TestClient` fixture) is
      in place for them to build on
- [ ] SQLite foreign key enforcement is off by default (`PRAGMA
      foreign_keys` is 0 unless explicitly enabled per-connection) - the
      three FK-existence checks added in this pass close the concrete holes
      found, but any other unvalidated FK write path has the same
      underlying gap. Enabling it globally (`PRAGMA foreign_keys=ON` on
      connect) would be the systemic fix, but wasn't done here since it
      changes error behavior (silent orphan → `IntegrityError`/500) for
      every FK in the schema at once and needs its own testing pass
- [ ] Populate `mapping_rules.json` for the remaining three frameworks
      (`iso27001`, `cis`, `owasp-asvs` are still 0 bytes) — the mapping
      engine already merges whatever it finds, so this is pure data entry,
      no code changes needed
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
