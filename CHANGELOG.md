## v0.6-alpha11

Test coverage & CI/CD: the third "industry level" axis. Fills in the four
previously-empty test files and adds the first CI pipeline this repo has
ever had, automating the manual verification process (including a rootless
local PostgreSQL) used by hand throughout this whole session.

### Added
- `app/tests/conftest.py`: `as_role` fixture - the first way to test RBAC
  *denial* paths. The existing `get_current_user` override always returned
  admin, so no test anywhere in the suite could exercise "a non-admin/
  analyst gets 403" despite RBAC being a core security feature. `test_assets
  .py::test_create_asset_requires_admin_or_analyst` is the first such test
- `reset_rate_limiter` fixture - `slowapi`'s `Limiter` (added last pass)
  uses a single process-wide in-memory store, not reset between tests;
  without this, login-rate-limit tests would interfere with each other and
  any other test hitting `/login` within the same pytest run
- `seed_asset` fixture - shared setup reused by `test_assets.py`,
  `test_dashboard.py`, `test_imports.py`
- `app/tests/fixtures/sample_nessus_report.pdf` - the real sample Nessus
  PDF used for manual testing all session (`uploads/VA_Scan.pdf`, gitignored
  and therefore invisible to CI) copied to a tracked path. Confirmed
  harmless demo/lab content (private IP range, generic OpenSSH CVEs)
- `app/tests/test_assets.py` (9 tests), `app/tests/test_auth.py` (7 tests),
  `app/tests/test_dashboard.py` (4 tests), `app/tests/test_imports.py`
  (3 tests) - the suite goes from 45 to 68 tests
- `backend/pytest.ini` (`testpaths = app/tests`)
- `.github/workflows/backend-ci.yml` - two jobs on every push/PR to
  `main`/`develop`: `test-sqlite` (fast, zero setup - both `pytest` and
  `alembic upgrade head` work with zero env vars in a fresh checkout) and
  `test-postgres` (real `postgres:18-alpine` service container, runs
  `scripts/bootstrap_database.py` as a migrate+seed smoke test, then the
  full suite against it) - this automates exactly the manual rootless-
  Postgres verification used throughout this whole session, so the two
  dialect-specific bugs found by hand in prior passes (naive/aware
  `datetime` comparison, "database is locked" from the enrichment cache's
  first design) would now be caught automatically on every push, not just
  when someone happens to test against Postgres by hand

### Notes
- `test_auth.py::test_register_and_login_happy_path` surfaced a
  pre-existing `DeprecationWarning`: `services/auth/auth.py` uses
  `datetime.utcnow()` (deprecated in favor of `datetime.now(timezone.utc)`).
  Not fixed here (out of scope, cosmetic, still functionally correct) -
  tracked in TODO.md
- `.github/workflows/backend-ci.yml` is written and YAML-syntax-validated
  but **not executed** - this sandbox has no GitHub Actions runner/API
  access, same honesty standard applied to the Docker files in the
  database-foundation pass. The `test-postgres` job's steps were run
  manually against a real Postgres instance and produced identical results
  (68/68 passing), which is the closest verification possible here, but
  the workflow itself should be watched on its first real push

## v0.6-alpha10

Security & reliability hardening: the second "industry level" axis after
the database foundation. Covers the four things named up front (fragile
CVE-enrichment scraping, no rate limiting, hardcoded `SECRET_KEY`
fallback, inconsistent error responses), scoped down from a bigger
DB-session-restructuring idea that turned out unnecessary once the real
audit was done.

### Added
- `SECRET_KEY` fail-fast: new `ENVIRONMENT` env var (defaults to
  `development`). Outside `development`/`local`/`test`, the app refuses
  to start (`RuntimeError` at import time) if `SECRET_KEY` is unset,
  equals the dev default, or equals the `.env.example` placeholder -
  catches both "forgot to set it" and "copy-pasted the example verbatim"
- Security middleware baseline: `CORSMiddleware` (env-configured
  `CORS_ALLOWED_ORIGINS`, empty by default - no frontend exists yet, and
  an empty list is safe since CORS only gates browser requests), and a
  hand-rolled `SecurityHeadersMiddleware` (`app/middleware/`) setting
  `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`,
  `Strict-Transport-Security`, `Content-Security-Policy` on every response
- Rate limiting via `slowapi` (in-memory, no new infra): a global
  100/minute default, and `POST /login` specifically limited to
  5/minute/IP as a practical substitute for full account lockout
  (there was previously zero brute-force protection on login)
- Persistent CVE-enrichment cache: new `PluginEnrichmentCache` table
  (`plugin_id`, `cve_ids`, `description`, `solution`, `status`,
  `fetched_at`) + `repositories/enrichment/plugin_cache_repository.py`.
  `services/enrichment/plugin_enrichment.py` checks the cache before
  ever hitting tenable.com; a failed lookup is cached with a 24h TTL
  before retrying (avoids hammering plugin IDs that reliably 404, while
  still recovering from a transient outage)
- Hand-rolled retry with exponential backoff on the outbound HTTP call
  (3 attempts; retries timeouts/connection errors/5xx/429, does not
  retry other 4xx since that means "no such plugin page," not transient)

### Changed
- 19 API-layer sites that returned a bare `{"message": "..."}` dict with
  an implicit 200 for what was semantically an error now
  `raise HTTPException(status_code=X, detail="...")` (16×404, 2×400,
  1×401), matching the style already used correctly in
  `frameworks.py`/`mappings.py`. `POST /register`'s validation moved
  from `services/users/user_service.py` (an ambiguous dict-return) into
  `api/users.py` (checks + raises), matching the "validate in API layer,
  service does the write" pattern used by `create_risk`/
  `framework_service.create_framework`
- `app/api/imports.py`'s `upload_report` no longer leaks raw exception
  text to the client (`{"error": str(error)}`, 200) - now
  `HTTPException(500, "Failed to process import findings")`, full
  traceback still logged server-side
- `vulnerability_importer.py`'s three separate enrichment calls
  collapsed into one `get_plugin_enrichment(db, plugin_id)`

### Fixed (found via direct testing, not just code review)
- A naive-vs-aware `datetime` comparison crashed the cache's TTL check
  on SQLite: `DateTime(timezone=True)` columns don't reliably round-trip
  tzinfo through SQLite specifically (Postgres does). Fixed by normalizing
  to UTC-aware on read when the value comes back naive
- **Design correction, caught empirically, not by inspection**: the
  first version of the enrichment cache gave `plugin_enrichment.py` its
  own short-lived DB session (independent of the caller's), reasoning
  that it would protect a successful cache write from being discarded
  if an unrelated later finding in the same import batch caused a
  rollback. Direct testing of a real multi-finding import against a
  file-based SQLite DB proved this reliably crashes with
  `database is locked` - not a rare race, but near-certain, because
  it's the same thread using two connections sequentially (one holding
  an open write transaction), not a genuine concurrent-request race
  that a busy_timeout could wait out. Reverted to sharing the caller's
  session (`add()` + `flush()`, caller commits - the same convention
  every other repository in this codebase already follows), accepting
  the minor durability tradeoff (a lost cache entry on a whole-batch
  rollback just costs one more network fetch next time) over a
  near-guaranteed crash on the common case (any multi-finding import)

### Tests
- `app/tests/test_creation_validation.py`: 6 of 9 assertions updated for
  the new status codes/`detail` field (the other 3 are success-path,
  untouched)
- No automated test coverage added for the enrichment retry/cache logic
  itself (`test_imports.py` is still an empty stub) - verified manually
  with mocked `requests.get` instead; tracked in TODO.md

### Verified
- Full 45-test suite green throughout, including against a real
  PostgreSQL instance (rootless local, same technique as the DB
  foundation pass) for both the baseline and new
  `plugin_enrichment_cache` migrations
- SECRET_KEY fail-fast confirmed in all 4 combinations (dev default,
  prod+placeholder, prod+dev-default, prod+real secret)
- Security headers present on every response; CORS correctly rejects an
  unlisted origin; rate limiting confirmed 5×401 then 429 on repeated
  `/login` failures
- All 19 error-consistency sites confirmed returning their correct
  status code via a live endpoint walkthrough
- Enrichment: retry-then-succeed, cache-hit-skips-network,
  non-transient-404-no-retry, and cached-failure-TTL all confirmed with
  mocked network; the reverted-session-design fix confirmed against a
  real 8-finding import on file-based SQLite (WAL mode) with zero lock
  errors; durability tradeoff confirmed as documented (rollback
  discards the cache write too)

## v0.6-alpha9

Database foundation work: PostgreSQL support, Alembic migrations, Docker,
and real DB-level foreign key enforcement — first step of an "industry
level" push, chosen as the highest-priority axis since everything else
(observability, scale, further hardening) builds on top of it.

### Added
- `DATABASE_URL` is now environment-configured (`app/db/database.py`):
  PostgreSQL via `postgresql+psycopg://...` (used in Docker/production),
  or the unchanged SQLite zero-config local default (now anchored to
  `BACKEND_DIR` instead of a bare relative path — see Fixed)
