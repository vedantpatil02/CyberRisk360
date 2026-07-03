"""
CyberRisk360

Purpose:
Configure database connection and SQLAlchemy session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite database location
DATABASE_URL = "sqlite:///./cyberrisk360.db"

# Create database engine
# check_same_thread=False is required for SQLite with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Database session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base class inherited by all SQLAlchemy models
Base = declarative_base()
