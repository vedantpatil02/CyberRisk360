# ADR-001: Compliance Architecture Normalization

| Field | Value |
|-------|-------|
| **ADR ID** | ADR-001 |
| **Title** | Compliance Architecture Normalization |
| **Status** | Accepted |
| **Date** | July 2026 |
| **Authors** | Vedant Patil |
| **Version** | 1.0 |

---

# 1. Context

CyberRisk360 is evolving from a vulnerability management backend into a complete Cyber Risk and Compliance Management Platform.

The initial implementation stored compliance controls in a single table where each control directly contained framework information.

Example:

```
Control
--------
control_id
framework
name
description
status
```

While this design was sufficient for the MVP, it introduces limitations as the platform expands to support multiple compliance frameworks, framework versions, and advanced reporting.

---

# 2. Problem Statement

The original design presents several challenges:

- Framework information is duplicated across every control.
- Controls cannot be grouped into categories.
- Framework versions cannot be managed independently.
- Reporting capabilities are limited.
- Adding new compliance frameworks requires framework-specific logic.
- The database structure does not scale well as the number of controls increases.

These limitations would lead to technical debt as CyberRisk360 grows.

---

# 3. Decision

The compliance data model will be normalized by introducing dedicated **Framework** and **Category** entities.

The new hierarchy will be:

```
Framework
    │
    ▼
Category
    │
    ▼
Control
    │
    ▼
VulnerabilityControlMapping
    ▲
    │
Vulnerability
```

Framework information will no longer be stored directly inside the Control entity.

Instead, each control belongs to a category, and each category belongs to a framework.

---

# 4. Architecture Overview

```
Framework
──────────────
id
name
short_name
version
publisher
description

        │
        ▼

Category
──────────────
id
framework_id
category_code
name
description

        │
        ▼

Control
──────────────
id
category_id
control_id
title
description
implementation_guidance
priority
status

        │
        ▼

VulnerabilityControlMapping

        ▲
        │

Vulnerability
```

---

# 5. Rationale

This architecture provides several advantages.

## 5.1 Database Normalization

Framework information is stored once instead of being duplicated across hundreds of controls.

---

## 5.2 Multiple Framework Versions

Future versions can coexist.

Examples:

- NIST-CSF 1.1
- NIST-CSF 2.0
- ISO 27001:2013
- ISO 27001:2022

without modifying application logic.

---

## 5.3 Category Support

Controls can now be grouped logically.

Examples:

```
Protect

Detect

Respond

Recover
```

or

```
Access Control

Cryptography

Asset Management
```

depending on the framework.

---

## 5.4 Improved Reporting

Reports can now aggregate information by:

- Framework
- Category
- Control
- Compliance Status

instead of only by control.

---

## 5.5 Better Scalability

Adding a new compliance framework becomes a data operation rather than a code change.

The application will load framework definitions dynamically from the framework repository.

---

# 6. Alternatives Considered

## Option 1 — Keep Current Design

Advantages

- No database changes.
- Minimal implementation effort.

Disadvantages

- Poor scalability.
- Framework duplication.
- Difficult reporting.
- Technical debt.

Decision:

Rejected.

---

## Option 2 — Separate Tables for Every Framework

Example:

```
nist_controls

iso_controls

cis_controls
```

Advantages

- Simple implementation.

Disadvantages

- Significant code duplication.
- Framework-specific queries.
- Difficult maintenance.
- Inconsistent APIs.

Decision:

Rejected.

---

## Option 3 — Normalized Compliance Model

Framework

↓

Category

↓

Control

Advantages

- Clean architecture.
- Reusable logic.
- Supports unlimited frameworks.
- Easier reporting.
- Better maintainability.

Decision:

Accepted.

---

# 7. Consequences

Positive:

- Improved maintainability.
- Reduced data duplication.
- Better reporting.
- Cleaner architecture.
- Easier framework expansion.
- Future-proof design.

Negative:

- Requires database refactoring.
- Framework importer must be updated.
- Framework loader must be updated.
- Existing controls must be migrated.

The long-term benefits outweigh the migration effort.

---

# 8. Impacted Components

The following components will be updated:

## Database

- Framework Model
- Category Model
- Control Model

---

## Services

- Framework Loader
- Framework Importer
- Control Mapper

---

## Analytics

- Compliance Summary
- Gap Analysis
- Executive Dashboard

---

## APIs

- Controls
- Frameworks
- Dashboard

---

# 9. Migration Strategy

The migration will be completed in phases.

### Phase 1

Create Framework model. **Status: Complete.**

---

### Phase 2

Create Category model. **Status: Complete.**

---

### Phase 3

Update Control model. **Status: Complete.**

---

### Phase 4

Update framework loader. **Status: Complete** (path resolution fixed to
match the versioned `frameworks/<name>/<version>/` layout).

---

### Phase 5

Update framework importer. **Status: Complete** (resolves/creates
`Framework` + `Category` from `metadata.json`, uses `title`/`category_id`).

---

### Phase 6

Migrate existing framework data. **Status: Complete** for all four
supported frameworks (NIST CSF, ISO 27001, CIS Controls, OWASP ASVS); all
remaining `Control.framework`/`Control.name` references removed
repository-wide (`api/`, `services/`, `analytics/`).

---

### Phase 7

Refactor compliance dashboards. **Status: Complete** — `analytics/`
(`grc.py`, `gap_analysis.py`, `control_risk_analysis.py`, `executive.py`,
`asset_risk.py`) no longer queries the database directly; all access goes
through the repository layer added alongside this migration.

---

# 10. Future Considerations

This architecture enables future support for:

- PCI DSS
- SOC 2
- HIPAA
- NIST SP 800-53
- MITRE ATT&CK mappings
- Framework versioning
- Custom organizational frameworks
- Compliance evidence management
- Automated control recommendations

without requiring structural database redesign.

---

# 11. Risks

Potential risks include:

- Temporary incompatibility during migration.
- Import failures if framework data is malformed.
- Existing APIs requiring minor updates.

These risks will be mitigated through incremental implementation and testing.

---

# 12. Decision Summary

The CyberRisk360 compliance architecture will adopt a normalized database design centered around **Framework → Category → Control**.

This decision establishes the long-term foundation for scalable compliance management, advanced reporting, and multi-framework support while minimizing future technical debt.

This ADR represents the first major architectural decision for CyberRisk360 and serves as the reference point for all future compliance-related enhancements.

---

# References

- ../PRODUCT_DESIGN_DOCUMENT.md
- architecture.md
- database.md (Planned)
- ROADMAP.md