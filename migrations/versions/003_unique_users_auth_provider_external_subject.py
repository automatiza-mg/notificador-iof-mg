"""unique constraint users (auth_provider, external_subject)

Revision ID: 003
Revises: 002
Create Date: 2025-02-04

"""
from sqlalchemy import inspect
from alembic import op


revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    if "users" not in inspector.get_table_names():
        return
    existing_indexes = [idx["name"] for idx in inspector.get_indexes("users")]
    if "uq_users_provider_subject" not in existing_indexes:
        op.create_index(
            "uq_users_provider_subject",
            "users",
            ["auth_provider", "external_subject"],
            unique=True,
        )


def downgrade() -> None:
    op.drop_index("uq_users_provider_subject", table_name="users")
