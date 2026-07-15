"""
CyberRisk360

Purpose:
Provision the platform super-admin (ROLE_SUPER_ADMIN) - the account
that spans every organization. Deliberately a separate, manually-run
script rather than part of bootstrap_database.py/docker-entrypoint.sh:
unlike seeding public reference data (frameworks/controls), creating a
privileged account is a deliberate operator action, not something that
should happen silently on every container start. super_admin is also
excluded from /register's VALID_ROLES (see app/core/constants.py), so
there is no other way to create one.

Safe to run multiple times: if a user with the target email already
exists, the script leaves it untouched by default (pass --force to
reset its password and grant it super_admin instead).

Usage:
    python scripts/bootstrap_super_admin.py
    python scripts/bootstrap_super_admin.py --force

Configuration (all optional, via environment variables):
    SUPER_ADMIN_EMAIL     default: superadmin@example.com
    SUPER_ADMIN_USERNAME  default: superadmin
    SUPER_ADMIN_PASSWORD  default: randomly generated and printed once
    SUPER_ADMIN_ORG_SLUG  default: "default" (org_id is a required
                           column but doesn't restrict a super_admin -
                           org scoping is bypassed for that role)

(can be run from any directory; the script anchors itself to backend/)
"""

import os
import secrets
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(BACKEND_DIR)

from sqlalchemy.exc import OperationalError

from app.db.database import SessionLocal
import app.models  # noqa: F401  (registers models with Base.metadata)

from app.core.constants import ROLE_SUPER_ADMIN
from app.repositories.users.user_repository import get_by_email, create_user
from app.repositories.organizations.organization_repository import (
    get_organization_by_slug
)
from app.services.security.security import hash_password

DEFAULT_EMAIL = "superadmin@example.com"
DEFAULT_USERNAME = "superadmin"
DEFAULT_ORG_SLUG = "default"


def _resolve_org(db, slug):
    organization = get_organization_by_slug(db, slug)

    if organization is None:
        raise RuntimeError(
            f"Organization with slug '{slug}' not found. Run "
            "`python scripts/bootstrap_database.py` (or an equivalent "
            "migration) first to seed the default organization."
        )

    return organization


def main():
    force = "--force" in sys.argv[1:]

    email = os.environ.get("SUPER_ADMIN_EMAIL", DEFAULT_EMAIL)
    username = os.environ.get("SUPER_ADMIN_USERNAME", DEFAULT_USERNAME)
    org_slug = os.environ.get("SUPER_ADMIN_ORG_SLUG", DEFAULT_ORG_SLUG)

    password = os.environ.get("SUPER_ADMIN_PASSWORD")
    generated = password is None

    if generated:
        password = secrets.token_urlsafe(16)

    db = SessionLocal()

    try:
        try:
            existing = get_by_email(db, email)
        except OperationalError:
            raise RuntimeError(
                "Database not migrated yet. Run "
                "`python scripts/bootstrap_database.py` first."
            )

        if existing is not None and not force:
            print(
                f"User '{email}' already exists (role={existing.role}) - "
                "leaving it untouched. Re-run with --force to reset its "
                "password and grant it super_admin."
            )
            return

        organization = _resolve_org(db, org_slug)

        if existing is not None and force:
            existing.password = hash_password(password)
            existing.role = ROLE_SUPER_ADMIN
            existing.is_active = True
            db.commit()
            print(f"Updated existing user '{email}' to super_admin.")
        else:
            create_user(
                db,
                username=username,
                email=email,
                password=hash_password(password),
                role=ROLE_SUPER_ADMIN,
                org_id=organization.id,
            )
            print(f"Created super_admin user '{email}'.")

    finally:
        db.close()

    if generated:
        print()
        print("Generated password (shown once - store it securely):")
        print(f"  {password}")
        print()
        print("Log in via POST /login, then change the password via")
        print("POST /users/me/change-password.")


if __name__ == "__main__":
    main()
