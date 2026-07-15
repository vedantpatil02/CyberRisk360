# CyberRisk360 — Industry-Readiness Roadmap

This roadmap turns the MVP backend into a deployable, industry-usable
GRC platform. It complements `TODO.md` (near-term punch list) and
`PRODUCT_DESIGN_DOCUMENT.md` (§13 release roadmap). Items are ordered by
value and by how expensive they are to retrofit later.

Legend: ✅ done · 🚧 in progress · ⬜ not started

---

## Phase 1 — Reporting module ✅

**Why first:** A promised core module (§8.6) that shipped as 0-byte
stubs, and a stated success criterion ("executive-ready reports"). Turns
the platform into something demonstrable to a CISO/auditor. No schema
changes.

- ✅ Report builders that compose existing analytics into structured
  data: Executive Summary, Technical Vulnerability, Compliance Assessment
- ✅ HTML renderer (Jinja2, autoescaped — reports embed user-controlled
  vulnerability text)
- ✅ PDF renderer (xhtml2pdf — pure-Python, no system libs, container-safe)
- ✅ `/reports/*` API with `?format=json|html|pdf`, RBAC-guarded
- ✅ Tests covering all three reports × three formats (96 → 103 tests)

## Phase 2 — Audit log + user hardening ✅

**Why:** An audit trail is table-stakes for a GRC product and ironic to
lack. User identity is currently minimal. Low schema risk.

- ✅ `audit_logs` table (actor, action, entity, entity_id, ip,
  timestamp, detail) + a `record_audit()` service and write hooks on
  auth, account management, imports, and mapping review; oversight-only
  `GET /audit-logs` with filters + pagination
- ✅ `User`: `created_at`, `updated_at`, `last_login`, `is_active`
  (+ `failed_login_attempts`, `locked_until`)
- ✅ Account safety: failed-login lockout (5 attempts / 15 min),
  disabled-account rejection, self change-password + admin reset/
  activate/deactivate. (Token-based self-service "forgot password"
  deferred to Phase 5 — needs email/notifications.)
- ✅ Expanded roles to the six design-doc personas via semantic role
  groups (`WRITE_ROLES`/`COMPLIANCE_ROLES`/`OVERSIGHT_ROLES`/
  `READ_ROLES`) — pentester, GRC analyst, security manager, CISO
  (105 → 125 tests)

## Phase 3 — Scale & correctness floor 🚧

- ✅ Pagination + filtering + sorting on the list endpoints
  (`/vulnerabilities`, `/assets`, `/risks`) — opt-in `limit`/`offset`,
  filters, and allowlisted `sort_by`/`order`
- ✅ `/health` and `/ready` endpoints (readiness checks DB + migration
  head); structured logging + `X-Request-ID` request correlation
- ✅ `X-Forwarded-For` handling behind a proxy, gated by
  `TRUST_PROXY_HEADERS` (shared client-IP resolver for rate limiting +
  audit)
- ⬜ Object storage for uploads (S3-compatible) instead of local disk —
  `UPLOAD_DIR` is now env-configurable as a stepping stone; needs the
  storage backend + infra to build against
- ⬜ Redis-backed rate limiting for multi-replica deployments — needs
  Redis to build against
- ⬜ Basic metrics endpoint (Prometheus-style)

## Phase 4 — Multi-tenancy ✅

**Why later:** Highest-effort change (touches every model and query), so
sequenced after the foundations are stable.

- ✅ `Organization` model; `org_id` FK on every per-org table (users,
  assets, vulnerabilities, risks, mappings, mapping history, audit
  logs). Frameworks/controls/plugin cache stay shared reference data.
- ✅ Row-level org scoping across repositories, services, analytics,
  dashboards, and reports (`app/dependencies/tenancy.py`, `org_id` JWT
  claim); org-aware admin actions
- ✅ Platform super-admin spanning all orgs + org management API
- ✅ Migration with default-org backfill (verified fwd/reverse); 149 →
  156 tests incl. cross-org isolation
