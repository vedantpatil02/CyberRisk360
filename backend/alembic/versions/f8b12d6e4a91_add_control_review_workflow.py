"""add control review workflow

Revision ID: f8b12d6e4a91
Revises: a3f7c2e91b4d
Create Date: 2026-07-16 14:00:00.000000

Adds the control_reviews table - an audit trail of control
implementation-status review events, layered on top of the existing
global Control.status field (no schema change to controls itself).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f8b12d6e4a91'
down_revision: Union[str, Sequence[str], None] = 'a3f7c2e91b4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "control_reviews",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("control_id", sa.Integer(), nullable=False),
        sa.Column("reviewer", sa.String(), nullable=True),
        sa.Column("previous_status", sa.String(), nullable=True),
        sa.Column("new_status", sa.String(), nullable=False),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("org_id", sa.Integer(), nullable=False),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["control_id"],
            ["controls.id"],
            name=op.f("fk_control_reviews_control_id_controls"),
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organizations.id"],
            name=op.f("fk_control_reviews_org_id_organizations"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_control_reviews")),
    )
    op.create_index(
        op.f("ix_control_reviews_id"), "control_reviews", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_control_reviews_control_id"),
        "control_reviews",
        ["control_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_control_reviews_org_id"), "control_reviews", ["org_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_control_reviews_org_id"), table_name="control_reviews")
    op.drop_index(op.f("ix_control_reviews_control_id"), table_name="control_reviews")
    op.drop_index(op.f("ix_control_reviews_id"), table_name="control_reviews")
    op.drop_table("control_reviews")
