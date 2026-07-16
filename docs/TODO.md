# CyberRisk360 — TODO

Working punch list of near-term follow-ups. For the full long-term roadmap
see `../PRODUCT_DESIGN_DOCUMENT.md` (Section 13) and `architecture.md`
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
      `../frontend/README.md`
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
- [x] Phase 6 (partial) - Reports. Landing page (Executive Summary,
      Technical Vulnerability, framework picker for Compliance
      Assessment) plus one page per report type rendering Phase 1's
      `/reports/*` JSON envelope as stat cards/tables, with an
      authenticated PDF-download control (blob-fetch + synthetic
      link - a plain `<a href>` can't carry the JWT). Verified
      end-to-end incl. all three report types, PDF download, and the
      compliance 404 state. See `ROADMAP.md` Phase 6
- [x] v1.1-alpha1 - Risk Treatment + Approval workflow (Sprint 1 of
      the v1.1+ enterprise roadmap). `treatment_type`/
      `approval_status`/`approved_by`/`approved_at` added to `Risk`
      (layered on the existing `status` field rather than duplicating
      it - two new terminal statuses, `Transferred`/`Avoided`,
      alongside the existing `Mitigated`/`Accepted`), a new
      `risk_treatment_history` table mirroring `mapping_history`'s
      shape, and `POST /risks/{id}/treatment` +
      `PATCH .../treatment/{approve,reject}` +
      `GET .../treatment/history`. Propose = `COMPLIANCE_ROLES`,
      approve/reject = `OVERSIGHT_ROLES` (separation of duties).
      First create/mutate UI + first `useMutation` usage for a
      resource in the frontend. 198 -> 213 tests. See `ROADMAP.md`'s
      new v1.1+ section and `workflow.md`
- [x] Documentation restructure: moved `ARCHITECTURE.md`,
      `DATABASE.md`, `ROADMAP.md`, `TODO.md`, `CHANGELOG.md` into
      `docs/`, fixed every cross-reference repo-wide, added
      `AI_CONTEXT.md` and `workflow.md`
- [x] Frontend CRUD completion (v1.1-alpha2): Create/Update UI (+
      Delete for Frameworks) across Vulnerabilities, Assets, Risks,
      Frameworks - the resources that previously only had read-only
      list+detail views. Added the one missing backend piece (`GET`/
      `PUT /assets/{id}`) needed to make Assets editable at all, fixing
      two real bugs along the way (a route-ordering collision with
      `/assets/risk-summary`, and an expired-ORM-object-on-response bug
      identical to one already fixed once before for
      `update_framework`). No delete added for Vulnerabilities/Assets/
      Risks - no backend support, and a deliberate call, not an
      oversight (see `CHANGELOG.md`). 213 -> 218 tests. Verified
      end-to-end in a real browser for every resource. Imports/
      Evidence/Admin-Org-management frontend modules remain (separate,
      larger effort - Evidence is nearly fully backed already)
- [x] v1.1-alpha3: Audit Management - `Audit`/`AuditFinding` models
      (net-new GRC audit-engagement entity, not to be confused with
      the existing `audit_logs` activity trail), full CRUD + close
      lifecycle + findings, `OVERSIGHT_ROLES` write / `READ_ROLES`
      read, frontend list+detail+create+edit+close matching the Risks
      pattern exactly. 218 -> 238 tests. See `CHANGELOG.md`
- [x] v1.1-alpha4: Control Review Workflow - `ControlReview` model (an
      audit trail on top of the existing global `Control.status`,
      deliberately not the separately-deferred per-org control status
      join table), `POST /controls/{id}/review` (`COMPLIANCE_ROLES`) +
      `GET /controls/{id}/reviews` (`READ_ROLES`), coexisting with the
      pre-existing status-only `PATCH` endpoint. Added `id`/`status` to
      `get_framework_gaps`'s control rows (needed to make review
      possible from the frontend at all). Frontend: Status column +
      inline Review form on `FrameworkDetailPage`'s control tables.
      238 -> 244 tests. See `CHANGELOG.md`
- [x] v1.1-alpha5 (final v1.1 sprint): Evidence Expiry & Notifications.
      **v1.1 "GRC Core" is now fully complete.** Optional `expires_at`
      on evidence attachments; `GET /notifications` computed live at
      read time (no background job - none exists in this codebase),
      bucketing expired/expiring-soon evidence; in-app
      `NotificationBell` in the frontend header per explicit user
      choice (no email/webhook - no credentials/endpoint available).
      Found and fixed a real pre-existing bug along the way: evidence
      upload stamped `org_id` from `org_scope` (None for super-admin)
      instead of `org_home` (always concrete), crashing uploads by a
      super-admin. Also fixed the shared test-suite rate limiter to
      reset per-test automatically instead of relying on opt-in.
      244 -> 251 tests. See `CHANGELOG.md`
- [x] v1.2-alpha1 (Sprint 1 of v1.2 "Vulnerability Intelligence"): CISA
      KEV Integration. New `CisaKevEntry` cache table (whole-catalog
      fetch/replace on a 24h TTL, lazy refresh - no scheduler needed,
      confirmed real outbound network access to `www.cisa.gov` before
      committing); `GET /vulnerabilities/{id}/kev-status`
      (`admin`/`analyst`/`auditor`); frontend badge on
      `VulnerabilityDetailPage`. Found and fixed a real DOM-nesting bug
      via manual browser verification (a `Chip`/`Tooltip` badge nested
      inside the shared `Field` helper's `<Typography>`-as-`<p>`
      wrapper - invalid `<p><div>` HTML). Verified end-to-end against
      the live CISA feed (`CVE-2021-44228`). 251 -> 260 tests. See
      `CHANGELOG.md`
