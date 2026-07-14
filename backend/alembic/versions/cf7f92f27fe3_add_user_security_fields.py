"""add user security fields

Revision ID: cf7f92f27fe3
Revises: dd92d089fdb0
Create Date: 2026-07-14 11:29:06.478425

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf7f92f27fe3'
down_revision: Union[str, Sequence[str], None] = 'dd92d089fdb0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # batch_alter_table is required for SQLite: a plain ADD COLUMN there
    # cannot use a CURRENT_TIMESTAMP default (SQLite rejects it), so the
    # created_at/updated_at columns would fail. Batch mode recreates the
    # table (default applied per-row during the copy); on PostgreSQL it
    # emits ordinary ALTER TABLE ADD COLUMN statements.
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default=sa.text('(true)'), nullable=False))
        batch_op.add_column(sa.Column('failed_login_attempts', sa.Integer(), server_default=sa.text('0'), nullable=False))
        batch_op.add_column(sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))
        batch_op.add_column(sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False))


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('updated_at')
        batch_op.drop_column('created_at')
        batch_op.drop_column('last_login')
        batch_op.drop_column('locked_until')
        batch_op.drop_column('failed_login_attempts')
        batch_op.drop_column('is_active')
