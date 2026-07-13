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
