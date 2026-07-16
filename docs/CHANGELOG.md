## v1.2-alpha5

Sprint 5 of v1.2 "Vulnerability Intelligence": **ExploitDB Lookup**.
Network access confirmed via a direct `curl` before committing: the
GitHub `offensive-security/exploitdb` repo's raw CSV path 404s (a stub
redirect, flagged in an earlier session), but the real GitLab mirror
(`gitlab.com/exploit-database/exploitdb`) works.

### Added
- `ExploitDbEntry` model (table `exploitdb_entries`) - same whole-
  catalog-cache-with-TTL shape as CISA KEV (Exploit-DB publishes one
  bulk CSV, ~10MB/47,108 rows, no per-CVE endpoint), but one row per
  (`cve_id`, `exploit_id`) **pair**, not one row per CVE - a CVE can
  have multiple exploits and a single Exploit-DB row can list multiple
  CVEs. Only the ~27,402 rows that reference at least one real CVE are
  cached (the other ~20k reference OSVDB/BID/etc only, which this
  system has no use for). Migration `1bb9ebeab100`.
- `app/services/enrichment/exploitdb.py` - fetches and parses the whole
  CSV (retry/backoff mirroring `cisa_kev.py`, `timeout=60` for the
  larger payload), `CATALOG_TTL` 24h, full-replace on refresh (same
  reasoning as KEV: correctly drops anything Exploit-DB removes,
  simpler than diffing).
- `GET /vulnerabilities/{id}/exploits` (`admin`/`analyst`/`auditor` -
  same tier as the sibling KEV/EPSS/CWE routes). Returns `[]`
  immediately, no network call, when the vulnerability has no `cve_id`.
- `app/tests/test_exploitdb.py` (12 tests): no-cve_id short-circuit,
  fresh/stale cache, full-replace-on-refresh, a CVE with multiple
  exploits, a CSV row listing multiple CVEs correctly exploded to each,
  rows without any CVE never cached, retry-then-succeed, network-
  failure-falls-back-to-existing-cache, endpoint found/404/RBAC.
  289 -> 301 tests.
- Frontend: a new "Public Exploits (Exploit-DB)" **table section** on
  `VulnerabilityDetailPage` (a list, not a scalar value like KEV/EPSS/
  CWE, so a dedicated table matching "Mapped Controls" rather than a
  `Field`) - Exploit ID (linked), Title, Type, Platform, Verified,
  Published; "No known public exploits." when empty.

### Verified
- Full backend suite green (301/301). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough against the **live** GitLab-hosted
  CSV (not mocked): vulnerability #1 (`CVE-2021-44228`) correctly shows
  all 3 real linked exploits (`51183`, `50592`, `50590`, matching
  exactly what was found during planning) with correct titles/dates/
  links; a vulnerability with no `cve_id` shows no Exploits section at
  all. Zero console errors either way. The live fetch+parse of the full
  ~10MB CSV took ~6 seconds - acceptable for a lazy refresh that happens
  at most once per 24h.

## v1.2-alpha4

