"""create search tables

Revision ID: 001
Revises: 
Create Date: 2025-01-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Verificar se as tabelas já existem antes de criar
    # Isso evita erro se db.create_all() já tiver criado as tabelas
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()
    
    # Criar tabela search_configs apenas se não existir
    if 'search_configs' not in existing_tables:
        op.create_table(
            'search_configs',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
            sa.Column('label', sa.String(length=255), nullable=False),
            sa.Column('description', sa.Text(), nullable=False, server_default=''),
            sa.Column('attach_csv', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('mail_to', sa.Text(), nullable=False, server_default='[]'),  # JSON array como texto
            sa.Column('mail_subject', sa.String(length=255), nullable=False, server_default=''),
            sa.Column('teams_webhook', sa.Text(), nullable=True),
            sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'))
        )
    
    # Criar tabela search_terms apenas se não existir
    if 'search_terms' not in existing_tables:
        op.create_table(
            'search_terms',
            sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
            sa.Column('term', sa.Text(), nullable=False),
            sa.Column('exact', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('search_config_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['search_config_id'], ['search_configs.id'], ondelete='CASCADE')
        )
    
    # Criar índice apenas se não existir
    # Verificar se a tabela existe (pode ter sido criada acima ou já existir)
    tables_after = inspector.get_table_names()
    if 'search_terms' in tables_after:
        try:
            # Verificar se o índice já existe
            existing_indexes = [idx['name'] for idx in inspector.get_indexes('search_terms')]
            if 'search_terms_config_idx' not in existing_indexes:
                op.create_index('search_terms_config_idx', 'search_terms', ['search_config_id'])
        except Exception:
            # Se não conseguir verificar índices, verificar via SQL
            try:
                result = bind.execute(sa.text(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='search_terms_config_idx'"
                )).fetchone()
                if not result:
                    op.create_index('search_terms_config_idx', 'search_terms', ['search_config_id'])
            except Exception:
                pass  # Índice provavelmente já existe ou erro ao verificar


def downgrade() -> None:
    op.drop_index('search_terms_config_idx', table_name='search_terms')
    op.drop_table('search_terms')
    op.drop_table('search_configs')

