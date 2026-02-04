"""add users and user_id to search_configs

Revision ID: 002
Revises: 001
Create Date: 2025-02-04

"""
from sqlalchemy import inspect
from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("password_hash", sa.Text(), nullable=True),
            sa.Column("auth_provider", sa.String(length=32), nullable=False, server_default="local"),
            sa.Column("external_subject", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

        conn = op.get_bind()
        conn.execute(
            sa.text(
                "INSERT INTO users (email, auth_provider, created_at) "
                "VALUES ('migration-default@local', 'local', CURRENT_TIMESTAMP)"
            )
        )
    else:
        # Tabela já existe (migração parcial); garantir que exista usuário id=1
        conn = op.get_bind()
        r = conn.execute(sa.text("SELECT 1 FROM users WHERE id = 1 LIMIT 1")).fetchone()
        if not r:
            conn.execute(
                sa.text(
                    "INSERT INTO users (id, email, auth_provider, created_at) "
                    "VALUES (1, 'migration-default@local', 'local', CURRENT_TIMESTAMP)"
                )
            )

    if "search_configs" in existing_tables:
        cols = [c["name"] for c in inspector.get_columns("search_configs")]
        if "user_id" not in cols:
            # SQLite não suporta ADD COLUMN com FK em ALTER; usar apenas Integer
            op.add_column(
                "search_configs",
                sa.Column("user_id", sa.Integer(), nullable=False, server_default=sa.text("1")),
            )
        existing_indexes = [idx["name"] for idx in inspector.get_indexes("search_configs")]
        if "ix_search_configs_user_id_active" not in existing_indexes:
            op.create_index(
                "ix_search_configs_user_id_active",
                "search_configs",
                ["user_id", "active"],
            )


def downgrade() -> None:
    op.drop_index("ix_search_configs_user_id_active", table_name="search_configs")
    op.drop_column("search_configs", "user_id")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")