- Alembic (`backend/alembic/`) is the sole schema authority. `env.py`
  reuses the app's actual `engine`/`DATABASE_URL`/`Base` rather than
  duplicating connection logic, so migrations get identical dialect
  behavior to the running app. One hand-reviewed baseline migration
  covers all 9 current tables/FKs (verified via full downgrade→upgrade
  roundtrip on real PostgreSQL)
- Foreign keys are now enforced at the database level, not just the
  application layer added last pass: natively on PostgreSQL, and via a
  `PRAGMA foreign_keys=ON` connect-event hook on SQLite (SQLite ignores
  FK constraints by default unless told per-connection). Verified: an
  insert with a nonexistent `category_id` is rejected by both dialects
  (`ForeignKeyViolation` on Postgres, `IntegrityError` on SQLite) at the
  database level, on top of the app-level checks added previously
- `backend/Dockerfile` (non-root user, `psycopg[binary]` needs no
  compiler toolchain), `backend/docker-entrypoint.sh` (runs
  `bootstrap_database.py` then `uvicorn`), `docker-compose.yml` (repo
  root: postgres + backend, healthcheck-gated startup order, named
  volumes), `.env.example`, `backend/.dockerignore`
- `python-dotenv` support in both `db/database.py` and `core/config.py`
  (local `.env` populates `DATABASE_URL`/`SECRET_KEY` without manual
  `export`; inert inside Docker, where compose injects real env vars)
