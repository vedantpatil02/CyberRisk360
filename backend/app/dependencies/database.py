"""
CyberRisk360

Purpose:
Provide shared FastAPI dependencies.
"""

from app.database import SessionLocal


def get_db():
    """
    Create database session for a request.

    Automatically closes the session when
    request processing finishes.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()