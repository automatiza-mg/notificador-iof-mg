"""Utilitário para inicializar banco de dados."""

from typing import Any

from app.extensions import db


def init_db(app: Any) -> None:
    """
    Cria todas as tabelas do banco de dados se não existirem.

    Args:
        app: Instância da aplicação Flask
    """
    with app.app_context():
        # Verificar se as tabelas existem
        inspector = db.inspect(db.engine)
        existing_tables = inspector.get_table_names()

        tables_to_create = ["search_configs", "search_terms"]
        missing_tables = [t for t in tables_to_create if t not in existing_tables]

        if missing_tables:
            app.logger.warning("Tabelas faltando: %s. Criando...", missing_tables)
            # Criar todas as tabelas
            db.create_all()
            app.logger.info("Tabelas criadas com sucesso")
        else:
            app.logger.info("Todas as tabelas já existem")
