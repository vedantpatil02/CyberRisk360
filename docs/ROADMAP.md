# CyberRisk360 — Industry-Readiness Roadmap

This roadmap turns the MVP backend into a deployable, industry-usable
GRC platform. It complements `TODO.md` (near-term punch list) and
`../PRODUCT_DESIGN_DOCUMENT.md` (§13 release roadmap). Items are ordered by
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
- ✅ `super_admin` now bypasses every `require_role(...)` check
  (`app/dependencies/rbac.py`), not just `/organizations` — previously
  it could only manage orgs and hit the role-check-free
  `/dashboard/overview`, 403ing on every other endpoint since it's
  deliberately excluded from `ALL_ROLES`. Mirrors how
  `tenancy.py`'s `org_scope`/`org_home` and `users.py`'s
  `_get_managed_user` already special-case it (a platform super-admin
  is meant to span every capability, not just tenant management).
  Frontend's `ProtectedRoute`/nav-gating updated to match via a
  `hasRole()` helper
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
  repo-root `.env` for local dev (see `../frontend/README.md`)
- ✅ Assets list + detail, reusing the `DataTable`/hook/page pattern
  unchanged. Confirms the pattern generalizes to per-endpoint RBAC
  that differs *within* one resource: `GET /assets` has no role check
  at all (list route ungated), but `GET /assets/{id}/summary` and
  `.../vulnerabilities` require `admin`/`analyst`/`auditor` (detail
  route gated) — the two aren't the same tier. Detail view is
  necessarily partial: there's no `GET /assets/{id}` on the backend,
  so it shows the severity breakdown + vulnerability list from the
  summary/vulnerabilities endpoints, not the asset's own fields
  (owner/criticality/IP/environment — visible only from the list).
  Verified end-to-end incl. the 404 state for a nonexistent asset
- ✅ Risks list + detail, reusing the `DataTable`/hook/page pattern
  unchanged — simpler than Assets since `GET /risks` and
  `GET /risks/{id}` share one RBAC tier (`admin`/`analyst`/`auditor`)
  rather than splitting across endpoints. `SeverityChip`/`StatusChip`
  generalized (loosened from vulnerability-only prop types to plain
  `string`) to cover `risk_level`/the 3 additional risk statuses
  (`Under Review`/`Mitigated`/`Accepted`) instead of duplicating chip
  markup. No "mapped controls" equivalent — risks don't map to
  compliance controls in this schema, so that section is simply
  absent rather than stubbed. Verified end-to-end incl. the 404 state