Sprint 4 of v1.2 "Vulnerability Intelligence": **CAPEC + MITRE ATT&CK
Mapping**, delivered as one sprint (as anticipated in the CWE Mapping
sprint's own plan) - MITRE's own CAPEC data already links both a CWE
and, where mapped, an ATT&CK technique, so no separate ATT&CK
ingestion was needed. No external network dependency, same reasoning
as CWE Mapping - a small curated static catalog, not a live fetch.

### Added
- `backend/frameworks/common/capec_catalog.json` (new) - verified
  against the official MITRE CAPEC catalog
  (`capec.mitre.org/data/csv/1000.csv.zip`, the 559-pattern
  "Mechanisms of Attack" view, confirmed reachable). One representative
  CAPEC attack pattern per CWE already in `cwe_catalog.json` (11
  entries, same curated scoping), each with its real MITRE ATT&CK
  technique(s) where one exists - honestly `[]`, not padded, for the 7
  of 11 that genuinely have no ATT&CK linkage in MITRE's own data.
- `app/services/enrichment/capec_catalog.py::get_capec_for_cwe(cwe_id)`
  - loads the catalog via the same `load_framework()` reuse as
    `cwe_catalog.py`; computes CAPEC/ATT&CK definition URLs
    deterministically (MITRE's real sub-technique URL scheme: `T1110.001`
    -> `.../techniques/T1110/001/`).
- `GET /vulnerabilities/{id}/cwe-info` gains a `capec` key (backward-
  compatible addition, not a new endpoint - CAPEC is a natural
  extension of "given this CWE, what's the attack pattern," the same
  lookup this endpoint already does) -
  `{capec_id, name, description, url, attack_techniques: [{id, name,
  url}]}` or `null`.
- `app/tests/test_cwe_mapping.py` (extended, +4 tests): catalog lookup
  (known/unknown CWE, sub-technique URL formatting), endpoint `capec`
  populated with ATT&CK techniques, `capec: null` for the no-CWE and
  uncatalogued-CWE cases. 285 -> 289 tests.
- Frontend: `CweValue` extended to render the CAPEC pattern and any
  ATT&CK technique(s) as more inline `<Link>`s next to the CWE link -
  `CWE-20: ... · Attack Pattern: CAPEC-120: ...` and, when techniques
  exist, `· MITRE ATT&CK: T1548: ...`. Same DOM-nesting-safe approach
  (plain `<a>` elements) as every field added this version.

### Verified
- Full backend suite green (289/289). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough of both paths: vulnerability #1
  (`CWE-20` -> `CAPEC-120` Double Encoding) confirmed the empty-
  `attack_techniques` case renders cleanly with no broken/empty MITRE
  ATT&CK section; a second vulnerability created via the API with
  `CWE-287` in its description (`CAPEC-115` Authentication Bypass ->
  `T1548` Abuse Elevation Control Mechanism) confirmed the populated
  case renders the full CWE -> CAPEC -> ATT&CK chain correctly. Zero
  console errors in both.

## v1.2-alpha3

Sprint 3 of v1.2 "Vulnerability Intelligence": **CWE Mapping**. No
external network dependency - CWE weakness definitions barely change,
so this ships a small curated static reference catalog instead of a
live per-request API call (unlike KEV/EPSS).

### Added
- `backend/frameworks/common/cwe_catalog.json` (new) - real MITRE text
  (verified against the official CWE CSV catalog,
  `cwe.mitre.org/data/csv/2000.csv.zip`, confirmed reachable) for the
  11 CWE IDs already referenced across this codebase's 5 existing
  `mapping_rules.json` files. First real use of the `frameworks/
  common/` directory - `categories.json`/`severity_weights.json` sit
  there too but were never actually loaded by any code.
- `app/services/enrichment/cwe_catalog.py::get_cwe_info(cwe_id)` -
  loads the catalog via the existing `framework_loader.load_framework()`
  utility (reused, not duplicated).
- `GET /vulnerabilities/{id}/cwe-info` (`admin`/`analyst`/`auditor` -
  same tier as `/kev-status`/`/epss-score`). Resolves a CWE two ways:
  (1) the authoritative `cwe_id` NVD enrichment already caches per CVE
  (previously fetched and immediately discarded - only ever used to
  backfill a missing description) via `nvd_cache_repository
  .get_cache_entry()`, or (2) falling back to the mapping engine's own
  `CWE-\d+` regex extraction from title/description (`mapping_engine
  .extract_cwe_ids` - renamed from `_extract_cwe_ids` since it now has
  a second caller) - the same value the mapping engine itself already
  matches control mappings against. A real-but-uncatalogued CWE id
  still returns its definitive `cwe.mitre.org` URL rather than being
  hidden or given a fabricated name.
- `app/tests/test_cwe_mapping.py` (10 tests): catalog lookup,
  NVD-cache resolution (incl. preferring it over the regex fallback,
  and ignoring a `status="failed"` entry), regex fallback, no-CWE-
  found, real-but-uncatalogued CWE, 404, RBAC. 275 -> 285 tests.
- Frontend: a "Weakness (CWE)" field next to CVSS/EPSS Score on
  `VulnerabilityDetailPage`, linking out to the CWE's official
  definition page with a tooltip description. Rendered as a plain
  `<Link>` (an `<a>`, not a `<Chip>`) so it goes through the ordinary
  `Field` component safely - third sprint in a row avoiding Sprint 1's
  `<div>`-in-`<p>` DOM-nesting bug class.

### Verified
- Full backend suite green (285/285). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough: triggered the existing (already
  real) `POST /vulnerabilities/{id}/enrich-cve` on vulnerability #1
  against the live NVD API, confirmed it cached `CWE-20` (Improper
  Input Validation) for `CVE-2021-44228` - genuinely different from
  this plan's own guess of CWE-502, underscoring why the value comes
  from the real cache rather than being hardcoded - then confirmed the
  Weakness field renders that exact value with zero console errors.

## v1.2-alpha2

Sprint 2 of v1.2 "Vulnerability Intelligence": **EPSS Integration**.
Network access to `api.first.org` confirmed reachable before committing
to this plan (verified via a direct `curl`, not assumed).

### Added
- `EpssScoreCache` model (table `epss_score_cache`) - one row per CVE:
  `cve_id` (unique/indexed), `epss_score`, `percentile`, `score_date`
  (informational), `status` (`"ok"`/`"failed"`), `fetched_at`.
  Migration `65fe339a2f7c`.
- `app/services/enrichment/epss_enrichment.py` - per-CVE lookup against
  FIRST.org's EPSS API (`?cve={id}`), unlike CISA KEV's whole-catalog
  fetch - structurally the same shape as the existing NVD lookup
  (`cve_enrichment.py`), which this mirrors closely (same retry/backoff:
  3 attempts, exponential backoff, retry on timeout/connection-error/
  5xx/429). One deliberate divergence from NVD: EPSS scores are
  recomputed daily, so even a `status="ok"` cache entry expires after a
  24h `SCORE_TTL` and is re-fetched - NVD's CVSS/CWE/description data is
  immutable once published and is trusted forever.
- `GET /vulnerabilities/{id}/epss-score` (`admin`/`analyst`/`auditor` -
  same tier as the sibling `/kev-status` route). Returns
  `{epss_score: null, percentile: null, date: null}` immediately, with
  no network call, when the vulnerability has no `cve_id`.
- `app/tests/test_epss_enrichment.py` (10 tests): no-cve_id short-
  circuit, fresh-cache-skips-refetch, stale-cache-triggers-refetch,
  not-found (empty `data`), retry-then-succeed, network-failure-falls-
  back-to-cached-failure, endpoint found/no-cve_id/not-found/RBAC.
  265 -> 275 tests.
- Frontend: an "EPSS Score" field next to CVSS Score on
  `VulnerabilityDetailPage`, with a tooltip surfacing the percentile
  rank and score date. Only fetches when the vulnerability has a
  `cve_id`, same `enabled` gate as the KEV badge. Deliberately rendered
  as a plain `<Tooltip><span>...</span></Tooltip>` (not a `Chip`) so it
  goes through the ordinary `Field` component without hitting Sprint
  1's `<div>`-in-`<p>` DOM-nesting bug class again.

### Verified
- Full backend suite green (275/275). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough against the **live** FIRST.org feed
  (not mocked): reused vulnerability #1 (`cve_id` = `CVE-2021-44228`
  from Sprint 1's verification), confirmed the EPSS Score field renders
  `100.00%` with the correct tooltip and zero console errors.

## Phase 6 completion — Frontend gap-fill

User-requested audit of the frontend surface against the backend API
found 8 features that were fully backend-ready but had zero UI: evidence
management, user registration, self-service password change, admin user
management (which also needed two new backend endpoints - no `GET
/users` or role-change endpoint existed at all), the GRC and Executive
dashboards, organization (tenant) management, the vulnerability-control
mapping review workflow, and scan-report imports. All eight built and
verified end-to-end in the same sprint.

### Added
- **Evidence management UI**: upload (with optional expiry), list,
  download, and delete, via a shared `EvidenceSection` component wired
  into both `VulnerabilityDetailPage` and `RiskDetailPage`. Uses the
  backend's generic `WRITE_ROLES`/`READ_ROLES` (not the narrower
  per-resource write-role tuples) - a pentester can attach remediation
  evidence without being able to create/edit the vulnerability or risk
  itself.
- **Backend**: `GET /users` (org-scoped, admin-only) and
  `PATCH /users/{id}/role` (admin-only) - neither existed before this;
  a real User Management UI needed a way to list users and change
  roles that the API never exposed. New `ACTION_USER_ROLE_CHANGE` audit
  action. 6 new tests. 260 -> 265 tests.
- **User/Account Management page** (`/users`, admin-only): list, change
  role, activate/deactivate, reset password. `RegisterPage` (`/register`,
  public) and `AccountPage` (`/account`, self-service password change)
  round out the account lifecycle that previously had no UI beyond
  Login.
- **Executive Dashboard** (`/executive-dashboard`) and **GRC Dashboard**
  (`/grc-dashboard`, per-framework via a picker) - both `GET
  /dashboard/executive` and `GET /dashboard/grc/{framework}` existed
  since Phase 5/6 analytics work but were never surfaced.
- **Organizations page** (`/organizations`, super-admin only): list and
  create tenant organizations.
- **Mapping Review page** (`/mappings/review`): the pending
  vulnerability-control mapping queue (approve/reject with an optional
  note), previously only reachable via raw API calls despite being a
  core part of the mapping engine's design (manual review of
  auto-suggested mappings). Read-only for auditor; approve/reject
  restricted to admin/analyst, matching the backend exactly.
- **Import Report page** (`/imports`): upload a Nessus CSV/XML or PDF
  report, surfacing the parse + dedupe/import summary. The importer
  pipeline (Phase 5-era) had zero frontend since it shipped.
- Nav drawer gained 6 new role-gated entries (Users, Organizations,
  Executive Dashboard, GRC Dashboard, Mapping Review, Import Report)
  and an account-icon button in the header linking to `/account`.