- [x] Phase 6 completion - frontend gap-fill. A full frontend-vs-backend
      audit (user-requested) found 8 features with a working backend
      but zero UI: evidence upload/list/download/delete, user
      registration, self-service password change, admin user
      management (needed two new backend endpoints - `GET /users`,
      `PATCH /users/{id}/role` - neither existed), the Executive and
      GRC dashboards, organization (tenant) management, the
      vulnerability-control mapping review workflow, and scan-report
      imports. All 8 built, wired into the nav, and verified end-to-end
      in a live browser session (zero console errors). Found and fixed
      a real bug along the way: the Users page's role dropdown rendered
      blank for a `super_admin` row (that role is deliberately excluded
      from the assignable-roles list) - now shown as a plain chip
      instead. 260 -> 265 tests. See `CHANGELOG.md`
- [x] v1.2-alpha2 (Sprint 2 of v1.2 "Vulnerability Intelligence"): EPSS
      Integration. New `EpssScoreCache` table (per-CVE lookup against
      FIRST.org, mirroring the NVD enrichment pattern - confirmed real
      outbound network access to `api.first.org` before committing),
      with a 24h TTL even on a successful fetch (EPSS scores are
      recomputed daily, unlike NVD's immutable CVSS/CWE/description
      data); `GET /vulnerabilities/{id}/epss-score`
      (`admin`/`analyst`/`auditor`); frontend field on
      `VulnerabilityDetailPage`, deliberately rendered as a plain
      `<Tooltip><span>` (not a `Chip`) to avoid repeating the KEV
      sprint's `<div>`-in-`<p>` DOM-nesting bug. Verified end-to-end
      against the live FIRST.org feed (`CVE-2021-44228` -> 100.00%).
      265 -> 275 tests. See `CHANGELOG.md`
- [x] v1.2-alpha3 (Sprint 3 of v1.2 "Vulnerability Intelligence"): CWE
      Mapping. Curated static catalog (`frameworks/common/
      cwe_catalog.json`, real MITRE text - no live API, CWE
      definitions barely change) for the 11 CWE ids already referenced
      across the 5 existing `mapping_rules.json` files;
      `GET /vulnerabilities/{id}/cwe-info` resolves via NVD
      enrichment's already-cached `cwe_id` (previously fetched and
      silently discarded) or the mapping engine's own regex
      extraction (`extract_cwe_ids`, renamed from `_extract_cwe_ids`
      now that it has two callers); frontend field on
      `VulnerabilityDetailPage` via a plain `<Link>` (not a `Chip`) to
      keep dodging the KEV sprint's DOM-nesting bug class. Verified
      end-to-end against the real NVD API (`CVE-2021-44228` ->
      `CWE-20`, Improper Input Validation). 275 -> 285 tests. See
      `CHANGELOG.md`
- [x] v1.2-alpha4 (Sprint 4 of v1.2 "Vulnerability Intelligence"): CAPEC
      + MITRE ATT&CK Mapping, delivered together - MITRE's own CAPEC
      data links both a CWE and (where mapped) an ATT&CK technique, so
      one curated catalog (`frameworks/common/capec_catalog.json`, 11
      entries, verified against the real CAPEC CSV) covered both
      remaining roadmap items, no separate ATT&CK ingestion needed.
      Extends `GET /vulnerabilities/{id}/cwe-info` with a `capec` key
      (backward-compatible, not a new endpoint); frontend renders the
      CAPEC pattern + any ATT&CK technique(s) as more inline links next
      to the CWE link. Verified end-to-end for both the empty- and
      populated-`attack_techniques` cases (`CWE-20` -> `CAPEC-120`, no
      ATT&CK; `CWE-287` -> `CAPEC-115` -> `T1548`). 285 -> 289 tests.
      See `CHANGELOG.md`
- [x] v1.2-alpha5 (Sprint 5 of v1.2 "Vulnerability Intelligence"):
      ExploitDB Lookup. New `ExploitDbEntry` cache table (same whole-
      catalog-with-TTL shape as CISA KEV - confirmed real outbound
      network access to the GitLab mirror before committing, since the
      GitHub repo is a stub redirect - one row per (cve_id, exploit_id)
      pair since a CVE can have multiple exploits and a row can list
      multiple CVEs); `GET /vulnerabilities/{id}/exploits`
      (`admin`/`analyst`/`auditor`); frontend table section (not a
      `Field` - this is a list) on `VulnerabilityDetailPage`. Verified
      end-to-end against the live GitLab-hosted CSV
      (`CVE-2021-44228` -> 3 real linked exploits, matching exactly
      what was found during planning). 289 -> 301 tests. See
      `CHANGELOG.md`

## Next up

- [ ] Last open item in v1.2 Vulnerability Intelligence: business-aware
      risk scoring (CVSS + EPSS + asset criticality + exposure +
      business impact + existing controls - purely computational, every
      input now available: EPSS/KEV/CWE/CAPEC/ATT&CK/ExploitDB all
      landed this version)
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
