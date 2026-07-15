"""add nvd enrichment cache

Revision ID: 7269075996ec
Revises: 87367710486c
Create Date: 2026-07-15 11:22:04.252258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7269075996ec'
down_revision: Union[str, Sequence[str], None] = '87367710486c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'nvd_enrichment_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cve_id', sa.String(), nullable=False),
        sa.Column('cvss_score', sa.Float(), nullable=True),
        sa.Column('cvss_vector', sa.String(), nullable=True),
        sa.Column('cvss_version', sa.String(), nullable=True),
        sa.Column('cwe_id', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_nvd_enrichment_cache'))
    )
    op.create_index(op.f('ix_nvd_enrichment_cache_id'), 'nvd_enrichment_cache', ['id'], unique=False)
    op.create_index(op.f('ix_nvd_enrichment_cache_cve_id'), 'nvd_enrichment_cache', ['cve_id'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_nvd_enrichment_cache_cve_id'), table_name='nvd_enrichment_cache')
    op.drop_index(op.f('ix_nvd_enrichment_cache_id'), table_name='nvd_enrichment_cache')
    op.drop_table('nvd_enrichment_cache')