- ✅ Frameworks list + detail — the first resource that genuinely
  doesn't fit the `DataTable` pattern: none of `GET /frameworks`,
  `.../summary`, `.../gaps` support server-side pagination/sort/
  filter, so this uses plain MUI tables instead (matching
  `DashboardPage`'s precedent) rather than faking a contract the
  backend doesn't offer. Detail page shows the framework's real
  compliance posture (`vulnerability_coverage_score` + controls
  split into with/without-coverage) via `.../gaps` — deliberately no
  per-control drill-down page, since no endpoint exposes one
  framework's controls with full description/priority/guidance (`GET
  /controls` is all 465 controls, unfiltered and unpaginated, with no
  way to resolve a control back to its framework). "Not found" is
  inferred from `total_controls === 0` since neither endpoint 404s
  for an unknown short_name. Verified end-to-end incl. that state
- ✅ Reports — landing page (Executive Summary, Technical Vulnerability,
  and a framework picker for Compliance Assessment) plus one page per
  report type, rendering the JSON envelope from Phase 1's `/reports/*`
  as stat cards/tables, with an authenticated PDF-download control
  (blob-fetch + synthetic link, since a plain `<a href>` can't carry
  the JWT). Verified end-to-end incl. all three report types, PDF
  download, and the 404 state for an unknown compliance framework
- ✅ Full CRUD for Vulnerabilities/Assets/Risks/Frameworks — Create/
  Update UI (+ Delete for Frameworks, the only one the backend
  supports it for) added to every existing resource, closing the
  "every module needs Create/Update/Delete" gap for resources that
  previously had only read-only list+detail views. Required one small
  backend addition (`GET`/`PUT /assets/{id}`, the one resource missing
  update entirely). No delete added for Vulnerabilities/Assets/Risks —
  deliberate (no backend support, a real retention/compliance decision
  not made yet), not an oversight. See `CHANGELOG.md` (`v1.1-alpha2`)
- ✅ Remaining resources: Imports, Evidence, Admin/Org management —
  plus the previously-unsurfaced Executive/GRC dashboards and the
  mapping review workflow, found via a full frontend-vs-backend audit.
  See `CHANGELOG.md` ("Phase 6 completion — Frontend gap-fill"). Every
  backend endpoint that existed before this now has a UI; `GET /users`
  and `PATCH /users/{id}/role` were added as the two backend gaps the
  audit surfaced. 251 -> 265 tests (incl. v1.2-alpha1 CISA KEV work
  landing in between)

---

**Current focus:** Phases 1, 2, 4 & 6 complete; Phase 3 largely done
(remaining: object storage + Redis, both blocked on external infra).
Phase 5: remediation workflow, CVE enrichment, and (as of v1.2-alpha1)
CISA KEV done; notifications' email/webhook target, scheduled imports,
additional frameworks, and SSO remain (each needs infra/credentials/
source data beyond this codebase). Phase 6: every resource has full
CRUD and every backend endpoint has a UI (Imports/Evidence/Admin/Org/
GRC+Executive dashboards/Mapping review all closed out in one gap-fill
sprint - see `CHANGELOG.md`). Next:
the rest of Phase 5, or the rest of Phase 6 — or, as of the v1.1+
roadmap below, one of that roadmap's sprints.

---

# v1.1+ — Enterprise GRC Roadmap

Layered on top of the phased roadmap above per explicit direction: a
multi-version enterprise roadmap (v1.1 GRC Core through v3.0 AI
Platform) comparable in scope to ServiceNow GRC/Archer/Drata/Vanta/
Tenable One/Microsoft Defender Exposure Management. Worked one sprint
at a time (see `TODO.md`'s Done section for the current state) —
this section tracks which v1.1+ items are net-new versus already
satisfied by a Phase above, so nothing gets tracked (or built) twice.

## v1.1 — GRC Core

- Risk Register — already exists (Phase 1-era `risks` table + list/
  detail API + Phase 6 frontend view). Not re-implemented.
- ✅ **Risk Treatment Workflow** (Mitigate/Accept/Transfer/Avoid) +
  **Risk Approval Workflow** — Sprint 1, see `CHANGELOG.md`
  (`v1.1-alpha1`) and `workflow.md` for the full design. Adds
  `treatment_type`/`approval_status`/`approved_by`/`approved_at` to
  `Risk` plus a `risk_treatment_history` table; `COMPLIANCE_ROLES`
  propose, `OVERSIGHT_ROLES` approve/reject (separation of duties).
  First create/mutate UI in the frontend.
- Evidence Management — already exists (Phase 5's
  `evidence_attachments` table + upload/list/download/delete API).
  Not re-implemented.
- ✅ **Audit Management** — Sprint 3, see `CHANGELOG.md`
  (`v1.1-alpha3`). `Audit`/`AuditFinding` — a genuinely net-new GRC
  "audit engagement" entity (scope, schedule, findings), not to be
  confused with the existing `audit_logs` activity trail. Full CRUD +
  close lifecycle + findings; `OVERSIGHT_ROLES` write, `READ_ROLES`
  read. Frontend list+detail+create+edit+close matching the Risks
  pattern exactly.
- ✅ **Control Review Workflow** — Sprint 4, see `CHANGELOG.md`
  (`v1.1-alpha4`). `ControlReview` — an audit trail (reviewer, previous/
  new status, notes) layered on top of the existing global
  `Control.status` field. Deliberately does not touch the separately-
  deferred per-org control-status join table (Phase 4's flagged
  follow-up, still open — a distinct, larger change). Coexists with
  the pre-existing status-only `PATCH` endpoint rather than replacing
  it. `COMPLIANCE_ROLES` submit, `READ_ROLES` read. Surfaced on
  `FrameworkDetailPage`'s control tables — no standalone Controls page
  exists in this app.
- ✅ **Evidence Expiry & Notifications** — Sprint 5 (final v1.1 sprint),
  see `CHANGELOG.md` (`v1.1-alpha5`). Per explicit user choice: in-app
  notification list only. `expires_at` on evidence attachments;
  `GET /notifications` computed live at read time (no background job —
  none exists in this codebase, same technique as `sla_breached`);
  `NotificationBell` in the frontend header. Found and fixed a real
  pre-existing bug along the way (evidence upload crashed for a
  super-admin — wrong tenancy dependency used for the write).

## v1.1 — GRC Core: ✅ complete

All five sprints done: Risk Treatment + Approval Workflow, Frontend CRUD
Completion, Audit Management, Control Review Workflow, Evidence Expiry &
Notifications. 196 → 251 backend tests across the version. Next up:
v1.2 — Vulnerability Intelligence.

## v1.2 — Vulnerability Intelligence

- CVE Enrichment — already exists (Phase 5, real NVD lookup).
- ✅ **CISA KEV Integration** — Sprint 1, see `CHANGELOG.md`
  (`v1.2-alpha1`). New `CisaKevEntry` cache table (whole-catalog
  fetch/replace, 24h TTL, lazy refresh — no scheduler needed) +
  `GET /vulnerabilities/{id}/kev-status`; frontend badge on
  `VulnerabilityDetailPage`. Verified end-to-end against the live CISA
  feed (`CVE-2021-44228`).
- ✅ **EPSS Integration** — Sprint 2, see `CHANGELOG.md`
  (`v1.2-alpha2`). New `EpssScoreCache` table (per-CVE, 24h TTL even on
  success since EPSS is recomputed daily — the one divergence from the
  NVD cache's "trust forever" model) + `GET
  /vulnerabilities/{id}/epss-score`; frontend field on
  `VulnerabilityDetailPage`. Verified end-to-end against the live
  FIRST.org feed (`CVE-2021-44228` → 100.00%).
- ✅ **CWE Mapping** — Sprint 3, see `CHANGELOG.md` (`v1.2-alpha3`). A
  curated static catalog (real MITRE text, no live API — CWE
  definitions barely change) + `GET /vulnerabilities/{id}/cwe-info`,
  resolving via NVD enrichment's already-cached `cwe_id` (previously
  fetched and discarded) or the mapping engine's own regex extraction.
  Frontend field on `VulnerabilityDetailPage`. Verified end-to-end
  (`CVE-2021-44228` → `CWE-20`, via the real NVD API).
- ✅ **CAPEC + MITRE ATT&CK Mapping** — Sprint 4, see `CHANGELOG.md`
  (`v1.2-alpha4`). Delivered together as anticipated: MITRE's own CAPEC
  data links both a CWE and (where mapped) an ATT&CK technique, so one
  curated catalog (`capec_catalog.json`) covered both roadmap items —
  no separate ATT&CK ingestion. Extends `GET
  /vulnerabilities/{id}/cwe-info` with a `capec` key rather than a new
  endpoint. Verified end-to-end for both the empty- and populated-
  `attack_techniques` cases.
- ✅ **ExploitDB Lookup** — Sprint 5, see `CHANGELOG.md`
  (`v1.2-alpha5`). New `ExploitDbEntry` cache table (same whole-
  catalog-with-TTL shape as CISA KEV, one row per (cve_id, exploit_id)
  pair) + `GET /vulnerabilities/{id}/exploits`; frontend table section
  on `VulnerabilityDetailPage`. Verified end-to-end against the live
  GitLab-hosted CSV (`CVE-2021-44228` → 3 real exploits).
- ⬜ business-aware Risk Scoring (CVSS + EPSS + asset criticality +
  exposure + business impact + existing controls) — not started. The
  last open item in v1.2; every input it needs now exists (EPSS/KEV/
  CWE/CAPEC/ATT&CK/ExploitDB all landed this version).

## v1.3 — Enterprise Risk Management

- ⬜ Business Risk Register, Threat Catalog, Likelihood Matrix, Impact
  Matrix, Residual Risk, Risk Heatmap, Risk Trends, Business Impact
  Analysis — not started.

## v1.4 — Governance

- ⬜ Policy Management, Policy Versioning, Exception Management, Risk
  Acceptance Workflow (distinct from this sprint's Risk Approval
  Workflow — that's per-risk treatment sign-off; this would be a
  standing policy-level acceptance record), Vendor Risk Management,
  Third-party Assessment, Audit Scheduling, Evidence Review — not
  started.

## v1.5 — Compliance Automation

- Cross-Framework support for NIST CSF/OWASP ASVS/OWASP Top 10 —
  already exists (Phase 5-era framework population, real official
  control data). PCI DSS/SOC 2/HIPAA/NIST 800-53 — deferred (Phase 5,
  needs real control text sourced from the standards). CIS Controls
  v8/ISO 27001 — populated as 2-item placeholders only, blocked on
  licensing (CC BY-NC-ND / full copyright — see `CHANGELOG.md`).
- ⬜ Cross-Framework Mapping (as a first-class feature, not just
  shared `mapping_rules.json` matching), Compliance Score / Gap
  Analysis / Control Effectiveness / Compliance Trends beyond what
  `analytics/compliance.py` and `analytics/gap_analysis.py` already
  compute, Continuous Compliance — not started.

## v2.0 — Enterprise Platform

- PostgreSQL, Docker — already exist (Phase 3-era `DATABASE_URL`
  support, `docker-compose.yml`, unverified in this sandbox — no
  Docker daemon access — see `TODO.md`).
- ⬜ Redis, Celery, Kubernetes, Elasticsearch, RabbitMQ, SAML/OIDC/
  Azure AD/Okta/LDAP, and every named scanner/SIEM/cloud integration
  (Nessus/OpenVAS/Qualys/Rapid7/Burp Suite/Nmap/QRadar/Splunk/
  Sentinel/Wazuh/DefectDojo, AWS/Azure/GCP) — not started. Nessus file
  *import* (PDF/CSV/`.nessus` XML) already exists (Phase 1-era) but
  that's a different thing than a live Nessus API integration.

## v3.0 — AI Platform

- ⬜ AI Risk Advisor, AI Control Mapping, AI Compliance Advisor, AI
  Report Generator, AI Attack Path Analysis, AI Executive Assistant —
  not started.
