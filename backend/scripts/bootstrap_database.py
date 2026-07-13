"""
CyberRisk360

Purpose:
Bootstrap the database: create all tables and import every
supported compliance framework from the frameworks/ repository.

Safe to run multiple times — table creation is a no-op if tables
already exist, and framework/category/control import skips anything
already present (see get_or_create_framework, get_or_create_category,
and get_control_by_code).

Usage:
    python scripts/bootstrap_database.py
(can be run from any directory; the script anchors itself to backend/)
"""

import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from app.db.database import engine, Base, SessionLocal
import app.models  # noqa: F401  (registers models with Base.metadata)

from app.core.constants import FRAMEWORK_FILES, FRAMEWORK_METADATA_FILES
from app.services.frameworks.framework_loader import load_framework
from app.services.frameworks.framework_importer import import_framework
from app.repositories.frameworks.framework_repository import (
    get_all_frameworks
)
from app.repositories.controls.control_repository import get_all_controls


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables ready.")


def import_all_frameworks(db):
    print("Importing compliance frameworks...")

    for framework_name in FRAMEWORK_FILES:
        controls = load_framework(FRAMEWORK_FILES[framework_name])
        metadata = load_framework(FRAMEWORK_METADATA_FILES[framework_name])

        imported_count = import_framework(metadata, controls, db)

        print(
            f"  {framework_name}: {imported_count} new control(s) imported"
        )


def verify_import(db):
    frameworks = get_all_frameworks(db)
    controls = get_all_controls(db)

    print(
        f"Verification: {len(frameworks)} framework(s), "
        f"{len(controls)} control(s) in database."
    )

    imported_short_names = {
        framework.short_name for framework in frameworks
    }

    missing = [
        name for name in FRAMEWORK_FILES
        if name not in imported_short_names
    ]

    if missing:
        raise RuntimeError(
            f"Bootstrap verification failed, frameworks missing: {missing}"
        )

    if not controls:
        raise RuntimeError(
            "Bootstrap verification failed: no controls were imported."
        )

    print("Verification passed.")


def main():
    create_tables()

    db = SessionLocal()

    try:
        import_all_frameworks(db)
        verify_import(db)
    finally:
        db.close()

    print("Database bootstrap complete.")


if __name__ == "__main__":
    main()
