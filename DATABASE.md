# CyberRisk360 Database Design Document

**Version:** 1.0  
**Database:** SQLite (Current) → PostgreSQL (Future)  
**ORM:** SQLAlchemy  
**Migration Tool:** Alembic (Planned)

---

# 1. Database Overview

## Purpose

The **CyberRisk360** database is designed to store, organize, and manage cybersecurity information required for enterprise cyber risk management.

It serves as the central repository for:

- Users
- IT Assets
- Vulnerabilities
- Compliance Frameworks
- Categories
- Controls
- Vulnerability-to-Control mappings
- Risk-related information
- Future reporting and audit data

The database enables organizations to:

- Track discovered vulnerabilities
- Map vulnerabilities to compliance controls
- Assess organizational risk
- Monitor compliance posture
- Generate dashboards and reports
- Support multiple compliance frameworks

---

# 2. Database Technology

| Item | Value |
|------|-------|
| ORM | SQLAlchemy |
| Current Database | SQLite |
| Future Database | PostgreSQL |
| Migration Tool | Alembic (Planned) |
| Language | Python |
| Design Pattern | Relational Database (Normalized) |

---

# 3. Current Entity Relationship (ER) Diagram

Current database architecture:

```text
+--------+
| User   |
+--------+

+--------+
| Asset  |
+--------+

+---------------+
| Vulnerability |
+---------------+

+---------+
| Control |
+---------+

+------+
| Risk |
+------+

+--------------------------------+
| VulnerabilityControlMapping    |
+--------------------------------+
```

Current tables are relatively independent and provide the foundation for future normalization.

---

# 4. Target Entity Relationship (ER) Diagram