- ✅ `scripts/bootstrap_super_admin.py`: idempotent super-admin
  provisioning (create-or-`--force`-reset), configurable via
  `SUPER_ADMIN_EMAIL`/`SUPER_ADMIN_USERNAME`/`SUPER_ADMIN_PASSWORD`/
  `SUPER_ADMIN_ORG_SLUG`, generates and prints a random password when
  none is supplied. Deliberately separate from `bootstrap_database.py`/
  `docker-entrypoint.sh` — provisioning a privileged account is a
  manual operator action, not something to run silently on every
  container start
- ⬜ Follow-up: per-org control implementation status (join table)

## Phase 5 — Workflow, integrations, enrichment 🚧

- ✅ Remediation workflow: `assignee_id` (real `User` FK, validated
  same-org via a 404-on-cross-org check), `due_date`/SLA (fixed
  hours-per-severity, computed once at creation, never silently
  reshifted on a later edit; a stateless `sla_breached` filter on the
  list endpoints), and evidence attachments (`evidence_attachments`
  table + `POST/GET .../evidence` + `GET/DELETE /evidence/{id}`,
  reusing the `UPLOAD_DIR` convention). `owner` (free text) is kept
  alongside `assignee_id`, not replaced — it holds non-user values
  (`"Imported"`, an asset's owner label) that don't map to a real
  account. 178 tests (was 156)
- ✅ CVE enrichment (`cve_enrichment.py` was a no-op) via a real NVD
  lookup: new `nvd_enrichment_cache` table mirroring
  `plugin_enrichment_cache`'s cache/retry/backoff shape, a second
  enrichment pass in the import pipeline keyed off the first CVE ID
  per finding (bounded NVD call volume), optional `NVD_API_KEY` for a
  higher rate limit, and a standalone `POST
  /vulnerabilities/{id}/enrich-cve` to backfill vulnerabilities
  imported before this existed. 196 tests (was 178)
- ⬜ Notifications (email/webhook): new criticals, SLA breach, import
  done — needs a background-job mechanism (no Celery/APScheduler in
  this codebase yet) and a notification target (SMTP/webhook)
- ⬜ Scheduled / API-based imports (Nessus/OpenVAS APIs) — needs
  external API credentials
- ⬜ Additional frameworks: PCI DSS, SOC 2, HIPAA, NIST SP 800-53
  (pure data — no code changes required, but needs real control text
  sourced from the actual standards, not fabricated)
- ⬜ SSO (SAML/OIDC) — needs an IdP to integrate against

## Phase 6 — Frontend 🚧

- ✅ First slice: `frontend/` scaffolded from nothing (Vite + React +
  TypeScript + MUI + TanStack Query + React Router — zero Node tooling
  existed before this). Auth (form-encoded `POST /login`, JWT decoded
  client-side for role/org, `sessionStorage`, no refresh token so a
  hard re-login on the fixed 60-min expiry), a role-gated nav shell,
  the `/dashboard/overview` page, and a full Vulnerabilities
  list+detail view exercising a generic paginated/sortable/filterable
  `DataTable` (built against the API's bare-array/no-total-count list
  convention) that Risks/Assets will reuse unchanged. Verified
  end-to-end in a real headless-Chromium session against the running
  backend: login, dashboard, sort/filter/paginate, detail + mapped
  controls, logout, RBAC nav-gating + in-place "Access denied" for a
  restricted role hitting a route directly (not a crash, not a
  logout), and an invalid/expired token correctly redirecting to
  `/login`. Needs `CORS_ALLOWED_ORIGINS=http://localhost:5173` in the
  repo-root `.env` for local dev (see `frontend/README.md`)
- ⬜ Remaining resources: Assets, Risks, Controls/Frameworks, Reports,
  Imports, Evidence, Admin/Org management — each follows the same
  DataTable/hook/page pattern the Vulnerabilities slice established

---

**Current focus:** Phases 1, 2 & 4 complete; Phase 3 largely done
(remaining: object storage + Redis, both blocked on external infra).
Phase 5: remediation workflow + CVE enrichment done; notifications,
scheduled imports, additional frameworks, and SSO remain (each needs
infra/credentials/source data beyond this codebase). Phase 6: first
frontend slice (auth/dashboard/vulnerabilities) done; the remaining
resources are follow-up iterations of the same pattern. Next: the rest
of Phase 5, or the rest of Phase 6.