### Fixed (found via manual verification, not introduced this sprint)
- The Users page's role `<Select>` rendered blank for a `super_admin`
  row, since `super_admin` is deliberately excluded from the
  assignable-roles list (backend `VALID_ROLES` = `ALL_ROLES`, a
  platform role can't be assigned via this endpoint) - its current
  value didn't match any `MenuItem`. Fixed by rendering a plain,
  non-editable chip for that one case instead of a broken-looking
  empty dropdown.

### Verified
- Full backend suite green (265/265). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough of all 8 new pages plus the evidence
  sections on both detail pages, zero console errors throughout
  (including after the role-`Select` fix above).

## v1.2-alpha1

Sprint 1 of v1.2 "Vulnerability Intelligence": **CISA KEV Integration**.
Network access to `www.cisa.gov` confirmed reachable before committing to
this plan (verified via a direct `curl`, not assumed).

### Added
- `CisaKevEntry` model (table `cisa_kev_entries`) - one row per catalog
  entry: `cve_id` (unique/indexed), `vulnerability_name`, `date_added`,
  `due_date`, `required_action`, `known_ransomware_use`
  (`knownRansomwareCampaignUse` - `"Known"`/`"Unknown"`), `notes`,
  `fetched_at`. Migration `d47a9c3e6f18`.
- `app/services/enrichment/cisa_kev.py` - fetches the whole CISA KEV
  bulk JSON feed (single feed, ~1,400+ CVEs, no per-CVE endpoint -
  structurally different from the existing per-CVE NVD/plugin
  enrichment pattern), caches it locally, refreshes lazily on the next
  lookup once stale (24h TTL, no scheduler needed). Retry/backoff
  mirrors `cve_enrichment.py::_fetch_cve` (3 attempts, exponential
  backoff). `replace_catalog()` does a full replace on refresh, not a
  diff/upsert - correctly handles CISA removing an entry over time for
  free.
- `GET /vulnerabilities/{id}/kev-status` (`admin`/`analyst`/`auditor` -
  same tier as the sibling `/controls` and `/suggested-controls`
  routes on this resource). Returns `{in_kev: false}` immediately, with
  no network call, when the vulnerability has no `cve_id`.
- `app/tests/test_cisa_kev.py` (9 tests): no-cve_id short-circuit,
  fresh-cache-skips-refetch, stale-cache-triggers-refetch, empty-cache
  fetch, retry-then-succeed, network-failure-falls-back-to-existing-
  cache, endpoint found/not-found/RBAC. 251 -> 260 tests.
- Frontend: a "CISA Known Exploited" badge next to the CVE ID field on
  `VulnerabilityDetailPage`, with a tooltip surfacing known-ransomware-
  use and CISA's remediation due date. Only fetches when the
  vulnerability has a `cve_id` (`enabled` gate on the query, mirroring
  the backend's own short-circuit) - no visual noise or extra request
  for the common case.

### Fixed (found via manual verification, not introduced this sprint)
- The CVE ID field's badge (a `Chip` inside a `Tooltip`, both rendering
  `<div>`s) was placed inside the shared `Field` helper's
  `<Typography variant="body2">` wrapper, which renders a `<p>` -
  producing invalid `<p><div>...</div></p>` DOM nesting and a React
  `validateDOMNesting` console warning. Caught by a real headless-
  browser walkthrough against the live CISA feed, not by `tsc`/`eslint`
  (both were clean). Fixed by giving the CVE ID row its own Grid cell
  (matching how Severity/Status already avoid the generic `Field`
  helper for non-plain-text values) instead of routing the badge
  through `Field`'s `value` prop.

### Verified
- Full backend suite green (260/260). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough against the **live** CISA KEV feed
  (not mocked): set a dev-DB vulnerability's `cve_id` to
  `CVE-2021-44228` (Log4Shell, confirmed via direct `curl` to still be
  in the live catalog), opened its detail page, confirmed the badge
  renders with correct tooltip content and zero console errors after
  the DOM-nesting fix above.

## v1.1-alpha5

Sprint 5 (final) of v1.1 "GRC Core": **Evidence Expiry & Notifications**
- **v1.1 is now fully complete.** Per explicit user direction: in-app
notification list only (no email/webhook - no SMTP/receiving-endpoint
credentials available; no new background-job infra - no Celery/
APScheduler in this codebase).

### Added
- `expires_at` (nullable) on `EvidenceAttachment` - optional at upload
  time, no expiry by default. Migration `c92e4f018a5d`.
- Both evidence upload routes (`POST /vulnerabilities/{id}/evidence`,
  `POST /risks/{id}/evidence`) gain an optional `expires_at` form
  field alongside the file.
- `app/analytics/notifications.py::get_notifications` - computed
  **live at read time**, never stored, same "always fresh" technique
  already used for SLA breach (`is_sla_breached`). Buckets evidence
  into `evidence_expired` (past due) and `evidence_expiring_soon`
  (within 30 days), sorted soonest-first.
- `GET /notifications` (`READ_ROLES` - visible to any authenticated
  user, same tier as Dashboard/Reports).
- `app/tests/test_notifications.py` (6 tests): expired/expiring-soon/
  far-future/no-expiry buckets, org isolation, sort order. 244 -> 250
  tests.
- Frontend: `NotificationBell` (badge + dropdown menu) in the app
  header - first use of MUI `Menu`/`Badge` in this codebase, same
  "first use of a standard primitive" tier as last sprint's
  `stopPropagation()`. Polls every 60s (`refetchInterval`) - no
  WebSocket/push infra needed for this scope. No frontend Evidence-
  upload module exists yet (separately flagged, larger future Phase 6
  item) - this sprint's frontend piece is the bell itself, which works
  correctly today against evidence created via the API regardless.

### Fixed (found via manual verification, not introduced this sprint)
- **Real bug**: `POST /risks/{id}/evidence` and
  `POST /vulnerabilities/{id}/evidence` stamped new rows' `org_id` from
  `org_scope` (which is `None` for a super-admin - "no read filter"),
  not `org_home` (always a concrete org - "write under your own org"),
  the convention every other create endpoint in this codebase already
  follows correctly (e.g. `POST /risks`). This crashed with a `NOT
  NULL constraint failed: evidence_attachments.org_id` the moment a
  super-admin tried to upload evidence - caught by manually exercising
  the exact feature this sprint touches, not by the test suite (no
  existing test uploaded evidence as a super-admin). Fixed both
  routes; added `test_super_admin_can_upload_evidence` regression
  test. 250 -> 251 tests.
- **Test-suite flakiness**: the shared, process-wide `slowapi` rate
  limiter (100/minute, previously reset only via an opt-in
  `reset_rate_limiter` fixture that most test files never requested)
  started failing unrelated tests once this sprint's added request
  volume pushed the full suite's cumulative count over the shared
  budget within the same 60-second window - reproduced by running the
  full suite (passed in isolation per-file). Fixed by resetting the
  limiter in the `client` fixture itself (used by every test), removing
  the shared budget entirely instead of relying on each new test file
  to opt in - a fix that scales as the suite keeps growing, not just a
  patch for this sprint's specific tests.

### Verified
- Full backend suite green (251/251). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough: uploaded evidence with a past
  `expires_at` via a direct API call, confirmed it appeared in the
  notification bell with the correct badge count and message in a live
  browser session - zero console errors.

### Deferred (explicitly, not silently dropped)
- Dismiss/read-state for notifications (currently always-fresh/
  always-shown, matching `sla_breached`'s philosophy).
- A real scheduler + email/webhook notification target, if ever
  needed - would need SMTP credentials or a receiving endpoint the
  user would have to provide.

## v1.1-alpha4

Sprint 4 of v1.1 "GRC Core": **Control Review Workflow** - a formal,
auditable review event for a control's implementation status (who
reviewed it, when, what changed, why), layered on top of the existing
global `Control.status` field. Explicitly does not touch the separately-
deferred "per-org control implementation status" join table
(`docs/ROADMAP.md` Phase 4) - that's a distinct, larger architectural
change, not part of this sprint.

### Added
- `ControlReview` model (`control_id` FK, `reviewer` string from the
  JWT - same convention as `MappingHistory.actor`, `previous_status`,
  `new_status`, `notes`, `org_id`, `reviewed_at`). Migration
  `f8b12d6e4a91`, verified round-trip.
- `POST /controls/{id}/review` (`COMPLIANCE_ROLES` - admin/analyst/
  grc_analyst, an exact match for that group's own documented purpose)
  and `GET /controls/{id}/reviews` (`READ_ROLES`). Coexists with the
  pre-existing `PATCH /controls/{id}/status` (unchanged, no trail) -
  the new endpoint is a superset, not a replacement, preserving
  backward compatibility.
- `app/services/controls/control_review.py::submit_review` - snapshots
  the previous status, applies the new one via the existing
  `update_control_status`, records the review. Plain history listing
  stays a direct repository call from the API layer.
- `analytics/gap_analysis.py::get_framework_gaps`: added `id` (the
  control's numeric PK) and `status` to each control's row - both
  needed to make a review action possible from `FrameworkDetailPage`
  at all, since neither was previously exposed there. Additive,
  backward-compatible (extra dict keys, nothing removed/changed).
- `app/tests/test_control_review.py` (6 tests): submit review changes
  the control's actual status, history ordering, RBAC denial, 404s.
  238 -> 244 tests.
- Frontend: no standalone Controls page exists in this app (`GET
  /controls` is all 465 controls, unfiltered) - the natural, already-
  existing integration point is `FrameworkDetailPage`'s two
  `ControlsTable`s, which gain a Status column and a per-row inline
  "Review" toggle (status select + notes field), gated to
  `CONTROL_REVIEW_ROLES`.

### Verified
- Full backend suite green (244/244). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough: opened a framework, submitted a
  review changing `CIS-1` from `Missing` to `Implemented`, confirmed
  the Status column updated live - zero console errors.

## v1.1-alpha3

Sprint 3 of v1.1 "GRC Core": **Audit Management** - a GRC audit
engagement entity (scope, schedule, findings), confirmed net-new in
earlier research (distinct from the pre-existing `audit_logs` activity
trail).

### Added
- `Audit` (`title`, `framework_id` FK nullable, `lead_auditor_id` FK
  nullable - same convention as `Risk.assignee_id`, `scope`, `status`
  Planned/In Progress/Completed/Closed, `start_date`/`end_date`,
  `org_id`, timestamps) and `AuditFinding` (`audit_id` FK, `control_id`
  FK nullable, `title`, `description`, `severity`, `status`
  Open/Remediated/Accepted/Closed) models. Migration `a3f7c2e91b4d`,
  verified round-trip.
- `POST/GET/PUT /audits`, `GET /audits/{id}`, `PATCH
  /audits/{id}/close`, `POST/GET /audits/{id}/findings`, `PUT
  /findings/{id}`. Write (create/update/close audits, create/update
  findings) = `OVERSIGHT_ROLES` (admin/auditor/ciso/manager - audits
  are fundamentally an oversight function); read = `READ_ROLES` (all 7
  roles), matching Reports' precedent.
- `app/schemas/audit_engagement.py` (not `audit.py` - that name was
  already taken by the unrelated `AuditLogOut` response schema for the
  generic activity trail; naming collision caught and avoided during
  implementation, not after).
- Plain CRUD calls the repository directly from the API layer (same
  convention as `api/risks.py`); a thin `audit_workflow.py` service
  handles the two pieces of real logic (closing, finding-status
  changes), same justification as the Risk Treatment sprint's
  `risk_treatment.py`.
- No delete on either entity - same principle as Risk/Vulnerability/
  Asset, doubly so for an audit record specifically.
- `app/tests/test_audits.py` (20 tests): CRUD, close (incl. "already
  closed" 400), findings CRUD, RBAC denial, cross-org isolation.
  218 -> 238 tests.
- Frontend: `AuditsListPage`/`AuditDetailPage`, following the exact
  list+detail+create+edit+close shape established for Risks, plus a
  Findings sub-table with an inline add-finding form and a per-finding
  status dropdown gated the same way. New "Audits" nav item.

### Verified
- Full backend suite green (238/238). `tsc -b`/`vite build`/`eslint`
  clean. Real browser walkthrough: create an audit, edit it, add a
  finding, mark it Remediated, close the audit - zero console errors.

## v1.1-alpha2

Frontend CRUD completion: every existing resource (Vulnerabilities,
Assets, Risks, Frameworks) gains Create/Update UI (Delete too for
Frameworks, the only one the backend supports it for), closing out the
"every module needs List/Detail/Create/Update/Delete/Search/Filtering/
Pagination/RBAC/Loading/Error/Empty" requirement for the resources that
already existed on the frontend. Imports/Evidence/Admin/Org-management
remain a separate follow-up (net-new modules, not a gap in existing ones).

### Added
- **Assets**: the one real backend gap - no `GET /assets/{id}`, no
  update at all. Added `GET /assets/{id}` and `PUT /assets/{id}`
  (`app/schemas/asset_update.py::AssetUpdate`,
  `asset_repository.py::update_asset`, both `admin`/`analyst` on write,
  matching `POST /assets`'s existing tier) - both registered *after*
  the fixed `/assets/risk-summary` path, since this router (like
  `vulnerabilities.py`) doesn't use an explicit `{id:int}` path
  converter and Starlette matches routes in registration order, not by
  segment-count fallback. Caught two real bugs while wiring this up,
  both via the test suite catching them immediately: (1) the ordering
  issue just described, surfaced as `/assets/risk-summary` suddenly
  422ing; (2) `PUT /assets/{id}` returning an emptied object because
  `update_asset()` commits (expiring the ORM instance) without a
  `db.refresh()` before the endpoint returns it directly - the exact
  same bug class already fixed once before for `update_framework`/
  mapping-approve, now fixed the same way here.
- `app/tests/test_assets.py`: 5 new tests for the above (GET/PUT happy
  path, 404s, RBAC denial). 213 -> 218 tests.
- **Frontend**: `create`/`update` (`delete` for Frameworks) functions +
  `*_WRITE_ROLES` constants added to every resource's `api/endpoints/
  *.ts`, one `useMutation`-based hook per action (invalidating the
  resource's query-key prefix, same pattern as last sprint's
  `useProposeTreatment`), and inline toggleable forms wired into each
  List/Detail page - no `Dialog`/modal introduced (still none anywhere
  in this codebase); Frameworks' Edit/Delete live inline per table row
  instead of a separate detail-page round trip, since every editable
  field is already present in the list response. First use of
  `stopPropagation()` in this codebase (needed for the per-row action
  buttons inside the Frameworks table's clickable rows).
- `AssetDetailPage` now also fetches the asset's own fields via the new
  `GET /assets/{id}`, replacing the previous "these fields aren't
  available yet" notice with an actual editable field block - the
  gap flagged as a "real, documented gap, not papered over" in the
  Phase 6 Assets entry is now closed.
- Vulnerabilities and Risks both gained UI for their existing-but-
  previously-unwired `PATCH .../close` endpoint, alongside the new Edit
  forms.
- Deliberately **not added**: delete for Vulnerabilities/Assets/Risks -
  no backend route or repository function exists for any of them, and
  adding one would be a real retention/compliance decision (hard vs.
  soft delete, cascade to evidence/mappings), not a UI gap to close
  silently.

### Verified
- Full backend suite green (218/218). `tsc -b`/`vite build`/`eslint`
  clean. Real end-to-end browser walkthrough: create + edit + close a
  Vulnerability, create + view-own-fields + edit an Asset, create +
  edit + close a Risk, create + inline-edit + delete a Framework - all
  confirmed via live DOM assertions (not just "no crash"), zero
  browser console errors throughout.

## v1.1-alpha1

Sprint 1 of the v1.1 "GRC Core" roadmap: the Risk Treatment + Approval
workflow, plus a documentation restructure.

### Added
- **Risk Treatment workflow** (mitigate/accept/transfer/avoid) +
  **Risk Approval workflow**, layered onto the existing Risk Register
  rather than duplicating its `status` field: `treatment_type` records
  what was proposed, and approval drives `status` to the matching
  terminal value. `Mitigated`/`Accepted` already existed as statuses;
  two new ones were added for the previously-uncovered outcomes -
  `RISK_STATUS_TRANSFERRED`, `RISK_STATUS_AVOIDED` (also added to
  `RISK_TERMINAL_STATUSES` in `app/services/remediation/sla.py`, so a
  transferred/avoided risk stops accruing SLA breach like the other
  terminal states).
  - New `Risk` columns: `treatment_type`, `treatment_justification`,
    `approval_status`, `approved_by`, `approved_at`. New
    `risk_treatment_history` table (mirrors `mapping_history`'s shape
    exactly) recording every proposed/approved/rejected transition.
    Migration `ed54d857372f`, verified round-trip (upgrade/downgrade/
    upgrade) against the real dev database.
  - `POST /risks/{id}/treatment` (propose - `admin`/`analyst`/
    `grc_analyst`, i.e. `COMPLIANCE_ROLES`), `PATCH .../treatment/
    {approve,reject}` (`admin`/`auditor`/`ciso`/`manager`, i.e.
    `OVERSIGHT_ROLES` - deliberately a different tier than propose, so
    a risk owner can't approve their own treatment), `GET .../
    treatment/history` (`READ_ROLES`). Structured like the existing
    vulnerability-control mapping approve/reject workflow
    (`app/services/mapping/mapping_service.py`) - one commit per
    transition pairing the state change with a history row, then a
    separate `record_audit()` call.
  - New `app/services/risks/risk_treatment.py`,
    `app/repositories/risks/risk_treatment_history_repository.py`,
    `app/schemas/risk_treatment.py`. New audit actions
    `risk.treatment_propose`/`_approve`/`_reject`.
  - `app/tests/test_risk_treatment.py` (15 tests): propose (happy
    path, 404, invalid `treatment_type`, RBAC denial, rejected on a
    closed risk), approve (all 4 treatment types map to the correct
    terminal status, RBAC denial, no-pending-treatment conflict),
    reject (reverts to `Open`), and history ordering. 198 -> 213 tests.
  - Frontend: `RiskDetailPage` gained the first create/mutate UI in
    this codebase (every other resource is still read-only) - a
    propose form and an approve/reject form, each gated by
    `hasRole()` against the corresponding role tuple, plus a
    treatment-history table. First use of TanStack Query's
    `useMutation` for a resource (previously only `LoginPage` used
    it) and the first query-invalidation-after-write in the codebase
    (`queryClient.invalidateQueries({ queryKey: ['risks'] })`, which
    covers the detail, every list-page variant, and the history query
    in one call via prefix matching). Verified end-to-end in a real
    browser: propose -> pending (Approve/Reject shown) -> approve ->
    status transitions to `Mitigated`, history shows both rows.
- **Documentation restructure**: moved `ARCHITECTURE.md`,
  `DATABASE.md`, `ROADMAP.md`, `TODO.md`, and this file into `docs/`
  (lowercased `architecture.md`/`database.md` per the new convention),
  fixed every cross-reference repo-wide (backend docstrings, frontend
  README, the ADR's reference list, and the docs' own
  cross-references to each other and to the root-level `README.md`/
  `PRODUCT_DESIGN_DOCUMENT.md`). Added `AI_CONTEXT.md` (agent-
  facing project orientation) and `workflow.md` (living reference
  of every approval-style workflow in the codebase - mapping approval,
  remediation SLA/evidence, and now risk treatment/approval).

## Unreleased

### Added
- **Complete, officially-sourced control data** for 3 of the 5
  compliance frameworks, replacing 2-10 item placeholder samples:
  - **NIST CSF 2.0**: all 106 subcategories across 22 categories/6
    functions (was 10, missing the entire GOVERN function), sourced
    from NIST's own public-domain OSCAL catalog
    (`usnistgov/oscal-content`), including official Implementation
    Example text where NIST provides it (`implementation_guidance`).
    Filtered out ~38 CSF-1.1-era categories/subcategories the source
    file bundles as a withdrawn crosswalk (e.g. legacy `PR.AC`,
    superseded by `PR.AA` in 2.0) - importing them unfiltered would
    have silently doubled the category count with dead 1.1 codes.
  - **OWASP ASVS**: upgraded `v4.0.3` -> **`v5.0.0`** (345
    requirements across 17 chapters, was 2), sourced from OWASP's
    official CSV (CC BY-SA 4.0), including the official Level
    (`priority`: L1/L2/L3) per requirement.
  - **OWASP Top 10 2021**: descriptions replaced with verbatim
    official text (from each category's own `## Description` section,
    CC BY-SA 4.0) - control IDs/titles were already correct; only the
    prior paraphrased descriptions changed.
  - `framework_importer.py`: additive, backward-compatible support
    for optional `priority`/`implementation_guidance` fields on a
    control (existing schema columns, previously always unset).
- 197 -> 198 tests (one assertion updated for NIST 2.0's real category
  codes - see Fixed).

### Fixed
- `mapping_rules.json` for `nist-csf` and `owasp-asvs` retargeted from
  placeholder-era control IDs (`PR.AC-1`, bare `V5`/`V2`) to real ones
  in the new datasets (`PR.AA-01`, `V1.2.1`, etc.) - the old IDs no
  longer exist as real controls, which would have silently stopped
  vulnerability-to-control auto-mapping for both frameworks.
- `test_frameworks.py`/`test_mapping_engine.py`/
  `test_mapping_status_analytics.py`: updated hardcoded old-format
  NIST IDs (`PR.AC-1` -> `PR.AA-01`, `ID.RA-1` -> `ID.RA-01`) to match.

### Not done - blocked on licensing (reported, not fabricated)
- **CIS Controls v8**: still the 2-item placeholder. Licensed CC
  BY-**NC**-**ND** 4.0 - the No-Derivatives clause explicitly
  prohibits distributing a modified/transformed version, which is
  exactly what importing into this DB's schema would be.
- **ISO/IEC 27001:2022 Annex A**: still the 2-item placeholder. Full
  copyright, no redistribution license identified for the standard's
  control text.

## v0.9-alpha1

### Added
- **Multi-tenancy (organizations)** - the platform is now tenant-aware.
  A new `organizations` table is the tenant boundary; `org_id` is added
  to every per-organization table (users, assets, vulnerabilities,
  risks, vulnerability-control mappings, mapping history, audit logs),
  while reference data (frameworks, categories, controls, plugin cache)
  stays a shared global catalog.
- **Row-level org scoping** threaded through every repository, service,
  analytic, dashboard, and report: reads filter to the caller's org and
  writes are stamped with it. Enforced via `app/dependencies/tenancy.py`
  (`org_scope` for reads, `org_home` for writes) driven by an `org_id`
  claim now carried in the JWT.
- **Platform super-admin** (`ROLE_SUPER_ADMIN`) that spans all orgs for
  reads (org filter disabled). Excluded from open-registration roles so
  it can't be self-assigned. New super-admin-only organization API:
  `GET /organizations`, `POST /organizations`.
- Registration assigns users to an org by `org_slug` (default: the
  "default" org). Admin user-management is org-scoped (an org admin
  can't touch another org's users).
- Migration `b7c1a4e9f0d2`: creates `organizations`, seeds a "Default
  Organization", backfills all existing rows to it, then adds the
  NOT NULL `org_id` + FKs (audit_logs' org_id is nullable for org-less
  events like an unknown-email login failure). Uses `batch_alter_table`
  and disables SQLite FK enforcement during the run (env.py) so
  recreating FK-referenced tables succeeds; verified on a populated DB
  copy, forward and reverse.
- `app/tests/test_multitenancy.py` - cross-org isolation (assets/vulns
  invisible across orgs, cross-org detail 404s, super-admin sees all,
  writes land in the caller's org) + org API RBAC. 149 -> 156 tests.

### Known limitations (tracked for follow-up)
- Control implementation *status* (Implemented/Partial/Missing) is still
  global because controls are shared reference data; per-org control
  status needs a join table. Gap and control-risk views ARE org-scoped
  (they count the org's mappings).
- The first super-admin must be provisioned out-of-band (DB/seed); no
  bootstrap flow creates one yet.

## v0.8-alpha1

### Added
- **Liveness/readiness probes**: `GET /health` (process up, no deps) and
  `GET /ready` (database reachable **and** schema migrated to Alembic
  head, else 503 with detail). The readiness migration check turns the
  previously-opaque "no such table" 500 on a behind-head database into a
  clear signal to run `alembic upgrade head`. Both unauthenticated.
- **Pagination, filtering, and sorting** on the list endpoints
  (`/vulnerabilities`, `/assets`, `/risks`) - one scan import can be
  thousands of findings. `limit`/`offset`, entity-appropriate filters
  (e.g. `severity`/`status`/`asset_id` for vulnerabilities), and
  allowlisted `sort_by` + `order`. Opt-in: with no query params the
  endpoints still return everything, so the existing contract is
  unchanged. (Audit log already had this from Phase 2.)
- **Structured logging** (`app/core/logging.py`): a dedicated
  `cyberrisk360` logger namespace with console or `LOG_FORMAT=json`
  output, and a request-logging middleware that emits method/path/
  status/duration/client-IP per request and sets an `X-Request-ID`
  correlation header (echoing an inbound one if present). Replaced the
  `traceback.print_exc()` calls in the import endpoint with
  `logger.exception`.
- **Configurable client-IP resolution** (`app/core/net.py`): a single
  `get_client_ip` used by both rate limiting and the audit trail. Honors
  `X-Forwarded-For` only when `TRUST_PROXY_HEADERS` is enabled (behind a
  trusted proxy), otherwise the socket peer - closing the "everything
  looks like it comes from the proxy IP" gap noted in TODO.md.
- `UPLOAD_DIR` is now env-configurable (mount a volume / step toward
  externalized storage); `LOG_LEVEL`/`LOG_FORMAT`/`TRUST_PROXY_HEADERS`
  documented in `.env.example`.
- New tests: `test_health.py`, `test_list_pagination.py`,
  `test_observability.py`. 133 -> 149 tests.

### Deferred (need external infra, tracked in ROADMAP.md Phase 3)
- Object-storage (S3-compatible) backend for uploads and a Redis-backed
  rate-limit store for multi-replica deployments. Config surfaces exist
  (`UPLOAD_DIR`, the single rate-limiter definition); the backends land
  when that infra is available to build against.

## v0.7-alpha3

### Added
- **Automatic risk generation from vulnerabilities**
  (`app/services/risks/risk_generation.py`). Each asset now gets one
  maintained aggregate risk (`source="auto"`): every vulnerability on
  the asset is linked to it via the previously-unused
  `vulnerability.risk_id` FK, impact is derived from the asset's
  criticality, likelihood from the asset's worst finding, and the risk
  is assigned to the asset's owner (falling back to "Unassigned" when
  the asset has no owner set). Idempotent - re-running updates the
  existing auto risk in place rather than duplicating, so it tracks
  findings as they're imported or closed. Manual risks
  (`source="manual"`) are never modified by the engine.
- Auto risks are produced on **import** (wired into the vulnerability
  importer's write phase) and on demand via a new backfill endpoint,
  **`POST /risks/generate`** (admin/analyst, audited as `risk.generate`),
  which derives/refreshes risks for every asset - the way to populate
  risks for data imported before this existed.
- `source` column on `risks` (migration `21824ec0933b`) distinguishing
  auto- from manually-created risks; surfaced in the risk API responses.
- `app/tests/test_risk_generation.py` (8 tests): derivation, owner
  fallback, vulnerability linkage, idempotency, manual-risk isolation,
  the backfill endpoint + RBAC, and end-to-end import wiring.
  125 -> 133 tests.

## v0.7-alpha2

### Added
- **Audit trail** (`audit_logs` table + `app/services/audit/`): an
  append-only log of security-relevant actions - authentication
  (`login.success`/`login.failure`/`login.locked`), account management
  (`user.register`/`user.password_change`/`user.password_reset`/
  `user.activate`/`user.deactivate`), report imports (`import.upload`),
  and mapping review decisions (`mapping.approve`/`mapping.reject`).
  Each entry records actor, action, entity, source IP, and timestamp.
  This is the general audit log a GRC product is expected to keep,
  distinct from the mapping-only `MappingHistory`.
- `GET /audit-logs` - oversight-only (admin/auditor/CISO/manager) read
  API with `action`/`actor` filters and `limit`/`offset` pagination.
- **Account lockout**: after 5 consecutive failed logins an account is
  locked for 15 minutes (`MAX_FAILED_LOGIN_ATTEMPTS` /
  `ACCOUNT_LOCKOUT_MINUTES`); a successful login clears the counter.
  Complements the existing per-IP `/login` rate limit with a
  per-account control. `attempt_login` returns a specific outcome
  (invalid / locked / inactive) that the endpoint maps to 401/403.
- **User identity fields**: `is_active`, `failed_login_attempts`,
  `locked_until`, `last_login`, `created_at`, `updated_at`. Disabled
  accounts (`is_active = false`) are rejected at login while keeping
  their history.
- **Account management endpoints**: `POST /users/me/change-password`
  (self, verifies current password, 8-char minimum),
  `POST /users/{id}/reset-password` (admin), and
  `POST /users/{id}/{activate,deactivate}` (admin). Token-based
  self-service "forgot password" is deferred to Phase 5 (needs email).
- **Persona roles**: the three original roles are joined by the
  remaining design-doc personas - `pentester`, `grc_analyst`,
  `manager`, `ciso`. Endpoints now reference semantic role groups
  (`WRITE_ROLES` / `COMPLIANCE_ROLES` / `OVERSIGHT_ROLES` / `READ_ROLES`
  in `constants.py`) so a new persona slots in without editing every
  router. Dashboards and reports widened to all read roles; audit log
  to the oversight roles.
- Migrations `dd92d089fdb0` (audit_logs) and `cf7f92f27fe3` (user
  fields). The user-fields migration uses `batch_alter_table` so the
  `created_at`/`updated_at` `CURRENT_TIMESTAMP` defaults apply on SQLite
  (a plain `ADD COLUMN` there rejects that default); verified against a
  populated table.
- 105 -> 125 tests: `test_audit.py`, `test_user_hardening.py`.

### Fixed
- Mapping approve/reject endpoints returned an empty body after audit
  logging was added: `record_audit`'s commit expired the `mapping` ORM
  object (SQLAlchemy `expire_on_commit`) and nothing reloaded it before
  serialization. Fixed with a `db.refresh(mapping)` after the audit
  write.

## v0.7-alpha1

### Fixed
- `/docs` (Swagger UI) and `/redoc` rendered as a blank page: the
  security-headers middleware sent `Content-Security-Policy:
  default-src 'none'` on *every* response, which blocked Swagger UI's
  CDN assets and inline bootstrap script. Its comment ("this API never
  serves HTML/JS") stopped being true once the docs UIs - and the new
  HTML report views - are considered. CSP is now chosen per response:
  strict `default-src 'none'` for JSON, a Swagger/ReDoc policy allowing
  the jsdelivr CDN + inline bootstrap + same-origin `/openapi.json`
  fetch on `/docs` and `/redoc`, and an inline-`style-src`-only policy
  (no scripts, no external origins) for HTML reports. Regression-
  guarded by `test_docs_csp_allows_swagger_cdn`,
  `test_json_report_keeps_strict_csp`, and the HTML-report CSP assertion.

### Added
- Reporting module (`app/reports/`), replacing the four 0-byte stubs
  that had shipped since the MVP. Three reports, each composed purely
  from existing analytics (no new business logic, no schema change):
  - **Executive Summary** - assets/vulnerabilities/controls at a glance,
    per-framework compliance, top-risk assets and controls
  - **Technical Vulnerability Report** - the full finding register
    grouped by severity (worst CVSS first) with remediation guidance
  - **Compliance Assessment Report** - per-framework posture, control
    gaps (affected/unaffected), and control risk
- New reporting API (`app/api/reports.py`): `GET /reports/executive`,
  `GET /reports/technical`, `GET /reports/compliance/{framework_name}`,
  each with `?format=json|html|pdf`, RBAC-guarded to admin/analyst/
  auditor. Unknown framework -> 404, render failure -> 500.
- HTML rendering via Jinja2 with autoescaping **on** - reports embed
  user-controlled vulnerability text (titles, descriptions), so escaping
  is a security control against stored-XSS-in-report, not cosmetic.
  Covered by a test asserting a raw `<script>` in a finding title does
  not survive into the HTML.
- PDF rendering via xhtml2pdf - pure-Python, needs no system libraries,
  so the app container produces PDFs with no extra OS packages.
- `app/tests/test_reports.py` (7 tests): each report in JSON/HTML/PDF
  (PDF verified by `%PDF` magic bytes), compliance 404, and an RBAC
  denial. 96 -> 103 tests. Compliance success path additionally smoke-
  tested end-to-end against a bootstrapped DB (all 5 frameworks).
- `ROADMAP.md` - phased industry-readiness roadmap (reporting first,
  then audit log + user hardening, scale floor, multi-tenancy,
  workflow/integrations, frontend).

## v0.6-alpha16

### Changed
- `vulnerability_importer.import_findings` split into two phases -
  `_enrich_findings` then `_write_findings` - instead of one loop that
  held a single write transaction open across the whole batch while
  also making real, slow network calls (`get_plugin_enrichment` can
  hit tenable.com, up to 3 retries with backoff). Now enrichment runs
  first, entirely separate from the write transaction, and commits
  immediately whenever the enrichment cache is actually written (a
  real fetch happened) - not on every finding, so a cache-hit-heavy
  repeat import doesn't turn into thousands of needless commits.
  `_write_findings` then does the local DB writes (asset + vulnerability
  creation, control mapping) in one fast, network-free transaction,
  single commit at the end - same atomicity as before for that part.
  A "deliberately deferred twice" item from TODO.md's backlog, now
  more relevant since the CSV/`.nessus` importers (previous pass) feed
  the same function
- `get_plugin_enrichment` (`services/enrichment/plugin_enrichment.py`)
  now returns `(dict, cache_written: bool)` instead of just `dict`, so
  the caller knows whether this call actually wrote the cache (a real
  fetch happened) versus a cache hit - the signal `_enrich_findings`
  uses to decide whether a commit is needed

### Fixed
- Found and fixed a real regression risk while designing the split:
  today, checking `get_by_plugin_id` inside the same session correctly
  catches the SAME `plugin_id` appearing twice within one import batch
  (e.g. a Nessus report listing one plugin on multiple hosts), because
  SQLAlchemy sessions see their own flushed-but-uncommitted inserts -
  but this was untested (no test exercised it), and splitting enrichment
  out into its own phase-before-any-flush would have silently broken it
  (both occurrences would have sailed through and created duplicate
  vulnerability rows). Fixed by deduping against an in-memory set in
  `_enrich_findings` in addition to the DB check, preserving the exact
  "first occurrence in the batch wins" semantics without depending on
  flush timing. Covered by
  `test_intra_batch_duplicate_plugin_id_creates_only_one`
- As a side effect of committing the enrichment cache immediately
  instead of only at the very end of the whole batch, a successfully
  fetched cache entry now survives even if a later finding in the same
  batch fails and the write phase rolls back - previously the cache
  write shared the same not-yet-committed transaction as the failed
  write and was lost too. Covered by
  `test_enrichment_cache_persists_when_phase_two_fails`

### Tests
- New `test_vulnerability_importer.py` - direct unit tests for
  `import_findings` below the HTTP/file-parsing level: intra-batch
  dedup, cross-batch (DB) dedup, cache durability on phase-2 failure,
  and commit-granularity on a cache hit (`_enrich_findings` alone
  should commit zero times on an all-cache-hit batch - the whole point
  of the conditional-commit design). `test_imports.py`'s 5 mocked
  `get_plugin_enrichment` call sites updated to the new
  `(dict, cache_written)` return shape. 91 → 96 tests. Verified green
  on both SQLite and a real PostgreSQL instance

## v0.6-alpha15

### Added
- CSV and native `.nessus` XML report importers -
  `importers/nessus_csv_parser.py` and `importers/nessus_xml_parser.py`,
  wired into `services/imports/report_processor.py` alongside the
  existing PDF path. Both produce the same finding dict shape PDF
  import does, so `vulnerability_importer.import_findings` needed no
  changes at all. CSV parses Nessus's standard export columns
  (`Plugin ID`/`CVE`/`CVSS`/`Risk`/`Host`/.../`Name`); `.nessus` XML
  parses `<ReportHost><ReportItem severity="0-4">` with the host
  attribution taken directly from the enclosing `<ReportHost name="...">`
  (no host-tracking-state hack needed, unlike the PDF parser). Both skip
  informational-level findings (`Risk="None"` / `severity="0"`), matching
  the PDF parser's existing behavior
- `.nessus` XML is parsed with `defusedxml.ElementTree` (new dependency),
  not stdlib `ElementTree` - blocks XXE/entity-expansion attacks on
  untrusted uploads. Verified with a real attack payload
  (`<!ENTITY xxe SYSTEM "file:///etc/passwd">`) in
  `test_xxe_attack_is_blocked`, which confirms `defusedxml` actually
  raises rather than silently parsing
- File-extension allowlist (`pdf`/`csv`/`nessus`) in `api/imports.py`,
  rejecting anything else with a clean `400` before the file is written
  to disk

### Fixed
- `api/imports.py` dispatched to `import_findings` with
  `if result["file_type"] == "pdf":` - the CSV/`.nessus` stubs never
  returned a `"file_type"` key at all, so uploading either format raised
  an unguarded `KeyError` → raw 500. Generalized to
  `if result.get("findings"):`, which is format-agnostic and needed no
  changes for this or any future format
- `process_report()` was never wrapped in try/except (only
  `import_findings` was, from the earlier security-hardening pass) - a
  malformed CSV or invalid XML upload produced an unguarded 500 with a
  leaked traceback. Now converts any parse failure into
  `HTTPException(400, "Failed to parse report")`, traceback logged
  server-side only, matching the existing `import_findings` failure
  pattern

### Tests
- `test_nessus_csv_parser.py` (4 tests), `test_nessus_xml_parser.py`
  (6 tests, including the XXE-blocking test), plus 5 new
  `test_imports.py` cases covering full-pipeline CSV/`.nessus` upload,
  rejected extensions, and malformed-upload 400s. 76 → 91 tests.
  Verified green on both SQLite and a real PostgreSQL instance

## v0.6-alpha14

### Fixed
- Resolved the `compliance_score` naming collision: `GET
  /frameworks/{name}/summary` (`api/controls.py`) computed something
  genuinely different from `analytics/compliance.py`'s `compliance_score`
  (used by `/compliance-summary` and `/dashboard/grc/{name}`) - the
  former is 100% minus % of controls with an approved vulnerability
  mapping, the latter is % of controls manually marked `"Implemented"`.
  Both were called `compliance_score`, so they could (and did, in
  testing) disagree for the same framework at the same instant. Per
  explicit direction: renamed `api/controls.py`'s field to
  `vulnerability_coverage_score` rather than picking one definition as
  canonical - both metrics are legitimate and answer different
  questions, they just needed to stop sharing a name. No behavior
  change, no value change - purely a response-field rename

## v0.6-alpha13

### Changed
- `POST /vulnerabilities` (manual entry) now runs the mapping engine
  automatically, same as PDF-imported vulnerabilities - previously only
  `import_findings` called `map_vulnerability_to_controls`, so
  manually-created vulnerabilities silently got no mapping at all,
  which undercut the mapping engine's whole purpose for an entire
  creation pathway. `VulnerabilityCreate` has no `cve_id`/`plugin_id`
  fields, so manual entries only ever match via keyword - narrower
  than imports, but still real value (e.g. "Weak SSH configuration"
  correctly matches the same keyword rules a PDF-imported finding
  would). `db_create_vulnerability`'s docstring already said "Caller
  flushes to obtain an id for control mapping" - this was clearly the
  intent from the start, just never wired up in this one endpoint

### Tests
- `test_create_vulnerability_triggers_mapping_engine` - 76 tests total

### Removed
- The two `*.pre-alembic-backup` SQLite files (repo root and
  `backend/`), per explicit user instruction - they pre-dated Alembic's
  `alembic_version` tracking and were fully superseded by
  `alembic upgrade head`

## v0.6-alpha12

TODO.md backlog cleanup: 5 of the smaller flagged items, chosen as the
ones that were genuinely actionable code/data fixes rather than product
decisions only the user can make (the `compliance_score` contradiction,
whether `POST /vulnerabilities` should auto-map, and the `.pre-alembic-
backup` file disposition are all still open, deliberately not decided here).

### Fixed
- `services/auth/auth.py` used the deprecated `datetime.utcnow()` -
  moved to `datetime.now(timezone.utc)`
- **Nessus PDF parser's multi-host bug**: `extract_findings` used to take
  the first IP address anywhere in the whole document and attribute
  every finding to it. A single-host report (the only shape the real
  sample fixture has) never surfaced this - both the old and new code
  produce identical output against it. Rewrote to track the current host
  as running state instead: a line that's just an IP marks the start of
  that host's "Vulnerabilities by Host" block, and every finding after
  it is attributed to that host until the next one. Also handles a real
  quirk confirmed against the actual sample PDF's extracted text: pypdf
  sometimes glues the per-page footer ("`<ip> <page>`") directly onto the
  start of the next finding line with no newline. Verified with a
  synthetic 2-host report: findings on host A/B were correctly separated
  (would have all been attributed to host A under the old code)

### Added
- `app/tests/conftest.py`'s isolated test engine now has the same
  `PRAGMA foreign_keys=ON` connect-event as the real app engine -
  previously only the app-level FK-existence checks were exercised by
  tests, never the DB constraint itself. New
  `test_db_level_fk_enforcement_rejects_orphaned_control` proves it
- `GET /risks` (list all) - the one resource missing this endpoint while
  every other one (`assets`, `controls`, `vulnerabilities`, `frameworks`)
  already had it
- Real `mapping_rules.json` content for the 3 frameworks that were still
  0 bytes (`iso27001`, `cis`, `owasp-asvs`) - CVE/CWE/keyword entries
  matching the format used for `nist-csf`/`owasp-top10`. Confirmed the
  mapping engine merges all 5 correctly, including real cross-framework
  overlap (e.g. `CWE-798` now maps to controls in `cis`, `iso27001`,
  `nist-csf`, `owasp-asvs`, and `owasp-top10` simultaneously - a single
  real vulnerability legitimately violates multiple standards at once)
- `app/tests/test_risks.py`, `app/tests/test_nessus_pdf_parser.py` -
  suite goes from 68 to 75 tests

### Verified
- Full suite green throughout (including against real Postgres for the
  final state) and unchanged behavior on the real sample PDF

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