**Status: implemented.** As of July 2026, this is the live schema — the
Framework → Category → Control hierarchy is in place, the repository layer
(Section 9's data flow) is wired end-to-end, and the framework importer
populates this structure directly from `frameworks/<name>/<version>/`
metadata and definitions.

The target architecture introduces compliance framework normalization and hierarchical relationships.

```text
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
        │
        ▼
Asset
```

### Logical Flow

```
Framework
    └── Category
            └── Control
                    └── VulnerabilityControlMapping
                            ├── Vulnerability
                            └── Control
                                    ▲
                                    │
                                 Asset
```

---

# 5. Table Definitions

---

## 5.1 Framework

### Purpose

Stores supported cybersecurity and compliance frameworks.

Examples include:

- NIST CSF
- ISO 27001
- CIS Controls
- PCI DSS
- SOC 2
- HIPAA

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| name | Framework name |
| short_name | Abbreviation |
| version | Framework version |
| publisher | Organization publishing the framework |
| description | Framework description |
| release_year | Release year |

### Primary Key

- `id`

### Relationships

```
Framework
    │
    └── Categories
```

---

## 5.2 Category

### Purpose

Represents logical groups of controls within a framework.

Example:

```
Framework
    ├── Access Control
    ├── Asset Management
    ├── Incident Response
```

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| framework_id | FK → Framework |
| category_code | Category identifier |
| name | Category name |
| description | Description |

### Primary Key

- `id`

### Foreign Keys

- `framework_id`

### Relationships

```
Framework
    └── Category
            └── Controls
```

---

## 5.3 Control

### Purpose

Represents an individual compliance requirement.

Example:

```
AC-2
IA-5
CM-8
```

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| category_id | FK → Category |
| control_id | Official control identifier |
| title | Control title |
| description | Control description |
| implementation_guidance | Recommended implementation |
| priority | Criticality |
| status | Active / Deprecated |

### Primary Key

- `id`

### Foreign Keys

- `category_id`

### Relationships

```
Category
    └── Controls
```

---

## 5.4 Vulnerability

### Purpose

Stores discovered vulnerabilities imported from scanners.

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| asset_id | FK → Asset |
| plugin_id | Scanner plugin identifier |
| cve | CVE identifier |
| title | Vulnerability title |
| severity | Severity level |
| cvss_score | CVSS score |
| description | Technical description |
| status | Open / Closed |

### Primary Key

- `id`

### Foreign Keys

- `asset_id`

### Relationships

```
Asset
    └── Vulnerabilities
```

---

## 5.5 Asset

### Purpose

Represents IT assets being monitored.

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| hostname | Device hostname |
| ip_address | IP address |
| operating_system | Operating system |
| owner | Asset owner |
| criticality | Business importance |
| status | Active / Retired |

### Primary Key

- `id`

### Relationships

```
Asset
    └── Vulnerabilities
```

---

## 5.6 VulnerabilityControlMapping

### Purpose

Maps vulnerabilities to one or more compliance controls.

This enables automated compliance impact analysis.

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| vulnerability_id | FK → Vulnerability |
| control_id | FK → Control |
| mapping_confidence | Confidence score |
| notes | Analyst notes |

### Primary Key

- `id`

### Foreign Keys

- `vulnerability_id`
- `control_id`

### Relationships

```
Control
      ▲
      │
VulnerabilityControlMapping
      │
      ▼
Vulnerability
```

---

## 5.7 User

### Purpose

Stores application users and authentication information.

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| username | Login username |
| email | Email address |
| password_hash | Encrypted password |
| role | User role |
| created_at | Account creation date |

### Relationships

Users interact with:

- Reports
- Dashboards
- Risk assessments
- Audit records

---

## 5.8 Risk

### Purpose

Stores calculated cyber risk information based on assets, vulnerabilities, and compliance status.

### Fields

| Field | Description |
|--------|-------------|
| id | Primary Key |
| asset_id | FK → Asset |
| risk_score | Calculated score |
| likelihood | Likelihood rating |
| impact | Business impact |
| status | Open / Mitigated |

---

# 6. Relationship Diagram

```text
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
      │
      ▼
Asset
```

Relationship Summary:

- One Framework contains many Categories.
- One Category contains many Controls.
- One Control can map to many Vulnerabilities.
- One Vulnerability can map to many Controls.
- One Asset can have many Vulnerabilities.

---

# 7. Database Normalization

## Previous Design

```text
Control
--------------------
framework = "NIST"
framework = "NIST"
framework = "ISO"
framework = "NIST"
```

The framework name was stored as a plain string, leading to repeated values and potential inconsistencies.

## New Design

```text
Framework
      │
      ▼
Category
      │
      ▼
Control
```

Controls now reference frameworks through foreign keys.

## Benefits

- Eliminates duplicate framework names
- Ensures consistent framework metadata
- Supports multiple framework versions
- Simplifies reporting
- Improves query performance
- Makes adding new frameworks easier
- Enables richer metadata (publisher, release year, descriptions)

---

# 8. Future Tables

The following tables are planned for future releases:

| Table | Purpose |
|---------|----------|
| Report | Generated compliance and risk reports |
| ScanHistory | Historical scanner execution records |
| Remediation | Tracks remediation actions |
| Evidence | Compliance evidence repository |
| Audit | Audit trail for system changes |
| Notifications | User alerts and notifications |
| Integrations | External tool integrations |

These tables are reserved to support future expansion without major schema redesign.

---

# 9. Index Strategy

To improve query performance, the following indexes are recommended:

| Index | Purpose |
|---------|----------|
| control_id | Fast control lookups |
| framework_id | Framework filtering |
| category_id | Category filtering |
| asset_id | Asset queries |
| vulnerability_id | Vulnerability lookups |
| plugin_id | Scanner plugin searches |
| cvss_score | Severity-based filtering |
| severity | Severity reports |
| status | Open/closed vulnerability queries |
| hostname | Asset searches |
| ip_address | Asset identification |

Additional composite indexes may be introduced as reporting requirements evolve.

---

# 10. Data Flow

The following illustrates the typical flow of cybersecurity data through the system:

```text
Scanner Report
       │
       ▼
Import Process
       │
       ▼
Vulnerability
       │
       ▼
Asset
       │
       ▼
VulnerabilityControlMapping
       │
       ▼
Control
       │
       ▼
Category
       │
       ▼
Framework
       │
       ▼
Risk Analysis
       │
       ▼
Dashboard & Reports
```

## Data Flow Description

1. Security scanners generate vulnerability reports.
2. Reports are imported into the system.
3. Vulnerabilities are associated with the affected assets.
4. Vulnerabilities are mapped to compliance controls.
5. Controls are linked to categories within compliance frameworks.
6. Risk calculations are performed based on vulnerability severity and asset criticality.
7. Dashboards and reports present compliance status and cyber risk metrics.

---

# Conclusion

The CyberRisk360 database is designed using a normalized relational model that supports scalable cybersecurity operations, compliance management, and enterprise risk assessment. The architecture provides a clear separation of concerns between compliance frameworks, controls, assets, and vulnerabilities while remaining flexible for future enhancements such as reporting, auditing, remediation tracking, and external integrations.