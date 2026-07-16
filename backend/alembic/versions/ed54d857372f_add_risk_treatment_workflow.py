"""add risk treatment workflow

Revision ID: ed54d857372f
Revises: 7269075996ec
Create Date: 2026-07-16 12:00:00.000000

Adds the Risk Treatment + Approval workflow columns to `risks`
(treatment_type, treatment_justification, approval_status, approved_by,
approved_at) and a new risk_treatment_history table, mirroring
mapping_history's shape for the vulnerability-control mapping approval
workflow.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ed54d857372f'
down_revision: Union[str, Sequence[str], None] = '7269075996ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("risks", schema=None) as batch:
        batch.add_column(sa.Column("treatment_type", sa.String(), nullable=True))
        batch.add_column(sa.Column("treatment_justification", sa.String(), nullable=True))
        batch.add_column(sa.Column("approval_status", sa.String(), nullable=True))
        batch.add_column(sa.Column("approved_by", sa.String(), nullable=True))
        batch.add_column(sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True))

    op.create_table(
        "risk_treatment_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("risk_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("previous_status", sa.String(), nullable=True),
        sa.Column("new_status", sa.String(), nullable=False),
        sa.Column("treatment_type", sa.String(), nullable=True),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("note", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["risk_id"],
            ["risks.id"],
            name=op.f("fk_risk_treatment_history_risk_id_risks"),
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_risk_treatment_history_org_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_risk_treatment_history")),
    )
    op.create_index(
        op.f("ix_risk_treatment_history_id"),
        "risk_treatment_history",
        ["id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_risk_treatment_history_org_id"),
        "risk_treatment_history",
        ["org_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_risk_treatment_history_org_id"), table_name="risk_treatment_history")
    op.drop_index(op.f("ix_risk_treatment_history_id"), table_name="risk_treatment_history")
    op.drop_table("risk_treatment_history")

    with op.batch_alter_table("risks", schema=None) as batch:
        batch.drop_column("approved_at")
        batch.drop_column("approved_by")
        batch.drop_column("approval_status")
        batch.drop_column("treatment_justification")
        batch.drop_column("treatment_type")
