from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import CORS_ALLOWED_ORIGINS
from app.core.rate_limiter import limiter
from app.core.logging import configure_logging
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.middleware.request_logging import RequestLoggingMiddleware

configure_logging()

from app.api.auth import router as auth_router
from app.api.users import router as user_router
from app.api.assets import router as asset_router
from app.api.risks import router as risk_router
from app.api.vulnerabilities import router as vulnerability_router
from app.api.controls import router as control_router
from app.api.frameworks import router as framework_router
from app.api.imports import router as import_router
from app.api.dashboard import (router as dashboard_router)
from app.api.mappings import router as mapping_router
from app.api.reports import router as report_router
from app.api.audit import router as audit_router
from app.api.audits import router as audits_router
from app.api.health import router as health_router
from app.api.organizations import router as organization_router
from app.api.evidence import router as evidence_router
from app.api.notifications import router as notifications_router
import app.models

# Schema is managed exclusively by Alembic (see backend/alembic/ and
# scripts/bootstrap_database.py) - run `alembic upgrade head` (or the
# bootstrap script, which does that plus seeds reference data) before
# starting the app. Deliberately not run here: in-process schema
# creation/migration at import time doesn't survive multiple replicas
# and mixing it with Alembic causes "table already exists" errors.

app = FastAPI(
    title="CyberRisk360",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(RequestLoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(user_router)
app.include_router(auth_router)
app.include_router(asset_router)
app.include_router(risk_router)
app.include_router(vulnerability_router)
app.include_router(control_router)
app.include_router(framework_router)
app.include_router(import_router)
app.include_router(dashboard_router)
app.include_router(mapping_router)
app.include_router(report_router)
app.include_router(audit_router)
app.include_router(audits_router)
app.include_router(health_router)
app.include_router(organization_router)
app.include_router(evidence_router)
app.include_router(notifications_router)

@app.get("/")
def home():

    return {
        "message": "CyberRisk360 API Running"
    }
