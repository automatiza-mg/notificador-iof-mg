"""drop description from search_configs

Revision ID: 004
Revises: 003
Create Date: 2026-04-16

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "search_configs" not in inspector.get_table_names():
        return

    columns = [column["name"] for column in inspector.get_columns("search_configs")]
    if "description" in columns:
        op.drop_column("search_configs", "description")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "search_configs" not in inspector.get_table_names():
        return

    columns = [column["name"] for column in inspector.get_columns("search_configs")]
    if "description" not in columns:
        op.add_column(
            "search_configs",
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
        )
