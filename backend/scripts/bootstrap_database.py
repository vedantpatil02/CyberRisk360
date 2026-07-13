"""
CyberRisk360

Purpose:
Bootstrap the database: create all tables and import every
compliance framework found under frameworks/, discovered
automatically rather than from a hardcoded list.

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

from app.core.constants import FRAMEWORKS_DIR
from app.services.frameworks.framework_loader import (
    load_framework,
    discover_frameworks
)
from app.services.frameworks.framework_importer import import_framework
from app.repositories.frameworks.framework_repository import (
    get_all_frameworks
)
from app.repositories.categories.category_repository import (
    get_all_categories
)
from app.repositories.controls.control_repository import get_all_controls


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables ready.")


def import_all_frameworks(db, discovered):
    print(f"Discovered {len(discovered)} framework(s) under {FRAMEWORKS_DIR}")

    for short_name, paths in sorted(discovered.items()):
        controls = load_framework(paths["framework_path"])
        metadata = load_framework(paths["metadata_path"])

        imported_count = import_framework(metadata, controls, db)

        print(
            f"  {short_name} ({metadata.get('version')}): "
            f"{imported_count} new control(s) imported"
        )


def verify_import(db, discovered):
    frameworks = get_all_frameworks(db)
    categories = get_all_categories(db)
    controls = get_all_controls(db)

    print(f"✓ Frameworks Imported: {len(frameworks)}")
    print(f"✓ Categories Imported: {len(categories)}")
    print(f"✓ Controls Imported: {len(controls)}")

    imported_short_names = {
        framework.short_name for framework in frameworks
    }

    missing = [
        name for name in discovered
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

    discovered = discover_frameworks(FRAMEWORKS_DIR)

    db = SessionLocal()

    try:
        import_all_frameworks(db, discovered)
        verify_import(db, discovered)
    finally:
        db.close()

    print("Database bootstrap complete.")


if __name__ == "__main__":
    main()
