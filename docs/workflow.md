# workflow.md

Living reference for every multi-step / approval-style workflow implemented
in CyberRisk360. Updated whenever a sprint adds or changes one — see
`CHANGELOG.md` for the commit-level history behind each entry.

## Common shape

Every workflow below follows the same additive pattern rather than each
inventing its own:

- A `status`-like string field lives directly on the entity (no DB enum —
  enforced in application code via constants in `app/core/constants.py`).
- Reviewer/actor identity is a plain string (email/subject claim), not a
  `User` foreign key — consistent across every workflow that has one.
- A dedicated `*_history` table records every transition: `action`,
  `previous_status`, `new_status`, `actor`, `note`, `created_at`, `org_id`.
  Written in the same transaction as the state change (one `db.commit()`).
- A generic `record_audit()` call (separate transaction) additionally logs
  the security-relevant event to `audit_logs` — the workflow-specific
  history table and the generic audit trail are deliberately both written;
  see `AI_CONTEXT.md`'s note on the difference.

## Vulnerability-Control Mapping Approval (existing)

The mapping engine (`app/services/mapping/mapping_engine.py`) auto-generates
`VulnerabilityControlMapping` rows at `pending` status by matching
CVE/CWE/Plugin ID/keyword. A human then approves or rejects:

- `GET /mappings/pending`, `GET /vulnerabilities/{id}/mappings`,
  `GET /mappings/{id}/history` — `admin`/`analyst`/`auditor`
- `PATCH /mappings/{id}/approve`, `PATCH /mappings/{id}/reject` —
  `admin`/`analyst`

Status: `pending` → `approved` | `rejected`. `MappingHistory`
(`app/models/mapping_history.py`) records every transition. Only
`approved` mappings count toward compliance/risk scoring
(`gap_analysis.py`, `control_risk_analysis.py`) — a pending match doesn't
move numbers before a human reviews it.

## Remediation SLA + Evidence (existing)

Vulnerabilities and risks both carry `assignee_id` (real `User` FK,
same-org validated), `due_date` (computed once at creation from
severity/risk_level via `app/services/remediation/sla.py::compute_due_date`,
never recomputed on edit), and an `sla_breached` filter computed at query
time (never persisted — see `is_sla_breached`). `EvidenceAttachment` rows
attach to either a vulnerability or a risk (exactly one of the two FKs set)
via `POST/GET .../evidence`.

## Risk Treatment + Approval (new this sprint)

Extends the Risk Register with a formal treatment decision workflow:
**Mitigate / Accept / Transfer / Avoid**, gated by a separate approval
step — separation of duties between who proposes a treatment and who
signs off on it.

`Risk.status` already had `Mitigated`/`Accepted` as existing terminal
values from the plain status field. Rather than introduce a
`treatment_type` dimension that duplicates that semantic, treatment is
layered on top of the same `status` field: `treatment_type` records what
was *proposed*; approval drives `status` to the corresponding terminal
value. Two new terminal statuses were added to cover the two treatment
outcomes that didn't already have one: `Transferred`, `Avoided` (alongside
the existing `Mitigated`/`Accepted`/`Closed`).

New fields on `Risk`: `treatment_type` (mitigate/accept/transfer/avoid),
`treatment_justification`, `approval_status` (pending/approved/rejected),
`approved_by`, `approved_at`. New table `risk_treatment_history` (same
shape as `MappingHistory`, one row per risk instead of per mapping).

Flow:
1. `POST /risks/{id}/treatment` (`admin`/`analyst`/`grc_analyst` —
   `COMPLIANCE_ROLES`) — proposes a treatment. `status` → `Under Review`,
   `approval_status` → `pending`.
2. `PATCH /risks/{id}/treatment/approve` or `.../reject`
   (`admin`/`auditor`/`ciso`/`manager` — `OVERSIGHT_ROLES`, deliberately a
   *different* role tier than who can propose). On approve, `status`
   moves to the treatment's terminal value (mitigate → `Mitigated`,
   accept → `Accepted`, transfer → `Transferred`, avoid → `Avoided`). On
   reject, `status` reverts to `Open` for reconsideration.
3. `GET /risks/{id}/treatment/history` (`READ_ROLES`) — the transition
   log.

Frontend: this is the first resource in the codebase with a
create/mutate UI (previously only Login had a form, and only Login used
`useMutation`) — see `frontend/src/pages/risks/RiskDetailPage.tsx`.
