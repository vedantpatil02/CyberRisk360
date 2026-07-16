"""add cisa kev cache

Revision ID: d47a9c3e6f18
Revises: c92e4f018a5d
Create Date: 2026-07-16 16:00:00.000000

Adds the cisa_kev_entries table caching CISA's Known Exploited
Vulnerabilities catalog (a single bulk feed, refreshed as a whole -
see app/services/enrichment/cisa_kev.py).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd47a9c3e6f18'
down_revision: Union[str, Sequence[str], None] = 'c92e4f018a5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cisa_kev_entries",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("cve_id", sa.String(), nullable=False),
        sa.Column("vulnerability_name", sa.String(), nullable=True),
        sa.Column("date_added", sa.DateTime(timezone=True), nullable=True),
        sa.Column("due_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("required_action", sa.Text(), nullable=True),
        sa.Column("known_ransomware_use", sa.String(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cisa_kev_entries")),
    )
    op.create_index(
        op.f("ix_cisa_kev_entries_id"), "cisa_kev_entries", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_cisa_kev_entries_cve_id"),
        "cisa_kev_entries",
        ["cve_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_cisa_kev_entries_cve_id"), table_name="cisa_kev_entries")
    op.drop_index(op.f("ix_cisa_kev_entries_id"), table_name="cisa_kev_entries")
    op.drop_table("cisa_kev_entries")