- Standard Alembic-recommended `MetaData` naming convention on `Base`,
  so autogenerate produces stable, non-empty constraint names on both
  dialects instead of dialect-dependent auto-generated ones

### Fixed
- `app/main.py` called `Base.metadata.create_all(bind=engine)` at
  **import time** — including during every `pytest` run, since
  `conftest.py` imports `app.main`, silently touching the real
  `cyberrisk360.db` file even though tests then ran against an
  isolated in-memory DB. Removed: schema management is now an explicit
  step (`alembic upgrade head` / `bootstrap_database.py`), never an
  app-startup side effect — avoids the "table already exists" conflict
  that mixing `create_all()` with Alembic causes, and doesn't need
  reconciling with multiple replicas later
- `DATABASE_URL`'s SQLite default and `UPLOAD_DIR` were both bare
  relative paths that resolved differently depending on process cwd —
  caught in the wild as two different `cyberrisk360.db` files (one
  empty, at repo root; the real one under `backend/`). Both now anchor
  to `BACKEND_DIR`, matching how `FRAMEWORKS_DIR` already worked;
  `api/imports.py` now imports `UPLOAD_DIR` from `core.constants`
  instead of shadowing it with its own local relative string

### Notes
- `app/tests/conftest.py` is untouched and confirmed unaffected (it
  builds its own separate in-memory SQLite engine, never imports the
  real one) - verified by running the full 45-test suite with
  `DATABASE_URL` pointed at real Postgres, all passing unmodified. One
  explicit, deliberate gap: FK enforcement isn't wired into conftest's
  engine, so the pytest suite doesn't exercise DB-level FK rejection
  (only the app-level checks). Left as a safe one-line follow-up so
  this pass didn't touch test behavior
- Docker files are written and reviewed for correctness (YAML/shell
  syntax validated) but **not executable in this environment** - the
  Docker daemon socket isn't reachable here (`permission denied`).
  Alembic/Postgres/pytest were all verified for real against a rootless
  local PostgreSQL 18 instance instead
