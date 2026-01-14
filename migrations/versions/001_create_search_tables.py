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
    # Criar tabela search_configs
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
    
    # Criar tabela search_terms
    op.create_table(
        'search_terms',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False, primary_key=True),
        sa.Column('term', sa.Text(), nullable=False),
        sa.Column('exact', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('search_config_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['search_config_id'], ['search_configs.id'], ondelete='CASCADE')
    )
    
    # Criar índices
    op.create_index('search_terms_config_idx', 'search_terms', ['search_config_id'])


def downgrade() -> None:
    op.drop_index('search_terms_config_idx', table_name='search_terms')
    op.drop_table('search_terms')
    op.drop_table('search_configs')

