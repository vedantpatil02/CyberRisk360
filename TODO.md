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
- [x] Database foundation: `DATABASE_URL` is env-configured (PostgreSQL
      via `postgresql+psycopg://...`, SQLite zero-config default),
      Alembic (`backend/alembic/`) is the sole schema authority with one
      baseline migration covering all 9 tables, and foreign keys are now
      enforced at the DB level on both dialects (not just the app-level
      checks from the previous pass) - verified end-to-end against a
      real PostgreSQL instance (migrations, bootstrap, full 45-test
      pytest suite, FK rejection on bad inserts). `docker-compose.yml` +
      `backend/Dockerfile` ship a working Postgres+backend setup
      (written/reviewed, not executable in this environment - no Docker
      daemon access here)
- [x] Security & reliability hardening: `SECRET_KEY` fail-fast outside
      dev (`ENVIRONMENT` env var), CORS + security-headers middleware,
      `slowapi` rate limiting (100/min global, 5/min on `/login`), all
      19 bare-`{"message":...}`-with-200 error sites converted to
      proper `HTTPException`s, and a persistent CVE-enrichment cache
      (`PluginEnrichmentCache`) with retry/backoff - replacing the
      in-memory-only cache and single-attempt scraping. Caught and fixed
      a real bug along the way: the cache's first design (its own DB
      session) reliably crashed multi-finding SQLite imports with
      "database is locked" - reverted to sharing the caller's session
- [x] Test coverage & CI: filled in all 4 empty test files (45 → 68
      tests) and added the first CI pipeline (`.github/workflows/
      backend-ci.yml`, SQLite + real-Postgres jobs). Added an `as_role`
      fixture closing a real gap - no test could previously exercise an
      RBAC *denial* path. `.github/workflows/backend-ci.yml` itself is
      unexecuted in this sandbox (no GitHub Actions runner access) -
      watch its first real push

## Next up

- [ ] Watch `.github/workflows/backend-ci.yml`'s first real run on
      GitHub - written and YAML-validated here, its steps were run
      manually with identical results (68/68 passing against real
      Postgres), but the workflow itself was never executed by an
      actual runner
- [ ] `services/auth/auth.py` uses the deprecated `datetime.utcnow()`
      (surfaced as a `DeprecationWarning` by the new `test_auth.py`) -
      should move to `datetime.now(timezone.utc)`, cosmetic/low-priority
- [ ] Rate limiting (`slowapi`) uses in-memory storage - fine for the
      current single-instance `docker-compose.yml`, but needs a shared
      backend (e.g. Redis) before ever running multiple backend
      replicas, since each process would track limits independently
- [ ] `get_remote_address` (rate limiting's key function) trusts
      `request.client.host` directly - correct with no reverse proxy in
      front today, but would need to trust `X-Forwarded-For` instead if
      one is ever added, otherwise every request appears to come from
      the proxy's IP
- [ ] Add the same `PRAGMA foreign_keys=ON` connect-event to
      `app/tests/conftest.py`'s isolated test engine, so the pytest
      suite exercises DB-level FK rejection too (currently only the
      app-level existence checks are covered by tests; deliberately
      deferred so this pass didn't change any test behavior)
- [ ] Verify the Docker setup (`docker-compose.yml`, `backend/Dockerfile`,
      `backend/docker-entrypoint.sh`) with a real `docker compose up` in
      an environment with daemon access - written and syntax-checked
      here, but never actually built/run. Pay particular attention to
      the `uploads` volume's ownership (non-root `appuser` needs write
      access after the volume mounts over `/app/uploads`)
- [ ] Decide whether to keep or delete the two renamed
      `*.pre-alembic-backup` SQLite files (pre-date Alembic's
      `alembic_version` tracking, superseded by `alembic upgrade head`)
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
- [ ] Populate `mapping_rules.json` for the remaining three frameworks
      (`iso27001`, `cis`, `owasp-asvs` are still 0 bytes) — the mapping
      engine already merges whatever it finds, so this is pure data entry,
      no code changes needed
- [ ] Fix the Nessus PDF parser's multi-host bug
      (`app/importers/nessus_pdf_parser.py` attributes every finding in a
      report to the first IP address found in the document)
- [ ] `vulnerability_importer.py`'s `import_findings` still holds one
      DB session/transaction open across a whole import batch's worth
      of sequential enrichment lookups, only committing at the end (or
      rolling everything back on any failure). The persistent cache
      (this pass) means most of those lookups skip the network
      entirely after the first import, but a large *first-time* import
      still serializes real network calls inside one long-held
      transaction. Fixing this properly means restructuring
      `import_findings` into two phases (enrich-then-write) -
      deliberately deferred twice now (database-foundation pass and
      this one) as a bigger scalability refactor, not a "fragile
      dependency" reliability fix

## Deferred (explicitly out of scope per Phase 1 Stabilization)

- [ ] CSV / native `.nessus` XML importers (`services/imports/report_processor.py`
      stubs)
- [ ] `services/enrichment/cve_enrichment.py` (currently a no-op)
- [ ] `backend/app/reports/*.py` report generation (all empty stubs)
- [ ] Additional frameworks: PCI DSS, SOC 2, HIPAA, NIST SP 800-53
- [ ] Kubernetes deployment (Docker/Compose done - see Done section)
- [ ] React frontend
