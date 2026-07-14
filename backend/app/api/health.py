"""
CyberRisk360

Purpose:
Liveness and readiness probes for orchestrators/load balancers.

  /health - liveness: the process is up. No dependencies, never fails
            while the app can serve requests. Unauthenticated.
  /ready  - readiness: dependencies (database, schema migration) are
            healthy. Returns 503 when not ready. Unauthenticated.

Both are deliberately auth-free so infrastructure can probe them.
"""

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.services.health.health import check_readiness


router = APIRouter()


@router.get("/health")
def health():
    """
    Liveness probe.
    """

    return {"status": "ok"}


@router.get("/ready")
def ready(
    response: Response,
    db: Session = Depends(get_db)
):
    """
    Readiness probe - 200 when the database is reachable and migrated to
    head, otherwise 503 with detail.
    """

    is_ready, detail = check_readiness(db)

    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "status": "ready" if is_ready else "not ready",
        **detail,
    }
