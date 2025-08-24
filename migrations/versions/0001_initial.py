"""initial schema
Revision ID: 0001
Revises:
Create Date: 2025-08-24
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password", sa.String(length=120), nullable=False),
        sa.UniqueConstraint("username", name="uq_user_username"),
    )

    op.create_table(
        "meal_plan",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete=None),
    )

    op.create_table(
        "day",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("meal_plan_id", sa.Integer(), nullable=False),
        sa.Column("day_number", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["meal_plan_id"], ["meal_plan.id"], ondelete=None
        ),
    )

    op.create_table(
        "meal",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("day_id", sa.Integer(), nullable=False),
        sa.Column("meal_type", sa.String(length=50), nullable=False),
        sa.ForeignKeyConstraint(["day_id"], ["day.id"], ondelete=None),
    )

    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("weight", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["meal_id"], ["meal.id"], ondelete=None),
    )


def downgrade() -> None:
    op.drop_table("product")
    op.drop_table("meal")
    op.drop_table("day")
    op.drop_table("meal_plan")
    op.drop_table("user")
