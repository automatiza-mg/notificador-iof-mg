"""force exact search terms

Revision ID: 005
Revises: 004
Create Date: 2026-04-23

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy import inspect

revision = "005"
down_revision = "004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "search_terms" not in inspector.get_table_names():
        return

    op.execute(sa.text("UPDATE search_terms SET exact = 1 WHERE exact = 0"))


def downgrade() -> None:
    """Não reverte, pois os valores anteriores de exact=false não são recuperáveis."""
