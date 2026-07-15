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
- [x] TODO.md backlog cleanup: fixed the deprecated `datetime.utcnow()`
      in `services/auth/auth.py`; added `GET /risks`; populated
      `mapping_rules.json` for `iso27001`/`cis`/`owasp-asvs`; fixed the
      Nessus PDF parser's multi-host bug (was attributing every finding
      to the first IP anywhere in the document - now tracks current host
      as running state, verified with a synthetic 2-host report since
      the real sample fixture is single-host); added the same
      `PRAGMA foreign_keys=ON` to `conftest.py`'s test engine as the
      real app engine has. 68 → 75 tests
- [x] `POST /vulnerabilities` (manual entry) now runs the mapping engine
      automatically, same as PDF import - previously silently skipped,
      an inconsistency that undercut the mapping engine's purpose for
      an entire creation pathway. Keyword-only (no `cve_id`/`plugin_id`
      in this schema). 75 → 76 tests
- [x] Deleted the two `*.pre-alembic-backup` SQLite files (pre-dated
      Alembic's `alembic_version` tracking, fully superseded by
      `alembic upgrade head`)
- [x] Resolved the `compliance_score` naming collision: renamed
      `api/controls.py`'s `GET /frameworks/{name}/summary` field to
      `vulnerability_coverage_score` per explicit direction (neither
      definition picked as canonical - both are legitimate, they just
      needed to stop sharing a name). No behavior/value change
- [x] CSV and native `.nessus` XML importers (`importers/
      nessus_csv_parser.py`, `importers/nessus_xml_parser.py`), replacing
      the `report_processor.py` stubs. `.nessus` XML parsed with
      `defusedxml` for XXE protection. Added a file-extension allowlist
      and try/except hardening around `process_report()` in
      `api/imports.py`, fixing a latent `KeyError`→500 bug the stubs had
      (missing `"file_type"` key). 76 → 91 tests
- [x] `vulnerability_importer.import_findings` split into two phases
      (`_enrich_findings` then `_write_findings`) so slow/failed
      network-bound enrichment lookups no longer sit inside one
      long-held write transaction with the actual DB writes - the
      "deliberately deferred twice" item below. Along the way, found
      and fixed a real regression risk: splitting the phases would
      have silently broken intra-batch duplicate-`plugin_id` dedup
      (previously working only by accident, via flush-visibility, and
      untested) - fixed with an explicit in-memory dedup set.
      `get_plugin_enrichment` now returns `(dict, cache_written: bool)`
      so phase 1 only commits when it actually wrote the cache, not on
      every cache hit. 91 → 96 tests
- [x] Reporting module (`app/reports/`) - the four 0-byte stubs are now
      implemented: Executive Summary, Technical Vulnerability, and
      Compliance Assessment reports, each served as JSON/HTML/PDF via
      `GET /reports/*` (RBAC admin/analyst/auditor). Builders compose
      existing analytics only (no schema change). HTML via Jinja2
      (autoescaped - XSS control over user-supplied vuln text), PDF via
      pure-Python xhtml2pdf (no system libs, container-safe). See
      `ROADMAP.md` Phase 1. 96 → 103 tests
- [x] Phase 2 - audit log + user hardening. New `audit_logs` table and
      `record_audit()` service wired into auth, account management,
      imports, and mapping review; oversight-only `GET /audit-logs`.
      Account lockout (5 fails / 15 min), disabled-account rejection,
      `last_login`/`is_active`/timestamps on `User`, self change-password
      + admin reset/activate/deactivate. Six design-doc personas via
      semantic role groups. Migrations `dd92d089fdb0` + `cf7f92f27fe3`
      (batch_alter_table for the SQLite CURRENT_TIMESTAMP default). See
      `ROADMAP.md` Phase 2. 103 → 125 tests
- [x] Phase 5 (partial) - remediation workflow. `assignee_id` (real
      `User` FK, validated same-org) and `due_date`/SLA (fixed
      hours-per-severity, computed once at creation, never reshifted
      by a later edit; a stateless `sla_breached` query filter) on
      vulnerabilities and risks, plus a new `evidence_attachments`
      table with upload/list/download/delete endpoints reusing the
      `UPLOAD_DIR` convention. Migration `87367710486c`, verified to
      round-trip cleanly. See `ROADMAP.md` Phase 5. 156 → 178 tests
- [x] Phase 5 (partial) - CVE enrichment via NVD. Real
      `cve_enrichment.py` (was a 3-line no-op, never called) with its
      own persistent cache/retry/backoff mirroring
      `plugin_enrichment.py`, wired into the import pipeline as a
      second pass keyed off each finding's first CVE ID (deduped
      across the batch, bounded call volume), optional `NVD_API_KEY`
      for a higher rate limit, and a standalone `POST
      /vulnerabilities/{id}/enrich-cve` to backfill vulnerabilities
      imported before this existed. Migration `7269075996ec`, verified
      to round-trip cleanly. See `ROADMAP.md` Phase 5. 178 → 196 tests