- Two pre-Alembic SQLite files (`cyberrisk360.db` at repo root and
  under `backend/`) were renamed to `*.pre-alembic-backup` rather than
  deleted, since they predate `alembic_version` tracking and mixing
  them with a fresh `alembic upgrade head` fails. Not deleted - your
  call whether to keep or remove them

## v0.6-alpha8

Full endpoint walkthrough (all 52 routes, real JWT auth flow, real PDF
import against `uploads/VA_Scan.pdf` including live plugin enrichment)
to find and fix bugs unreachable by unit tests alone.

### Fixed
- **Crash**: `POST /controls` accepted any `category_id` with no existence
  check. A control created with a dangling `category_id` later crashed
  `GET /controls/{id}/vulnerabilities` with an unhandled
  `AttributeError: 'NoneType' object has no attribute 'framework'` (500) -
  downstream code assumes `control.category` is never `None`. Fixed by
  validating the category exists before creating the control
- `POST /risks` accepted any `asset_id` with no existence check, silently
  creating risks pointing at nonexistent assets (SQLite's FK enforcement is
  off by default, so nothing caught this at the DB layer either). Fixed by
  validating the asset exists before creating the risk
- `POST /vulnerabilities` had the same gap for both `asset_id` and
  `risk_id`, and - separately - validated `cvss_score` on `PUT` update but
  never on `POST` create, letting out-of-range scores (e.g. `15.0`) in.
  Fixed by validating both FKs and the CVSS range before creating

### Tests
- `app/tests/test_creation_validation.py` — 8 tests locking in the three
  fixes above (rejection + happy path for each)

### Notes (flagged, not changed)
- `GET /frameworks/{name}/summary` (`api/controls.py`) and
  `GET /compliance-summary` / `GET /dashboard/grc/{name}`
  (`analytics/compliance.py`) both return a field called `compliance_score`
  for the same framework, but they measure two different things:
  `compliance.py` is % of controls manually marked `"Implemented"`;
  `controls.py`'s framework summary is 100% minus % of controls with an
  approved vulnerability mapping. In one live test run these read 0.0 and
  100.0 for the same framework at the same instant. Not fixed here since
  picking a single canonical definition is a product decision, not a bug
  fix - left as-is and called out in TODO.md
- No route runs the mapping engine when a vulnerability is created via
  `POST /vulnerabilities` directly (only the PDF import pipeline does) -
  confirmed intentional-looking rather than broken, but worth a product
  decision; noted in TODO.md
- `GET /risks` (list all risks) doesn't exist - every other resource
  (`assets`, `controls`, `vulnerabilities`, `frameworks`) has one

## v0.6-alpha7

### Fixed
- Compliance-scoring analytics counted `"pending"` (unreviewed) vulnerability-
  control mappings the same as `"approved"` ones, so the mapping engine's
  manual-approval gate (v0.6-alpha6) had no actual effect on reported
  numbers. `analytics/gap_analysis.py`, `analytics/control_risk_analysis.py`,
  and `api/controls.py`'s `GET /frameworks/{name}/summary` now only count
  `status="approved"` mappings. `GRC`/executive dashboards inherit the fix
  automatically since they compose these two analytics functions rather than
  querying mappings directly
- `mapping_repository.get_by_control` / `count_by_control` gained an
  optional `status` filter (default `None` = all statuses, so the existing
  `GET /controls/{id}/vulnerabilities` inspection endpoint, which
  intentionally shows every match regardless of review state, is unchanged)

### Tests
- `app/tests/test_mapping_status_analytics.py` — 5 tests proving a pending
  mapping doesn't move gap analysis, control risk score, or the framework
  compliance summary, and that approving it does

## v0.6-alpha6

### Added
- Generic Vulnerability Mapping Engine (`services/mapping/mapping_engine.py`):
  matches vulnerabilities to controls by CVE (from `Vulnerability.cve_id`),
  CWE (extracted from title/description via regex), Plugin ID, and keyword,
  using rules merged from every framework's `mapping_rules.json` via the
  existing `discover_frameworks()` scanner — no framework or control set is
  ever referenced by name
- Confidence scoring by match specificity: CVE 0.95, Plugin ID 0.9,
  CWE 0.85, keyword 0.5 (`MAPPING_CONFIDENCE_BY_MATCH_TYPE` in
  `core/constants.py`)
