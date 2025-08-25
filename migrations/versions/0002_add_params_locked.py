"""add params_locked to user_plan_settings

Revision ID: 0002_add_params_locked
Revises: 0001_initial
Create Date: 2025-08-25 00:00:00
"""

from alembic import op
import sqlalchemy as sa
from alembic import context


# revision identifiers, used by Alembic.
revision = '0002_add_params_locked'
down_revision = '0001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add NOT NULL column with default False so existing rows get a value.
    op.add_column(
        'user_plan_settings',
        sa.Column(
            'params_locked',
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )

    # Drop server default on dialects that support it (SQLite does not).
    try:
        if context.get_context().dialect.name != 'sqlite':
            op.alter_column(
                'user_plan_settings',
                'params_locked',
                server_default=None,
            )
    except Exception:
        # Be conservative: skip altering default if unsupported
        pass


def downgrade() -> None:
    op.drop_column('user_plan_settings', 'params_locked')