- [x] Phase 6 (partial) - first frontend slice. `frontend/` scaffolded
      from an empty directory (Vite + React + TypeScript + MUI +
      TanStack Query + React Router - no Node tooling existed before
      this). Form-encoded login (matches the backend's
      `OAuth2PasswordRequestForm`), JWT decoded client-side for
      role/org (no `/me` round trip needed), `sessionStorage` (no
      refresh-token endpoint exists, so nothing is gained by
      localStorage), a role-gated nav shell, `GET /dashboard/overview`,
      and a full Vulnerabilities list+detail view with a generic
      `DataTable` built against the API's bare-array/no-total-count
      pagination convention (`limit = pageSize + 1` to derive
      `hasNextPage`) - the piece Assets/Risks reuse unchanged next.
      Verified end-to-end in real headless Chromium against the
      running backend, including the RBAC edge cases: nav-gating,
      in-place "Access denied" (not a crash/logout) for a
      permitted-but-restricted route, and an invalid/expired token
      correctly redirecting to `/login`. See `ROADMAP.md` Phase 6 and
      `frontend/README.md`
- [x] Phase 6 (partial) - Assets list + detail, reusing the
      `DataTable`/hook/page pattern unchanged - confirms it
      generalizes to a resource whose list and detail endpoints sit at
      *different* RBAC tiers (`GET /assets` ungated, `.../summary` and
      `.../vulnerabilities` require admin/analyst/auditor). Detail view
      is necessarily partial (severity breakdown + vulnerability list
      only) since there's no `GET /assets/{id}` on the backend to
      fetch the asset's own fields by id - a real, documented gap, not
      papered over. Verified end-to-end incl. the 404 state. See
      `ROADMAP.md` Phase 6
- [x] Populated 3 of the 5 compliance frameworks with complete,
      officially-sourced control data (were 2-10 item placeholder
      samples): NIST CSF 2.0 (106 subcategories, public domain, from
      NIST's own OSCAL catalog - filtered out ~38 withdrawn CSF-1.1
      crosswalk entries the source bundles alongside the real 2.0
      data), OWASP ASVS upgraded v4.0.3 → v5.0.0 (345 requirements,
      CC BY-SA), OWASP Top 10 2021 (verbatim official descriptions,
      CC BY-SA). `mapping_rules.json` for both retargeted to real
      control IDs (old placeholder IDs like `PR.AC-1`/bare `V5` don't
      exist in the new datasets). CIS Controls v8 and ISO/IEC
      27001:2022 deliberately left as 2-item placeholders and NOT
      populated - see `CHANGELOG.md` for the specific licensing
      blocker per framework (CIS: CC BY-NC-ND's No-Derivatives clause;
      ISO: full copyright, no redistribution rights found). 197 → 198
      tests.
- [x] Phase 6 (partial) - Risks list + detail, reusing the
      `DataTable`/hook/page pattern unchanged - simpler than Assets
      since `GET /risks` and `GET /risks/{id}` share one RBAC tier.
      `SeverityChip`/`StatusChip` generalized to plain `string` props
      so both Vulnerabilities and Risks share them instead of
      duplicating chip markup. Verified end-to-end incl. the 404
      state. See `ROADMAP.md` Phase 6
- [x] Phase 6 (partial) - Frameworks list + detail. First resource
      that doesn't fit `DataTable` - none of its endpoints support
      server-side pagination/sort/filter, so plain MUI tables are used
      instead of forcing the generic component onto a contract the
      backend doesn't offer. Detail page surfaces real compliance gap
      analysis (controls with/without approved-mapping coverage) via
      `GET /frameworks/{name}/gaps`; per-control drill-down is out of
      scope since no endpoint exposes one framework's controls with
      full detail (documented gap, not papered over). Verified
      end-to-end incl. the not-found state. See `ROADMAP.md` Phase 6

## Next up

- [ ] Watch `.github/workflows/backend-ci.yml`'s first real run on
      GitHub - written and YAML-validated here, its steps were run
      manually with identical results (75/75 passing against real
      Postgres), but the workflow itself was never executed by an
      actual runner
- [ ] Rate limiting (`slowapi`) uses in-memory storage - fine for the
      current single-instance `docker-compose.yml`, but needs a shared
      backend (e.g. Redis) before ever running multiple backend
      replicas, since each process would track limits independently
- [x] `X-Forwarded-For` handling (Phase 3): rate limiting and the audit
      trail now share `app/core/net.py::get_client_ip`, which trusts
      `X-Forwarded-For` when `TRUST_PROXY_HEADERS=true` (behind a trusted
      proxy) and otherwise reads the socket peer. Replaced slowapi's
      `get_remote_address` as the limiter key function
- [ ] Verify the Docker setup (`docker-compose.yml`, `backend/Dockerfile`,
      `backend/docker-entrypoint.sh`) with a real `docker compose up` in
      an environment with daemon access - written and syntax-checked
      here, but never actually built/run. Pay particular attention to
      the `uploads` volume's ownership (non-root `appuser` needs write
      access after the volume mounts over `/app/uploads`)

## Deferred (explicitly out of scope per Phase 1 Stabilization)

- [ ] Additional frameworks: PCI DSS, SOC 2, HIPAA, NIST SP 800-53
- [ ] Kubernetes deployment (Docker/Compose done - see Done section)
- [ ] React frontend
