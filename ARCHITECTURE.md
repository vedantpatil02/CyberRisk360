# ARCHITECTURE.md

# CyberRisk360 Architecture

**Project:** CyberRisk360

**Version:** v0.6 (Enterprise Compliance Engine)

**Document Version:** 1.0

**Last Updated:** July 2026

---

# 1. Overview

CyberRisk360 follows a layered, modular architecture designed around the principles of Separation of Concerns (SoC), scalability, maintainability, and extensibility.

Rather than acting as a vulnerability scanner, CyberRisk360 functions as a Cyber Risk and Compliance Management Platform that consumes findings from multiple security tools and converts them into actionable business intelligence.

The architecture has been designed to support multiple compliance frameworks, enterprise integrations, executive reporting, and future cloud-native deployment.

---

# 2. High-Level Architecture

```
                   External Security Tools

      Nessus    OpenVAS    Burp Suite    Nmap

                        │
                        ▼

                Report Import Layer

                        │
                        ▼

            Vulnerability Processing Layer

                        │
                        ▼

              Asset Correlation Layer

                        │
                        ▼

           Compliance Mapping Engine

                        │
                        ▼

              Risk Analysis Engine

                        │
                        ▼

            Executive Dashboard Layer

                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼

   Dashboards      PDF Reports      Compliance Reports
```

---

# 3. Architecture Principles

CyberRisk360 follows the following engineering principles:

- Modular Design
- Layered Architecture
- Separation of Concerns
- Data-Driven Compliance
- Reusable Business Logic
- API First Development
- Secure by Design
- Scalable Module Organization

---

# 4. Project Structure

```
CyberRisk360/

backend/
frameworks/
docs/

README.md
PRODUCT_DESIGN_DOCUMENT.md
ARCHITECTURE.md
DATABASE.md
ROADMAP.md
CHANGELOG.md
API_REFERENCE.md
```

---

# 5. Backend Architecture

```
Backend

├── api/
├── analytics/
├── services/
├── models/
├── schemas/
├── dependencies/
├── importers/
├── core/
├── db/
└── main.py
```

---

# 6. Module Responsibilities

## API Layer

Responsible for:

- REST endpoints
- Request validation
- Authentication
- Authorization
- Response formatting

Business logic must never exist inside API routes.

---

## Service Layer

Responsible for:

- Business logic
- Framework loading
- Framework importing
- Vulnerability processing
- Asset mapping
- Authentication
- Report processing

Services communicate with models but never expose HTTP responses.

---

## Analytics Layer

Responsible for:

- Risk calculations
- Compliance scoring
- Dashboard statistics
- Executive KPIs
- Trend analysis
- Gap analysis

Analytics modules should contain calculations only.

---

## Models Layer

Responsible for:

- Database entities
- ORM relationships
- Constraints
- Foreign Keys

Models should not contain business logic.

---

## Schemas Layer

Responsible for:

- Request validation
- Response serialization
- API contracts

Schemas isolate external APIs from database models.

---

## Dependencies Layer

Responsible for:

- JWT Authentication
- RBAC
- Database Sessions
- Shared FastAPI dependencies

---

## Importers

Responsible for:

- Parsing third-party reports
- Data normalization
- Import preparation

---

# 7. Compliance Architecture

The Compliance Engine follows a generic framework model.

```
Framework

↓

Categories

↓

Controls

↓

Mapping Rules

↓

Compliance Engine
```

The backend does not contain framework-specific logic.

All framework information is loaded dynamically.

Supported Frameworks

- NIST CSF
- ISO 27001
- CIS Controls
- OWASP ASVS

Future

- PCI DSS
- SOC 2
- HIPAA
- NIST 800-53

---

# 8. Framework Repository

```
frameworks/

nist-csf/
    v2.0/
        metadata.json
        framework.json
        mapping_rules.json

iso27001/
    2022/
        metadata.json
        framework.json
        mapping_rules.json

cis-controls/
    v8/
        metadata.json
        framework.json
        mapping_rules.json

owasp-asvs/
    v4.0.3/
        metadata.json
        framework.json
        mapping_rules.json

common/
    severity_weights.json
    categories.json
```

Frameworks are treated as data rather than code.

---

# 9. Compliance Workflow

```
Framework Loader

↓

Framework Importer

↓

Framework

↓

Categories

↓

Controls

↓

Compliance Dashboard
```

---

# 10. Vulnerability Workflow

```
Security Report

↓

Parser

↓

Normalized Findings

↓

Plugin Enrichment

↓

Asset Mapping

↓

Vulnerability Storage

↓

Control Mapping

↓

Risk Analysis

↓

Dashboard
```

---

# 11. Control Mapping Workflow

```
Imported Vulnerability

↓

Keyword Extraction

↓

mapping_rules.json

↓

Matching Controls

↓

Vulnerability-Control Mapping

↓

Compliance Dashboard
```

Future versions will replace keyword matching with a more intelligent rule engine.

---

# 12. Risk Engine

The Risk Engine evaluates organizational risk using multiple factors.

Current Inputs

- CVSS Score
- Vulnerability Severity
- Asset Criticality
- Compliance Coverage

Future Inputs

- Business Impact
- Likelihood
- Threat Intelligence
- Exploit Availability
- Exposure

---

# 13. Executive Dashboard

The Executive Dashboard aggregates information from multiple analytics modules.

```
Assets

↓

Vulnerabilities

↓

Compliance

↓

Risk

↓

Executive KPIs
```

Outputs include:

- Overall Risk Score
- Compliance Score
- High-Risk Assets
- Top Risky Controls
- Vulnerability Distribution

---

# 14. Authentication Architecture

```
User Login

↓

JWT Generation

↓

RBAC Validation

↓

API Authorization

↓

Protected Endpoint
```

Supported Roles

- Administrator
- Analyst
- Auditor

Future

- Manager
- Executive
- Read-Only

---

# 15. Database Architecture

Current Core Entities

```
User

Asset

Vulnerability

Control

VulnerabilityControlMapping

Risk
```

Target Architecture

```
Framework

↓

Category

↓

Control

↓

VulnerabilityControlMapping

↓

Vulnerability

↓

Asset
```

This normalization improves scalability and reporting.

---

# 16. Future Integrations

Planned integrations include:

- Nessus API
- OpenVAS
- Burp Suite Enterprise
- Microsoft Defender
- Jira
- ServiceNow
- Slack
- Microsoft Teams

---

# 17. Deployment Architecture (Future)

```
                Internet

                     │

              Reverse Proxy

                     │

               FastAPI Backend

                     │

             PostgreSQL Database

                     │

             Object Storage

                     │

              Frontend (React)
```

Future versions will support Docker and Kubernetes deployment.

---

# 18. Design Principles

The architecture is governed by the following principles:

- Single Responsibility Principle
- Separation of Concerns
- Modular Design
- Extensibility
- Reusability
- Maintainability
- Enterprise Readiness
- Security by Design

---

# 19. Version History

| Version | Description |
|----------|-------------|
| v0.5 | Backend MVP |
| v0.6 | Enterprise Compliance Architecture |
| v0.7 | Reporting Architecture |
| v0.8 | Analytics Expansion |
| v0.9 | Frontend Integration |
| v1.0 | Production Architecture |

---

# 20. Conclusion

CyberRisk360 is designed as a modular Cyber Risk and Compliance Management Platform capable of integrating technical vulnerability data with business context, compliance frameworks, and organizational risk.

The architecture emphasizes extensibility, maintainability, and enterprise readiness, allowing new frameworks, integrations, and analytical capabilities to be introduced with minimal changes to the existing codebase.