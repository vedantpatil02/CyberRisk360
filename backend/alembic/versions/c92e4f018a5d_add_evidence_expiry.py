"""add evidence expiry

Revision ID: c92e4f018a5d
Revises: f8b12d6e4a91
Create Date: 2026-07-16 15:00:00.000000

Adds the optional expires_at column to evidence_attachments, driving
the in-app notification list (computed live, no background job).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c92e4f018a5d'
down_revision: Union[str, Sequence[str], None] = 'f8b12d6e4a91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("evidence_attachments", schema=None) as batch:
        batch.add_column(sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("evidence_attachments", schema=None) as batch:
        batch.drop_column("expires_at")
