"""Worker para processar diário oficial diário."""

import traceback
from datetime import date
from pathlib import Path

from redis import Redis

from app import create_app
from app.repositories.search_config_repository import SearchConfigRepository
from app.repositories.sqlite_document_repository import SQLiteDocumentRepository
from app.services.gazette_service import GazetteService
from app.services.search_service import SearchService


def process_daily_gazette(publish_date: date) -> None:
    """
    Processa o diário oficial de uma data específica.

    Args:
        publish_date: Data de publicação do diário
    """
    app = create_app()
    with app.app_context():
        try:
            # Configurar dependências
            diarios_dir = app.config.get("DIARIOS_DIR", "diarios")
            search_db = str(Path(diarios_dir) / "diarios.db")

            doc_repo = SQLiteDocumentRepository(search_db)
            config_repo = SearchConfigRepository()
            search_service = SearchService(config_repo)

            # Redis connection para enfileiramento
            redis_conn = Redis.from_url(
                app.config.get("REDIS_URL", "redis://localhost:6379/0")
            )

            # Instanciar e executar serviço
            service = GazetteService(
                doc_repository=doc_repo,
                search_service=search_service,
                queue_connection=redis_conn,
            )

            service.process_date(publish_date)

        except Exception:
            app.logger.exception("Erro na task process_daily_gazette")
            traceback.print_exc()
            raise