- Manual approval workflow: every engine-generated mapping starts
  `"pending"`; `services/mapping/mapping_service.py` + new `api/mappings.py`
  (`GET /mappings/pending`, `GET /vulnerabilities/{id}/mappings`,
  `GET /mappings/{id}/history`, `PATCH /mappings/{id}/approve`,
  `PATCH /mappings/{id}/reject`) let an admin/analyst approve or reject.
  Reviewer identity comes from the JWT (`current_user["sub"]`), not the
  request body
- `MappingHistory` model/table — an audit trail of every mapping lifecycle
  event (`created`, `approved`, `rejected`) with actor, timestamp, and note
- `VulnerabilityControlMapping` extended with `match_type`, `matched_value`,
  `confidence_score`, `status`, `created_at`, `reviewed_at`, `reviewed_by`
  (additive; existing columns/relationships untouched)
- Real `mapping_rules.json` content for `nist-csf` and `owasp-top10`
  (CVE/CWE/plugin_id/keyword entries); the NIST keyword rules are a
  data-only port of the old hardcoded `CONTROL_RULES` dict, so existing
  keyword-matching behavior carries over unchanged
- `app/tests/test_mapping_engine.py` — 20 tests: pure matcher unit tests,
  rule-merging, persisted-mapping + history creation, idempotency, the
  approve/reject service and API flow

### Changed
- `services/vulnerabilities/vulnerability_importer.py` now calls the new
  engine (loading rules once per batch instead of per finding) instead of
  the old keyword-only mapper

### Removed
- `services/controls/control_mapper.py` — the hardcoded, NIST-CSF-specific
  `CONTROL_RULES` keyword dict is superseded by the generic, data-driven
  engine above. `services/controls/control_suggester.py` (a separate,
  unrelated "suggest control names while typing" helper with no DB writes)
  is untouched

### Fixed
- `mapping_service.review_mapping` committed without calling `db.refresh()`
  afterward, so (same bug pattern as `update_framework` in v0.6-alpha4)
  the approve/reject API responses silently dropped every field

## v0.6-alpha5

### Added
- `services/frameworks/framework_loader.py`: `discover_frameworks(frameworks_dir)`
  — scans `frameworks/*/*/metadata.json` and returns
  `{short_name: {metadata_path, framework_path, version_dir}}`. No framework
  name is ever referenced in code; a new framework is picked up automatically
  by adding `frameworks/<name>/<version>/{metadata.json,framework.json}`
- `frameworks/owasp-top10/2021/` — fifth supported framework (OWASP Top 10
  2021, controls A01–A10), added purely as data with zero code changes
- `get_all_categories(db)` in `repositories/categories/category_repository.py`,
  used for the new bootstrap summary counts
- `bootstrap_database.py` now prints a `✓ Frameworks Imported / ✓ Categories
  Imported / ✓ Controls Imported` summary after import

