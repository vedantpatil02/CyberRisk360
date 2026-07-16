"""add audit management

Revision ID: a3f7c2e91b4d
Revises: ed54d857372f
Create Date: 2026-07-16 13:00:00.000000

Adds the Audit Management (GRC audit engagement) tables: audits and
audit_findings. Net-new tables, not column additions to an existing
table, so no batch_alter_table needed.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f7c2e91b4d'
down_revision: Union[str, Sequence[str], None] = 'ed54d857372f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audits",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("framework_id", sa.Integer(), nullable=True),
        sa.Column("lead_auditor_id", sa.Integer(), nullable=True),
        sa.Column("scope", sa.String(), nullable=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["framework_id"],
            ["frameworks.id"],
            name=op.f("fk_audits_framework_id_frameworks"),
        ),
        sa.ForeignKeyConstraint(
            ["lead_auditor_id"],
            ["users.id"],
            name=op.f("fk_audits_lead_auditor_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_audits_org_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audits")),
    )
    op.create_index(op.f("ix_audits_id"), "audits", ["id"], unique=False)
    op.create_index(
        op.f("ix_audits_lead_auditor_id"), "audits", ["lead_auditor_id"], unique=False
    )
    op.create_index(op.f("ix_audits_org_id"), "audits", ["org_id"], unique=False)

    op.create_table(
        "audit_findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("audit_id", sa.Integer(), nullable=False),
        sa.Column("control_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("severity", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["audit_id"],
            ["audits.id"],
            name=op.f("fk_audit_findings_audit_id_audits"),
        ),
        sa.ForeignKeyConstraint(
            ["control_id"],
            ["controls.id"],
            name=op.f("fk_audit_findings_control_id_controls"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_findings")),
    )
    op.create_index(
        op.f("ix_audit_findings_id"), "audit_findings", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_audit_findings_audit_id"), "audit_findings", ["audit_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_audit_findings_audit_id"), table_name="audit_findings")
    op.drop_index(op.f("ix_audit_findings_id"), table_name="audit_findings")
    op.drop_table("audit_findings")

    op.drop_index(op.f("ix_audits_org_id"), table_name="audits")
    op.drop_index(op.f("ix_audits_lead_auditor_id"), table_name="audits")
    op.drop_index(op.f("ix_audits_id"), table_name="audits")
    op.drop_table("audits")
