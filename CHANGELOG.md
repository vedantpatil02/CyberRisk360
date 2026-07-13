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