### Changed
- `services/frameworks/framework_importer.py`: `import_framework` no longer
  dumps every control into a single hardcoded `"GENERAL"` category. It now
  derives a category code from each control's `control_id` structure
  (everything before the final `.` or `-` delimited segment, e.g.
  `"PR.AC-3"` → `"PR.AC"`, `"A.5.1"` → `"A.5"`; falls back to the full
  `control_id` when there's no delimiter, e.g. `"V5"`). No framework-specific
  branching. Verified against real data: 26 controls across all 5 frameworks
  now resolve to 23 distinct categories instead of 5 "GENERAL" ones
- `bootstrap_database.py` and `api/frameworks.py` (`POST
  /frameworks/import/{framework_name}`, `GET
  /frameworks/{framework_name}/search`) now call `discover_frameworks()`
  instead of a hardcoded per-framework dict — both endpoints keep their
  existing request/response shape, only the internal lookup changed
- `core/constants.py`: removed `FRAMEWORK_VERSION_DIRS`, `FRAMEWORK_FILES`,
  `FRAMEWORK_METADATA_FILES`, and the unused `FRAMEWORK_ISO27001` /
  `FRAMEWORK_NIST_CSF` / `FRAMEWORK_OWASP_ASVS` / `FRAMEWORK_CIS` constants
  (`FRAMEWORKS_DIR` is kept — it's just a path, not a framework list)

### Tests
- `app/tests/test_frameworks.py`: added coverage for `discover_frameworks`
  finding all 5 frameworks, the importer deriving multiple real categories
  from a single framework's controls (not a catch-all), and all 5
  bootstrap-style-imported frameworks being visible through the management
  API — 12 tests total, all passing

## v0.6-alpha4

### Added
- Framework management CRUD: `create_framework`/`update_framework`/`delete_framework`
  added to `repositories/frameworks/framework_repository.py`; new
  `services/frameworks/framework_service.py` orchestrating them; new
  `GET /frameworks`, `GET /frameworks/{id}`, `POST /frameworks`,
  `PATCH /frameworks/{id}`, `DELETE /frameworks/{id}` endpoints in
  `api/frameworks.py`; new `schemas/framework.py` (`FrameworkCreate`,
  `FrameworkUpdate`). Writes are admin-only; reads follow the existing
  admin/analyst/auditor pattern
- `app/tests/conftest.py` — first test fixtures in the repo: in-memory
  SQLite (`StaticPool`-backed so all sessions share one connection) with
  `get_db`/`get_current_user` dependency overrides, plus a `TestClient`
  fixture
- `app/tests/test_frameworks.py` — 10 tests covering create/list/get/update/
  delete, the short_name conflict (409) and not-found (404) paths, and a
  check that frameworks imported the same way `bootstrap_database.py`
  imports them are visible through the new management API
- `httpx2`/`httpcore2`/`truststore` pinned in `requirements.txt` — required
  by the installed `starlette==1.2.1`'s `TestClient`, which wasn't usable
  until now despite `pytest` already being listed

### Fixed
- `update_framework` repository function committed but never called
  `db.refresh()`, so SQLAlchemy expired the instance's `__dict__` on
  commit and the PATCH endpoint's JSON response silently dropped every
  field (caught by `test_update_framework`)

## v0.6-alpha3

### Added
- `backend/scripts/bootstrap_database.py` — creates all tables and imports
  every supported framework (NIST CSF, ISO 27001, CIS Controls, OWASP ASVS)
  in one idempotent run; verifies frameworks/controls landed before exiting
- `TODO.md` — working punch list of near-term and deferred follow-ups

## v0.6-alpha2

### Added
- Full repository layer implementation: `assets`, `categories`, `controls`,
  `frameworks`, `risks`, `vulnerabilities`, plus new `users` and
  `vulnerability_control_mappings` repositories
- `services/users/user_service.py` (`register_user`, `authenticate_user`)
- Real `metadata.json` reference data for NIST CSF 2.0, ISO/IEC 27001:2022,
  CIS Controls v8, and OWASP ASVS 4.0.3
- RBAC enforcement on 5 previously-unauthenticated endpoints (asset/control/
  vulnerability detail routes)
- `SECRET_KEY` now configurable via environment variable (dev-only fallback
  retained)

### Fixed
- Framework import pipeline: `core/constants.py`'s `FRAMEWORK_FILES` pointed
  at old flat filenames instead of the real versioned
  `frameworks/<name>/<version>/framework.json` layout; `framework_importer.py`
  rewritten to resolve/create `Framework` + a default `Category` and use
  `title=`/`category_id=` instead of the removed `name=`/`framework=` fields
- Remaining `Control.framework` / `Control.name` references outside
  `analytics/` (`api/controls.py`, `api/vulnerabilities.py`,
  `schemas/control.py`) migrated to `title` / `category.framework.short_name`
- Missing `VULNERABILITY_STATUS_CLOSED` import in `api/vulnerabilities.py`
  (latent `NameError` on `PATCH /vulnerabilities/{id}/close`)
- Dead imports (`SessionLocal`, commented-out model imports in `main.py`)

### Changed
- `analytics/*.py` (`asset_risk`, `control_risk_analysis`, `executive`,
  `gap_analysis`, `grc`) no longer performs direct SQL/ORM queries; routes
  through the repository layer
- All `api/*.py` routes thinned to service/repository calls only, per the
  layering rules in `ARCHITECTURE.md`

## v0.6-alpha1

### Added
- Framework model
- Category model
- Normalized compliance architecture
- SQLAlchemy relationships
- Product Design Document
- Architecture Document
- Database Design
- ADR-001

### Changed
- Refactored Control model
- Introduced Framework → Category → Control hierarchy
- Improved ORM relationships
