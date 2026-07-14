"""add organizations and org_id multitenancy

Revision ID: b7c1a4e9f0d2
Revises: 21824ec0933b
Create Date: 2026-07-14

Introduces the Organization tenant boundary and adds a non-null
`org_id` to every per-organization table. Existing rows are backfilled
to a seeded "Default Organization" so the NOT NULL + FK can be applied
without data loss.

Reference data (frameworks, categories, controls, plugin_enrichment_
cache) is intentionally NOT scoped - it is shared across organizations.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7c1a4e9f0d2"
down_revision: Union[str, Sequence[str], None] = "21824ec0933b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Per-organization tables that gain a NOT NULL org_id (a row always
# belongs to exactly one organization).
SCOPED_TABLES = [
    "users",
    "assets",
    "risks",
    "vulnerabilities",
    "vulnerability_control_mappings",
    "mapping_history",
]

# audit_logs is org-scoped too, but its org_id is NULLABLE: some events
# have no organization (a failed login for an unknown email, or a
# platform super-admin action).
AUDIT_TABLE = "audit_logs"

DEFAULT_ORG_ID = 1


def upgrade() -> None:
    # 1. Organizations table.
    op.create_table(
        "organizations",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("slug", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_organizations")),
    )
    op.create_index(
        op.f("ix_organizations_id"), "organizations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_organizations_slug"),
        "organizations",
        ["slug"],
        unique=True,
    )

    # 2. Seed the default organization existing data is assigned to.
    op.execute(
        "INSERT INTO organizations (id, name, slug) "
        f"VALUES ({DEFAULT_ORG_ID}, 'Default Organization', 'default')"
    )

    # 3. Add org_id to every scoped table: nullable -> backfill ->
    #    NOT NULL + FK. batch_alter_table makes the NOT NULL/FK steps
    #    work on SQLite (which can't ALTER them in place).
    for table in SCOPED_TABLES:
        with op.batch_alter_table(table, schema=None) as batch:
            batch.add_column(
                sa.Column("org_id", sa.Integer(), nullable=True)
            )

        op.execute(
            f"UPDATE {table} SET org_id = {DEFAULT_ORG_ID}"
        )

        with op.batch_alter_table(table, schema=None) as batch:
            batch.alter_column(
                "org_id",
                existing_type=sa.Integer(),
                nullable=False,
            )
            batch.create_foreign_key(
                op.f(f"fk_{table}_org_id_organizations"),
                "organizations",
                ["org_id"],
                ["id"],
            )
            batch.create_index(
                op.f(f"ix_{table}_org_id"), ["org_id"], unique=False
            )

    # 4. audit_logs: nullable org_id + FK + index (existing rows
    #    backfilled to the default org).
    with op.batch_alter_table(AUDIT_TABLE, schema=None) as batch:
        batch.add_column(sa.Column("org_id", sa.Integer(), nullable=True))
        batch.create_foreign_key(
            op.f(f"fk_{AUDIT_TABLE}_org_id_organizations"),
            "organizations",
            ["org_id"],
            ["id"],
        )
        batch.create_index(
            op.f(f"ix_{AUDIT_TABLE}_org_id"), ["org_id"], unique=False
        )

    op.execute(
        f"UPDATE {AUDIT_TABLE} SET org_id = {DEFAULT_ORG_ID}"
    )


def downgrade() -> None:
    with op.batch_alter_table(AUDIT_TABLE, schema=None) as batch:
        batch.drop_index(op.f(f"ix_{AUDIT_TABLE}_org_id"))
        batch.drop_constraint(
            op.f(f"fk_{AUDIT_TABLE}_org_id_organizations"),
            type_="foreignkey",
        )
        batch.drop_column("org_id")

    for table in SCOPED_TABLES:
        with op.batch_alter_table(table, schema=None) as batch:
            batch.drop_index(op.f(f"ix_{table}_org_id"))
            batch.drop_constraint(
                op.f(f"fk_{table}_org_id_organizations"),
                type_="foreignkey",
            )
            batch.drop_column("org_id")

    op.drop_index(op.f("ix_organizations_slug"), table_name="organizations")
    op.drop_index(op.f("ix_organizations_id"), table_name="organizations")
    op.drop_table("organizations")
