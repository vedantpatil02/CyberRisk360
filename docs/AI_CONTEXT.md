# AI_CONTEXT.md

Context for an AI agent (or a new contributor) picking up work on
CyberRisk360. This is a pointer document, not a replacement for the docs it
points at — read those for detail; this file just orients you fast.

## What this project is

CyberRisk360 is a Cyber Risk & GRC (governance, risk, compliance) platform —
comparable in scope to ServiceNow GRC, Archer, Drata, Vanta, Tenable One, and
Microsoft Defender Exposure Management. It ingests vulnerability scanner
output (Nessus/CSV/PDF today), correlates it to assets, maps it to compliance
controls across multiple frameworks, and turns that into risk scoring,
compliance dashboards, and executive/technical/compliance reports.

## Architecture (frozen)

```
API → Services → Repositories → Models → Database
```

- **API** (`backend/app/api/`): FastAPI routes. Request validation, auth,
  RBAC, response shaping. No business logic, no `db.query()`.
- **Services** (`backend/app/services/`): business logic. Call
  repositories, never touch the ORM/session directly, never return an HTTP
  response.
- **Repositories** (`backend/app/repositories/`): the *only* layer allowed
  to run `db.query()` / `db.add()` / `db.commit()`. One module per
  resource.
- **Models** (`backend/app/models/`): SQLAlchemy ORM entities. No business
  logic.
- **Database**: SQLite (zero-config local default) or PostgreSQL (via
  `DATABASE_URL`, used in Docker/production). Alembic is the sole schema
  authority — never `Base.metadata.create_all()` outside tests.

This layering is enforced today, not aspirational — see `architecture.md`
§0. Never bypass it: no `db.query()` in `api/`, `services/`, or
`analytics/`; always go through a repository function.

## Conventions worth knowing before writing code

- **RBAC**: role checks use `require_role(*ROLE_GROUP)` from
  `app/dependencies/rbac.py`, where `ROLE_GROUP` is one of the semantic
  tuples in `app/core/constants.py` (`WRITE_ROLES`, `COMPLIANCE_ROLES`,
  `OVERSIGHT_ROLES`, `READ_ROLES`) — prefer these over hardcoding a role
  list, so a new persona slots in by editing one tuple, not every router.
  `super_admin` always bypasses every check.
- **Multi-tenancy**: every per-org table has `org_id`; reads go through
  `Depends(org_scope)`, writes through `Depends(org_home)`
  (`app/dependencies/tenancy.py`).
- **Approval/review workflows**: the established pattern is a `status`
  string field + `reviewed_at`/`reviewed_by` (string identity, not a `User`
  FK) directly on the entity, plus a separate `*_history` table recording
  every transition (`action`, `previous_status`, `new_status`, `actor`,
  `note`, `created_at`, `org_id`). See `app/models/mapping_history.py` and
  `app/services/mapping/mapping_service.py::review_mapping` for the
  reference implementation; `workflow.md` documents every workflow
  built this way.
- **Audit trail**: security/activity-relevant actions call
  `record_audit()` (`app/services/audit/audit.py`) with a canonical
  `ACTION_*` key. This is a generic activity log — distinct from any
  resource-specific `*_history` table.
- **Migrations**: Alembic, one hand-reviewed revision per change,
  `op.batch_alter_table(table, schema=None)` for SQLite compatibility.
  Naming convention lives in `app/db/database.py`.
- **No background jobs / notifications infrastructure exists yet** — no
  Celery, no APScheduler, no email/webhook sender. Anything needing
  scheduled or async execution needs that infrastructure built first.

## Where the other docs live

All under `docs/`:
- `architecture.md` — full layered architecture, module responsibilities,
  compliance/vulnerability/mapping workflows, deployment status.
- `database.md` — schema, entity relationships, table definitions.
- `ROADMAP.md` — phased roadmap (Phase 1–6, historical) plus the current
  v1.1+ enterprise roadmap appended below it.
- `TODO.md` — near-term punch list, updated every sprint.
- `CHANGELOG.md` — detailed per-release history — the most reliable record
  of what's actually been built and why, sprint by sprint.
- `workflow.md` — living reference of every GRC workflow implemented in
  the codebase (approval patterns, remediation SLA, risk treatment, etc).

`../PRODUCT_DESIGN_DOCUMENT.md` (root) has the original product vision and
persona definitions. `../README.md` (root) is the project entry point.

## Current state (see `ROADMAP.md` for detail)

Phases 1, 2, 4 complete. Phase 3 mostly done (object storage/Redis/metrics
blocked on external infra). Phase 5 partial (remediation workflow + CVE
enrichment done; notifications, scheduled imports, extra frameworks, SSO
remain). Phase 6 (frontend) in progress — Vulnerabilities/Assets/Risks/
Frameworks/Reports have list+detail views; Imports/Evidence/Admin remain.
The v1.1+ enterprise roadmap is being worked one sprint at a time on top of
this — check `TODO.md`'s "Done" section for the latest.
