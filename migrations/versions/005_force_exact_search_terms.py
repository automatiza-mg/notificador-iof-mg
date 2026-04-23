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

    search_terms = sa.table(
        "search_terms",
        sa.column("exact", sa.Boolean()),
    )
    op.execute(
        search_terms.update()
        .where(search_terms.c.exact.is_(sa.false()))
        .values(exact=sa.true())
    )


def downgrade() -> None:
    """Não reverte, pois os valores anteriores de exact=false não são recuperáveis."""
