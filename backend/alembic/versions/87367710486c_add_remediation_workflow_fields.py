"""add remediation workflow fields

Revision ID: 87367710486c
Revises: b7c1a4e9f0d2
Create Date: 2026-07-15 11:09:22.557584

Adds the remediation-workflow columns to vulnerabilities/risks
(assignee_id, due_date, created_at, updated_at) and a new
evidence_attachments table for uploaded remediation evidence.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '87367710486c'
down_revision: Union[str, Sequence[str], None] = 'b7c1a4e9f0d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Tables gaining assignee/due_date/timestamps.
REMEDIATION_TABLES = ["vulnerabilities", "risks"]


def upgrade() -> None:
    for table in REMEDIATION_TABLES:
        with op.batch_alter_table(table, schema=None) as batch:
            batch.add_column(sa.Column("assignee_id", sa.Integer(), nullable=True))
            batch.add_column(sa.Column("due_date", sa.DateTime(timezone=True), nullable=True))
            batch.add_column(
                sa.Column(
                    "created_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    nullable=False,
                )
            )
            batch.add_column(
                sa.Column(
                    "updated_at",
                    sa.DateTime(timezone=True),
                    server_default=sa.text("(CURRENT_TIMESTAMP)"),
                    nullable=False,
                )
            )
            batch.create_foreign_key(
                op.f(f"fk_{table}_assignee_id_users"),
                "users",
                ["assignee_id"],
                ["id"],
            )
            batch.create_index(
                op.f(f"ix_{table}_assignee_id"), ["assignee_id"], unique=False
            )

    op.create_table(
        "evidence_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vulnerability_id", sa.Integer(), nullable=True),
        sa.Column("risk_id", sa.Integer(), nullable=True),
        sa.Column("file_name", sa.String(), nullable=False),
        sa.Column("stored_path", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("uploaded_by_id", sa.Integer(), nullable=False),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column(
            "uploaded_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["vulnerability_id"],
            ["vulnerabilities.id"],
            name=op.f("fk_evidence_attachments_vulnerability_id_vulnerabilities"),
        ),
        sa.ForeignKeyConstraint(
            ["risk_id"],
            ["risks.id"],
            name=op.f("fk_evidence_attachments_risk_id_risks"),
        ),
        sa.ForeignKeyConstraint(
            ["uploaded_by_id"],
            ["users.id"],
            name=op.f("fk_evidence_attachments_uploaded_by_id_users"),
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_evidence_attachments_org_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_evidence_attachments")),
    )
    op.create_index(
        op.f("ix_evidence_attachments_id"), "evidence_attachments", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_evidence_attachments_vulnerability_id"),
        "evidence_attachments",
        ["vulnerability_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_attachments_risk_id"),
        "evidence_attachments",
        ["risk_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_attachments_org_id"),
        "evidence_attachments",
        ["org_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_evidence_attachments_uploaded_by_id"),
        "evidence_attachments",
        ["uploaded_by_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_evidence_attachments_uploaded_by_id"), table_name="evidence_attachments")
    op.drop_index(op.f("ix_evidence_attachments_org_id"), table_name="evidence_attachments")
    op.drop_index(op.f("ix_evidence_attachments_risk_id"), table_name="evidence_attachments")
    op.drop_index(op.f("ix_evidence_attachments_vulnerability_id"), table_name="evidence_attachments")
    op.drop_index(op.f("ix_evidence_attachments_id"), table_name="evidence_attachments")
    op.drop_table("evidence_attachments")

    for table in reversed(REMEDIATION_TABLES):
        with op.batch_alter_table(table, schema=None) as batch:
            batch.drop_index(op.f(f"ix_{table}_assignee_id"))
            batch.drop_constraint(op.f(f"fk_{table}_assignee_id_users"), type_="foreignkey")
            batch.drop_column("updated_at")
            batch.drop_column("created_at")
            batch.drop_column("due_date")
            batch.drop_column("assignee_id")
