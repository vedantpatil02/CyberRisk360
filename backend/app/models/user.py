"""
CyberRisk360

Purpose:
Database model representing platform users.
"""

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Boolean
from sqlalchemy import DateTime
from sqlalchemy import text
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr

from app.db.database import Base


class User(Base):
    """
    User table.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String,
        unique=True,
        nullable=False
    )

    email = Column(
        String,
        unique=True,
        nullable=False
    )

    password = Column(
        String,
        nullable=False
    )

    role = Column(
        String,
        default="analyst"
    )

    # Deactivated accounts are rejected at login without being deleted,
    # preserving their history and audit trail.
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("true")
    )

    # Brute-force protection: consecutive failures accumulate here and,
    # past a threshold, set `locked_until` to a future time. Both reset
    # on a successful login.
    failed_login_attempts = Column(
        Integer,
        nullable=False,
        server_default=text("0")
    )

    locked_until = Column(
        DateTime(timezone=True),
        nullable=True
    )

    last_login = Column(
        DateTime(timezone=True),
        nullable=True
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )



class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str