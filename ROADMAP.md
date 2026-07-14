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
- ⬜ Follow-ups: per-org control implementation status (join table);
  a bootstrap flow for the first super-admin

## Phase 5 — Workflow, integrations, enrichment ⬜

- ⬜ Remediation workflow: assignee, due date, SLA, evidence attachments
- ⬜ CVE enrichment (`cve_enrichment.py` is a no-op today) via NVD lookup
- ⬜ Notifications (email/webhook): new criticals, SLA breach, import done
- ⬜ Scheduled / API-based imports (Nessus/OpenVAS APIs)
- ⬜ Additional frameworks: PCI DSS, SOC 2, HIPAA, NIST SP 800-53
  (pure data — no code changes required)
- ⬜ SSO (SAML/OIDC)

## Phase 6 — Frontend ⬜

- ⬜ React application consuming the API (design-doc v0.9). Largest single
  effort; unblocks every non-technical persona.

---

**Current focus:** Phases 1, 2 & 4 complete; Phase 3 largely done
(remaining: object storage + Redis, both blocked on external infra).
Next: Phase 5 (workflow/integrations) or Phase 6 (frontend).
